#!/usr/bin/env python
import copy
import os
import youtube_dl

from le_utils.constants import content_kinds, exercises, licenses
from le_utils.constants.languages import getlang, getlang_by_name
from pressurecooker.youtube import get_language_with_alpha2_fallback
from ricecooker.chefs import JsonTreeChef
from ricecooker.classes.files import is_youtube_subtitle_file_supported_language
from ricecooker.config import LOGGER as logger
from ricecooker.utils.jsontrees import write_tree_to_json_tree

from common_core_tags import generate_common_core_mapping
from constants import UNSUBTITLED_LANGS, CHANNEL_DESCRIPTION_LOOKUP, VIDEO_LANGUAGE_MAPPING
from curation import get_slug_blacklist
from khan import KhanArticle, KhanExercise, KhanTopic, KhanVideo, get_khan_topic_tree



LICENSE_MAPPING = {
    "CC BY": dict(license_id=licenses.CC_BY, copyright_holder="Khan Academy"),
    "CC BY-NC": dict(license_id=licenses.CC_BY_NC, copyright_holder="Khan Academy"),
    "CC BY-NC-ND": dict(
        license_id=licenses.CC_BY_NC_ND, copyright_holder="Khan Academy"
    ),
    "CC BY-NC-SA (KA default)": dict(
        license_id=licenses.CC_BY_NC_SA, copyright_holder="Khan Academy"
    ),
    "CC BY-SA": dict(license_id=licenses.CC_BY_SA, copyright_holder="Khan Academy"),
    "Non-commercial/non-Creative Commons (College Board)": dict(
        license_id=licenses.SPECIAL_PERMISSIONS,
        copyright_holder="Khan Academy",
        description="Non-commercial/non-Creative Commons (College Board)",
    ),
    # "Standard Youtube": licenses.ALL_RIGHTS_RESERVED,
}

EXERCISE_MAPPING = {
    "do-all": exercises.DO_ALL,
    "skill-check": exercises.SKILL_CHECK,
    "num_problems_4": {"mastery_model": exercises.M_OF_N, "m": 3, "n": 4},
    "num_problems_7": {"mastery_model": exercises.M_OF_N, "m": 5, "n": 7},
    "num_problems_14": {"mastery_model": exercises.M_OF_N, "m": 10, "n": 14},
    "num_correct_in_a_row_2": {"mastery_model": exercises.NUM_CORRECT_IN_A_ROW_2},
    "num_correct_in_a_row_3": {"mastery_model": exercises.NUM_CORRECT_IN_A_ROW_3},
    "num_correct_in_a_row_5": {"mastery_model": exercises.NUM_CORRECT_IN_A_ROW_5},
    "num_correct_in_a_row_10": {"mastery_model": exercises.NUM_CORRECT_IN_A_ROW_10},
}


CC_MAPPING = generate_common_core_mapping()


class KhanAcademySushiChef(JsonTreeChef):
    """
    Khan Academy sushi chef.
    """

    def get_json_tree_path(self, *args, **kwargs):
        """
        Return path to ricecooker json tree file. Override this method to use
        a custom filename, e.g., for channel with multiple languages.
        """
        RICECOOKER_JSON_TREE_TPL = "ricecooker_json_tree_{}.json"

        # Get channel language from kwargs
        if "lang" in kwargs:
            language_code = kwargs["lang"]
        else:
            language_code = "en"  # default to en if lang not specifed

        lang_obj = getlang(language_code) or getlang_by_name(language_code)

        json_filename = RICECOOKER_JSON_TREE_TPL.format(lang_obj.code)
        json_tree_path = os.path.join(self.TREES_DATA_DIR, json_filename)
        return json_tree_path


    def pre_run(self, args, options):
        if "lang" in options:
            language_code = options["lang"]
        else:
            language_code = "en"  # default to en if lang not specifed
        lang_obj = getlang(language_code) or getlang_by_name(language_code)

        channel_node = dict(
            source_id="KA ({0})".format(language_code),
            source_domain="khanacademy.org",
            title="Khan Academy ({0})".format(lang_obj.first_native_name),
            description=CHANNEL_DESCRIPTION_LOOKUP.get(
                language_code, "Khan Academy content for {}.".format(lang_obj.name)
            ),
            thumbnail=os.path.join("chefdata", "khan-academy-logo.png"),
            language=lang_obj.code,
            children=[],
        )

        # build studio channel out of youtube playlist
        if options.get("youtube_channel_id"):
            youtube_id = options.get("youtube_channel_id")
            logger.info(
                "Downloading youtube playlist {} for {} language".format(
                    youtube_id, lang_obj.name
                )
            )
            root_node = youtube_playlist_scraper(youtube_id, channel_node)
            # write to json file
            logger.info("writing ricecooker json to a file")
            json_tree_path = self.get_json_tree_path(*args, **options)
            write_tree_to_json_tree(json_tree_path, root_node)
            return

        logger.info("downloading KA tree")
        # build channel through KA API
        ka_root_topic = get_khan_topic_tree(lang=language_code)

        if options.get("english_subtitles"):
            # we will include english videos with target language subtitles
            duplicate_videos(ka_root_topic)

        language_code = lang_obj.code  # using internal code repr. from le-utils
        logger.info("converting KA nodes to ricecooker json nodes")
        root_topic = convert_ka_node_to_ricecooker_node(
            ka_root_topic, target_lang=language_code
        )
        for topic in root_topic["children"]:
            channel_node["children"].append(topic)

        # write to ricecooker tree to json file
        logger.info("writing ricecooker json to a file")
        json_tree_path = self.get_json_tree_path(*args, **options)
        write_tree_to_json_tree(json_tree_path, channel_node)




def youtube_playlist_scraper(channel_id, channel_node):
    ydl = youtube_dl.YoutubeDL(
        {
            "no_warnings": True,
            "writesubtitles": True,
            "allsubtitles": True,
            "ignoreerrors": True,  # Skip over deleted videos in a playlist
            "skip_download": True,
        }
    )
    youtube_channel_url = "https://www.youtube.com/channel/{}/playlists".format(
        channel_id
    )
    youtube_channel = ydl.extract_info(youtube_channel_url)
    for playlist in youtube_channel["entries"]:
        if playlist:
            topic_node = dict(
                kind=content_kinds.TOPIC,
                source_id=playlist["id"],
                title=playlist["title"],
                description="",
                children=[],
            )
            channel_node["children"].append(topic_node)
            entries = []
            for video in playlist["entries"]:
                if video and video["id"] not in entries:
                    entries.append(video["id"])
                    files = [dict(file_type="video", youtube_id=video["id"])]
                    video_node = dict(
                        kind=content_kinds.VIDEO,
                        source_id=video["id"],
                        title=video["title"],
                        description="",
                        thumbnail=video["thumbnail"],
                        license=LICENSE_MAPPING["CC BY-NC-ND"],
                        files=files,
                    )
                    topic_node["children"].append(video_node)

    return channel_node


def duplicate_videos(node):
    """
    Duplicate any videos that are dubbed, but convert them to being english only
    in order to add subtitled english videos (if available).
    """
    children = list(node.children)
    add = 0
    for idx, ka_node in enumerate(children):
        if isinstance(ka_node, KhanTopic):
            duplicate_videos(ka_node)
        if isinstance(ka_node, KhanVideo):
            if ka_node.lang != "en":
                replica_node = copy.deepcopy(ka_node)
                replica_node.translated_youtube_id = ka_node.youtube_id
                replica_node.lang = "en"
                ka_node.title = ka_node.title + " -dubbed(KY)"
                node.children.insert(idx + add, replica_node)
                add += 1

    return node


def should_include_subtitle(youtube_language, target_lang):
    """
    Determine whether subtitles with language code `youtube_language` available
    for a YouTube video should be imported as part of the Khan Academy chef run
    for language `target_lang` (internal language code).
    """
    lang_obj = get_language_with_alpha2_fallback(youtube_language)
    target_lang_obj = getlang(target_lang)
    if lang_obj.primary_code == target_lang_obj.primary_code:
        return True  # accept if the same language code even if different locale
    else:
        return False


def convert_ka_node_to_ricecooker_node(ka_node, target_lang=None):
    """
    Convert a KA node (a subclass of `KhanNode`) to a ricecooker node (dict).
    Returns None if node slug is blacklisted or inadmissable for inclusion for
    some other reason (e.g. video not translated and no subtitles available).
    """
    SLUG_BLACKLIST = get_slug_blacklist(lang=target_lang)

    if ka_node.slug in SLUG_BLACKLIST:
        return None

    if isinstance(ka_node, KhanTopic):
        topic = dict(
            kind=content_kinds.TOPIC,
            source_id=ka_node.id,
            title=ka_node.title,
            description=ka_node.description[:400] if ka_node.description else '',
            slug=ka_node.slug,
            children=[],
        )
        for ka_subtopic in ka_node.children:
            subtopic = convert_ka_node_to_ricecooker_node(
                ka_subtopic, target_lang=target_lang
            )
            if subtopic:
                topic["children"].append(subtopic)
        if len(topic["children"]) > 0:
            return topic
        else:
            return None

    elif isinstance(ka_node, KhanExercise):

        if ka_node.mastery_model in EXERCISE_MAPPING:
            mastery_model = EXERCISE_MAPPING[ka_node.mastery_model]
        else:
            logger.warning(
                "Unknown mastery model ({}) for exercise with id: {}".format(
                    ka_node.mastery_model, ka_node.id
                )
            )
            mastery_model = exercises.M_OF_N

        # common core tags
        tags = []
        if ka_node.slug in CC_MAPPING:
            tags.append(CC_MAPPING[ka_node.slug])

        exercise = dict(
            kind=content_kinds.EXERCISE,
            source_id=ka_node.id,
            title=ka_node.title,
            description=ka_node.description[:400] if ka_node.description else '',
            exercise_data=mastery_model,
            license=dict(
                license_id=licenses.SPECIAL_PERMISSIONS,
                copyright_holder="Khan Academy",
                description="Permission granted to distribute through Kolibri for non-commercial use",
            ),  # need to formalize with KA
            thumbnail=ka_node.thumbnail,
            slug=ka_node.slug,
            questions=[],
            tags=tags,
        )
        for ka_assessment_item in ka_node.get_assessment_items():
            if ka_assessment_item.data and ka_assessment_item.data != "null":
                assessment_item = dict(
                    question_type=exercises.PERSEUS_QUESTION,
                    id=ka_assessment_item.id,
                    item_data=ka_assessment_item.data,
                    source_url=ka_assessment_item.source_url,
                )
            exercise["questions"].append(assessment_item)
        # if there are no questions for this exercise, return None
        if not exercise["questions"]:
            return None
        return exercise

    elif isinstance(ka_node, KhanVideo):
        le_target_lang = target_lang
        target_lang = VIDEO_LANGUAGE_MAPPING.get(target_lang, target_lang)

        if ka_node.youtube_id != ka_node.translated_youtube_id:
            if ka_node.lang != target_lang.lower():
                logger.error(
                    "Node with youtube id: {} and translated id: {} has wrong language".format(
                        ka_node.youtube_id, ka_node.translated_youtube_id
                    )
                )
                return None

        # if download_url is missing, return None for this node
        download_url = ka_node.download_urls.get("mp4-low", ka_node.download_urls.get("mp4"))
        if download_url is None:
            logger.error(
                "No download urls for youtube_id: {}".format(ka_node.youtube_id)
            )
            return None

        # for lite languages, replace youtube ids with translated ones
        if ka_node.translated_youtube_id not in download_url:
            download_url = ka_node.download_urls.get("mp4").replace(
                ka_node.youtube_id, ka_node.translated_youtube_id
            )

        # TODO: Use traditional compression here to avoid breaking existing KA downloads?
        files = [
            # Mar 25: special run for Italian and Chinese: download from youtube instead of from KA CDN
            dict(
                file_type="video",
                # path=download_url,
                youtube_id=ka_node.translated_youtube_id,
                high_resolution=False,
            )
        ]

        # include any subtitles that are available for this video
        if le_target_lang not in UNSUBTITLED_LANGS:
            subtitle_languages = ka_node.get_subtitle_languages()
        else:
            subtitle_languages = []

        # if we dont have video in target lang or subtitle not available in target lang, return None
        if ka_node.lang != target_lang.lower():
            if target_lang not in subtitle_languages:
                logger.error(
                    "Video {} not transalated and no subtitles available. Skipping.".format(ka_node.translated_youtube_id)
                )
                return None

        for lang_code in subtitle_languages:
            if is_youtube_subtitle_file_supported_language(lang_code):
                if target_lang == "en":
                    files.append(
                        dict(
                            file_type="subtitles",
                            youtube_id=ka_node.translated_youtube_id,
                            language=lang_code,
                        )
                    )
                elif should_include_subtitle(lang_code, le_target_lang):
                    files.append(
                        dict(
                            file_type="subtitles",
                            youtube_id=ka_node.translated_youtube_id,
                            language=lang_code,
                        )
                    )
                else:
                    logger.debug(
                        'Skipping subs with lang_code {} for video {}'.format(
                            lang_code, ka_node.translated_youtube_id))

        # convert KA's license format into our internal license classes
        if ka_node.license in LICENSE_MAPPING:
            license = LICENSE_MAPPING[ka_node.license]
        else:
            # license = licenses.CC_BY_NC_SA # or?
            logger.error("Unknown license ({}) on video with youtube id: {}".format(
                ka_node.license, ka_node.translated_youtube_id))
            return None

        video = dict(
            kind=content_kinds.VIDEO,
            source_id=ka_node.translated_youtube_id if "-dubbed(KY)" in ka_node.title else ka_node.youtube_id,
            title=ka_node.title,
            description=ka_node.description[:400] if ka_node.description else '',
            license=license,
            thumbnail=ka_node.thumbnail,
            files=files,
        )

        return video

    elif isinstance(ka_node, KhanArticle):
        # TODO
        return None


if __name__ == "__main__":
    chef = KhanAcademySushiChef()
    chef.main()

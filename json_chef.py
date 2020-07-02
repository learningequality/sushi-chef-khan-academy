#!/usr/bin/env python
import copy
import os
import youtube_dl

from le_utils.constants import content_kinds, exercises, licenses
from le_utils.constants.languages import getlang
from pressurecooker.youtube import get_language_with_alpha2_fallback
from ricecooker.chefs import JsonTreeChef
from ricecooker.classes.files import is_youtube_subtitle_file_supported_language
from ricecooker.classes.nodes import ChannelNode
from ricecooker.config import LOGGER
from ricecooker.utils.jsontrees import write_tree_to_json_tree

from common_core_tags import generate_common_core_mapping
from constants import DUBBED_VIDEOS_BY_LANG
from constants import VIDEO_LANGUAGE_MAPPING
from constants import get_channel_title
from constants import get_channel_description
from curation import get_slug_blacklist
from curation import get_topic_tree_replacements
from khan import KhanArticle, KhanExercise, KhanTopic, KhanVideo, get_khan_topic_tree
from network import get_subtitle_languages


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
    # "Standard Youtube": licenses.ALL_RIGHTS_RESERVED,  # warn and skip these
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


CC_MAPPING = {}  # Common Core State Standards slug -> list(tag) to apply


class KhanAcademySushiChef(JsonTreeChef):
    """
    Khan Academy sushi chef.
    """
    slug_blacklist = []      # spec about `KhanTopic`s to be skipped
    topics_by_slug = {}      # lookup table { slug --> KhanTopic }
    topic_replacements = {}  # spec about `KhanTopic`s to be replaced


    def parse_lang_and_variant_from_kwargs(self, kwargs):
        """
        Helper method to parse and validate the `lang` and `variant` options.
        Returns: (lang, variant), where `lang` uses internal repr. from le-utils
        and `variant` (str or None) identifies different channel version.
        """
        if "lang" not in kwargs:
            raise ValueError('Khan Academy chef must be run with lang=<code>')
        lang = kwargs["lang"]
        assert getlang(lang), 'Language code ' + lang + ' not recognized'
        variant = kwargs.get("variant", None)
        return lang, variant


    def get_channel_dict(self, kwargs):
        """
        Returns the channel info as a Python dictionary (to avoid duplication).
        """
        lang, variant = self.parse_lang_and_variant_from_kwargs(kwargs)
        if variant:
            channel_source_id = "KA ({}/{})".format(lang, variant)
        else:
            channel_source_id = "KA ({})".format(lang)
        # Build dict with all the info required to create the ChannelNode object
        channel_dict = dict(
            source_id=channel_source_id,
            source_domain="khanacademy.org",
            title=get_channel_title(lang=lang, variant=variant),
            description=get_channel_description(lang=lang, variant=variant),
            thumbnail=os.path.join("chefdata", "khan-academy-logo.png"),
            language=lang,
        )
        return channel_dict

    def get_channel(self, **kwargs):
        """
        Override the base class method to load the same data as in `pre_run`.
        """
        channel_dict = self.get_channel_dict(kwargs)
        return ChannelNode(**channel_dict)


    def get_json_tree_path(self, **kwargs):
        """
        Return path to file that contains the ricecooker json tree.
        """
        lang, variant = self.parse_lang_and_variant_from_kwargs(kwargs)
        if variant:
            filename_suffix = "{}_{}".format(lang, variant)
        else:
            filename_suffix = lang
        RICECOOKER_JSON_TREE_TPL = "ricecooker_json_tree_{}.json"
        json_filename = RICECOOKER_JSON_TREE_TPL.format(filename_suffix)
        json_tree_path = os.path.join(self.TREES_DATA_DIR, json_filename)
        return json_tree_path


    def pre_run(self, args, options):
        """
        This is where all the works happens for this chef:
        - Load the source tree from the Khan Academy API
        - Convert the tree of Khan-objects in ricecooker_json dicts objects
        - Write ricecooker json tree to the appropriate file
        """
        lang, variant = self.parse_lang_and_variant_from_kwargs(options)

        if lang == "en" and variant != "in-in":
            # Load the CCSSM tags for the KA en channel (but not in-in variant)
            global CC_MAPPING
            CC_MAPPING = generate_common_core_mapping()

        channel_node = self.get_channel_dict(options)
        channel_node["children"] = []

        # Handle special case of building Kolibri channel from youtube playlists
        if options.get("youtube_channel_id"):
            youtube_channel_id = options.get("youtube_channel_id")
            LOGGER.info("Found YouTube channel {}".format(youtube_channel_id))
            root_node = youtube_playlist_scraper(youtube_channel_id, channel_node)
            json_tree_path = self.get_json_tree_path(**options)
            LOGGER.info("Writing youtube ricecooker tree to " + json_tree_path)
            write_tree_to_json_tree(json_tree_path, root_node)
            return None

        LOGGER.info("Downloading KA topic tree")
        # Obtain the complete topic tree for lang=lang from the KA API
        ka_root_topic, topics_by_slug = get_khan_topic_tree(lang=lang)
        # TODO: discuss w @kollivier introducing "archive" step here (for source diffs)
        self.topics_by_slug = topics_by_slug  # to be used for topic replacments
        self.slug_blacklist = get_slug_blacklist(lang=lang, variant=variant)
        self.topic_replacements = get_topic_tree_replacements(lang=lang, variant=variant)

        if options.get("english_subtitles"):
            # we will include english videos with target language subtitles
            duplicate_videos(ka_root_topic)

        LOGGER.info("Converting KA nodes to ricecooker json nodes")
        root_topic = self.convert_ka_node_to_ricecooker_node(ka_root_topic, target_lang=lang)
        for topic in root_topic["children"]:
            channel_node["children"].append(topic)

        # write to ricecooker tree to json file
        json_tree_path = self.get_json_tree_path(**options)
        LOGGER.info("Writing ricecooker json tree to " + json_tree_path)
        write_tree_to_json_tree(json_tree_path, channel_node)


    def convert_ka_node_to_ricecooker_node(self, ka_node, target_lang=None):
        """
        Convert a KA node (a subclass of `KhanNode`) to a ricecooker node (dict).
        Returns None if node slug is blacklisted or inadmissable for inclusion
        due to another reason (e.g. undtranslated video and no subs available).
        """

        if ka_node.slug in self.slug_blacklist:
            return None

        if isinstance(ka_node, KhanTopic):
            LOGGER.debug('Converting ka_node ' + ka_node.slug + ' to ricecooker json')
            topic = dict(
                kind=content_kinds.TOPIC,
                source_id=ka_node.id,
                title=ka_node.title,
                description=ka_node.description[:400] if ka_node.description else '',
                slug=ka_node.slug,
                children=[],
            )
            for ka_node_child in ka_node.children:
                if isinstance(ka_node_child, KhanTopic) and ka_node_child.slug in self.topic_replacements:
                    # This topic must be replaced by a list of other topic nodes
                    replacements = self.topic_replacements[ka_node_child.slug]
                    LOGGER.debug('Replacing ka_node ' + ka_node.slug + ' with replacements=' + str(replacements))
                    for r in replacements:
                        rtopic = dict(
                            kind=content_kinds.TOPIC,
                            source_id=r['slug'],
                            title=r['translatedTitle'],        # guaranteed to exist
                            description=r.get('description'),  # (optional)
                            slug=r['slug'],
                            children=[],
                        )
                        topic["children"].append(rtopic)
                        LOGGER.debug('  >>> rtopic = ' + rtopic["slug"])
                        for rchild in r['children']:  # guaranteed to exist
                            LOGGER.debug('      >>>> rchild["slug"] = ' + rchild["slug"])
                            if 'children' not in rchild:
                                # CASE A: two-level replacement hierarchy
                                rchild_ka_node = self.topics_by_slug[rchild['slug']]
                                rchildtopic = self.convert_ka_node_to_ricecooker_node(
                                    rchild_ka_node, target_lang=target_lang)
                                if rchildtopic:
                                    rtopic["children"].append(rchildtopic)
                            else:
                                # CASE B: three-level replacement hierarchy
                                rchildtopic = dict(
                                    kind=content_kinds.TOPIC,
                                    source_id=rchild['slug'],
                                    title=rchild['translatedTitle'],   # guaranteed to exist
                                    description=rchild.get('description'),  # (optional)
                                    slug=rchild['slug'],
                                    children=[],
                                )
                                rtopic["children"].append(rchildtopic)
                                for rgrandchild in rchild['children']:
                                    rgrandchild_slug = rgrandchild['slug']
                                    LOGGER.debug('               >>> rgrandchild_slug = ' + rgrandchild_slug)
                                    rgrandchild_ka_node = self.topics_by_slug[rgrandchild_slug]
                                    rgrandchildtopic = self.convert_ka_node_to_ricecooker_node(
                                        rgrandchild_ka_node, target_lang=target_lang)
                                    if rgrandchildtopic:
                                        rchildtopic["children"].append(rgrandchildtopic)
                else:
                    # This is the more common case (no replacement), just add...
                    child = self.convert_ka_node_to_ricecooker_node(
                        ka_node_child, target_lang=target_lang,
                    )
                    if child:
                        topic["children"].append(child)
            # Skip empty topics
            if topic["children"]:
                return topic
            else:
                return None

        elif isinstance(ka_node, KhanExercise):
            if ka_node.mastery_model in EXERCISE_MAPPING:
                mastery_model = EXERCISE_MAPPING[ka_node.mastery_model]
            else:
                LOGGER.warning(
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
            DUBBED_VIDEOS = DUBBED_VIDEOS_BY_LANG.get(le_target_lang, [])
            target_lang = VIDEO_LANGUAGE_MAPPING.get(target_lang, target_lang)

            if ka_node.youtube_id != ka_node.translated_youtube_id:
                if ka_node.lang != target_lang.lower():
                    LOGGER.info(
                        "Node with youtube id: {} and translated id: {} has wrong language".format(
                            ka_node.youtube_id, ka_node.translated_youtube_id
                        )
                    )
                    return None

            files = [
                dict(
                    file_type="video",
                    youtube_id=ka_node.translated_youtube_id,
                    high_resolution=False,
                    download_settings = {
                        'postprocessors': [
                            {
                                'key': 'ExecAfterDownload',
                                'exec_cmd': 'ffmpeg -hide_banner -loglevel panic -i {} -b:a 32k -ac 1 {}_tmp.mp4 && mv {}_tmp.mp4 {}',
                            }
                        ]
                    }
                )
            ]

            # Find all subtitles that are available for this video
            subtitle_languages = get_subtitle_languages(ka_node.translated_youtube_id)

            # if we dont have video in target lang or subtitle not available in target lang, return None
            if ka_node.lang != target_lang.lower():
                if ka_node.translated_youtube_id in DUBBED_VIDEOS:
                    pass  # videos known to be transalted and should be included
                elif not any(should_include_subtitle(sub_code, le_target_lang) for sub_code in subtitle_languages):
                    LOGGER.error("Untranslated video {} and no subs available. Skipping.".format(ka_node.translated_youtube_id))
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
                        LOGGER.debug(
                            'Skipping subs with lang_code {} for video {}'.format(
                                lang_code, ka_node.translated_youtube_id))

            # convert KA's license format into our internal license classes
            if ka_node.license in LICENSE_MAPPING:
                license = LICENSE_MAPPING[ka_node.license]
            else:
                # license = licenses.CC_BY_NC_SA # or?
                LOGGER.error("Unknown license ({}) on video with youtube id: {}".format(
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




if __name__ == "__main__":
    chef = KhanAcademySushiChef()
    chef.main()

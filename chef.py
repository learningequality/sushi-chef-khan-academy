#!/usr/bin/env python
import logging
import os
import copy

import youtube_dl
from khan import (KhanArticle, KhanExercise, KhanTopic, KhanVideo,
                  get_khan_topic_tree)
from le_utils.constants import exercises
from le_utils.constants.languages import getlang, getlang_by_name
from ricecooker.chefs import SushiChef
from ricecooker.classes import licenses, nodes
from ricecooker.classes.files import (VideoFile, YouTubeSubtitleFile,
                                      YouTubeVideoFile, is_youtube_subtitle_file_supported_language)
from ricecooker.classes.questions import PerseusQuestion

i = 0
while os.path.exists("sushi_khan_academy{}.log".format(i)):
    i += 1

logging.basicConfig(filename='sushi_khan_academy{}.log'.format(i), filemode='w', level=logging.DEBUG)

logger = logging.getLogger("root")
logger.setLevel(logging.DEBUG)

LICENSE_MAPPING = {
    "CC BY": licenses.CC_BYLicense(copyright_holder="Khan Academy"),
    "CC BY-NC": licenses.CC_BY_NCLicense(copyright_holder="Khan Academy"),
    "CC BY-NC-ND": licenses.CC_BY_NC_NDLicense(copyright_holder="Khan Academy"),
    "CC BY-NC-SA (KA default)": licenses.CC_BY_NC_SALicense(copyright_holder="Khan Academy"),
    "CC BY-SA": licenses.CC_BY_SALicense(copyright_holder="Khan Academy"),
    "Non-commercial/non-Creative Commons (College Board)": licenses.SpecialPermissionsLicense(copyright_holder="Khan Academy", description="Non-commercial/non-Creative Commons (College Board)"),
    # "Standard Youtube": licenses.ALL_RIGHTS_RESERVED,
}

EXERCISE_MAPPING = {
    "do-all": exercises.DO_ALL,
    "skill-check": exercises.SKILL_CHECK,
    "num_problems_4": {"mastery_model": exercises.M_OF_N, 'm': 3, 'n': 4},
    "num_problems_7": {"mastery_model": exercises.M_OF_N, 'm': 5, 'n': 7},
    "num_problems_14": {"mastery_model": exercises.M_OF_N, 'm': 10, 'n': 14},
    "num_correct_in_a_row_2": {"mastery_model": exercises.NUM_CORRECT_IN_A_ROW_2},
    "num_correct_in_a_row_3": {"mastery_model": exercises.NUM_CORRECT_IN_A_ROW_3},
    "num_correct_in_a_row_5": {"mastery_model": exercises.NUM_CORRECT_IN_A_ROW_5},
    "num_correct_in_a_row_10": {"mastery_model": exercises.NUM_CORRECT_IN_A_ROW_10}
}

SLUG_BLACKLIST = ["new-and-noteworthy", "talks-and-interviews", "coach-res"]  # not relevant
SLUG_BLACKLIST += ["cs", "towers-of-hanoi"]  # not (yet) compatible
# SLUG_BLACKLIST += ["cc-third-grade-math", "cc-fourth-grade-math", "cc-fifth-grade-math", "cc-sixth-grade-math",
#                    "cc-seventh-grade-math", "cc-eighth-grade-math"]  # common core
SLUG_BLACKLIST += ["MoMA", "getty-museum", "stanford-medicine", "crash-course1", "mit-k12", "hour-of-code",
                   "metropolitan-museum", "bitcoin", "tate", "crash-course1", "crash-course-bio-ecology",
                   "british-museum", "aspeninstitute", "asian-art-museum", "amnh", "nova"]  # partner content

# TODO(jamalex): re-check these videos later and remove them from here if they've recovered
# SLUG_BLACKLIST += ["mortgage-interest-rates", "factor-polynomials-using-the-gcf", "inflation-overview",
#                    "time-value-of-money", "changing-a-mixed-number-to-an-improper-fraction",
#                    "applying-the-metric-system"]  # errors on video downloads


class KhanAcademySushiChef(SushiChef):
    """
    Khan Academy sushi chef.
    """

    def get_channel(self, **kwargs):

        lang_code = kwargs.get("lang", "en")

        lang = getlang(lang_code) or getlang_by_name(lang_code)

        channel = nodes.ChannelNode(
            source_id="KA ({0})".format(lang_code),
            source_domain="khanacademy.org",
            title="Khan Academy ({0})".format(lang.native_name),
            description='Khan Academy content for {}.'.format(lang.name),
            thumbnail="https://upload.wikimedia.org/wikipedia/commons/1/15/Khan_Academy_Logo_Old_version_2015.jpg",
            language=lang
        )

        return channel

    def construct_channel(self, **kwargs):

        # create channel
        channel = self.get_channel(**kwargs)

        # build studio channel out of youtube playlist
        if kwargs.get('youtube_channel_id'):
            return youtube_playlist_scraper(kwargs.get('youtube_channel_id'), channel)

        # build channel through KA API
        lang_code = kwargs.get("lang", "en")
        ka_root_topic = get_khan_topic_tree(lang=lang_code)

        if kwargs.get('english_subtitles'):
            # we will include english videos with target language subtitles
            duplicate_videos(ka_root_topic)

        lang = getlang(lang_code) or getlang_by_name(lang_code)
        lang_code = lang.primary_code
        if lang.subcode:
            lang_code = lang_code + "-" + lang.subcode

        root_topic = convert_ka_node_to_ricecooker_node(ka_root_topic, target_lang=lang_code)

        for topic in root_topic.children:
            channel.add_child(topic)

        return channel


def youtube_playlist_scraper(channel_id, channel):
    ydl = youtube_dl.YoutubeDL({
        'no_warnings': True,
        'writesubtitles': True,
        'allsubtitles': True,
        'ignoreerrors': True,  # Skip over deleted videos in a playlist
        'skip_download': True,
    })
    youtube_channel_url = 'https://www.youtube.com/channel/{}/playlists'.format(channel_id)
    youtube_channel = ydl.extract_info(youtube_channel_url)
    for playlist in youtube_channel['entries']:
        if playlist:
            topic_node = nodes.TopicNode(source_id=playlist['id'],
                                         title=playlist['title'],
                                         description='',
                                         )
            channel.add_child(topic_node)
            entries = []
            for video in playlist['entries']:
                if video and video['id'] not in entries:
                    entries.append(video['id'])
                    files = [YouTubeVideoFile(video['id'])]
                    video_node = nodes.VideoNode(source_id=video['id'],
                                                 title=video['title'],
                                                 description='',
                                                 thumbnail=video['thumbnail'],
                                                 license=LICENSE_MAPPING['CC BY-NC-ND'],
                                                 files=files,
                                                 )
                    topic_node.add_child(video_node)

    return channel

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


def convert_ka_node_to_ricecooker_node(ka_node, target_lang=None):

    if ka_node.slug in SLUG_BLACKLIST:
        return None

    if isinstance(ka_node, KhanTopic):
        topic = nodes.TopicNode(
            source_id=ka_node.id,
            title=ka_node.title,
            description=ka_node.description[:400],
        )
        for ka_subtopic in ka_node.children:
            subtopic = convert_ka_node_to_ricecooker_node(ka_subtopic, target_lang=target_lang)
            if subtopic:
                topic.add_child(subtopic)
        topic.derive_thumbnail()
        if len(topic.children) > 0:
            return topic
        else:
            return None

    elif isinstance(ka_node, KhanExercise):

        if ka_node.mastery_model in EXERCISE_MAPPING:
            mastery_model = EXERCISE_MAPPING[ka_node.mastery_model]
        else:
            logger.warning("Unknown mastery model ({}) for exercise with id: {}".format(ka_node.mastery_model, ka_node.id))
            mastery_model = exercises.M_OF_N

        exercise = nodes.ExerciseNode(
            source_id=ka_node.id,
            title=ka_node.title,
            description=ka_node.description[:400],
            exercise_data=mastery_model,
            license=licenses.SpecialPermissionsLicense(copyright_holder="Khan Academy", description="Permission granted to distribute through Kolibri for non-commercial use"),  # need to formalize with KA
            thumbnail=ka_node.thumbnail,
        )
        for ka_assessment_item in ka_node.get_assessment_items():
            assessment_item = PerseusQuestion(
                id=ka_assessment_item.id,
                raw_data=ka_assessment_item.data,
                source_url=ka_assessment_item.source_url,
            )
            exercise.add_question(assessment_item)
        # if there are no questions for this exercise, return None
        if not exercise.questions:
            return None
        return exercise

    elif isinstance(ka_node, KhanVideo):

        if ka_node.youtube_id != ka_node.translated_youtube_id:
            if ka_node.lang != target_lang.lower():
                logger.error("Node with youtube id: {} and translated id: {} has wrong language".format(ka_node.youtube_id, ka_node.translated_youtube_id))
                return None

        # if download_url is missing, return None for this node
        download_url = ka_node.download_urls.get("mp4-low", ka_node.download_urls.get("mp4"))
        if download_url is None:
            logger.error("Download urls are missing for youtube_id: {}".format(ka_node.youtube_id))
            return None

        # for lite languages, replace youtube ids with translated ones
        if ka_node.translated_youtube_id not in download_url:
            download_url = ka_node.download_urls.get("mp4").replace(ka_node.youtube_id, ka_node.translated_youtube_id)

        # TODO: Use traditional compression here to avoid breaking existing KA downloads?
        files = [VideoFile(download_url)]

        # include any subtitles that are available for this video
        subtitle_languages = ka_node.get_subtitle_languages()

        # if we dont have video in target lang or subtitle not available in target lang, return None
        if ka_node.lang != target_lang.lower():
            if target_lang not in subtitle_languages:
                logger.error('Incorrect target language for youtube_id: {}'.format(ka_node.translated_youtube_id))
                return None

        for lang_code in subtitle_languages:
            if is_youtube_subtitle_file_supported_language(lang_code):
                if target_lang == 'en':
                    files.append(YouTubeSubtitleFile(ka_node.translated_youtube_id, language=lang_code))
                elif lang_code == target_lang:
                    files.append(YouTubeSubtitleFile(ka_node.translated_youtube_id, language=lang_code))

        # convert KA's license format into our own license classes
        if ka_node.license in LICENSE_MAPPING:
            license = LICENSE_MAPPING[ka_node.license]
        else:
            # license = licenses.CC_BY_NC_SA # or?
            logger.error("Unknown license ({}) on video with youtube id: {}".format(ka_node.license, ka_node.translated_youtube_id))
            return None

        video = nodes.VideoNode(
            source_id=ka_node.translated_youtube_id if '-dubbed(KY)' in ka_node.title else ka_node.youtube_id,
            title=ka_node.title,
            description=ka_node.description[:400],
            license=license,
            thumbnail=ka_node.thumbnail,
            files=files,
        )

        return video

    elif isinstance(ka_node, KhanArticle):
        # TODO
        return None


if __name__ == '__main__':
    chef = KhanAcademySushiChef()
    chef.main()

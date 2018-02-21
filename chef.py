#!/usr/bin/env python
import logging

from khan import (KhanArticle, KhanExercise, KhanTopic, KhanVideo,
                  get_khan_topic_tree)
from le_utils.constants.languages import getlang, getlang_by_name
from ricecooker.chefs import SushiChef
from ricecooker.classes import licenses, nodes, questions
from ricecooker.classes.files import VideoFile, YouTubeSubtitleFile
from ricecooker.classes.questions import PerseusQuestion

logging.basicConfig(filename='sushi_khan_academy.log', filemode='w', level=logging.DEBUG)

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
            source_id="KA ({0}) hooplah".format(lang_code),
            source_domain="khanacademy.org-test",
            title="Khan Academy ({0}) - TEST".format(lang.native_name),
            description='Khan Academy content for {}.'.format(lang.name),
            thumbnail="https://upload.wikimedia.org/wikipedia/commons/1/15/Khan_Academy_Logo_Old_version_2015.jpg",
            language=lang
        )

        return channel

    def construct_channel(self, **kwargs):

        # create channel
        channel = self.get_channel(**kwargs)

        lang_code = kwargs.get("lang", "en")
        ka_root_topic = get_khan_topic_tree(lang=lang_code)

        lang_code = getlang(lang_code) or getlang_by_name(lang_code)
        root_topic = convert_ka_node_to_ricecooker_node(ka_root_topic, target_lang=lang_code.primary_code)

        for topic in root_topic.children:
            channel.add_child(topic)

        return channel


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
        exercise = nodes.ExerciseNode(
            source_id=ka_node.id,
            title=ka_node.title,
            description=ka_node.description[:400],
            # exercise_data={'mastery_model': node.get('suggested_completion_criteria')},
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

        # if download_url is missing, return None for this node
        download_url = ka_node.download_urls.get("mp4-low", ka_node.download_urls.get("mp4"))
        if download_url is None:
            logger.warning("Download urls are missing for youtube_id: {}".format(ka_node.youtube_id))
            return None

        # for lite languages, replace youtube ids with translated ones
        if ka_node.translated_youtube_id not in download_url:
            download_url = ka_node.download_urls.get("mp4").replace(ka_node.youtube_id, ka_node.translated_youtube_id)

        # TODO: Use traditional compression here to avoid breaking existing KA downloads?
        files = [VideoFile(download_url)]

        # include any subtitles that are available for this video
        subtitle_languages = ka_node.get_subtitle_languages()

        # if we dont have video in target lang or subtitle not available in target lang, return None
        if ka_node.lang != target_lang:
            if target_lang not in subtitle_languages:
                logger.warning('Incorrect target language for youtube_id: {}'.format(ka_node.translated_youtube_id))
                return None

        for lang_code in subtitle_languages:
            if target_lang == 'en':
                files.append(YouTubeSubtitleFile(ka_node.translated_youtube_id, language=lang_code))
            elif lang_code == target_lang:
                files.append(YouTubeSubtitleFile(ka_node.translated_youtube_id, language=lang_code))

        # convert KA's license format into our own license classes
        if ka_node.license in LICENSE_MAPPING:
            license = LICENSE_MAPPING[ka_node.license]
        else:
            # license = licenses.CC_BY_NC_SA # or?
            logger.error("Unknown license ({}) on video with youtube id {}".format(ka_node.license, ka_node.translated_youtube_id))
            return None

        video = nodes.VideoNode(
            source_id=ka_node.youtube_id,
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

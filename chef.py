#!/usr/bin/env python

from le_utils.constants.languages import getlang
from ricecooker.chefs import SushiChef
from ricecooker.classes import nodes, questions, licenses

from .khan import get_khan_topic_tree


LICENSE_MAPPING = {
    "CC BY": licenses.CC_BYLicense(copyright_holder="Khan Academy"),
    "CC BY-NC": licenses.CC_BY_NCLicense,
    "CC BY-NC-ND": licenses.CC_BY_NC_NDLicense,
    "CC BY-NC-SA (KA default)": licenses.CC_BY_NC_SALicense,
    "CC BY-SA": licenses.CC_BY_SALicense,
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

        lang = getlang(lang_code)

        channel = nodes.ChannelNode(
            source_id="KA ({0})".format(lang_code),
            source_domain="khanacademy.org-test",
            title="Khan Academy ({0}) - TEST".format(lang.native_name),
            description='Khan Academy content for {}.'.format(lang.name),
            thumbnail="https://upload.wikimedia.org/wikipedia/commons/1/15/Khan_Academy_Logo_Old_version_2015.jpg",
        )

        return channel

    def construct_channel(self, **kwargs):

        # create channel
        channel = self.get_channel(**kwargs)

        lang_code = kwargs.get("lang", "en")

        ka_root_topic = get_khan_topic_tree(lang=lang_code)

        root_topic = convert_ka_node_to_ricecooker_node(ka_root_topic, lang=lang_code)

        for topic in root_topic.children:
            channel.add_child(topic)

        return channel


def convert_ka_node_to_ricecooker_node(ka_node):

    if ka_node.slug in SLUG_BLACKLIST:
        return None

    if isinstance(ka_node, KhanTopic):
        topic = nodes.TopicNode(
            source_id=ka_node.id,
            title=ka_node.title,
            description=ka_node.description[:400],
        )
        for ka_subtopic in ka_node.children:
            subtopic = convert_ka_node_to_ricecooker_node(ka_subtopic)
            if subtopic:
                topic.add_child(subtopic)
        return topic
    
    elif isinstance(ka_node, KhanExercise):
        exercise = nodes.ExerciseNode(
            source_id=ka_node.id,
            title=ka_node.title,
            description=ka_node.description[:400],
            # exercise_data={'mastery_model': node.get('suggested_completion_criteria')},
            license=licenses.SpecialPermissionsLicense(copyright_holder="Khan Academy", description="Permission granted to distribute through Kolibri for non-commercial use"),  # need to formalize with KA
            thumbnail=node.thumbnail,
        )
        for ka_assessment_item in ka_node.get_assessment_items():
            assessment_item = PerseusQuestion(
                id=assessment_item.id,
                raw_data=assessment_item.data,
                source_url=assessment_item.source_url,
            )
            exercise.add_question(assessment_item)
        return exercise

    elif isinstance(ka_node, KhanVideo):
        
        # TODO: Use traditional compression here to avoid breaking existing KA downloads?
        files = [VideoFile(ka_node.download_urls.get("mp4-low", ka_node.download_urls.get("mp4")))]
        
        # if the video is in English, include any subtitles available along with it
        if ka_node.lang == "en":
            for lang_code in ka_node.get_subtitle_languages():
                files.append(YouTubeSubtitleFile(node.id, language=lang_code))
    
        # convert KA's license format into our own license classes
        if ka_node.license in LICENSE_MAPPING:
            license = LICENSE_MAPPING[ka_node.license]
        else:
            # license = licenses.CC_BY_NC_SA # or?
            raise Exception("Unknown license on video {}: {}".format(ka_node.id, ka_node.license))

        video = nodes.VideoNode(
            source_id=ka_node.id,
            title=ka_node.title,
            description=ka_node.description[:400],
            license=license,
            thumbnail=node.thumbnail,
            files=files,
        )

        return video

    elif isinstance(ka_node, KhanArticle):
        # TODO
        return None


if __name__ == '__main__':
    chef = KhanAcademySushiChef()
    chef.main()
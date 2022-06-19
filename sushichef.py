#!/usr/bin/env python
import os

from le_utils.constants import content_kinds, exercises, licenses
from le_utils.constants.languages import getlang
from ricecooker.chefs import JsonTreeChef
from ricecooker.classes.nodes import ChannelNode
from ricecooker.config import LOGGER
from ricecooker.utils.jsontrees import write_tree_to_json_tree

from common_core_tags import generate_common_core_mapping
from constants import VIDEO_LANGUAGE_MAPPING
from constants import INVERSE_VIDEO_LANGUAGE_MAPPING
from constants import get_channel_title
from constants import get_channel_description
from curation import get_slug_blacklist
from curation import get_topic_tree_replacements
from network import get_subtitles

from tsvkhan import KhanArticle, KhanExercise, KhanTopic, KhanVideo, get_khan_topic_tree



LICENSE_MAPPING = {
    # OLD KEYS
    "CC BY": dict(license_id=licenses.CC_BY, copyright_holder="Khan Academy"),
    "CC BY-NC": dict(license_id=licenses.CC_BY_NC, copyright_holder="Khan Academy"),
    "CC BY-NC-ND": dict(license_id=licenses.CC_BY_NC_ND, copyright_holder="Khan Academy"),
    "CC BY-NC-SA (KA default)": dict(license_id=licenses.CC_BY_NC_SA, copyright_holder="Khan Academy"),
    "CC BY-SA": dict(license_id=licenses.CC_BY_SA, copyright_holder="Khan Academy"),
    "Non-commercial/non-Creative Commons (College Board)": dict(
        license_id=licenses.SPECIAL_PERMISSIONS,
        copyright_holder="Khan Academy",
        description="Non-commercial/non-Creative Commons (College Board)",
    ),
    # "Standard Youtube": licenses.ALL_RIGHTS_RESERVED,  # warn and skip these
    #
    #
    #
    # NEW KEYS
    'cc-by-nc-nd': dict(license_id=licenses.CC_BY_NC_ND, copyright_holder="Khan Academy"),
    'cc-by-nc-sa': dict(license_id=licenses.CC_BY_NC_SA, copyright_holder="Khan Academy"),
    'cb-ka-copyright': dict(
        license_id=licenses.SPECIAL_PERMISSIONS,
        copyright_holder="Khan Academy",
        description="Non-commercial/non-Creative Commons (College Board)",
    ),
    # 'yt-standard': licenses.ALL_RIGHTS_RESERVED,  # warn and skip these
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

        LOGGER.info("Downloading KA topic tree")
        # Obtain the complete topic tree for lang=lang from the KA API
        ka_root_topic, topics_by_slug = get_khan_topic_tree(lang=lang)
        # TODO: discuss w @kollivier introducing "archive" step here (for source diffs)
        self.topics_by_slug = topics_by_slug  # to be used for topic replacments
        self.slug_blacklist = get_slug_blacklist(lang=lang, variant=variant)
        self.topic_replacements = get_topic_tree_replacements(lang=lang, variant=variant)

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
                                rchild_ka_node = self.topics_by_slug.get(rchild['slug'])
                                if rchild_ka_node:
                                    if 'translatedTitle' in rchild:
                                        rchild_ka_node.title = rchild['translatedTitle']
                                    rchildtopic = self.convert_ka_node_to_ricecooker_node(
                                        rchild_ka_node, target_lang=target_lang)
                                    if rchildtopic:
                                        rtopic["children"].append(rchildtopic)
                                else:
                                    LOGGER.warning('Failed to find rchild slug=' + rchild['slug'])
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
                                    rgrandchild_ka_node = self.topics_by_slug.get(rgrandchild_slug)
                                    if rgrandchild_ka_node:
                                        if 'translatedTitle' in rgrandchild:
                                            rgrandchild_ka_node = rgrandchild['translatedTitle']
                                        rgrandchildtopic = self.convert_ka_node_to_ricecooker_node(
                                            rgrandchild_ka_node, target_lang=target_lang)
                                        if rgrandchildtopic:
                                            rchildtopic["children"].append(rgrandchildtopic)
                                    else:
                                        LOGGER.warning('Failed to find rgrandchild slug=' + rgrandchild_slug)
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
                mastery_model = EXERCISE_MAPPING["do-all"]

            # common core tags
            tags = []
            if ka_node.slug in CC_MAPPING:
                tags.append(CC_MAPPING[ka_node.slug])

            exercise = dict(
                kind=content_kinds.EXERCISE,
                source_id=ka_node.slug,
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
                    path=ka_node.download_url,
                    ffmpeg_settings={
                        "max_height": 480,
                    }
                )
            ]
            if ka_node.subbed:
                for lang_code, path in get_subtitles(ka_node.translated_youtube_id, target_lang):
                    files.append(
                        dict(
                            file_type="subtitles",
                            path=path,
                            language=INVERSE_VIDEO_LANGUAGE_MAPPING.get(lang_code, lang_code),
                        )
                    )

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
                # POLICY: set the `source_id` based on the `youtube_id` of the
                # original English video and not the `translated_youtube_id`:
                source_id=ka_node.youtube_id,
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

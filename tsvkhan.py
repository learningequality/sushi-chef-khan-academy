#!/usr/bin/env python
"""
Logic for parsing the "flat" lists of TSV data from Khan Academy and
converting to a topic tree of ricecooker classes.
"""
import argparse
import csv
from google.cloud import storage
from html2text import html2text
from itertools import groupby
import json
from operator import itemgetter
import os

from le_utils.constants import exercises, file_formats, format_presets

from ricecooker.config import LOGGER
from ricecooker.classes.files import RemoteFile
from ricecooker.classes.files import SubtitleFile
from ricecooker.classes.files import VideoFile
from ricecooker.classes.licenses import SpecialPermissionsLicense
from ricecooker.classes.nodes import VideoNode
from ricecooker.classes.nodes import ExerciseNode
from ricecooker.classes.nodes import TopicNode
from ricecooker.classes.questions import PerseusQuestion
from ricecooker.config import LOGGER
from ricecooker.utils.youtube import get_language_with_alpha2_fallback

from common_core_tags import CC_MAPPING
from constants import SUPPORTED_LANGS, ASSESSMENT_LANGUAGE_MAPPING, KHAN_ACADEMY_LANGUAGE_MAPPING
from constants import VIDEO_LANGUAGE_MAPPING
from constants import LICENSE_MAPPING
from curation import get_slug_blacklist
from curation import get_topic_tree_replacements
from crowdin import retrieve_translations
from kolibridb import get_nodes_for_remote_files
from network import post_request
from network import get_subtitles

translations = {}

TOPIC_LIKE_KINDS = ["Domain", "Course", "Unit", "Lesson"]
SUPPORTED_KINDS = TOPIC_LIKE_KINDS + ["Exercise", "Video"]
UNSUPPORTED_KINDS = ["Article", "Interactive"]
UNSUPPORTED_KINDS += ["TopicQuiz", "TopicUnitTest"]            # exercise-like
UNSUPPORTED_KINDS += ["Challenge", "Project", "Talkthrough"]   # scratchpad-like

KHAN_TSV_EXPORT_BUCKET_NAME = "public-content-export-data"

KHAN_TSV_CACHE_DIR = os.path.join("chefdata", "khantsvcache")


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


# EXTERNAL API
################################################################################

def get_khan_tsv(lang, update=False):
    """
    Get TSV data export for le-utils language `lang` from the KA exports bucket.
    """
    if lang in KHAN_ACADEMY_LANGUAGE_MAPPING:
        kalang = KHAN_ACADEMY_LANGUAGE_MAPPING[lang]
    else:
        kalang = lang
    filename = 'topic_tree_export.{}.tsv'.format(kalang)
    filepath = os.path.join(KHAN_TSV_CACHE_DIR, filename)
    if os.path.exists(filepath) and not update:
        LOGGER.info('Loaded KA TSV data from cache ' + filepath)
        data = parse_tsv_file(filepath)
    else:
        LOGGER.info('Downloading KA TSV data for kalang=' + kalang)
        if not os.path.exists(KHAN_TSV_CACHE_DIR):
            os.makedirs(KHAN_TSV_CACHE_DIR, exist_ok=True)
        download_latest_tsv_export(kalang, filepath)
        data = parse_tsv_file(filepath)
    return data


class TSVManager:
    def __init__(self, channel, lang="en", variant=None, update=True, onlylisted=True):
        """
        Build the complete topic tree based on the results obtained from the KA API.
        Note this topic tree contains a combined topic strcuture that includes all
        curriculum variants, curation pages, and child data may be in wrong order.
        Returns: tuple (root_node, topics_by_slug) for further processing according
        based on SLUG_BLACKLIST and TOPIC_TREE_REPLACMENTS specified in curation.py.
        """
        if lang == "sw":  # for backward compatibility in case old Swahili code used
            lang = "swa"

        # Get fresh TSV data (combined topics, videos, exercises, etc.)
        self.tree_dict = get_khan_tsv(lang, update=update)  # a {id --> datum} dict

        if lang not in SUPPORTED_LANGS:
            global translations
            translations = retrieve_translations(lang)

        channel_id = channel.channel_id or channel.get_node_id().hex

        self.remote_nodes = get_nodes_for_remote_files(channel_id)
        self.update = update
        self.onlylisted = onlylisted
        self.lang = lang
        self.variant = variant

        # The TSV domains do not appear in sorted order so must sort them manually
        DOMAINS_SORT_ORDER = [
            'math',
            'science',
            'economics-finance-domain',
            'humanities',
            'computing',
            'test-prep',
            'ela',
            'partner-content',
            'college-careers-more',
            'khan-for-educators',
            'kmap',                     # will be skipped later on
            'internal-courses',         # will be skipped later on
            'gtp',                      # will be skipped later on
        ]
        root_children = []
        domains = [row for row in self.tree_dict.values() if row['kind'] == 'Domain']
        domains_by_slug = dict((domain['slug'], domain) for domain in domains)
        for domain_slug in DOMAINS_SORT_ORDER:
            if domain_slug in domains_by_slug:
                domain = domains_by_slug[domain_slug]
                root_children.append({'kind':'Domain', 'id':domain['id']})

        # Build a lookup table {slug --> KhanTopic} to be used for replacement logic
        self.topics_by_slug = {}

        for node in self.tree_dict.values():
            if node["kind"] in TOPIC_LIKE_KINDS:
                self.topics_by_slug[node["slug"]] = node

        self.slug_blacklist = get_slug_blacklist(lang=lang, variant=variant)
        self.topic_replacements = get_topic_tree_replacements(lang=lang, variant=variant)
        for child_pointer in root_children:
            if "id" in child_pointer and child_pointer["id"] in self.tree_dict:
                    child_node = self.tree_dict[child_pointer["id"]]
                    self._recurse_create(channel, child_node)
    
    def _create_replacement_node(self, parent, child):
        fake_child_id = "{}_{}".format(parent["slug"], child["slug"])
        if child["slug"] in self.topics_by_slug:
            child_node = self.topics_by_slug[child["slug"]].copy()
        else:
            child_node = {
                "translated_description_html": "",
                "curriculum_key": "",
                "kind": "Course",
                "listed": True,
            }
        child_node.update({
            "id": fake_child_id,
            "original_title": child.get("translatedTitle", child_node.get("original_title", "")),
            "translated_title": child.get("translatedTitle", child_node.get("translated_title", "")),
            "slug": child["slug"],
        })
        self.tree_dict[fake_child_id] = child_node
        return child_node

    def _recurse_create(self, parent, node):
        """
        Main tree-building function that takes the rows from the TSV data and makes
        a tree out of them. By default we want to process only nodes with
        `listed=True` (onlylisted=True). Use onlylisted=False only for debugging.
        """
        if self.onlylisted and (node['listed'] == False or node['listed'] == None):
            return None   # we want to keep only nodes with `listed=True`
        
        if node["slug"] in self.slug_blacklist:
            return None
        
        if self.variant and node["curriculum_key"] and node["curriculum_key"] != self.variant:
            return None

        # Title info comes form different place if `en` vs. translated trees
        title = node['original_title'] if self.lang=='en' else node['translated_title']
        description_html = node['translated_description_html']

        # Check if crowdin translations for title or description are available:
        if title in translations:
            title = translations[title]
        if description_html in translations:
            description_html = translations[description_html]

        # Let's have plain text description
        # TODO: description_html might contain hyperlinks, so need to remove them
        # see also github.com/learningequality/sushi-chef-khan-academy/issues/4
        if description_html:
            full_description = html2text(description_html, bodywidth=0)
            raw_description = full_description[0:400]
            description = raw_description.replace('\n', ' ').strip()
        else:
            description =  ""

        if node["kind"] == "Exercise":
            slug_no_prefix = node['slug'].replace('e/','')  # remove the `e/`-prefix
            khan_node = KhanExercise(
                node["id"],
                title,
                description,
                slug_no_prefix, # set slug to slug_no_prefix (used for source_id)
                node["thumbnail_url"],
                node["assessment_item_ids"],
                node["suggested_completion_criteria"],
                node["canonical_url"],
                lang=self.lang,
            )
            parent.add_child(khan_node)

        elif node["kind"] in TOPIC_LIKE_KINDS:
            slug = node["slug"]
            if slug in self.topic_replacements:
                replacements = self.topic_replacements.pop(slug)
                for replacement in replacements:
                    children_ids = []
                    r_node = node.copy()
                    for child in replacement["children"]:
                        child_node = self._create_replacement_node(replacement, child)
                        if "children" in child:
                            gchild_ids = []
                            for gchild in child["children"]:
                                gchild_node = self._create_replacement_node(child_node, gchild)
                                gchild_ids.append({"id": gchild_node["id"]})
                            child_node["children_ids"] = gchild_ids
                        children_ids.append({"id": child_node["id"]})

                    r_node["original_title"] = replacement.get("translatedTitle", title)
                    r_node["translated_title"] = replacement.get("translatedTitle", title)
                    r_node["slug"] = replacement.get("slug", slug)
                    r_node["children_ids"] = children_ids
                    self._recurse_create(parent, r_node)
            else:
                khan_node = KhanTopic(
                    slug,   # set topic id to slug (used for source_id later)
                    title,
                    description,
                )
                parent.add_child(khan_node)

                for child_pointer in node.get("children_ids", []):
                    if "id" in child_pointer and child_pointer["id"] in self.tree_dict:
                        child_node = self.tree_dict[child_pointer["id"]]
                        self._recurse_create(khan_node, child_node)
                    else:
                        if "kind" in child_pointer and child_pointer["kind"] not in SUPPORTED_KINDS:
                            # silentry skip unsupported content kinds like Article, Project,
                            # Talkthrough, Challenge, Interactive, TopicQuiz, TopicUnitTest
                            pass
                        else:
                            LOGGER.warning('Missing id=' + child_pointer.get('id') + \
                                ' in children_ids of topic node with id=' + node["id"])
                if not khan_node.children:
                    parent.children.remove(khan_node)

        elif node["kind"] == "Video":
            slug_no_prefix = node['slug'].replace('v/','')  # remove the `v/`-prefix

            # The `translated_youtube_id` attr will be used to create the file later
            if "translated_youtube_id" in node:
                # for dubbed videos
                translated_youtube_id = node["translated_youtube_id"]
            else:
                # for subbed videos and original videos
                translated_youtube_id = node["youtube_id"]

            if not node["download_urls"]:
                LOGGER.warning("Node with youtube id: {} has no download urls".format(translated_youtube_id))
                return None

            # convert KA's license format into our internal license classes
            if node["license"] in LICENSE_MAPPING:
                license = LICENSE_MAPPING[node["license"]]
            else:
                # license = licenses.CC_BY_NC_SA # or?
                LOGGER.error("Unknown license ({}) on video with youtube id: {}".format(
                    node["license"], translated_youtube_id))
                return None

            khan_node = KhanVideo(
                title,
                description,
                node["thumbnail_url"],
                license,
                node["download_urls"],
                node["youtube_id"],  # original English video (used for `source_id` later)
                translated_youtube_id,
                # The en TSV doesn't include these fields, so default to True in this case.
                node.get("subbed", self.lang == "en"),
                node.get("dubbed", self.lang == "en"),
                node.get("dub_subbed", self.lang == "en"),
                lang=self.lang if node.get("dubbed") else node["source_lang"],
            )
            # Add the video to the parent before setting any files, as we need the node id
            # to lookup any potentially pre-existing remote files.
            parent.add_child(khan_node)
            khan_node._set_video_files(self.remote_nodes)
        else:
            if node["kind"] in UNSUPPORTED_KINDS:
                # silentry skip unsupported content kinds like Article, Project,
                # Talkthrough, Challenge, Interactive, TopicQuiz, TopicUnitTest
                pass
            else:
                LOGGER.warning('Unrecognized node kind ' + node["kind"] + ' ' + title)



# EXTRACT (download TSV export files from the KHAN_TSV_EXPORT_BUCKET_NAME)
################################################################################

def list_latest_tsv_exports():
    """
    List the language codes available in the KHAN_TSV_EXPORT_BUCKET_NAME bucket.
    """
    storage_client = storage.Client.create_anonymous_client()
    blobs = storage_client.list_blobs(KHAN_TSV_EXPORT_BUCKET_NAME, prefix='')
    blob_names = [blob.name for blob in blobs]
    exports = []
    for blob_name in blob_names:
        kalang = blob_name.split('-export')[0]
        exports.append((kalang, blob_name))
    return sorted(exports, key=itemgetter(1))


def download_latest_tsv_export(kalang, filepath):
    """
    Download latest TSV data for the language code `kalang` from the exports
    bucket and save it to the local path `filepath`.
    """
    storage_client = storage.Client.create_anonymous_client()
    blobs = storage_client.list_blobs(KHAN_TSV_EXPORT_BUCKET_NAME, prefix=kalang)
    if not blobs:
        raise ValueError('An export for kalang=' + kalang + ' is not available.')
    blob_names = [blob.name for blob in blobs]
    LOGGER.debug('Found a total of ' + str(len(blob_names)) + ' export files.')
    # Get the blob with the most recent export file based on blob name
    # Example blob name: `es-export-2020-07-10T09:54:36+0000.tsv`
    latest_blob_name = sorted(blob_names, reverse=True)[0]
    bucket = storage_client.bucket(KHAN_TSV_EXPORT_BUCKET_NAME)
    blob = bucket.blob(latest_blob_name)
    blob.download_to_filename(filepath)
    LOGGER.debug("Blob {} downloaded to {}.".format(latest_blob_name, filepath))


def parse_tsv_file(filepath):
    """
    Load data from the TSV file located at `filepath` using csv.DictReader.
    Returns: a dict {id --> datum} of all the rows.
    """
    print('Loading TSV file', filepath)
    data_by_id = {}
    with open(filepath, encoding="utf-8-sig") as tsvfile:
        reader = csv.DictReader(tsvfile, dialect='excel-tab')
        for row in reader:
            if not row['id']:
                raise ValueError("Row with missing id " + str(row))
            try:
                clean_row = clean_tsv_row(row)
                data_by_id[row['id']] = clean_row
            except json.JSONDecodeError as e:
                LOGGER.error('Failed to parse row=' + str(dict(row)))
    return data_by_id


COLUMN_TYPES_MAP = {
    'listed': bool,
    'children_ids': json.loads,
    # 'standards': json.loads,  # not implemented yet, but it will prob. be json
    'duration': int,
    'download_urls': json.loads,
    'prerequisites': json.loads,
    'related_content': json.loads,
    'time_estimate': json.loads,
    'assessment_item_ids': json.loads,
    'subbed': bool,
    'dubbed': bool,
    'dub_subbed': bool,
    # not needed but let's parse as int just for completeness
    'word_count': int,
    'approved_count': int,
    'translated_count': int,
    'word_count_revised': int,
    'approved_count_revised': int,
    'translated_count_revised': int,
}

def clean_tsv_row(row):
    """
    Transform empty strings values to None and map the keys in `COLUMN_TYPES_MAP`
    to the appropriate data types (e.g. parse json string to Python dict value).
    """
    clean_row = {}
    for key, val in row.items():
        if val is None or val == '':
            clean_row[key] = None
        else:
            if key in COLUMN_TYPES_MAP:
                dest_type = COLUMN_TYPES_MAP[key]
                if dest_type == bool:
                    clean_val = True if val == 'True' or val == 'true' else False
                    clean_row[key] = clean_val
                else:
                    clean_row[key] = dest_type(val)
            else:
                clean_row[key] = val.strip()
    return clean_row 



# DATA CLASSES
################################################################################

class KhanTopic(TopicNode):
    def __init__(self, id, title, description):
        super(KhanTopic, self).__init__(
            id,
            title,
            description=description[:400] if description else '',
        )

    def __repr__(self):
        return "Topic Node: {}".format(self.title)


assessment_item_query = """
query LearningEquality_assessmentItems($itemDescriptors: [String]!) {
    assessmentItems(reservedItemDescriptors: $itemDescriptors) {
        id
        itemData
    }
}
"""


class KhanExercise(ExerciseNode):
    def __init__(
        self,
        id,
        title,
        description,
        slug,
        thumbnail,
        assessment_items,
        mastery_model,
        source_url,
        lang="en",
    ):
        self.assessment_items = assessment_items
        self.source_url = source_url
        self.lang = lang
        if mastery_model in EXERCISE_MAPPING:
            mastery_model = EXERCISE_MAPPING[mastery_model]
        else:
            LOGGER.warning(
                "Unknown mastery model ({}) for exercise with id: {}".format(
                    mastery_model, id
                )
            )
            mastery_model = EXERCISE_MAPPING["do-all"]
        # common core tags
        tags = []
        if slug in CC_MAPPING:
            tags.append(CC_MAPPING[slug])

        self.khan_id = id

        super(KhanExercise, self).__init__(
            slug,
            title,
            description=description[:400] if description else '',
            exercise_data=mastery_model,
            license=SpecialPermissionsLicense(
                copyright_holder="Khan Academy",
                description="Permission granted to distribute through Kolibri for non-commercial use",
            ),  # need to formalize with KA
            language=lang,
            thumbnail=thumbnail,
            tags=tags,
        )

    def validate(self):
        self.set_assessment_items()
        super(KhanExercise, self).validate()

    def set_assessment_items(self):
        kalang = ASSESSMENT_LANGUAGE_MAPPING.get(self.language, self.language)
        url = "https://{}.khanacademy.org/graphql/LearningEquality_assessmentItems".format(kalang)
        data = {
            "query": assessment_item_query,
            "variables": {
                "itemDescriptors":["{}|{}".format(self.khan_id, ai_id) for ai_id in self.assessment_items]
            }
        }

        response_data = post_request(url, data)

        if response_data:
            for item in response_data.get("data", {}).get("assessmentItems", []):
                if item["itemData"] and item["itemData"] != "null":
                    assessment_item = PerseusQuestion(
                        item["id"],
                        item["itemData"],
                        source_url=self.source_url,
                    )
                    self.questions.append(assessment_item)

    def __repr__(self):
        return "Exercise Node: {}".format(self.title)


class KhanVideo(VideoNode):
    def __init__(
        self,
        title,
        description,
        thumbnail,
        license,
        download_urls,
        youtube_id,
        translated_youtube_id,
        subbed,
        dubbed,
        dub_subbed,
        lang="en",
    ):
        super(KhanVideo, self).__init__(
            # POLICY: set the `source_id` based on the `youtube_id` of the
            # original English video and not the `translated_youtube_id`:
            youtube_id,
            title,
            description=description[:400] if description else '',
            license=license,
            thumbnail=thumbnail,
            language=lang,
        )
        self.license = license
        self.thumbnail = thumbnail
        self.high_res_video = None
        self.low_res_video = None
        self.low_res_ios_video = None
        for durl in download_urls:
            if durl['filetype'] == "mp4":
                self.high_res_video = durl["url"]
            if durl['filetype'] == "mp4-low":
                self.low_res_video = durl["url"]
            if durl['filetype'] == "mp4-low-ios":
                self.low_res_ios_video = durl["url"]
        self.youtube_id = youtube_id
        self.translated_youtube_id = translated_youtube_id
        self.subbed = subbed
        self.dubbed = dubbed
        self.dub_subbed = dub_subbed
        self.lang = lang

    @property
    def download_url(self):
        return self.high_res_video or self.low_res_video or self.low_res_ios_video

    def __repr__(self):
        return "Video Node: {}".format(self.title)
    
    def _set_video_files(self, remote_nodes):
        video_node_id = self.get_node_id().hex

        remote_node_files = remote_nodes.get(video_node_id, {}).get("files", [])

        remote_files = False

        for file in remote_node_files:
            if file["preset"] == format_presets.VIDEO_HIGH_RES or file["preset"] == format_presets.VIDEO_LOW_RES:
                remote_file = RemoteFile(
                    file["checksum"],
                    file["extension"],
                    file["preset"],
                    is_primary=True,
                )
                self.add_file(remote_file)
                remote_files = True

        if not remote_files:
            # If we didn't find any pre-existing remote files, add a file for download here.
            self.add_file(
                VideoFile(
                    self.download_url,
                    ffmpeg_settings={
                        "max_height": 480,
                    }
                )
            )

        if self.subbed:
            target_lang = VIDEO_LANGUAGE_MAPPING.get(self.lang, self.lang)
            for lang_code, path in get_subtitles(self.translated_youtube_id):
                lang_obj = get_language_with_alpha2_fallback(lang_code)
                if lang_obj is not None and (lang_code == target_lang or self.dub_subbed):
                    self.add_file(
                        SubtitleFile(
                            path,
                            language=lang_obj.code,
                            subtitlesformat=file_formats.VTT,
                        )
                    )


# REPORTS
################################################################################

def report_from_raw_data(lang, tree_dict):
    """
    Basic report on raw, flat data from the API (not parsed into a tree yet).
    Counts not representative since they include listed=False and listed=None.
    """
    report = {'lang': lang}

    # general counts
    sorted_items = sorted(tree_dict.values(), key=itemgetter('kind'))
    nodes_by_kind = dict((k, list(g)) for k, g in groupby(sorted_items, key=itemgetter('kind')))
    report['#TSV rows of Topics'] = 0
    for kind in SUPPORTED_KINDS:
        report['#TSV rows of ' + kind] = len(nodes_by_kind.get(kind, []))
        if kind in TOPIC_LIKE_KINDS:
            report['#TSV rows of Topics'] = report['#TSV rows of Topics'] + len(nodes_by_kind.get(kind, []))
    for kind in UNSUPPORTED_KINDS:
        report['#TSV rows of ' + kind + ' (unsupported)'] = len(nodes_by_kind.get(kind, []))

    # video stats
    translated_videos = []
    untranslated_videos = []
    dubbed_videos = []
    subbed_videos = []
    dub_subbed_videos = []
    has_mp4 = []
    has_mp4_low = []
    has_mp4_low_ios = []
    for v in nodes_by_kind['Video']:
        vid = v['id']
        if v.get('dubbed'):
            dubbed_videos.append(vid)
        if v.get('subbed'):
            subbed_videos.append(vid)
        if v.get('dub_subbed'):
            dub_subbed_videos.append(vid)
        if v.get('dubbed') or v.get('subbed') or v.get('dub_subbed'):
            translated_videos.append(vid)
        else:
            untranslated_videos.append(vid)

        durls = v['download_urls']
        if durls:
            for durl in durls:
                if durl['filetype'] == "mp4":
                    has_mp4.append(vid)
                if durl['filetype'] == "mp4-low":
                    has_mp4_low.append(vid)
                if durl['filetype'] == "mp4-low-ios":
                    has_mp4_low_ios.append(vid)

    report['#dubbed_videos'] = len(dubbed_videos)
    report['#subbed_videos'] = len(subbed_videos)
    report['#dub_subbed_videos'] = len(dub_subbed_videos)
    report['#translated_videos'] = len(translated_videos)
    report['#untranslated_videos'] = len(untranslated_videos)
    report['#has_mp4'] = len(has_mp4)
    report['#has_mp4_low'] = len(has_mp4_low)
    report['#has_mp4_low_ios'] = len(has_mp4_low_ios)

    # Keys <k> that can be used in https://{lang}.khanacademy.org/?curriculum=<k>
    report['curriculum_keys'] = []
    for node in tree_dict.values():
        if node['kind'] in TOPIC_LIKE_KINDS:
            curriculum = node.get("curriculum_key", None)
            if curriculum and curriculum not in report['curriculum_keys']:
                report['curriculum_keys'].append(curriculum)

    return report




# CLI
################################################################################

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Khan Academy TSV exports viewer')
    parser.add_argument('--latest', action='store_true', help="show only most recent")
    parser.add_argument('--kalang', help="language code filter")
    args = parser.parse_args()

    all_exports = list_latest_tsv_exports()
    exports_by_kalang = dict((k, list(g)) for k, g in groupby(all_exports, key=itemgetter(0)))
    if args.latest:
        for kalang in exports_by_kalang.keys():
            exports_by_kalang[kalang] = [exports_by_kalang[kalang][-1]]

    print('all supported kalang =', sorted(exports_by_kalang.keys()))
    if args.kalang:
        for export in exports_by_kalang[args.kalang]:
            print(export)
    else:
        for kalang, exports in exports_by_kalang.items():
            print('Exports for kalang =', kalang)
            for export in exports:
                print('  -', export[1])

#!/usr/bin/env python
"""
Logic for parsing the "flat" lists of JSON data from the Khan Academy API and
converting to a topic tree of `KhanNode` classes.
"""
import argparse
import csv
from google.cloud import storage
from html2text import html2text
from itertools import groupby
import json
from operator import itemgetter
import os

from ricecooker.config import LOGGER

from constants import SUPPORTED_LANGS, ASSESSMENT_LANGUAGE_MAPPING, KHAN_ACADEMY_LANGUAGE_MAPPING
from crowdin import retrieve_translations
from network import cached_post

translations = {}

TOPIC_LIKE_KINDS = ["Domain", "Course", "Unit", "Lesson"]
SUPPORTED_KINDS = TOPIC_LIKE_KINDS + ["Exercise", "Video"]
UNSUPPORTED_KINDS = ["Article", "Interactive"]
UNSUPPORTED_KINDS += ["TopicQuiz", "TopicUnitTest"]            # exercise-like
UNSUPPORTED_KINDS += ["Challenge", "Project", "Talkthrough"]   # scratchpad-like

KHAN_TSV_EXPORT_BUCKET_NAME = "public-content-export-data"

KHAN_TSV_CACHE_DIR = os.path.join("chefdata", "khantsvcache")


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


def get_khan_topic_tree(lang="en", update=True, onlylisted=True):
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
    tree_dict = get_khan_tsv(lang, update=update)  # a {id --> datum} dict

    if lang not in SUPPORTED_LANGS:
        global translations
        translations = retrieve_translations(lang)


    # The TSV data dows not contain a "root" node so we must manually create one
    root_node = {
        'kind': 'Root',
        'slug': 'root',
        'id': 'x00000000',
        'original_title': 'THE CHANNEL ROOT NODE',
        'translated_title': 'THE CHANNEL ROOT NODE',
        'listed': True,
        'translated_description_html': '',
        'children_ids': [],  # to be filled below
    }

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
    domains = [row for row in tree_dict.values() if row['kind'] == 'Domain']
    domains_by_slug = dict((domain['slug'], domain) for domain in domains)
    for domain_slug in DOMAINS_SORT_ORDER:
        if domain_slug in domains_by_slug:
            domain = domains_by_slug[domain_slug]
            root_node['children_ids'].append({'kind':'Domain', 'id':domain['id']})

    # Build a lookup table {slug --> KhanTopic} to be used for replacement logic
    topics_by_slug = {}

    root = _recurse_create(root_node, tree_dict, topics_by_slug, lang=lang, onlylisted=onlylisted)
    return root, topics_by_slug




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




# TREE-BUILDING LOGIC
################################################################################

def _recurse_create(node, tree_dict, topics_by_slug, lang="en", onlylisted=True):
    """
    Main tree-building function that takes the rows from the TSV data and makes
    a KhanNode tree out of them. By default we want to process only nodes with
    `listed=True` (onlylisted=True). Use onlylisted=False only for debugging.
    """
    if onlylisted and (node['listed'] == False or node['listed'] == None):
        return None   # we want to keep only nodes with `listed=True`

    # Title info comes form different place if `en` vs. translated trees
    title = node['original_title'] if lang=='en' else node['translated_title']
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
            id=slug_no_prefix,   # set id to slug_no_prefix (used for source_id)
            title=title,
            description=description,
            slug=slug_no_prefix,
            thumbnail=node["thumbnail_url"],
            assessment_items=node["assessment_item_ids"],
            mastery_model=node["suggested_completion_criteria"],
            source_url=node["canonical_url"],
            listed=node['listed'],
            lang=lang,
        )
        return khan_node

    elif node["kind"] in TOPIC_LIKE_KINDS or node["kind"] == "Root":
        khan_node = KhanTopic(
            id=node["slug"],   # set topic id to slug (used for source_id later)
            title=title,
            description=description,
            slug=node["slug"],
            lang=lang,
            listed=node['listed'],
            curriculum=node.get("curriculum_key", None),
        )
        topics_by_slug[node["slug"]] = khan_node

        for child_pointer in node.get("children_ids", []):
            if "id" in child_pointer and child_pointer["id"] in tree_dict:
                child_node = tree_dict[child_pointer["id"]]
                child = _recurse_create(child_node, tree_dict, topics_by_slug, lang=lang, onlylisted=onlylisted)
                if child:
                    khan_node.children.append(child)
            else:
                if "kind" in child_pointer and child_pointer["kind"] not in SUPPORTED_KINDS:
                    # silentry skip unsupported content kinds like Article, Project,
                    # Talkthrough, Challenge, Interactive, TopicQuiz, TopicUnitTest
                    pass
                else:
                    LOGGER.warning('Missing id=' + child_pointer.get('id') + \
                        ' in children_ids of topic node with id=' + node["id"])
        return khan_node

    elif node["kind"] == "Video":
        slug_no_prefix = node['slug'].replace('v/','')  # remove the `v/`-prefix

        # The `translated_youtube_id` attr will be used to create the file later
        if "translated_youtube_id" in node:
            # for dubbed videos
            translated_youtube_id = node["translated_youtube_id"]
        else:
            # for subbed videos and original videos
            translated_youtube_id = node["youtube_id"]

        khan_node = KhanVideo(
            id=node["id"],
            title=title,
            description=description,
            slug=slug_no_prefix,
            thumbnail=node["thumbnail_url"],
            license=node["license"],
            download_urls=node["download_urls"],
            youtube_id=node["youtube_id"],  # original English video (used for `source_id` later)
            translated_youtube_id=translated_youtube_id,
            listed=node['listed'],
            lang=lang if node.get("dubbed") else node["source_lang"],
            # TODO(ivan): store subbed, dubbed, and dub_subbed as class attributes
        )
        return khan_node

    elif node["kind"] == "Article":
        slug_no_prefix = node['slug'].replace('a/','')  # remove the `a/`-prefix
        khan_node = KhanArticle(
            id=node["id"],
            title=title,
            description=description,
            slug=slug_no_prefix,
            listed=node['listed'],
            lang=lang,
        )
        return khan_node

    else:
        if node["kind"] in UNSUPPORTED_KINDS:
            # silentry skip unsupported content kinds like Article, Project,
            # Talkthrough, Challenge, Interactive, TopicQuiz, TopicUnitTest
            pass
        else:
            LOGGER.warning('Unrecognized node kind ' + node["kind"] + ' ' + title)



    



# DATA CLASSES
################################################################################

class KhanNode(object):
    """
    Basic container class for the metadata associated with Khan Academy nodes.
    TODO: the following data are available in the TSV exports, but are not used:
      - standards: not currently exported but will be important alignment data
      - prerequisites: not yet supported by ricecooker, woudl be nice to have
      - related_content: not clear where to store this in Kolibri data model
    """
    def __init__(self, id, title, description, slug, listed, lang="en"):
        self.id = id
        self.title = title
        self.description = description
        self.slug = slug
        self.listed = listed
        self.lang = lang

    def __repr__(self):
        return self.title


class KhanTopic(KhanNode):
    def __init__(self, id, title, description, slug, listed, lang="en", curriculum=None):
        super(KhanTopic, self).__init__(id, title, description, slug, listed, lang=lang)
        self.curriculum = curriculum
        self.children = []

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



class KhanExercise(KhanNode):
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
        listed,
        lang="en",
    ):
        super(KhanExercise, self).__init__(id, title, description, slug, listed, lang=lang)
        self.thumbnail = thumbnail
        self.assessment_items = assessment_items
        self.mastery_model = mastery_model
        self.source_url = source_url

    def get_assessment_items(self):
        kalang = ASSESSMENT_LANGUAGE_MAPPING.get(self.lang, self.lang)
        url = "https://{}.khanacademy.org/graphql/LearningEquality_assessmentItems".format(kalang)
        data = {
            "query": assessment_item_query,
            "variables": {
                "itemDescriptors":["{}|{}".format(self.id, ai_id) for ai_id in self.assessment_items]
            }
        }

        response_data = cached_post(url, data)

        if response_data:
            return [KhanAssessmentItem(item["id"], item["itemData"], self.source_url) for item in response_data.get("data", {}).get("assessmentItems", [])]
        return []

    def __repr__(self):
        return "Exercise Node: {}".format(self.title)


class KhanAssessmentItem(object):
    def __init__(self, id, data, source_url):
        self.id = id
        self.data = data
        self.source_url = source_url


class KhanVideo(KhanNode):
    def __init__(
        self,
        id,
        title,
        description,
        slug,
        thumbnail,
        license,
        download_urls,
        youtube_id,
        translated_youtube_id,
        listed,
        lang="en",
    ):
        super(KhanVideo, self).__init__(id, title, description, slug, listed, lang=lang)
        self.license = license
        self.thumbnail = thumbnail
        self.download_urls = download_urls
        self.youtube_id = youtube_id
        self.translated_youtube_id = translated_youtube_id

    def __repr__(self):
        return "Video Node: {}".format(self.title)


class KhanArticle(KhanNode):
    def __init__(self, id, title, description, slug, listed, lang="en"):
        super(KhanArticle, self).__init__(id, title, description, slug, listed, lang=lang)

    def __repr__(self):
        return "Article Node: {}".format(self.title)




# KHAN TREE UTILS
################################################################################

def get_kind(node):
    if isinstance(node, KhanTopic):
        return 'topic'
    elif isinstance(node, KhanExercise):
        return 'exercise'
    elif isinstance(node, KhanVideo):
        return 'video'
    elif isinstance(node, KhanArticle):
        return 'article'
    else:
        return 'unknown kind'




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

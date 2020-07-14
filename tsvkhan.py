"""
Logic for parsing the "flat" lists of JSON data from the Khan Academy API and
converting to a topic tree of `KhanNode` classes.
"""
import csv
from google.cloud import storage
from html2text import html2text
import json
import os

from le_utils.constants.languages import getlang
from ricecooker.config import LOGGER

from constants import ASSESSMENT_URL, SUPPORTED_LANGS, ASSESSMENT_LANGUAGE_MAPPING
from crowdin import retrieve_translations
from dubbed_mapping import generate_dubbed_video_mappings_from_csv
from network import make_request
from utils import get_video_id_english_mappings

translations = {}
video_map = generate_dubbed_video_mappings_from_csv()
english_video_map = get_video_id_english_mappings()

TOPIC_LIKE_KINDS = ["Root", "Domain", "Course", "Unit", "Lesson"]
SUPPORTED_KINDS = TOPIC_LIKE_KINDS + ["Exercise", "Video"]
# UNSUPPORTED_KINDS = ["Article", "Challenge", "Interactive", "Project", "Talkthrough"]


KHAN_TSV_EXPORT_BUCKET_NAME = "public-content-export-data"

KHAN_TSV_CACHE_DIR = os.path.join("chefdata", "khantsvcache")





# EXTERNAL API
################################################################################

def get_khan_api_json(lang, update=False):
    """
    TMP shim to keep the katrees working.
    """
    data = get_khan_tsv(lang)
    print('len(data)', len(data))
    return data


def get_khan_tsv(lang, update=False):
    """
    Get TSV data export for language `lang` from the KA exports bucket.
    """
    filename = 'topic_tree_export.{}.tsv'.format(lang)
    filepath = os.path.join(KHAN_TSV_CACHE_DIR, filename)
    if os.path.exists(filepath) and not update:
        LOGGER.info('Loaded KA TSV data from cache ' + filepath)
        data = parse_tsv_file(filepath)
    else:
        LOGGER.info('Downloading KA TSV data for lang=' + lang)
        if not os.path.exists(KHAN_TSV_CACHE_DIR):
            os.makedirs(KHAN_TSV_CACHE_DIR, exist_ok=True)
        download_latest_tsv_export(lang, filepath)
        data = parse_tsv_file(filepath)
    return data


def get_khan_topic_tree(lang="en", update=True):
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
        translations = retrieve_translations(lang_code=lang)


    # The TSV data dows not contain a "root" node so we must manually create one
    root_node = {
        'kind': 'Root',
        'slug': 'root',
        'id': 'x00000000',
        'original_title': '',
        'translated_title': '',
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

    root = _recurse_create(root_node, tree_dict, topics_by_slug, lang=lang)
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
    langs = set()
    for blob_name in blob_names:
        lang = blob_name.split('-export')[0]
        langs.add(lang)
    return sorted(list(langs))


def download_latest_tsv_export(lang, filepath):
    """
    Download latest TSV data for language `lang` from the KA exports bucket and
    save it to the local path `filepath`.
    """
    storage_client = storage.Client.create_anonymous_client()
    blobs = storage_client.list_blobs(KHAN_TSV_EXPORT_BUCKET_NAME, prefix=lang)
    if not blobs:
        raise ValueError('The export for lang=' + lang + ' is not available.')
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
    # 'standards': json.loads,  # not implemented yet, but guess it will be json
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
                clean_row[key] = COLUMN_TYPES_MAP[key](val)
            else:
                clean_row[key] = val.strip()
    return clean_row

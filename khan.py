"""
Logic for parsing the "flat" lists of JSON data from the Khan Academy API and
converting to a topic tree of `KhanNode` classes.
"""
from collections import OrderedDict
from html2text import html2text
import json
import os

from le_utils.constants.languages import getlang, getlang_by_name
from ricecooker.config import LOGGER

from constants import ASSESSMENT_URL, ASSESSMENT_LANGUAGE_MAPPING
from constants import SUPPORTED_LANGS
from crowdin import retrieve_translations
from dubbed_mapping import generate_dubbed_video_mappings_from_csv
from network import make_request


translations = {}
video_map = generate_dubbed_video_mappings_from_csv()


SUPPORTED_KINDS = ["Topic", "Exercise", "Video"]

KHAN_API_CACHE_DIR = os.path.join("chefdata", "khanapicache")


V2_API_URL = "http://www.khanacademy.org/api/v2/topics/topictree?lang={lang}&projection={projection}"

TOPIC_ATTRIBUTES = [
    'childData',
    'deleted',
    'doNotPublish',
    'hide',
    'id',
    'kind',
    'slug',
    'translatedTitle',
    'translatedDescription',
    'curriculumKey'
]

EXERCISE_ATTRIBUTES = [
    'allAssessmentItems',
    'displayName',
    'fileName',
    'id',
    'kind',
    'name',
    'prerequisites',
    'slug',
    'usesAssessmentItems',
    'relatedContent',
    'translatedTitle',
    'translatedDescription',
    'suggestedCompletionCriteria',
    'kaUrl',
    'imageUrl'
]

VIDEO_ATTRIBUTES = [
    'id',
    'kind',
    'licenseName',
    'slug',
    'youtubeId',
    'translatedYoutubeLang',
    'translatedYoutubeId',
    'translatedTitle',
    'translatedDescription',
    'translatedDescriptionHtml',
    'downloadUrls',
    'imageUrl'
]
# Note (May 2020): we also want `sourceLanguage` but not avail. thorugh /api/v2/

# ARTICLE_ATTRIBUTES = [
#     'id',
#     'kind',
#     'slug',
#     'descriptionHtml',
#     'perseusContent',
#     'title',
#     'imageUrl'
# ]

PROJECTION_KEYS = json.dumps(OrderedDict([
    ("topics", [OrderedDict((key, 1) for key in TOPIC_ATTRIBUTES)]),
    ("exercises", [OrderedDict((key, 1) for key in EXERCISE_ATTRIBUTES)]),
    ("videos", [OrderedDict((key, 1) for key in VIDEO_ATTRIBUTES)]),
    # ("articles", [OrderedDict((key, 1) for key in ARTICLE_ATTRIBUTES)])
]))



# this code moved here to avoid circular imports
from utils import get_video_id_english_mappings
english_video_map = get_video_id_english_mappings()



# EXTERNAL API
################################################################################

def get_khan_api_json(lang, update=False):
    """
    Get all data for language `lang` from the KA API at /api/v2/topics/topictree
    """
    filename = 'khan_academy_json_{}.json'.format(lang)
    filepath = os.path.join(KHAN_API_CACHE_DIR, filename)
    if os.path.exists(filepath) and not update:
        print('Loaded KA API json from cache', filepath)
        data = json.load(open(filepath))
    else:
        print('Downloading KA API json for lang =', lang)
        url = V2_API_URL.format(lang=lang, projection=PROJECTION_KEYS)
        LOGGER.debug('khan API url=' + url)
        response = make_request(url, timeout=120)
        data = response.json()
        if not os.path.exists(KHAN_API_CACHE_DIR):
            os.makedirs(KHAN_API_CACHE_DIR, exist_ok=True)
        json.dump(data, open(filepath, 'w'), ensure_ascii=False, indent=4)
    return data


def get_khan_topic_tree(lang="en", update=False):
    """
    Build the complete topic tree based on the results obtained from the KA API.
    Note this topic tree contains a combined topic strcuture that includes all
    curriculum variants, curation pages, and child data may be in wrong order.
    Returns: tuple (root_node, topics_by_slug) for further processing according
    based on SLUG_BLACKLIST and TOPIC_TREE_REPLACMENTS specified in curation.py.
    """
    if lang == "sw":  # for backward compatibility in case old Swahili code used
        lang = "swa"

    # Get the fresh data from the KA API (do not try to re-use cached data)
    topic_tree = get_khan_api_json(lang, update=update)

    # if name of lang is passed in, get language code
    if getlang(lang) is None and getlang_by_name(lang):
        lang = getlang_by_name(lang).primary_code

    if lang not in SUPPORTED_LANGS:
        global translations
        translations = retrieve_translations(lang)

    # Flatten node_data (combine topics, videos, and exercises in a single list)
    flattened_tree = [node for node_list in topic_tree.values() for node in node_list]

    # Convert to dict with ids as keys (for fast lookups by id)
    tree_dict = {node["id"]: node for node in flattened_tree}

    # Build a lookup table {slug --> KhanTopic} to be used for replacement logic
    topics_by_slug = {}

    root_node = tree_dict["x00000000"]
    root = _recurse_create(root_node, tree_dict, topics_by_slug, lang=lang)

    return root, topics_by_slug


# TREE-BUILDING LOGIC
################################################################################

def _recurse_create(node, tree_dict, topics_by_slug, lang="en"):

    # If CrowdIn translations for title or description are available, load them:
    if node["translatedTitle"] in translations:
        node["translatedTitle"] = translations[node["translatedTitle"]]
    if node["translatedDescription"] in translations:
        node["translatedDescription"] = translations[node["translatedDescription"]]

    if node["kind"] == "Exercise":
        khan_node = KhanExercise(
            id=node["name"],  # set id to name for backwards compatibility
            title=node["translatedTitle"].replace('\xa0', ' ').replace('\n', ' ').strip(),
            description=node["translatedDescription"].replace('\xa0', ' ').replace('\n', ' ').strip(),
            slug=node["slug"],
            thumbnail=node["imageUrl"],
            assessment_items=node["allAssessmentItems"],
            mastery_model=node["suggestedCompletionCriteria"],
            source_url=node["kaUrl"],
            lang=lang,
        )

    elif node["kind"] == "Topic":
        khan_node = KhanTopic(
            id=node["slug"],  # set topic id to slug for backwards compatibility
            title=node["translatedTitle"].replace('\xa0', ' ').replace('\n', ' ').strip(),
            description=node["translatedDescription"].replace('\xa0', ' ').replace('\n', ' ').strip() if node["translatedDescription"] else None,
            slug=node["slug"],
            lang=lang,
            curriculum=node["curriculumKey"] if node["curriculumKey"] else None,
        )
        topics_by_slug[node["slug"]] = khan_node

    elif node["kind"] == "Video":
        name = getlang(lang).name.lower()
        if node["translatedYoutubeLang"] != lang:
            if video_map.get(name):
                if video_map[name].get(node["translatedYoutubeId"]):
                    node["translatedYoutubeId"] = video_map[name].get(
                        node["translatedYoutubeId"]
                    )
                    node["translatedYoutubeLang"] = lang

        if node.get("translatedDescriptionHtml"):
            video_description = html2text(
                translations.get(
                    node["translatedDescriptionHtml"], node["translatedDescriptionHtml"]
                ),
                bodywidth=0
            )[:400]
        elif node.get("translatedDescription"):
            video_description = translations.get(
                node["translatedDescription"], node["translatedDescription"]
            )[:400]
        else:
            video_description = ""
        khan_node = KhanVideo(
            id=node["id"],
            title=node["translatedTitle"].replace('\xa0', ' ').replace('\n', ' ').strip(),
            description=video_description.replace('\xa0', ' ').replace('\n', ' ').strip(),
            slug=node["slug"],
            thumbnail=node["imageUrl"],
            license=node["licenseName"],
            download_urls=node["downloadUrls"],
            # for backwards compatibility, youtubeId is the source_id for chef video nodes
            # these should be the english youtubeIds corresponding to the translated youtubeId
            youtube_id=english_video_map.get(node["id"]) or node["youtubeId"],
            translated_youtube_id=node["translatedYoutubeId"],
            lang=node["translatedYoutubeLang"],
        )

    elif node["kind"] == "Article":
        khan_node = KhanArticle(
            id=node["id"],
            title=node["translatedTitle"],
            description=node["translatedDescription"],
            slug=node["slug"],
            lang=lang,
        )

    for child_pointer in node.get("childData", []):
        if "id" in child_pointer and child_pointer["id"] in tree_dict:
            child_node = tree_dict[child_pointer["id"]]
            child = _recurse_create(child_node, tree_dict, topics_by_slug, lang=lang)
            khan_node.children.append(child)
        else:
            if "kind" in child_pointer and child_pointer["kind"] not in SUPPORTED_KINDS:
                # silentry skip unsupported content kinds like Article, Project,
                # Talkthrough, Challenge, Interactive,  TopicQuiz, TopicUnitTest
                pass
            else:
                LOGGER.warning('Missing id=' + child_pointer.get('id', 'noid') + \
                               ' in childData of topic node with id=' + node["id"])

    return khan_node



# DATA CLASSES
################################################################################

class KhanNode(object):
    def __init__(self, id, title, description, slug, lang="en"):
        self.id = id
        self.title = title
        self.description = description
        self.slug = slug
        self.lang = lang

    def __repr__(self):
        return self.title


class KhanTopic(KhanNode):
    def __init__(self, id, title, description, slug, lang="en", curriculum=None):
        super(KhanTopic, self).__init__(id, title, description, slug, lang=lang)
        self.curriculum = curriculum
        self.children = []

    def __repr__(self):
        return "Topic Node: {}".format(self.title)


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
        lang="en",
    ):
        super(KhanExercise, self).__init__(id, title, description, slug, lang=lang)
        self.thumbnail = thumbnail
        self.assessment_items = assessment_items
        self.mastery_model = mastery_model
        self.source_url = source_url

    def get_assessment_items(self):
        items_list = []
        kalang = ASSESSMENT_LANGUAGE_MAPPING.get(self.lang, self.lang)
        for i in self.assessment_items:
            item_url = ASSESSMENT_URL.format(assessment_item=i["id"], kalang=kalang)
            item = make_request(item_url).json()
            # check if assessment item is fully translated, before adding it to list
            if item["is_fully_translated"]:
                ai = KhanAssessmentItem(item["id"], item["item_data"], self.source_url)
                items_list.append(ai)
        return items_list

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
        lang="en",
    ):
        super(KhanVideo, self).__init__(id, title, description, slug, lang=lang)
        self.license = license
        self.thumbnail = thumbnail
        self.download_urls = download_urls
        self.youtube_id = youtube_id
        self.translated_youtube_id = translated_youtube_id

    def __repr__(self):
        return "Video Node: {}".format(self.title)


class KhanArticle(KhanNode):
    def __init__(self, id, title, description, slug, lang="en"):
        super(KhanArticle, self).__init__(id, title, description, slug, lang=lang)

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

def report_from_raw_data(lang, data):
    """
    Basic report on raw, flat data from the API (not parsed into a tree yet).
    """
    report = {'lang': lang}

    # general counts
    report['#topics'] = len(data['topics'])
    report['#videos'] = len(data['videos'])
    report['#exercises'] = len(data['exercises'])

    # video stats
    translated_videos = []
    untranslated_videos = []
    has_mp4 = []
    has_mp4_low = []
    has_mp4_low_ios = []
    for v in data['videos']:
        vid = v['id']
        if v['translatedYoutubeLang'] != 'en':
            translated_videos.append(vid)
        else:
            untranslated_videos.append(vid)
        durls = v['downloadUrls']
        if 'mp4' in durls:
            has_mp4.append(vid)
        if 'mp4-low' in durls:
            has_mp4_low.append(vid)
        if 'mp4-low-ios' in durls:
            has_mp4_low_ios.append(vid)
    report['#translated_videos'] = len(translated_videos)
    report['#untranslated_videos'] = len(untranslated_videos)
    report['#has_mp4'] = len(has_mp4)
    report['#has_mp4_low'] = len(has_mp4_low)
    report['#has_mp4_low_ios'] = len(has_mp4_low_ios)

    # Keys <k> that can be used in https://{lang}.khanacademy.org/?curriculum=<k>
    report['curriculum_keys'] = []
    for topic in data['topics']:
        curriculum = topic.get("curriculumKey", None)
        if curriculum and curriculum not in report['curriculum_keys']:
            report['curriculum_keys'].append(curriculum)

    return report

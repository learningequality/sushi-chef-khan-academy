from html2text import html2text
import ujson

from le_utils.constants.languages import getlang, getlang_by_name
from pressurecooker.youtube import YouTubeResource
from ricecooker.config import LOGGER

from constants import ASSESSMENT_URL, PROJECTION_KEYS, V2_API_URL, SUPPORTED_LANGS, ASSESSMENT_LANGUAGE_MAPPING
from crowdin import retrieve_translations
from dubbed_mapping import generate_dubbed_video_mappings_from_csv
from network import make_request
from utils import get_video_id_english_mappings

translations = {}
video_map = generate_dubbed_video_mappings_from_csv()
english_video_map = get_video_id_english_mappings()


def get_khan_topic_tree(lang="en"):
    """
    Build the complete topic tree based on the results obtained from the KA API.
    Note this topic tree contains a combined topic strcuture that includes all
    curriculum variants, curation pages, and child data may be in wrong order.
    Returns: tuple (root_node, topics_by_slug) for further processing according
    based on SLUG_BLACKLIST and TOPIC_TREE_REPLACMENTS specified in curation.py
    """
    if lang == "sw":
        response = make_request(
            V2_API_URL.format(lang="swa", projection=PROJECTION_KEYS), timeout=120
        )
    else:
        response = make_request(
            V2_API_URL.format(lang=lang, projection=PROJECTION_KEYS), timeout=120
        )

    topic_tree = ujson.loads(response.content)
    # if name of lang is passed in, get language code
    if getlang_by_name(lang):
        lang = getlang_by_name(lang).primary_code

    if lang not in SUPPORTED_LANGS:
        global translations
        translations = retrieve_translations(lang_code=lang)

    # Flatten node_data (combine topics, videos, and exercises in a single list)
    flattened_tree = [node for node_list in topic_tree.values() for node in node_list]

    # Convert to dict with ids as keys (for fast lookups by id)
    tree_dict = {node["id"]: node for node in flattened_tree}

    # Build a lookup table {slug --> KhanTopic} to be used for replacement logic
    topics_by_slug = {}

    root_node = tree_dict["x00000000"]
    root = _recurse_create(root_node, tree_dict, topics_by_slug, lang=lang)

    return root, topics_by_slug


def _recurse_create(node, tree_dict, topics_by_slug, lang="en"):

    node["translatedTitle"] = translations.get(
        node["translatedTitle"], node["translatedTitle"]
    )
    node["translatedDescription"] = translations.get(
        node["translatedDescription"], node["translatedDescription"]
    )

    if node["kind"] == "Exercise":
        khan_node = KhanExercise(
            id=node["name"],  # set id to name for backwards compatibility
            title=node["translatedTitle"],
            description=node["translatedDescription"],
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
            title=node["translatedTitle"],
            description=node["translatedDescription"],
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
                )
            )[:400]
        elif node.get("translatedDescription"):
            video_description = translations.get(
                node["translatedDescription"], node["translatedDescription"]
            )[:400]
        else:
            video_description = ""
        khan_node = KhanVideo(
            id=node["id"],
            title=node["translatedTitle"],
            description=video_description,
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
            LOGGER.warning('Missing id in childData of node ' + node["id"])

    return khan_node


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
        lang = ASSESSMENT_LANGUAGE_MAPPING.get(self.lang, self.lang)
        for i in self.assessment_items:
            item_url = ASSESSMENT_URL.format(assessment_item=i["id"], lang=lang)
            item = make_request(item_url).json()
            # check if assessment item is fully translated, before adding it to list
            if item["is_fully_translated"]:
                items_list.append(
                    KhanAssessmentItem(item["id"], item["item_data"], self.source_url)
                )

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

    def get_subtitle_languages(self):
        youtube_url = 'https://youtube.com/watch?v=' + self.translated_youtube_id
        yt_resource = YouTubeResource(youtube_url)
        lang_codes = []
        try:
            result = yt_resource.get_resource_subtitles()
            if result:
                for lang_code, lang_subs in result['subtitles'].items():
                    for lang_sub in lang_subs:
                        if 'ext' in lang_sub and lang_sub['ext'] == 'vtt' and lang_code not in lang_codes:
                            lang_codes.append(lang_code)
        except Exception as e:
            print('get_subtitle_languages failed on youtube URL ' + youtube_url)
            print(e)
        return lang_codes

    def __repr__(self):
        return "Video Node: {}".format(self.title)


class KhanArticle(KhanNode):
    def __init__(self, id, title, description, slug, lang="en"):
        super(KhanArticle, self).__init__(id, title, description, slug, lang=lang)

    def __repr__(self):
        return "Article Node: {}".format(self.title)

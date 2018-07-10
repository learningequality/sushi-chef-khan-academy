from urllib.parse import urlparse

import ujson
import youtube_dl
from constants import ASSESSMENT_URL, PROJECTION_KEYS, V2_API_URL
from crowdin import retrieve_translations
from dubbed_mapping import generate_dubbed_video_mappings_from_csv
from html2text import html2text
from le_utils.constants.languages import getlang, getlang_by_name
from network import make_request
from utils import get_video_id_english_mappings
from youtube_dl.extractor import YoutubeIE

translations = {}
video_map = generate_dubbed_video_mappings_from_csv()
english_video_map = get_video_id_english_mappings()


def get_khan_topic_tree(lang="en", curr_key=None):
    if lang == 'sw':
        response = make_request(V2_API_URL.format(lang='swa', projection=PROJECTION_KEYS), timeout=120)
    else:
        response = make_request(V2_API_URL.format(lang=lang, projection=PROJECTION_KEYS), timeout=120)

    topic_tree = ujson.loads(response.content)
    # if name of lang is passed in, get language code
    if getlang_by_name(lang):
        lang = getlang_by_name(lang).primary_code

    if lang != "en":
        global translations
        translations = retrieve_translations(lang_code=lang)

    # Flatten node_data
    flattened_tree = [node for node_list in topic_tree.values() for node in node_list]

    # convert to dict with ids as keys
    tree_dict = {node['id']: node for node in flattened_tree}

    return _recurse_create(tree_dict["x00000000"], tree_dict, lang=lang)


def _recurse_create(node, tree_dict, lang="en"):

        node["translatedTitle"] = translations.get(node["translatedTitle"], node["translatedTitle"])
        node["translatedDescription"] = translations.get(node["translatedDescription"], node["translatedDescription"])

        if node['kind'] == 'Exercise':
            khan_node = KhanExercise(id=node['name'],  # ID is the name of exercise node, for backwards compatibility
                                     title=node["translatedTitle"],
                                     description=node["translatedDescription"],
                                     slug=node['slug'],
                                     thumbnail=node['imageUrl'],
                                     assessment_items=node['allAssessmentItems'],
                                     mastery_model=node['suggestedCompletionCriteria'],
                                     source_url=node['kaUrl'],
                                     lang=lang)
        elif node['kind'] == 'Topic':
            khan_node = KhanTopic(id=node['slug'],  # ID is the slug of topic node, for backwards compatibility
                                  title=node["translatedTitle"],
                                  description=node["translatedDescription"],
                                  slug=node['slug'],
                                  lang=lang)
        elif node['kind'] == 'Video':

            name = getlang(lang).name.lower()
            if node['translatedYoutubeLang'] != lang:
                if video_map.get(name):
                    if video_map[name].get(node['translatedYoutubeId']):
                        node['translatedYoutubeId'] = video_map[name].get(node['translatedYoutubeId'])
                        node['translatedYoutubeLang'] = lang

            if node.get('translatedDescriptionHtml'):
                video_description = html2text(translations.get(node["translatedDescriptionHtml"], node["translatedDescriptionHtml"]))[:400]
            elif node.get('translatedDescription'):
                video_description = translations.get(node["translatedDescription"], node["translatedDescription"])[:400]
            else:
                video_description = ''
            khan_node = KhanVideo(id=node['id'],
                                  title=node["translatedTitle"],
                                  description=video_description,
                                  slug=node['slug'],
                                  thumbnail=node['imageUrl'],
                                  license=node['licenseName'],
                                  download_urls=node['downloadUrls'],
                                  # for backwards compatibility, youtubeId is the source_id for chef video nodes
                                  # these should be the english youtubeIds corresponding to the translated youtubeId
                                  youtube_id=english_video_map.get(node['id']) or node['youtubeId'],
                                  translated_youtube_id=node['translatedYoutubeId'],
                                  lang=node['translatedYoutubeLang'])
        elif node['kind'] == 'Article':
            khan_node = KhanArticle(id=node['id'],
                                    title=node["translatedTitle"],
                                    description=node["translatedDescription"],
                                    slug=node['slug'],
                                    lang=lang)

        for c in node.get('childData', []):
            # if key is missing, we don't add it to list of children of topic node
            try:
                child_node = tree_dict[c['id']]
                khan_node.children.append(_recurse_create(child_node, tree_dict, lang=lang))
            except KeyError:
                pass

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

    def __init__(self, id, title, description, slug, lang="en"):
        super(KhanTopic, self).__init__(id, title, description, slug, lang=lang)
        self.children = []

    def __repr__(self):
        return "Topic Node: {}".format(self.title)


class KhanExercise(KhanNode):

    def __init__(self, id, title, description, slug, thumbnail, assessment_items, mastery_model, source_url, lang="en"):
        super(KhanExercise, self).__init__(id, title, description, slug, lang=lang)
        self.thumbnail = thumbnail
        self.assessment_items = assessment_items
        self.mastery_model = mastery_model
        self.source_url = source_url

    def get_assessment_items(self):
        items_list = []
        for i in self.assessment_items:
            item_url = ASSESSMENT_URL.format(assessment_item=i['id'], lang=self.lang)
            item = make_request(item_url).json()
            # check if assessment item is fully translated, before adding it to list
            if item['is_fully_translated']:
                items_list.append(KhanAssessmentItem(item['id'], item['item_data'], self.source_url))

        return items_list

    def __repr__(self):
        return "Exercise Node: {}".format(self.title)


class KhanAssessmentItem(object):

    def __init__(self, id, data, source_url):
        self.id = id
        self.data = data
        self.source_url = source_url


class KhanVideo(KhanNode):

    def __init__(self, id, title, description, slug, thumbnail, license, download_urls, youtube_id, translated_youtube_id, lang="en"):
        super(KhanVideo, self).__init__(id, title, description, slug, lang=lang)
        self.license = license
        self.thumbnail = thumbnail
        self.download_urls = download_urls
        self.youtube_id = youtube_id
        self.translated_youtube_id = translated_youtube_id

    def get_subtitle_languages(self):
        with youtube_dl.YoutubeDL({"listsubtitles": True}) as ydl:
            try:
                return list(YoutubeIE(ydl).extract(self.translated_youtube_id)["subtitles"].keys())
            except youtube_dl.utils.ExtractorError:
                return []

    def __repr__(self):
        return "Video Node: {}".format(self.title)


class KhanArticle(KhanNode):

    def __init__(self, id, title, description, slug, lang="en"):
        super(KhanArticle, self).__init__(id, title, description, slug, lang=lang)

    def __repr__(self):
        return "Article Node: {}".format(self.title)

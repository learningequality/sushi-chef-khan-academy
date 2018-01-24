import requests
import ujson
import youtube_dl
from constants import ASSESSMENT_URL, PROJECTION_KEYS, V2_API_URL
from html2text import html2text
from ricecooker.utils.caching import (CacheControlAdapter,
                                      CacheForeverHeuristic, FileCache,
                                      InvalidatingCacheControlAdapter)
from youtube_dl.extractor import YoutubeIE

sess = requests.Session()
cache = FileCache('.webcache')
forever_adapter = CacheControlAdapter(heuristic=CacheForeverHeuristic(), cache=cache)

sess.mount('http://www.khanacademy.org/api/v2/topics/topictree', forever_adapter)
sess.mount('http://www.khanacademy.org/api/v1/assessment_items/', forever_adapter)
# sess.mount('https://api.crowdin.com', forever_adapter)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive"
}


def get_khan_topic_tree(lang="en", curr_key=None):
    response = sess.get(V2_API_URL.format(lang=lang, projection=PROJECTION_KEYS), headers=headers)
    if response.status_code != 200:
        raise requests.RequestException('Downloading topic tree failed.')
    topic_tree = ujson.loads(response.content)

    # Flatten node_data
    flattened_tree = [node for node_list in topic_tree.values() for node in node_list]

    # convert to dict with ids as keys
    tree_dict = {node['id']: node for node in flattened_tree}

    return _recurse_create(tree_dict["x00000000"], tree_dict, lang=lang)


def _recurse_create(node, tree_dict, lang="en"):

        if node['kind'] == 'Exercise':
            khan_node = KhanExercise(id=node['name'],  # ID is the name of exercise node, for backwards compatibility
                                     title=node['translatedTitle'],
                                     description=node['translatedDescription'],
                                     slug=node['slug'],
                                     thumbnail=node['imageUrl'],
                                     assessment_items=node['allAssessmentItems'],
                                     source_url=node['kaUrl'],
                                     lang=lang)
        elif node['kind'] == 'Topic':
            khan_node = KhanTopic(id=node['slug'],  # ID is the slug of topic node, for backwards compatibility
                                  title=node['translatedTitle'],
                                  description=node['translatedDescription'],
                                  slug=node['slug'],
                                  lang=lang)
        elif node['kind'] == 'Video':
            if node.get('translatedDescriptionHtml'):
                video_description = html2text(node.get('translatedDescriptionHtml'))[:400]
            elif node.get('translatedDescription'):
                video_description = node.get('translatedDescription')[:400]
            else:
                video_description = ''
            khan_node = KhanVideo(id=node['translatedYoutubeId'],
                                  title=node['translatedTitle'],
                                  description=video_description,
                                  slug=node['slug'],
                                  thumbnail=node['imageUrl'],
                                  license=node['licenseName'],
                                  download_urls=node['downloadUrls'],
                                  lang=node['translatedYoutubeLang'])
        elif node['kind'] == 'Article':
            khan_node = KhanArticle(id=node['id'],
                                    title=node['translatedTitle'],
                                    description=node['translatedDescription'],
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

    def __init__(self, id, title, description, slug, thumbnail, assessment_items, source_url, lang="en"):
        super(KhanExercise, self).__init__(id, title, description, slug, lang=lang)
        self.thumbnail = thumbnail
        self.assessment_items = assessment_items
        self.source_url = source_url

    def get_assessment_items(self):
        items_list = []
        for i in self.assessment_items:
            item_url = ASSESSMENT_URL.format(assessment_item=i['id'], lang=self.lang)
            response = sess.get(item_url, headers=headers).json()
            # check if assessment item is fully translated, before adding it to list
            if response['is_fully_translated']:
                items_list.append(KhanAssessmentItem(response['id'], response['item_data'], self.source_url))

        return items_list

    def __repr__(self):
        return "Exercise Node: {}".format(self.title)


class KhanAssessmentItem(object):

    def __init__(self, id, data, source_url):
        self.id = id
        self.data = data
        self.source_url = source_url


class KhanVideo(KhanNode):

    def __init__(self, id, title, description, slug, thumbnail, license, download_urls, lang="en"):
        super(KhanVideo, self).__init__(id, title, description, slug, lang=lang)
        self.license = license
        self.thumbnail = thumbnail
        self.download_urls = download_urls

    def get_subtitle_languages(self):
        with youtube_dl.YoutubeDL({"listsubtitles": True}) as ydl:
                return list(YoutubeIE(ydl).extract(self.id)["subtitles"].keys())

    def __repr__(self):
        return "Video Node: {}".format(self.title)


class KhanArticle(KhanNode):

    def __init__(self, id, title, description, slug, lang="en"):
        super(KhanArticle, self).__init__(id, title, description, slug, lang=lang)

    def __repr__(self):
        return "Article Node: {}".format(self.title)

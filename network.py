import hashlib
import json
import os
import requests
import time

from pycaption import CaptionNode
from pycaption import Caption
from pycaption import CaptionSet
from pycaption import CaptionList
from pycaption import WebVTTWriter

from ricecooker.config import LOGGER
from ricecooker.utils.caching import (
    CacheControlAdapter,
    CacheForeverHeuristic,
    FileCache,
    InvalidatingCacheControlAdapter,
)

from constants import INVERSE_VIDEO_LANGUAGE_MAPPING

YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', None)

sess = requests.Session()
cache = FileCache(".webcache")
forever_adapter = CacheControlAdapter(heuristic=CacheForeverHeuristic(), cache=cache)
invalidate_adapter = InvalidatingCacheControlAdapter(cache=cache)

sess.mount("http://www.khanacademy.org/api/v2/topics/topictree", forever_adapter)
sess.mount("http://www.khanacademy.org/api/v1/assessment_items/", forever_adapter)
sess.mount("https://api.crowdin.com", forever_adapter)
# TODO: review caching used by make_request to avoid need to delete .webcache

# Directory to store list-of-subtitles-available-for-
SUBTITLE_LANGUAGES_CACHE_DIR = 'chefdata/sublangscache'
os.makedirs(SUBTITLE_LANGUAGES_CACHE_DIR, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


class Dummy404ResponseObject(requests.Response):
    def __init__(self, url):
        super(Dummy404ResponseObject, self).__init__()
        self._content = b""
        self.status_code = 404
        self.url = url


def make_request(url, clear_cookies=True, timeout=60, *args, **kwargs):
    if clear_cookies:
        sess.cookies.clear()

    retry_count_500 = 0
    retry_count = 0
    max_retries = 5
    while True:
        try:
            response = sess.get(url, headers=headers, timeout=timeout, *args, **kwargs)
            retry_count_500 += 1
            if response.status_code == 500:
                time.sleep(retry_count_500 * 1)
                continue
            if retry_count_500 >= max_retries:
                break
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
        ) as e:
            retry_count += 1
            print(
                "Error with connection ('{msg}'); about to perform retry {count} of {trymax}.".format(
                    msg=str(e), count=retry_count, trymax=max_retries
                )
            )
            time.sleep(retry_count * 1)
            if retry_count >= max_retries:
                return Dummy404ResponseObject(url=url)

    if response.status_code != 200:
        print("NOT FOUND:", url)
    # elif not response.from_cache:
    #     print("NOT CACHED:", url)

    return response


def post_request(url, data, clear_cookies=True, timeout=60, *args, **kwargs):
    if clear_cookies:
        sess.cookies.clear()

    retry_count = 0
    max_retries = 5
    while True:
        try:
            response = sess.post(url, json=data, headers=headers, timeout=timeout, *args, **kwargs)
            response.raise_for_status()
            break
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
        ) as e:
            retry_count += 1
            print(
                "Error with connection ('{msg}'); about to perform retry {count} of {trymax}.".format(
                    msg=str(e), count=retry_count, trymax=max_retries
                )
            )
            time.sleep(retry_count * 1)
            if retry_count >= max_retries:
                return None
    return response.json()


subtitles_query = """
query LearningEquality_getSubtitles($youtubeId: String!, $kaLocale: String) {
    subtitles(youtubeId: $youtubeId, kaLocale: $kaLocale) {
        text
        startTime
        endTime
        kaIsValid
    }
}
"""

SUBTITLE_LANGUAGES_CACHE_INDEX = os.path.join(SUBTITLE_LANGUAGES_CACHE_DIR, "index.json")


def _populate_sublangscache_index():
    LOGGER.info("Populating subtitle language cache index to create complete listing of all subtitles for all KA Youtube videos")
    url = "https://amara.org/api/videos/?team=khan-academy&limit=100&format=json"
    LOGGER.info("Fetching and processing {}".format(url))
    response = make_request(url)
    if response.status_code == 200:
        index = {}
        data = response.json()
        while data:
            for video in data["objects"]:
                youtube_id = video["all_urls"][0].replace("http://www.youtube.com/watch?v=", "")
                published_subtitles = []
                for subtitle in video["languages"]:
                    if subtitle.get("published", False):
                        published_subtitles.append({
                            "lang": subtitle["code"],
                            "url": subtitle["subtitles_uri"].replace("format=json", "format=vtt"),
                        })
                index[youtube_id] = published_subtitles
            url = data["meta"]["next"]
            if url:
                LOGGER.info("Fetching and processing {}".format(url))
                response = make_request(url)
                data = response.json()
            else:
                data = None
    LOGGER.info("Writing subtitles language cache to disk")
    with open(SUBTITLE_LANGUAGES_CACHE_INDEX, "w") as f:
        json.dump(index, f)

subtitle_language_cache = {}


def get_subtitles(youtube_id):
    if not subtitle_language_cache:
        if not os.path.exists(SUBTITLE_LANGUAGES_CACHE_INDEX):
            _populate_sublangscache_index()
        with open(SUBTITLE_LANGUAGES_CACHE_INDEX, "r") as f:
            data = json.load(f)
            subtitle_language_cache.update(data)
    return [(sub["lang"], sub["url"]) for sub in subtitle_language_cache.get(youtube_id, [])]

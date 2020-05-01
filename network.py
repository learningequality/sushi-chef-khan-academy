from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import requests
import time

from pressurecooker.youtube import YouTubeResource
from ricecooker.config import LOGGER
from ricecooker.utils.caching import (
    CacheControlAdapter,
    CacheForeverHeuristic,
    FileCache,
    InvalidatingCacheControlAdapter,
)

if 'YOUTUBE_API_KEY' not in os.environ:
    LOGGER.warning('Specify YOUTUBE_API_KEY env var for faster operation.')
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', None)

sess = requests.Session()
cache = FileCache(".webcache")
forever_adapter = CacheControlAdapter(heuristic=CacheForeverHeuristic(), cache=cache)
invalidate_adapter = InvalidatingCacheControlAdapter(cache=cache)

sess.mount("http://www.khanacademy.org/api/v2/topics/topictree", forever_adapter)
sess.mount("http://www.khanacademy.org/api/v1/assessment_items/", forever_adapter)
sess.mount("https://api.crowdin.com", forever_adapter)


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



def get_subtitle_languages(youtube_id):
    """
    Returns a list of the subtitle language codes available for a given video.
    We'll try to get the list using two approach:
    1. The Youtube API (works for public videos when YOUTUBE_API_KEY defined)
    2. Slow by using YouTubeResource, which in turn calls youtube_dl
    """
    if YOUTUBE_API_KEY:
        try:
            lang_codes = get_subtitles_using_api(youtube_id)
            return lang_codes
        except HttpError as e:
            LOGGER.info("Can't access API for video {} ...".format(youtube_id))
    lang_codes = get_subtitles_using_youtube_dl(youtube_id)
    return lang_codes


def get_subtitles_using_api(youtube_id):
    """
    YouTube API call to get the subtitles langs available for video `youtube_id`.
    Raises `HttpError` in case video is Private, Unlisted, or has been removed.
    """
    youtube = build("youtube", "v3", cache_discovery=False, developerKey=YOUTUBE_API_KEY)
    request = youtube.captions().list(part="snippet", videoId=youtube_id)
    response = request.execute()
    all_subs = [item['snippet'] for item in response['items']]
    lang_codes = [sub['language'] for sub in all_subs if sub['trackKind'] == 'standard']
    return lang_codes


def get_subtitles_using_youtube_dl(youtube_id):
    youtube_url = 'https://youtube.com/watch?v=' + youtube_id
    yt_resource = YouTubeResource(youtube_url)
    lang_codes = []
    try:
        result = yt_resource.get_resource_subtitles()
        # TODO(ivan) Consider including auto-generated subtitles to increase
        #       coverage and handle edge cases of videos that are transalted
        #       but no metadata: https://www.youtube.com/watch?v=qlGjA9p1UAM
        if result:
            for lang_code, lang_subs in result['subtitles'].items():
                for lang_sub in lang_subs:
                    if 'ext' in lang_sub and lang_sub['ext'] == 'vtt' and lang_code not in lang_codes:
                        lang_codes.append(lang_code)
    except Exception as e:
        LOGGER.error('get_subtitles_using_youtube_dl failed for ' + youtube_url)
        LOGGER.error(str(e))
    return lang_codes

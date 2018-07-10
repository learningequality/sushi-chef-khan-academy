import time

import requests
from ricecooker.utils.caching import (CacheControlAdapter,
                                      CacheForeverHeuristic, FileCache,
                                      InvalidatingCacheControlAdapter)

sess = requests.Session()
cache = FileCache('.webcache')
forever_adapter = CacheControlAdapter(heuristic=CacheForeverHeuristic(), cache=cache)

sess.mount('http://www.khanacademy.org/api/v2/topics/topictree', forever_adapter)
sess.mount('http://www.khanacademy.org/api/v1/assessment_items/', forever_adapter)
sess.mount('https://api.crowdin.com', forever_adapter)


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive"
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
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            retry_count += 1
            print("Error with connection ('{msg}'); about to perform retry {count} of {trymax}."
                  .format(msg=str(e), count=retry_count, trymax=max_retries))
            time.sleep(retry_count * 1)
            if retry_count >= max_retries:
                return Dummy404ResponseObject(url=url)

    if response.status_code != 200:
        print("NOT FOUND:", url)
    # elif not response.from_cache:
    #     print("NOT CACHED:", url)

    return response

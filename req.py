import random
import time
from functools import lru_cache

import requests
from parsel import Selector


class RequestHelper:
    """
    This class attempts to enable to make requests more easily.
    """

    def __init__(self, timeout=10, maximum_retries=5, verify=True, proxy_list=None, disable_debug_print=False):
        """
        __init__ method for RequestHelper class

        :param int timeout: Maximum wait time.
        :param int maximum_retries: Maximum retries on URL opening.
        :param bool verify: If set to false, skips https verification.
        :param list proxy_list: List of strings of proxies to be used for opening urls.
        """
        self.proxy_list = proxy_list
        self.timeout = timeout
        self.maximum_retries = maximum_retries
        self.verify = verify
        self._disable_debug_print = disable_debug_print

    @lru_cache(maxsize=5000, typed=False)
    def make_request(self, url):
        """
        Making requests with retry logic and headers mocking real-world browser

        :param str url: Url to open
        :return requests.Response: Response object
        """
        headers = {
            'cache-control': 'max-age=0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
            'dnt': '1',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,'
                      'image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'en,cs;q=0.9,sk;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        }

        for attempt in range(self.maximum_retries):
            try:
                proxy_dict = None
                if self.proxy_list:
                    proxy_host = random.choice(self.proxy_list)
                    proxy_dict = {'http': proxy_host, 'https': proxy_host}
                if not self._disable_debug_print:
                    print(f'Attempt {attempt} for {url}.')
                r = requests.get(url, headers=headers, timeout=self.timeout, verify=self.verify, proxies=proxy_dict)
                return r
            except Exception as e:
                if attempt < self.maximum_retries - 1:
                    time.sleep(10)
                    continue
                raise

    def get_selector(self, url):
        """
        Returns selector object for given url
        :param str url: url to open
        :return parsel.Selector: Selector object
        """
        r = self.make_request(url=url)
        return Selector(r.text)

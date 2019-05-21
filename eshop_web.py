from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import re
import time

from tqdm import tqdm

from req import RequestHelper
from base import BaseDownload


class EshopWebsite(BaseDownload):
    """
    Downloads the data from eshop's page.
    """

    def __init__(self, req=None, *, concurrent_threads_count=30):
        """
        __init__ method for the class.

        :param RequestHelper req: Request helper objects, if not supplied, instantiated automatically.
        :param int concurrent_threads_count: Number of threads to be used in download of data.
        """

        self.r = req or RequestHelper()
        if not isinstance(self.r, RequestHelper):
            raise NotImplementedError('Only RequestHelper instance can be passed in req argument, otherwise'
                                      'leave it to its default value.')

        self._concurrent_threads_count = concurrent_threads_count

        self.output = []

    def _run_multiple_threads(self, website_list):
        """
        Wrapper for threads download.

        :param list website_list: List of strings containing urls (with protocol specified).
        """
        print(f' - getting data from eshop pages in {self._concurrent_threads_count} threads:')
        t = ThreadPoolExecutor(self._concurrent_threads_count)

        self.output.extend(
            list(tqdm(t.map(self._parse_data_from_eshop_website, website_list), total=len(website_list))))

    def _parse_data_from_eshop_website(self, url):
        """
        For the given url it downloads additional data. Currently, only instagram account is supported
        :param str url:  url (with protocol specified).
        :return dict:
        """
        output_dict = {}
        sel = self.r.get_selector(url)
        output_dict['url'] = url
        output_dict['instagram'] = self._parse_instagram_links(sel)

        return output_dict

    @staticmethod
    def _parse_instagram_links(sel):
        """
        This method finds all candidate instagram links from the supplied object and returns the instagram account name
        that is most common on the page.

        :param parsel.Selector sel:
        :return str: Instagram account as string.
        """
        # find all links containing instagram
        instagram_links = sel.xpath('//a[contains(@href,"instag")]/@href').getall()

        # if nothing found, return None
        if not instagram_links:
            return None

        # Get matches for all links. They are usually in the form of instagram.com/datapythonies/anything_else
        regex_matches = (re.search(r'(instagram.com|instagr.am)/(?P<id>[\w\.]{3,})', link) for link in instagram_links)

        # list where we append all instagram accounts found
        candidates = []
        for match in regex_matches:
            if match:
                candidates.append(match['id'])

        # if the length is greater than 1, then we compute the most common and return it
        if len(candidates) > 0:
            return Counter(candidates).most_common()[0][0]

    def run(self, website_list):
        """
        Triggers the download for the list of urls supplied. Result is stored in the 'output' class attribute.
        Download is done in threads to speed it up - we are contacting different sites, therefore, we do not need
        (in theory) to worry about being blocked.

        :param list website_list:  List of strings containing urls (with protocol specified).
        """
        start_time = time.time()

        self._run_multiple_threads(website_list=website_list)

        print(f'Data from Eshop pages finished in {round(time.time() - start_time, 3)}s.')

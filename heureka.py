from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
import re
import time

from req import RequestHelper
from tqdm import tqdm

class Heureka:
    """
    Downloads the data from the Heureka from the obchody.heureka.cz page.
    """

    def __init__(self, req=None, *, use_multiple_threads=False):
        """
        __init__ method for the class.

        :param RequestHelper req: Request helper objects, if not supplied, instantiated automatically.
        :param use_multiple_threads: If True, multiple threads are used. Handle with care.
        """

        self.r = req or RequestHelper()
        if not isinstance(self.r, RequestHelper):
            raise NotImplementedError('Only RequestHelper instance can be passed in req argument, otherwise'
                                      'leave it to its default value.')

        self._next_link = None
        self._output_from_list_page = []
        self._use_multiple_threads = use_multiple_threads

        self.heureka_output = []

    def _download_list_of_links(self, how_many_pages_download=2):
        """
        Downloads the basic info available from the listing pages.

        :param int how_many_pages_download: How many listings pages to open. One how_many_pages_download equals to
                                            20 eshops downloaded.
        """
        # either continue where left or start at the beginning
        self._next_link = self._next_link or 'https://obchody.heureka.cz/'

        print(' - getting Heureka lists of eshops:')
        for _ in tqdm(range(how_many_pages_download)):
            sel = self.r.get_selector(self._next_link)
            # parse info from the listing page
            self._parse_listing_page(sel)
            # get the link for the "next" page
            self._next_link = urljoin(self._next_link,
                                      sel.xpath('/html/body/div[2]/div/div[2]/nav/ol//a[@rel="next"]/@href').get())

    def _parse_listing_page(self, sel):
        """
        Parses the values from the listing page.

        :param parsel.Selector sel: Input Selector object.
        """
        self._output_from_list_page.extend(
            [{
                # re.sub -> replace all that does not match digit
                'reviews': float(re.sub(r'[^\d]+', '', tr.xpath('./td[4]/a/ul/li[2]/text()').get())),
                # urljoin -> solves relative vs. absolute links
                'inner_link': urljoin(self._next_link, tr.xpath('./td[4]/a/@href').get()),
                'name': tr.xpath('./th/a/text()').get(),
            }
                for tr in sel.xpath('/html/body/div[2]/div/div[2]/div/table//tr')])

    def _extend_list_page_by_details(self, how_many):
        """
        For the _output_from_list_page dictionary, gets the fields from the detailed page and
        saves it to the heureka_output dictionary.
        """
        print(' - getting Heureka page details:')
        for eshop in tqdm(self._output_from_list_page[:how_many]):
            self.heureka_output.append(self._download_eshop_detail(eshop))

    def _extend_list_page_by_details_in_threads(self, how_many, threads=10):
        """
        The same functionality as _extend_list_page_by_details method, but uses threads. Use with caution, otherwise,
        you might get blocked.

        :param int threads: Number of connections to be opened in parallel threads.
        """
        self.heureka_output.extend(list(
            ThreadPoolExecutor(threads).map(self._download_eshop_detail, self._output_from_list_page[:how_many])))

    def _download_eshop_detail(self, eshop):
        """
        Wrapper for downloading the detail page

        :param dict eshop: Dictionary, must contain the 'inner_link' key.
        :return dict: Dictionary enhanced by the values from the detail page.
        """
        sel = self.r.get_selector(eshop['inner_link'])
        eshop.update(self._parse_detail_page(sel))
        return eshop

    def _parse_detail_page(self, sel):
        """
        Parses the detail page

        :param parsel.Selector sel: Input selector object.
        :return dict: Returns the detailed values from the page.
        """
        output = {}
        link = sel.xpath('/html/body/div[2]/div/'
                         'div[2]/aside//dd[@class="c-pair-list__value"]/'
                         'a[contains(@href,"heureka.cz/exit")]/text()').get().strip()
        output['link'] = link

        rating = sel.css('body > div.scope-essentials.scope-shop-detail > '
                         'div > div.l-shop-detail__wrapper > aside > div > '
                         'section.c-shop-detail-stats.c-aside__section > table > '
                         'tbody > tr:nth-child(1) > td > '
                         'span.c-shop-detail-stats__value::text').get()
        output['rating'] = float(rating.replace(',', '.'))

        negative_reviews_count = sel.xpath('//*[@id="filtr"]/div/nav/ul/li[3]/a/@data-count').get()
        output['reviews_negative_count'] = float(re.sub(r'&nbsp;|\s+','',negative_reviews_count))

        positive_reviews_count = sel.xpath('//*[@id="filtr"]/div/nav/ul/li[2]/a/@data-count').get()
        output['reviews_positive_count'] = float(re.sub(r'&nbsp;|\s+', '', positive_reviews_count))
        return output

    def run(self, how_many_pages_download):
        """
        Main method for the class, output is stored in the heureka_output attribute.

        :param int how_many_pages_download: How many pages should be there in the output.
        """
        start_time = time.time()

        # there are 20 eshops on 1 listing page
        listings_needed = (how_many_pages_download // 20) + 1
        self._download_list_of_links(listings_needed)
        if self._use_multiple_threads:
            self._extend_list_page_by_details_in_threads(how_many_pages_download)
        else:
            self._extend_list_page_by_details(how_many_pages_download)

        print(f'Data from Heureka finished in {round(time.time() - start_time, 3)}s.')

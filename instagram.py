import json
import re
import time
from concurrent.futures import ThreadPoolExecutor

from tqdm import tqdm

from req import RequestHelper


class Instagram:
    """
    Downloads the data from Instagram profile pages.
    """

    RGX_PATTERN_INSTAGRAM = r"""
^                         # start of string
[^\{]*?                   # any characters except "{", as few as possible
(?P<json_obj>\{.*\})      # json_obj: starts with "{" and ends with "}"
[^\}]*?                   # any characters except "}", as few as possible
$                         # end of string
"""

    def __init__(self, req=None, *, use_multiple_threads=False, concurrent_threads_count=30):
        """
        __init__ method for the class.

        :param RequestHelper req: Request helper objects, if not supplied, instantiated automatically.
        :param int concurrent_threads_count: Number of threads to be used in download of data.
        """

        self.r = req or RequestHelper()
        if not isinstance(self.r, RequestHelper):
            raise NotImplementedError('Only RequestHelper instance can be passed in req argument, otherwise'
                                      'leave it to its default value.')
        self._use_multiple_threads = use_multiple_threads
        self._concurrent_threads_count = concurrent_threads_count

        self.output = []

    def _run_multiple_threads(self, instagram_accounts_list):
        """
        Wrapper for threads download in multiple threads. Not recommenced for instagram.

        :param list instagram_accounts_list: List of instagram accounts' ids.
        """

        print(f' - getting data from Instagram in {self._concurrent_threads_count} threads:')
        self.output.extend(list(
            tqdm(ThreadPoolExecutor(self._concurrent_threads_count).map(self._parse_data_from_instagram_account,
                                                                        instagram_accounts_list))))

    def _run_single_thread(self, instagram_accounts_list):
        """
        Wrapper for threads download.

        :param list instagram_accounts_list: List of instagram accounts' ids.
        """
        print(f' - getting data from Instagram:')
        self.output.extend(
            [self._parse_data_from_instagram_account(account) for account in tqdm(instagram_accounts_list)])

    def _parse_data_from_instagram_account(self, account_id):
        """
        For the given instagram account, download details.

        :param str account_id:  instagram account name.
        :return dict:
        """

        output_dict = {'account': account_id}

        instagram_json = self.get_instagram_data(account_id)
        if not instagram_json:
            return output_dict

        output_dict['instagram_followers'] = instagram_json['edge_followed_by']['count']
        output_dict['instagram_posts_count'] = instagram_json['edge_owner_to_timeline_media']['count']

        posts = instagram_json['edge_owner_to_timeline_media']['edges']
        output_dict['instagram_posts_average_like'] = sum(p['node']['edge_liked_by']['count'] for p in posts) / len(
            posts)

        descriptions = (re.sub(r'^Image may contain:\s+|No photo description available\.', '',
                               p['node'].get('accessibility_caption', '')) for p in posts)
        output_dict['instagram_classified_descriptions'] = ';'.join(d for d in descriptions if d)

        # as a backup, store the full json from instagram
        output_dict['instagram_full_json'] = instagram_json
        return output_dict

    def get_instagram_data(self, instagram_id):
        """
        Extract the json object from the page for the given account.

        :param str instagram_id: Instagram account id.
        :return dict: Outputs json loaded as dictionary.
        """
        i_s = self.r.get_selector(f'https://www.instagram.com/{instagram_id}/')
        if 'Sorry, this page' in i_s.get():
            # the instagram profile does not exist, see for example https://instagram.com/dafdsfasdfjefwollaskjf
            return None
        output_object = json.loads(
            re.match(self.RGX_PATTERN_INSTAGRAM, i_s.xpath('/html/body/script[1]/text()').get(), re.VERBOSE)[
                'json_obj'])
        return output_object['entry_data']['ProfilePage'][0]['graphql']['user']

    def run(self, instagram_accounts_list):
        """
        Triggers the download.

        :param list instagram_accounts_list:  List of instagram accounts' ids.
        """
        start_time = time.time()

        if self._use_multiple_threads:
            self._run_multiple_threads(instagram_accounts_list=instagram_accounts_list)
        else:
            self._run_single_thread(instagram_accounts_list=instagram_accounts_list)

        print(f'Data from Instagram pages finished in {round(time.time() - start_time, 3)}s.')

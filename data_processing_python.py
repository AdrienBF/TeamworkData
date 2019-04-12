import json
import re
from functools import lru_cache
from urllib.parse import urljoin

import requests
import pandas as pd
from parsel import Selector
import matplotlib.pyplot as plt

MAX_HEUREKA_PAGING_PAGES = 2  # this means that MAX_HEUREKA_PAGING_PAGES  * 20 eshops will be crawled
RGX_PATTERN_INSTAGRAM = r"""
^                         # start of string
[^\{]*?                   # any characters except "{", as few as possible
(?P<json_obj>\{.*\})      # json_obj: starts with "{" and ends with "}"
[^\}]*?                   # any characters except "}", as few as possible
$                         # end of string
"""


# @lru_cache - caching of calls to this function, helpful for debugging to save calls
@lru_cache(maxsize=1000, typed=False)
def get_selector(link):
    """
    For a given link returns an instance of parsel.Selector object.

    :param link: URL
    :return: parsel.Selector instance
    """
    headers = {
        'authority': 'obchody.heureka.cz',
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

    response = requests.get(link, headers=headers)
    return Selector(response.text)


def get_instagram_data(instagram_id):
    i_s = get_selector(f"https://www.instagram.com/{instagram_id}/")
    if 'Sorry, this page' in i_s.get():
        # the instagram profile does not exist, see https://instagram.com/dafdsfasdfjefwollaskjf
        return None
    output_object = json.loads(
        re.match(RGX_PATTERN_INSTAGRAM, i_s.xpath('/html/body/script[1]/text()').get(), re.VERBOSE)['json_obj'])
    return output_object


data = []
next_link = 'https://obchody.heureka.cz/'
# get list if eshops from 'https://obchody.heureka.cz/' using paging
for _ in range(MAX_HEUREKA_PAGING_PAGES):
    print(f'Getting link: {next_link}')
    s = get_selector(next_link)

    data.extend(
        [{'reviews': float(re.sub(r'[^\d]+', '', tr.xpath('./td[4]/a/ul/li[2]/text()').get())),
          'inner_link': urljoin(next_link, tr.xpath('./td[4]/a/@href').get()),
          'name': tr.xpath('./th/a/text()').get(),

          }
         for tr in s.xpath('/html/body/div[2]/div/div[2]/div/table//tr')])
    next_link = urljoin(next_link, s.xpath('/html/body/div[2]/div/div[2]/nav/ol//a[@rel="next"]/@href').get())

# get details for eshops in the list
for eshop in data:
    # detail on heureka
    print(f"Starting for: {eshop['inner_link']}")
    s = get_selector(eshop['inner_link'])
    link = s.xpath('/html/body/div[2]/div/'
                   'div[2]/aside//dd[@class="c-pair-list__value"]/'
                   'a[contains(@href,"heureka.cz/exit")]/text()').get().strip()
    eshop['link'] = link
    eshop['rating'] = s.css('body > div.scope-essentials.scope-shop-detail > '
                            'div > div.l-shop-detail__wrapper > aside > div > '
                            'section.c-shop-detail-stats.c-aside__section > table > '
                            'tbody > tr:nth-child(1) > td > '
                            'span.c-shop-detail-stats__value::text').get()
    eshop['rating'] = float(eshop['rating'].replace(',', '.'))

    # detail from eshop page
    # download links containing instagram.com from eshop page
    instagram_link = get_selector(link).xpath('//a[contains(@href,"instagram.com")]/@href').get()
    if instagram_link:
        m = re.search(r'instagram.com/(?P<id>[\w\.]{3,})', instagram_link)
    eshop['instagram'] = m['id'] if instagram_link and m else None

    # download links containing twitter.com from eshop page
    twitter_link = get_selector(link).xpath('//a[contains(@href,"twitter.com")]/@href').get()
    if twitter_link:
        m = re.search(r'twitter.com/@?(?P<id>[\w\.]+)', twitter_link)

    # not used further for now
    eshop['twitter'] = m['id'] if twitter_link and m else None

    # detail from instagram profile
    # get data from instagram profile
    if eshop['instagram']:
        instagram_data = get_instagram_data(eshop['instagram'])
        eshop['instagram_followers'] = instagram_data['entry_data']['ProfilePage'][
            0]['graphql']['user']['edge_followed_by']['count'] if instagram_data else None

# plot the data
d = pd.DataFrame(data)
plt.scatter(d['reviews'], d['instagram_followers'])
plt.show()

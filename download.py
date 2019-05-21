import pandas as pd

from heureka import Heureka
from eshop_web import EshopWebsite
from instagram import Instagram


def download_all(count_of_eshops=30, req=None):
    """
    A function for downloading it all-at-once.

    :param RequestHelper req: a Request helper class to be passed
    :param int count_of_eshops: Number of eshops to include.
    :return pandas.DataFrame: Data frame with all the data
    """

    # we run the Heureka first
    h = Heureka(req=req)
    h.run(count_of_eshops)

    # then we find the instagram links on the eshop's webpages
    e = EshopWebsite(req=req)
    e.run([shop['link'] for shop in h.output])

    # then use the information from web pages to collect instagram accounts
    i = Instagram(req=req)
    i.run([shop['instagram'] for shop in e.output if shop['instagram']])

    # here we create DataFrames
    df_h = pd.DataFrame(h.output).set_index('link')
    df_e = pd.DataFrame(e.output).set_index('url')
    df_i = pd.DataFrame(i.output).set_index('account')
    df_all = df_h.join(pd.merge(df_e, df_i, left_on='instagram', right_index=True))

    # and return the merged DataFrame
    return df_all


if __name__ == '__main__':
    # testing if it works
    test = download_all(1)

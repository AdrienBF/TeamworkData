from heureka import Heureka
from eshop_web import EshopWebsite
from instagram import Instagram

import pandas as pd


def download_all(count_of_eshops=30, req=None):
    """
    A function for downloading it all-at-once.

    :param req:
    :param int count_of_eshops: Number of eshops to include.
    :return pandas.DataFrame:
    """

    h = Heureka(req=req)
    h.run(count_of_eshops)

    e = EshopWebsite(req=req)
    e.run([shop['link'] for shop in h.heureka_output])

    i = Instagram(req=req)
    i.run([shop['instagram'] for shop in e.output if shop['instagram']])

    df_h = pd.DataFrame(h.heureka_output).set_index('link')
    df_e = pd.DataFrame(e.output).set_index('url')
    df_i = pd.DataFrame(i.output).set_index('account')
    df_all = df_h.join(pd.merge(df_e, df_i, left_on='instagram', right_index=True))

    return df_all


if __name__ == '__main__':
    test = download_all(1)

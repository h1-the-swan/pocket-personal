# -*- coding: utf-8 -*-

DESCRIPTION = """Core for pocket-personal"""

import os

import logging
from typing import List, Optional, Dict

root_logger = logging.getLogger()
logger = root_logger.getChild(__name__)

from pocket import Pocket

from collections import defaultdict
import pandas as pd

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class PocketPersonal:
    """PocketPersonal class

    Usage:
    pp = PocketPersonal()
    print(pp.get_auth_url())
    # go to url and authenticate, then:
    pp.authenticate()
    pp.load_articles()
    """

    def __init__(
        self,
        pocket_instance: Optional[Pocket] = None,
        request_token: Optional[str] = None,
    ) -> None:
        self.pocket_instance = pocket_instance  # Authenticated Pocket instance
        self.request_token = request_token

        self.data = dict()
        self.since = 0

        self._df = None

    def get_auth_url(self, new_token: bool = False) -> str:
        consumer_key = os.environ["POCKET_CONSUMER_KEY"]
        redirect_uri = "https://www.google.com"
        if self.request_token is None or new_token is True:
            request_token = Pocket.get_request_token(
                consumer_key=consumer_key, redirect_uri=redirect_uri
            )
            self.request_token = request_token
        auth_url = Pocket.get_auth_url(
            code=self.request_token, redirect_uri=redirect_uri
        )
        return auth_url

    def authenticate(self) -> None:
        consumer_key = os.environ["POCKET_CONSUMER_KEY"]
        user_credentials = Pocket.get_credentials(
            consumer_key=consumer_key, code=self.request_token
        )
        access_token = user_credentials["access_token"]
        self.pocket_instance = Pocket(consumer_key, access_token)

    def load_articles(self, state: str = "all", force: bool = False) -> None:
        offset = 0
        count = 5000
        i = 0
        if force is True:
            self.since = 0
        while True:
            r = self.pocket_instance.get(
                state=state,
                detailType="complete",
                count=count,
                offset=offset,
                since=self.since,
            )
            if r[0]["status"] != 1:
                # print('status is {} (i is {})'.format(r[0]['status'], i))
                self.since = r[0]["since"]
                break
            self.data.update(r[0]["list"])
            offset += count
            i += 1

    @property
    def df(self) -> pd.DataFrame:
        if self._df is None:
            d = []
            columns = [
                "item_id",
                "resolved_id",
                "given_url",
                "given_title",
                "favorite",
                "status",
                "time_added",
                "time_updated",
                "time_read",
                "time_favorited",
                "resolved_title",
                "resolved_url",
                "word_count",
                "lang",
                "time_to_read",
            ]
            for article in self.data.values():
                d.append({c: article.get(c) for c in columns})
            self._df = pd.DataFrame(d)
        return self._df

    def articles_by_tag(self) -> Dict[str, List]:
        articles_by_tag = defaultdict(list)
        for article_id, article in self.data.items():
            if "tags" in article:
                for tag in article["tags"].keys():
                    articles_by_tag[tag].append(article_id)
            else:
                articles_by_tag["no_tags"].append(article_id)

        return articles_by_tag

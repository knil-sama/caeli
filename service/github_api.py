import logging
import requests
import typing
from dataclasses import dataclass


@dataclass
class GithubApi:
    """Class for handling Github api"""

    url_api: str
    headers: dict
    chunk_size: int

    def make_call(self, endpoint: str) -> list:
        result_to_fetch = True
        fetched_result = list()
        next_url = None
        while result_to_fetch:
            try:
                # first call
                if not next_url:
                    r = requests.get(
                        "/".join([self.url_api, endpoint]), headers=self.headers
                    )
                else:
                    r = requests.get(next_url, headers=self.headers
                    )
                logging.info(r)
                if r.status_code == requests.codes.ok:
                    result = r.json()
                    fetched_result = self._concat_result(fetched_result, result)
                    next_url = self._fetch_next_url(r)
                    if len(fetched_result) <= self.chunk_size and next_url:
                        continue
                result_to_fetch = False
            except Exception as e:
                logging.exception(e)
                result_to_fetch = False
        return fetched_result

    @staticmethod
    def _concat_result(fetched_result: list,result) -> list:
        if not isinstance(result, list):
            result = [result]
        fetched_result += result
        return fetched_result

    @staticmethod
    def _fetch_next_url(r) -> typing.Optional[str]:
        url_to_fetch = None
        if r.links and "url" in r.links.get("next", []):
            url_to_fetch = r.links["next"]["url"]
        return url_to_fetch

    def check_rate(self) -> dict:
        """
        This don't count as rate consumption

        Returns:
            dict: {"limit": 30, "remaining": 18,"reset": 1372697452}
        """
        ressources = self.make_call("rate_limit")[0]["resources"]
        logging.info(ressources)
        return ressources

    def listing_repositories(self, type_owner: str, owner: str) -> list:
        """
        Official doc https://developer.github.com/v3/repos/#list-your-repositories

        Returns:
            list: Existing repositories in json format
        """
        return self.make_call(f"/{type_owner}/{owner}/repos")

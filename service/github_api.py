import logging
import requests

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
        while result_to_fetch:
            try:
                r = requests.get(
                    "/".join([self.url_api, endpoint]), headers=self.headers
                )
                logging.info(r)
                if r.status_code == requests.codes.ok:
                    result = r.json()
                    if not isinstance(result, list):
                        result = [result]
                    fetched_result += result
                    if len(fetched_result) <= self.chunk_size:
                        if r.links and "url" in r.links.get("next", []):
                            url_to_fetch = r.links["next"]["url"]
                            continue
                result_to_fetch = False
            except Exception as e:
                logging.exception(e)
                result_to_fetch = False
        return fetched_result

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

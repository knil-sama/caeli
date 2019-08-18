import logging
import requests
from dataclasses import dataclass
import tenacity
import typing


@dataclass
class GithubApi:
    """Class for handling Github api"""

    url_api: str
    headers: dict
    chunk_size: int

    # TODO improve by listing internet and timeout error to only retry situation where we didn't reach quota
    @tenacity.retry(
        wait=tenacity.wait_fixed(2), reraise=True, stop=tenacity.stop_after_attempt(3)
    )
    def _direct_call(self, url: str):
        logging.debug(f"calling url {url}")
        return requests.get(url, headers=self.headers)

    def make_call(self, endpoint: str) -> list:
        result_to_fetch = True
        fetched_result = list()
        next_url = None
        while result_to_fetch:
            try:
                # first call
                if not next_url:
                    r = self._direct_call("/".join([self.url_api, endpoint]))
                else:
                    r = self._direct_call(next_url)
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
    def _concat_result(fetched_result: list, result) -> list:
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
        return self.make_call(f"{type_owner}/{owner}/repos")

    def listing_new_contributors(
        self, contributors: list, owner: str, repo: str, since: str
    ) -> list:
        """
        https://developer.github.com/v3/repos/commits/
        """
        starting_date = f"?since={since}" if since else ""
        endpoint = f"repos/{owner}/{repo}/commits{starting_date}"
        all_new_commits = self.make_call(endpoint)
        logging.info(
            f"{len(all_new_commits)} all new commits for {owner}/{repo} since : {since}"
        )
        commits_from_new_committer = list()
        for new_commit in all_new_commits:
            try:
                if not new_commit["author"]["login"] in contributors:
                    commits_from_new_committer.append(new_commit)
            except (TypeError, KeyError) as e:
                # author can be None and login missing
                # logging.exception(e)
                # logging.info(new_commit)
                pass
        new_contributors = dict()
        for new_commit in commits_from_new_committer:
            if not new_commit in list(new_contributors.keys()):
                new_contributors[new_commit["author"]["login"]] = new_commit
        logging.info(
            f"Fetched {len(new_contributors)} new contributors for {owner}/{repo} since : {since}"
        )
        return list(new_contributors.values())

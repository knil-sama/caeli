import requests
import datetime
import os
import click
import logging
import psycopg2
from psycopg2.extras import Json
import time
from dataclasses import dataclass
import random
import sys
from threading import Thread
import time

logging.basicConfig(level=logging.DEBUG)

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
                r = requests.get("/".join([self.url_api, endpoint]), headers=self.headers)
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

    def listing_new_contributors(
        self, contributors: list, owner: str, repo: str, since: str
    ) -> list:
        """
        https://developer.github.com/v3/repos/commits/
        """
        starting_date = f"?since={since}" if since else ""
        endpoint = f"/repos/{owner}/{repo}/commits?{starting_date}"
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


class DatabaseApi:
    """Class for hnadling postgres database"""

    def __init__(self, user: str, password: str, host: str, port: int, database: str):
        tables = ["repositories", "contributors", "stats_contributions"]
        self.connection = psycopg2.connect(user=user, password=password, host=host, port=port, dbname=database)
        # init db
        with self.connection.cursor() as cursor:
            for table in tables:
                with open(f"sql/{table}.sql", "r") as sql:
                    cursor.execute(sql.read())
                    self.connection.commit()

    def listing_existing_contributors(self, repo_id: int):
        with self.connection.cursor() as cursor:
            cursor.execute(f"SELECT login FROM contributors WHERE repo_id = {repo_id}")
            contributors = [res[0] for res in cursor.fetchall()]
            logging.info(f"Exisiting contributors {contributors}")
        return contributors

    def upsert_contributors(self, repo_id: int, contributors: list):
        with self.connection.cursor() as cursor:
            for new_contributor in contributors:
                cursor.execute(
                    f"""INSERT INTO contributors (login,repo_id,first_commit_at,commit_json) VALUES ('{new_contributor["author"]["login"]}', {repo_id}, '{new_contributor["commit"]["author"]["date"]}', {Json(new_contributor)})"""
                )
            if contributors:
                # yes you can have project with 0 contributors https://github.com/facebook/Conditional-character-based-RNN
                cursor.execute(
                    f"""UPDATE repositories SET last_commit_check = '{contributors[-1]["commit"]["author"]["date"]}' WHERE id = {repo_id}"""
                )
            self.connection.commit()

    def insert_new_repositories(self, repositories: list):
        with self.connection.cursor() as cursor:
            for repo in repositories:
                cursor.execute(
                    f"""INSERT INTO repositories (id,name,owner,last_commit_check, repo_json)
                VALUES ({repo["id"]}, '{repo["name"]}', '{repo["owner"]["login"]}', NULL, {Json(repo)})
                ON CONFLICT (id)
                DO NOTHING;"""
                )
            self.connection.commit()

    def refresh_view(self):
        with self.connection.cursor() as cursor:
            cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY stats_contributions")
        self.connection.commit()

    def listing_repositories(self) -> list:
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, owner, name, last_commit_check FROM repositories ORDER BY last_commit_check NULLS FIRST"
            )
            repositories = cursor.fetchall()
            self.connection.commit()
        return repositories

class RefreshThread(Thread):
    def __init__(self, database_api: DatabaseApi, refresh_frequency:int):
        Thread.__init__(self)
        self.database_api = database_api
        self.refresh_frequency = refresh_frequency

    def run(self):
        while True:
            self.database_api.refresh_view()
            logging.info(f"Refresh view, waiting for interval of {self.refresh_frequency} secondes")
            time.sleep(self.refresh_frequency)


def time_before_reset(github_api: GithubApi, api: str = "core") -> int:
    """
    This don't count as rate consumption

    Args:
        api: Name of the github api resource we want rate for
    Returns:
        int: Return 0 if there still "credit" to consume else second to wait before reset
    """
    current_rate = github_api.check_rate()
    if current_rate[api]["remaining"]:
        return 0
    else:
        return current_rate[api]["reset"] - int(datetime.datetime.utcnow().timestamp())


def update_contributors_by_repo(
    database_api: DatabaseApi,
    github_api: GithubApi,
    repo_id: int,
    owner: str,
    repo: str,
    since: str,
):
    """
    since YYYY-MM-DDTHH:MM:SSZ
    """
    contributors = database_api.listing_existing_contributors(repo_id)
    list_new_contributors = github_api.listing_new_contributors(
        contributors, owner, repo, since
    )
    database_api.upsert_contributors(repo_id, list_new_contributors)


def update_repos(
    database_api: DatabaseApi, github_api: GithubApi, type_owner: str, owner: str
):
    repositories = github_api.listing_repositories(type_owner, owner)
    database_api.insert_new_repositories(repositories)


def loop(database_api: DatabaseApi, github_api: GithubApi, type_owner: str, owner: str):
    update_repos(database_api, github_api, type_owner, owner)
    repositories = database_api.listing_repositories()
    for repo in repositories:
        update_contributors_by_repo(
            database_api,
            github_api,
            repo_id=repo[0],
            owner=repo[1],
            repo=repo[2],
            since=repo[3],
        )
        logging.info(f"done one batch for {repo}")
        database_api.refresh_view()
    wait_time = time_before_reset(github_api)
    if wait_time:
        logging.info(
            f"Reached rate limit, going to sleep for {wait_time} seconds to replenish"
        )
        time.sleep(wait_time)

@click.command()
@click.option(
    "--url-api",
    type=str,
    default="https://api.github.com",
    help="Github token to extend limit rate",
)
@click.option(
    "--type-owner",
    type=click.Choice(["orgs", "users"]),
    help="Type of owner either an orgs or a simple user",
)
@click.option("--owner", type=str, help="Owner name of the account")
@click.option(
    "--chunk-size",
    type=int,
    default=300,
    help="Size max of batch for each api requests",
)
@click.option("--token", type=str, default="", help="Github token to extend limit rate")
@click.option(
    "--refresh-frequency",
    type=int,
    # 10 min
    default=600,
    help="Interval in second between each refresh of stats view",
)
def main(
    url_api: str,
    type_owner: str,
    owner: str,
    chunk_size: int,
    token: str,
    refresh_frequency: int,
):
    headers = {"Authorization": f"token {token}"} if token else {}
    github_api = GithubApi(url_api, headers=headers, chunk_size=chunk_size)
    database_api = DatabaseApi(
        user=os.environ.get("POSTGRES_USER", "NOT_SET"),
        password=os.environ.get("POSTGRES_PASSWORD", "NOT_SET"),
        host=os.environ.get("POSTGRES_HOST", "NOT_SET"),
        port=int(os.environ.get("POSTGRES_PORT", 42)),
        database=os.environ.get("POSTGRES_DB", "NOT_SET")
    )
    refresh_thread = RefreshThread(database_api, refresh_frequency)
    refresh_thread.start()
    while True:
        loop(database_api, github_api, type_owner, owner)


if __name__ == "__main__":
    main()

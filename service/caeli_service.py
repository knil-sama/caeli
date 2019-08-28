import datetime
import os
import click
import logging
import time

from service import github_api
from service import database_api
import service


def time_before_reset(github_client: github_api.GithubApi, api: str = "core") -> int:
    """
    This don't count as rate consumption

    Args:
        api: Name of the github api resource we want rate for
    Returns:
        int: Return 0 if there still "credit" to consume else second to wait before reset
    """
    current_rate = github_client.check_rate()
    if current_rate[api]["remaining"]:
        return 0
    else:
        return current_rate[api]["reset"] - int(datetime.datetime.utcnow().timestamp())


def update_contributors_by_repo(
    database_client: database_api.DatabaseApi,
    github_client: github_api.GithubApi,
    repo_id: int,
    owner: str,
    repo: str,
    since: str,
):
    """
    since YYYY-MM-DDTHH:MM:SSZ
    """
    contributors = database_client.listing_existing_contributors(repo_id)
    list_new_contributors = github_client.listing_new_contributors(
        contributors, owner, repo, since
    )
    database_client.upsert_contributors(repo_id, list_new_contributors)


def update_repos(
    database_client: database_api.DatabaseApi,
    github_client: github_api.GithubApi,
    type_owner: str,
    owner: str,
):
    repositories = github_client.listing_repositories(type_owner, owner)
    database_client.insert_new_repositories(repositories)


def loop(
    database_client: database_api.DatabaseApi,
    github_client: github_api.GithubApi,
    type_owner: str,
    owner: str,
):
    update_repos(database_client, github_client, type_owner, owner)
    repositories = database_client.listing_repositories()
    for repo in repositories:
        update_contributors_by_repo(
            database_client,
            github_client,
            repo_id=repo["id"],
            owner=repo["owner"],
            repo=repo["name"],
            since=repo["last_commit_check"],
        )
        logging.info(f"done one batch for {repo}")
    wait_time = time_before_reset(github_client)
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
    github_client = github_api.GithubApi(
        url_api, headers=headers, chunk_size=chunk_size
    )
    database_client = database_api.DatabaseApi(
        user=service.DB_USER,
        password=service.DB_PASSWORD,
        host=service.DB_HOST,
        port=service.DB_PORT,
        database=service.DB_DATABASE,
    )
    refresh_thread = database_api.RefreshThread(database_client, refresh_frequency)
    refresh_thread.start()
    while True:
        loop(database_client, github_client, type_owner, owner)


if __name__ == "__main__":
    main()

import logging
from threading import Thread
from datetime import datetime
import anosql
import psycopg2
import psycopg2.extras
import tenacity
import service


class DatabaseApi:
    """Class for handling postgres database"""

    def __init__(self, user: str, password: str, host: str, port: int, database: str):
        tables = ["repositories", "contributors", "stats_contributions"]
        self.connection = self._create_connection(user, password, host, port, database)
        # init queries
        self.queries = None
        for table in tables:
            queries = anosql.from_path(
                f"{service.ROOT_DIR}/sql/{table}.sql", "psycopg2"
            )
            if self.queries:
                for qname in queries.available_queries:
                    self.queries.add_query(qname, getattr(queries, qname))
            else:
                self.queries = queries
            # init db
            getattr(self.queries, f"create_{table}")(self.connection)

    @tenacity.retry(stop=tenacity.stop_after_delay(service.TENACITY_DELAY))
    def _create_connection(
        self, user: str, password: str, host: str, port: int, database: str
    ):
        return psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            dbname=database,
            cursor_factory=psycopg2.extras.RealDictCursor,
        )

    def listing_existing_contributors(self, repo_id: int) -> list:
        contributors = list()
        try:
            contributors = self.queries.list_contributors_by_id(
                self.connection, repo_id=repo_id
            )
            logging.info(f"Existing contributors {contributors}")
        except psycopg2.ProgrammingError:
            logging.info(f"No contributors found")
        return contributors

    def upsert_contributors(self, repo_id: int, contributors: list):
        sql_formatted_contributors = [
            {
                "login": new_contributor["author"]["login"],
                "repo_id": repo_id,
                "first_commit_at": new_contributor["commit"]["author"]["date"],
                "commit_json": psycopg2.extras.Json(new_contributor),
            }
            for new_contributor in contributors
        ]
        self.queries.upsert_contributors(self.connection, sql_formatted_contributors)
        if contributors:
            # yes you can have project with 0 contributors https://github.com/facebook/Conditional-character-based-RNN
            self.queries.update_last_commit_check_repositories(
                self.connection,
                last_commit_check=contributors[-1]["commit"]["author"]["date"],
                repo_id=repo_id,
            )

    def listing_repositories(self):
        repositories = list()
        try:
            repositories = self.queries.select_repositories(self.connection)
            logging.info(f"Existing repositories {repositories}")
        except psycopg2.ProgrammingError:
            logging.info(f"No repositories found")
        return repositories

    def insert_new_repositories(self, repositories: list):
        sql_formatted_repositories = [
            {
                "repo_id": repo["id"],
                "name": repo["name"],
                "owner": repo["owner"]["login"],
                "repo_json": psycopg2.extras.Json(repo),
            }
            for repo in repositories
        ]
        self.queries.upsert_repositories(self.connection, sql_formatted_repositories)

    def refresh_view(self):
        self.queries.refresh_stats_contributions(self.connection)

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

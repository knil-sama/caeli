import logging
from threading import Thread
import psycopg2
from psycopg2.extras import Json


class DatabaseApi:
    """Class for handling postgres database"""

    def __init__(self, user: str, password: str, host: str, port: int, database: str):
        tables = ["repositories", "contributors", "stats_contributions"]
        self.connection = psycopg2.connect(
            user=user, password=password, host=host, port=port, dbname=database
        )
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

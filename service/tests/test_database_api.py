import unittest
import psycopg2
import tenacity
import service
from service import database_api


class TestDatabaseApi(unittest.TestCase):
    @tenacity.retry(stop=tenacity.stop_after_delay(service.TENACITY_DELAY))
    def setUp(self):
        connection = psycopg2.connect(
            user=service.DB_USER,
            password=service.DB_PASSWORD,
            host=service.DB_HOST,
            port=service.DB_PORT,
            database=service.DB_DATABASE,
        )
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS repositories, contributors;")
            connection.commit()

    def test_listing_existing_contributors_with_no_value(self):
        database_client = database_api.DatabaseApi(
            user=service.DB_USER,
            password=service.DB_PASSWORD,
            host=service.DB_HOST,
            port=service.DB_PORT,
            database=service.DB_DATABASE,
        )
        self.assertEqual(list(), database_client.listing_existing_contributors(21))

    def test_listing_existing_contributors(self):
        database_client = database_api.DatabaseApi(
            user=service.DB_USER,
            password=service.DB_PASSWORD,
            host=service.DB_HOST,
            port=service.DB_PORT,
            database=service.DB_DATABASE,
        )
        repo_json = {"id": 21, "name": "harold", "owner": {"login": "test"}}
        database_client.insert_new_repositories([repo_json])
        contributor_json = {
            "author": {"login": "knil"},
            "commit": {"author": {"date": "2012-07-09T16:13:30+12:00"}},
        }
        expected_contributors = [contributor_json]
        database_client.upsert_contributors(
            repo_id=repo_json["id"], contributors=expected_contributors
        )
        result_contributors = database_client.listing_existing_contributors(21)
        self.assertEqual(1, len(result_contributors))
        self.assertEqual(
            contributor_json["author"]["login"], result_contributors[0]["login"]
        )

    def test_upsert_contributors_duplicates(self):
        database_client = database_api.DatabaseApi(
            user=service.DB_USER,
            password=service.DB_PASSWORD,
            host=service.DB_HOST,
            port=service.DB_PORT,
            database=service.DB_DATABASE,
        )
        repo_json = {"id": 21, "name": "harold", "owner": {"login": "test"}}
        database_client.insert_new_repositories([repo_json])
        expected_contributors = [
            {
                "author": {"login": "knil"},
                "commit": {"author": {"date": "2012-07-09T16:13:30+12:00"}},
            },
            {
                "author": {"login": "leroy"},
                "commit": {"author": {"date": "2012-07-09T16:13:30+12:00"}},
            },
            {
                "author": {"login": "knil"},
                "commit": {"author": {"date": "2011-07-09T16:13:30+12:00"}},
            },
            {
                "author": {"login": "knil"},
                "commit": {"author": {"date": "2015-07-09T16:13:30+12:00"}},
            },
        ]
        database_client.upsert_contributors(
            repo_id=repo_json["id"], contributors=expected_contributors
        )
        result_contributors = database_client.listing_existing_contributors(21)
        self.assertEqual(2, len(result_contributors))
        self.assertEqual(
            expected_contributors[1]["author"]["login"], result_contributors[0]["login"]
        )
        # offset is +12 from github api
        self.assertEqual(
            "2012-07-09T04:13:30+00:00",
            result_contributors[0]["first_commit_at"].isoformat(),
        )
        self.assertEqual(None, result_contributors[0]["update_at"])

        self.assertEqual(
            expected_contributors[3]["author"]["login"], result_contributors[1]["login"]
        )
        self.assertEqual(
            "2011-07-09T04:13:30+00:00",
            result_contributors[1]["first_commit_at"].isoformat(),
        )
        self.assertNotEqual(None, result_contributors[1]["update_at"].isoformat())

    def test_insert_new_repositories_duplicates(self):
        database_client = database_api.DatabaseApi(
            user=service.DB_USER,
            password=service.DB_PASSWORD,
            host=service.DB_HOST,
            port=service.DB_PORT,
            database=service.DB_DATABASE,
        )
        expected_repositories = [
            {"id": 21, "name": "harold", "owner": {"login": "test"}},
            {"id": 34, "name": "henry", "owner": {"login": "retest"}},
            {"id": 21, "name": "ford", "owner": {"login": "test"}},
        ]
        database_client.insert_new_repositories(expected_repositories)
        result_repositories = database_client.listing_repositories()
        self.assertEqual(2, len(result_repositories))
        self.assertEqual(
            expected_repositories[0]["owner"]["login"], result_repositories[0]["owner"]
        )
        self.assertEqual(
            expected_repositories[0]["name"], result_repositories[0]["name"]
        )
        self.assertEqual(None, result_repositories[0]["last_commit_check"])
        self.assertEqual(
            expected_repositories[1]["owner"]["login"], result_repositories[1]["owner"]
        )
        self.assertEqual(
            expected_repositories[1]["name"], result_repositories[1]["name"]
        )

    def test_listing_repositories_with_no_value(self):
        database_client = database_api.DatabaseApi(
            user=service.DB_USER,
            password=service.DB_PASSWORD,
            host=service.DB_HOST,
            port=service.DB_PORT,
            database=service.DB_DATABASE,
        )
        self.assertEqual(list(), database_client.listing_repositories())

    def test_listing_repositories(self):
        database_client = database_api.DatabaseApi(
            user=service.DB_USER,
            password=service.DB_PASSWORD,
            host=service.DB_HOST,
            port=service.DB_PORT,
            database=service.DB_DATABASE,
        )
        repo_json = {"id": 21, "name": "harold", "owner": {"login": "test"}}
        database_client.insert_new_repositories([repo_json])
        result_repositories = database_client.listing_repositories()
        self.assertEqual(1, len(result_repositories))
        self.assertEqual(repo_json["owner"]["login"], result_repositories[0]["owner"])
        self.assertEqual(repo_json["name"], result_repositories[0]["name"])
        self.assertEqual(None, result_repositories[0]["last_commit_check"])

    def test_refresh_view(self):
        database_client = database_api.DatabaseApi(
            user=service.DB_USER,
            password=service.DB_PASSWORD,
            host=service.DB_HOST,
            port=service.DB_PORT,
            database=service.DB_DATABASE,
        )
        repo_json = {"id": 21, "name": "harold", "owner": {"login": "test"}}
        database_client.insert_new_repositories([repo_json])
        expected_contributors = [
            {
                "author": {"login": "knil"},
                "commit": {"author": {"date": "2012-07-09T16:13:30+12:00"}},
            },
            {
                "author": {"login": "leroy"},
                "commit": {"author": {"date": "2012-07-09T16:13:30+12:00"}},
            },
            {
                "author": {"login": "knil"},
                "commit": {"author": {"date": "2011-07-09T16:13:30+12:00"}},
            },
            {
                "author": {"login": "knil"},
                "commit": {"author": {"date": "2015-07-09T16:13:30+12:00"}},
            },
        ]
        database_client.upsert_contributors(
            repo_id=repo_json["id"], contributors=expected_contributors
        )
        database_client.refresh_view()

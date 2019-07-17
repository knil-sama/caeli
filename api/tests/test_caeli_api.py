import unittest
from unittest.mock import patch, MagicMock
import json
from api import caeli_api


def unjsonify(data) -> str:
    """
    Convert binary to json
    Args:
        data: Binary json returned by Flask
    Returns:
        str:
    """
    return json.loads(data.decode("utf-8"))


class TestCaeliApi(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.connection = caeli_api.connect_db()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS stats_contributions (repository text, date text, number_of_new_contributors int)"
            )
        self.connection.commit()

    def setUp(self):
        """ """
        self.app = caeli_api.create_app()
        self.client = self.app.test_client

    def test_alive(self):
        """ """
        res = self.client().get("/")
        self.assertEqual(res.status_code, 200)
        json_result = unjsonify(res.data)
        self.assertGreater(len(json_result["message"]), 49)

    def test_stats_empty(self):
        with self.connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE stats_contributions")
        self.connection.commit()
        res = self.client().get(f"/stats")
        self.assertEqual(res.status_code, 200)
        json_result = unjsonify(res.data)
        self.assertEqual(json_result["message"], "No results to display")

    def test_stats(self):
        with self.connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE stats_contributions")
            self.connection.commit()
            cursor.execute(
                "INSERT INTO stats_contributions VALUES ('test', '2020-06', 34)"
            )
            self.connection.commit()
        res = self.client().get(f"/stats")
        self.assertEqual(res.status_code, 200)
        json_result = unjsonify(res.data)
        self.assertEqual(
            json_result,
            [
                {
                    "repository": "test",
                    "date": "2020-06",
                    "number_of_new_contributors": 34,
                }
            ],
        )

import unittest
from unittest.mock import patch, MagicMock
import datetime
import requests
from freezegun import freeze_time

from service import caeli_service


class TestCaeliService(unittest.TestCase):
    def test_time_before_reset_no_reset(self):
        mock_github_api = MagicMock()
        mock_github_api.check_rate.return_value = {"fake": {"remaining": 123}}
        self.assertEqual(0, caeli_service.time_before_reset(mock_github_api, "fake"))

    def test_time_before_reset_with_reset(self):
        mock_github_api = MagicMock()
        with freeze_time("2017-01-14 03:21:34"):
            mock_github_api.check_rate.return_value = {
                "core": {
                    "remaining": 0,
                    "reset": int(datetime.datetime(2017, 1, 14, 3, 22, 34).timestamp()),
                }
            }
            self.assertEqual(60, caeli_service.time_before_reset(mock_github_api))

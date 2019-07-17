import unittest
from unittest.mock import patch, MagicMock
import datetime
import requests
from freezegun import freeze_time

from service import caeli_service

class TestCaeliService(unittest.TestCase):
    @patch("service.caeli_service.requests.get")
    def test_listing_repositories(self, mock_request):
        mock_response = MagicMock(status_code=requests.codes.ok)
        mock_response.json.return_value = [{"name": "dmock"}, {"name": "react-native"}]
        mock_request.return_value = mock_response
        github_api = caeli_service.GithubApi("fake_url", headers={}, chunk_size=10)
        res = github_api.listing_repositories(
            "org", "facebook"
        )
        self.assertEqual(list(mock_response.json.return_value), res)

    @patch("service.caeli_service.requests.get")
    def test_check_rate(self,mock_request):
        test_rate_limit = {
            "rate": {"limit": 60, "remaining": 60, "reset": 1564304920},
            "resources": {
                "core": {"limit": 60, "remaining": 60, "reset": 1564304920},
                "graphql": {"limit": 0, "remaining": 0, "reset": 1564304920},
                "integration_manifest": {
                    "limit": 5000,
                    "remaining": 5000,
                    "reset": 1564304920,
                },
                "search": {"limit": 10, "remaining": 10, "reset": 1564301380},
            },
        }
        mock_response = MagicMock(status_code=requests.codes.ok)
        mock_response.json.return_value = test_rate_limit
        mock_request.return_value = mock_response
        github_api = caeli_service.GithubApi("fake_url", headers={}, chunk_size=10)
        res = github_api.check_rate()
        self.assertEqual(test_rate_limit["resources"], res)

    def test_time_before_reset_no_reset(self):
        mock_github_api = MagicMock()
        mock_github_api.check_rate.return_value = {"fake": {"remaining": 123}}
        self.assertEqual(0, caeli_service.time_before_reset(mock_github_api, "fake"))
    
    def test_time_before_reset_with_reset(self):
        mock_github_api = MagicMock()
        with freeze_time("2017-01-14 03:21:34"):
            mock_github_api.check_rate.return_value = {"core": {"remaining": 0, "reset":  int(datetime.datetime(2017, 1, 14, 3, 22, 34).timestamp())}}
            self.assertEqual(60, caeli_service.time_before_reset(mock_github_api))

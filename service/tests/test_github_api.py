import unittest
from unittest.mock import patch, MagicMock
import datetime
import requests
from freezegun import freeze_time

from service import github_api

class TestGithubApi(unittest.TestCase):
    @patch("service.github_api.requests.get")
    def test_listing_repositories(self, mock_request):
        mock_response = MagicMock(status_code=requests.codes.ok)
        mock_response.json.return_value = [{"name": "dmock"}, {"name": "react-native"}]
        mock_request.return_value = mock_response
        github_client = github_api.GithubApi("fake_url", headers={}, chunk_size=10)
        res = github_client.listing_repositories("org", "facebook")
        self.assertEqual(list(mock_response.json.return_value), res)

    @patch("service.github_api.requests.get")
    def test_check_rate(self, mock_request):
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
        github_client = github_api.GithubApi("fake_url", headers={}, chunk_size=10)
        res = github_client.check_rate()
        self.assertEqual(test_rate_limit["resources"], res)



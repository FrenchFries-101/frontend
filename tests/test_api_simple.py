from unittest.mock import Mock, patch

import requests

from service import api
from service import api_forum


def test_get_cambridge_list_success():
    fake_response = Mock()
    fake_response.json.return_value = [{"cambridge_id": 19}]

    with patch("service.api.requests.get", return_value=fake_response) as mock_get:
        result = api.get_cambridge_list()

    assert result == [{"cambridge_id": 19}]
    mock_get.assert_called_once_with(f"{api.BASE_URL}/listening/cambridge")


def test_get_sections_passes_params():
    fake_response = Mock()
    fake_response.json.return_value = {"sections": []}

    with patch("service.api.requests.get", return_value=fake_response) as mock_get:
        result = api.get_sections(test_id=12, user_id=3)

    assert result == {"sections": []}
    mock_get.assert_called_once_with(
        f"{api.BASE_URL}/listening/sections",
        params={"test_id": 12, "user_id": 3},
    )


def test_get_categories_returns_empty_list_on_error():
    with patch("service.api.requests.get", side_effect=requests.RequestException("boom")):
        result = api.get_categories()

    assert result == []


def test_forum_get_posts_returns_empty_dict_on_http_error():
    bad_response = Mock()
    bad_response.raise_for_status.side_effect = requests.HTTPError("500")

    with patch("service.api_forum.requests.get", return_value=bad_response):
        result = api_forum.get_posts(page=1, page_size=20)

    assert result == {}

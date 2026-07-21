import os
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from dotenv import load_dotenv

from substack import Api
from substack.exceptions import SubstackAPIException

load_dotenv()


def _api_from_env() -> Api:
    cookies_string = os.getenv("COOKIES_STRING")
    cookies_path = os.getenv("COOKIES_PATH")
    publication_url = os.getenv("PUBLICATION_URL")
    if cookies_string or cookies_path:
        return Api(
            cookies_string=cookies_string,
            cookies_path=cookies_path,
            publication_url=publication_url,
        )
    return Api(
        email=os.getenv("EMAIL"),
        password=os.getenv("PASSWORD"),
        publication_url=publication_url,
    )


_e2e = unittest.skipUnless(
    os.getenv("RUN_SUBSTACK_E2E"),
    "set RUN_SUBSTACK_E2E=1 and configure credentials to run live API tests",
)


class ApiTest(unittest.TestCase):
    def test_api_retries_rate_limited_get_and_delete_requests(self):
        publication = {
            "subdomain": "writer",
            "publication_url": "https://writer.substack.com",
        }
        with (
            patch("requests.Session") as session_class,
            patch.object(Api, "get_user_primary_publication", return_value=publication),
            patch.object(Api, "change_publication"),
        ):
            Api(cookies_string="sid=value")

        adapters = [
            call.args[1] for call in session_class.return_value.mount.call_args_list
        ]
        self.assertEqual(len(adapters), 2)
        retry = adapters[0].max_retries
        self.assertEqual(retry.total, 4)
        self.assertEqual(retry.status, 4)
        self.assertEqual(retry.status_forcelist, (429,))
        self.assertEqual(retry.allowed_methods, frozenset({"GET", "DELETE"}))
        self.assertFalse(retry.raise_on_status)

    def test_api_exception(self):
        response = Mock(status_code=401, text="Unauthorized")
        with self.assertRaises(SubstackAPIException):
            with patch("requests.Session.post", return_value=response):
                Api(email="", password="")

    def test_get_publication_subscriber_count_from_legacy_response(self):
        api = Api.__new__(Api)
        api.publication_url = "https://writer.substack.com/api/v1"
        api._session = Mock()
        response = Mock(status_code=200)
        response.json.return_value = {"subscriberCount": 123}
        api._session.get.return_value = response

        self.assertEqual(api.get_publication_subscriber_count(), 123)

    def test_get_publication_subscriber_count_from_subscribers(self):
        api = Api.__new__(Api)
        api.publication_url = "https://writer.substack.com/api/v1"
        api._session = Mock()
        response = Mock(status_code=200)
        response.json.return_value = {"subscribers": [{"id": 1}, {"id": 2}]}
        api._session.get.return_value = response

        self.assertEqual(api.get_publication_subscriber_count(), 2)

    def test_get_publication_subscriber_count_prefers_legacy_count(self):
        api = Api.__new__(Api)
        api.publication_url = "https://writer.substack.com/api/v1"
        api._session = Mock()
        response = Mock(status_code=200)
        response.json.return_value = {
            "subscriberCount": 123,
            "subscribers": [{"id": 1}],
        }
        api._session.get.return_value = response

        self.assertEqual(api.get_publication_subscriber_count(), 123)

    def test_schedule_draft_uses_scheduled_release_contract(self):
        api = Api.__new__(Api)
        api.publication_url = "https://writer.substack.com/api/v1"
        api._session = Mock()
        response = Mock(status_code=200)
        response.json.return_value = {"scheduled": True}
        api._session.post.return_value = response
        scheduled_at = datetime(2030, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

        self.assertEqual(
            api.schedule_draft(42, scheduled_at),
            {"scheduled": True},
        )
        api._session.post.assert_called_once_with(
            "https://writer.substack.com/api/v1/drafts/42/scheduled_release",
            json={"trigger_at": "2030-01-02T03:04:05+00:00"},
        )

    def test_unschedule_draft_deletes_scheduled_release(self):
        api = Api.__new__(Api)
        api.publication_url = "https://writer.substack.com/api/v1"
        api._session = Mock()
        response = Mock(status_code=200)
        response.json.return_value = {"scheduled": False}
        api._session.delete.return_value = response

        self.assertEqual(api.unschedule_draft(42), {"scheduled": False})
        api._session.delete.assert_called_once_with(
            "https://writer.substack.com/api/v1/drafts/42/scheduled_release"
        )

    @pytest.mark.live
    @_e2e
    def test_get_posts(self):
        api = _api_from_env()
        posts = api.get_posts()
        self.assertIsNotNone(posts)

    @pytest.mark.live
    @_e2e
    def test_get_drafts(self):
        api = _api_from_env()
        drafts = api.get_drafts()
        self.assertIsNotNone(drafts)

    @pytest.mark.live
    @_e2e
    def test_publication_users(self):
        api = _api_from_env()
        users = api.get_publication_users()
        self.assertIsNotNone(users)

    @pytest.mark.live
    @_e2e
    def test_get_categories(self):
        api = _api_from_env()
        categories = api.get_categories()
        self.assertIsNotNone(categories)

    @pytest.mark.live
    @_e2e
    def test_get_single_category(self):
        api = _api_from_env()
        category = api.get_single_category(4, "all", limit=100)
        self.assertIsNotNone(category)

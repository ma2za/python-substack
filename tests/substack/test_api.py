import os
import unittest

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
    def test_api_exception(self):
        with self.assertRaises(SubstackAPIException):
            Api(email="", password="")

    @_e2e
    def test_get_posts(self):
        api = _api_from_env()
        posts = api.get_posts()
        self.assertIsNotNone(posts)

    @_e2e
    def test_get_drafts(self):
        api = _api_from_env()
        drafts = api.get_drafts()
        self.assertIsNotNone(drafts)

    @_e2e
    def test_publication_users(self):
        api = _api_from_env()
        users = api.get_publication_users()
        self.assertIsNotNone(users)

    @_e2e
    def test_get_categories(self):
        api = _api_from_env()
        categories = api.get_categories()
        self.assertIsNotNone(categories)

    @_e2e
    def test_get_single_category(self):
        api = _api_from_env()
        category = api.get_single_category(4, "all", limit=100)
        self.assertIsNotNone(category)

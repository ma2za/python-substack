import logging

import requests

from substack.exceptions import SubstackAPIException, SubstackRequestException

logger = logging.getLogger(__name__)


class Api:
    """

    A python interface into the Substack API

    """

    def __init__(
        self,
        email: str,
        password: str,
        base_url: str | None = None,
        publication_url: str | None = None,
        debug: bool = False,
    ):
        """

        To create an instance of the substack.Api class:
            >>> import substack
            >>> api = substack.Api(email="substack email", password="substack password")

        Args:
          email:
          password:
          base_url:
            The base URL to use to contact the Substack API.
            Defaults to https://substack.com/api/v1.
        """
        self.base_url = base_url or "https://substack.com/api/v1"
        self.publication_url = publication_url

        if debug:
            logging.basicConfig()
            logging.getLogger().setLevel(logging.DEBUG)

        self._init_session(email, password)

    def login(self, email: str, password: str) -> dict:
        """

        Args:
          email:
          password:
        """

        response = self._session.post(
            f"{self.base_url}/login",
            json={
                "captcha_response": None,
                "email": email,
                "for_pub": "",
                "password": password,
                "redirect": "/",
            },
        )
        return Api._handle_response(response=response)

    def _init_session(self, email, password):
        self._session = requests.Session()

        self.login(email, password)

    @staticmethod
    def _handle_response(response: requests.Response):
        """

        Internal helper for handling API responses from the Substack server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.

        """

        if not (200 <= response.status_code < 300):
            raise SubstackAPIException(response.status_code, response.text)
        try:
            return response.json()
        except ValueError:
            raise SubstackRequestException("Invalid Response: %s" % response.text)

    def get_publication_users(self):
        """

        :return:
        """
        response = self._session.get(f"{self.publication_url}/publication/users")

        return Api._handle_response(response=response)

    def get_posts(self) -> dict:
        """

        :return:
        """
        response = self._session.get(f"{self.base_url}/reader/posts")

        return Api._handle_response(response=response)

    def get_drafts(self, filter: str = None, offset: int = None, limit: int = None):
        response = self._session.get(
            f"{self.publication_url}/drafts",
            params={"filter": filter, "offset": offset, "limit": limit},
        )
        return Api._handle_response(response=response)

    def post_draft(
        self,
        draft_bylines: list,
        title: str = None,
        subtitle: str = None,
        body: str = None,
    ) -> dict:
        """

        Args:
          draft_bylines:
          title:
          subtitle:
          body:

        Returns:

        """
        response = self._session.post(
            f"{self.publication_url}/drafts",
            json={
                "draft_bylines": draft_bylines,
                "draft_title": title,
                "draft_subtitle": subtitle,
                "draft_body": body,
            },
        )
        return Api._handle_response(response=response)

    def put_draft(
        self,
        draft: str,
        title: str = None,
        subtitle: str = None,
        body: str = None,
        cover_image: str = None,
    ) -> dict:
        """

        Args:
            draft:
            title:
            subtitle:
            body:
            cover_image:

        Returns:

        """

        response = self._session.put(
            f"{self.publication_url}/drafts/{draft}",
            json={
                "draft_title": title,
                "draft_subtitle": subtitle,
                "draft_body": body,
                "cover_image": cover_image,
            },
        )
        return Api._handle_response(response=response)

    def prepublish_draft(self, draft: str) -> dict:
        """

        Args:
            draft:

        Returns:

        """

        response = self._session.get(
            f"{self.publication_url}/drafts/{draft}/prepublish"
        )
        return Api._handle_response(response=response)

    def publish_draft(
        self, draft: str, send: bool = True, share_automatically: bool = False
    ) -> dict:
        """

        Args:
            draft:
            send:
            share_automatically:

        Returns:

        """
        response = requests.post(
            f"{self.publication_url}/drafts/{draft}/publish",
            json={"send": send, "share_automatically": share_automatically},
        )
        return Api._handle_response(response=response)

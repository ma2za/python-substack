import logging

import requests

from substack.exceptions import SubstackAPIException, SubstackRequestException

logger = logging.getLogger(__name__)


class Api:
    """

    A python interface into the Substack API

    """

    def __init__(self, email: str, password: str, base_url: str | None = None, debug: bool = False):
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

        if debug:
            logging.basicConfig()
            logging.getLogger().setLevel(logging.DEBUG)

        self._init_session(email, password)

    def login(self, email: str, password: str):
        """

        Args:
          email:
          password:
        """

        response = self._session.post(f"{self.base_url}/login", json={"captcha_response": None,
                                                                      "email": email,
                                                                      "for_pub": "",
                                                                      "password": password,
                                                                      "redirect": "/"})
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
            raise SubstackRequestException('Invalid Response: %s' % response.text)

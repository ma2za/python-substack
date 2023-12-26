"""

API Wrapper

"""

import base64
import json
import logging
import os
from datetime import datetime
from urllib.parse import urljoin

import requests

from substack.exceptions import SubstackAPIException, SubstackRequestException

logger = logging.getLogger(__name__)

__all__ = ["Api"]


class Api:
    """

    A python interface into the Substack API

    """

    def __init__(
        self,
        email=None,
        password=None,
        cookies_path=None,
        base_url=None,
        publication_url=None,
        debug=False,
    ):
        """

        To create an instance of the substack.Api class:
            >>> import substack
            >>> api = substack.Api(email="substack email", password="substack password")

        Args:
          email:
          password:
          cookies_path
            To re-use your session without logging in each time, you can save your cookies to a json file and
            then load them in the next session.
            Make sure to re-save your cookies, as they do update over time.
          base_url:
            The base URL to use to contact the Substack API.
            Defaults to https://substack.com/api/v1.
        """
        self.base_url = base_url or "https://substack.com/api/v1"

        if debug:
            logging.basicConfig()
            logging.getLogger().setLevel(logging.DEBUG)

        self._session = requests.Session()

        # Load cookies from file if provided
        # Helps with Captcha errors by reusing cookies from "local" auth, then switching to running code in the cloud
        if cookies_path is not None:
            with open(cookies_path) as f:
                cookies = json.load(f)
            self._session.cookies.update(cookies)

        elif email is not None and password is not None:
            self.login(email, password)
        else:
            raise ValueError(
                "Must provide email and password or cookies_path to authenticate."
            )

        user_publication = None
        # if the user provided a publication url, then use that
        if publication_url:
            import re

            # Regular expression to extract subdomain name
            match = re.search(r"https://(.*).substack.com", publication_url.lower())
            subdomain = match.group(1) if match else None

            user_publications = self.get_user_publications()
            # search through publications to find the publication with the matching subdomain
            for publication in user_publications:
                if publication["subdomain"] == subdomain:
                    # set the current publication to the users publication
                    user_publication = publication
                    break
        else:
            # get the users primary publication
            user_publication = self.get_user_primary_publication()

        # set the current publication to the users primary publication
        self.change_publication(user_publication)

    def login(self, email, password) -> dict:
        """

        Login to the substack account.

        Args:
          email: substack account email
          password: substack account password
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

    def signin_for_pub(self, publication):
        """
        Complete the signin process
        """
        response = self._session.get(
            f"https://substack.com/sign-in?redirect=%2F&for_pub={publication['subdomain']}",
        )
        try:
            output = Api._handle_response(response=response)
        except SubstackRequestException as ex:
            output = {}
        return output

    def change_publication(self, publication):
        """
        Change the publication URL
        """
        self.publication_url = urljoin(publication["publication_url"], "api/v1")

        # sign-in to the publication
        self.signin_for_pub(publication)

    def export_cookies(self, path: str = "cookies.json"):
        """
        Export cookies to a json file.
        Args:
            path: path to the json file
        """
        cookies = self._session.cookies.get_dict()
        with open(path, "w") as f:
            json.dump(cookies, f)

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

    def get_user_id(self):
        """

        Returns:

        """
        profile = self.get_user_profile()
        user_id = profile["id"]

        return user_id

    @staticmethod
    def get_publication_url(publication: dict) -> str:
        """
        Gets the publication url

        Args:
            publication:
        """
        custom_domain = publication["custom_domain"]
        if not custom_domain:
            publication_url = f"https://{publication['subdomain']}.substack.com"
        else:
            publication_url = f"https://{custom_domain}"

        return publication_url

    def get_user_primary_publication(self):
        """
        Gets the users primary publication
        """

        profile = self.get_user_profile()
        primary_publication = profile["primaryPublication"]
        primary_publication["publication_url"] = self.get_publication_url(
            primary_publication
        )

        return primary_publication

    def get_user_publications(self):
        """
        Gets the users publications
        """

        profile = self.get_user_profile()

        # Loop through users "publicationUsers" list, and return a list
        # of dictionaries of "name", and "subdomain", and "id"
        user_publications = []
        for publication in profile["publicationUsers"]:
            pub = publication["publication"]
            pub["publication_url"] = self.get_publication_url(pub)
            user_publications.append(pub)

        return user_publications

    def get_user_profile(self):
        """
        Gets the users profile
        """
        response = self._session.get(f"{self.base_url}/user/profile/self")

        return Api._handle_response(response=response)

    def get_user_settings(self):
        """
        Get list of users.

        Returns:

        """
        response = self._session.get(f"{self.base_url}/settings")

        return Api._handle_response(response=response)

    def get_publication_users(self):
        """
        Get list of users.

        Returns:

        """
        response = self._session.get(f"{self.publication_url}/publication/users")

        return Api._handle_response(response=response)

    def get_publication_subscriber_count(self):

        """
        Get subscriber count.

        Returns:

        """
        response = self._session.get(
            f"{self.publication_url}/publication_launch_checklist"
        )

        return Api._handle_response(response=response)["subscriberCount"]

    def get_published_posts(
        self, offset=0, limit=25, order_by="post_date", order_direction="desc"
    ):
        """
        Get list of published posts for the publication.
        """
        response = self._session.get(
            f"{self.publication_url}/post_management/published",
            params={
                "offset": offset,
                "limit": limit,
                "order_by": order_by,
                "order_direction": order_direction,
            },
        )

        return Api._handle_response(response=response)

    def get_posts(self) -> dict:
        """

        Returns:

        """
        response = self._session.get(f"{self.base_url}/reader/posts")

        return Api._handle_response(response=response)

    def get_drafts(self, filter=None, offset=None, limit=None):
        """

        Args:
            filter:
            offset:
            limit:

        Returns:

        """
        response = self._session.get(
            f"{self.publication_url}/drafts",
            params={"filter": filter, "offset": offset, "limit": limit},
        )
        return Api._handle_response(response=response)

    def get_draft(self, draft_id):
        """
        Gets a draft given it's id.

        """
        response = self._session.get(f"{self.publication_url}/drafts/{draft_id}")
        return Api._handle_response(response=response)

    def delete_draft(self, draft_id):
        """

        Args:
            draft_id:

        Returns:

        """
        response = self._session.delete(f"{self.publication_url}/drafts/{draft_id}")
        return Api._handle_response(response=response)

    def post_draft(self, body) -> dict:
        """

        Args:
          body:

        Returns:

        """
        response = self._session.post(f"{self.publication_url}/drafts", json=body)
        return Api._handle_response(response=response)

    def put_draft(self, draft, **kwargs) -> dict:
        """

        Args:
            draft:
            **kwargs:

        Returns:

        """
        response = self._session.put(
            f"{self.publication_url}/drafts/{draft}",
            json=kwargs,
        )
        return Api._handle_response(response=response)

    def prepublish_draft(self, draft) -> dict:
        """

        Args:
            draft: draft id

        Returns:

        """

        response = self._session.get(
            f"{self.publication_url}/drafts/{draft}/prepublish"
        )
        return Api._handle_response(response=response)

    def publish_draft(
        self, draft, send: bool = True, share_automatically: bool = False
    ) -> dict:
        """

        Args:
            draft: draft id
            send:
            share_automatically:

        Returns:

        """
        response = self._session.post(
            f"{self.publication_url}/drafts/{draft}/publish",
            json={"send": send, "share_automatically": share_automatically},
        )
        return Api._handle_response(response=response)

    def schedule_draft(self, draft, draft_datetime: datetime) -> dict:
        """

        Args:
            draft: draft id
            draft_datetime: datetime to schedule the draft

        Returns:

        """
        response = self._session.post(
            f"{self.publication_url}/drafts/{draft}/schedule",
            json={"post_date": draft_datetime.isoformat()},
        )
        return Api._handle_response(response=response)

    def unschedule_draft(self, draft) -> dict:
        """

        Args:
            draft: draft id

        Returns:

        """
        response = self._session.post(
            f"{self.publication_url}/drafts/{draft}/schedule", json={"post_date": None}
        )
        return Api._handle_response(response=response)

    def get_image(self, image: str):
        """

        This method generates a new substack link that contains the image.

        Args:
            image: filepath or original url of image.

        Returns:

        """
        if os.path.exists(image):
            with open(image, "rb") as file:
                image = b"data:image/jpeg;base64," + base64.b64encode(file.read())

        response = self._session.post(
            f"{self.publication_url}/image",
            data={"image": image},
        )
        return Api._handle_response(response=response)

    def get_categories(self):
        """

        Retrieve list of all available categories.

        Returns:

        """
        response = self._session.get(f"{self.base_url}/categories")
        return Api._handle_response(response=response)

    def get_category(self, category_id, category_type, page):
        """

        Args:
            category_id:
            category_type:
            page:

        Returns:

        """
        response = self._session.get(
            f"{self.base_url}/category/public/{category_id}/{category_type}",
            params={"page": page},
        )
        return Api._handle_response(response=response)

    def get_single_category(self, category_id, category_type, page=None, limit=None):
        """

        Args:
            category_id:
            category_type: paid or all
            page: by default substack retrieves only the first 25 publications in the category. If this is left None,
                  then all pages will be retrieved. The page size is 25 publications.
            limit:
        Returns:

        """
        if page is not None:
            output = self.get_category(category_id, category_type, page)
        else:
            publications = []
            page = 0
            while True:
                page_output = self.get_category(category_id, category_type, page)
                publications.extend(page_output.get("publications", []))
                if (
                    limit is not None and limit <= len(publications)
                ) or not page_output.get("more", False):
                    publications = publications[:limit]
                    break
                page += 1
            output = {
                "publications": publications,
                "more": page_output.get("more", False),
            }
        return output

    def delete_all_drafts(self):
        """

        Returns:

        """
        response = None
        while True:
            drafts = self.get_drafts(filter="draft", limit=10, offset=0)
            if len(drafts) == 0:
                break
            for draft in drafts:
                response = self.delete_draft(draft.get("id"))
        return response

    def get_sections(self):
        """
        Get a list of the sections of your publication.

        TODO: this is hacky but I cannot find another place where to get the sections.
        Returns:

        """
        response = self._session.get(
            f"{self.publication_url}/subscriptions",
        )
        content = Api._handle_response(response=response)
        sections = [
            p.get("sections")
            for p in content.get("publications")
            if p.get("hostname") in self.publication_url
        ]
        return sections[0]

    def publication_embed(self, url):
        """

        Args:
            url:

        Returns:

        """
        return self.call("/publication/embed", "GET", url=url)

    def call(self, endpoint, method, **params):
        """

        Args:
            endpoint:
            method:
            **params:

        Returns:

        """
        response = self._session.request(
            method=method,
            url=f"{self.publication_url}/{endpoint}",
            params=params,
        )
        return Api._handle_response(response=response)

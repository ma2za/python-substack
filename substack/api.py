import base64
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
          base_url:
            The base URL to use to contact the Substack API.
            Defaults to https://substack.com/api/v1.
        """
        self.base_url = base_url or "https://substack.com/api/v1"
        if publication_url:
            self.change_publication(publication_url)

        if debug:
            logging.basicConfig()
            logging.getLogger().setLevel(logging.DEBUG)

        self._session = requests.Session()

        if email is not None and password is not None:
            self.login(email, password)

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
    
    def change_publication(self, publication_url):
        """
        Change the publication URL
        """
        self.publication_url = urljoin(publication_url, "api/v1")

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
        profile = self.get_user_profile()
        user_id = profile['id']

        return user_id

    def get_user_primary_publication(self):
        """
        Gets the users primary publication
        """

        profile = self.get_user_profile()
        primary_publication = profile['primaryPublication']
        return {
            "id": primary_publication['id'],
            "name": primary_publication['name'],
            "publication_url": f"https://{primary_publication['subdomain']}.substack.com"
        }
    
    def get_user_publications(self):
        """
        Gets the users publications
        """

        profile = self.get_user_profile()

        # Loop through users "publicationUsers" list, and return a list of dictionaries of "name", and "subdomain", and "id"
        user_publications = []
        for publication in profile['publicationUsers']:
            user_publications.append({"id": publication['publication_id'], 
                "name": publication['publication']['name'], 
                "publication_url": f"https://{publication['publication']['subdomain']}.substack.com"
            })
        
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
        response = self._session.get(f"{self.publication_url}/publication_launch_checklist")

        return Api._handle_response(response=response)['subscriberCount']

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

    def put_draft(
            self,
            draft,
            **kwargs
    ) -> dict:
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
        sections = [p.get("sections") for p in content.get("publications") if p.get("hostname") in self.publication_url]
        return sections[0]

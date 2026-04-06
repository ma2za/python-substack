"""API Wrapper."""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from typing import TYPE_CHECKING
from urllib.parse import unquote, urljoin

import requests

from substack.exceptions import SubstackAPIException, SubstackRequestException
from substack.models import PostMetadata

if TYPE_CHECKING:
    from datetime import datetime

logger = logging.getLogger(__name__)

__all__ = ["Api"]


class Api:
    """A python interface into the Substack API."""

    def __init__(
        self,
        email=None,
        password=None,
        cookies_path=None,
        base_url=None,
        publication_url=None,
        debug=False,
        cookies_string=None,
    ) -> None:
        self.base_url = base_url or "https://substack.com/api/v1"

        if debug:
            logging.basicConfig()
            logging.getLogger().setLevel(logging.DEBUG)

        self._session = requests.Session()

        if cookies_path is not None:
            with open(cookies_path) as f:
                cookies = json.load(f)
            self._session.cookies.update(cookies)
        elif cookies_string is not None:
            cookies = self._parse_cookies_string(cookies_string)
            self._session.cookies.update(cookies)
        elif email is not None and password is not None:
            self.login(email, password)
        else:
            raise ValueError(
                "Must provide email and password, cookies_path, or cookies_string to authenticate."
            )

        user_publication = None
        if publication_url:
            match = re.search(r"https://(.*).substack.com", publication_url.lower())
            subdomain = match.group(1) if match else None

            user_publications = self.get_user_publications()
            for publication in user_publications:
                if publication["subdomain"] == subdomain:
                    user_publication = publication
                    break

            # Fallback: construct publication dict if not in user's list
            if user_publication is None and subdomain:
                user_publication = {
                    "subdomain": subdomain,
                    "publication_url": f"https://{subdomain}.substack.com",
                }
        else:
            user_publication = self.get_user_primary_publication()

        self.change_publication(user_publication)

    @staticmethod
    def _parse_cookies_string(cookies_string: str) -> dict:
        cookies = {}
        for cookie_pair in cookies_string.split(";"):
            cookie_pair = cookie_pair.strip()
            if not cookie_pair:
                continue
            if "=" in cookie_pair:
                key, value = cookie_pair.split("=", 1)
                key = key.strip()
                value = value.strip()
                value = unquote(value)
                cookies[key] = value
        return cookies

    def login(self, email, password) -> dict:
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
        response = self._session.get(
            f"https://substack.com/sign-in?redirect=%2F&for_pub={publication['subdomain']}",
        )
        try:
            output = Api._handle_response(response=response)
        except SubstackRequestException:
            output = {}
        return output

    def change_publication(self, publication) -> None:
        self.publication = publication
        self.publication_url = urljoin(publication["publication_url"], "api/v1")
        self.signin_for_pub(publication)

    def export_cookies(self, path: str = "cookies.json") -> None:
        cookies = self._session.cookies.get_dict()
        with open(path, "w") as f:
            json.dump(cookies, f)

    @staticmethod
    def _handle_response(response: requests.Response):
        if not (200 <= response.status_code < 300):
            raise SubstackAPIException(response.status_code, response.text)
        try:
            return response.json()
        except ValueError:
            raise SubstackRequestException(f"Invalid Response: {response.text}")

    def get_user_id(self):
        profile = self.get_user_profile()
        return profile["id"]

    @staticmethod
    def get_publication_url(publication: dict) -> str:
        custom_domain = publication.get("custom_domain")
        if not custom_domain and not publication.get("custom_domain_optional"):
            publication_url = f"https://{publication['subdomain']}.substack.com"
        else:
            publication_url = f"https://{custom_domain}"
        return publication_url

    def get_user_primary_publication(self):
        profile = self.get_user_profile()
        primary_publication = None

        if (
            "primaryPublication" in profile
            and profile["primaryPublication"] is not None
        ):
            primary_publication = profile["primaryPublication"]
        else:
            publication_users = profile.get("publicationUsers")
            if publication_users is not None and len(publication_users) > 0:
                for pub_user in publication_users:
                    if pub_user.get("is_primary", False):
                        primary_publication = pub_user.get("publication")
                        if primary_publication:
                            break
                if primary_publication is None:
                    primary_publication = publication_users[0].get("publication")

        if primary_publication is None:
            raise SubstackRequestException(
                "Could not find primary publication in profile"
            )

        primary_publication["publication_url"] = self.get_publication_url(
            primary_publication
        )
        return primary_publication

    def get_user_publications(self):
        profile = self.get_user_profile()
        user_publications = []
        publication_users = profile.get("publicationUsers")

        if publication_users is None:
            return user_publications

        for publication in publication_users:
            pub = publication.get("publication")
            if pub is not None:
                pub["publication_url"] = self.get_publication_url(pub)
                user_publications.append(pub)

        return user_publications

    def get_user_profile(self):
        response = self._session.get(f"{self.base_url}/user/profile/self")
        return Api._handle_response(response=response)

    def get_user_settings(self):
        response = self._session.get(f"{self.base_url}/settings")
        return Api._handle_response(response=response)

    def get_publication_users(self):
        response = self._session.get(f"{self.publication_url}/publication/users")
        return Api._handle_response(response=response)

    def get_publication_subscriber_count(self):
        response = self._session.get(
            f"{self.publication_url}/publication_launch_checklist"
        )
        return Api._handle_response(response=response)["subscriberCount"]

    def get_published_posts(
        self, offset=0, limit=25, order_by="post_date", order_direction="desc"
    ):
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
        response = self._session.get(f"{self.base_url}/reader/posts")
        return Api._handle_response(response=response)

    def get_drafts(self, filter=None, offset=None, limit=None):
        response = self._session.get(
            f"{self.publication_url}/drafts",
            params={"filter": filter, "offset": offset, "limit": limit},
        )
        return Api._handle_response(response=response)

    def get_draft(self, draft_id):
        response = self._session.get(f"{self.publication_url}/drafts/{draft_id}")
        return Api._handle_response(response=response)

    def delete_draft(self, draft_id):
        response = self._session.delete(f"{self.publication_url}/drafts/{draft_id}")
        return Api._handle_response(response=response)

    def post_draft(self, body) -> dict:
        response = self._session.post(f"{self.publication_url}/drafts", json=body)
        return Api._handle_response(response=response)

    def put_draft(self, draft, **kwargs) -> dict:
        response = self._session.put(
            f"{self.publication_url}/drafts/{draft}",
            json=kwargs,
        )
        return Api._handle_response(response=response)

    def prepublish_draft(self, draft) -> dict:
        response = self._session.get(
            f"{self.publication_url}/drafts/{draft}/prepublish"
        )
        return Api._handle_response(response=response)

    def publish_draft(
        self, draft, send: bool = True, share_automatically: bool = False
    ) -> dict:
        response = self._session.post(
            f"{self.publication_url}/drafts/{draft}/publish",
            json={"send": send, "share_automatically": share_automatically},
        )
        return Api._handle_response(response=response)

    def schedule_draft(self, draft, draft_datetime: datetime) -> dict:
        response = self._session.post(
            f"{self.publication_url}/drafts/{draft}/schedule",
            json={"post_date": draft_datetime.isoformat()},
        )
        return Api._handle_response(response=response)

    def unschedule_draft(self, draft) -> dict:
        response = self._session.post(
            f"{self.publication_url}/drafts/{draft}/schedule",
            json={"post_date": None},
        )
        return Api._handle_response(response=response)

    def get_image(self, image: str):
        if os.path.exists(image):
            with open(image, "rb") as file:
                image = b"data:image/jpeg;base64," + base64.b64encode(file.read())

        response = self._session.post(
            f"{self.publication_url}/image",
            data={"image": image},
        )
        return Api._handle_response(response=response)

    def add_tags_to_post(self, post_id: int, tag_names: list) -> dict:
        results = []
        for tag_name in tag_names:
            result = self.add_tag_to_post(post_id, tag_name)
            results.append(result)
        return {"tags_added": results}

    def get_publication_post_tags(self) -> list:
        response = self._session.get(f"{self.publication_url}/publication/post-tag")
        return Api._handle_response(response=response)

    def add_tag_to_post(self, post_id: int, tag_name: str) -> dict:
        existing_tags = self.get_publication_post_tags() or []
        existing_tag = next(
            (tag for tag in existing_tags if tag.get("name") == tag_name),
            None,
        )

        if existing_tag is not None:
            tag_id = existing_tag["id"]
        else:
            create_tag_response = self._session.post(
                f"{self.publication_url}/publication/post-tag",
                json={"name": tag_name},
            )
            tag_data = Api._handle_response(create_tag_response)
            tag_id = tag_data["id"]

        apply_tag_response = self._session.post(
            f"{self.publication_url}/post/{post_id}/tag/{tag_id}",
        )
        return Api._handle_response(apply_tag_response)

    def get_categories(self):
        response = self._session.get(f"{self.base_url}/categories")
        return Api._handle_response(response=response)

    def get_category(self, category_id, category_type, page):
        response = self._session.get(
            f"{self.base_url}/category/public/{category_id}/{category_type}",
            params={"page": page},
        )
        return Api._handle_response(response=response)

    def get_single_category(self, category_id, category_type, page=None, limit=None):
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
        response = None
        while True:
            drafts = self.get_drafts(filter="draft", limit=10, offset=0)
            if len(drafts) == 0:
                break
            for draft in drafts:
                response = self.delete_draft(draft.get("id"))
        return response

    def get_sections(self):
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
        return self.call("/publication/embed", "GET", url=url)

    def call(self, endpoint, method, **params):
        response = self._session.request(
            method=method,
            url=f"{self.publication_url}/{endpoint}",
            params=params,
        )
        return Api._handle_response(response=response)

    # ---- Higher-level helpers returning dataclasses ----

    def schedule_release(
        self,
        draft_id: int,
        trigger_at: datetime,
        post_audience: str = "everyone",
        email_audience: str = "only_free",
    ) -> None:
        """Schedule a post's audience change (e.g. paid -> free).

        Uses POST /drafts/{id}/scheduled_release.
        """
        response = self._session.post(
            f"{self.publication_url}/drafts/{draft_id}/scheduled_release",
            json={
                "trigger_at": trigger_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "post_audience": post_audience,
                "email_audience": email_audience,
            },
        )
        # Substack returns empty response on success
        if not (200 <= response.status_code < 300):
            raise SubstackAPIException(response.status_code, response.text)

    def get_post_metadata(self, draft_id: int) -> PostMetadata:
        """Get full post metadata as a dataclass."""
        data = self.get_draft(draft_id)
        return PostMetadata.from_api(data)

    def make_post_free(self, post_id: int) -> PostMetadata:
        """Set a post's audience and comments to everyone."""
        data = self.put_draft(
            post_id,
            audience="everyone",
            write_comment_permissions="everyone",
        )
        return PostMetadata.from_api(data)

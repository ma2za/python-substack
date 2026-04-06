"""API Wrapper."""

from __future__ import annotations

import base64
import json
import logging
import re
from pathlib import Path
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

    _PRODUCTION_SUBDOMAINS: frozenset[str] = frozenset()

    def __init__(
        self,
        email: str | None = None,
        password: str | None = None,
        cookies_path: str | None = None,
        base_url: str | None = None,
        publication_url: str | None = None,
        debug: bool = False,
        cookies_string: str | None = None,
    ) -> None:
        self.base_url = base_url or "https://substack.com/api/v1"
        if debug:
            logging.basicConfig()
            logging.getLogger().setLevel(logging.DEBUG)
        self._session = requests.Session()
        self._authenticate(email, password, cookies_path, cookies_string)
        self._resolve_publication(publication_url)

    def _authenticate(
        self,
        email: str | None,
        password: str | None,
        cookies_path: str | None,
        cookies_string: str | None,
    ) -> None:
        """Set up session credentials from one of the supported auth methods."""
        if cookies_path is not None:
            cookies = json.loads(Path(cookies_path).read_text(encoding="utf-8"))
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

    def _resolve_publication(self, publication_url: str | None) -> None:
        """Resolve and set the active publication."""
        if not publication_url:
            self.change_publication(self.get_user_primary_publication())
            return

        match = re.search(r"https://(.*).substack.com", publication_url.lower())
        subdomain = match.group(1) if match else None

        if subdomain in self._PRODUCTION_SUBDOMAINS:
            raise ValueError(
                f"Subdomain '{subdomain}' is a PRODUCTION publication and is blocked."
            )

        # Try to find in user's publications
        if pub := next(
            (p for p in self.get_user_publications() if p["subdomain"] == subdomain),
            None,
        ):
            self.change_publication(pub)
        elif subdomain:
            # Fallback: construct publication dict from URL
            self.change_publication(
                {
                    "subdomain": subdomain,
                    "publication_url": f"https://{subdomain}.substack.com",
                }
            )
        else:
            self.change_publication(self.get_user_primary_publication())

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

    def login(self, email: str, password: str) -> dict:
        return self._post(
            f"{self.base_url}/login",
            captcha_response=None,
            email=email,
            for_pub="",
            password=password,
            redirect="/",
        )

    def signin_for_pub(self, publication: dict) -> dict:
        response = self._session.get(
            f"https://substack.com/sign-in?redirect=%2F&for_pub={publication['subdomain']}",
        )
        return self._handle_response(response, allow_empty=True) or {}

    def change_publication(self, publication: dict) -> None:
        self.publication = publication
        self.publication_url = urljoin(publication["publication_url"], "api/v1")
        self.signin_for_pub(publication)

    def export_cookies(self, path: str = "cookies.json") -> None:
        cookies = self._session.cookies.get_dict()
        Path(path).write_text(json.dumps(cookies), encoding="utf-8")

    @staticmethod
    def _handle_response(
        response: requests.Response, *, allow_empty: bool = False
    ) -> dict | list | None:
        if not (200 <= response.status_code < 300):
            raise SubstackAPIException(response.status_code, response.text)
        if allow_empty:
            try:
                return response.json()
            except ValueError:
                return None
        try:
            return response.json()
        except ValueError as err:
            raise SubstackRequestException(
                f"Invalid Response: {response.text}"
            ) from err

    # ---- HTTP helper methods ----

    def _get(self, url: str, **params: str | int | None) -> dict | list | None:
        response = self._session.get(url, params=params or None)
        return Api._handle_response(response)

    def _post(
        self, url: str, **json_data: str | int | bool | None
    ) -> dict | list | None:
        response = self._session.post(url, json=json_data)
        return Api._handle_response(response)

    def _put(
        self, url: str, **json_data: str | int | bool | None
    ) -> dict | list | None:
        response = self._session.put(url, json=json_data)
        return Api._handle_response(response)

    def _delete(self, url: str) -> dict | list | None:
        response = self._session.delete(url)
        return Api._handle_response(response)

    def get_user_id(self) -> int:
        profile = self.get_user_profile()
        return profile["id"]

    @staticmethod
    def get_publication_url(publication: dict) -> str:
        if domain := (
            publication.get("custom_domain")
            or publication.get("custom_domain_optional")
        ):
            return f"https://{domain}"
        return f"https://{publication['subdomain']}.substack.com"

    def get_user_primary_publication(self) -> dict:
        profile = self.get_user_profile()

        if pp := profile.get("primaryPublication"):
            pp["publication_url"] = self.get_publication_url(pp)
            return pp

        pub_users = profile.get("publicationUsers") or []

        # Find the one marked as primary
        for pu in pub_users:
            if pu.get("is_primary", False) and (pub := pu.get("publication")):
                pub["publication_url"] = self.get_publication_url(pub)
                return pub

        # Last resort: first publication in the list
        if pub_users and (pub := pub_users[0].get("publication")):
            pub["publication_url"] = self.get_publication_url(pub)
            return pub

        raise SubstackRequestException("Could not find primary publication in profile")

    def get_user_publications(self) -> list[dict]:
        profile = self.get_user_profile()
        user_publications: list[dict] = []
        publication_users = profile.get("publicationUsers")

        if publication_users is None:
            return user_publications

        for publication in publication_users:
            pub = publication.get("publication")
            if pub is not None:
                pub["publication_url"] = self.get_publication_url(pub)
                user_publications.append(pub)

        return user_publications

    def get_user_profile(self) -> dict:
        return self._get(f"{self.base_url}/user/profile/self")

    def get_user_settings(self) -> dict:
        return self._get(f"{self.base_url}/settings")

    def get_publication_users(self) -> list[dict]:
        return self._get(f"{self.publication_url}/publication/users")

    def get_publication_subscriber_count(self) -> int:
        return self._get(f"{self.publication_url}/publication_launch_checklist")[
            "subscriberCount"
        ]

    def get_published_posts(
        self,
        offset: int = 0,
        limit: int = 25,
        order_by: str = "post_date",
        order_direction: str = "desc",
    ) -> dict:
        return self._get(
            f"{self.publication_url}/post_management/published",
            offset=offset,
            limit=limit,
            order_by=order_by,
            order_direction=order_direction,
        )

    def get_posts(self) -> dict:
        return self._get(f"{self.base_url}/reader/posts")

    def get_drafts(
        self,
        filter: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        return self._get(
            f"{self.publication_url}/drafts",
            filter=filter,
            offset=offset,
            limit=limit,
        )

    def get_draft(self, draft_id: int) -> dict:
        return self._get(f"{self.publication_url}/drafts/{draft_id}")

    def delete_draft(self, draft_id: int) -> dict:
        return self._delete(f"{self.publication_url}/drafts/{draft_id}")

    def post_draft(self, body: dict) -> dict:
        response = self._session.post(f"{self.publication_url}/drafts", json=body)
        return Api._handle_response(response)

    def put_draft(self, draft: int, **kwargs: str | int | bool | None) -> dict:
        response = self._session.put(
            f"{self.publication_url}/drafts/{draft}",
            json=kwargs,
        )
        return Api._handle_response(response)

    def publish_draft(
        self, draft: int, send: bool = True, share_automatically: bool = False
    ) -> dict:
        # Run prepublish validation (matches browser flow)
        pre = self._get(f"{self.publication_url}/drafts/{draft}/prepublish")
        if pre.get("errors"):
            logger.warning(f"Prepublish warnings for draft {draft}: {pre['errors']}")

        return self._post(
            f"{self.publication_url}/drafts/{draft}/publish",
            send=send,
            share_automatically=share_automatically,
        )

    def schedule_draft(self, draft: int, draft_datetime: datetime) -> dict:
        return self._post(
            f"{self.publication_url}/drafts/{draft}/schedule",
            post_date=draft_datetime.isoformat(),
        )

    def unschedule_draft(self, draft: int) -> dict:
        return self._post(
            f"{self.publication_url}/drafts/{draft}/schedule",
            post_date=None,
        )

    def get_image(self, image: str) -> dict:
        image_path = Path(image)
        if image_path.exists():
            image = b"data:image/jpeg;base64," + base64.b64encode(
                image_path.read_bytes()
            )

        response = self._session.post(
            f"{self.publication_url}/image",
            data={"image": image},
        )
        return Api._handle_response(response=response)

    def add_tags_to_post(self, post_id: int, tag_names: list[str]) -> dict:
        results = []
        for tag_name in tag_names:
            result = self.add_tag_to_post(post_id, tag_name)
            results.append(result)
        return {"tags_added": results}

    def get_publication_post_tags(self) -> list[dict]:
        return self._get(f"{self.publication_url}/publication/post-tag")

    def add_tag_to_post(self, post_id: int, tag_name: str) -> dict:
        existing_tags = self.get_publication_post_tags() or []
        if existing := next(
            (t for t in existing_tags if t.get("name") == tag_name), None
        ):
            tag_id = existing["id"]
        else:
            tag_data = self._post(
                f"{self.publication_url}/publication/post-tag", name=tag_name
            )
            tag_id = tag_data["id"]

        response = self._session.post(
            f"{self.publication_url}/post/{post_id}/tag/{tag_id}"
        )
        return Api._handle_response(response)

    def get_categories(self) -> list[dict]:
        return self._get(f"{self.base_url}/categories")

    def get_category(self, category_id: int, category_type: str, page: int) -> dict:
        return self._get(
            f"{self.base_url}/category/public/{category_id}/{category_type}",
            page=page,
        )

    def get_single_category(
        self,
        category_id: int,
        category_type: str,
        page: int | None = None,
        limit: int | None = None,
    ) -> dict:
        if page is not None:
            output = self.get_category(category_id, category_type, page)
        else:
            publications: list[dict] = []
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

    def delete_all_drafts(self) -> dict | None:
        response = None
        while True:
            drafts = self.get_drafts(filter="draft", limit=10, offset=0)
            if len(drafts) == 0:
                break
            for draft in drafts:
                response = self.delete_draft(draft.get("id"))
        return response

    def get_sections(self) -> list[dict]:
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

    def publication_embed(self, url: str) -> dict:
        return self.call("/publication/embed", "GET", url=url)

    def call(
        self, endpoint: str, method: str, **params: str | int | None
    ) -> dict | list | None:
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
        self._handle_response(response, allow_empty=True)

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

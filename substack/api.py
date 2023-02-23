import logging
from datetime import datetime

import requests

from substack.exceptions import SubstackAPIException, SubstackRequestException

logger = logging.getLogger(__name__)


class Api:
	"""

	A python interface into the Substack API

	"""

	def __init__(
			self,
			email = None,
			password = None,
			base_url = None,
			publication_url = None,
			debug = False,
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
		self.publication_url = f"{publication_url}/api/v1"

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

	def get_drafts(self, filter = None, offset = None, limit = None):
		response = self._session.get(
			f"{self.publication_url}/drafts",
			params={"filter": filter, "offset": offset, "limit": limit},
		)
		return Api._handle_response(response=response)

	def delete_draft(self, draft_id):
		response = self._session.delete(
			f"{self.publication_url}/drafts/{draft_id}"
		)
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
			title = None,
			subtitle = None,
			body = None,
			cover_image = None,
	) -> dict:
		"""

		Args:
			draft: draft id
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
			json={"post_date": draft_datetime.isoformat()}
		)
		return Api._handle_response(response=response)

	def unschedule_draft(self, draft) -> dict:
		"""

		Args:
			draft: draft id

		Returns:

		"""
		response = self._session.post(
			f"{self.publication_url}/drafts/{draft}/schedule",
			json={"post_date": None}
		)
		return Api._handle_response(response=response)

	def get_image(self, image):
		response = self._session.post(
			f"{self.publication_url}/image",
			json={
				"image": image
			},
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
		response = self._session.get(f"{self.base_url}/category/public/{category_id}/{category_type}",
		                             params={"page": page})
		return Api._handle_response(response=response)

	def get_single_category(self, category_id, category_type, page = None,
	                        limit = None):
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
				if (limit is not None and limit <= len(publications)) or not page_output.get("more", False):
					publications = publications[:limit]
					break
				page += 1
			output = {
				"publications": publications,
				"more": page_output.get("more", False)
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

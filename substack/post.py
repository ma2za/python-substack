import json


class Post:

	def __init__(self, title, subtitle, user_id):
		self.draft_title = title
		self.draft_subtitle = subtitle
		self.draft_body = {"type": "doc", "content": []}
		self.draft_bylines = [{"id": int(user_id), "is_guest": False}]

	def add(self, item):
		self.draft_body["content"] = self.draft_body.get("content", []) + [{"type": item.get("type")}]
		content = item.get("content")
		if item.get("type") == "captionedImage":
			self.captioned_image(item)
		elif item.get("type") == "youtube2":
			self.youtube(item.get("src"))
		else:
			if content is not None:
				self.add_complex_text(content)

		if item.get("type") == "heading":
			self.attrs(item.get("level", 1))

		marks = item.get("marks")
		if marks is not None:
			self.marks(marks)

		return self

	def paragraph(self, content=None):
		item = {"type": "paragraph"}
		if content is not None:
			item["content"] = content
		return self.add(item)

	def heading(self, content=None, level=1):
		item = {"type": "heading"}
		if content is not None:
			item["content"] = content
		item["level"] = level
		return self.add(item)

	def horizontal_rule(self):
		return self.add({"type": "horizontal_rule"})

	def attrs(self, level):
		content_attrs = self.draft_body["content"][-1].get("attrs", {})
		content_attrs.update({"level": level})
		self.draft_body["content"][-1]["attrs"] = content_attrs
		return self

	def captioned_image(self, value):
		content = self.draft_body["content"][-1].get("content", [])
		content += [{"type": "image2", "attrs": {
			"src": value.get("src"),
			"fullscreen": False,
			"imageSize": value.get("size", "normal"),
			"height": 819,
			"width": 1456,
			"resizeWidth": 728,

			"bytes": None, "alt": None, "title": None, "type": None, "href": None, "belowTheFold": False,
			"internalRedirect": None

		}}]
		self.draft_body["content"][-1]["content"] = content

	def text(self, value):
		"""

		Add text to the last paragraph.

		Args:
			value: Text to add to paragraph.

		Returns:

		"""
		content = self.draft_body["content"][-1].get("content", [])
		content += [{"type": "text", "text": value}]
		self.draft_body["content"][-1]["content"] = content
		return self

	def add_complex_text(self, text):
		if isinstance(text, str):
			self.text(text)
		else:
			for chunk in text:
				if chunk:
					self.text(chunk.get("content")).marks(chunk.get("marks"))

	def marks(self, marks):
		content = self.draft_body["content"][-1].get("content", [])[-1]
		content_marks = content.get("marks", [])
		for mark in marks:
			new_mark = {"type": mark.get("type")}
			if mark.get("type") == "link":
				href = mark.get("href")
				new_mark.update({"attrs": {
					"href": href
				}})
			content_marks.append(new_mark)
		content["marks"] = content_marks
		return self

	def remove_last_paragraph(self):
		del self.draft_body.get("content")[-1]

	def get_draft(self):
		out = vars(self)
		out["draft_body"] = json.dumps(out["draft_body"])
		return out

	def subscribe_with_caption(self, value):
		content = self.draft_body["content"][-1].get("content", [])
		content += [{"type": "subscribeWidget",
		             "attrs": {"url": "%%checkout_url%%", "text": "Subscribe"},
		             "content": [
			             {
				             "type": "ctaCaption",
				             "content": [{"type": "text",
				                          "text": f"Thanks for reading {value}! Subscribe for free to receive new posts and support my work."}]
			             }
		             ]}]
		self.draft_body["content"][-1]["content"] = content
		return self

	def youtube(self, value):
		content_attrs = self.draft_body["content"][-1].get("attrs", {})
		content_attrs.update({"videoId": value})
		self.draft_body["content"][-1]["attrs"] = content_attrs
		return self

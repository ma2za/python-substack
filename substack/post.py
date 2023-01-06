import json


class Post:

	def __init__(self, title: str, subtitle: str, user_id: str):
		self.draft_title = title
		self.draft_subtitle = subtitle
		self.draft_body = {"type": "doc", "content": []}
		self.draft_bylines = [{"id": int(user_id), "is_guest": False}]

	def add(self, item):
		self.draft_body["content"] = self.draft_body.get("content", []) + [{"type": item.get("type")}]
		content = item.get("content")
		if content is not None:
			self.text(content)

		if item.get("type") == "heading":
			self.attrs(item.get("level", 1))
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

	def text(self, value: str):
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

	def marks(self, marks):
		content = self.draft_body["content"][-1].get("content", [])[-1]
		content_marks = content.get("marks", [])
		for mark in marks:
			content_marks.append({"type": mark})
		content["marks"] = content_marks
		return self

	def remove_last_paragraph(self):
		del self.draft_body.get("content")[-1]

	def get_draft(self):
		out = vars(self)
		out["draft_body"] = json.dumps(out["draft_body"])
		return out

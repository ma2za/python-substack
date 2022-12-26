class Post:

	def __init__(self, title: str, subtitle: str, user_id: str):
		self.draft_title = title
		self.draft_subtitle = subtitle
		self.draft_body = {"type": "doc", "content": []}
		self.draft_bylines = [{"id": int(user_id), "is_guest": False}]

	def paragraph(self):
		self.draft_body["content"] = self.draft_body.get("content", []) + [{"type": "paragraph"}]
		return self

	def text(self, value):
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

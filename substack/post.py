import json
from typing import Dict


class Post:

    def __init__(self, title: str, subtitle: str, user_id,
                 audience: str = None,
                 write_comment_permissions: str = None):
        """

        Args:
            title:
            subtitle:
            user_id:
            audience: possible values: everyone, only_paid, founding, only_free
            write_comment_permissions: none, only_paid, everyone (this field is a mess)
        """
        self.draft_title = title
        self.draft_subtitle = subtitle
        self.draft_body = {"type": "doc", "content": []}
        self.draft_bylines = [{"id": int(user_id), "is_guest": False}]
        self.audience = audience if audience is not None else "everyone"

        # TODO better understand the possible values and combinations with audience
        if write_comment_permissions is not None:
            self.write_comment_permissions = write_comment_permissions
        else:
            self.write_comment_permissions = self.audience

    def add(self, item: Dict):
        """

        Add item to draft body.

        Args:
            item:

        Returns:

        """

        self.draft_body["content"] = self.draft_body.get("content", []) + [{"type": item.get("type")}]
        content = item.get("content")
        if item.get("type") == "captionedImage":
            self.captioned_image(**item)
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
        """

        Args:
            content:

        Returns:

        """
        item = {"type": "paragraph"}
        if content is not None:
            item["content"] = content
        return self.add(item)

    def heading(self, content=None, level: int = 1):
        """

        Args:
            content:
            level:

        Returns:

        """

        item = {"type": "heading"}
        if content is not None:
            item["content"] = content
        item["level"] = level
        return self.add(item)

    def horizontal_rule(self):
        """

        Returns:

        """
        return self.add({"type": "horizontal_rule"})

    def attrs(self, level):
        """

        Args:
            level:

        Returns:

        """
        content_attrs = self.draft_body["content"][-1].get("attrs", {})
        content_attrs.update({"level": level})
        self.draft_body["content"][-1]["attrs"] = content_attrs
        return self

    def captioned_image(self,
                        src: str,
                        fullscreen: bool = False,
                        imageSize: str = "normal",
                        height: int = 819,
                        width: int = 1456,
                        resizeWidth: int = 728,
                        bytes: str = None,
                        alt: str = None,
                        title: str = None,
                        type: str = None,
                        href: str = None,
                        belowTheFold: bool = False,
                        internalRedirect: str = None
                        ):
        """

        Add image to body.

        Args:
            bytes:
            alt:
            title:
            type:
            href:
            belowTheFold:
            internalRedirect:
            src:
            fullscreen:
            imageSize:
            height:
            width:
            resizeWidth:
        """

        content = self.draft_body["content"][-1].get("content", [])
        content += [{"type": "image2", "attrs": {
            "src": src,
            "fullscreen": fullscreen,
            "imageSize": imageSize,
            "height": height,
            "width": width,
            "resizeWidth": resizeWidth,
            "bytes": bytes,
            "alt": alt,
            "title": title,
            "type": type,
            "href": href,
            "belowTheFold": belowTheFold,
            "internalRedirect": internalRedirect

        }}]
        self.draft_body["content"][-1]["content"] = content
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

    def add_complex_text(self, text):
        """

        Args:
            text:
        """
        if isinstance(text, str):
            self.text(text)
        else:
            for chunk in text:
                if chunk:
                    self.text(chunk.get("content")).marks(chunk.get("marks"))

    def marks(self, marks):
        """

        Args:
            marks:

        Returns:

        """
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
        """

        """
        del self.draft_body.get("content")[-1]

    def get_draft(self):
        """

        Returns:

        """
        out = vars(self)
        out["draft_body"] = json.dumps(out["draft_body"])
        return out

    def subscribe_with_caption(self, value: str):
        """

        Args:
            value:

        Returns:

        """
        content = self.draft_body["content"][-1].get("content", [])
        content += [{"type": "subscribeWidget",
                     "attrs": {"url": "%%checkout_url%%", "text": "Subscribe"},
                     "content": [
                         {
                             "type": "ctaCaption",
                             "content": [{"type": "text",
                                          "text": f"""Thanks for reading {value}! 
                                          Subscribe for free to receive new posts and support my work."""}]
                         }
                     ]}]
        self.draft_body["content"][-1]["content"] = content
        return self

    def youtube(self, value: str):
        """

        Args:
            value:

        Returns:

        """
        content_attrs = self.draft_body["content"][-1].get("attrs", {})
        content_attrs.update({"videoId": value})
        self.draft_body["content"][-1]["attrs"] = content_attrs
        return self

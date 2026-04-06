"""Post Utilities."""

from __future__ import annotations

import json
import re

from substack.exceptions import SectionNotExistsException

__all__ = ["Post", "parse_inline"]


def parse_inline(text: str) -> list[dict]:
    """Convert inline Markdown in a text string into a list of tokens."""
    if not text:
        return []

    tokens = []
    link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    bold_pattern = r"\*\*([^*]+)\*\*"
    italic_pattern = r"(?<!\*)\*([^*]+)\*(?!\*)"

    matches = []
    for match in re.finditer(link_pattern, text):
        if match.start() == 0 or text[match.start() - 1 : match.start() + 1] != "![":
            matches.append(
                (match.start(), match.end(), "link", match.group(1), match.group(2))
            )

    for match in re.finditer(bold_pattern, text):
        if not any(start <= match.start() < end for start, end, _, _, _ in matches):
            matches.append((match.start(), match.end(), "bold", match.group(1), None))

    for match in re.finditer(italic_pattern, text):
        if not any(start <= match.start() < end for start, end, _, _, _ in matches):
            matches.append((match.start(), match.end(), "italic", match.group(1), None))

    matches.sort(key=lambda x: x[0])

    last_pos = 0
    for start, end, match_type, content, url in matches:
        if start > last_pos:
            tokens.append({"content": text[last_pos:start]})

        if match_type == "link":
            tokens.append(
                {
                    "content": content,
                    "marks": [{"type": "link", "attrs": {"href": url}}],
                }
            )
        elif match_type == "bold":
            tokens.append({"content": content, "marks": [{"type": "strong"}]})
        elif match_type == "italic":
            tokens.append({"content": content, "marks": [{"type": "em"}]})

        last_pos = end

    if last_pos < len(text):
        tokens.append({"content": text[last_pos:]})

    return [t for t in tokens if t.get("content")]


def _tokens_to_text_nodes(tokens: list[dict]) -> list[dict]:
    """Convert parse_inline tokens to ProseMirror text nodes."""
    nodes = []
    for t in tokens:
        if not t:
            continue
        node = {"type": "text", "text": t["content"]}
        marks = t.get("marks")
        if marks:
            pm_marks = []
            for m in marks:
                pm = {"type": m["type"]}
                if m["type"] == "link":
                    pm["attrs"] = {"href": m.get("attrs", {}).get("href", "")}
                pm_marks.append(pm)
            node["marks"] = pm_marks
        nodes.append(node)
    return nodes


class Post:
    """Post utility class."""

    def __init__(
        self,
        title: str,
        subtitle: str,
        user_id,
        audience: str | None = None,
        write_comment_permissions: str | None = None,
    ) -> None:
        self.draft_title = title
        self.draft_subtitle = subtitle
        self.draft_body = {"type": "doc", "content": []}
        self.draft_bylines = [{"id": int(user_id), "is_guest": False}]
        self.audience = audience if audience is not None else "everyone"
        self.draft_section_id = None
        self.section_chosen = True

        if write_comment_permissions is not None:
            self.write_comment_permissions = write_comment_permissions
        else:
            self.write_comment_permissions = self.audience

    def set_section(self, name: str, sections: list) -> None:
        section = [s for s in sections if s.get("name") == name]
        if len(section) != 1:
            raise SectionNotExistsException(name)
        section = section[0]
        self.draft_section_id = section.get("id")

    def add(self, item: dict):
        self.draft_body["content"] = self.draft_body.get("content", []) + [
            {"type": item.get("type")}
        ]
        content = item.get("content")
        if item.get("type") == "captionedImage":
            self.captioned_image(**item)
        elif item.get("type") == "embeddedPublication":
            self.draft_body["content"][-1]["attrs"] = item.get("url")
        elif item.get("type") == "youtube2":
            self.youtube(item.get("src"))
        elif item.get("type") == "subscribeWidget":
            self.subscribe_with_caption(item.get("message"))
        elif item.get("type") == "codeBlock":
            self.code_block(item.get("content"), item.get("attrs", {}))
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

    def heading(self, content=None, level: int = 1):
        item = {"type": "heading"}
        if content is not None:
            item["content"] = content
        item["level"] = level
        return self.add(item)

    def blockquote(self, content=None):
        paragraphs: list[dict] = []
        if content is not None:
            if isinstance(content, str):
                tokens = parse_inline(content)
                text_nodes = [
                    {"type": "text", "text": t["content"]} for t in tokens if t
                ]
                if text_nodes:
                    paragraphs.append({"type": "paragraph", "content": text_nodes})
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "paragraph":
                        paragraphs.append(item)
                    elif isinstance(item, dict):
                        text_nodes = [{"type": "text", "text": item.get("content", "")}]
                        paragraphs.append({"type": "paragraph", "content": text_nodes})

        node: dict = {"type": "blockquote"}
        if paragraphs:
            node["content"] = paragraphs
        self.draft_body["content"] = self.draft_body.get("content", []) + [node]
        return self

    def paywall(self):
        """Insert a paywall boundary. Content above is the free preview, below is paid-only."""
        return self.add({"type": "paywall"})

    def horizontal_rule(self):
        return self.add({"type": "horizontal_rule"})

    def attrs(self, level):
        content_attrs = self.draft_body["content"][-1].get("attrs", {})
        content_attrs.update({"level": level})
        self.draft_body["content"][-1]["attrs"] = content_attrs
        return self

    def captioned_image(
        self,
        src: str,
        fullscreen: bool = False,
        imageSize: str = "normal",
        height: int = 819,
        width: int = 1456,
        resizeWidth: int = 728,
        bytes: str | None = None,
        alt: str | None = None,
        title: str | None = None,
        type: str | None = None,
        href: str | None = None,
        belowTheFold: bool = False,
        internalRedirect: str | None = None,
    ):
        content = self.draft_body["content"][-1].get("content", [])
        content += [
            {
                "type": "image2",
                "attrs": {
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
                    "internalRedirect": internalRedirect,
                },
            }
        ]
        self.draft_body["content"][-1]["content"] = content
        return self

    def text(self, value: str):
        content = self.draft_body["content"][-1].get("content", [])
        content += [{"type": "text", "text": value}]
        self.draft_body["content"][-1]["content"] = content
        return self

    def add_complex_text(self, text) -> None:
        if isinstance(text, str):
            self.text(text)
        else:
            for chunk in text:
                if chunk:
                    self.text(chunk.get("content")).marks(chunk.get("marks", []))

    def marks(self, marks):
        if not marks:
            return self
        content = self.draft_body["content"][-1].get("content", [])[-1]
        content_marks = content.get("marks", [])
        for mark in marks:
            new_mark = {"type": mark.get("type")}
            if mark.get("type") == "link":
                href = mark.get("href") or mark.get("attrs", {}).get("href")
                new_mark.update({"attrs": {"href": href}})
            content_marks.append(new_mark)
        content["marks"] = content_marks
        return self

    def remove_last_paragraph(self) -> None:
        del self.draft_body.get("content")[-1]

    def get_draft(self):
        out = vars(self)
        out["draft_body"] = json.dumps(out["draft_body"])
        return out

    def subscribe_with_caption(self, message: str | None = None):
        if message is None:
            message = "Thanks for reading this newsletter! Subscribe for free to receive new posts and support my work."

        subscribe = self.draft_body["content"][-1]
        subscribe["attrs"] = {
            "url": "%%checkout_url%%",
            "text": "Subscribe",
            "language": "en",
        }
        subscribe["content"] = [
            {
                "type": "ctaCaption",
                "content": [{"type": "text", "text": message}],
            }
        ]
        return self

    def youtube(self, value: str):
        content_attrs = self.draft_body["content"][-1].get("attrs", {})
        content_attrs.update({"videoId": value})
        self.draft_body["content"][-1]["attrs"] = content_attrs
        return self

    def code_block(self, content, attrs=None):
        if attrs is None:
            attrs = {}

        if isinstance(content, str):
            code_content = [{"type": "text", "text": content}]
        elif isinstance(content, list):
            code_content = content
        else:
            code_content = []

        code_block = self.draft_body["content"][-1]
        code_block["content"] = code_content
        if attrs:
            code_block["attrs"] = attrs

        return self

    def from_markdown(self, markdown_content: str, api=None):
        """Parse Markdown content and add it to the post."""
        lines = markdown_content.split("\n")
        blocks = []
        current_block: list[str] = []
        in_code_block = False
        code_block_language = None

        for line in lines:
            if line.strip().startswith("```"):
                if in_code_block:
                    if current_block:
                        blocks.append(
                            {
                                "type": "code",
                                "language": code_block_language,
                                "content": "\n".join(current_block),
                            }
                        )
                    current_block = []
                    in_code_block = False
                    code_block_language = None
                else:
                    if current_block:
                        blocks.append(
                            {"type": "text", "content": "\n".join(current_block)}
                        )
                        current_block = []
                    language = line.strip()[3:].strip()
                    code_block_language = language if language else None
                    in_code_block = True
                continue

            if in_code_block:
                current_block.append(line)
            else:
                if line.strip() == "":
                    if current_block:
                        blocks.append(
                            {"type": "text", "content": "\n".join(current_block)}
                        )
                        current_block = []
                else:
                    current_block.append(line)

        if current_block:
            if in_code_block:
                blocks.append(
                    {
                        "type": "code",
                        "language": code_block_language,
                        "content": "\n".join(current_block),
                    }
                )
            else:
                blocks.append({"type": "text", "content": "\n".join(current_block)})

        # -- Render blocks into ProseMirror nodes --
        # Track pending bullet items across blocks so consecutive bullet
        # blocks (even separated by blank lines) merge into one bullet_list.
        pending_bullets: list[list[dict]] = []

        def flush_bullets() -> None:
            if not pending_bullets:
                return
            list_items = []
            for bullet_tokens in pending_bullets:
                list_items.append(
                    {
                        "type": "list_item",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": _tokens_to_text_nodes(bullet_tokens),
                            }
                        ],
                    }
                )
            self.draft_body["content"].append(
                {"type": "bullet_list", "content": list_items}
            )
            pending_bullets.clear()

        def _is_hr(text: str) -> bool:
            stripped = text.strip()
            return stripped in ("---", "***", "___") or (
                len(stripped) >= 3
                and set(stripped) <= {"-", "*", "_", " "}
                and any(c * 3 in stripped for c in "-*_")
            )

        def _extract_bullet(line: str) -> str | None:
            """Return bullet text if line is a bullet, else None."""
            if line.startswith("- "):
                return line[2:].strip()
            if line.startswith("* "):
                return line[2:].strip()
            if line.startswith("*") and not line.startswith("**"):
                return line[1:].strip()
            return None

        pending_para_lines: list[str] = []
        pending_quote_paras: list[dict] = []

        def flush_para() -> None:
            """Merge accumulated plain-text lines into one paragraph."""
            if not pending_para_lines:
                return
            merged = " ".join(pending_para_lines)
            tokens = parse_inline(merged)
            self.add({"type": "paragraph", "content": tokens})
            pending_para_lines.clear()

        def flush_quotes() -> None:
            """Emit accumulated blockquote paragraphs as one blockquote node."""
            if not pending_quote_paras:
                return
            node: dict = {"type": "blockquote", "content": list(pending_quote_paras)}
            self.draft_body["content"].append(node)
            pending_quote_paras.clear()

        def _process_line(line: str) -> None:
            """Process a single line of text content."""
            bullet_text = _extract_bullet(line)
            if bullet_text is not None:
                flush_para()
                flush_quotes()
                tokens = parse_inline(bullet_text)
                if tokens:
                    pending_bullets.append(tokens)
                return

            # Not a bullet — flush any pending bullets first
            flush_bullets()

            if line.startswith("> ") or line == ">":
                flush_para()
                quote_text = line[2:] if line.startswith("> ") else ""
                tokens = parse_inline(quote_text)
                text_nodes = _tokens_to_text_nodes(tokens)
                para = (
                    {"type": "paragraph", "content": text_nodes}
                    if text_nodes
                    else {"type": "paragraph"}
                )
                pending_quote_paras.append(para)
            else:
                flush_quotes()
                # Accumulate consecutive plain lines into one paragraph
                pending_para_lines.append(line)

        for block in blocks:
            if block["type"] == "code":
                flush_para()
                flush_quotes()
                flush_bullets()
                code_content = block.get("content", "").strip()
                if code_content:
                    code_attrs = {}
                    if block.get("language"):
                        code_attrs["language"] = block["language"]
                    self.add(
                        {
                            "type": "codeBlock",
                            "content": code_content,
                            "attrs": code_attrs,
                        }
                    )
                continue

            text_content = block.get("content", "").strip()
            if not text_content:
                continue

            # Horizontal rule
            if _is_hr(text_content):
                flush_para()
                flush_quotes()
                flush_bullets()
                self.draft_body["content"].append({"type": "horizontal_rule"})
                continue

            # Heading
            if text_content.startswith("#"):
                flush_para()
                flush_quotes()
                flush_bullets()
                level = len(text_content) - len(text_content.lstrip("#"))
                heading_text = text_content.lstrip("#").strip()
                if heading_text:
                    self.heading(content=heading_text, level=min(level, 6))
                continue

            # Image
            if text_content.startswith("!") or (
                text_content.startswith("[") and "![" in text_content
            ):
                flush_para()
                flush_quotes()
                flush_bullets()
                linked_image_match = re.match(
                    r"\[!\[([^\]]*)\]\(([^)]+)\)\]\(([^)]+)\)", text_content
                )
                if linked_image_match:
                    alt_text = linked_image_match.group(1)
                    image_url = linked_image_match.group(2)
                    link_url = linked_image_match.group(3)
                    image_url = (
                        image_url[1:] if image_url.startswith("/") else image_url
                    )
                    if api is not None:
                        try:
                            image = api.get_image(image_url)
                            image_url = image.get("url")
                        except Exception:
                            pass
                    self.add(
                        {
                            "type": "captionedImage",
                            "src": image_url,
                            "alt": alt_text,
                            "href": link_url,
                        }
                    )
                else:
                    match = re.match(r"!\[.*?\]\((.*?)\)", text_content)
                    if match:
                        image_url = match.group(1)
                        image_url = (
                            image_url[1:] if image_url.startswith("/") else image_url
                        )
                        if api is not None:
                            try:
                                image = api.get_image(image_url)
                                image_url = image.get("url")
                            except Exception:
                                pass
                        self.add({"type": "captionedImage", "src": image_url})
                continue

            # Text content — may contain bullets, blockquotes, paragraphs
            # Each block is separated by blank lines in the source,
            # so flush any pending content from the previous block.
            flush_para()
            flush_quotes()
            for line in text_content.split("\n"):
                line = line.strip()
                if line:
                    _process_line(line)

        flush_para()
        flush_quotes()
        flush_bullets()
        return self

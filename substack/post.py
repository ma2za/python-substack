"""

Post Utilities

"""

import json
import re
from typing import Dict, List

__all__ = ["Post", "parse_inline", "tokens_to_text_nodes"]

from substack.exceptions import SectionNotExistsException

# Markdown footnotes: ``text.[^label]`` references and ``[^label]: definition`` lines.
FOOTNOTE_REFERENCE_PATTERN = re.compile(r"\[\^([^\]]+)\]")
FOOTNOTE_DEFINITION_PATTERN = re.compile(r"^\[\^([^\]]+)\]:\s?(.*)$")


def tokens_to_text_nodes(tokens: List[Dict]) -> List[Dict]:
    """Convert parse_inline() tokens to ProseMirror text nodes.

    parse_inline() returns {"content": "text", "marks": [...]}.
    ProseMirror expects {"type": "text", "text": "text", "marks": [...]}.
    """
    nodes = []
    for token in tokens:
        if not token or not token.get("content"):
            continue
        node = {"type": "text", "text": token["content"]}
        marks = token.get("marks")
        if marks:
            node["marks"] = marks
        nodes.append(node)
    return nodes


def parse_inline(text: str) -> List[Dict]:
    """
    Convert inline Markdown in a text string into a list of tokens
    for use in the post content.

    Supported formatting:
      - `code`: Text wrapped in backticks.
      - **Bold**: Text wrapped in double asterisks.
      - *Italic*: Text wrapped in single asterisks.
      - ***Bold+Italic***: Text wrapped in triple asterisks.
      - ~~Strikethrough~~: Text wrapped in double tildes.
      - [Links]: Text wrapped in square brackets followed by URL in parentheses.

    Args:
        text: Text string containing inline Markdown formatting.

    Returns:
        List of token dictionaries with content and marks.

    Example:
        >>> parse_inline("This is **bold** and this is [a link](https://example.com)")
        [{'content': 'This is '}, {'content': 'bold', 'marks': [{'type': 'strong'}]}, {'content': ' and this is '}, {'content': 'a link', 'marks': [{'type': 'link', 'attrs': {'href': 'https://example.com'}}]}]
    """
    if not text:
        return []

    tokens = []

    # Pattern order matters: code > links > bold+italic > bold > italic > strikethrough
    code_pattern = r'`([^`]+)`'
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    bold_italic_pattern = r'\*\*\*([^*]+)\*\*\*'
    bold_pattern = r'\*\*([^*]+)\*\*'
    italic_pattern = r'(?<!\*)\*([^*]+)\*(?!\*)'  # Not preceded or followed by *
    strikethrough_pattern = r'~~([^~]+)~~'

    # Find all matches with their positions
    matches = []

    # Inline code FIRST -- content inside backticks must not be parsed for other formatting
    for match in re.finditer(code_pattern, text):
        matches.append((match.start(), match.end(), "code", match.group(1), None))

    # Links
    for match in re.finditer(link_pattern, text):
        # Skip if it's an image link (starts with ![)
        # But do NOT skip normal links at position 0.
        if match.start() == 0 or text[match.start()-1:match.start()+1] != "![":
            if not any(start <= match.start() < end for start, end, _, _, _ in matches):
                matches.append((match.start(), match.end(), "link", match.group(1), match.group(2)))

    # Bold+italic combo
    for match in re.finditer(bold_italic_pattern, text):
        if not any(start <= match.start() < end for start, end, _, _, _ in matches):
            matches.append((match.start(), match.end(), "bold_italic", match.group(1), None))

    # Bold
    for match in re.finditer(bold_pattern, text):
        if not any(start <= match.start() < end for start, end, _, _, _ in matches):
            matches.append((match.start(), match.end(), "bold", match.group(1), None))

    # Italic
    for match in re.finditer(italic_pattern, text):
        if not any(start <= match.start() < end for start, end, _, _, _ in matches):
            matches.append((match.start(), match.end(), "italic", match.group(1), None))

    # Strikethrough
    for match in re.finditer(strikethrough_pattern, text):
        if not any(start <= match.start() < end for start, end, _, _, _ in matches):
            matches.append((match.start(), match.end(), "strikethrough", match.group(1), None))

    # Sort matches by position
    matches.sort(key=lambda x: x[0])

    # Build tokens
    last_pos = 0
    for start, end, match_type, content, url in matches:
        # Add text before this match
        if start > last_pos:
            tokens.append({"content": text[last_pos:start]})

        # Add the formatted content
        if match_type == "code":
            tokens.append({
                "content": content,
                "marks": [{"type": "code"}]
            })
        elif match_type == "link":
            tokens.append({
                "content": content,
                "marks": [{"type": "link", "attrs": {"href": url}}]
            })
        elif match_type == "bold_italic":
            tokens.append({
                "content": content,
                "marks": [{"type": "strong"}, {"type": "em"}]
            })
        elif match_type == "bold":
            tokens.append({
                "content": content,
                "marks": [{"type": "strong"}]
            })
        elif match_type == "italic":
            tokens.append({
                "content": content,
                "marks": [{"type": "em"}]
            })
        elif match_type == "strikethrough":
            tokens.append({
                "content": content,
                "marks": [{"type": "strikethrough"}]
            })

        last_pos = end

    # Add remaining text
    if last_pos < len(text):
        tokens.append({"content": text[last_pos:]})

    # Filter out empty tokens
    tokens = [t for t in tokens if t.get("content")]

    return tokens


class Post:
    """

    Post utility class

    """

    def __init__(
        self,
        title: str,
        subtitle: str,
        user_id,
        audience: str = None,
        write_comment_permissions: str = None,
    ):
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
        self.draft_section_id = None
        self.section_chosen = True

        # TODO better understand the possible values and combinations with audience
        if write_comment_permissions is not None:
            self.write_comment_permissions = write_comment_permissions
        else:
            self.write_comment_permissions = self.audience

    def set_section(self, name: str, sections: list):
        """

        Args:
            name:
            sections:

        Returns:

        """
        section = [s for s in sections if s.get("name") == name]
        if len(section) != 1:
            raise SectionNotExistsException(name)
        section = section[0]
        self.draft_section_id = section.get("id")

    def add(self, item: Dict):
        """

        Add item to draft body.

        Args:
            item:

        Returns:

        """

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

    def blockquote(self, content=None):
        """
        Add a blockquote to the post.

        The blockquote wraps one or more paragraph nodes.

        Args:
            content: Text string or list of inline token dicts.  When a plain
                string is provided it is wrapped in a single paragraph node.

        Returns:
            Self for method chaining.
        """
        paragraphs: List[Dict] = []
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

        node: Dict = {"type": "blockquote"}
        if paragraphs:
            node["content"] = paragraphs
        self.draft_body["content"] = self.draft_body.get("content", []) + [node]
        return self

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

    def captioned_image(
        self,
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
        internalRedirect: str = None,
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
                    self.text(chunk.get("content")).marks(chunk.get("marks", []))

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
                href = mark.get("href") or mark.get("attrs", {}).get("href")
                new_mark.update({"attrs": {"href": href}})
            content_marks.append(new_mark)
        content["marks"] = content_marks
        return self

    def remove_last_paragraph(self):
        """Remove last paragraph"""
        del self.draft_body.get("content")[-1]

    def get_draft(self):
        """

        Returns:

        """
        out = vars(self)
        out["draft_body"] = json.dumps(out["draft_body"])
        return out

    def subscribe_with_caption(self, message: str = None):
        """

        Add subscribe widget with caption

        Args:
            message:

        Returns:

        """

        if message is None:
            message = """Thanks for reading this newsletter!
            Subscribe for free to receive new posts and support my work."""

        subscribe = self.draft_body["content"][-1]
        subscribe["attrs"] = {
            "url": "%%checkout_url%%",
            "text": "Subscribe",
            "language": "en",
        }
        subscribe["content"] = [
            {
                "type": "ctaCaption",
                "content": [
                    {
                        "type": "text",
                        "text": message,
                    }
                ],
            }
        ]
        return self

    def youtube(self, value: str):
        """

        Add youtube video to post.

        Args:
            value: youtube url

        Returns:

        """
        content_attrs = self.draft_body["content"][-1].get("attrs", {})
        content_attrs.update({"videoId": value})
        self.draft_body["content"][-1]["attrs"] = content_attrs
        return self

    def code_block(self, content, attrs=None):
        """
        Add code block to post.

        Args:
            content: String containing code or list of text nodes
            attrs: Optional attributes like language

        Returns:

        """
        if attrs is None:
            attrs = {}

        # Handle content - can be list of text nodes or a string
        if isinstance(content, str):
            # Convert string to list of text nodes
            code_content = [{"type": "text", "text": content}]
        elif isinstance(content, list):
            code_content = content
        else:
            code_content = []

        # Set up the code block structure
        code_block = self.draft_body["content"][-1]
        code_block["content"] = code_content
        if attrs:
            code_block["attrs"] = attrs

        return self

    def footnote_anchor(self, number: int):
        """

        Add an inline footnote reference (the superscript marker) to the last block.

        Args:
            number: The footnote number this anchor points to.

        Returns:
            Self for method chaining.

        """
        content = self.draft_body["content"][-1].get("content", [])
        content += [{"type": "footnoteAnchor", "attrs": {"number": number}}]
        self.draft_body["content"][-1]["content"] = content
        return self

    def footnote(self, number: int, content=None):
        """

        Append a footnote block (the note shown at the foot of the post).

        Args:
            number: The footnote number, matching a footnote_anchor.
            content: Text string or list of inline token dicts. A plain string is
                parsed for inline Markdown and may contain blank-line-separated
                paragraphs; a parse_inline() token list or a list of ready text
                nodes is also accepted (single paragraph).

        Returns:
            Self for method chaining.

        """
        paragraphs: List[Dict] = []
        if isinstance(content, str):
            # Blank lines separate paragraphs within the footnote.
            for chunk in re.split(r"\n\s*\n", content):
                chunk = chunk.strip()
                if chunk:
                    paragraphs.append(
                        {"type": "paragraph", "content": tokens_to_text_nodes(parse_inline(chunk))}
                    )
        elif isinstance(content, list):
            # Accept either parse_inline tokens ({"content": ...}) or text nodes.
            if content and content[0].get("type") == "text":
                text_nodes = content
            else:
                text_nodes = tokens_to_text_nodes(content)
            paragraphs.append({"type": "paragraph", "content": text_nodes})

        if not paragraphs:
            paragraphs = [{"type": "paragraph", "content": []}]

        node: Dict = {
            "type": "footnote",
            "attrs": {"number": number},
            "content": paragraphs,
        }
        self.draft_body["content"] = self.draft_body.get("content", []) + [node]
        return self

    @staticmethod
    def _extract_footnote_definitions(markdown_content: str):
        """

        Pull ``[^label]: definition`` lines out of the Markdown.

        Definitions may wrap onto indented continuation lines and may contain
        multiple paragraphs (blank line followed by an indented block). Returns
        the body with definitions removed plus a {label: definition_text} mapping,
        where paragraphs are separated by a blank line.

        """
        lines = markdown_content.split("\n")
        body_lines: List[str] = []
        definitions: Dict[str, str] = {}
        in_code_fence = False
        i = 0
        while i < len(lines):
            # Track fenced code blocks so footnote-like lines inside them are
            # left untouched.
            if lines[i].lstrip().startswith("```"):
                in_code_fence = not in_code_fence
                body_lines.append(lines[i])
                i += 1
                continue
            match = None if in_code_fence else FOOTNOTE_DEFINITION_PATTERN.match(lines[i])
            if match:
                label, first = match.group(1), match.group(2)
                paragraphs: List[str] = []
                current = [first.strip()] if first.strip() else []
                i += 1
                while i < len(lines):
                    line = lines[i]
                    if line.strip() == "":
                        # A blank line stays in the footnote only if the next
                        # non-empty line is indented (a further paragraph).
                        nxt = i + 1
                        if (
                            nxt < len(lines)
                            and lines[nxt].strip()
                            and lines[nxt][:1] in (" ", "\t")
                        ):
                            if current:
                                paragraphs.append(" ".join(current))
                                current = []
                            i += 1
                            continue
                        break
                    if line[:1] in (" ", "\t"):
                        current.append(line.strip())
                        i += 1
                    else:
                        break
                if current:
                    paragraphs.append(" ".join(current))
                definitions[label] = "\n\n".join(paragraphs)
            else:
                body_lines.append(lines[i])
                i += 1
        return "\n".join(body_lines), definitions

    @staticmethod
    def _number_footnotes(markdown_content: str, definitions: Dict[str, str]):
        """Number footnotes by order of first inline reference in the body."""
        order: List[str] = []
        for match in FOOTNOTE_REFERENCE_PATTERN.finditer(markdown_content):
            label = match.group(1)
            if label in definitions and label not in order:
                order.append(label)
        # Defined-but-unreferenced footnotes go last, in definition order.
        for label in definitions:
            if label not in order:
                order.append(label)
        return {label: index + 1 for index, label in enumerate(order)}

    def _inject_footnote_anchors(self, node: Dict, numbers_by_label: Dict[str, int]):
        """Recursively replace ``[^label]`` in text nodes with footnoteAnchor nodes."""
        # Never rewrite the contents of a code block.
        if node.get("type") == "codeBlock":
            return
        content = node.get("content")
        if not isinstance(content, list):
            return
        new_content: List[Dict] = []
        for child in content:
            text = child.get("text", "")
            has_code_mark = any(
                mark.get("type") == "code" for mark in (child.get("marks") or [])
            )
            if (
                child.get("type") == "text"
                and not has_code_mark
                and FOOTNOTE_REFERENCE_PATTERN.search(text)
            ):
                marks = child.get("marks")
                last = 0
                for match in FOOTNOTE_REFERENCE_PATTERN.finditer(text):
                    label = match.group(1)
                    if label not in numbers_by_label:
                        continue  # Unknown label: leave the literal text in place.
                    if match.start() > last:
                        segment = {"type": "text", "text": text[last:match.start()]}
                        if marks:
                            segment["marks"] = marks
                        new_content.append(segment)
                    new_content.append(
                        {"type": "footnoteAnchor", "attrs": {"number": numbers_by_label[label]}}
                    )
                    last = match.end()
                if last < len(text):
                    segment = {"type": "text", "text": text[last:]}
                    if marks:
                        segment["marks"] = marks
                    new_content.append(segment)
            else:
                self._inject_footnote_anchors(child, numbers_by_label)
                new_content.append(child)
        node["content"] = new_content

    def from_markdown(self, markdown_content: str, api=None):
        """
        Parse Markdown content and add it to the post.

        Supported Markdown features:
          - Headings: Lines starting with '#' characters (1-6 levels)
          - Images: Markdown image syntax ![Alt](URL)
          - Linked images: [![Alt](image_url)](link_url) - images that are also links
          - Links: [text](url) - inline links in paragraphs
          - Code blocks: Fenced code blocks with ```language or ```
          - Blockquotes: Lines starting with '>' (consecutive lines grouped)
          - Paragraphs: Regular text blocks
          - Bullet lists: Lines starting with '*' or '-'
          - Ordered lists: Lines starting with '1.', '2.', etc.
          - Horizontal rules: Lines with ---, ***, or ___
          - Inline formatting: **bold**, *italic*, ***bold+italic***, `code`, ~~strikethrough~~
          - Footnotes: ``text.[^label]`` references plus ``[^label]: definition``
            lines. References become inline anchors and definitions become
            footnote blocks, numbered by order of first appearance. Labels may be
            numbers or names (e.g. ``[^1]`` or ``[^agi-book]``).

        Args:
            markdown_content: Markdown string to parse and add to the post.
            api: Optional Api instance for uploading local images. If provided,
                 local image paths will be uploaded via api.get_image().

        Returns:
            Self for method chaining.

        Example:
            >>> post = Post("Title", "Subtitle", user_id)
            >>> post.from_markdown("# Heading\\n\\nThis is **bold** text with [a link](https://example.com).")
        """
        # Footnotes: extract ``[^label]: ...`` definitions and number them by
        # order of first reference before parsing the rest of the body.
        markdown_content, footnote_definitions = self._extract_footnote_definitions(
            markdown_content
        )
        footnote_numbers = self._number_footnotes(markdown_content, footnote_definitions)

        lines = markdown_content.split("\n")
        blocks = []
        current_block: List[str] = []
        in_code_block = False
        code_block_language = None

        for line in lines:
            # Check for fenced code block start/end
            if line.strip().startswith("```"):
                if in_code_block:
                    # End of code block
                    if current_block:
                        blocks.append({
                            "type": "code",
                            "language": code_block_language,
                            "content": "\n".join(current_block)
                        })
                    current_block = []
                    in_code_block = False
                    code_block_language = None
                else:
                    # Start of code block
                    if current_block:
                        blocks.append({"type": "text", "content": "\n".join(current_block)})
                        current_block = []
                    # Extract language if specified
                    language = line.strip()[3:].strip()
                    code_block_language = language if language else None
                    in_code_block = True
                continue

            if in_code_block:
                # Inside code block - collect lines as-is
                current_block.append(line)
            else:
                # Regular content
                if line.strip() == "":
                    # Empty line - end current block if it has content
                    if current_block:
                        blocks.append({"type": "text", "content": "\n".join(current_block)})
                        current_block = []
                else:
                    current_block.append(line)

        # Add any remaining content
        if current_block:
            if in_code_block:
                blocks.append({
                    "type": "code",
                    "language": code_block_language,
                    "content": "\n".join(current_block)
                })
            else:
                blocks.append({"type": "text", "content": "\n".join(current_block)})

        # Process blocks
        for block in blocks:
            if block["type"] == "code":
                # Add code block
                code_content = block.get("content", "").strip()
                if code_content:
                    # Substack uses "codeBlock" type
                    code_attrs = {}
                    if block.get("language"):
                        code_attrs["language"] = block["language"]
                    self.add({
                        "type": "codeBlock",
                        "content": code_content,  # Pass as string, code_block method will handle it
                        "attrs": code_attrs
                    })
            else:
                # Process text block
                text_content = block.get("content", "").strip()
                if not text_content:
                    continue

                # Check for horizontal rule: ---, ***, ___
                if re.match(r'^(\*{3,}|-{3,}|_{3,})\s*$', text_content):
                    self.horizontal_rule()
                    continue

                # Process headings (lines starting with '#' characters)
                if text_content.startswith("#"):
                    level = len(text_content) - len(text_content.lstrip("#"))
                    heading_text = text_content.lstrip("#").strip()
                    if heading_text:  # Only add if there's actual text
                        self.heading(content=heading_text, level=min(level, 6))

                # Process images using Markdown image syntax: ![Alt](URL)
                # Also handle linked images: [![Alt](image_url)](link_url)
                elif text_content.startswith("!") or (text_content.startswith("[") and "![" in text_content):
                    # Check for linked image first: [![alt](img)](link)
                    linked_image_match = re.match(r'\[!\[([^\]]*)\]\(([^)]+)\)\]\(([^)]+)\)', text_content)
                    if linked_image_match:
                        # Linked image - create image with href
                        alt_text = linked_image_match.group(1)
                        image_url = linked_image_match.group(2)
                        link_url = linked_image_match.group(3)

                        # Adjust image URL if it starts with a slash
                        image_url = image_url[1:] if image_url.startswith("/") else image_url

                        # If api is provided and image_url is a local file, upload it
                        if api is not None:
                            try:
                                image = api.get_image(image_url)
                                image_url = image.get("url")
                            except Exception:
                                # If upload fails, use original URL
                                pass

                        self.add({
                            "type": "captionedImage",
                            "src": image_url,
                            "alt": alt_text,
                            "href": link_url
                        })
                    else:
                        # Regular image: ![Alt](URL)
                        match = re.match(r"!\[.*?\]\((.*?)\)", text_content)
                        if match:
                            image_url = match.group(1)
                            # Adjust image URL if it starts with a slash
                            image_url = image_url[1:] if image_url.startswith("/") else image_url

                            # If api is provided and image_url is a local file, upload it
                            if api is not None:
                                try:
                                    image = api.get_image(image_url)
                                    image_url = image.get("url")
                                except Exception:
                                    # If upload fails, use original URL
                                    pass

                            self.add({"type": "captionedImage", "src": image_url})

                # Process paragraphs, bullet lists, ordered lists, or blockquotes
                else:
                    if "\n" in text_content:
                        # Process each line, grouping consecutive bullets/ordered items
                        # into list nodes and consecutive blockquote lines into a
                        # single blockquote node.
                        pending_bullets: List[List[Dict]] = []
                        pending_quotes: List[str] = []
                        pending_ordered: List[List[Dict]] = []

                        def flush_bullets():
                            if not pending_bullets:
                                return
                            list_items = []
                            for bullet_nodes in pending_bullets:
                                list_items.append({
                                    "type": "list_item",
                                    "content": [{"type": "paragraph", "content": bullet_nodes}],
                                })
                            self.draft_body["content"].append(
                                {"type": "bullet_list", "content": list_items}
                            )
                            pending_bullets.clear()

                        def flush_quotes():
                            if not pending_quotes:
                                return
                            paragraphs: List[Dict] = []
                            for quote_line in pending_quotes:
                                tokens = parse_inline(quote_line)
                                text_nodes = tokens_to_text_nodes(tokens)
                                if text_nodes:
                                    paragraphs.append({"type": "paragraph", "content": text_nodes})
                            node: Dict = {"type": "blockquote"}
                            if paragraphs:
                                node["content"] = paragraphs
                            self.draft_body["content"].append(node)
                            pending_quotes.clear()

                        def flush_ordered():
                            if not pending_ordered:
                                return
                            list_items = []
                            for item_nodes in pending_ordered:
                                list_items.append({
                                    "type": "list_item",
                                    "content": [{"type": "paragraph", "content": item_nodes}],
                                })
                            self.draft_body["content"].append(
                                {"type": "ordered_list", "content": list_items}
                            )
                            pending_ordered.clear()

                        for line in text_content.split("\n"):
                            line = line.strip()
                            if not line:
                                flush_bullets()
                                flush_ordered()
                                flush_quotes()
                                continue

                            # Check for blockquote marker
                            if line.startswith("> ") or line == ">":
                                flush_bullets()
                                flush_ordered()
                                quote_text = line[2:] if line.startswith("> ") else ""
                                pending_quotes.append(quote_text)
                                continue

                            # Check for ordered list marker
                            ordered_match = re.match(r'^(\d+)\.\s+(.*)', line)
                            if ordered_match:
                                flush_bullets()
                                flush_quotes()
                                item_text = ordered_match.group(2).strip()
                                tokens = parse_inline(item_text)
                                text_nodes = tokens_to_text_nodes(tokens)
                                if text_nodes:
                                    pending_ordered.append(text_nodes)
                                continue

                            # Check for bullet marker
                            bullet_text = None
                            if line.startswith("* "):
                                bullet_text = line[2:].strip()
                            elif line.startswith("- "):
                                bullet_text = line[2:].strip()
                            elif line.startswith("*") and not line.startswith("**"):
                                bullet_text = line[1:].strip()

                            if bullet_text is not None:
                                flush_ordered()
                                flush_quotes()
                                tokens = parse_inline(bullet_text)
                                text_nodes = tokens_to_text_nodes(tokens)
                                if text_nodes:
                                    pending_bullets.append(text_nodes)
                            else:
                                flush_bullets()
                                flush_ordered()
                                flush_quotes()
                                tokens = parse_inline(line)
                                self.add({"type": "paragraph", "content": tokens})

                        flush_bullets()
                        flush_ordered()
                        flush_quotes()
                    else:
                        # Single line — blockquote, ordered list, or paragraph
                        if text_content.startswith("> ") or text_content == ">":
                            quote_text = text_content[2:] if text_content.startswith("> ") else ""
                            tokens = parse_inline(quote_text)
                            text_nodes = tokens_to_text_nodes(tokens)
                            para = {"type": "paragraph", "content": text_nodes} if text_nodes else {"type": "paragraph"}
                            self.draft_body["content"] = self.draft_body.get("content", []) + [
                                {"type": "blockquote", "content": [para]}
                            ]

                        elif re.match(r'^(\d+)\.\s+(.*)', text_content):
                            ordered_match = re.match(r'^(\d+)\.\s+(.*)', text_content)
                            item_text = ordered_match.group(2).strip()
                            tokens = parse_inline(item_text)
                            text_nodes = tokens_to_text_nodes(tokens)
                            if text_nodes:
                                list_item = {
                                    "type": "list_item",
                                    "content": [{"type": "paragraph", "content": text_nodes}],
                                }
                                self.draft_body["content"].append(
                                    {"type": "ordered_list", "content": [list_item]}
                                )

                        else:
                            tokens = parse_inline(text_content)
                            self.add({"type": "paragraph", "content": tokens})

        # Footnotes: turn ``[^label]`` references into inline anchors, then append
        # the footnote blocks in numbered order.
        if footnote_numbers:
            self._inject_footnote_anchors(self.draft_body, footnote_numbers)
            for label, number in sorted(footnote_numbers.items(), key=lambda item: item[1]):
                self.footnote(number, footnote_definitions[label])

        return self

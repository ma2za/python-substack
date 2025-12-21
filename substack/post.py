"""

Post Utilities

"""

import json
import re
from typing import Dict, List

__all__ = ["Post", "parse_inline"]

from substack.exceptions import SectionNotExistsException


def parse_inline(text: str) -> List[Dict]:
    """
    Convert inline Markdown in a text string into a list of tokens
    for use in the post content.

    Supported formatting:
      - **Bold**: Text wrapped in double asterisks.
      - *Italic*: Text wrapped in single asterisks.
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
    # Process text character by character to handle nested formatting
    # We'll use regex to find all markdown patterns, then process them in order
    
    # Find all markdown patterns: links, bold, italic
    # Pattern order: links first (to avoid conflicts), then bold, then italic
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    bold_pattern = r'\*\*([^*]+)\*\*'
    italic_pattern = r'(?<!\*)\*([^*]+)\*(?!\*)'  # Not preceded or followed by *
    
    # Find all matches with their positions
    matches = []
    for match in re.finditer(link_pattern, text):
        # Skip if it's an image link (starts with ![)
        if match.start() > 0 and text[match.start()-1:match.start()+1] != "![":
            matches.append((match.start(), match.end(), "link", match.group(1), match.group(2)))
    
    for match in re.finditer(bold_pattern, text):
        # Check if this range is already covered by a link
        if not any(start <= match.start() < end for start, end, _, _, _ in matches):
            matches.append((match.start(), match.end(), "bold", match.group(1), None))
    
    for match in re.finditer(italic_pattern, text):
        # Check if this range is already covered by a link or bold
        if not any(start <= match.start() < end for start, end, _, _, _ in matches):
            matches.append((match.start(), match.end(), "italic", match.group(1), None))
    
    # Sort matches by position
    matches.sort(key=lambda x: x[0])
    
    # Build tokens
    last_pos = 0
    for start, end, match_type, content, url in matches:
        # Add text before this match
        if start > last_pos:
            tokens.append({"content": text[last_pos:start]})
        
        # Add the formatted content
        if match_type == "link":
            tokens.append({
                "content": content,
                "marks": [{"type": "link", "attrs": {"href": url}}]
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
                href = mark.get("href")
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

    def from_markdown(self, markdown_content: str, api=None):
        """
        Parse Markdown content and add it to the post.

        Supported Markdown features:
          - Headings: Lines starting with '#' characters (1-6 levels)
          - Images: Markdown image syntax ![Alt](URL)
          - Linked images: [![Alt](image_url)](link_url) - images that are also links
          - Links: [text](url) - inline links in paragraphs
          - Code blocks: Fenced code blocks with ```language or ```
          - Paragraphs: Regular text blocks
          - Bullet lists: Lines starting with '*' or '-'
          - Inline formatting: **bold** and *italic* within paragraphs

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

                # Process paragraphs or bullet lists
                else:
                    if "\n" in text_content:
                        # Process each line separately (for bullet lists)
                        for line in text_content.split("\n"):
                            line = line.strip()
                            if not line:
                                continue
                            # Remove bullet marker if present
                            if line.startswith("* "):
                                line = line[2:].strip()
                            elif line.startswith("- "):
                                line = line[2:].strip()
                            elif line.startswith("*") and not line.startswith("**"):
                                line = line[1:].strip()

                            if line:
                                tokens = parse_inline(line)
                                self.add({"type": "paragraph", "content": tokens})
                    else:
                        # Single paragraph
                        tokens = parse_inline(text_content)
                        self.add({"type": "paragraph", "content": tokens})

        return self

"""ProseMirror node builders for Substack documents.

Centralises the (undocumented) Substack ProseMirror schema in one place.
The node-type strings ("paragraph", "footnoteAnchor", "image2", ...) and
their shapes live here rather than as inline dict literals scattered across
post.py, giving:

  * one source of truth for node shapes (so a schema change is a one-line fix),
  * discoverable, typed constructors instead of bare dict literals,
  * a natural seam for validation.

The builders intentionally return plain dicts so they stay 100% compatible with
the existing draft_body structure.
"""

from __future__ import annotations

from typing import Dict, List, Optional


class NodeType:
    DOC = "doc"
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    TEXT = "text"
    BLOCKQUOTE = "blockquote"
    CODE_BLOCK = "codeBlock"
    HORIZONTAL_RULE = "horizontal_rule"
    BULLET_LIST = "bullet_list"
    ORDERED_LIST = "ordered_list"
    LIST_ITEM = "list_item"
    FOOTNOTE = "footnote"
    FOOTNOTE_ANCHOR = "footnoteAnchor"
    CAPTIONED_IMAGE = "captionedImage"
    CAPTION = "caption"
    LATEX_BLOCK = "latex_block"
    LATEX_INLINE = "latex"
    TABLE = "table"
    TABLE_ROW = "table_row"
    TABLE_HEADER = "table_header"
    TABLE_CELL = "table_cell"


class MarkType:
    STRONG = "strong"
    EM = "em"
    CODE = "code"
    STRIKETHROUGH = "strikethrough"
    LINK = "link"


def code_mark() -> Dict:
    return {"type": MarkType.CODE}


def text(value: str, marks: Optional[List[Dict]] = None) -> Dict:
    node: Dict = {"type": NodeType.TEXT, "text": value}
    if marks:
        node["marks"] = marks
    return node


def link_mark(href: str) -> Dict:
    return {"type": MarkType.LINK, "attrs": {"href": href}}


def paragraph(content: Optional[List[Dict]] = None) -> Dict:
    return {"type": NodeType.PARAGRAPH, "content": content or []}


def heading(content: List[Dict], level: int = 1) -> Dict:
    return {"type": NodeType.HEADING, "content": content, "attrs": {"level": level}}


def horizontal_rule() -> Dict:
    return {"type": NodeType.HORIZONTAL_RULE}


def blockquote(paragraphs: List[Dict]) -> Dict:
    node: Dict = {"type": NodeType.BLOCKQUOTE}
    if paragraphs:
        node["content"] = paragraphs
    return node


def list_item(content_nodes: List[Dict]) -> Dict:
    return {
        "type": NodeType.LIST_ITEM,
        "content": [paragraph(content_nodes)],
    }


def bullet_list(items: List[Dict]) -> Dict:
    return {"type": NodeType.BULLET_LIST, "content": items}


def ordered_list(items: List[Dict]) -> Dict:
    return {"type": NodeType.ORDERED_LIST, "content": items}


def code_block(code: str, language: Optional[str] = None) -> Dict:
    node: Dict = {"type": NodeType.CODE_BLOCK, "content": [text(code)]}
    if language:
        node["attrs"] = {"language": language}
    return node


def captioned_image(
    src: str,
    alt: Optional[str] = None,
    href: Optional[str] = None,
    caption: Optional[List[Dict]] = None,
    image_size: str = "normal",
) -> Dict:
    content: List[Dict] = [
        {
            "type": "image2",
            "attrs": {
                "src": src,
                "srcNoWatermark": None,
                "fullscreen": False,
                "imageSize": image_size,
                "height": 819,
                "width": 1456,
                "resizeWidth": 728 if image_size == "normal" else None,
                "bytes": None,
                "alt": alt,
                "title": None,
                "type": None,
                "href": href,
                "belowTheFold": False,
                "topImage": False,
                "internalRedirect": None,
                "isProcessing": False,
                "align": None,
                "offset": False,
            },
        }
    ]
    if caption:
        content.append({"type": NodeType.CAPTION, "content": caption})
    return {"type": NodeType.CAPTIONED_IMAGE, "content": content}


def footnote_anchor(number: int) -> Dict:
    return {"type": NodeType.FOOTNOTE_ANCHOR, "attrs": {"number": number}}


def footnote(number: int, paragraphs: List[Dict]) -> Dict:
    return {
        "type": NodeType.FOOTNOTE,
        "attrs": {"number": number},
        "content": paragraphs or [paragraph()],
    }


def latex_block(expression: str) -> Dict:
    return {
        "type": NodeType.LATEX_BLOCK,
        "attrs": {"persistentExpression": expression, "dirty": True},
    }


def latex_inline(expression: str) -> Dict:
    return {
        "type": NodeType.LATEX_INLINE,
        "attrs": {"expression": expression, "persistentExpression": expression},
    }


def table(rows: List[Dict]) -> Dict:
    return {"type": NodeType.TABLE, "content": rows}


def table_row(cells: List[Dict]) -> Dict:
    return {"type": NodeType.TABLE_ROW, "content": cells}


def table_header(content: List[Dict]) -> Dict:
    return {"type": NodeType.TABLE_HEADER, "content": content}


def table_cell(content: List[Dict]) -> Dict:
    return {"type": NodeType.TABLE_CELL, "content": content}

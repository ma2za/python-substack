"""Markdown -> Substack ProseMirror via markdown-it-py.

Implements Post.from_markdown() using a real CommonMark parser (markdown-it-py)
plus the standard footnote plugin, with a small renderer that walks the syntax
tree into Substack's node schema.

Node construction goes through ``substack.nodes`` so the (undocumented) schema
lives in exactly one place.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from mdit_py_plugins.footnote import footnote_plugin

from substack import nodes
from substack.nodes import MarkType, NodeType

_MARK_FOR = {
    "strong": {"type": MarkType.STRONG},
    "em": {"type": MarkType.EM},
    "s": {"type": MarkType.STRIKETHROUGH},
}


def _make_parser() -> MarkdownIt:
    return MarkdownIt("commonmark").use(footnote_plugin).enable("strikethrough")


def _coalesce(out_nodes: List[Dict]) -> List[Dict]:
    """Merge adjacent text nodes that carry identical marks (e.g. softbreaks)."""
    merged: List[Dict] = []
    for node in out_nodes:
        if (
            merged
            and node.get("type") == NodeType.TEXT
            and merged[-1].get("type") == NodeType.TEXT
            and node.get("marks") == merged[-1].get("marks")
        ):
            merged[-1]["text"] += node["text"]
        else:
            merged.append(node)
    return merged


def _render_inline(node: SyntaxTreeNode, marks: List[Dict]) -> List[Dict]:
    """Render an inline subtree into a flat list of text / anchor nodes."""
    out: List[Dict] = []
    for child in node.children:
        t = child.type
        if t == "text":
            if child.content:
                out.append(nodes.text(child.content, marks))
        elif t == "code_inline":
            out.append(nodes.text(child.content, marks + [nodes.code_mark()]))
        elif t in _MARK_FOR:
            out.extend(_render_inline(child, marks + [_MARK_FOR[t]]))
        elif t == "link":
            href = child.attrs.get("href", "")
            out.extend(_render_inline(child, marks + [nodes.link_mark(href)]))
        elif t in ("softbreak", "hardbreak"):
            out.append(nodes.text(" ", marks))
        elif t == "footnote_ref":
            out.append(nodes.footnote_anchor(child.meta["id"] + 1))
        elif t == "image":
            # Inline images are rare in this schema; fall back to alt text.
            alt = child.attrs.get("alt") or "".join(
                c.content for c in child.children if c.type == "text"
            )
            if alt:
                out.append(nodes.text(alt, marks))
    return _coalesce(out)


def _only_image(inline: SyntaxTreeNode) -> Optional[SyntaxTreeNode]:
    """If an inline node is just an image (optionally wrapped in a link), return it."""
    kids = [c for c in inline.children if c.type != "softbreak"]
    if len(kids) == 1 and kids[0].type == "image":
        return kids[0]
    if len(kids) == 1 and kids[0].type == "link":
        inner = [c for c in kids[0].children if c.type != "softbreak"]
        if len(inner) == 1 and inner[0].type == "image":
            img = inner[0]
            img._link_href = kids[0].attrs.get("href")  # type: ignore[attr-defined]
            return img
    return None


def _captioned_image(img: SyntaxTreeNode, api) -> Dict:
    src = img.attrs.get("src", "")
    if src.startswith("/"):
        src = src[1:]
    if api is not None and not src.startswith("http"):
        try:
            src = api.get_image(src).get("url")
        except Exception:
            pass
    # markdown-it stores the image alt text as the node's content, not in attrs.
    alt = img.content or img.attrs.get("alt") or None
    return nodes.captioned_image(
        src,
        alt=alt,
        href=getattr(img, "_link_href", None),
    )


def _render_block(node: SyntaxTreeNode, api) -> List[Dict]:
    """Render a block-level node into zero or more Substack nodes."""
    t = node.type

    if t == "paragraph":
        inline = node.children[0]
        img = _only_image(inline)
        if img is not None:
            return [_captioned_image(img, api)]
        return [nodes.paragraph(_render_inline(inline, []))]

    if t == "heading":
        level = int(node.tag[1])
        return [nodes.heading(_render_inline(node.children[0], []), level=level)]

    if t == "hr":
        return [nodes.horizontal_rule()]

    if t in ("fence", "code_block"):
        return [
            nodes.code_block(
                node.content.rstrip("\n"), language=node.info.strip() or None
            )
        ]

    if t == "blockquote":
        paras: List[Dict] = []
        for child in node.children:
            paras.extend(_render_block(child, api))
        return [nodes.blockquote(paras)]

    if t == "bullet_list":
        return [nodes.bullet_list(_render_list_items(node, api))]

    if t == "ordered_list":
        return [nodes.ordered_list(_render_list_items(node, api))]

    if t == "footnote_block":
        out = []
        for fn in node.children:
            number = fn.meta["id"] + 1
            paras = [
                nodes.paragraph(_render_inline(child.children[0], []))
                for child in fn.children
                if child.type == "paragraph"
            ]
            out.append(nodes.footnote(number, paras))
        return out

    return []


def _render_list_items(list_node: SyntaxTreeNode, api) -> List[Dict]:
    items = []
    for li in list_node.children:
        # A list_item built by nodes.list_item wraps inline content in a single
        # paragraph; here items may already contain block nodes, so build directly.
        content: List[Dict] = []
        for child in li.children:
            content.extend(_render_block(child, api))
        items.append({"type": NodeType.LIST_ITEM, "content": content})
    return items


def markdown_to_doc(markdown_content: str, api=None) -> List[Dict]:
    """Convert Markdown into a list of Substack ProseMirror block nodes."""
    tree = SyntaxTreeNode(_make_parser().parse(markdown_content))
    out: List[Dict] = []
    for node in tree.children:
        out.extend(_render_block(node, api))
    return out

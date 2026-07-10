"""Markdown -> Substack ProseMirror via markdown-it-py.

Implements Post.from_markdown() using a real CommonMark parser (markdown-it-py)
plus the standard footnote plugin, with a small renderer that walks the syntax
tree into Substack's node schema.

Node construction goes through ``substack.nodes`` so the (undocumented) schema
lives in exactly one place.

Footnotes: Substack numbers footnote anchors by their position in the document
and pairs them one-to-one, in order, with the footnote blocks at the end (it
ignores any explicit number and does not support one block serving several
anchors). So each reference is emitted as its own sequentially-numbered anchor,
and a matching footnote block is appended for each -- a definition referenced
more than once is duplicated, which mirrors how Substack's own editor behaves.
"""

from __future__ import annotations

import copy
from typing import Dict, List, Optional

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin

from substack import nodes
from substack.nodes import MarkType, NodeType

_MARK_FOR = {
    "strong": {"type": MarkType.STRONG},
    "em": {"type": MarkType.EM},
    "s": {"type": MarkType.STRIKETHROUGH},
}


def _make_parser() -> MarkdownIt:
    return (
        MarkdownIt("commonmark")
        .use(footnote_plugin)
        .use(dollarmath_plugin, double_inline=True)
        .enable("strikethrough")
        .enable("table")
    )


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


def _render_inline(node: SyntaxTreeNode, marks: List[Dict], ctx: Dict) -> List[Dict]:
    """Render an inline subtree into a flat list of text / anchor nodes."""
    out: List[Dict] = []
    for child in node.children:
        t = child.type
        if t == "text":
            if child.content:
                out.append(nodes.text(child.content, marks))
        elif t == "code_inline":
            out.append(nodes.text(child.content, marks + [nodes.code_mark()]))
        elif t in ("math_inline", "math_inline_double"):
            out.append(nodes.latex_inline(child.content.strip()))
        elif t in _MARK_FOR:
            out.extend(_render_inline(child, marks + [_MARK_FOR[t]], ctx))
        elif t == "link":
            href = child.attrs.get("href", "")
            out.extend(_render_inline(child, marks + [nodes.link_mark(href)], ctx))
        elif t in ("softbreak", "hardbreak"):
            out.append(nodes.text(" ", marks))
        elif t == "footnote_ref":
            # Number anchors by document position and record which definition each
            # one points to, so matching blocks can be emitted 1:1 afterwards.
            ctx["order"].append(child.meta["id"])
            out.append(nodes.footnote_anchor(len(ctx["order"])))
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
    # Standard markdown image title `![alt](src "caption")` maps to Substack's caption node.
    title = img.attrs.get("title") or None
    caption = [nodes.text(title)] if title else None
    return nodes.captioned_image(
        src,
        alt=alt,
        href=getattr(img, "_link_href", None),
        caption=caption,
    )


def _render_block(node: SyntaxTreeNode, api, ctx: Dict) -> List[Dict]:
    """Render a block-level node into zero or more Substack nodes."""
    t = node.type

    if t == "paragraph":
        inline = node.children[0]
        img = _only_image(inline)
        if img is not None:
            return [_captioned_image(img, api)]
        return [nodes.paragraph(_render_inline(inline, [], ctx))]

    if t == "heading":
        level = int(node.tag[1])
        return [nodes.heading(_render_inline(node.children[0], [], ctx), level=level)]

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
            paras.extend(_render_block(child, api, ctx))
        return [nodes.blockquote(paras)]

    if t == "bullet_list":
        return [nodes.bullet_list(_render_list_items(node, api, ctx))]

    if t == "ordered_list":
        return [nodes.ordered_list(_render_list_items(node, api, ctx))]

    if t == "math_block":
        return [nodes.latex_block(node.content.strip())]

    if t == "table":
        return [_render_table(node, None, ctx)]

    # footnote_block is handled separately in markdown_to_doc; ignore it here.
    return []


def _render_table(node: SyntaxTreeNode, _api, ctx: Dict) -> Dict:
    rows = []
    for section in node.children:  # thead, tbody
        for tr in section.children:
            cells = []
            for cell in tr.children:  # th or td
                inline = cell.children[0] if cell.children else None
                content = _render_inline(inline, [], ctx) if inline else []
                if cell.type == "th":
                    cells.append(nodes.table_header([nodes.paragraph(content)]))
                else:
                    cells.append(nodes.table_cell([nodes.paragraph(content)]))
            rows.append(nodes.table_row(cells))
    return nodes.table(rows)


def _render_list_items(list_node: SyntaxTreeNode, api, ctx: Dict) -> List[Dict]:
    items = []
    for li in list_node.children:
        content: List[Dict] = []
        for child in li.children:
            content.extend(_render_block(child, api, ctx))
        items.append({"type": NodeType.LIST_ITEM, "content": content})
    return items


def _footnote_definitions(tree: SyntaxTreeNode, api) -> Dict[int, List[Dict]]:
    """Map each footnote id to its rendered block content."""
    definitions: Dict[int, List[Dict]] = {}
    for node in tree.children:
        if node.type != "footnote_block":
            continue
        for fn in node.children:
            # A footnote's own content should not register anchors of its own.
            local_ctx = {"order": []}
            content: List[Dict] = []
            for child in fn.children:
                content.extend(_render_block(child, api, local_ctx))
            definitions[fn.meta["id"]] = content
    return definitions


def markdown_to_doc(markdown_content: str, api=None) -> List[Dict]:
    """Convert Markdown into a list of Substack ProseMirror block nodes."""
    tree = SyntaxTreeNode(_make_parser().parse(markdown_content))

    definitions = _footnote_definitions(tree, api)

    ctx: Dict = {"order": []}
    out: List[Dict] = []
    for node in tree.children:
        if node.type == "footnote_block":
            continue
        out.extend(_render_block(node, api, ctx))

    # Emit one footnote block per reference, in anchor order, numbered to match.
    for number, footnote_id in enumerate(ctx["order"], start=1):
        content = copy.deepcopy(definitions.get(footnote_id, []))
        out.append(nodes.footnote(number, content))

    return out

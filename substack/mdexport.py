import base64
import copy
import json
import re

_BLOCK_TYPES = {
    "paragraph",
    "heading",
    "blockquote",
    "codeBlock",
    "horizontal_rule",
    "bullet_list",
    "ordered_list",
    "captionedImage",
    "footnote",
    "latex_block",
    "pullquote",
    "calloutBlock",
}
_MARK_TYPES = {
    "strong",
    "em",
    "code",
    "strikethrough",
    "superscript",
    "subscript",
    "link",
}
_IMAGE_ATTRS = {
    "src",
    "srcNoWatermark",
    "fullscreen",
    "imageSize",
    "height",
    "width",
    "resizeWidth",
    "bytes",
    "alt",
    "title",
    "type",
    "href",
    "belowTheFold",
    "topImage",
    "internalRedirect",
    "isProcessing",
    "align",
    "offset",
}


def _marker(node, unsupported):
    unsupported.append(copy.deepcopy(node))
    payload = json.dumps(
        node, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    return f"<!-- python-substack-node:v1 {encoded} -->"


def _require_dict(node, context):
    if not isinstance(node, dict):
        raise ValueError(f"Malformed draft body: {context} must be an object")
    if not isinstance(node.get("type"), str) or not node["type"]:
        raise ValueError(f"Malformed draft body: {context} has no node type")


def _content(node, context):
    content = node.get("content", [])
    if not isinstance(content, list):
        raise ValueError(f"Malformed draft body: {context} content must be a list")
    return content


def _attrs(node, context):
    attrs = node.get("attrs", {})
    if not isinstance(attrs, dict):
        raise ValueError(f"Malformed draft body: {context} attrs must be an object")
    return attrs


def _has_unknown_keys(value, allowed):
    return bool(set(value) - set(allowed))


def _escape_text(value):
    return re.sub(r"([\\`*_{}\[\]()<>#+\-.!|])", r"\\\1", value)


def _escape_destination(value):
    return str(value).replace("\\", "\\\\").replace(")", "\\)")


def _escape_title(value):
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _code_span(value):
    runs = [len(match.group(0)) for match in re.finditer(r"`+", value)]
    delimiter = "`" * max(1, (max(runs) + 1) if runs else 1)
    padding = " " if value.startswith(("`", " ")) or value.endswith(("`", " ")) else ""
    return f"{delimiter}{padding}{value}{padding}{delimiter}"


def _render_marked_text(value, marks, node, unsupported):
    if not isinstance(value, str) or not isinstance(marks, list):
        raise ValueError("Malformed draft body: text and marks have invalid types")
    for mark in marks:
        _require_dict(mark, "mark")
        if mark["type"] not in _MARK_TYPES:
            return _marker(node, unsupported)
        allowed = {"type", "attrs"} if mark["type"] == "link" else {"type"}
        if _has_unknown_keys(mark, allowed):
            return _marker(node, unsupported)

    rendered = (
        _code_span(value)
        if any(mark["type"] == "code" for mark in marks)
        else _escape_text(value)
    )
    for mark in marks:
        mark_type = mark["type"]
        if mark_type == "code":
            continue
        if mark_type == "strong":
            rendered = f"**{rendered}**"
        elif mark_type == "em":
            rendered = f"*{rendered}*"
        elif mark_type == "strikethrough":
            rendered = f"~~{rendered}~~"
        elif mark_type == "superscript":
            rendered = f"^{rendered}^"
        elif mark_type == "subscript":
            rendered = f"~{rendered}~"
        elif mark_type == "link":
            attrs = _attrs(mark, "link mark")
            if _has_unknown_keys(attrs, {"href"}) or not isinstance(
                attrs.get("href"), str
            ):
                return _marker(node, unsupported)
            rendered = f"[{rendered}]({_escape_destination(attrs['href'])})"
    return rendered


def _render_inline(nodes, unsupported):
    if not isinstance(nodes, list):
        raise ValueError("Malformed draft body: inline content must be a list")
    rendered = []
    for node in nodes:
        _require_dict(node, "inline node")
        node_type = node["type"]
        if node_type == "text":
            if _has_unknown_keys(node, {"type", "text", "marks"}):
                rendered.append(_marker(node, unsupported))
                continue
            rendered.append(
                _render_marked_text(
                    node.get("text"), node.get("marks", []), node, unsupported
                )
            )
        elif node_type == "footnoteAnchor":
            attrs = _attrs(node, "footnote anchor")
            number = attrs.get("number")
            if (
                _has_unknown_keys(node, {"type", "attrs"})
                or _has_unknown_keys(attrs, {"number"})
                or not isinstance(number, int)
            ):
                rendered.append(_marker(node, unsupported))
            else:
                rendered.append(f"[^{number}]")
        elif node_type == "latex":
            attrs = _attrs(node, "inline math")
            expression = attrs.get("expression", attrs.get("persistentExpression"))
            if (
                _has_unknown_keys(node, {"type", "attrs"})
                or _has_unknown_keys(attrs, {"expression", "persistentExpression"})
                or not isinstance(expression, str)
            ):
                rendered.append(_marker(node, unsupported))
            else:
                rendered.append(f"${expression}$")
        else:
            rendered.append(_marker(node, unsupported))
    return "".join(rendered)


def _render_list(node, unsupported, ordered=False):
    lines = []
    for index, item in enumerate(_content(node, "list"), start=1):
        _require_dict(item, "list item")
        if item["type"] != "list_item" or _has_unknown_keys(item, {"type", "content"}):
            item_text = _marker(item, unsupported)
        else:
            item_blocks = [
                _render_block(child, unsupported)
                for child in _content(item, "list item")
            ]
            item_text = "\n\n".join(item_blocks)
        prefix = f"{index}. " if ordered else "- "
        item_lines = item_text.splitlines() or [""]
        lines.append(prefix + item_lines[0])
        lines.extend("    " + line if line else "" for line in item_lines[1:])
    return "\n".join(lines)


def _render_image(node, unsupported):
    content = _content(node, "captioned image")
    if not content:
        raise ValueError("Malformed draft body: captioned image has no image")
    image = content[0]
    _require_dict(image, "image")
    attrs = _attrs(image, "image")
    if (
        image["type"] != "image2"
        or _has_unknown_keys(node, {"type", "content"})
        or _has_unknown_keys(image, {"type", "attrs"})
        or _has_unknown_keys(attrs, _IMAGE_ATTRS)
        or not isinstance(attrs.get("src"), str)
    ):
        return _marker(node, unsupported)

    alt = str(attrs.get("alt") or "").replace("\\", "\\\\").replace("]", "\\]")
    image_markdown = f"![{alt}]({_escape_destination(attrs['src'])}"
    if len(content) > 2:
        return _marker(node, unsupported)
    if len(content) == 2:
        caption = content[1]
        _require_dict(caption, "image caption")
        caption_nodes = _content(caption, "image caption")
        if (
            caption["type"] != "caption"
            or _has_unknown_keys(caption, {"type", "content"})
            or any(
                not isinstance(child, dict)
                or child.get("type") != "text"
                or child.get("marks")
                or not isinstance(child.get("text"), str)
                for child in caption_nodes
            )
        ):
            return _marker(node, unsupported)
        caption_text = "".join(child.get("text", "") for child in caption_nodes)
        image_markdown += f' "{_escape_title(caption_text)}"'
    image_markdown += ")"
    href = attrs.get("href")
    if href:
        if not isinstance(href, str):
            return _marker(node, unsupported)
        image_markdown = f"[{image_markdown}]({_escape_destination(href)})"
    return image_markdown


def _render_footnote(node, unsupported):
    attrs = _attrs(node, "footnote")
    number = attrs.get("number")
    if (
        _has_unknown_keys(node, {"type", "attrs", "content"})
        or _has_unknown_keys(attrs, {"number"})
        or not isinstance(number, int)
    ):
        return _marker(node, unsupported)
    body = "\n\n".join(
        _render_block(child, unsupported) for child in _content(node, "footnote")
    )
    lines = body.splitlines() or [""]
    return f"[^{number}]: {lines[0]}" + "".join(
        f"\n    {line}" if line else "\n" for line in lines[1:]
    )


def _render_block(node, unsupported):
    _require_dict(node, "block node")
    node_type = node["type"]
    if node_type not in _BLOCK_TYPES:
        return _marker(node, unsupported)

    if node_type == "paragraph":
        if _has_unknown_keys(node, {"type", "content"}):
            return _marker(node, unsupported)
        return _render_inline(_content(node, "paragraph"), unsupported)
    if node_type == "heading":
        attrs = _attrs(node, "heading")
        level = attrs.get("level")
        if (
            _has_unknown_keys(node, {"type", "content", "attrs"})
            or _has_unknown_keys(attrs, {"level"})
            or not isinstance(level, int)
            or not 1 <= level <= 6
        ):
            return _marker(node, unsupported)
        return f"{'#' * level} {_render_inline(_content(node, 'heading'), unsupported)}"
    if node_type == "horizontal_rule":
        return (
            "---"
            if not _has_unknown_keys(node, {"type"})
            else _marker(node, unsupported)
        )
    if node_type == "codeBlock":
        attrs = _attrs(node, "code block")
        if _has_unknown_keys(node, {"type", "content", "attrs"}) or _has_unknown_keys(
            attrs, {"language"}
        ):
            return _marker(node, unsupported)
        code_nodes = _content(node, "code block")
        if any(
            not isinstance(child, dict)
            or child.get("type") != "text"
            or _has_unknown_keys(child, {"type", "text"})
            or not isinstance(child.get("text"), str)
            for child in code_nodes
        ):
            raise ValueError("Malformed draft body: invalid code block content")
        code = "".join(child["text"] for child in code_nodes)
        runs = [len(match.group(0)) for match in re.finditer(r"`+", code)]
        fence = "`" * max(3, (max(runs) + 1) if runs else 3)
        language = attrs.get("language") or ""
        if not isinstance(language, str) or "\n" in language:
            return _marker(node, unsupported)
        return f"{fence}{language}\n{code}\n{fence}"
    if node_type == "blockquote":
        if _has_unknown_keys(node, {"type", "content"}):
            return _marker(node, unsupported)
        body = "\n\n".join(
            _render_block(child, unsupported) for child in _content(node, "blockquote")
        )
        return "\n".join(">" if not line else f"> {line}" for line in body.splitlines())
    if node_type in {"bullet_list", "ordered_list"}:
        if _has_unknown_keys(node, {"type", "content"}):
            return _marker(node, unsupported)
        return _render_list(node, unsupported, ordered=node_type == "ordered_list")
    if node_type == "captionedImage":
        return _render_image(node, unsupported)
    if node_type == "footnote":
        return _render_footnote(node, unsupported)
    if node_type == "latex_block":
        attrs = _attrs(node, "math block")
        expression = attrs.get("persistentExpression", attrs.get("expression"))
        if (
            _has_unknown_keys(node, {"type", "attrs"})
            or _has_unknown_keys(attrs, {"persistentExpression", "expression", "dirty"})
            or not isinstance(expression, str)
        ):
            return _marker(node, unsupported)
        return f"$$\n{expression}\n$$"
    if node_type in {"pullquote", "calloutBlock"}:
        allowed = (
            {"type", "content", "attrs"}
            if node_type == "pullquote"
            else {"type", "content"}
        )
        if _has_unknown_keys(node, allowed):
            return _marker(node, unsupported)
        if node_type == "pullquote":
            attrs = _attrs(node, "pull quote")
            if _has_unknown_keys(attrs, {"align", "color"}) or any(
                attrs.get(key) is not None for key in ("align", "color")
            ):
                return _marker(node, unsupported)
        body = "\n\n".join(
            _render_block(child, unsupported) for child in _content(node, node_type)
        )
        name = "pullquote" if node_type == "pullquote" else "callout"
        return f"::: {name}\n{body}\n:::"
    raise AssertionError(node_type)


def document_to_markdown(document):
    _require_dict(document, "document")
    if document["type"] != "doc":
        raise ValueError("Malformed draft body: root node must have type 'doc'")
    if _has_unknown_keys(document, {"type", "content"}):
        raise ValueError("Malformed draft body: document has unsupported root fields")

    unsupported = []
    blocks = [
        _render_block(node, unsupported) for node in _content(document, "document")
    ]
    markdown = "\n\n".join(blocks)
    if markdown:
        markdown += "\n"
    return markdown, unsupported

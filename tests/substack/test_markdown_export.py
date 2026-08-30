import base64
import json
from pathlib import Path

import pytest

from substack.api import Api
from substack.mdexport import document_to_markdown
from substack.mdrender import markdown_to_doc
from substack.nodes import captioned_image
from substack.post import Post


def _text(value, marks=None):
    node = {"type": "text", "text": value}
    if marks:
        node["marks"] = marks
    return node


def _paragraph(value):
    return {"type": "paragraph", "content": [_text(value)]}


def test_document_to_markdown_golden_covers_supported_nodes():
    image = captioned_image(
        "https://example.com/image.png",
        alt="Alt text",
        href="https://example.com/target",
        caption=[_text("Caption")],
    )
    document = {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [_text("Heading", [{"type": "strong"}])],
            },
            {
                "type": "paragraph",
                "content": [
                    _text("Bold", [{"type": "strong"}]),
                    _text(" and "),
                    _text("italic", [{"type": "em"}]),
                    _text(" and "),
                    _text("code", [{"type": "code"}]),
                    _text(" and "),
                    _text("strike", [{"type": "strikethrough"}]),
                    _text(" and "),
                    _text("sup", [{"type": "superscript"}]),
                    _text(" and "),
                    _text("sub", [{"type": "subscript"}]),
                    _text(" and "),
                    _text(
                        "link",
                        [
                            {
                                "type": "link",
                                "attrs": {"href": "https://example.com"},
                            }
                        ],
                    ),
                    _text(" "),
                    {
                        "type": "latex",
                        "attrs": {
                            "expression": "E=mc^2",
                            "persistentExpression": "E=mc^2",
                        },
                    },
                    {"type": "footnoteAnchor", "attrs": {"number": 1}},
                ],
            },
            {
                "type": "bullet_list",
                "content": [
                    {
                        "type": "list_item",
                        "content": [
                            _paragraph("Bullet"),
                            {
                                "type": "ordered_list",
                                "content": [
                                    {
                                        "type": "list_item",
                                        "content": [_paragraph("Nested")],
                                    }
                                ],
                            },
                        ],
                    }
                ],
            },
            {
                "type": "blockquote",
                "content": [_paragraph("First"), _paragraph("Second")],
            },
            {
                "type": "codeBlock",
                "attrs": {"language": "python"},
                "content": [_text("print('ok')")],
            },
            {"type": "horizontal_rule"},
            {
                "type": "latex_block",
                "attrs": {"persistentExpression": "x^2", "dirty": True},
            },
            {
                "type": "pullquote",
                "attrs": {"align": None, "color": None},
                "content": [_paragraph("Pull")],
            },
            {"type": "calloutBlock", "content": [_paragraph("Callout")]},
            image,
            {
                "type": "footnote",
                "attrs": {"number": 1},
                "content": [_paragraph("Footnote")],
            },
        ],
    }

    markdown, unsupported = document_to_markdown(document)

    assert unsupported == []
    assert markdown == (
        "## **Heading**\n\n"
        "**Bold** and *italic* and `code` and ~~strike~~ and ^sup^ and ~sub~ "
        "and [link](https://example.com) $E=mc^2$[^1]\n\n"
        "- Bullet\n\n"
        "    1. Nested\n\n"
        "> First\n>\n> Second\n\n"
        "```python\nprint('ok')\n```\n\n"
        "---\n\n"
        "$$\nx^2\n$$\n\n"
        "::: pullquote\nPull\n:::\n\n"
        "::: callout\nCallout\n:::\n\n"
        '[![Alt text](https://example.com/image.png "Caption")]'
        "(https://example.com/target)\n\n"
        "[^1]: Footnote\n"
    )
    round_trip = markdown_to_doc(markdown)
    assert [node["type"] for node in round_trip] == [
        "heading",
        "paragraph",
        "bullet_list",
        "blockquote",
        "codeBlock",
        "horizontal_rule",
        "latex_block",
        "pullquote",
        "calloutBlock",
        "captionedImage",
        "footnote",
    ]


def test_full_feature_fixture_round_trips_exactly():
    fixture = Path(__file__).parent / "fixtures" / "full_features.md"
    post = Post("Feature complete", "", user_id=1)
    post.from_markdown(fixture.read_text(encoding="utf-8"))

    markdown, unsupported = document_to_markdown(post.draft_body)

    assert unsupported == []
    assert markdown_to_doc(markdown) == post.draft_body["content"]


def test_unsupported_node_is_visible_and_decodes_exactly():
    unknown = {
        "type": "futureWidget",
        "attrs": {"emoji": "\U0001f680", "nested": {"value": [1, None, "x"]}},
    }

    markdown, unsupported = document_to_markdown(
        {"type": "doc", "content": [_paragraph("Before"), unknown]}
    )

    marker = markdown.splitlines()[2]
    encoded = marker.removeprefix("<!-- python-substack-node:v1 ").removesuffix(" -->")
    decoded = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    assert json.loads(decoded.decode("utf-8")) == unknown
    assert unsupported == [unknown]


def test_unknown_attribute_preserves_the_entire_node_as_opaque():
    node = {"type": "paragraph", "content": [_text("Visible")], "future": True}

    markdown, unsupported = document_to_markdown({"type": "doc", "content": [node]})

    assert markdown.startswith("<!-- python-substack-node:v1 ")
    assert unsupported == [node]


@pytest.mark.parametrize(
    "document",
    [
        None,
        [],
        {},
        {"type": "paragraph", "content": []},
        {"type": "doc", "content": "not-a-list"},
        {"type": "doc", "content": [None]},
        {"type": "doc", "content": [{"type": "paragraph", "content": {}}]},
    ],
)
def test_malformed_documents_fail(document):
    with pytest.raises(ValueError, match="Malformed draft body"):
        document_to_markdown(document)


def test_api_export_fetches_once_and_performs_no_writes(monkeypatch):
    api = Api.__new__(Api)
    draft = {
        "id": 42,
        "draft_body": json.dumps({"type": "doc", "content": [_paragraph("Read only")]}),
    }
    calls = []

    def get_draft(draft_id):
        calls.append(draft_id)
        return draft

    monkeypatch.setattr(api, "get_draft", get_draft)

    assert api.export_draft_to_markdown(42) == {
        "draft": draft,
        "markdown": "Read only\n",
        "unsupported_nodes": [],
    }
    assert calls == [42]


@pytest.mark.parametrize("draft_body", [None, "not json", "[]"])
def test_api_export_rejects_malformed_draft_body(monkeypatch, draft_body):
    api = Api.__new__(Api)
    monkeypatch.setattr(api, "get_draft", lambda draft_id: {"draft_body": draft_body})

    with pytest.raises(ValueError, match="Malformed draft body"):
        api.export_draft_to_markdown(42)

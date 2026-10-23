"""Style precedence through the public Markdown import and export paths."""

import pytest

from substack.mdexport import document_to_markdown
from substack.mdrender import markdown_to_doc
from substack.post import Post


def render(markdown):
    post = Post("T", "", user_id=1)
    post.from_markdown(markdown)
    return post.draft_body


def marks_for(document, text):
    node = next(n for n in document["content"][0]["content"] if n["text"] == text)
    return node.get("marks", [])


@pytest.mark.parametrize(
    ("property_name", "mark_type"),
    [("color", "textStyle"), ("background-color", "highlight")],
)
@pytest.mark.parametrize(
    "declarations",
    [
        "{prop}:red; {prop}:blue",
        "{prop}:red; {prop}:green; {prop}:blue",
        "{prop}:red; {prop}:; font-weight:bold; {prop}:blue; {prop}:",
        "{prop}:red; {prop_upper} : blue",
    ],
)
def test_last_nonempty_style_declaration_wins(property_name, mark_type, declarations):
    style = declarations.format(prop=property_name, prop_upper=property_name.upper())
    document = render(f'[x]{{style="{style}"}}')
    assert marks_for(document, "x") == [{"type": mark_type, "attrs": {"color": "blue"}}]


@pytest.mark.parametrize(
    ("property_name", "mark_type"),
    [("color", "textStyle"), ("background-color", "highlight")],
)
def test_nested_style_overrides_without_leaking_to_siblings(property_name, mark_type):
    document = render(
        f'[before [inner]{{style="{property_name}:red"}} after]'
        f'{{style="{property_name}:blue"}} outside'
    )
    for text in ("before ", " after"):
        assert marks_for(document, text) == [
            {"type": mark_type, "attrs": {"color": "blue"}}
        ]
    assert marks_for(document, "inner") == [
        {"type": mark_type, "attrs": {"color": "red"}}
    ]
    assert marks_for(document, " outside") == []


def test_nested_styles_preserve_other_marks_and_round_trip():
    document = render(
        "[before [**bold** and [link](https://example.com) and `code`]"
        '{style="color:green; color:red"} after]'
        '{style="color:blue; background-color:yellow"}'
    )
    expected_styles = {
        "textStyle": {"color": "red"},
        "highlight": {"color": "yellow"},
    }
    for text, extra_type in (("bold", "strong"), ("link", "link"), ("code", "code")):
        marks = marks_for(document, text)
        assert len(marks) == 3
        assert {
            m["type"]: m["attrs"] for m in marks if "attrs" in m and m["type"] != "link"
        } == expected_styles
        assert any(m["type"] == extra_type for m in marks)
    assert next(m for m in marks_for(document, "link") if m["type"] == "link")[
        "attrs"
    ] == {"href": "https://example.com"}

    markdown, unsupported = document_to_markdown(document)
    assert unsupported == []
    assert markdown_to_doc(markdown) == document["content"]


def test_three_levels_override_color_and_highlight_independently():
    document = render(
        '[outer [middle [inner]{style="color:red"} middle-end]'
        '{style="background-color:green"} outer-end]'
        '{style="color:blue; background-color:yellow"}'
    )
    for text, color, highlight in (
        ("outer ", "blue", "yellow"),
        ("middle ", "blue", "green"),
        ("inner", "red", "green"),
        (" middle-end", "blue", "green"),
        (" outer-end", "blue", "yellow"),
    ):
        marks = marks_for(document, text)
        assert len(marks) == 2
        assert {m["type"]: m["attrs"]["color"] for m in marks} == {
            "textStyle": color,
            "highlight": highlight,
        }


def test_unrecognized_or_empty_inner_styles_keep_inherited_styles():
    document = render(
        '[outer [inner]{style="color:; background-color:; font-weight:bold"}]'
        '{style="color:blue; background-color:yellow"}'
    )
    assert document["content"][0]["content"] == [
        {
            "type": "text",
            "text": "outer inner",
            "marks": [
                {"type": "textStyle", "attrs": {"color": "blue"}},
                {"type": "highlight", "attrs": {"color": "yellow"}},
            ],
        }
    ]

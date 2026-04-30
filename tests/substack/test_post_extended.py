"""Tests for extended post.py -- inline code, ordered lists, horizontal rules, bold+italic, strikethrough."""

import json

import pytest
from substack.post import Post, parse_inline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_post():
    """Create a fresh Post instance for testing."""
    return Post(title="Test", subtitle="Sub", user_id=1)


def body_content(post):
    """Return the content list from the post's draft body."""
    return post.draft_body["content"]


# ---------------------------------------------------------------------------
# TestParseInlineCode
# ---------------------------------------------------------------------------

class TestParseInlineCode:
    def test_inline_code_basic(self):
        tokens = parse_inline("`code`")
        assert len(tokens) == 1
        assert tokens[0]["content"] == "code"
        assert tokens[0]["marks"] == [{"type": "code"}]

    def test_inline_code_in_sentence(self):
        tokens = parse_inline("Use `foo()` here")
        assert len(tokens) == 3
        assert tokens[0] == {"content": "Use "}
        assert tokens[1] == {"content": "foo()", "marks": [{"type": "code"}]}
        assert tokens[2] == {"content": " here"}

    def test_inline_code_preserves_special_chars(self):
        tokens = parse_inline("`**not bold**`")
        assert len(tokens) == 1
        assert tokens[0]["content"] == "**not bold**"
        assert tokens[0]["marks"] == [{"type": "code"}]

    def test_inline_code_multiple(self):
        tokens = parse_inline("`a` and `b`")
        assert len(tokens) == 3
        assert tokens[0] == {"content": "a", "marks": [{"type": "code"}]}
        assert tokens[1] == {"content": " and "}
        assert tokens[2] == {"content": "b", "marks": [{"type": "code"}]}

    def test_inline_code_empty_backticks(self):
        tokens = parse_inline("``")
        # Empty backticks should not match the code pattern
        assert len(tokens) == 1
        assert tokens[0] == {"content": "``"}


# ---------------------------------------------------------------------------
# TestParseInlineBoldItalic
# ---------------------------------------------------------------------------

class TestParseInlineBoldItalic:
    def test_bold_italic_combo(self):
        tokens = parse_inline("***text***")
        assert len(tokens) == 1
        assert tokens[0]["content"] == "text"
        assert {"type": "strong"} in tokens[0]["marks"]
        assert {"type": "em"} in tokens[0]["marks"]

    def test_bold_italic_in_sentence(self):
        tokens = parse_inline("This is ***important*** stuff")
        assert len(tokens) == 3
        assert tokens[0] == {"content": "This is "}
        assert tokens[1]["content"] == "important"
        assert {"type": "strong"} in tokens[1]["marks"]
        assert {"type": "em"} in tokens[1]["marks"]
        assert tokens[2] == {"content": " stuff"}

    def test_bold_italic_does_not_break_bold(self):
        tokens = parse_inline("**bold** and ***both***")
        assert len(tokens) == 3
        assert tokens[0]["content"] == "bold"
        assert tokens[0]["marks"] == [{"type": "strong"}]
        assert tokens[2]["content"] == "both"
        assert {"type": "strong"} in tokens[2]["marks"]
        assert {"type": "em"} in tokens[2]["marks"]

    def test_bold_italic_does_not_break_italic(self):
        tokens = parse_inline("*italic* and ***both***")
        assert len(tokens) == 3
        assert tokens[0]["content"] == "italic"
        assert tokens[0]["marks"] == [{"type": "em"}]
        assert tokens[2]["content"] == "both"
        assert {"type": "strong"} in tokens[2]["marks"]
        assert {"type": "em"} in tokens[2]["marks"]


# ---------------------------------------------------------------------------
# TestParseInlineStrikethrough
# ---------------------------------------------------------------------------

class TestParseInlineStrikethrough:
    def test_strikethrough_basic(self):
        tokens = parse_inline("~~struck~~")
        assert len(tokens) == 1
        assert tokens[0]["content"] == "struck"
        assert tokens[0]["marks"] == [{"type": "strikethrough"}]

    def test_strikethrough_in_sentence(self):
        tokens = parse_inline("This is ~~wrong~~ right")
        assert len(tokens) == 3
        assert tokens[0] == {"content": "This is "}
        assert tokens[1] == {"content": "wrong", "marks": [{"type": "strikethrough"}]}
        assert tokens[2] == {"content": " right"}

    def test_strikethrough_with_other_marks(self):
        tokens = parse_inline("**bold** and ~~struck~~")
        assert len(tokens) == 3
        assert tokens[0]["marks"] == [{"type": "strong"}]
        assert tokens[2]["marks"] == [{"type": "strikethrough"}]


# ---------------------------------------------------------------------------
# TestOrderedListFromMarkdown
# ---------------------------------------------------------------------------

class TestOrderedListFromMarkdown:
    def test_basic_ordered_list(self):
        post = make_post()
        post.from_markdown("1. a\n2. b\n3. c")
        content = body_content(post)
        assert len(content) == 1
        ol = content[0]
        assert ol["type"] == "ordered_list"
        assert len(ol["content"]) == 3
        for item in ol["content"]:
            assert item["type"] == "list_item"

    def test_ordered_list_with_inline_formatting(self):
        post = make_post()
        post.from_markdown("1. **bold item**\n2. normal")
        content = body_content(post)
        ol = content[0]
        first_item_tokens = ol["content"][0]["content"][0]["content"]
        assert any(
            t.get("marks") == [{"type": "strong"}]
            for t in first_item_tokens
        )

    def test_ordered_list_single_item(self):
        post = make_post()
        post.from_markdown("1. only")
        content = body_content(post)
        assert len(content) == 1
        assert content[0]["type"] == "ordered_list"
        assert len(content[0]["content"]) == 1

    def test_mixed_list_types(self):
        post = make_post()
        post.from_markdown("- bullet a\n- bullet b\n\n1. ordered a\n2. ordered b")
        content = body_content(post)
        types = [node["type"] for node in content]
        assert "bullet_list" in types
        assert "ordered_list" in types

    def test_ordered_list_non_sequential_numbers(self):
        post = make_post()
        post.from_markdown("1. a\n5. b\n3. c")
        content = body_content(post)
        ol = content[0]
        assert ol["type"] == "ordered_list"
        assert len(ol["content"]) == 3

    def test_ordered_list_with_links(self):
        post = make_post()
        post.from_markdown("1. [link](https://example.com)\n2. plain")
        content = body_content(post)
        ol = content[0]
        first_item_tokens = ol["content"][0]["content"][0]["content"]
        assert any(
            any(m.get("type") == "link" for m in t.get("marks", []))
            for t in first_item_tokens
        )

    def test_single_line_ordered_item(self):
        """A single ordered list item as its own block (no newlines in block)."""
        post = make_post()
        # Surround with blank lines so it's its own block
        post.from_markdown("\n1. item\n")
        content = body_content(post)
        assert any(node["type"] == "ordered_list" for node in content)


# ---------------------------------------------------------------------------
# TestHorizontalRuleFromMarkdown
# ---------------------------------------------------------------------------

class TestHorizontalRuleFromMarkdown:
    def test_horizontal_rule_dashes(self):
        post = make_post()
        post.from_markdown("text\n\n---\n\nmore text")
        content = body_content(post)
        types = [node["type"] for node in content]
        assert "horizontal_rule" in types

    def test_horizontal_rule_asterisks(self):
        post = make_post()
        post.from_markdown("text\n\n***\n\nmore text")
        content = body_content(post)
        types = [node["type"] for node in content]
        assert "horizontal_rule" in types

    def test_horizontal_rule_underscores(self):
        post = make_post()
        post.from_markdown("text\n\n___\n\nmore text")
        content = body_content(post)
        types = [node["type"] for node in content]
        assert "horizontal_rule" in types

    def test_horizontal_rule_extended(self):
        post = make_post()
        post.from_markdown("text\n\n-----\n\nmore text")
        content = body_content(post)
        types = [node["type"] for node in content]
        assert "horizontal_rule" in types

    def test_horizontal_rule_between_paragraphs(self):
        post = make_post()
        post.from_markdown("above\n\n---\n\nbelow")
        content = body_content(post)
        assert len(content) == 3
        assert content[0]["type"] == "paragraph"
        assert content[1]["type"] == "horizontal_rule"
        assert content[2]["type"] == "paragraph"

    def test_horizontal_rule_not_in_code_block(self):
        post = make_post()
        post.from_markdown("```\n---\n```")
        content = body_content(post)
        types = [node["type"] for node in content]
        assert "horizontal_rule" not in types
        assert "codeBlock" in types


# ---------------------------------------------------------------------------
# TestExistingFeaturesUnchanged
# ---------------------------------------------------------------------------

class TestExistingFeaturesUnchanged:
    def test_bold(self):
        tokens = parse_inline("**bold**")
        assert len(tokens) == 1
        assert tokens[0]["content"] == "bold"
        assert tokens[0]["marks"] == [{"type": "strong"}]

    def test_italic(self):
        tokens = parse_inline("*italic*")
        assert len(tokens) == 1
        assert tokens[0]["content"] == "italic"
        assert tokens[0]["marks"] == [{"type": "em"}]

    def test_links(self):
        tokens = parse_inline("[text](https://example.com)")
        assert len(tokens) == 1
        assert tokens[0]["content"] == "text"
        assert tokens[0]["marks"] == [{"type": "link", "attrs": {"href": "https://example.com"}}]

    def test_bullet_list(self):
        post = make_post()
        post.from_markdown("- a\n- b\n- c")
        content = body_content(post)
        assert len(content) == 1
        assert content[0]["type"] == "bullet_list"
        assert len(content[0]["content"]) == 3

    def test_code_block(self):
        post = make_post()
        post.from_markdown("```python\nprint('hello')\n```")
        content = body_content(post)
        assert len(content) == 1
        assert content[0]["type"] == "codeBlock"

    def test_blockquote(self):
        post = make_post()
        post.from_markdown("> quote text")
        content = body_content(post)
        assert len(content) == 1
        assert content[0]["type"] == "blockquote"

    def test_heading(self):
        post = make_post()
        post.from_markdown("## Heading Two")
        content = body_content(post)
        assert len(content) == 1
        assert content[0]["type"] == "heading"
        assert content[0]["attrs"]["level"] == 2

    def test_image(self):
        post = make_post()
        post.from_markdown("![alt](https://example.com/img.png)")
        content = body_content(post)
        assert len(content) == 1
        assert content[0]["type"] == "captionedImage"

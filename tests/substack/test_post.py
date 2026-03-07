"""Tests for Post and parse_inline."""

import json

from substack.post import Post, parse_inline


class TestParseInline:
    """Tests for parse_inline link handling."""

    def test_link_at_start_of_text(self):
        """Links at position 0 should be parsed correctly."""
        result = parse_inline("[GPT](https://openai.com/)")
        assert len(result) == 1
        assert result[0]["content"] == "GPT"
        assert result[0]["marks"][0]["attrs"]["href"] == "https://openai.com/"

    def test_multiple_links_on_same_line(self):
        """All links on the same line should be parsed."""
        result = parse_inline(
            "[GPT](https://openai.com/) and [Claude](https://anthropic.com/)"
        )
        links = [r for r in result if r.get("marks")]
        assert len(links) == 2
        assert links[0]["content"] == "GPT"
        assert links[0]["marks"][0]["attrs"]["href"] == "https://openai.com/"
        assert links[1]["content"] == "Claude"
        assert links[1]["marks"][0]["attrs"]["href"] == "https://anthropic.com/"

    def test_image_not_parsed_as_link(self):
        """Image syntax ![alt](url) should not be parsed as a link."""
        result = parse_inline("![alt](https://example.com/img.png)")
        links = [r for r in result if r.get("marks")]
        assert len(links) == 0

    def test_link_mid_text(self):
        """Links in the middle of text should work."""
        result = parse_inline("Check [this](https://example.com) out")
        links = [r for r in result if r.get("marks")]
        assert len(links) == 1
        assert links[0]["marks"][0]["attrs"]["href"] == "https://example.com"


class TestPostMarks:
    """Tests for Post.marks() link href handling."""

    def test_marks_preserves_href_from_attrs(self):
        """marks() should read href from attrs when present."""
        post = Post(title="Test", subtitle="", user_id=1)
        post.from_markdown("[Example](https://example.com)")
        body = json.loads(post.get_draft()["draft_body"])
        # Find the link mark
        for block in body["content"]:
            for node in block.get("content", []):
                for mark in node.get("marks", []):
                    if mark.get("type") == "link":
                        assert mark["attrs"]["href"] == "https://example.com"
                        return
        raise AssertionError("No link mark found in output")

    def test_marks_preserves_href_from_top_level(self):
        """marks() should also work when href is at top level (legacy format)."""
        post = Post(title="Test", subtitle="", user_id=1)
        post.add(
            {
                "type": "paragraph",
                "content": [
                    {
                        "content": "Link",
                        "marks": [{"type": "link", "href": "https://example.com"}],
                    }
                ],
            }
        )
        body = json.loads(post.get_draft()["draft_body"])
        for block in body["content"]:
            for node in block.get("content", []):
                for mark in node.get("marks", []):
                    if mark.get("type") == "link":
                        assert mark["attrs"]["href"] == "https://example.com"
                        return
        raise AssertionError("No link mark found in output")

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


class TestBlockquoteFromMarkdown:
    """Tests for blockquote parsing in from_markdown()."""

    def test_single_blockquote_line(self):
        """A single '> text' line produces a blockquote with one paragraph."""
        post = Post(title="T", subtitle="S", user_id=1)
        post.from_markdown("> This is a quote")
        body = json.loads(post.get_draft()["draft_body"])
        bq = body["content"][0]
        assert bq["type"] == "blockquote"
        assert len(bq["content"]) == 1
        assert bq["content"][0]["type"] == "paragraph"
        assert bq["content"][0]["content"][0]["text"] == "This is a quote"

    def test_multiline_blockquote_grouped(self):
        """Consecutive '>' lines become a single blockquote with multiple paragraphs."""
        post = Post(title="T", subtitle="S", user_id=1)
        post.from_markdown("> Line one\n> Line two\n> Line three")
        body = json.loads(post.get_draft()["draft_body"])
        bq = body["content"][0]
        assert bq["type"] == "blockquote"
        assert len(bq["content"]) == 3
        texts = [p["content"][0]["text"] for p in bq["content"]]
        assert texts == ["Line one", "Line two", "Line three"]

    def test_blockquote_separated_by_blank_line(self):
        """A blank line between '>' groups creates two separate blockquotes."""
        post = Post(title="T", subtitle="S", user_id=1)
        post.from_markdown("> First block\n\n> Second block")
        body = json.loads(post.get_draft()["draft_body"])
        blockquotes = [n for n in body["content"] if n["type"] == "blockquote"]
        assert len(blockquotes) == 2

    def test_blockquote_then_paragraph(self):
        """A blockquote followed by a regular paragraph produces both node types."""
        post = Post(title="T", subtitle="S", user_id=1)
        post.from_markdown("> A quote\n\nA regular paragraph")
        body = json.loads(post.get_draft()["draft_body"])
        assert body["content"][0]["type"] == "blockquote"
        assert body["content"][1]["type"] == "paragraph"

    def test_paragraph_blockquote_paragraph(self):
        """Blockquote sandwiched between paragraphs preserves order."""
        post = Post(title="T", subtitle="S", user_id=1)
        post.from_markdown("Before\n\n> The quote\n\nAfter")
        body = json.loads(post.get_draft()["draft_body"])
        types = [n["type"] for n in body["content"]]
        assert types == ["paragraph", "blockquote", "paragraph"]

    def test_blockquote_with_inline_link(self):
        """Links inside blockquotes are parsed as marks."""
        post = Post(title="T", subtitle="S", user_id=1)
        post.from_markdown("> See [example](https://example.com)")
        body = json.loads(post.get_draft()["draft_body"])
        bq = body["content"][0]
        assert bq["type"] == "blockquote"
        para = bq["content"][0]
        assert para["type"] == "paragraph"

    def test_blockquote_adjacent_to_bullet_list(self):
        """Blockquote followed immediately by bullets flushes correctly."""
        post = Post(title="T", subtitle="S", user_id=1)
        post.from_markdown("> A quote\n- bullet one\n- bullet two")
        body = json.loads(post.get_draft()["draft_body"])
        types = [n["type"] for n in body["content"]]
        assert types == ["blockquote", "bullet_list"]

    def test_empty_continuation_line(self):
        """A bare '>' between quoted lines keeps them in one blockquote."""
        post = Post(title="T", subtitle="S", user_id=1)
        post.from_markdown("> First\n>\n> Third")
        body = json.loads(post.get_draft()["draft_body"])
        blockquotes = [n for n in body["content"] if n["type"] == "blockquote"]
        assert len(blockquotes) == 1
        paras_with_content = [p for p in blockquotes[0]["content"] if p.get("content")]
        assert len(paras_with_content) == 2


class TestBlockquoteMethod:
    """Tests for the Post.blockquote() convenience method."""

    def test_blockquote_string(self):
        """blockquote('text') wraps text in a blockquote node."""
        post = Post(title="T", subtitle="S", user_id=1)
        post.blockquote("Hello world")
        body = json.loads(post.get_draft()["draft_body"])
        bq = body["content"][0]
        assert bq["type"] == "blockquote"
        assert bq["content"][0]["content"][0]["text"] == "Hello world"

    def test_blockquote_chaining(self):
        """blockquote() returns self for method chaining."""
        post = Post(title="T", subtitle="S", user_id=1)
        result = post.blockquote("one").blockquote("two")
        assert result is post
        body = json.loads(post.get_draft()["draft_body"])
        blockquotes = [n for n in body["content"] if n["type"] == "blockquote"]
        assert len(blockquotes) == 2

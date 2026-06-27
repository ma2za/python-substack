"""Tests for Markdown footnote support in post.py."""

from substack.post import Post


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_post():
    """Create a fresh Post instance for testing."""
    return Post(title="Test", subtitle="Sub", user_id=1)


def body_content(post):
    """Return the content list from the post's draft body."""
    return post.draft_body["content"]


def find_nodes(node, node_type, acc=None):
    """Recursively collect every node of a given type from a doc tree."""
    if acc is None:
        acc = []
    if isinstance(node, dict):
        if node.get("type") == node_type:
            acc.append(node)
        for value in node.values():
            find_nodes(value, node_type, acc)
    elif isinstance(node, list):
        for value in node:
            find_nodes(value, node_type, acc)
    return acc


def anchors(post):
    return find_nodes(post.draft_body, "footnoteAnchor")


def footnotes(post):
    return find_nodes(post.draft_body, "footnote")


# ---------------------------------------------------------------------------
# TestFootnoteHelpers
# ---------------------------------------------------------------------------

class TestFootnoteHelpers:
    def test_footnote_anchor_added_inline(self):
        post = make_post()
        post.paragraph(content=[{"content": "See here."}])
        post.footnote_anchor(1)
        para = body_content(post)[0]
        assert para["content"][-1] == {"type": "footnoteAnchor", "attrs": {"number": 1}}

    def test_footnote_block_from_string(self):
        post = make_post()
        post.footnote(1, "A simple note.")
        block = body_content(post)[-1]
        assert block["type"] == "footnote"
        assert block["attrs"] == {"number": 1}
        assert block["content"][0]["type"] == "paragraph"
        assert block["content"][0]["content"][0]["text"] == "A simple note."

    def test_footnote_block_parses_inline_markdown(self):
        post = make_post()
        post.footnote(2, "See [the source](https://example.com).")
        block = footnotes(post)[0]
        text_nodes = block["content"][0]["content"]
        link_node = next(n for n in text_nodes if n.get("marks"))
        assert link_node["text"] == "the source"
        assert link_node["marks"] == [{"type": "link", "attrs": {"href": "https://example.com"}}]


# ---------------------------------------------------------------------------
# TestFromMarkdownFootnotes
# ---------------------------------------------------------------------------

class TestFromMarkdownFootnotes:
    def test_basic_reference_and_definition(self):
        post = make_post()
        post.from_markdown("A claim.[^1]\n\n[^1]: The supporting detail.")
        assert len(anchors(post)) == 1
        assert anchors(post)[0]["attrs"]["number"] == 1
        blocks = footnotes(post)
        assert len(blocks) == 1
        assert blocks[0]["attrs"]["number"] == 1
        assert blocks[0]["content"][0]["content"][0]["text"] == "The supporting detail."

    def test_definition_removed_from_body(self):
        post = make_post()
        post.from_markdown("A claim.[^1]\n\n[^1]: The note.")
        # The definition line must not leak into a paragraph.
        paragraphs = find_nodes(post.draft_body, "paragraph")
        body_text = " ".join(
            n.get("text", "")
            for p in paragraphs
            for n in p.get("content", [])
        )
        assert "[^1]:" not in body_text

    def test_anchor_injected_mid_sentence(self):
        post = make_post()
        post.from_markdown("Before[^1] and after.\n\n[^1]: Note.")
        para = find_nodes(post.draft_body, "paragraph")[0]
        types = [c["type"] for c in para["content"]]
        assert types == ["text", "footnoteAnchor", "text"]
        assert para["content"][0]["text"] == "Before"
        assert para["content"][2]["text"] == " and after."

    def test_named_labels_numbered_by_first_appearance(self):
        post = make_post()
        md = (
            "First[^book] then second[^study].\n\n"
            "[^study]: Second definition.\n"
            "[^book]: First definition.\n"
        )
        post.from_markdown(md)
        nums = [a["attrs"]["number"] for a in anchors(post)]
        assert nums == [1, 2]  # order of reference, not of definition
        blocks = sorted(footnotes(post), key=lambda b: b["attrs"]["number"])
        assert blocks[0]["content"][0]["content"][0]["text"] == "First definition."
        assert blocks[1]["content"][0]["content"][0]["text"] == "Second definition."

    def test_repeated_reference_reuses_number(self):
        post = make_post()
        post.from_markdown("One[^a] two[^a].\n\n[^a]: Note.")
        nums = [a["attrs"]["number"] for a in anchors(post)]
        assert nums == [1, 1]
        assert len(footnotes(post)) == 1

    def test_link_inside_definition_preserved(self):
        post = make_post()
        post.from_markdown("Claim.[^1]\n\n[^1]: See [docs](https://example.com).")
        block = footnotes(post)[0]
        link_node = next(
            n for n in block["content"][0]["content"] if n.get("marks")
        )
        assert link_node["marks"][0]["attrs"]["href"] == "https://example.com"

    def test_multiline_definition(self):
        post = make_post()
        md = "Claim.[^1]\n\n[^1]: First line\n    continued on the next line."
        post.from_markdown(md)
        text = footnotes(post)[0]["content"][0]["content"][0]["text"]
        assert text == "First line continued on the next line."

    def test_unreferenced_definition_still_appended(self):
        post = make_post()
        post.from_markdown("No references here.\n\n[^1]: Orphan note.")
        assert len(anchors(post)) == 0
        assert len(footnotes(post)) == 1

    def test_reference_without_definition_left_as_text(self):
        post = make_post()
        post.from_markdown("A dangling[^missing] reference.")
        assert len(anchors(post)) == 0
        assert len(footnotes(post)) == 0
        para = find_nodes(post.draft_body, "paragraph")[0]
        assert "[^missing]" in para["content"][0]["text"]

    def test_definition_in_middle_moves_to_end(self):
        post = make_post()
        md = (
            "First paragraph.[^1]\n\n"
            "[^1]: First footnote.\n\n"
            "Second paragraph."
        )
        post.from_markdown(md)

        types = [node["type"] for node in body_content(post)]
        # Both paragraphs come first; the footnote block is last regardless of
        # where the definition appeared in the source.
        assert types == ["paragraph", "paragraph", "footnote"]

        paragraphs = find_nodes(post.draft_body, "paragraph")
        assert paragraphs[0]["content"][0]["text"] == "First paragraph."
        # The definition line did not become a paragraph in the body.
        assert paragraphs[1]["content"][0]["text"] == "Second paragraph."

        assert len(anchors(post)) == 1
        block = footnotes(post)[0]
        assert block["content"][0]["content"][0]["text"] == "First footnote."

    def test_footnote_definition_inside_fenced_code_stays_code(self):
        post = make_post()
        post.from_markdown("```\n[^1]: not a footnote\n```")
        content = body_content(post)
        assert len(content) == 1
        assert content[0]["type"] == "codeBlock"
        assert content[0]["content"][0]["text"] == "[^1]: not a footnote"

    def test_footnote_reference_inside_fenced_code_stays_text(self):
        post = make_post()
        post.from_markdown("```\ncode [^1]\n```\n\n[^1]: note")
        content = body_content(post)
        assert content[0]["type"] == "codeBlock"
        assert content[0]["content"][0]["text"] == "code [^1]"

    def test_footnote_reference_inside_inline_code_stays_text(self):
        post = make_post()
        post.from_markdown("`code [^1]`\n\n[^1]: note")
        content = body_content(post)
        assert content[0]["type"] == "paragraph"
        assert content[0]["content"][0]["text"] == "code [^1]"
        assert content[0]["content"][0]["marks"] == [{"type": "code"}]

    def test_multiparagraph_definition(self):
        post = make_post()
        md = "Claim.[^1]\n\n[^1]: First para.\n\n    Second para."
        post.from_markdown(md)
        # The second paragraph must stay in the footnote, not leak into the body.
        assert [n["type"] for n in body_content(post)] == ["paragraph", "footnote"]
        block = footnotes(post)[0]
        assert len(block["content"]) == 2
        assert block["content"][0]["content"][0]["text"] == "First para."
        assert block["content"][1]["content"][0]["text"] == "Second para."

    def test_multiparagraph_definition_in_middle(self):
        post = make_post()
        md = (
            "First.[^1]\n\n"
            "[^1]: Note para one.\n\n"
            "    Note para two.\n\n"
            "Back to the body."
        )
        post.from_markdown(md)
        types = [n["type"] for n in body_content(post)]
        assert types == ["paragraph", "paragraph", "footnote"]
        assert body_content(post)[1]["content"][0]["text"] == "Back to the body."
        assert len(footnotes(post)[0]["content"]) == 2

    def test_footnote_helper_splits_paragraphs(self):
        post = make_post()
        post.footnote(1, "Para one.\n\nPara two.")
        block = footnotes(post)[0]
        assert len(block["content"]) == 2
        assert block["content"][1]["content"][0]["text"] == "Para two."

    def test_no_footnotes_is_unchanged(self):
        post = make_post()
        post.from_markdown("Just a plain paragraph.")
        assert len(anchors(post)) == 0
        assert len(footnotes(post)) == 0
        assert find_nodes(post.draft_body, "paragraph")[0]["content"][0]["text"] == (
            "Just a plain paragraph."
        )

"""End-to-end coverage of every feature listed in Post.from_markdown().

These exercise the renderer through from_markdown() (as opposed to the
parse_inline() unit tests), so they cover the actual Markdown -> Substack path.
"""

from substack.post import Post


def make_post():
    return Post(title="T", subtitle="S", user_id=1)


def body(post):
    return post.draft_body["content"]


def first_para_nodes(post):
    return body(post)[0]["content"]


def marked(nodes, text):
    """Return the marks on the text node with the given text."""
    node = next(n for n in nodes if n.get("text") == text)
    return node.get("marks", [])


class TestInlineFormatting:
    def test_bold(self):
        post = make_post()
        post.from_markdown("x **b** y")
        assert {"type": "strong"} in marked(first_para_nodes(post), "b")

    def test_italic(self):
        post = make_post()
        post.from_markdown("x *i* y")
        assert {"type": "em"} in marked(first_para_nodes(post), "i")

    def test_bold_italic(self):
        post = make_post()
        post.from_markdown("***bi***")
        marks = marked(first_para_nodes(post), "bi")
        assert {"type": "strong"} in marks
        assert {"type": "em"} in marks

    def test_inline_code(self):
        post = make_post()
        post.from_markdown("use `code` now")
        assert marked(first_para_nodes(post), "code") == [{"type": "code"}]

    def test_strikethrough(self):
        post = make_post()
        post.from_markdown("a ~~s~~ b")
        assert marked(first_para_nodes(post), "s") == [{"type": "strikethrough"}]

    def test_link(self):
        post = make_post()
        post.from_markdown("[t](https://e.com)")
        assert marked(first_para_nodes(post), "t") == [
            {"type": "link", "attrs": {"href": "https://e.com"}}
        ]

    def test_multiple_marks_in_one_paragraph(self):
        post = make_post()
        post.from_markdown("**b** and *i* and `c` and [l](https://e.com)")
        nodes = first_para_nodes(post)
        assert {"type": "strong"} in marked(nodes, "b")
        assert {"type": "em"} in marked(nodes, "i")
        assert marked(nodes, "c") == [{"type": "code"}]
        assert marked(nodes, "l")[0]["type"] == "link"


class TestBlocks:
    def test_all_heading_levels(self):
        for level in range(1, 7):
            post = make_post()
            post.from_markdown("#" * level + " Heading")
            block = body(post)[0]
            assert block["type"] == "heading"
            assert block["attrs"]["level"] == level

    def test_paragraph(self):
        post = make_post()
        post.from_markdown("Just a plain paragraph.")
        block = body(post)[0]
        assert block["type"] == "paragraph"
        assert block["content"][0]["text"] == "Just a plain paragraph."

    def test_bullet_list(self):
        post = make_post()
        post.from_markdown("- a\n- b")
        block = body(post)[0]
        assert block["type"] == "bullet_list"
        assert len(block["content"]) == 2
        assert block["content"][0]["type"] == "list_item"

    def test_ordered_list(self):
        post = make_post()
        post.from_markdown("1. a\n2. b")
        block = body(post)[0]
        assert block["type"] == "ordered_list"
        assert len(block["content"]) == 2

    def test_code_block_with_language(self):
        post = make_post()
        post.from_markdown("```python\nprint('hi')\n```")
        block = body(post)[0]
        assert block["type"] == "codeBlock"
        assert block["attrs"]["language"] == "python"
        assert block["content"][0]["text"] == "print('hi')"

    def test_code_block_without_language(self):
        post = make_post()
        post.from_markdown("```\nplain\n```")
        block = body(post)[0]
        assert block["type"] == "codeBlock"
        assert "attrs" not in block or "language" not in block.get("attrs", {})

    def test_horizontal_rule(self):
        post = make_post()
        post.from_markdown("a\n\n---\n\nb")
        assert [n["type"] for n in body(post)] == ["paragraph", "horizontal_rule", "paragraph"]

    def test_blockquote(self):
        post = make_post()
        post.from_markdown("> quote")
        block = body(post)[0]
        assert block["type"] == "blockquote"
        assert block["content"][0]["type"] == "paragraph"

    def test_image(self):
        post = make_post()
        post.from_markdown("![alt](https://example.com/img.png)")
        block = body(post)[0]
        assert block["type"] == "captionedImage"
        assert len(block["content"]) == 1
        assert block["content"][0]["type"] == "image2"
        attrs = block["content"][0]["attrs"]
        assert attrs["src"] == "https://example.com/img.png"
        assert attrs["alt"] == "alt"
        assert attrs["href"] is None
        assert attrs["imageSize"] == "normal"
        assert attrs["srcNoWatermark"] is None
        assert attrs["topImage"] is False
        assert attrs["isProcessing"] is False
        assert attrs["align"] is None
        assert attrs["offset"] is False

    def test_image_with_caption(self):
        post = make_post()
        post.from_markdown('![alt](https://example.com/img.png "My caption")')
        block = body(post)[0]
        assert block["type"] == "captionedImage"
        assert len(block["content"]) == 2
        assert block["content"][0]["type"] == "image2"
        assert block["content"][0]["attrs"]["alt"] == "alt"
        caption = block["content"][1]
        assert caption["type"] == "caption"
        assert caption["content"] == [{"type": "text", "text": "My caption"}]

    def test_image_without_caption_has_no_caption_node(self):
        post = make_post()
        post.from_markdown("![alt](https://example.com/img.png)")
        block = body(post)[0]
        types = [n["type"] for n in block["content"]]
        assert "caption" not in types

    def test_linked_image(self):
        post = make_post()
        post.from_markdown("[![alt](https://i/x.png)](https://link)")
        block = body(post)[0]
        assert block["type"] == "captionedImage"
        assert block["content"][0]["type"] == "image2"
        attrs = block["content"][0]["attrs"]
        assert attrs["src"] == "https://i/x.png"
        assert attrs["href"] == "https://link"

    def test_latex_block(self):
        post = make_post()
        post.from_markdown("$$\nE=mc^2\n$$\n")
        block = body(post)[0]
        assert block["type"] == "latex_block"
        assert block["attrs"]["persistentExpression"] == "E=mc^2"
        assert block["attrs"]["dirty"] is True

    def test_latex_inline(self):
        post = make_post()
        post.from_markdown("A paragraph with $E=mc^2$ inline.")
        para = body(post)[0]
        assert para["type"] == "paragraph"
        latex = [n for n in para["content"] if n["type"] == "latex"]
        assert len(latex) == 1
        assert latex[0]["attrs"]["expression"] == "E=mc^2"
        assert latex[0]["attrs"]["persistentExpression"] == "E=mc^2"

    def test_superscript(self):
        post = make_post()
        post.from_markdown("E=mc^2^ here.")
        para = body(post)[0]
        sup = [n for n in para["content"] if n.get("marks")]
        assert sup[0]["text"] == "2"
        assert sup[0]["marks"] == [{"type": "superscript"}]

    def test_subscript(self):
        post = make_post()
        post.from_markdown("H~2~O here.")
        para = body(post)[0]
        sub = [n for n in para["content"] if n.get("marks")]
        assert sub[0]["text"] == "2"
        assert sub[0]["marks"] == [{"type": "subscript"}]

    def test_subscript_does_not_clash_with_strikethrough(self):
        post = make_post()
        post.from_markdown("~~struck~~ and H~2~O")
        para = body(post)[0]
        marks = {
            m["type"]
            for n in para["content"]
            for m in n.get("marks", [])
        }
        assert marks == {"strikethrough", "subscript"}

    def test_pullquote(self):
        post = make_post()
        post.from_markdown(":::pullquote\nA **bold** quote.\n:::\n")
        block = body(post)[0]
        assert block["type"] == "pullquote"
        assert block["attrs"] == {"align": None, "color": None}
        para = block["content"][0]
        assert para["type"] == "paragraph"
        assert para["content"][1]["text"] == "bold"
        assert para["content"][1]["marks"] == [{"type": "strong"}]

    def test_callout(self):
        post = make_post()
        post.from_markdown(":::callout\nA callout with a [link](https://example.com).\n:::\n")
        block = body(post)[0]
        assert block["type"] == "calloutBlock"
        para = block["content"][0]
        assert para["type"] == "paragraph"
        link = [n for n in para["content"] if n.get("marks")][0]
        assert link["marks"][0]["attrs"]["href"] == "https://example.com"

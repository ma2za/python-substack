import base64
import json
import re
from unittest.mock import Mock

import pytest

from substack.api import Api
from substack.mdexport import document_to_markdown
from substack.mdrender import markdown_to_doc, parse_image_marker
from substack.nodes import captioned_image, paragraph, text
from substack.post import Post


def _make_v2_marker(src: str, attrs: dict) -> str:
    payload = {"src": src, **attrs}
    data = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    encoded = base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")
    return f"<!-- python-substack-image:v2 {encoded} -->"


def _make_v1_marker(attrs: dict) -> str:
    data = json.dumps(
        attrs, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    encoded = base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")
    return f"<!-- python-substack-image:v1 {encoded} -->"


def test_document_to_markdown_exports_v2_image_marker():
    img = captioned_image(
        "https://example.com/photo.png",
        alt="Photo alt",
        caption=[text("Photo caption")],
    )
    # Customize some attributes
    img["content"][0]["attrs"]["imageSize"] = "wide"
    img["content"][0]["attrs"]["align"] = "center"
    img["content"][0]["attrs"]["fullscreen"] = True

    document = {"type": "doc", "content": [img]}
    markdown, unsupported = document_to_markdown(document)

    assert unsupported == []
    assert "python-substack-image:v2" in markdown
    assert "python-substack-image:v1" not in markdown

    # Extract marker payload
    match = re.search(r"<!-- python-substack-image:v2 ([A-Za-z0-9_-]+=*) -->", markdown)
    assert match is not None
    encoded = match.group(1)
    encoded += "=" * (-len(encoded) % 4)
    payload = json.loads(
        base64.urlsafe_b64decode(encoded.encode("ascii")).decode("utf-8")
    )

    assert payload["src"] == "https://example.com/photo.png"
    assert payload["imageSize"] == "wide"
    assert payload["align"] == "center"
    assert payload["fullscreen"] is True
    assert "alt" not in payload
    assert "href" not in payload
    assert "isProcessing" not in payload


def test_document_to_markdown_preserves_unknown_attributes_in_v2():
    img = captioned_image("https://example.com/photo.png")
    img["content"][0]["attrs"]["customEditorAttr"] = {"nested": [1, 2, 3]}
    img["content"][0]["attrs"]["watermarkVersion"] = 42

    document = {"type": "doc", "content": [img]}
    markdown, unsupported = document_to_markdown(document)

    assert unsupported == []
    match = re.search(r"<!-- python-substack-image:v2 ([A-Za-z0-9_-]+=*) -->", markdown)
    assert match is not None
    encoded = match.group(1)
    encoded += "=" * (-len(encoded) % 4)
    payload = json.loads(
        base64.urlsafe_b64decode(encoded.encode("ascii")).decode("utf-8")
    )

    assert payload["customEditorAttr"] == {"nested": [1, 2, 3]}
    assert payload["watermarkVersion"] == 42


def test_v2_changed_source_update(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    remote_img = captioned_image("https://substackcdn.com/original.png")["content"][0][
        "attrs"
    ]
    remote_img["imageSize"] = "wide"
    remote_img["align"] = "center"
    remote_img["fullscreen"] = True
    remote_img["height"] = 600
    remote_img["width"] = 1200
    remote_img["srcNoWatermark"] = "https://substackcdn.com/nowatermark.png"
    remote_img["unknownAttr"] = "preserved"

    remote_doc = {
        "type": "doc",
        "content": [
            {
                "type": "captionedImage",
                "content": [{"type": "image2", "attrs": remote_img}],
            }
        ],
    }

    mock_get_draft = Mock(return_value={"id": 42, "draft_body": json.dumps(remote_doc)})
    monkeypatch.setattr(api, "get_draft", mock_get_draft)

    put_calls = []

    def mock_put_draft(draft_id, **kwargs):
        put_calls.append((draft_id, kwargs))
        return {"id": draft_id}

    monkeypatch.setattr(api, "put_draft", mock_put_draft)

    # User changes image in markdown to a new URL, new alt, new caption
    marker = _make_v2_marker(
        "https://substackcdn.com/original.png",
        {
            "imageSize": "wide",
            "align": "center",
            "fullscreen": True,
            "height": 600,
            "width": 1200,
            "srcNoWatermark": "https://substackcdn.com/nowatermark.png",
            "unknownAttr": "preserved",
        },
    )
    submitted_md = (
        f'![New Alt](https://substackcdn.com/replacement.png "New Caption")\n{marker}\n'
    )

    res = api.update_draft_from_markdown(
        42, submitted_md, allow_image_replacement=False
    )
    assert res["action"] == "update"
    assert len(put_calls) == 1

    saved_body = json.loads(put_calls[0][1]["draft_body"])
    saved_img = saved_body["content"][0]["content"][0]["attrs"]

    # Markdown authoritative for src and alt
    assert saved_img["src"] == "https://substackcdn.com/replacement.png"
    assert saved_img["alt"] == "New Alt"
    # Preserved editor attributes
    assert saved_img["imageSize"] == "wide"
    assert saved_img["align"] == "center"
    assert saved_img["fullscreen"] is True
    assert saved_img["height"] == 600
    assert saved_img["width"] == 1200
    assert saved_img["srcNoWatermark"] == "https://substackcdn.com/nowatermark.png"
    assert saved_img["unknownAttr"] == "preserved"
    assert saved_img["isProcessing"] is False


def test_v1_resolvable_update(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    remote_img = captioned_image("https://example.com/unique.png")["content"][0][
        "attrs"
    ]
    remote_img["imageSize"] = "wide"
    remote_doc = {
        "type": "doc",
        "content": [
            {
                "type": "captionedImage",
                "content": [{"type": "image2", "attrs": remote_img}],
            }
        ],
    }

    monkeypatch.setattr(
        api,
        "get_draft",
        Mock(return_value={"id": 42, "draft_body": json.dumps(remote_doc)}),
    )
    put_calls = []
    monkeypatch.setattr(
        api,
        "put_draft",
        lambda d_id, **kw: put_calls.append((d_id, kw)) or {"id": d_id},
    )

    # V1 marker with identical src
    v1_marker = _make_v1_marker({"imageSize": "wide"})
    submitted_md = f"![Alt](https://example.com/unique.png)\n{v1_marker}\n"

    res = api.update_draft_from_markdown(
        42, submitted_md, allow_image_replacement=False
    )
    assert res["action"] == "update"
    assert len(put_calls) == 1
    saved_body = json.loads(put_calls[0][1]["draft_body"])
    saved_img = saved_body["content"][0]["content"][0]["attrs"]
    assert saved_img["src"] == "https://example.com/unique.png"
    assert saved_img["imageSize"] == "wide"


def test_v1_ambiguous_update_rejected(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    # 2 remote images with identical URLs
    remote_img1 = captioned_image("https://example.com/dup.png")["content"][0]["attrs"]
    remote_img2 = captioned_image("https://example.com/dup.png")["content"][0]["attrs"]
    remote_doc = {
        "type": "doc",
        "content": [
            {
                "type": "captionedImage",
                "content": [{"type": "image2", "attrs": remote_img1}],
            },
            {
                "type": "captionedImage",
                "content": [{"type": "image2", "attrs": remote_img2}],
            },
        ],
    }
    monkeypatch.setattr(
        api,
        "get_draft",
        Mock(return_value={"id": 42, "draft_body": json.dumps(remote_doc)}),
    )
    monkeypatch.setattr(api, "put_draft", Mock())

    # V1 marker submitted
    v1_marker = _make_v1_marker({"imageSize": "wide"})
    submitted_md = f"![Alt](https://example.com/dup.png)\n{v1_marker}\n"

    with pytest.raises(ValueError, match="cannot be matched uniquely"):
        api.update_draft_from_markdown(42, submitted_md, allow_image_replacement=False)

    # Succeeds with allow_image_replacement=True
    res = api.update_draft_from_markdown(42, submitted_md, allow_image_replacement=True)
    assert res["action"] == "update"


def test_v1_changed_source_rejected(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    remote_img = captioned_image("https://example.com/original.png")["content"][0][
        "attrs"
    ]
    remote_doc = {
        "type": "doc",
        "content": [
            {
                "type": "captionedImage",
                "content": [{"type": "image2", "attrs": remote_img}],
            }
        ],
    }
    monkeypatch.setattr(
        api,
        "get_draft",
        Mock(return_value={"id": 42, "draft_body": json.dumps(remote_doc)}),
    )
    monkeypatch.setattr(api, "put_draft", Mock())

    # V1 marker with changed source in markdown
    v1_marker = _make_v1_marker({"imageSize": "wide"})
    submitted_md = f"![Alt](https://example.com/changed.png)\n{v1_marker}\n"

    with pytest.raises(
        ValueError, match="cannot be matched uniquely|cannot authorize changed source"
    ):
        api.update_draft_from_markdown(42, submitted_md, allow_image_replacement=False)

    res = api.update_draft_from_markdown(42, submitted_md, allow_image_replacement=True)
    assert res["action"] == "update"


def test_duplicate_remote_urls_with_v2(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    remote_img1 = captioned_image("https://example.com/dup.png")["content"][0]["attrs"]
    remote_img1["imageSize"] = "wide"
    remote_img1["align"] = "center"

    remote_img2 = captioned_image("https://example.com/dup.png")["content"][0]["attrs"]
    remote_img2["imageSize"] = "normal"
    remote_img2["align"] = "left"

    remote_doc = {
        "type": "doc",
        "content": [
            {
                "type": "captionedImage",
                "content": [{"type": "image2", "attrs": remote_img1}],
            },
            {
                "type": "captionedImage",
                "content": [{"type": "image2", "attrs": remote_img2}],
            },
        ],
    }
    monkeypatch.setattr(
        api,
        "get_draft",
        Mock(return_value={"id": 42, "draft_body": json.dumps(remote_doc)}),
    )

    put_calls = []
    monkeypatch.setattr(
        api,
        "put_draft",
        lambda d_id, **kw: put_calls.append((d_id, kw)) or {"id": d_id},
    )

    # Two V2 markers each bound to https://example.com/dup.png
    m1 = _make_v2_marker(
        "https://example.com/dup.png", {"imageSize": "wide", "align": "center"}
    )
    m2 = _make_v2_marker(
        "https://example.com/dup.png", {"imageSize": "normal", "align": "left"}
    )

    submitted_md = f"![First](https://example.com/dup.png)\n{m1}\n\n![Second](https://example.com/dup.png)\n{m2}\n"

    res = api.update_draft_from_markdown(
        42, submitted_md, allow_image_replacement=False
    )
    assert res["action"] == "update"

    saved_body = json.loads(put_calls[0][1]["draft_body"])
    saved_img1 = saved_body["content"][0]["content"][0]["attrs"]
    saved_img2 = saved_body["content"][1]["content"][0]["attrs"]

    assert saved_img1["imageSize"] == "wide"
    assert saved_img1["align"] == "center"
    assert saved_img2["imageSize"] == "normal"
    assert saved_img2["align"] == "left"


def test_v2_marker_reuse_rejected(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    remote_img = captioned_image("https://example.com/single.png")["content"][0][
        "attrs"
    ]
    remote_doc = {
        "type": "doc",
        "content": [
            {
                "type": "captionedImage",
                "content": [{"type": "image2", "attrs": remote_img}],
            }
        ],
    }
    monkeypatch.setattr(
        api,
        "get_draft",
        Mock(return_value={"id": 42, "draft_body": json.dumps(remote_doc)}),
    )
    monkeypatch.setattr(api, "put_draft", Mock())

    # Two images in markdown reusing the marker bound to the single remote image
    m = _make_v2_marker("https://example.com/single.png", {"imageSize": "wide"})
    submitted_md = f"![First](https://example.com/single.png)\n{m}\n\n![Second](https://example.com/other.png)\n{m}\n"

    with pytest.raises(ValueError, match="reused or duplicate image marker"):
        api.update_draft_from_markdown(42, submitted_md, allow_image_replacement=False)


def test_v2_stale_marker_rejected(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    remote_img = captioned_image("https://example.com/actual.png")["content"][0][
        "attrs"
    ]
    remote_doc = {
        "type": "doc",
        "content": [
            {
                "type": "captionedImage",
                "content": [{"type": "image2", "attrs": remote_img}],
            }
        ],
    }
    monkeypatch.setattr(
        api,
        "get_draft",
        Mock(return_value={"id": 42, "draft_body": json.dumps(remote_doc)}),
    )
    monkeypatch.setattr(api, "put_draft", Mock())

    # Marker bound to a non-existent remote source
    m = _make_v2_marker("https://example.com/stale.png", {"imageSize": "wide"})
    submitted_md = f"![Photo](https://example.com/actual.png)\n{m}\n"

    with pytest.raises(ValueError, match="stale image marker"):
        api.update_draft_from_markdown(42, submitted_md, allow_image_replacement=False)


def test_corrupt_image_markers():
    # Corrupt base64
    with pytest.raises(ValueError, match="Corrupt image marker format"):
        markdown_to_doc("![Photo](url.png)\n<!-- python-substack-image:v2 @@@ -->\n")

    # Missing src in v2
    payload = json.dumps({"imageSize": "wide"}).encode("utf-8")
    enc = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    with pytest.raises(ValueError, match="Invalid image marker attributes"):
        markdown_to_doc(f"![Photo](url.png)\n<!-- python-substack-image:v2 {enc} -->\n")

    # Forbidden keys in v2 (alt, href, isProcessing)
    payload = json.dumps({"src": "url.png", "alt": "bad"}).encode("utf-8")
    enc = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    with pytest.raises(ValueError, match="Invalid image marker attributes"):
        markdown_to_doc(f"![Photo](url.png)\n<!-- python-substack-image:v2 {enc} -->\n")

    # Forbidden keys in v1 (src in v1)
    payload = json.dumps({"src": "url.png"}).encode("utf-8")
    enc = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    with pytest.raises(ValueError, match="Invalid image marker attributes"):
        markdown_to_doc(f"![Photo](url.png)\n<!-- python-substack-image:v1 {enc} -->\n")


def test_non_adjacent_image_markers():
    m = _make_v2_marker("https://example.com/img.png", {"imageSize": "wide"})

    # Marker before image / at document start
    with pytest.raises(
        ValueError, match="Image marker must immediately follow an image"
    ):
        markdown_to_doc(f"{m}\n\n![Photo](https://example.com/img.png)\n")

    # Marker after paragraph
    with pytest.raises(
        ValueError, match="Image marker must immediately follow an image"
    ):
        markdown_to_doc(f"Some text paragraph.\n\n{m}\n")

    # Marker after heading
    with pytest.raises(
        ValueError, match="Image marker must immediately follow an image"
    ):
        markdown_to_doc(f"# Heading\n\n{m}\n")

    # Two markers after one image
    with pytest.raises(
        ValueError, match="Image marker must immediately follow an image"
    ):
        markdown_to_doc(f"![Photo](https://example.com/img.png)\n{m}\n{m}\n")

    # Marker inlined inside text
    with pytest.raises(
        ValueError, match="Image marker must immediately follow an image"
    ):
        markdown_to_doc(f"Some text with {m} inline.\n")


def test_new_image_without_marker(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    remote_img = captioned_image("https://example.com/existing.png")["content"][0][
        "attrs"
    ]
    remote_doc = {
        "type": "doc",
        "content": [
            {
                "type": "captionedImage",
                "content": [{"type": "image2", "attrs": remote_img}],
            }
        ],
    }
    monkeypatch.setattr(
        api,
        "get_draft",
        Mock(return_value={"id": 42, "draft_body": json.dumps(remote_doc)}),
    )
    monkeypatch.setattr(api, "put_draft", Mock(return_value={"id": 42}))

    # Markdown has existing image with v2 marker + a brand new image without marker
    m = _make_v2_marker("https://example.com/existing.png", {"imageSize": "wide"})
    submitted_md = (
        f"![Existing](https://example.com/existing.png)\n{m}\n\n"
        f"![Brand New](https://example.com/brand_new.png)\n"
    )

    with pytest.raises(ValueError, match="cannot be matched uniquely"):
        api.update_draft_from_markdown(42, submitted_md, allow_image_replacement=False)

    # Allowed with allow_image_replacement=True
    res = api.update_draft_from_markdown(42, submitted_md, allow_image_replacement=True)
    assert res["action"] == "update"


def test_adversarial_unicode_bidi_and_special_characters(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    complex_url = "https://substackcdn.com/test%20image%F0%9F%9A%80.png?v=1&foo=bar#baz"
    bidi_alt = 'Bidi test \u202e\u0627\u0644\u0639\u0631\u0628\u064a\u0629\u202c [brackets] "quotes"'
    complex_attrs = {
        "align": "center",
        "custom_emoji": "🚀🔥✨",
        "nested": {"array": [1, None, False, {"deep": "utf-8 \u00e9\u00e8\u00e0"}]},
    }

    remote_img = captioned_image(complex_url)["content"][0]["attrs"]
    remote_img.update(complex_attrs)
    remote_doc = {
        "type": "doc",
        "content": [
            {
                "type": "captionedImage",
                "content": [{"type": "image2", "attrs": remote_img}],
            }
        ],
    }
    monkeypatch.setattr(
        api,
        "get_draft",
        Mock(return_value={"id": 42, "draft_body": json.dumps(remote_doc)}),
    )
    put_calls = []
    monkeypatch.setattr(
        api,
        "put_draft",
        lambda d_id, **kw: put_calls.append((d_id, kw)) or {"id": d_id},
    )

    # Export document to markdown
    md, unsupported = document_to_markdown(remote_doc)
    assert unsupported == []
    assert "python-substack-image:v2" in md

    # Round-trip update
    res = api.update_draft_from_markdown(42, md, allow_image_replacement=False)
    assert res["action"] == "update"
    saved = json.loads(put_calls[0][1]["draft_body"])
    saved_img = saved["content"][0]["content"][0]["attrs"]
    assert saved_img["custom_emoji"] == "🚀🔥✨"
    assert saved_img["nested"]["array"][3]["deep"] == "utf-8 \u00e9\u00e8\u00e0"


def test_adversarial_mixed_v1_and_v2_with_interleaved_blocks(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    img1_attrs = captioned_image("https://example.com/one.png")["content"][0]["attrs"]
    img1_attrs["imageSize"] = "wide"
    img2_attrs = captioned_image("https://example.com/two.png")["content"][0]["attrs"]
    img2_attrs["align"] = "center"

    remote_doc = {
        "type": "doc",
        "content": [
            {
                "type": "captionedImage",
                "content": [{"type": "image2", "attrs": img1_attrs}],
            },
            {
                "type": "captionedImage",
                "content": [{"type": "image2", "attrs": img2_attrs}],
            },
        ],
    }
    monkeypatch.setattr(
        api,
        "get_draft",
        Mock(return_value={"id": 42, "draft_body": json.dumps(remote_doc)}),
    )
    put_calls = []
    monkeypatch.setattr(
        api,
        "put_draft",
        lambda d_id, **kw: put_calls.append((d_id, kw)) or {"id": d_id},
    )

    # Image 1 uses V1 marker, Image 2 uses V2 marker with changed source, separated by code block and callout
    v1_m = _make_v1_marker({"imageSize": "wide"})
    v2_m = _make_v2_marker("https://example.com/two.png", {"align": "center"})

    submitted_md = f"""# Title

![Image 1](https://example.com/one.png)
{v1_m}

```python
print("interleaved code block")
```

::: callout
Interleaved callout
:::

![Image 2 replaced](https://example.com/two-replacement.png)
{v2_m}
"""

    res = api.update_draft_from_markdown(
        42, submitted_md, allow_image_replacement=False
    )
    assert res["action"] == "update"
    saved = json.loads(put_calls[0][1]["draft_body"])
    images = [
        node["content"][0]["attrs"]
        for node in saved["content"]
        if node["type"] == "captionedImage"
    ]
    assert len(images) == 2
    assert images[0]["src"] == "https://example.com/one.png"
    assert images[0]["imageSize"] == "wide"
    assert images[1]["src"] == "https://example.com/two-replacement.png"
    assert images[1]["align"] == "center"


def test_adversarial_3_duplicates_and_4th_reused_rejected(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    remote_doc = {
        "type": "doc",
        "content": [
            {
                "type": "captionedImage",
                "content": [
                    {
                        "type": "image2",
                        "attrs": {"src": "https://example.com/same.png", "idx": 1},
                    }
                ],
            },
            {
                "type": "captionedImage",
                "content": [
                    {
                        "type": "image2",
                        "attrs": {"src": "https://example.com/same.png", "idx": 2},
                    }
                ],
            },
            {
                "type": "captionedImage",
                "content": [
                    {
                        "type": "image2",
                        "attrs": {"src": "https://example.com/same.png", "idx": 3},
                    }
                ],
            },
        ],
    }
    monkeypatch.setattr(
        api,
        "get_draft",
        Mock(return_value={"id": 42, "draft_body": json.dumps(remote_doc)}),
    )
    monkeypatch.setattr(api, "put_draft", Mock())

    m = _make_v2_marker("https://example.com/same.png", {"imageSize": "normal"})
    # 4 images claiming the 3 remote images
    submitted_md = f"""
![1](https://example.com/same.png)
{m}

![2](https://example.com/same.png)
{m}

![3](https://example.com/same.png)
{m}

![4](https://example.com/same.png)
{m}
"""
    with pytest.raises(ValueError, match="reused or duplicate image marker"):
        api.update_draft_from_markdown(42, submitted_md, allow_image_replacement=False)

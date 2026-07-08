import json
from unittest.mock import Mock

from substack import Api


def make_api():
    api = object.__new__(Api)
    api.get_user_id = Mock(return_value=1)
    api.post_draft = Mock(return_value={"id": 123, "title": "Draft"})
    api.put_draft = Mock(return_value={"id": 123, "slug": "my-post"})
    api.add_tags_to_post = Mock(return_value={"tags_added": [{"id": 1}]})
    api.prepublish_draft = Mock(return_value={"ok": True})
    api.publish_draft = Mock(return_value={"published": True})
    return api


def test_create_draft_from_markdown_creates_draft_and_updates_metadata():
    api = make_api()

    result = api.create_draft_from_markdown(
        title="Title",
        subtitle="Subtitle",
        markdown="# Heading\n\nBody",
        slug="my-post",
        search_engine_title="SEO title",
        search_engine_description="SEO description",
        tags="python",
        prepublish=True,
        publish=True,
        send=False,
        share_automatically=True,
    )

    api.post_draft.assert_called_once()
    draft_payload = api.post_draft.call_args.args[0]
    draft_body = json.loads(draft_payload["draft_body"])
    assert draft_body["content"][0]["type"] == "heading"
    assert draft_body["content"][1]["type"] == "paragraph"

    api.put_draft.assert_called_once_with(
        123,
        search_engine_title="SEO title",
        search_engine_description="SEO description",
        slug="my-post",
    )
    api.add_tags_to_post.assert_called_once_with(123, ["python"])
    api.prepublish_draft.assert_called_once_with(123)
    api.publish_draft.assert_called_once_with(
        123,
        send=False,
        share_automatically=True,
    )
    assert result["draft"] == {"id": 123, "slug": "my-post"}
    assert result["tags"] == {"tags_added": [{"id": 1}]}


def test_create_draft_from_markdown_skips_optional_calls_by_default():
    api = make_api()

    result = api.create_draft_from_markdown(
        title="Title",
        markdown="Body",
    )

    api.put_draft.assert_not_called()
    api.add_tags_to_post.assert_not_called()
    api.prepublish_draft.assert_not_called()
    api.publish_draft.assert_not_called()
    assert result == {
        "draft": {"id": 123, "title": "Draft"},
        "tags": None,
        "prepublish": None,
        "publish": None,
    }


def test_normalize_tags_accepts_none_string_and_iterable():
    assert Api._normalize_tags(None) == []
    assert Api._normalize_tags("python") == ["python"]
    assert Api._normalize_tags(["python", 123]) == ["python", "123"]

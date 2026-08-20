import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from substack_mcp.mcp_server import (
    add_tags,
    get_draft,
    get_status,
    list_drafts,
    list_publications,
    post_draft_from_markdown,
    prepublish_draft,
    publish_draft,
    publish_draft_checked,
    put_draft,
    schedule_draft,
    unschedule_draft,
)


@pytest.fixture
def mock_api():
    with patch("substack_mcp.mcp_server.get_api") as mock_get_api:
        mock_instance = MagicMock()
        mock_get_api.return_value = mock_instance
        yield mock_instance


def test_get_status(mock_api):
    mock_api.get_user_profile.return_value = {"id": 123, "name": "Test User"}
    mock_api.get_user_primary_publication.return_value = {"subdomain": "test"}

    result = asyncio.run(get_status())

    assert result["profile"]["id"] == 123
    assert result["primary_publication"]["subdomain"] == "test"
    mock_api.get_user_profile.assert_called_once()
    mock_api.get_user_primary_publication.assert_called_once()


def test_list_publications(mock_api):
    mock_api.get_user_publications.return_value = [{"id": 1}]

    result = asyncio.run(list_publications())

    assert result == [{"id": 1}]
    mock_api.get_user_publications.assert_called_once()


def test_list_drafts(mock_api):
    mock_api.get_drafts.return_value = [{"id": 42}]

    result = asyncio.run(list_drafts(filter="draft", offset=5, limit=10))

    assert result == [{"id": 42}]
    mock_api.get_drafts.assert_called_once_with(filter="draft", offset=5, limit=10)


def test_get_draft(mock_api):
    mock_api.get_draft.return_value = {"id": 42, "title": "My Draft"}

    result = asyncio.run(get_draft(42))

    assert result == {"id": 42, "title": "My Draft"}
    mock_api.get_draft.assert_called_once_with(42)


def test_schedule_draft(mock_api):
    mock_api.schedule_draft.return_value = {"status": "scheduled"}

    result = asyncio.run(schedule_draft(42, "2025-01-01T12:00:00Z"))

    assert result == {"status": "scheduled"}
    expected_dt = datetime.fromisoformat("2025-01-01T12:00:00+00:00")
    mock_api.schedule_draft.assert_called_once_with(42, expected_dt)


def test_schedule_draft_invalid_iso(mock_api):
    with pytest.raises(ValueError, match="Invalid ISO datetime string"):
        asyncio.run(schedule_draft(42, "invalid-date"))


def test_unschedule_draft(mock_api):
    mock_api.unschedule_draft.return_value = {"status": "unscheduled"}

    result = asyncio.run(unschedule_draft(42))

    assert result == {"status": "unscheduled"}
    mock_api.unschedule_draft.assert_called_once_with(42)


def test_publish_draft_checked(mock_api):
    mock_api.publish_draft.return_value = {"status": "published"}

    result = asyncio.run(
        publish_draft_checked(42, confirm=True, send=True, share_automatically=True)
    )

    assert result == {"status": "published"}
    mock_api.prepublish_draft.assert_called_once_with(42)
    mock_api.publish_draft.assert_called_once_with(
        42, send=True, share_automatically=True
    )


def test_publish_draft_checked_rejected_without_confirm(mock_api):
    with pytest.raises(
        ValueError, match="Publishing rejected: confirm parameter must be True."
    ):
        asyncio.run(publish_draft_checked(42, confirm=False))

    mock_api.prepublish_draft.assert_not_called()
    mock_api.publish_draft.assert_not_called()


def test_publish_draft_checked_defaults(mock_api):
    mock_api.publish_draft.return_value = {"status": "published"}

    result = asyncio.run(publish_draft_checked(42, confirm=True))

    assert result == {"status": "published"}
    mock_api.prepublish_draft.assert_called_once_with(42)
    mock_api.publish_draft.assert_called_once_with(
        42, send=False, share_automatically=False
    )


def test_publish_draft_legacy(mock_api):
    mock_api.publish_draft.return_value = {"status": "published"}

    result = asyncio.run(publish_draft(42, send=True, share_automatically=False))

    assert result == {"status": "published"}
    mock_api.publish_draft.assert_called_once_with(
        42, send=True, share_automatically=False
    )
    mock_api.prepublish_draft.assert_not_called()


def test_post_draft_from_markdown(mock_api):
    mock_api.create_draft_from_markdown.return_value = {"draft": {"id": 1}}

    result = asyncio.run(post_draft_from_markdown("Title", "Body"))

    assert result == {"draft": {"id": 1}}
    mock_api.create_draft_from_markdown.assert_called_once_with(
        title="Title",
        markdown="Body",
        subtitle="",
        audience="everyone",
        write_comment_permissions="everyone",
        search_engine_title=None,
        search_engine_description=None,
        slug=None,
        draft_section_id=None,
        tags=None,
        prepublish=False,
        publish=False,
        send=True,
        share_automatically=False,
    )


def test_put_draft(mock_api):
    mock_api.put_draft.return_value = {"id": 1, "slug": "new"}

    result = asyncio.run(put_draft(1, {"slug": "new"}))

    assert result == {"id": 1, "slug": "new"}
    mock_api.put_draft.assert_called_once_with(1, slug="new")


def test_add_tags(mock_api):
    mock_api.add_tags_to_post.return_value = {"status": "ok"}

    result = asyncio.run(add_tags(1, ["tag1", "tag2"]))

    assert result == {"status": "ok"}
    mock_api.add_tags_to_post.assert_called_once_with(1, ["tag1", "tag2"])


def test_add_tags_invalid(mock_api):
    with pytest.raises(ValueError, match="tags is required"):
        asyncio.run(add_tags(1, None))


def test_prepublish_draft(mock_api):
    mock_api.prepublish_draft.return_value = {"status": "ok"}

    result = asyncio.run(prepublish_draft(1))

    assert result == {"status": "ok"}
    mock_api.prepublish_draft.assert_called_once_with(1)

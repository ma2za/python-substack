from unittest.mock import Mock

import pytest

from substack import Api
from substack.exceptions import DraftConflictError
from substack.revision import compute_draft_revision, format_revision_marker


def test_update_draft_from_markdown_basic(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    mock_get_user_id = Mock(return_value=1)
    monkeypatch.setattr(api, "get_user_id", mock_get_user_id)
    draft = {"id": 42, "draft_body": '{"type":"doc","content":[]}'}
    mock_get_draft = Mock(return_value=draft)
    monkeypatch.setattr(api, "get_draft", mock_get_draft)
    mock_put_draft = Mock(return_value={"id": 42})
    monkeypatch.setattr(api, "put_draft", mock_put_draft)

    # 1. Without revision marker or override, raises DraftConflictError (unprotected update)
    with pytest.raises(DraftConflictError, match="missing revision metadata"):
        api.update_draft_from_markdown(42, "Updated content")

    # 2. With allow_conflict=True override, succeeds
    res_override = api.update_draft_from_markdown(
        42, "Updated content", allow_conflict=True
    )
    assert res_override["action"] == "update"
    assert res_override["draft_id"] == 42
    assert res_override["conflict"] is True
    assert res_override["override"] is True
    assert mock_put_draft.called

    # 3. With matching revision marker, succeeds without conflict
    mock_put_draft.reset_mock()
    marker = format_revision_marker(compute_draft_revision(draft))
    res_marker = api.update_draft_from_markdown(42, f"{marker}\n\nUpdated content")
    assert res_marker["action"] == "update"
    assert res_marker["draft_id"] == 42
    assert res_marker["conflict"] is False
    assert mock_put_draft.called

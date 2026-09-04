from unittest.mock import Mock, patch

import pytest

from substack import Api


def test_update_draft_from_markdown_basic(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    mock_get_user_id = Mock(return_value=1)
    monkeypatch.setattr(api, "get_user_id", mock_get_user_id)
    mock_get_draft = Mock(
        return_value={"id": 42, "draft_body": '{"type":"doc","content":[]}'}
    )
    monkeypatch.setattr(api, "get_draft", mock_get_draft)
    mock_put_draft = Mock(return_value={"id": 42})
    monkeypatch.setattr(api, "put_draft", mock_put_draft)
    res = api.update_draft_from_markdown(42, "Updated content")
    assert res["action"] == "update"
    assert res["draft_id"] == 42
    assert res["dry_run"] is False
    assert mock_put_draft.called

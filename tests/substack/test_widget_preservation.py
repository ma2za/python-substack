import base64
import json
from unittest.mock import Mock, patch

import pytest

from substack import Api, cli
from substack.mdrender import parse_node_marker, markdown_to_doc


def test_parse_node_marker_valid():
    node = {"type": "button", "attrs": {"text": "Click me", "url": "https://example.com"}}
    payload = json.dumps(node, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    comment = f"<!-- python-substack-node:v1 {encoded} -->"
    
    parsed = parse_node_marker(comment)
    assert parsed == node


def test_parse_node_marker_corrupt_format():
    with pytest.raises(ValueError, match="Corrupt marker format"):
        parse_node_marker("<!-- python-substack-node:v1 corrupt base64 here! -->")


def test_parse_node_marker_invalid_base64():
    # Attempted but bad character
    with pytest.raises(ValueError, match="Corrupt marker format"):
        parse_node_marker("<!-- python-substack-node:v1 @@@ -->")


def test_parse_node_marker_invalid_json():
    # Valid base64 but invalid JSON (not a complete object)
    encoded = base64.urlsafe_b64encode(b"{not valid json").decode("ascii").rstrip("=")
    with pytest.raises(ValueError, match="Invalid JSON"):
        parse_node_marker(f"<!-- python-substack-node:v1 {encoded} -->")


def test_parse_node_marker_not_object():
    # Valid JSON but a list instead of a dict
    encoded = base64.urlsafe_b64encode(b"[]").decode("ascii").rstrip("=")
    with pytest.raises(ValueError, match="not a top-level JSON object"):
        parse_node_marker(f"<!-- python-substack-node:v1 {encoded} -->")


def test_parse_node_marker_missing_type():
    # Valid object but missing type
    encoded = base64.urlsafe_b64encode(b'{"attrs": {}}').decode("ascii").rstrip("=")
    with pytest.raises(ValueError, match="missing or empty 'type'"):
        parse_node_marker(f"<!-- python-substack-node:v1 {encoded} -->")


def test_parse_node_marker_empty_type():
    # Valid object but empty type
    encoded = base64.urlsafe_b64encode(b'{"type": ""}').decode("ascii").rstrip("=")
    with pytest.raises(ValueError, match="missing or empty 'type'"):
        parse_node_marker(f"<!-- python-substack-node:v1 {encoded} -->")


def test_parse_node_marker_ordinary_comment():
    assert parse_node_marker("<!-- ordinary HTML comment -->") is None


def test_markdown_to_doc_preserves_block_and_inline_markers():
    # Build a button node
    btn = {"type": "button", "attrs": {"text": "Click me", "url": "https://example.com"}}
    btn_payload = json.dumps(btn, separators=(",", ":"), sort_keys=True).encode("utf-8")
    btn_encoded = base64.urlsafe_b64encode(btn_payload).decode("ascii").rstrip("=")
    btn_comment = f"<!-- python-substack-node:v1 {btn_encoded} -->"

    # Build an inline recipe node
    recipe = {"type": "recipe", "attrs": {"id": 123}}
    recipe_payload = json.dumps(recipe, separators=(",", ":"), sort_keys=True).encode("utf-8")
    recipe_encoded = base64.urlsafe_b64encode(recipe_payload).decode("ascii").rstrip("=")
    recipe_comment = f"<!-- python-substack-node:v1 {recipe_encoded} -->"

    markdown = f"""# Heading 1

Some text and inline {recipe_comment} recipe.

{btn_comment}

<!-- ordinary comment should be ignored -->
"""
    doc = markdown_to_doc(markdown)
    
    # doc should have heading, paragraph (with text, recipe inline node, text), and the button block node
    assert len(doc) == 3
    assert doc[0]["type"] == "heading"
    
    p = doc[1]
    assert p["type"] == "paragraph"
    inline_content = p["content"]
    assert len(inline_content) == 3
    assert inline_content[0]["text"] == "Some text and inline "
    assert inline_content[1] == recipe
    assert inline_content[2]["text"] == " recipe."

    assert doc[2] == btn


def test_update_draft_from_markdown_preservation(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    # Remote draft contains an unsupported "button" node
    remote_btn = {"type": "button", "attrs": {"text": "Click", "url": "https://example.com"}}
    remote_body = {
        "type": "doc",
        "content": [
            {"type": "heading", "attrs": {"level": 1}, "content": [{"type": "text", "text": "Hello"}]},
            remote_btn
        ]
    }
    mock_get_draft = Mock(return_value={"id": 42, "draft_body": json.dumps(remote_body)})
    monkeypatch.setattr(api, "get_draft", mock_get_draft)
    
    mock_put_draft = Mock(return_value={"id": 42})
    monkeypatch.setattr(api, "put_draft", mock_put_draft)

    # 1. Update with correct marker matches and succeeds
    btn_payload = json.dumps(remote_btn, separators=(",", ":"), sort_keys=True).encode("utf-8")
    btn_encoded = base64.urlsafe_b64encode(btn_payload).decode("ascii").rstrip("=")
    submitted_markdown = f"# New Title\n\n<!-- python-substack-node:v1 {btn_encoded} -->\n"

    res = api.update_draft_from_markdown(42, submitted_markdown)
    assert res["action"] == "update"
    assert res["dry_run"] is False
    assert mock_put_draft.called

    # 2. Update without marker fails when allow_unsupported_change is False
    mock_put_draft.reset_mock()
    with pytest.raises(ValueError, match="remote unsupported nodes are missing"):
        api.update_draft_from_markdown(42, "# New Title without button")
    assert not mock_put_draft.called

    # 3. Update without marker succeeds when allow_unsupported_change is True
    mock_put_draft.reset_mock()
    res = api.update_draft_from_markdown(42, "# New Title without button", allow_unsupported_change=True)
    assert res["action"] == "update"
    assert mock_put_draft.called


def test_cli_update_requires_yes_for_allow_unsupported_change(tmp_path, monkeypatch, capsys):
    # Mocking UpdateOperationsApi
    class MockApi:
        def update_draft_from_markdown(self, *args, **kwargs):
            return {"action": "update"}
    
    monkeypatch.setattr(cli, "_api_from_env", lambda **kw: MockApi())
    
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    
    # If passing --allow-unsupported-change without --yes, it must raise CLIUsageError
    assert cli.main(["drafts", "update", "42", str(md_file), "--allow-unsupported-change"]) == 2
    err = capsys.readouterr().err
    assert "--yes is required when using --allow-unsupported-change" in err

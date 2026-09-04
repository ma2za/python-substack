import json
from pathlib import Path

import pytest

from substack import cli


class UpdateOperationsApi:
    def __init__(self):
        self.calls = []

    def update_draft_from_markdown(self, draft_id, markdown, **kwargs):
        self.calls.append(("update", draft_id, markdown, kwargs))
        return {
            "action": "update",
            "draft_id": draft_id,
            "dry_run": kwargs.get("dry_run", False),
            "changed": not kwargs.get("dry_run", False),
            "payload": {},
            "draft": {"id": draft_id},
            "tags": None,
            "unsupported_nodes": [],
        }


def use_api(monkeypatch, mock_api):
    monkeypatch.setattr(cli, "_api_from_env", lambda **kw: mock_api)


def test_drafts_update_requires_yes_in_json_mode(tmp_path, monkeypatch, capsys):
    api = UpdateOperationsApi()
    use_api(monkeypatch, api)
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    assert cli.main(["--json", "drafts", "update", "42", str(md_file)]) == 2
    err = capsys.readouterr().err
    assert "requires" in err or "required" in err
    assert "--yes" in err
    assert api.calls == []


def test_drafts_update_json_dry_run(tmp_path, monkeypatch, capsys):
    api = UpdateOperationsApi()
    use_api(monkeypatch, api)
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    assert (
        cli.main(
            ["--json", "drafts", "update", "42", str(md_file), "--dry-run", "--yes"]
        )
        == 0
    )
    out = json.loads(capsys.readouterr().out)
    assert out["action"] == "update"
    assert out["draft_id"] == 42
    assert out["dry_run"] is True
    assert api.calls[0][0] == "update"
    assert api.calls[0][1] == 42
    assert api.calls[0][2] == "# Test"
    assert api.calls[0][3]["dry_run"] is True

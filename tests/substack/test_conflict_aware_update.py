import base64
import json
from unittest.mock import Mock

import pytest

from substack import Api, cli
from substack.exceptions import DraftConflictError, SubstackException
from substack.nodes import paragraph, text
from substack.revision import (
    compare_draft_revisions,
    compute_draft_revision,
    format_revision_marker,
    parse_revision_marker,
)


def _sample_draft(
    draft_id=42,
    body_text="Hello world",
    title="Original Title",
    subtitle="Original Subtitle",
    audience="everyone",
    write_comment_permissions="everyone",
    draft_section_id=None,
    slug="original-slug",
    updated_at="2026-10-01T10:00:00Z",
):
    body = {"type": "doc", "content": [paragraph([text(body_text)])]}
    return {
        "id": draft_id,
        "draft_body": json.dumps(body),
        "draft_title": title,
        "draft_subtitle": subtitle,
        "audience": audience,
        "write_comment_permissions": write_comment_permissions,
        "draft_section_id": draft_section_id,
        "slug": slug,
        "draft_updated_at": updated_at,
    }


# ==============================================================================
# 1. Revision Helper Unit Tests
# ==============================================================================


def test_compute_draft_revision_stability():
    draft1 = _sample_draft()
    draft2 = _sample_draft()
    rev1 = compute_draft_revision(draft1)
    rev2 = compute_draft_revision(draft2)
    assert rev1["revision"] == rev2["revision"]
    assert rev1["body_hash"] == rev2["body_hash"]
    assert rev1["draft_id"] == 42
    assert rev1["version"] == 1


def test_format_and_parse_revision_marker_roundtrip():
    draft = _sample_draft()
    rev = compute_draft_revision(draft)
    marker = format_revision_marker(rev)
    assert marker.startswith("<!-- python-substack-revision:v1 ")
    assert marker.endswith(" -->")

    markdown = f"{marker}\n\n# Document Title\n\nSome text content."
    parsed = parse_revision_marker(markdown)
    assert parsed is not None
    assert parsed["revision"] == rev["revision"]
    assert parsed["draft_id"] == 42
    assert parsed["body_hash"] == rev["body_hash"]


def test_parse_revision_marker_ignores_code_blocks():
    draft = _sample_draft()
    rev = compute_draft_revision(draft)
    marker = format_revision_marker(rev)

    # Marker inside fenced code block should not be parsed as the document revision marker
    fenced_code_md = f"""# Guide

```markdown
{marker}
```

No top-level marker here.
"""
    assert parse_revision_marker(fenced_code_md) is None


def test_parse_revision_marker_rejects_malformed_syntax():
    with pytest.raises(ValueError, match="Malformed revision marker"):
        parse_revision_marker("<!-- python-substack-revision:v1 @@@ -->")

    with pytest.raises(ValueError, match="Malformed revision marker"):
        parse_revision_marker("<!-- python-substack-revision:v1 not-valid-base64!! -->")


def test_parse_revision_marker_rejects_corrupt_json():
    corrupt_bytes = base64.urlsafe_b64encode(b"{not json").decode("ascii").rstrip("=")
    with pytest.raises(ValueError, match="invalid JSON"):
        parse_revision_marker(f"<!-- python-substack-revision:v1 {corrupt_bytes} -->")


def test_parse_revision_marker_rejects_non_dict_payload():
    non_dict = base64.urlsafe_b64encode(b'["list"]').decode("ascii").rstrip("=")
    with pytest.raises(ValueError, match="payload must be a JSON object"):
        parse_revision_marker(f"<!-- python-substack-revision:v1 {non_dict} -->")


def test_parse_revision_marker_rejects_missing_revision_field():
    missing_rev = (
        base64.urlsafe_b64encode(b'{"draft_id": 42}').decode("ascii").rstrip("=")
    )
    with pytest.raises(ValueError, match="missing or empty required 'revision' field"):
        parse_revision_marker(f"<!-- python-substack-revision:v1 {missing_rev} -->")


def test_parse_revision_marker_rejects_unsupported_version():
    valid = base64.urlsafe_b64encode(b'{"revision": "abc"}').decode("ascii").rstrip("=")
    with pytest.raises(ValueError, match="unsupported version '2'"):
        parse_revision_marker(f"<!-- python-substack-revision:v2 {valid} -->")


def test_parse_revision_marker_rejects_multiple_markers():
    draft = _sample_draft()
    rev = compute_draft_revision(draft)
    m = format_revision_marker(rev)
    multi_md = f"{m}\n\nSome text\n\n{m}"
    with pytest.raises(ValueError, match="multiple revision markers found"):
        parse_revision_marker(multi_md)


# ==============================================================================
# 2. SDK Unchanged Draft Updates
# ==============================================================================


def test_sdk_update_unchanged_draft_succeeds(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    draft = _sample_draft()
    monkeypatch.setattr(api, "get_draft", lambda d_id: draft)
    put_mock = Mock(return_value={"id": 42})
    monkeypatch.setattr(api, "put_draft", put_mock)

    exported = api.export_draft_to_markdown(42)
    assert "revision" in exported
    assert "python-substack-revision:v1" in exported["markdown"]

    # Update using exported markdown
    res = api.update_draft_from_markdown(42, exported["markdown"])
    assert res["action"] == "update"
    assert res["conflict"] is False
    assert res["mismatches"] == []
    assert put_mock.called


# ==============================================================================
# 3. SDK Conflict Detection: Remote Body and Metadata Changes
# ==============================================================================


def test_sdk_update_detects_remote_body_conflict(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    initial_draft = _sample_draft(body_text="Initial remote content")
    monkeypatch.setattr(api, "get_draft", lambda d_id: initial_draft)
    exported = api.export_draft_to_markdown(42)

    # Remote draft body is modified on Substack after export
    modified_draft = _sample_draft(body_text="Altered content on Substack web editor")
    monkeypatch.setattr(api, "get_draft", lambda d_id: modified_draft)
    put_mock = Mock()
    monkeypatch.setattr(api, "put_draft", put_mock)

    # 1. Normal update fails closed
    with pytest.raises(DraftConflictError) as exc_info:
        api.update_draft_from_markdown(42, exported["markdown"])

    err = exc_info.value
    assert isinstance(err, ValueError)
    assert isinstance(err, SubstackException)
    assert "Remote draft body has changed since export" in err.message
    assert "Remote draft body has changed since export" in err.mismatches
    assert not put_mock.called

    # 2. Dry run returns conflict details without writing
    dry = api.update_draft_from_markdown(42, exported["markdown"], dry_run=True)
    assert dry["dry_run"] is True
    assert dry["conflict"] is True
    assert "Remote draft body has changed since export" in dry["mismatches"]
    assert not put_mock.called

    # 3. Explicit override proceeds
    overridden = api.update_draft_from_markdown(
        42, exported["markdown"], allow_conflict=True
    )
    assert overridden["action"] == "update"
    assert overridden["conflict"] is True
    assert overridden["override"] is True
    assert put_mock.called


def test_sdk_update_detects_remote_metadata_conflicts(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    initial_draft = _sample_draft(
        title="Title A",
        subtitle="Subtitle A",
        audience="everyone",
        write_comment_permissions="everyone",
        draft_section_id=10,
        slug="slug-a",
    )
    monkeypatch.setattr(api, "get_draft", lambda d_id: initial_draft)
    exported = api.export_draft_to_markdown(42)

    # Remote metadata modified on Substack
    changed_draft = _sample_draft(
        title="Title B",
        subtitle="Subtitle B",
        audience="paid",
        write_comment_permissions="none",
        draft_section_id=20,
        slug="slug-b",
    )
    monkeypatch.setattr(api, "get_draft", lambda d_id: changed_draft)

    dry = api.update_draft_from_markdown(42, exported["markdown"], dry_run=True)
    assert dry["conflict"] is True
    mismatches_text = " ".join(dry["mismatches"])
    assert "Remote title changed" in mismatches_text
    assert "Remote subtitle changed" in mismatches_text
    assert "Remote audience changed" in mismatches_text
    assert "Remote write_comment_permissions changed" in mismatches_text
    assert "Remote section changed" in mismatches_text
    assert "Remote slug changed" in mismatches_text


def test_sdk_update_detects_draft_id_mismatch(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    draft_42 = _sample_draft(draft_id=42)
    monkeypatch.setattr(api, "get_draft", lambda d_id: draft_42)
    exported = api.export_draft_to_markdown(42)

    # Try applying markdown exported from 42 to draft 99
    draft_99 = _sample_draft(draft_id=99)
    monkeypatch.setattr(api, "get_draft", lambda d_id: draft_99)

    with pytest.raises(DraftConflictError, match="Draft ID mismatch"):
        api.update_draft_from_markdown(99, exported["markdown"])


# ==============================================================================
# 4. Old Exports / Missing Revision Metadata (Unprotected Update)
# ==============================================================================


def test_sdk_update_missing_revision_marker_fails_closed(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    draft = _sample_draft()
    monkeypatch.setattr(api, "get_draft", lambda d_id: draft)
    put_mock = Mock(return_value={"id": 42})
    monkeypatch.setattr(api, "put_draft", put_mock)

    legacy_markdown = "# Legacy Markdown\n\nNo revision marker here."

    # 1. Fails closed by default
    with pytest.raises(DraftConflictError) as exc_info:
        api.update_draft_from_markdown(42, legacy_markdown)
    assert "missing revision metadata" in exc_info.value.message
    assert not put_mock.called

    # 2. Dry run identifies missing metadata
    dry = api.update_draft_from_markdown(42, legacy_markdown, dry_run=True)
    assert dry["conflict"] is True
    assert any("missing revision metadata" in m for m in dry["mismatches"])
    assert not put_mock.called

    # 3. Explicit override with allow_conflict=True proceeds
    res = api.update_draft_from_markdown(42, legacy_markdown, allow_conflict=True)
    assert res["action"] == "update"
    assert res["conflict"] is True
    assert res["override"] is True
    assert put_mock.called

    # 4. Explicit override with force=True proceeds
    put_mock.reset_mock()
    res_force = api.update_draft_from_markdown(42, legacy_markdown, force=True)
    assert res_force["action"] == "update"
    assert res_force["conflict"] is True
    assert put_mock.called


# ==============================================================================
# 5. CLI Verification: JSON, Non-Interactive, Conflict Display, and Overrides
# ==============================================================================


class MockCliApi:
    def __init__(self, conflict=False, mismatches=None):
        self.calls = []
        self.conflict = conflict
        self.mismatches = mismatches or []

    def update_draft_from_markdown(self, draft_id, markdown, **kwargs):
        self.calls.append(("update", draft_id, markdown, kwargs))
        dry_run = kwargs.get("dry_run", False)
        allow_conflict = kwargs.get("allow_conflict", False)

        if self.conflict and not dry_run and not allow_conflict:
            raise DraftConflictError(
                f"Refusing to update: remote draft has changed since export ({'; '.join(self.mismatches)}). "
                "Re-export the draft or pass allow_conflict=True to proceed.",
                mismatches=self.mismatches,
            )

        payload = {
            "action": "update",
            "draft_id": draft_id,
            "dry_run": dry_run,
            "changed": not dry_run,
            "conflict": self.conflict,
            "mismatches": self.mismatches,
        }
        if self.conflict and allow_conflict:
            payload["override"] = True
        return payload


def test_cli_update_conflict_fails_with_exit_code_1(tmp_path, monkeypatch, capsys):
    mock_api = MockCliApi(
        conflict=True, mismatches=["Remote draft body has changed since export"]
    )
    monkeypatch.setattr(cli, "_api_from_env", lambda **kw: mock_api)

    md_file = tmp_path / "draft.md"
    md_file.write_text("# Draft Content", encoding="utf-8")

    # Non-interactive without --allow-conflict fails with exit code 1
    code = cli.main(["drafts", "update", "42", str(md_file), "--yes"])
    assert code == 1
    err = capsys.readouterr().err
    assert "remote draft has changed since export" in err


def test_cli_update_conflict_json_output(tmp_path, monkeypatch, capsys):
    mock_api = MockCliApi(
        conflict=True, mismatches=["Remote draft body has changed since export"]
    )
    monkeypatch.setattr(cli, "_api_from_env", lambda **kw: mock_api)

    md_file = tmp_path / "draft.md"
    md_file.write_text("# Draft Content", encoding="utf-8")

    # In --json mode, outputs structured conflict error
    code = cli.main(["--json", "drafts", "update", "42", str(md_file), "--yes"])
    assert code == 1
    err = json.loads(capsys.readouterr().err)
    assert err["error"]["type"] == "conflict_error"
    assert "Remote draft body has changed since export" in err["error"]["mismatches"]


def test_cli_update_dry_run_conflict_json_output(tmp_path, monkeypatch, capsys):
    mock_api = MockCliApi(
        conflict=True, mismatches=["Remote draft body has changed since export"]
    )
    monkeypatch.setattr(cli, "_api_from_env", lambda **kw: mock_api)

    md_file = tmp_path / "draft.md"
    md_file.write_text("# Draft Content", encoding="utf-8")

    code = cli.main(
        ["--json", "drafts", "update", "42", str(md_file), "--dry-run", "--yes"]
    )
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["conflict"] is True
    assert out["dry_run"] is True
    assert "Remote draft body has changed since export" in out["mismatches"]


def test_cli_update_override_with_allow_conflict_and_yes(tmp_path, monkeypatch, capsys):
    mock_api = MockCliApi(
        conflict=True, mismatches=["Remote draft body has changed since export"]
    )
    monkeypatch.setattr(cli, "_api_from_env", lambda **kw: mock_api)

    md_file = tmp_path / "draft.md"
    md_file.write_text("# Draft Content", encoding="utf-8")

    code = cli.main(
        [
            "--json",
            "drafts",
            "update",
            "42",
            str(md_file),
            "--allow-conflict",
            "--yes",
        ]
    )
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["conflict"] is True
    assert out["override"] is True


def test_cli_export_includes_revision_in_json(monkeypatch, capsys):
    class ExportApi:
        def export_draft_to_markdown(self, draft_id):
            return {
                "draft": {"id": draft_id},
                "markdown": "<!-- python-substack-revision:v1 test -->\n\n# Body",
                "unsupported_nodes": [],
                "revision": {"draft_id": draft_id, "revision": "rev123", "version": 1},
            }

    monkeypatch.setattr(cli, "_api_from_env", lambda **kw: ExportApi())
    code = cli.main(["--json", "drafts", "export", "42"])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["action"] == "export"
    assert out["revision"] == {
        "draft_id": 42,
        "revision": "rev123",
        "version": 1,
    }


# ==============================================================================
# 6. Adversarial Tests: Bidi, Unicode, Special Chars, Complex Nested Documents
# ==============================================================================


def test_adversarial_bidi_and_nested_content_conflict_resolution(monkeypatch):
    api = Api.__new__(Api)
    api.publication_url = "https://test.substack.com"
    monkeypatch.setattr(api, "get_user_id", lambda: 1)

    complex_title = "Hebrew & Arabic \u202e\u05e2\u05d1\u05e8\u05d9\u05ea\u202c \u202e\u0627\u0644\u0639\u0631\u0628\u064a\u0629\u202c \"Quotes\" 'Single'"
    complex_subtitle = "Special 🚀🔥✨ zero\u200bwidth & chars \x00 null test"

    draft = _sample_draft(
        title=complex_title,
        subtitle=complex_subtitle,
        body_text="Complex body with emojis 🌟🎉",
    )
    monkeypatch.setattr(api, "get_draft", lambda d_id: draft)
    put_mock = Mock(return_value={"id": 42})
    monkeypatch.setattr(api, "put_draft", put_mock)

    exported = api.export_draft_to_markdown(42)
    assert "python-substack-revision:v1" in exported["markdown"]

    # Updating with the exact exported markdown resolves without conflict
    res = api.update_draft_from_markdown(42, exported["markdown"])
    assert res["conflict"] is False
    assert put_mock.called

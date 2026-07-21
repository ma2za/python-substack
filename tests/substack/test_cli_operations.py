import io
import json
import sys
from datetime import datetime, timedelta, timezone

import pytest

from substack import cli
from substack.exceptions import SubstackAPIException


class OperationsApi:
    publication_url = "https://writer.substack.com/api/v1"

    def __init__(self):
        self.calls = []
        self.publish_error = None

    def get_user_profile(self):
        self.calls.append(("profile",))
        return {"id": 7, "email": "writer@example.com"}

    def get_user_publications(self):
        self.calls.append(("publications",))
        return [
            {
                "id": 11,
                "name": "Writer Notes",
                "subdomain": "writer",
                "publication_url": "https://writer.substack.com",
            }
        ]

    def get_publication_subscriber_count(self):
        self.calls.append(("subscriber_count",))
        return 123

    def get_drafts(self, **kwargs):
        self.calls.append(("list", kwargs))
        return [
            {
                "id": 42,
                "draft_title": "Draft title",
                "type": "draft",
                "post_date": None,
            }
        ]

    def get_draft(self, draft_id):
        self.calls.append(("get", draft_id))
        return {"id": draft_id, "draft_title": "Draft title", "slug": "draft-title"}

    def create_draft_from_markdown(self, **kwargs):
        self.calls.append(("create", kwargs))
        return {
            "draft": {"id": 43, "draft_title": kwargs["title"]},
            "tags": {"tags_added": kwargs["tags"]} if kwargs["tags"] else None,
            "prepublish": None,
            "publish": None,
        }

    def schedule_draft(self, draft_id, scheduled_at):
        self.calls.append(("schedule", draft_id, scheduled_at))
        return {"scheduled": True}

    def unschedule_draft(self, draft_id):
        self.calls.append(("unschedule", draft_id))
        return {"scheduled": False}

    def prepublish_draft(self, draft_id):
        self.calls.append(("prepublish", draft_id))
        if self.publish_error:
            raise self.publish_error
        return {"ready": True}

    def publish_draft(self, draft_id, send=True, share_automatically=False):
        self.calls.append(("publish", draft_id, send, share_automatically))
        return {"published": True}

    def delete_draft(self, draft_id):
        self.calls.append(("delete", draft_id))
        return {"deleted": True}


class TTYInput(io.StringIO):
    def isatty(self):
        return True


def use_api(monkeypatch, api):
    monkeypatch.setattr(
        cli,
        "_api_from_env",
        lambda cookies_path=None, publication_url=None: api,
    )


def test_status_human_output(monkeypatch, capsys):
    api = OperationsApi()
    use_api(monkeypatch, api)
    monkeypatch.setattr(cli, "_auth_method", lambda cookies_path=None: "cookies_path")

    assert cli.main(["status"]) == 0

    output = capsys.readouterr().out
    assert "Authenticated as: writer@example.com" in output
    assert "Publication: Writer Notes" in output
    assert "Subscribers: 123" in output


def test_publications_json_contract(monkeypatch, capsys):
    api = OperationsApi()
    use_api(monkeypatch, api)

    assert cli.main(["--json", "publications", "list"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["count"] == 1
    assert output["publications"][0]["id"] == 11


def test_drafts_list_defaults_and_json_contract(monkeypatch, capsys):
    api = OperationsApi()
    use_api(monkeypatch, api)

    assert cli.main(["--json", "drafts", "list"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output == {
        "drafts": [
            {
                "id": 42,
                "draft_title": "Draft title",
                "type": "draft",
                "post_date": None,
            }
        ],
        "count": 1,
        "filter": "draft",
        "offset": 0,
        "limit": 25,
    }
    assert api.calls == [("list", {"filter": "draft", "offset": 0, "limit": 25})]


def test_drafts_list_validates_pagination(monkeypatch, capsys):
    api = OperationsApi()
    use_api(monkeypatch, api)

    assert cli.main(["drafts", "list", "--limit", "0"]) == 2

    assert "--limit must be greater than zero" in capsys.readouterr().err
    assert api.calls == []


def test_drafts_get_human_output(monkeypatch, capsys):
    api = OperationsApi()
    use_api(monkeypatch, api)

    assert cli.main(["drafts", "get", "42"]) == 0

    output = capsys.readouterr().out
    assert "ID: 42" in output
    assert "Title: Draft title" in output
    assert "Slug: draft-title" in output


def test_drafts_create_infers_title_and_preserves_safe_defaults(
    tmp_path, monkeypatch, capsys
):
    markdown = tmp_path / "release-notes.md"
    markdown.write_text("# Inferred title\n\nBody", encoding="utf-8")
    api = OperationsApi()
    use_api(monkeypatch, api)

    assert cli.main(["drafts", "create", str(markdown)]) == 0

    assert capsys.readouterr().out == "Created draft 43: Inferred title\n"
    kwargs = api.calls[0][1]
    assert kwargs == {
        "title": "Inferred title",
        "markdown": "# Inferred title\n\nBody",
        "subtitle": "",
        "audience": "everyone",
        "write_comment_permissions": "everyone",
        "search_engine_title": None,
        "search_engine_description": None,
        "slug": None,
        "draft_section_id": None,
        "tags": None,
        "prepublish": False,
        "publish": False,
    }
    assert not any(
        call[0] in {"prepublish", "publish", "schedule", "delete"} for call in api.calls
    )


def test_drafts_create_help_lists_supported_options(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli._build_parser().parse_args(["drafts", "create", "--help"])

    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    for option in (
        "--title",
        "--subtitle",
        "--audience",
        "--write-comment-permissions",
        "--search-engine-title",
        "--search-engine-description",
        "--slug",
        "--draft-section-id",
        "--tag",
    ):
        assert option in output


def test_drafts_create_json_contract_and_options(tmp_path, monkeypatch, capsys):
    markdown = tmp_path / "post.md"
    markdown.write_text("Body", encoding="utf-8")
    api = OperationsApi()
    use_api(monkeypatch, api)

    assert (
        cli.main(
            [
                "--json",
                "drafts",
                "create",
                str(markdown),
                "--title",
                "Explicit title",
                "--subtitle",
                "Subtitle",
                "--audience",
                "only_paid",
                "--write-comment-permissions",
                "only_paid",
                "--search-engine-title",
                "Search title",
                "--search-engine-description",
                "Search description",
                "--slug",
                "explicit-title",
                "--draft-section-id",
                "9",
                "--tag",
                "python",
                "--tag",
                "automation",
            ]
        )
        == 0
    )

    kwargs = api.calls[0][1]
    assert kwargs["title"] == "Explicit title"
    assert kwargs["subtitle"] == "Subtitle"
    assert kwargs["audience"] == "only_paid"
    assert kwargs["write_comment_permissions"] == "only_paid"
    assert kwargs["search_engine_title"] == "Search title"
    assert kwargs["search_engine_description"] == "Search description"
    assert kwargs["slug"] == "explicit-title"
    assert kwargs["draft_section_id"] == 9
    assert kwargs["tags"] == ["python", "automation"]
    assert json.loads(capsys.readouterr().out) == {
        "action": "create",
        "draft_id": 43,
        "draft": {"id": 43, "draft_title": "Explicit title"},
        "tags": {"tags_added": ["python", "automation"]},
    }


def test_drafts_create_uses_filename_when_heading_is_missing(
    tmp_path, monkeypatch, capsys
):
    markdown = tmp_path / "file-title.md"
    markdown.write_text("Body", encoding="utf-8")
    api = OperationsApi()
    use_api(monkeypatch, api)

    assert cli.main(["drafts", "create", str(markdown)]) == 0

    assert api.calls[0][1]["title"] == "file-title"
    assert capsys.readouterr().out == "Created draft 43: file-title\n"


def test_drafts_create_missing_file_uses_existing_error_contract(
    tmp_path, monkeypatch, capsys
):
    api = OperationsApi()
    use_api(monkeypatch, api)

    assert cli.main(["--json", "drafts", "create", str(tmp_path / "missing.md")]) == 1

    error = json.loads(capsys.readouterr().err)
    assert error["error"]["type"] == "io_error"
    assert api.calls == []


def test_drafts_create_invalid_utf8_uses_existing_error_contract(
    tmp_path, monkeypatch, capsys
):
    markdown = tmp_path / "invalid.md"
    markdown.write_bytes(b"\xff")
    api = OperationsApi()
    use_api(monkeypatch, api)

    assert cli.main(["--json", "drafts", "create", str(markdown)]) == 1

    error = json.loads(capsys.readouterr().err)
    assert error["error"]["type"] == "configuration_error"
    assert api.calls == []


def test_drafts_create_api_error_is_redacted(tmp_path, monkeypatch, capsys):
    markdown = tmp_path / "post.md"
    markdown.write_text("Body", encoding="utf-8")
    secret = "draft-secret"
    api = OperationsApi()
    monkeypatch.setenv("PASSWORD", secret)
    monkeypatch.setattr(
        api,
        "create_draft_from_markdown",
        lambda **kwargs: (_ for _ in ()).throw(
            SubstackAPIException(400, json.dumps({"error": f"failed {secret}"}))
        ),
    )
    use_api(monkeypatch, api)

    assert cli.main(["--json", "drafts", "create", str(markdown)]) == 1

    error_text = capsys.readouterr().err
    assert secret not in error_text
    assert "[redacted]" in error_text
    assert json.loads(error_text)["error"]["type"] == "api_error"


def test_schedule_accepts_z_timestamp(monkeypatch, capsys):
    api = OperationsApi()
    use_api(monkeypatch, api)

    assert (
        cli.main(["--json", "drafts", "schedule", "42", "--at", "2030-01-02T03:04:05Z"])
        == 0
    )

    scheduled_at = api.calls[0][2]
    assert scheduled_at == datetime(2030, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    output = json.loads(capsys.readouterr().out)
    assert output["scheduled_at"] == "2030-01-02T03:04:05+00:00"


def test_schedule_preserves_timezone_offset(monkeypatch):
    api = OperationsApi()
    use_api(monkeypatch, api)

    assert (
        cli.main(["drafts", "schedule", "42", "--at", "2030-01-02T03:04:05+02:30"]) == 0
    )

    assert api.calls[0][2].utcoffset() == timedelta(hours=2, minutes=30)


def test_schedule_rejects_naive_and_malformed_timestamps(monkeypatch, capsys):
    api = OperationsApi()
    use_api(monkeypatch, api)

    assert cli.main(["drafts", "schedule", "42", "--at", "2030-01-02T03:04:05"]) == 2
    assert "timezone offset or Z" in capsys.readouterr().err
    assert cli.main(["drafts", "schedule", "42", "--at", "tomorrow"]) == 2
    assert "valid ISO 8601" in capsys.readouterr().err
    assert api.calls == []


def test_unschedule_json_contract(monkeypatch, capsys):
    api = OperationsApi()
    use_api(monkeypatch, api)

    assert cli.main(["--json", "drafts", "unschedule", "42"]) == 0

    assert json.loads(capsys.readouterr().out) == {
        "action": "unschedule",
        "draft_id": 42,
        "result": {"scheduled": False},
    }


def test_publish_requires_yes_in_noninteractive_mode(monkeypatch, capsys):
    api = OperationsApi()
    use_api(monkeypatch, api)
    monkeypatch.setattr(sys, "stdin", io.StringIO())

    assert cli.main(["drafts", "publish", "42"]) == 2

    assert "requires --yes" in capsys.readouterr().err
    assert api.calls == []


def test_publish_requires_yes_in_json_mode(monkeypatch, capsys):
    api = OperationsApi()
    use_api(monkeypatch, api)
    monkeypatch.setattr(sys, "stdin", TTYInput("yes\n"))

    assert cli.main(["--json", "drafts", "publish", "42"]) == 2

    error = json.loads(capsys.readouterr().err)
    assert error["error"]["type"] == "usage_error"
    assert "requires --yes" in error["error"]["message"]
    assert api.calls == []


def test_publish_calls_prepublish_before_publish(monkeypatch, capsys):
    api = OperationsApi()
    use_api(monkeypatch, api)

    assert (
        cli.main(
            [
                "--json",
                "drafts",
                "publish",
                "42",
                "--no-send",
                "--share-automatically",
                "--yes",
            ]
        )
        == 0
    )

    assert api.calls == [
        ("prepublish", 42),
        ("publish", 42, False, True),
    ]
    output = json.loads(capsys.readouterr().out)
    assert output["prepublish"] == {"ready": True}
    assert output["result"] == {"published": True}


def test_publish_stops_when_prepublish_fails(monkeypatch, capsys):
    api = OperationsApi()
    api.publish_error = SubstackAPIException(400, '{"error":"Draft is not ready"}')
    use_api(monkeypatch, api)

    assert cli.main(["drafts", "publish", "42", "--yes"]) == 1

    assert api.calls == [("prepublish", 42)]
    assert "Draft is not ready" in capsys.readouterr().err


def test_delete_interactive_confirmation(monkeypatch, capsys):
    api = OperationsApi()
    use_api(monkeypatch, api)
    monkeypatch.setattr(sys, "stdin", TTYInput("yes\n"))

    assert cli.main(["drafts", "delete", "42"]) == 0

    assert api.calls == [("delete", 42)]
    assert "Deleted draft 42" in capsys.readouterr().out


def test_delete_interactive_decline(monkeypatch, capsys):
    api = OperationsApi()
    use_api(monkeypatch, api)
    monkeypatch.setattr(sys, "stdin", TTYInput("no\n"))

    assert cli.main(["drafts", "delete", "42"]) == 2

    assert api.calls == []
    assert "Cancelled" in capsys.readouterr().err


def test_delete_yes_json_contract(monkeypatch, capsys):
    api = OperationsApi()
    use_api(monkeypatch, api)

    assert cli.main(["--json", "drafts", "delete", "42", "--yes"]) == 0

    assert json.loads(capsys.readouterr().out) == {
        "action": "delete",
        "draft_id": 42,
        "result": {"deleted": True},
    }
    assert api.calls == [("delete", 42)]


def test_json_error_redacts_secrets(monkeypatch, capsys):
    secret = "session-secret"
    api = OperationsApi()
    monkeypatch.setenv("COOKIES_STRING", secret)
    monkeypatch.setattr(
        api,
        "get_drafts",
        lambda **kwargs: (_ for _ in ()).throw(
            SubstackAPIException(401, json.dumps({"error": f"bad cookie {secret}"}))
        ),
    )
    use_api(monkeypatch, api)

    assert cli.main(["--json", "drafts", "list"]) == 1

    error = capsys.readouterr().err
    assert secret not in error
    assert "[redacted]" in error
    assert json.loads(error)["error"]["status_code"] == 401


def test_api_from_env_preserves_auth_precedence_and_publication_override(monkeypatch):
    calls = []
    monkeypatch.setenv("COOKIES_PATH", "environment-cookies.json")
    monkeypatch.setenv("COOKIES_STRING", "cookie=value")
    monkeypatch.setenv("EMAIL", "writer@example.com")
    monkeypatch.setenv("PASSWORD", "secret")
    monkeypatch.setenv("PUBLICATION_URL", "https://environment.substack.com")
    monkeypatch.setattr(cli, "Api", lambda **kwargs: calls.append(kwargs) or kwargs)

    result = cli._api_from_env(
        cookies_path="explicit-cookies.json",
        publication_url="https://selected.substack.com",
    )

    assert result == {
        "cookies_path": "explicit-cookies.json",
        "cookies_string": "cookie=value",
        "publication_url": "https://selected.substack.com",
    }
    assert calls == [result]


def test_api_from_env_uses_email_password_without_cookies(monkeypatch):
    calls = []
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.delenv("COOKIES_PATH", raising=False)
    monkeypatch.delenv("COOKIES_STRING", raising=False)
    monkeypatch.setenv("EMAIL", "writer@example.com")
    monkeypatch.setenv("PASSWORD", "secret")
    monkeypatch.setenv("PUBLICATION_URL", "https://writer.substack.com")
    monkeypatch.setattr(cli, "Api", lambda **kwargs: calls.append(kwargs) or kwargs)

    result = cli._api_from_env()

    assert result == {
        "email": "writer@example.com",
        "password": "secret",
        "publication_url": "https://writer.substack.com",
    }
    assert calls == [result]


def test_main_forwards_global_auth_and_publication_options(monkeypatch):
    api = OperationsApi()
    received = []
    monkeypatch.setattr(
        cli,
        "_api_from_env",
        lambda cookies_path=None, publication_url=None: (
            received.append((cookies_path, publication_url)) or api
        ),
    )

    assert (
        cli.main(
            [
                "--cookies",
                "cookies.json",
                "--publication-url",
                "https://selected.substack.com",
                "drafts",
                "get",
                "42",
            ]
        )
        == 0
    )

    assert received == [("cookies.json", "https://selected.substack.com")]

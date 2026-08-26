import json
import os
from datetime import datetime, timedelta, timezone

import pytest
from dotenv import load_dotenv

from substack import cli
from substack.post import Post

load_dotenv()


def _enabled():
    if os.getenv("RUN_SUBSTACK_CLI_E2E") != "1":
        return False
    has_cookies = bool(os.getenv("COOKIES_PATH") or os.getenv("COOKIES_STRING"))
    has_password = bool(os.getenv("EMAIL") and os.getenv("PASSWORD"))
    return bool(os.getenv("PUBLICATION_URL") and (has_cookies or has_password))


@pytest.mark.skipif(
    not _enabled(),
    reason="Set RUN_SUBSTACK_CLI_E2E=1 and configure Substack credentials.",
)
@pytest.mark.live
def test_cli_draft_lifecycle(monkeypatch, capsys):
    api = cli._api_from_env()
    post = Post("python-substack CLI smoke test", "Disposable draft", api.get_user_id())
    post.paragraph("This draft is created and deleted by the opt-in CLI smoke test.")
    draft = api.post_draft(post.get_draft())
    draft_id = draft["id"]

    monkeypatch.setattr(
        cli,
        "_api_from_env",
        lambda cookies_path=None, publication_url=None, timeout=None: api,
    )

    try:
        assert cli.main(["--json", "status"]) == 0
        assert cli.main(["--json", "publications", "list"]) == 0
        assert cli.main(["--json", "drafts", "list", "--limit", "10"]) == 0
        assert cli.main(["--json", "drafts", "get", str(draft_id)]) == 0

        scheduled_at = datetime.now(timezone.utc) + timedelta(days=1)
        assert (
            cli.main(
                [
                    "--json",
                    "drafts",
                    "schedule",
                    str(draft_id),
                    "--at",
                    scheduled_at.isoformat(),
                ]
            )
            == 0
        )
        assert cli.main(["--json", "drafts", "unschedule", str(draft_id)]) == 0
    finally:
        assert cli.main(["--json", "drafts", "delete", str(draft_id), "--yes"]) == 0
        capsys.readouterr()


@pytest.mark.skipif(
    not _enabled(),
    reason="Set RUN_SUBSTACK_CLI_E2E=1 and configure Substack credentials.",
)
@pytest.mark.live
def test_cli_create_markdown_draft(tmp_path, monkeypatch, capsys):
    api = cli._api_from_env()
    markdown = tmp_path / "cli-create.md"
    markdown.write_text(
        "# CLI create smoke test\n\nDisposable draft.", encoding="utf-8"
    )
    monkeypatch.setattr(
        cli,
        "_api_from_env",
        lambda cookies_path=None, publication_url=None, timeout=None: api,
    )

    assert cli.main(["--json", "drafts", "create", str(markdown)]) == 0
    created = json.loads(capsys.readouterr().out)
    draft_id = created["draft_id"]
    try:
        stored = api.get_draft(draft_id)
        assert stored["id"] == draft_id
    finally:
        api.delete_draft(draft_id)

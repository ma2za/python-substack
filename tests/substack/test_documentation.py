from pathlib import Path

import pytest
from markdown_it import MarkdownIt

from substack import cli
from substack.cli import main

ROOT = Path(__file__).parents[2]


@pytest.mark.parametrize("option", ["--help", "--version"])
def test_documented_installation_checks_do_not_authenticate(option):
    with pytest.raises(SystemExit) as exc:
        main([option])

    assert exc.value.code == 0


def test_local_markdown_links_exist():
    documents = [
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "SECURITY.md",
        *sorted((ROOT / "docs").rglob("*.md")),
    ]

    for document in documents:
        markdown = document.read_text(encoding="utf-8")
        for target in _local_markdown_targets(markdown):
            linked = document.parent / target
            assert linked.is_file(), f"{document.relative_to(ROOT)} -> {target}"


def _local_markdown_targets(markdown):
    for token in MarkdownIt("commonmark").parse(markdown):
        for child in token.children or []:
            if child.type == "link_open":
                target = child.attrs.get("href", "")
            elif child.type == "image":
                target = child.attrs.get("src", "")
            else:
                continue

            target = target.split("#", 1)[0]
            if target and "://" not in target and not target.startswith("#"):
                yield target


def test_pages_documents_have_front_matter():
    for document in sorted((ROOT / "docs").rglob("*.md")):
        markdown = document.read_text(encoding="utf-8")
        assert markdown.startswith("---\n"), document.relative_to(ROOT)
        assert "\nlayout: default\n" in markdown, document.relative_to(ROOT)


class DocumentationApi:
    publication_url = "https://example.substack.com/api/v1"

    def __init__(self):
        self.calls = []

    def get_user_profile(self):
        return {"id": 1, "email": "writer@example.com"}

    def get_user_publications(self):
        return [
            {
                "id": 2,
                "name": "Example",
                "subdomain": "example",
                "publication_url": "https://example.substack.com",
            }
        ]

    def get_publication_subscriber_count(self):
        return 3

    def create_draft_from_markdown(self, **kwargs):
        self.calls.append(("create", kwargs))
        return {"draft": {"id": 12345}, "tags": None}

    def get_drafts(self, **kwargs):
        self.calls.append(("list", kwargs))
        return []

    def schedule_draft(self, draft_id, scheduled_at):
        self.calls.append(("schedule", draft_id, scheduled_at.isoformat()))
        return {"scheduled": True}


def test_documented_cli_onboarding_examples(tmp_path, monkeypatch, capsys):
    getting_started = (ROOT / "docs" / "getting-started.md").read_text(encoding="utf-8")
    cli_guide = (ROOT / "docs" / "cli.md").read_text(encoding="utf-8")
    documented = getting_started + cli_guide
    for command in (
        "substack status",
        "substack drafts create first-draft.md",
        "substack publications list",
        "substack --publication-url https://example.substack.com drafts list",
        "substack drafts schedule 12345 --at 2030-01-02T09:00:00+01:00",
        "substack --json drafts list --limit 10",
    ):
        assert command in documented

    markdown = tmp_path / "first-draft.md"
    markdown.write_text("# My first automated draft\n\nBody", encoding="utf-8")
    api = DocumentationApi()
    received = []
    monkeypatch.setattr(
        cli,
        "_api_from_env",
        lambda cookies_path=None, publication_url=None, timeout=None: (
            received.append((cookies_path, publication_url, timeout)) or api
        ),
    )

    assert main(["status"]) == 0
    assert main(["drafts", "create", str(markdown)]) == 0
    assert main(["publications", "list"]) == 0
    assert (
        main(
            [
                "--publication-url",
                "https://example.substack.com",
                "drafts",
                "list",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "drafts",
                "schedule",
                "12345",
                "--at",
                "2030-01-02T09:00:00+01:00",
            ]
        )
        == 0
    )
    assert main(["--json", "drafts", "list", "--limit", "10"]) == 0

    capsys.readouterr()
    assert received[3] == (None, "https://example.substack.com", None)
    assert ("list", {"filter": "draft", "offset": 0, "limit": 10}) in api.calls
    assert (
        "schedule",
        12345,
        "2030-01-02T09:00:00+01:00",
    ) in api.calls

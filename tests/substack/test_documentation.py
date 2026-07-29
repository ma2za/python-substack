from pathlib import Path

import pytest
from markdown_it import MarkdownIt

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

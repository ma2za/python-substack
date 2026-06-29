"""End-to-end Markdown -> Substack draft round-trip test.

Reads a feature-complete Markdown fixture, creates a real draft via the API,
retrieves it, and compares the (normalised) stored document against a saved
golden file (``full_features.expected.json``).

Requires live credentials in the environment (a ``.env`` file is loaded):

  - ``COOKIES_STRING`` (or ``COOKIES_PATH``), **or** ``EMAIL`` + ``PASSWORD``
  - ``PUBLICATION_URL`` (optional but recommended)

The test is skipped when no credentials are configured, so it is safe to run in
CI without secrets.

To regenerate the golden file after an intentional change::

    python -m tests.substack.test_end_to_end --generate
"""

import copy
import json
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

from substack import Api
from substack.post import Post

load_dotenv()

FIXTURES = Path(__file__).parent / "fixtures"
MARKDOWN_FILE = FIXTURES / "full_features.md"
EXPECTED_FILE = FIXTURES / "full_features.expected.json"

TITLE = "python-substack e2e feature test"
SUBTITLE = "Automated round-trip fixture"


def _has_credentials() -> bool:
    """Whether auth is configured, checked without any network calls."""
    return bool(
        os.getenv("COOKIES_STRING")
        or os.getenv("COOKIES_PATH")
        or (os.getenv("EMAIL") and os.getenv("PASSWORD"))
    )


def _api_from_env() -> Api:
    cookies_string = os.getenv("COOKIES_STRING")
    cookies_path = os.getenv("COOKIES_PATH")
    publication_url = os.getenv("PUBLICATION_URL")
    if cookies_string or cookies_path:
        return Api(
            cookies_string=cookies_string,
            cookies_path=cookies_path,
            publication_url=publication_url,
        )
    return Api(
        email=os.getenv("EMAIL"),
        password=os.getenv("PASSWORD"),
        publication_url=publication_url,
    )


def _normalize(content):
    """Replace values that legitimately vary between runs (e.g. image URLs)."""

    def walk(node):
        if isinstance(node, dict):
            return {
                key: ("<SRC>" if key == "src" else walk(value))
                for key, value in node.items()
            }
        if isinstance(node, list):
            return [walk(item) for item in node]
        return node

    return walk(copy.deepcopy(content))


def _roundtrip(api: Api):
    """Post the fixture as a draft, read it back, and return normalised content."""
    markdown = MARKDOWN_FILE.read_text(encoding="utf-8")
    post = Post(TITLE, SUBTITLE, user_id=api.get_user_id())
    post.from_markdown(markdown)
    draft = api.post_draft(post.get_draft())
    draft_id = draft.get("id")
    try:
        stored = api.get_draft(draft_id)
        body = stored.get("draft_body")
        if isinstance(body, str):
            body = json.loads(body)
        return _normalize(body["content"])
    finally:
        try:
            api.delete_draft(draft_id)
        except Exception:
            pass


@pytest.mark.skipif(not _has_credentials(), reason="no Substack credentials configured")
def test_full_features_roundtrip():
    api = _api_from_env()
    actual = _roundtrip(api)
    expected = json.loads(EXPECTED_FILE.read_text(encoding="utf-8"))
    assert actual == expected


def _generate():
    """Regenerate the golden file from a live round-trip."""
    if not _has_credentials():
        raise SystemExit("No credentials configured; cannot generate golden file.")
    api = _api_from_env()
    content = _roundtrip(api)
    EXPECTED_FILE.write_text(
        json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {EXPECTED_FILE}")


if __name__ == "__main__":
    if "--generate" in sys.argv:
        _generate()
    else:
        print(__doc__)

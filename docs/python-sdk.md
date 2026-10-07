---
layout: default
title: Python SDK
---

# Python SDK

Use `Api.create_draft_from_markdown` for the same draft-only workflow as the
CLI:

```python
import os

from dotenv import load_dotenv
from substack import Api

load_dotenv()

api = Api(
    cookies_path=os.getenv("COOKIES_PATH"),
    publication_url=os.getenv("PUBLICATION_URL"),
)

result = api.create_draft_from_markdown(
    title="Shipping with Python",
    subtitle="A draft created from a script",
    markdown="# Hello\n\nThis is **Markdown**.",
    tags=["python", "automation"],
)

print(result["draft"]["id"])
```

The method creates an unpublished draft by default. It publishes only when
`publish=True` is passed. It can also set audience, comment permissions, SEO
metadata, slug, section, and tags.

## Export a draft without modifying it

```python
from pathlib import Path

result = api.export_draft_to_markdown(12345)

Path("backup.md").write_text(result["markdown"], encoding="utf-8")
print(result["unsupported_nodes"])
```

The result contains the original `draft`, exported `markdown`, and an
`unsupported_nodes` list. The method performs one draft read and no server
writes. Unsupported editor nodes remain embedded in the Markdown as opaque,
decodable markers.

For supported syntax, see the [Markdown reference](markdown.md). For direct
editor-node construction, see the [low-level Python API](low-level-api.md).

## Update a draft safely

Preview an update before writing it:

```python
preview = api.update_draft_from_markdown(
    12345,
    "# Revised title\n\nUpdated body.",
    dry_run=True,
)
print(preview["payload"])
```

Run the same call without `dry_run=True` to write the update. Unsupported
editor nodes exported as `python-substack-node:v1` markers are preserved by
default. Removing or changing them raises `ValueError` unless
`allow_unsupported_change=True` is deliberately supplied. Similarly, image
replacements that cannot resolve to their original remote source require
`allow_image_replacement=True`.

The method verifies the revision fingerprint from `python-substack-revision:v1`
markers before updating. If the remote draft changed after export, it raises
`DraftConflictError` unless `allow_conflict=True` (or `force=True`) is passed.
Files lacking revision metadata are treated as unprotected updates and also
require `allow_conflict=True`. In dry-run mode (`dry_run=True`), conflict
status and specific mismatch details are returned in `preview["conflict"]` and
`preview["mismatches"]`.

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

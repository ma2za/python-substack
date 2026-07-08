# Python Substack

Unofficial Python tools for publishing to [Substack](https://substack.com/).

[![Downloads](https://static.pepy.tech/badge/python-substack/month)](https://pepy.tech/project/python-substack)
![Release Build](https://github.com/ma2za/python-substack/actions/workflows/ci_publish.yml/badge.svg)

## Features

- Create drafts and publish posts from Python.
- Convert Markdown into Substack's editor document format.
- Upload local images while rendering Markdown.
- Set audience, comment permissions, SEO title, SEO description, slug, sections, and tags.
- Publish now, schedule drafts, or keep drafts unpublished by default.
- Authenticate with email/password, cookies JSON, or a browser cookie string.
- Run a FastMCP server for AI-assisted publishing workflows.

## Installation

```bash
pip install python-substack
```

Install the MCP server extra:

```bash
pip install "python-substack[mcp]"
```

## Setup

Copy `.env.example` to `.env` and fill in one authentication method:

```env
EMAIL=
PASSWORD=
PUBLICATION_URL=
COOKIES_PATH=
COOKIES_STRING=
```

Use either `EMAIL` and `PASSWORD`, or cookie-based authentication with `COOKIES_PATH` or `COOKIES_STRING`. Cookie authentication is usually the better option if Substack prompts for captcha or magic-link sign-in.

Newer Substack accounts may only have magic-link sign-in enabled. To set a password, sign out of Substack, choose "Sign in with password", then choose "Set a new password".

## Quickstart

```python
import os

from dotenv import load_dotenv
from substack import Api

load_dotenv()

api = Api(
    email=os.getenv("EMAIL"),
    password=os.getenv("PASSWORD"),
    publication_url=os.getenv("PUBLICATION_URL"),
)

result = api.create_draft_from_markdown(
    title="Shipping with Python",
    subtitle="A short note from a script",
    markdown="""
# Hello

This draft was created from **Markdown**.

![Alt text](https://example.com/image.png "Image caption")
""",
    tags=["python", "automation"],
    slug="shipping-with-python",
)

print(result["draft"]["id"])
```

`create_draft_from_markdown` creates a draft by default. It only publishes when `publish=True` is passed.

## CLI

Check authentication without creating a draft:

```bash
substack-auth-check
```

With a cookies JSON file:

```bash
substack-auth-check --cookies cookies.json
```

Publish a Markdown file as a draft:

```bash
substack-publish-markdown post.md --title "My Post"
```

Create and publish:

```bash
substack-publish-markdown post.md --title "My Post" --publish
```

Publish from YAML:

```bash
substack-publish-yaml draft.yaml
```

Useful options:

```bash
substack-publish-markdown post.md \
  --title "My Post" \
  --subtitle "Optional subtitle" \
  --tag python \
  --tag substack \
  --slug my-post \
  --search-engine-title "SEO title" \
  --search-engine-description "SEO description"
```

## Cookie Authentication

Cookie authentication avoids logging in with email/password on every run and helps when Substack requires captcha or magic-link sign-in.

Use a cookies JSON file:

```python
import os

from dotenv import load_dotenv
from substack import Api

load_dotenv()

api = Api(
    cookies_path=os.getenv("COOKIES_PATH"),
    publication_url=os.getenv("PUBLICATION_URL"),
)
```

Or paste a browser cookie header into `COOKIES_STRING`:

```python
import os

from dotenv import load_dotenv
from substack import Api

load_dotenv()

api = Api(
    cookies_string=os.getenv("COOKIES_STRING"),
    publication_url=os.getenv("PUBLICATION_URL"),
)
```

To get a cookie string:

1. Sign in to Substack in your browser.
2. Open developer tools.
3. Go to the network tab and refresh Substack.
4. Select a request such as `subscription/unred/subscriptions`.
5. Copy the full `cookie` request header value into `COOKIES_STRING`.

To export a working session to a cookies JSON file:

```python
api.export_cookies("cookies.json")
```

Then set:

```env
COOKIES_PATH=cookies.json
```

The CLI also accepts a cookie JSON path:

```bash
substack-publish-markdown post.md --cookies cookies.json
```

## Low-Level Post Builder

```python
import os

from dotenv import load_dotenv
from substack import Api
from substack.post import Post

load_dotenv()

api = Api(
    email=os.getenv("EMAIL"),
    password=os.getenv("PASSWORD"),
    publication_url=os.getenv("PUBLICATION_URL"),
)

user_id = api.get_user_id()

post = Post(
    title="How to publish a Substack post using Python",
    subtitle="Created with python-substack",
    user_id=user_id,
    audience="everyone",
    write_comment_permissions="everyone",
)

post.paragraph("This is a paragraph.")
post.add(
    {
        "type": "paragraph",
        "content": [
            {"content": "A link to "},
            {
                "content": "Substack",
                "marks": [{"type": "link", "href": "https://substack.com"}],
            },
        ],
    }
)
post.add({"type": "paywall"})
post.add({"type": "captionedImage", "src": "https://example.com/image.png"})

draft = api.post_draft(post.get_draft())
api.prepublish_draft(draft.get("id"))
api.publish_draft(draft.get("id"))
```

## Markdown Support

```python
from substack.post import Post

post = Post("Title", "Subtitle", user_id=1)
post.from_markdown(
    """
# Heading

Paragraph with **bold**, *italic*, `code`, [links](https://example.com), and footnotes.[^1]

- Lists
- Images

![Alt](local-image.png "Caption")

[^1]: Footnote text.
"""
)
```

Supported Markdown includes headings, paragraphs, bold, italic, inline code, strikethrough, links, images, linked images, image captions, code blocks, blockquotes, ordered lists, unordered lists, horizontal rules, and footnotes.

When an `Api` instance is passed to `from_markdown`, local image paths are uploaded before the draft is created:

```python
post.from_markdown(markdown_content, api=api)
```

## YAML Drafts

```yaml
title: "My Post Title"
subtitle: "My Post Subtitle"
audience: "everyone"
write_comment_permissions: "everyone"
search_engine_title: "SEO title"
search_engine_description: "SEO description"
slug: "my-post-title"
tags:
  - python
  - substack
markdown: |
  # Introduction

  This post body is Markdown.
```

The lower-level node format is also supported:

```yaml
title: "My Post Title"
subtitle: "My Post Subtitle"
body:
  0:
    type: "heading"
    level: 1
    content: "Introduction"
  1:
    type: "paragraph"
    content: "This is a paragraph."
  2:
    type: "captionedImage"
    src: "local_image.jpg"
```

## MCP Server

Install the MCP extra:

```bash
pip install "python-substack[mcp]"
```

Run the server over stdio:

```bash
substack-mcp
```

Equivalent Python entry point:

```bash
python -c "from substack_mcp.mcp_server import main; main()"
```

Available tools:

- `post_draft_from_markdown(...)`
- `put_draft(draft_id, update_payload)`
- `add_tags(draft_id, tags)`
- `prepublish_draft(draft_id)`
- `publish_draft(draft_id, send=True, share_automatically=False)`

## Development

```bash
pip install pre-commit
pre-commit install
pytest
```

Live Substack tests are opt-in. Set `RUN_SUBSTACK_E2E=1` and configure credentials before running them.

Release changes are tracked in [CHANGELOG.md](CHANGELOG.md).

## Disclaimer

This project is not affiliated with Substack.

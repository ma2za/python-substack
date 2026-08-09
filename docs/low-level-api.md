---
layout: default
title: Low-level Python API
---

# Low-level Python API

Most callers should use `Api.create_draft_from_markdown`. The `Post` builder is
available for direct construction of Substack editor nodes.

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

post = Post(
    title="How to publish a Substack post using Python",
    subtitle="Created with python-substack",
    user_id=api.get_user_id(),
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
api.prepublish_draft(draft["id"])
api.publish_draft(draft["id"])
```

The final three calls write to Substack. `post_draft` creates an unpublished
draft. `publish_draft` publishes it and should be called only after review.

The node schema is undocumented upstream and may change. Prefer the Markdown
renderer when it supports the content being authored.

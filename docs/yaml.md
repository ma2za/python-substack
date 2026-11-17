---
layout: default
title: YAML drafts
---

# YAML drafts

The compatibility command `substack-publish-yaml` accepts Markdown-oriented
YAML:

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

The Markdown can also live in a separate file:

```yaml
title: "My Post Title"
markdown_file: "post.md"
```

Relative Markdown paths resolve from the YAML file's directory.

Relative local image paths resolve from the current working directory. An
image that is not found there is also looked up in the Markdown file's folder,
or in the YAML file's folder when the Markdown is inline.

The lower-level node form remains supported:

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

Create a draft:

```bash
substack-publish-yaml draft.yaml
```

Publish only when explicitly requested:

```bash
substack-publish-yaml draft.yaml --publish --no-send
```

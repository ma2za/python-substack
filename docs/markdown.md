---
layout: default
title: Markdown support
---

# Markdown support

`Post.from_markdown(markdown_content, api=None)` converts a Markdown document
into Substack's document format. Parsing is handled by
[markdown-it-py](https://github.com/executablebooks/markdown-it-py) (CommonMark)
plus a few plugins, so standard CommonMark works as you'd expect. This page
documents everything that maps to a Substack node.

```python
from substack.post import Post

post = Post(title="My Post", subtitle="", user_id=api.get_user_id())
post.from_markdown(open("post.md").read(), api=api)
draft = api.post_draft(post.get_draft())
```

Pass `api=` when your Markdown references local images so they can be uploaded
(see [Images](#images)); it is optional otherwise.

## Text formatting

| Markdown                      | Result            |
|-------------------------------|-------------------|
| `**bold**`                    | **bold**          |
| `*italic*`                    | *italic*          |
| `***bold italic***`           | ***bold italic*** |
| `` `inline code` ``           | `inline code`     |
| `~~strikethrough~~`           | ~~strikethrough~~ |
| `^superscript^`               | superscript       |
| `~subscript~`                 | subscript         |
| `[text](https://example.com)` | link              |
| `<https://example.com>`       | autolinked URL    |

Note that subscript uses a single tilde (`~x~`) and strikethrough uses a double
tilde (`~~x~~`); both work in the same document.

## Headings

Levels 1–6, using `#` through `######`. Headings may contain inline formatting
and links.

```markdown
# Heading level 1
## Heading level 2 with **bold** and a [link](https://example.com)
```

## Paragraphs and line breaks

Blank lines separate paragraphs. A single newline within a paragraph is treated
as a space (soft break), matching CommonMark.

## Lists

Bullet lists (`-`, `*`, or `+`) and ordered lists (`1.`), including nesting:

```markdown
- Bullet one
- Bullet two
  - Nested bullet
  1. Nested number

1. Ordered one
2. Ordered two
```

## Blockquotes

```markdown
> A blockquote.
>
> With multiple paragraphs.
```

## Code blocks

Fenced code blocks, with an optional language for syntax highlighting, and
indented code blocks:

````markdown
```python
print("hello")
```
````

## Horizontal rule

```markdown
---
```

## Images

A paragraph containing only an image becomes a captioned image.

```markdown
![Alt text](https://example.com/image.png)
```

- **Caption:** use the CommonMark title slot — `![alt](url "caption text")`.
- **Link:** wrap the image in a link — `[![alt](url)](https://target.com)`.
- **Local upload:** if `api=` is passed and the `src` is a local path (not an
  `http(s)` URL), the file is uploaded to Substack and the returned URL is used.
  Absolute paths are preserved, `~` expands to the user's home directory, and
  relative paths resolve from the current working directory. A leading `/` is
  removed only as a legacy fallback when the absolute file does not exist and
  the corresponding relative file does. Missing files and failed uploads raise
  an error naming the file instead of silently saving a broken image.
  PNG, JPEG, GIF, and WebP are uploaded without conversion, including animations.
  HTTP(S) and protocol-relative URLs remain unchanged. Without `api=`, image
  sources remain unchanged and no files are uploaded or checked for existence.
  Rendering with `api=` can upload images even during a draft update's dry run.

```markdown
![A chart](chart.png "Figure 1: quarterly results")
```

## Footnotes

References become inline anchors; definitions become footnote blocks at the end,
numbered by order of first appearance. Labels may be numeric or named, and a
definition may contain block content such as lists or multiple paragraphs.

```markdown
A claim that needs support.[^1] Another, with a named label.[^source]

[^1]: The supporting detail, with a [link](https://example.com).
[^source]: Author, *Title* (2025).
```

A reference used more than once is emitted as a separate numbered anchor each
time, mirroring the Substack editor. Definitions that are never referenced are
dropped.

## Math (LaTeX)

Inline math with single dollars, block math with double dollars:

```markdown
Einstein showed $E=mc^2$ inline.

$$
\int_0^\infty e^{-x} \, dx = 1
$$
```

Delimiters follow Pandoc's rules: the opening `$` must not be followed by
whitespace, and the closing `$` must not be preceded by whitespace or followed
by a digit. Ordinary dollar amounts (`$5 million to $10 million`) therefore
stay plain text. A label after a block (`$$ ... $$ (label)`) is accepted but
discarded, since Substack has no equation labels. Unclosed math delimiters remain
plain text.

## Pull quotes and callouts

These use fenced-container syntax (`:::`), since they have no native Markdown
equivalent:

```markdown
:::pullquote
A highlighted pull quote. **Formatting** works inside.
:::

:::callout
A callout block, e.g. an aside or note.
:::
```

Empty pull quotes and callouts produce an empty paragraph so the resulting
document remains valid. Unknown `:::` container names remain ordinary text.

## Not supported

- **Tables** — Substack has no table renderer or editor UI for them, so GFM
  table syntax is not converted. To include tabular data, embed a chart (for
  example via [Datawrapper](https://support.substack.com/hc/en-us/articles/15722290158100))
  and add it in the Substack editor.
- Widgets authored only in the Substack editor (buttons, polls, embeds, etc.)
  have no Markdown equivalent.

## Draft export and opaque nodes

`Api.export_draft_to_markdown(draft_id)` and `substack drafts export DRAFT_ID`
reverse supported Substack nodes into Markdown. The export is read-only and
returns every unsupported node separately in `unsupported_nodes`.

Unsupported nodes and supported nodes with unknown fields are also kept at
their document position as:

```text
<!-- python-substack-node:v1 BASE64URL_JSON -->
```

The payload is UTF-8 JSON encoded with URL-safe base64 and no padding. This
makes unsupported content visible and recoverable instead of silently dropping
it. `Api.update_draft_from_markdown` and `substack drafts update` recognize
valid markers and preserve the corresponding nodes. They refuse updates that
remove, duplicate, or alter remote unsupported nodes unless the caller
explicitly authorizes that change with `allow_unsupported_change=True` or
`--allow-unsupported-change --yes`.

Export preserves the Markdown meaning of supported images: source, alt text,
link, and plain-text caption. In addition, images are exported with an immediate:

```text
<!-- python-substack-image:v2 BASE64URL_JSON -->
```

The payload binds the image to its original remote source and preserves
editor layout and non-owned attributes (such as alignment, dimensions,
watermark, and unrecognized attributes). Markdown remains authoritative for
`src`, `alt`, `href`, and caption. Changed image sources resolve to their bound
remote image and restore those attributes safely. Stale, corrupt, duplicate,
reused, or non-adjacent markers are rejected. Unmatched image replacements require
`allow_image_replacement=True` or `--allow-image-replacement --yes`. Legacy `v1`
image markers remain supported when the image source resolves to exactly one
remote image.

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
  Local paths resolve relative to the current working directory.

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

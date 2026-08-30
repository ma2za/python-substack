---
layout: default
title: Safety and publishing behavior
---

# Safety and publishing behavior

Creating, scheduling, publishing, and deleting are separate operations.

| Operation | Effect | Confirmation |
|---|---|---|
| `drafts export` | Reads a draft and produces Markdown | None |
| `drafts create` | Creates an unpublished draft | None |
| `drafts schedule` | Adds a future release time | None |
| `drafts unschedule` | Removes a future release time | None |
| `drafts publish` | Publishes after a prepublish check | Interactive or `--yes` |
| `drafts delete` | Deletes the draft | Interactive or `--yes` |

`drafts publish --no-send` publishes without email delivery. Omitting
`--no-send` allows Substack to send the post. Review the draft ID and flags
before confirming.

In JSON or noninteractive mode, publish and delete reject the request unless
`--yes` is supplied. API errors redact configured passwords and cookie values
before they are printed by the CLI.

Substack's interfaces are undocumented and may change. Keep a reviewed copy of
important source Markdown and verify the selected publication with
`substack status` before any write.

Export never writes to Substack and never overwrites a local file unless
`--force` is supplied. Unsupported editor content is preserved as an opaque
marker and listed in JSON output so it cannot disappear unnoticed.

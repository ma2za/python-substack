---
layout: default
title: Unified CLI
---

# Unified CLI

Global options such as `--json`, `--cookies`, and `--publication-url` must
appear before the command.

## Create an unpublished draft

```bash
substack drafts create post.md
```

The title comes from the first Markdown heading, then the filename if the file
has no heading. Use `--title` to override it.

## Select a publication

List every publication available to the authenticated account:

```bash
substack publications list
```

Select one for a single command:

```bash
substack --publication-url https://example.substack.com drafts list
```

## Schedule an existing draft

Pass an ISO 8601 timestamp with a timezone offset or `Z`:

```bash
substack drafts schedule 12345 --at 2030-01-02T09:00:00+01:00
```

Remove the schedule without deleting the draft:

```bash
substack drafts unschedule 12345
```

## Stable JSON for automation

```bash
substack --json drafts list --limit 10
```

The command writes a JSON object containing `drafts`, `count`, `filter`,
`offset`, and `limit`. Errors are also JSON when `--json` is present.

## Publish and delete

```bash
substack drafts publish 12345 --no-send
substack drafts delete 12345 --yes
```

Publishing and deletion require confirmation. JSON and noninteractive
workflows must pass `--yes`. Publishing runs Substack's prepublish check first.
See [safety and publishing behavior](safety.md).

The original console scripts remain supported. See
[legacy CLI commands](legacy-cli.md).

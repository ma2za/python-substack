---
layout: default
title: Troubleshooting
---

# Troubleshooting

## The command asks for credentials

Run commands from the directory containing `.env`, or export the required
environment variables. Use one cookie method or `EMAIL` and `PASSWORD`. See
[authentication and cookies](authentication.md).

## Password login fails or requests a magic link

Use a browser cookie file or cookie header string. Cookie authentication reuses
an already authenticated browser session and is usually more reliable when
Substack requires captcha or magic-link sign-in.

## The wrong publication is selected

```bash
substack publications list
substack --publication-url https://example.substack.com status
```

Set `PUBLICATION_URL` to make the selection persistent for the current
environment.

## A schedule timestamp is rejected

Include an explicit timezone offset or `Z`. For example:

```bash
substack drafts schedule 12345 --at 2030-01-02T09:00:00Z
```

## Publishing or deletion requires `--yes`

Interactive terminal sessions prompt for confirmation. JSON output and other
noninteractive sessions cannot prompt, so pass `--yes` explicitly after
checking the draft ID.

## A local image does not upload

Pass the authenticated `Api` instance to `Post.from_markdown(..., api=api)` or
use `Api.create_draft_from_markdown`, which does this automatically. Relative
image paths resolve from the current working directory.

If the problem persists, open an issue using the repository's
[authentication bug form](https://github.com/ma2za/python-substack/issues/new?template=auth_bug.yml)
or [feature request form](https://github.com/ma2za/python-substack/issues/new?template=feature_request.yml).

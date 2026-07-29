# MCP server

Install the optional dependency and start the stdio server:

```bash
pip install "python-substack[mcp]"
substack-mcp
```

Equivalent Python entry point:

```bash
python -c "from substack_mcp.mcp_server import main; main()"
```

The server uses the same `EMAIL`, `PASSWORD`, `PUBLICATION_URL`,
`COOKIES_PATH`, and `COOKIES_STRING` environment variables as the SDK.

Available tools:

- `post_draft_from_markdown(...)`
- `put_draft(draft_id, update_payload)`
- `add_tags(draft_id, tags)`
- `prepublish_draft(draft_id)`
- `publish_draft(draft_id, send=True, share_automatically=False)`

`post_draft_from_markdown` creates an unpublished draft unless `publish=True`
is explicitly supplied. `publish_draft` publishes immediately and defaults to
sending email. Review the draft ID and arguments before invoking it.

The server currently exposes the compatibility tools listed above.

---
layout: default
title: MCP server
---

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

## Available Tools

The server exposes tools for reading content, managing drafts, and publishing.

**Read Operations (Safe to run automatically):**
- `get_status()` - Verify authentication and get basic user/publication information.
- `list_publications()` - List all publications you have access to.
- `list_drafts(filter="draft", offset=0, limit=25)` - View recent drafts.
- `get_draft(draft_id)` - Read the content and metadata of a specific draft.

**Draft Creation and Reversible Writes:**
- `post_draft_from_markdown(...)` - Creates an unpublished draft from Markdown.
- `put_draft(draft_id, update_payload)` - Update draft metadata (e.g. slug).
- `add_tags(draft_id, tags)` - Attach tags to a draft.
- `prepublish_draft(draft_id)` - Run Substack's pre-publication checks on a draft.
- `schedule_draft(draft_id, at)` - Schedule a draft for publication at an ISO timestamp.
- `unschedule_draft(draft_id)` - Remove a publication schedule from a draft.

**Publishing Operations (Use with caution):**
- `publish_draft_checked(draft_id, confirm=False, send=False, share_automatically=False)` - **Recommended**. A safer publishing path that requires explicit confirmation (`confirm=True`), runs prepublish checks automatically, and defaults to *not* sending emails.
- `publish_draft(draft_id, send=True, share_automatically=False)` - *Legacy compatibility interface*. Publishes immediately and defaults to sending email.

## Client Configuration Examples

### Claude Desktop

You can configure Claude Desktop to use `python-substack` as an MCP server by adding it to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "substack": {
      "command": "substack-mcp",
      "env": {
        "EMAIL": "your-email@example.com",
        "PASSWORD": "your-password"
      }
    }
  }
}
```

If you prefer to use session cookies instead of a password, use the `COOKIES_STRING` variable:

```json
{
  "mcpServers": {
    "substack": {
      "command": "substack-mcp",
      "env": {
        "COOKIES_STRING": "cookie1=value1; cookie2=value2"
      }
    }
  }
}
```

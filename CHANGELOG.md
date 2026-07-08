# Changelog

## 0.1.25

### Added

- Markdown-first draft helper: `Api.create_draft_from_markdown(...)`.
- CLI commands:
  - `substack-auth-check`
  - `substack-publish-markdown`
  - `substack-publish-yaml`
  - `substack-mcp`
- Optional MCP extra: `python-substack[mcp]`.
- `.env.example` for setup.
- GitHub issue templates for auth bugs and feature requests.

### Fixed

- Include `substack_mcp` in packaged distributions.
- Fix `examples/publish_post.py --publish` so the flag publishes.
- Correct MCP documentation to use `substack_mcp.mcp_server`.

### Improved

- Reworked README around Markdown, cookie auth, CLI usage, and MCP setup.
- Added PyPI classifiers and project links.
- Added focused tests for CLI behavior and Markdown draft creation.

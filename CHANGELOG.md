# Changelog

## 0.1.26

### Added

- Unified `substack` CLI for publication status and draft operations.
- Commands to list publications, inspect drafts, schedule, unschedule, publish, and delete.
- Stable `--json` output for automation and `--publication-url` overrides.
- Interactive confirmation and non-interactive `--yes` protection for publishing and deletion.
- Pull-request CI across Python 3.10 through 3.14.

### Improved

- Clear CLI error output, exit codes, timezone validation, and secret redaction.
- Package positioning, keywords, operational examples, and release validation.
- PyPI publishing now uploads the exact tested wheel and source distribution.

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

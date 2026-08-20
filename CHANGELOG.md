# Changelog

## 0.4.0

### Added

- Seven new MCP tools for read operations and safe publishing: `get_status`, `list_publications`, `list_drafts`, `get_draft`, `schedule_draft`, `unschedule_draft`, and `publish_draft_checked`.
- Pre-publish validation, interactive confirmation requirements, and no-email defaults for the new `publish_draft_checked` MCP tool.
- Verified MCP client configuration examples in `docs/mcp.md`.
- Documentation for Gemini CLI with Vertex AI (`docs/gemini-vertex-ai.md`).

### Improved

- Simplify MCP draft creation by routing through the existing `Api.create_draft_from_markdown` SDK helper, preserving response format.
- Document the legacy `publish_draft` MCP tool as the compatibility interface.
- Bump `cryptography` dependency from `48.0.1` to `50.0.0` (#68).

## 0.3.0

### Added

- GitHub Pages documentation with a task-oriented index for installation,
  authentication, CLI, Python, Markdown, MCP, safety, and troubleshooting.
- A five-minute Markdown-to-unpublished-draft walkthrough using the existing
  before and after images.
- Tested examples for draft creation, scheduling, publication selection,
  stable JSON automation, and cookie authentication verification.
- A documentation project link in package metadata and repository navigation.

### Improved

- Add Jekyll front matter to existing documentation while preserving every
  previous documentation path.
- Keep creating, scheduling, publishing, and deleting clearly separated in the
  onboarding and safety guides.

No runtime interface changed in this release.

## 0.2.0

### Added

- Outcome-focused documentation for authentication, legacy CLI commands,
  low-level Python construction, YAML drafts, MCP, compatibility, security,
  contributing, and adoption metrics.
- Offline tests for the documented unauthenticated installation checks and
  local documentation links.
- A documented compatibility commitment covering the Python API, five console
  scripts, unified CLI, JSON keys, environment variables, and MCP tools.

### Improved

- Reposition the package around safe writer-side Markdown automation.
- Put the unpublished draft workflow and publishing safeguards first in the
  README.
- Classify the package as Beta after four years of compatible releases.
- Update pre-commit, formatting, and import-sorting hooks to current verified
  releases.
- Validate the hook runner as a locked development dependency.
- Publish through short-lived PyPI Trusted Publishing credentials instead of a
  long-lived API token.

Existing Python APIs, CLI commands, console scripts, defaults, JSON contracts,
environment variables, and MCP tools remain unchanged.

## 0.1.27

### Added

- Unified `substack drafts create MARKDOWN_FILE` command for safe draft-only Markdown creation.
- Markdown rendering for LaTeX, superscript, subscript, pull quotes, and callouts.
- Registered `live` test marker with documented opt-in API and CLI smoke commands.

### Fixed

- Support Substack subscriber responses that provide a `subscribers` list instead of `subscriberCount`.
- Use Substack's current scheduled-release endpoint for scheduling and unscheduling drafts.
- Retry rate-limited GET and DELETE requests with bounded backoff without retrying write-producing POST requests.

### Improved

- Validate offline tests separately from live integrations.
- Validate wheel metadata, console entry points, base installations, and MCP-extra installations on Python 3.10 and 3.14.
- Require release tags, package metadata, and `substack.__version__` to agree before publishing.

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

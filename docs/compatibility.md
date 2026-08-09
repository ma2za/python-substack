---
layout: default
title: Compatibility policy
---

# Compatibility policy

python-substack preserves its established public interfaces while progressing
to 1.0 and throughout the 1.x series.

## Supported public contracts

- `substack.Api` and `substack.post.Post`.
- Existing public method names, argument meanings, and defaults.
- Console commands:
  - `substack`
  - `substack-auth-check`
  - `substack-publish-markdown`
  - `substack-publish-yaml`
  - `substack-mcp`
- Existing unified CLI commands, flags, confirmation behavior, and exit codes.
- Existing keys in documented JSON output.
- Environment variables:
  - `EMAIL`
  - `PASSWORD`
  - `PUBLICATION_URL`
  - `COOKIES_PATH`
  - `COOKIES_STRING`
- Existing MCP tool names, arguments, and defaults.

New optional arguments, commands, methods, tools, and JSON fields may be added.

## Deprecation

An established interface may be documented as deprecated, but it will not be
removed before 2.0. Deprecated behavior remains tested while it is supported.
Legacy console commands remain supported throughout 1.x.

## Upstream behavior

Substack does not provide a stable public API for the operations used by this
package. Compatible fixes for upstream endpoint or response changes may alter
internal requests while preserving the package's documented behavior.

Operations that write, publish, send, or delete content remain explicit.
Draft creation remains unpublished by default.

## Version support

The supported Python versions are declared in `pyproject.toml` and on PyPI.
Continuous integration tests every declared minor version. Security and
compatibility fixes target the latest python-substack release.

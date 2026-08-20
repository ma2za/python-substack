# python-substack maintainer instructions

## Project

This repository is a Python 3.10+ library, CLI, and optional MCP server for
creating and managing Substack drafts from Markdown. Poetry owns dependencies,
packaging, scripts, and the lock file. The public package is `python-substack`.

Read the relevant implementation, tests, and documentation before editing.
Keep changes focused and preserve existing public interfaces, defaults, JSON
keys, environment variables, console scripts, and MCP tool signatures through
the 1.x series as required by `docs/compatibility.md`.

## Development

- Use the existing style and the simplest working implementation.
- Add a regression test for every bug fix and offline tests for new behavior.
- Update user-facing documentation and `CHANGELOG.md` for behavior changes.
- Do not edit `poetry.lock` unless dependency declarations change.
- Never expose or commit `.env` contents, passwords, cookies, credentials,
  tokens, captured request headers, or local service-account files.
- Preserve user changes in a dirty worktree. Do not reset, restore, or delete
  unrelated work.

Install and validate with:

```bash
poetry install --all-extras
poetry run pytest -q -m "not live" --strict-markers
poetry run pre-commit run --all-files
```

Live tests call Substack and create disposable drafts. Run them only after the
maintainer explicitly authorizes the live operation and confirms suitable test
credentials. Live tests must never publish, and their drafts must be removed.

## Releases

Follow `docs/releasing.md` exactly. Use `/release:prepare X.Y.Z` to prepare a
candidate and `/release:verify` to validate it.

- Keep both version files unchanged during ordinary development.
- For a release candidate, synchronize `pyproject.toml` and
  `substack/__init__.py`, prepend `CHANGELOG.md`, and add
  `docs/releases/X.Y.Z.md` using only verified changes.
- Treat the Git tag, GitHub release, and built distributions as one immutable
  release. Never reuse a published version.
- Do not commit, tag, push, create a GitHub release, publish to PyPI, run live
  tests, or announce a release without explicit maintainer authorization for
  that action.
- Never bypass a failing check. Report the failure and preserve its output.
- Publish only from the exact commit that passed CI, using tag `vX.Y.Z`.

At handoff, state files changed, checks run, checks not run, and any external
actions still requiring maintainer approval.

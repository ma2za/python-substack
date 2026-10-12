# Cloud development handover

Repository: <https://github.com/ma2za/python-substack>, branch `main`.
The repository remains public. Package version: `0.10.0`.

## Environment setup

Use Python 3.10 or newer; Python 3.12 is recommended for the cloud environment.
The CI matrix covers Python 3.10 through 3.14. Git and Bash are required.

Run this from the checkout as the cloud environment's install script:

```bash
bash scripts/codex-cloud-setup.sh
```

The script installs Poetry 2.3.2 in `.tools/poetry`, installs the locked project
dependencies and all extras in `.venv`, and installs the pre-commit hook. It
requires package-registry access. It can be rerun on an existing checkout.
No credentials or external services are required for development setup.

In each new shell, make the isolated Poetry executable available:

```bash
export PATH="$PWD/.tools/poetry/bin:$PATH"
```

The setup is checked into Git; no workstation virtual environment, editor
configuration, or shared parent-directory `.env` is needed.

## Validation

```bash
poetry run pytest -q -m "not live" --strict-markers
poetry run pytest -q --strict-markers
poetry run pre-commit run --all-files
poetry check
poetry build
poetry run python -m twine check dist/*
```

Keep `RUN_SUBSTACK_E2E` and `RUN_SUBSTACK_CLI_E2E` unset for ordinary development.
The first test command excludes live tests; the second verifies they skip with
live opt-ins unset. Live tests create and delete real Substack drafts and need
explicit authorization for the operation. Follow [CONTRIBUTING.md](CONTRIBUTING.md)
and [docs/releasing.md](docs/releasing.md) before any live or release work.

## Authentication

Offline tests and package validation need no Substack credentials. For an
authorized live task, configure fresh values in the cloud environment:

- `PUBLICATION_URL`: the publication selected for the task.
- `COOKIES_STRING`: a cookie string, or `COOKIES_PATH`: a cookie file supplied
  within that environment.
- Alternatively, `EMAIL` and `PASSWORD` for password authentication.

Use the environment's protected configuration or personal vault for credentials.
The program must be able to read authentication values directly. See
[official cloud environment documentation](https://learn.chatgpt.com/docs/environments/cloud-environments)
and [docs/authentication.md](docs/authentication.md).

Never put real values in source files, example configuration, workflow output,
or documentation. GitHub Actions secrets do not automatically configure Codex
Cloud authentication. A local cookie file path cannot carry over to a new cloud
environment.

## Continuing work

Read [AGENTS.md](AGENTS.md), [CHANGELOG.md](CHANGELOG.md), and the relevant tests
before making changes. Preserve the current package version during ordinary
development and keep `poetry.lock` unchanged unless dependencies change.

This handover does not publish a package, create a release, or operate on a
Substack publication. Package publication remains governed by
[docs/releasing.md](docs/releasing.md) and the existing tag-gated Trusted
Publishing workflow.

## Validation checkpoint

Validated on 2026-10-12 in a clean Python 3.12 Linux container with no Substack
credentials:

- Cloud setup passed twice with the dependency lock file unchanged.
- Offline suite: 267 passed, 8 live tests deselected.
- Normal suite with opt-ins unset: 267 passed, 8 live tests skipped.
- Strict collection: 275 tests collected.
- All five repository hooks, Bash syntax, and ShellCheck passed.
- Poetry validation, wheel/sdist build, and Twine checks passed.
- Fresh base wheel, MCP wheel, and sdist installs passed their smoke checks.
- Project, tooling, and fresh package environments passed `pip check`.

No live tests, Substack writes, package publication, or release creation were
performed for this checkpoint.

# Contributing

## Setup

Fork and clone the repository, then install the package and all optional
dependencies:

```bash
poetry install --all-extras
```

Install the repository hooks:

```bash
poetry run pre-commit install
```

## Validation

Run the offline suite:

```bash
poetry run pytest -q -m "not live" --strict-markers
```

Run all configured hooks:

```bash
poetry run pre-commit run --all-files
```

Live tests are opt-in because they create disposable drafts in a real
publication:

```bash
RUN_SUBSTACK_E2E=1 poetry run pytest -q -m live
RUN_SUBSTACK_CLI_E2E=1 poetry run pytest -q -m live tests/substack/test_cli_end_to_end.py
```

Live tests must never publish. Confirm that disposable drafts are removed after
every run.

## Pull requests

- Keep changes focused and preserve existing public interfaces and defaults.
- Add a regression test for every bug fix.
- Add offline tests for new behavior.
- Update user-facing documentation and `CHANGELOG.md` when behavior changes.
- Never include passwords, cookies, `.env` contents, or captured request
  headers.

Feature requests and bug reports are welcome through the repository issue
templates. Authentication reports must have all credentials removed.

## Releases

Maintainer release requirements are documented in
[docs/releasing.md](docs/releasing.md).

# Release checklist

1. Keep `pyproject.toml` and `substack/__init__.py` on the previous version
   while implementing code, tests, workflows, and documentation.
2. Run `poetry install --all-extras`.
3. Run `poetry run pytest -q -m "not live" --strict-markers`.
4. Run `poetry run pytest -q` with live opt-ins unset and confirm all live tests
   are skipped.
5. With configured maintainer credentials, run:

   ```bash
   RUN_SUBSTACK_E2E=1 poetry run pytest -q -m live
   RUN_SUBSTACK_CLI_E2E=1 poetry run pytest -q -m live tests/substack/test_cli_end_to_end.py
   ```

6. Update `pyproject.toml`, `substack.__version__`, `CHANGELOG.md`, and the
   release page to the target version.
7. From a clean checkout, run `poetry check`, `poetry build`, and
   `poetry run python -m twine check dist/*`.
8. Install the wheel in fresh base and `[mcp]` virtual environments, run
   `pip check`, verify all five console entry points, and import the base and MCP
   modules.
9. Push only after CI passes. Create `vX.Y.Z` from that exact commit; the publish
   workflow rejects a tag that differs from either package version.
10. After publishing, install `python-substack==X.Y.Z` from PyPI in a clean
    environment and repeat the smoke checks before announcing.

Live tests create disposable drafts and must never publish. Confirm cleanup in
the publication after each run. If an artifact is defective, yank it rather
than attempting to replace the same version.

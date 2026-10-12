#!/bin/bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
python3 -c 'import sys; assert (3, 10) <= sys.version_info < (4, 0), "Python 3.10 or newer is required"'
python3 -m venv .tools/poetry
.tools/poetry/bin/python -m pip install poetry==2.3.2
export POETRY_VIRTUALENVS_IN_PROJECT=true
.tools/poetry/bin/python -m poetry install --with dev --all-extras
.tools/poetry/bin/python -m poetry run pre-commit install

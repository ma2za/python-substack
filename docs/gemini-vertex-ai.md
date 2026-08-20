---
layout: default
title: Gemini CLI with Vertex AI
---

# Gemini CLI with Vertex AI

The repository includes project settings, maintainer instructions, and release
commands for Gemini CLI. The project settings require Vertex AI authentication.
Routine file edits, repository inspection, dependency setup, offline tests, and
pre-commit checks are pre-approved. Commands that commit, tag, push, publish,
or run live tests still require explicit approval.

## Prerequisites

- Node.js 20 or later.
- Gemini CLI installed with `npm install -g @google/gemini-cli`.
- Google Cloud CLI with Application Default Credentials (ADC).
- A Google Cloud project with billing and the Vertex AI API enabled.
- The Vertex AI User role (`roles/aiplatform.user`) on that project.

Authenticate locally:

```powershell
gcloud auth application-default login
gcloud services enable aiplatform.googleapis.com --project YOUR_PROJECT_ID
```

Copy the checked-in environment template and set the project and region:

```powershell
Copy-Item .gemini/.env.example .gemini/.env
```

`.gemini/.env` is ignored by Git. Do not put API keys or service-account JSON
in the repository. ADC is preferred for local maintainer work.

## Start Gemini

Install the project dependencies, then start Gemini from the repository root:

```powershell
poetry install --all-extras
gemini
```

Trust the folder when Gemini CLI asks so it can load the checked-in project
settings and custom commands. Use `/memory show` to confirm `GEMINI.md` is
loaded and `/commands list` to confirm the release commands are available.

## Release workflow

Prepare a candidate without publishing it:

```text
/release:prepare 0.4.0
```

Review the diff, then run the independent release verification:

```text
/release:verify
```

Both commands deliberately stop before live Substack tests, commits, tags,
pushes, GitHub releases, PyPI publication, and announcements. Authorize those
steps explicitly only after reviewing the candidate and confirming CI passed.

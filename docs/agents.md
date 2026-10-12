---
layout: default
title: Agent workflow
---

# Agent workflow

This repository can be maintained with any compatible coding agent. Read
[`AGENTS.md`](../AGENTS.md) before inspecting or changing the project.

Maintainer guidance and optional workflows live under `.agents/` and are
tracked with the repository. The [release plan](../RELEASE_PLAN.md) records the
roadmap and handover context. Follow [cloud development](../CODEX_CLOUD.md) for
reproducible setup. Do not commit credentials, cookies, tokens, or
service-account files.

Use the documented Poetry commands for dependency installation, offline tests,
and release validation. Live tests require explicit maintainer authorization
and must never publish content.

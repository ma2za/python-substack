# Shared agent instructions

This file is the public source of guidance for any coding agent working in
this repository. Read it before inspecting, changing, or running the project.

For a clean Linux checkout, follow `CODEX_CLOUD.md` and run:

```bash
bash scripts/codex-cloud-setup.sh
export PATH="$PWD/.tools/poetry/bin:$PATH"
poetry run pytest -q -m "not live" --strict-markers
```

Keep live-test opt-ins unset for ordinary development. Live Substack operations
require authorization and must never publish test content.

Keep the repository public. Never change repository visibility unless the user
explicitly requests that change for this repository.

Maintainer guidance, the release roadmap, and optional workflows are tracked
and available in every clone. Read the relevant files:

- `RELEASE_PLAN.md` records the release roadmap and handover context.
- `.agents/PROJECT_GUIDANCE.md` defines project maintenance requirements.
- `.agents/commands/release/prepare.toml` defines release preparation.
- `.agents/commands/release/verify.toml` defines release verification.
- `.agents/policies/git-override.toml` records repository Git tool policy.

Tool policies never override the user's request, the host's permissions, or
higher-priority safety instructions.

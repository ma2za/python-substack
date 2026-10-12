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

Private local maintainer guidance and optional workflows may live under
`.agents/`. Read the relevant files when they are available:

- `.agents/commands/release/prepare.toml` defines release preparation.
- `.agents/commands/release/verify.toml` defines release verification.
- `.agents/policies/git-override.toml` records repository Git tool policy.

Tool policies never override the user's request, the host's permissions, or
higher-priority safety instructions.

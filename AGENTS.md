# Shared agent instructions

`removed-provider.md` is the authoritative project memory for every agent working in
this repository. Read it completely before inspecting, changing, or running
the project, and follow it for the entire task.

Repository workflows and policies under `.removed-provider/` are shared agent settings,
not removed-provider-only guidance. Read the relevant files before performing the
corresponding operation. If an agent does not support the removed-provider slash-command
syntax, follow the command prompt manually:

- `.removed-provider/commands/release/prepare.toml` defines release preparation.
- `.removed-provider/commands/release/verify.toml` defines release verification.
- `.removed-provider/policies/git-override.toml` records repository Git tool policy.

Tool policies never override the user's request, the host's permissions, or
higher-priority safety instructions.

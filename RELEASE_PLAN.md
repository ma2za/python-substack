# python-substack maintainer roadmap

This tracked roadmap is the execution handoff for the ten releases before
1.0.0. It describes the committed scope, public-contract rules, validation,
and release procedure so a fresh maintainer session can continue without
rediscovering the repository.

## Cloud handover baseline

As of 2026-10-12:

- GitHub and PyPI both publish `v0.10.0`; the next planned release is `0.11.0`.
- The repository remains public. The maintainer approved publishing this plan
  and the supporting agent workflows for cloud development.
- Follow `CODEX_CLOUD.md` for reproducible setup and offline validation.
- The original dated baseline below is historical, not a current security or
  repository-status assertion.

## Historical verified baseline

As of 2026-10-04:

- `v0.9.1` is published from the current clean `HEAD`.
- Dependencies are audited and free of known vulnerabilities (`urllib3>=2.8.0`,
  `virtualenv>=21.14.5`, `click>=8.5.0`).
- GitHub has no open pull requests, issues, or Dependabot alerts.
- The public package supports Python 3.10 through 3.14, five console scripts,
  the Python SDK, the unified CLI, and an optional MCP server.
- No package telemetry is permitted.

## Operating procedure

For every release:

1. Read this roadmap, `docs/releasing.md`, `CHANGELOG.md`, the preceding
   release page, and relevant implementation/tests before editing.
2. Select only the first unreleased entry. Change it to `in progress` before
   release-specific work and preserve unrelated working-tree changes.
3. Write regression tests before changing existing behavior. Keep package
   versions unchanged until implementation and validation are complete.
4. Run the offline suite, strict marker collection, build and metadata checks,
   base-wheel smoke test, MCP-extra smoke test, and the release's live gates.
5. Update `pyproject.toml`, `substack/__init__.py`, `CHANGELOG.md`, the
   release page, and this roadmap together. Commit and push the exact
   validated source.
6. Tag that commit, create the GitHub release, publish to PyPI, then install
   the published package in fresh base and MCP environments before announcing.
7. Mark the release `released` only after post-publication verification.
   Record GitHub stars/forks, PyPI 30-day downloads, and GitHub 14-day traffic
   at release time and approximately 14 days later.

If a gate fails, do not tag, publish, or announce. Leave the release `in
progress` and record the failure.

## Compatibility contract through 1.x

- Preserve `Api`, `Post`, existing method names, argument meanings, and
  defaults.
- Preserve all five console scripts, current CLI commands/flags/exit codes,
  JSON keys, confirmation behavior, and legacy CLI commands.
- Preserve `EMAIL`, `PASSWORD`, `PUBLICATION_URL`, `COOKIES_PATH`, and
  `COOKIES_STRING`.
- Preserve MCP tool names and parameters, including current
  `publish_draft` semantics. Additive fields and tools are allowed.
- Do not remove existing behavior before 2.0. Undocumented upstream behavior
  remains best-effort and receives compatible patch fixes.
- Every defect fix needs a regression test. Release tags, package metadata,
  and `substack.__version__` must agree.

## Release register

| Release | Status | Theme |
|---|---|---|
| 0.9.0 | released, 2026-09-27 | Editor image preservation |
| 0.9.1 | released, 2026-10-04 | Image-sync safety |
| 0.10.0 | released, 2026-10-07 | Conflict-aware draft updates |
| 0.11.0 | planned | Markdown fidelity contract |
| 0.12.0 | planned | Authentication resilience |
| 0.13.0 | planned | Safe draft lifecycle |
| 0.14.0 | planned | CLI automation contract |
| 0.15.0 | planned | MCP parity and agent safety |
| 0.16.0 | planned | Upstream compatibility resilience |
| 0.17.0 | planned | Public contract and maintainer docs |
| 0.18.0 | planned | Release-candidate audit |
| 1.0.0 | planned, not counted | Stable release |

## 0.9.1: Image-sync safety

**Objective:** Make exported Markdown image identity safe across edits without
breaking usable V1 backups.

### Implementation

- Export `python-substack-image:v2` immediately after every image. Its
  URL-safe base64 JSON payload contains the original remote `src` and the
  preserved non-owned attributes.
- Continue reading V1 markers only when the submitted image `src` resolves to
  exactly one remote image. V1 cannot authorize changed-source preservation.
- Resolve V2 markers by their bound original source, consume each remote image
  at most once, and reject corrupt, stale, duplicate, reused, missing, or
  non-adjacent markers.
- Keep Markdown authoritative for `src`, `alt`, `href`, and caption. Restore
  remote/editor attributes, including unknown attributes, and set
  `isProcessing` to `false`.
- Retain `allow_image_replacement=False` and the CLI
  `--allow-image-replacement --yes` escape hatch. It is required for unsafe
  or intentionally unmatched replacements.

### Tests and gates

- Cover V2 changed-source updates; resolvable and ambiguous V1 documents;
  duplicate remote URLs; marker reuse; stale/corrupt/non-adjacent markers;
  new images; explicit replacement; alignment, dimensions, watermark, and
  unknown attributes.
- Add API, renderer/exporter, and CLI regression coverage. Run a disposable
  live draft edit that changes editor image metadata and verifies preservation.

## 0.10.0: Conflict-aware draft updates

**Objective:** Prevent a Markdown update from silently overwriting remote
draft changes made after export.

### Implementation

- Export a stable remote revision/fingerprint with Markdown backup metadata.
- On update, compare the submitted expected revision with the current remote
  draft before any write. Return actionable mismatch details in dry-run mode.
- Add an explicit override using the project's established write-confirmation
  model; normal updates fail closed on conflict.
- Preserve old Markdown files by treating missing revision metadata as an
  unprotected update and requiring the deliberate override where safe
  comparison is impossible.

### Tests and gates

- Cover unchanged drafts, remote body and metadata changes, malformed revision
  metadata, old exports, dry-run output, SDK errors, CLI JSON/noninteractive
  behavior, and the explicit override.

## 0.11.0: Markdown fidelity contract

**Objective:** Make supported Markdown conversion deterministic and make every
unsupported editor construct visible and safe.

### Implementation

- Create versioned fixture pairs for each documented Markdown and ProseMirror
  construct: marks, links, lists, images, captions, code, footnotes, math,
  pull quotes, callouts, and opaque widgets.
- Assert canonical export-render-export output for supported constructs.
- Ensure unrepresentable content is wrapped in validated opaque markers at the
  original document position rather than silently discarded.
- Document the supported, canonicalized, and opaque-preserved categories.

### Tests and gates

- Run every fixture through both directions, test malformed markers and mixed
  supported/opaque documents, and pin output changes through reviewed fixtures.

## 0.12.0: Authentication resilience

**Objective:** Normalize authentication behavior across cookie and credential
flows without exposing secrets.

### Implementation

- Define consistent errors for invalid cookies, expired sessions, wrong
  publication/account selection, password failures, and upstream auth changes.
- Redact credentials, cookies, authorization headers, and sensitive URLs in
  SDK exceptions, CLI text/JSON errors, and MCP responses.
- Document cookie-first setup, expiry recovery, account selection, and the
  supported environment-variable precedence.

### Tests and gates

- Cover each authentication failure path, redaction in nested upstream errors,
  CLI JSON envelopes, and MCP error responses. Run disposable live checks for
  both configured authentication modes when credentials permit.

## 0.13.0: Safe draft lifecycle

**Objective:** Give every write operation consistent preflight, dry-run, and
confirmation semantics.

### Implementation

- Standardize create, update, schedule, unschedule, publish, and delete
  preflight results around action, target, intended metadata/body changes, and
  whether a remote write would occur.
- Extend dry-run where it is absent without changing existing successful-write
  defaults. Keep drafts unpublished by default and require existing explicit
  confirmation boundaries for publishing and deletion.
- Normalize scheduling timezone validation and clear actionable failure output.

### Tests and gates

- Cover every action in interactive, noninteractive, and JSON modes; require
  `--yes` where current policy requires it; verify dry-run produces no write.

## 0.14.0: CLI automation contract

**Objective:** Freeze the command-line interface as a dependable scripting
surface.

### Implementation

- Snapshot `--help`, command hierarchy, exit codes, JSON envelope keys, and
  legacy command behavior.
- Ensure all supported write workflows have documented JSON output and clear
  noninteractive requirements.
- Publish a CLI compatibility table and shell-safe automation examples.

### Tests and gates

- Test parser behavior, help snapshots, output schemas, exit codes, global
  option placement, redaction, confirmation failures, and legacy entry points.

## 0.15.0: MCP parity and agent safety

**Objective:** Make MCP workflows match the safe SDK/CLI behavior without
implicit publishing.

### Implementation

- Audit each MCP tool against its SDK/CLI equivalent and close documented
  capability or safety gaps.
- Return structured, stable tool results and actionable errors. Keep read
  operations side-effect free, write operations explicit, draft creation the
  default, and publication opt-in.
- Document tool schemas, write intent, confirmation expectations, and local
  credential handling.

### Tests and gates

- Snapshot tool schemas and test read/write parity, invalid input, dry-run
  behavior, publishing safeguards, and secret redaction.

## 0.16.0: Upstream compatibility resilience

**Objective:** Isolate Substack response-shape uncertainty behind compatible
normalization.

### Implementation

- Consolidate draft, post, tag, section, scheduling, and publication response
  envelope normalization in tested helpers.
- Replace or isolate the current `get_sections` workaround behind a documented
  compatibility boundary.
- Make malformed or unexpected upstream responses fail with contextual,
  redacted errors instead of incidental key/type failures.

### Tests and gates

- Add representative legacy/current/malformed response fixtures and verify
  public return shapes remain compatible. Run live read and lifecycle checks.

## 0.17.0: Public contract and maintainer docs

**Objective:** Make every supported behavior discoverable and maintainable.

### Implementation

- Publish complete API, CLI, MCP, environment, authentication, marker-format,
  compatibility, troubleshooting, and upstream-limitations references.
- Add a contributor fixture guide explaining fixture updates, live-test safety,
  redaction, compatibility snapshots, and release evidence.
- Reconcile README, Pages navigation, support matrix, release pages, and
  examples with implemented behavior only.

### Tests and gates

- Check internal documentation links, examples, command snippets, public API
  signatures, and compatibility claims against the repository.

## 0.18.0: Release-candidate audit

**Objective:** Freeze the feature surface and prove the pre-1.0 contract.

### Implementation

- Add public-surface snapshots for Python signatures, entry points, CLI help,
  JSON envelopes, marker formats, and MCP schemas.
- Reach at least 85% line coverage, excluding opt-in live behavior from the
  offline denominator only where justified.
- Add Windows and macOS smoke jobs while retaining the Linux Python 3.10-3.14
  matrix. Add dependency, build, metadata, docs-link, and clean-install CI
  checks.
- Triage all issues. No unresolved data-loss, authentication, publishing,
  packaging, P0, or P1 defect may remain.

### Tests and gates

- Run all offline/packaging/MCP/OS/docs checks, live SDK and CLI suites twice
  on separate runs, and clean PyPI installs on the oldest and newest supported
  Python versions.

## 1.0.0: Stable release

This release is not one of the ten pre-1.0 releases. It begins only after
0.18.0 feedback is triaged. Accept only release-blocking corrections, make no
intentional runtime behavior change, repeat every 0.18.0 gate from a clean
checkout, verify Trusted Publishing and artifacts, then publish the final
compatibility policy and launch material.

## Completion criteria

The roadmap completes when 0.9.1 through 0.18.0 are released with dates,
tags, validation evidence, and metrics; 1.0.0 has passed the same gates; and
the resulting public surface remains compatible throughout 1.x.

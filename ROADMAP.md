# Ten-release roadmap to python-substack 1.0

This local maintainer roadmap starts from 0.1.27 and defines the next ten releases. Releases
should normally be spaced two to three weeks apart. The sequence preserves
every existing public contract while improving adoption, documentation,
reliability, safe Markdown synchronization, and release security.

## Goals

Targets by 1.0:

- At least 300 GitHub stars.
- At least three times the rolling 30-day downloads measured at the start of
  0.2.0.
- No removal or incompatible change to existing Python APIs, CLI commands,
  JSON keys, environment variables, console scripts, or MCP tools.
- No package telemetry.

Starting state recorded on 2026-07-29:

- Version 0.1.27.
- 158 GitHub stars and 28 forks.
- Approximately 33.5k cumulative downloads reported by Pepy.
- 145 passing offline tests.
- Five console entry points.
- Python 3.10 through 3.14 support.

The rolling 30-day download baseline must be recorded immediately before
0.2.0 is released. Cumulative Pepy downloads are context only and are not the
growth denominator.

## Release authority

The instruction "go ahead with the next release" authorizes implementation,
validation, versioning, commit, tag creation, GitHub release creation, PyPI
publication, post-publication verification, and the launch work specified for
that release. This authority remains subject to credentials, external service
availability, repository protections, and every release gate below.

If a gate fails, do not tag, publish, or announce the release. Report the
failure and leave the roadmap entry `in progress`.

## Operating contract

Each release has one of these statuses:

- `planned`: no release work has started.
- `in progress`: implementation or validation has started.
- `released`: the tagged package is published and post-publication checks pass.

When starting a release:

1. Read this roadmap, `docs/releasing.md`, `CHANGELOG.md`, and the preceding
   release note.
2. Select the first entry that is not `released` and implement only that
   release.
3. Change its status to `in progress` before making release-specific changes.
4. Preserve unrelated working-tree changes.
5. Add regression tests before changing existing behavior.
6. Keep package versions unchanged until implementation and validation are
   complete.
7. Run the offline suite, strict marker collection, build validation,
   base-wheel smoke test, MCP-extra smoke test, and applicable live tests.
8. Update `pyproject.toml`, `substack.__version__`, `CHANGELOG.md`, the
   per-release page, and this roadmap together.
9. Commit and push the exact validated source.
10. Create the version tag and GitHub release, publish to PyPI, install the
    published artifact in clean base and MCP environments, and execute the
    release's launch work.
11. Mark the entry `released` only after the published artifact passes its
    checks.
12. Record release-time and approximately 14-day metrics before starting the
    following release.

## Compatibility contract through 1.x

- Preserve `Api`, `Post`, current method names, argument meanings, and
  defaults.
- Preserve all five console scripts.
- Preserve existing CLI commands, flags, confirmation behavior, exit codes,
  and JSON keys. Additive fields are allowed.
- Preserve `EMAIL`, `PASSWORD`, `PUBLICATION_URL`, `COOKIES_PATH`, and
  `COOKIES_STRING`.
- Preserve existing MCP tool names and parameters, including current
  `publish_draft` semantics.
- Existing behavior may be deprecated in documentation but cannot be removed
  before 2.0.
- Every fixed defect must receive a regression test.
- Release tags, package metadata, and `substack.__version__` must agree.
- Undocumented upstream Substack behavior remains best-effort. Compatible
  fixes for upstream changes are patch releases, not breaking changes.

## Metrics

Use these sources:

- GitHub stars and forks at release time.
- Rolling 30-day downloads from the
  [PyPI Stats recent endpoint](https://pypistats.org/api/), which excludes
  known mirrors.
- GitHub views, unique visitors, clones, and referrers from the repository's
  14-day traffic data.
- Measurements at release time and approximately 14 days later.

Do not add telemetry to the package, CLI, SDK, or MCP server.

| Release | Status | Released | Tag | Stars | Forks | 30-day downloads | 14-day unique visitors | 14-day unique clones | Announcement links |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| 0.2.0 | released | 2026-07-29 | v0.2.0 | 158 | 28 | 12,272 | 49 | 140 | [GitHub](https://github.com/ma2za/python-substack/releases/tag/v0.2.0); [Substack](https://mazzapaolo.substack.com/p/python-substack-0-2-0) |
| 0.3.0 | released | 2026-08-09 | v0.3.0 | 160 | 28 | 13,528 | 40 | 91 | [GitHub](https://github.com/ma2za/python-substack/releases/tag/v0.3.0) |
| 0.4.0 | released | 2026-08-24 | v0.4.0 | - | - | - | - | - | [GitHub](https://github.com/ma2za/python-substack/releases/tag/v0.4.0) |
| 0.5.0 | released | 2026-08-30 | v0.5.0 | 166 | 28 | 14,448 | 47 | 88 | [GitHub](https://github.com/ma2za/python-substack/releases/tag/v0.5.0) |
| 0.6.0 | released | 2026-08-30 | v0.6.0 | 166 | 28 | 14,448 | 47 | 88 | [GitHub](https://github.com/ma2za/python-substack/releases/tag/v0.6.0); [Substack](https://mazzapaolo.substack.com/p/back-up-substack-draft-markdown-python-substack-060) |
| 0.7.0 | released | 2026-09-22 | v0.7.0 | 166 | 28 | 14,448 | 47 | 88 | [GitHub](https://github.com/ma2za/python-substack/releases/tag/v0.7.0) |
| 0.8.0 | released | 2026-09-22 | v0.8.0 | 166 | 28 | 14,448 | 47 | 88 | [GitHub](https://github.com/ma2za/python-substack/releases/tag/v0.8.0) |
| 0.9.0 | planned | - | - | - | - | - | - | - | - |
| 0.10.0 | planned | - | - | - | - | - | - | - | - |
| 1.0.0 | planned | - | - | - | 300 target | - | 3x baseline target | - | - | - |

## 0.2.0: Positioning, compatibility, and supply-chain trust

**Status:** released

**Objective:** Make the existing package easier to understand and safer to
adopt before adding more functionality.

### Implementation

- Rewrite the README around the primary outcome: safely create, manage,
  schedule, and publish Substack drafts from Markdown through Python, CLI, or
  MCP.
- Put installation, a three-command Markdown-to-draft flow, draft-only safety,
  and a visual result above the fold.
- Move legacy CLI, low-level node construction, YAML details, and contributor
  instructions into focused documentation pages without deleting their
  content.
- Add `CONTRIBUTING.md`, `SECURITY.md`, and `docs/compatibility.md`.
- Link this roadmap from the README.
- Upgrade the existing pre-commit hooks to currently supported compatible
  revisions after verifying them.
- Change the PyPI development classifier from Alpha to Beta.
- Establish `docs/metrics.md` with the dated 0.2.0 baseline.
- Migrate publishing from `PYPI_TOKEN` to PyPI Trusted Publishing:
  - Configure the PyPI publisher for owner `ma2za`, repository
    `python-substack`, workflow `ci_publish.yml`, and environment `pypi`.
  - Give only the publish job `id-token: write`.
  - Remove the long-lived token input only after OIDC publishing is configured.
  - Protect the `pypi` GitHub environment.
  - Follow the
    [PyPI Trusted Publisher configuration](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).

### Public interfaces

- No runtime API changes.
- All existing README use cases remain reachable through documentation links.

### Tests and gates

- The existing 145 offline tests remain green.
- Test every README command that can run without credentials.
- Validate base and MCP wheel installations.
- Confirm the published artifact reports Trusted Publishing on PyPI.

### Launch

- Publish a GitHub release and a Substack announcement repositioning the
  project as writer-side Markdown automation.
- Update the repository description and PyPI summary to the same positioning.
- Record baseline stars, forks, downloads, traffic, and referrers.

## 0.3.0: Five-minute onboarding and GitHub Pages documentation

**Status:** released

**Objective:** Let a new user reach a safe unpublished draft without navigating
the full README.

### Implementation

- Publish `docs/` through GitHub Pages from `main/docs`, using GitHub Pages'
  built-in Markdown and Jekyll support without a third-party documentation
  framework.
- Add a documentation index with paths for:
  - Installation and first draft.
  - Authentication and cookie handling.
  - Unified CLI.
  - Python SDK.
  - Markdown syntax.
  - MCP setup.
  - Safety and publishing behavior.
  - Troubleshooting.
- Use the existing before and after images in a concrete
  Markdown-to-Substack walkthrough.
- Add tested examples for:
  - Markdown file to unpublished draft.
  - Scheduling an existing draft.
  - Selecting among multiple publications.
  - Stable JSON output in automation.
  - Cookie authentication verification.
- Add the GitHub Pages URL to PyPI project links and the repository About
  section.
- Preserve old documentation paths and provide links where content moves.

### Public interfaces

- No runtime behavior changes.
- Documentation examples use only supported interfaces.

### Tests and gates

- Add smoke tests for every executable example.
- Validate internal documentation links and code blocks.
- Verify the Pages site from a clean browser session.
- A new user with credentials can create an unpublished draft by following
  only the getting-started page.

### Launch

- Publish a tutorial built with the package itself.
- Share the five-minute workflow with Python and Substack writer communities.
- Compare documentation traffic and PyPI downloads with the 0.2.0 baseline.

The tutorial is stored as unpublished Substack draft `210457101`. Public
publication and community sharing are pending explicit approval for the
external account action.

## 0.4.0: MCP read operations and safe publishing path

**Status:** released

**Objective:** Make MCP useful for inspecting and preparing publications
without steering agents toward immediate publishing.

### Implementation

- Add these MCP tools:
  - `get_status()`
  - `list_publications()`
  - `list_drafts(filter="draft", offset=0, limit=25)`
  - `get_draft(draft_id)`
  - `schedule_draft(draft_id, at)`
  - `unschedule_draft(draft_id)`
  - `publish_draft_checked(draft_id, confirm=False, send=False, share_automatically=False)`
- `publish_draft_checked` rejects execution unless `confirm=True`, runs
  prepublish checks, and defaults to no email delivery.
- Keep the existing `publish_draft` tool unchanged for compatibility. Document
  it as the compatibility interface and recommend the checked tool.
- Remove duplicated MCP draft-building logic by routing through the existing
  SDK helper without changing responses.
- Add verified client configuration examples using official documentation
  current at implementation time.
- Document which MCP tools read, create drafts, perform reversible writes, or
  publish.

### Public interfaces

- The seven MCP tools above are additive.
- Existing MCP tools and signatures remain unchanged.

### Tests and gates

- Unit-test every MCP tool with a fake `Api`; the offline suite uses no network.
- Verify confirmation rejection, default no-send behavior, ISO timestamp
  validation, error redaction, and unchanged legacy behavior.
- Smoke-test MCP-extra installation and server startup.
- Run a live MCP smoke test that creates and deletes a disposable draft but
  never publishes it.

### Launch

- Publish an MCP workflow demonstration centered on drafting and review.
- Share it with MCP and relevant AI automation communities.
- Measure interest through issue feedback and download movement without adding
  telemetry.

## 0.5.0: Authentication, custom domains, uploads, and request reliability

**Status:** released

**Objective:** Remove common operational failures before introducing draft
synchronization.

### Implementation

- Resolve `publication_url` by normalized hostname against Substack subdomains
  and custom domains.
- Raise a clear `SubstackRequestException` when the requested publication is
  unavailable instead of failing through `None`.
- Add optional `timeout=None` to `Api`; preserve unlimited waiting when
  omitted.
- Add global CLI `--timeout SECONDS`, defaulting to existing behavior when
  absent.
- Pass configured timeouts consistently through SDK requests.
- Detect local image MIME type instead of always encoding uploads as JPEG:
  - Preserve JPEG behavior for JPEG files.
  - Support PNG, GIF, and WebP.
  - Use `application/octet-stream` only when the type cannot be identified.
- Expand secret redaction to cookie-like values in request errors.
- Keep bounded retries restricted to safe GET and DELETE requests.

### Public interfaces

- Add optional `Api(..., timeout=None)`.
- Add optional global CLI `--timeout`.
- No existing constructor or CLI invocation changes meaning.

### Tests and gates

- Cover Substack subdomains, custom domains, unavailable publications,
  uppercase hosts, and trailing slashes.
- Cover supported image MIME types and unknown extensions.
- Verify timeout omission preserves current request calls.
- Verify POST requests remain non-retried.
- Run live status, draft creation, image upload, scheduling, and cleanup.

### Launch

- Publish reliability-focused release notes with custom-domain and image-upload
  examples.
- Use a smaller maintenance announcement instead of a broad campaign.

## 0.6.0: Loss-aware draft export to Markdown

**Status:** released

**Objective:** Give users a safe way to back up a Substack draft before local
editing.

### Implementation

- Add `Api.export_draft_to_markdown(draft_id)`.
- Return `draft`, `markdown`, and `unsupported_nodes`.
- Add:

  ```text
  substack drafts export DRAFT_ID
  ```

- Add `--output PATH` and `--force`.
- Without `--output`, print Markdown to stdout.
- Under global `--json`, return `action`, `draft_id`, `markdown`, and
  `unsupported_nodes`.
- Never overwrite an existing output file without `--force`.
- Implement reverse rendering for every Markdown node supported by the forward
  renderer.
- Preserve headings, marks, links, lists, images, captions, code language,
  blockquotes, footnotes, math, pull quotes, and callouts semantically.
- Emit unsupported Substack nodes as:

  ```text
  <!-- python-substack-node:v1 BASE64URL_JSON -->
  ```

- Encode UTF-8 JSON using URL-safe base64 without padding.
- Do not discard unknown attributes or node types.
- Document that 0.6 exports opaque nodes but updates containing them become
  supported in 0.8.

### Public interfaces

- Add `Api.export_draft_to_markdown(draft_id)`.
- Add `drafts export`.

### Tests and gates

- Add golden tests for every supported node type.
- Export then render preserves semantic content for supported nodes.
- Unsupported-node payloads decode to the original dictionary.
- Malformed draft bodies fail without partial file output.
- Export performs no server writes.
- A live test exports a disposable feature-complete draft and deletes it.

### Launch

- Publish a "Back up a Substack draft as Markdown" demonstration.
- Emphasize read-only behavior and unsupported-node visibility.

## 0.7.0: Safe Markdown updates for supported drafts

**Status:** released

**Objective:** Complete the create, edit locally, inspect, and update loop
without risking unsupported content.

### Implementation

- Add:

  ```python
  Api.update_draft_from_markdown(
      draft_id,
      markdown,
      *,
      subtitle=None,
      audience=None,
      write_comment_permissions=None,
      search_engine_title=None,
      search_engine_description=None,
      slug=None,
      draft_section_id=None,
      tags=None,
      dry_run=False,
  )
  ```

- Return stable fields: `action`, `draft_id`, `dry_run`, `changed`, `payload`,
  `draft`, `tags`, and `unsupported_nodes`.
- Update body content by default. Leave metadata unchanged unless explicitly
  supplied.
- Treat supplied tags as additive because the SDK does not expose safe tag
  replacement.
- `dry_run=True` may fetch the draft but performs no PUT, tag, schedule,
  publish, or delete request.
- Add:

  ```text
  substack drafts update DRAFT_ID MARKDOWN_FILE
  ```

- Support the metadata flags from `drafts create`, plus `--dry-run` and
  `--yes`.
- Require interactive confirmation for updates. JSON or noninteractive mode
  requires `--yes`.
- If the remote draft contains unsupported nodes, abort before writing and
  instruct the user to export it.
- Do not silently remove, append, or reposition unsupported nodes.
- Never modify the local Markdown file.

### Public interfaces

- Add `Api.update_draft_from_markdown`.
- Add `drafts update`.
- Existing draft creation remains unchanged.

### Tests and gates

- Test body-only updates, selective metadata, additive tags, unchanged
  schedules, no-op updates, dry runs, confirmations, and JSON responses.
- Assert unsupported remote content blocks the PUT.
- Assert post-PUT failures report that the draft may have changed and do not
  attempt rollback deletion.
- A live test creates, updates, verifies, and deletes a disposable draft
  without publishing.

### Launch

- Demonstrate the safe local edit loop.
- Make update safety and dry-run behavior the primary message.

## 0.8.0: Lossless unsupported widget preservation

**Status:** released

**Objective:** Allow exported drafts containing Substack-only widgets to be
updated without data loss.

### Implementation

- Teach Markdown rendering and updates to recognize
  `python-substack-node:v1` markers.
- Validate every marker before writing:
  - Valid URL-safe base64.
  - Valid UTF-8 JSON.
  - Top-level JSON object.
  - Non-empty string `type`.
- Reinsert valid opaque nodes verbatim at their marker position.
- Compare opaque nodes in the current remote draft with markers in submitted
  Markdown.
- Abort if remote unsupported nodes are missing, duplicated, stale, or
  altered.
- Add `allow_unsupported_change=False` to the Python update API.
- Add CLI `--allow-unsupported-change`; require it together with `--yes` for
  intentional removal or replacement.
- Ordinary HTML comments must never become Substack nodes.
- Cover button, recipe, and Polymarket examples without hard-coding their
  schemas.
- Update issue #64 against the implemented CLI and close it only after live
  round-trip verification.

### Public interfaces

- Add optional `allow_unsupported_change=False`.
- Add CLI `--allow-unsupported-change`.
- Version-1 opaque markers are a documented file-format contract through 1.x.

### Tests and gates

- Exact round trips for arbitrary unknown nodes and nested attributes.
- Reject corrupt, malicious, stale, duplicate, and missing markers.
- Confirm no server request occurs after validation failure.
- A live test verifies that an editor-created unsupported node survives an
  update unchanged.
- If a live widget cannot be produced safely, keep issue #64 open and do not
  release 0.8.0.

### Launch

- Publish a technical preservation demonstration showing before, export,
  update, and after.
- Target existing users and Markdown-based publishing communities.

## 0.9.0: Editor image preservation

**Status:** planned

**Objective:** Preserve Substack editor image settings during Markdown
updates.

### Implementation

- Export image metadata immediately after its Markdown image as:

  ```text
  <!-- python-substack-image:v1 BASE64URL_ATTRS_JSON -->
  ```

- Markdown owns `src`, `alt`, `href`, and caption content.
- Preserve all other server and editor image attributes, including unknown
  future attributes.
- Always force `isProcessing` to `false` during an update.
- Validate image markers against the current remote image before writing.
- For unmarked images, preserve editor attributes only when a unique
  one-to-one exact source URL match exists.
- If a remote image cannot be matched safely, abort unless explicit image
  replacement is authorized.
- Add `allow_image_replacement=False` to the Python update API.
- Add CLI `--allow-image-replacement`, requiring `--yes`.
- New images without markers retain existing defaults and upload behavior.

### Public interfaces

- Add optional `allow_image_replacement=False`.
- Add CLI `--allow-image-replacement`.
- Version-1 image markers are a documented file-format contract through 1.x.

### Tests and gates

- Preserve alignment, size, dimensions, watermark URL, offset, top-image state,
  and unknown attributes.
- Markdown changes to alt, link, caption, or source win over stored values.
- Test duplicate source URLs, stale markers, changed editor uploads, new
  images, and explicit replacements.
- A live test edits image properties in Substack, performs a Markdown update,
  and verifies preservation.

### Launch

- Publish a visual before-and-after image preservation demonstration.
- Update the Markdown support matrix with complete round-trip guarantees.

## 0.10.0: 1.0 release candidate and compatibility audit

**Status:** planned

**Objective:** Freeze the supported contract and find defects before 1.0.

### Implementation

- Add a complete hand-written public API reference to GitHub Pages.
- Document:
  - Supported Python imports and signatures.
  - CLI commands, exit codes, and JSON envelopes.
  - MCP tools and safety properties.
  - Environment variables.
  - Opaque Markdown marker formats.
  - External Substack API limitations.
  - Deprecation and compatibility policy.
- Add snapshot tests for public Python signatures, console entry points, CLI
  help, JSON keys, and MCP tool schemas.
- Reach at least 85% line coverage while excluding live-only behavior from the
  offline denominator where appropriate.
- Add Windows and macOS smoke jobs on one supported Python version while
  retaining the full Linux Python-version matrix.
- Run dependency, build, metadata, documentation-link, and clean-install
  checks in CI.
- Triage all open issues:
  - No unresolved data-loss, authentication, publishing, or packaging defect
    may remain.
  - Lower-priority feature requests may be explicitly deferred.
- Publish a 1.0 migration guide stating that no migration is required from
  0.10.0.

### Public interfaces

- Feature freeze.
- Only additive corrections are allowed.
- Add no broad capability after the release-candidate tag.

### Tests and gates

- All offline, packaging, MCP, operating-system, and documentation checks pass.
- Live SDK and CLI suites pass twice on separate runs.
- Clean PyPI installations work on the oldest and newest supported Python
  versions.
- No P0 or P1 issue remains open.

### Launch

- Release as the public 1.0 candidate and request testing.
- Focus announcements on existing users and contributors.
- Record candidate feedback and the gap to 300 stars and three times baseline
  downloads.

## 1.0.0: Stable writer automation release

**Status:** planned

**Objective:** Declare the accumulated compatible interface stable and execute
the main growth launch.

### Implementation

- Accept only release-blocking fixes discovered during 0.10.0 testing.
- Set version 1.0.0 consistently.
- Change the development classifier to Production/Stable.
- Publish the final compatibility policy:
  - No breaking public change before 2.0.
  - Legacy console commands remain supported throughout 1.x.
  - Deprecations require documentation and warnings before future
    major-version removal.
  - Undocumented upstream Substack behavior remains best-effort and receives
    compatible patch fixes.
- Finalize the README, Pages documentation, changelog, release notes, and
  announcement copy.
- Use the package itself to prepare the Substack announcement when configured
  credentials permit.

### Public interfaces

- The 0.10.0 interface becomes the 1.x compatibility baseline.
- Make no intentional runtime behavior change in the version-only release.

### Tests and gates

- Repeat every 0.10.0 gate from a clean checkout.
- Verify Trusted Publishing and artifact attestations.
- Install 1.0.0 from PyPI in clean base and MCP environments.
- Run live status, create, export, update, schedule, unschedule, and cleanup
  workflows.
- Never publish a disposable live-test draft.

### Launch

- Publish the GitHub and PyPI release.
- Publish the Substack launch article.
- Post tailored announcements for Python, Substack, MCP, and developer
  automation communities, including a Show HN submission.
- Lead with a real Markdown-to-draft and update demonstration rather than a
  feature inventory.
- Include a restrained star request and contribution invitation.
- Record launch-day and 14-day metrics.
- Success requires at least 300 stars and at least three times the 0.2.0
  rolling 30-day download baseline.

## Completion criteria

The roadmap is complete when:

- Every release above is marked `released` with its date, tag, metrics, and
  announcement links.
- Existing public behavior remains compatible through 1.0.
- The package has safe create, export, update, widget-preservation,
  image-preservation, scheduling, publishing, CLI, Python, and MCP workflows.
- GitHub Pages provides task-oriented documentation.
- PyPI publishing uses short-lived OIDC credentials.
- The published 1.0 artifacts pass every clean-install and live validation
  gate.

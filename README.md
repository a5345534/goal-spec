# goal-spec

Standalone Pi skill folder for writing OpenSpec change packages from a user goal. It includes bundled helper scripts so target workspaces do not need to vendor `openspec/scripts/*` or depend on a neighboring `openspec-workflow` checkout for normal validation.

## What it provides

`goal-spec` is a self-contained OpenSpec authoring skill. Workspaces may
load this external skill, but should not copy/own separate OpenSpec writing or
planning skills for the same workflow. It writes and validates the normal
OpenSpec artifacts:

- `proposal.md`
- `design.md`
- `tasks.md`
- `specs/**/spec.md`
- `source-manifest.json`
- `change-explainer.html` when the target project requires it

It also covers update/review/explainer-only/archive-preflight modes for an
existing OpenSpec change package.

Stage 1 authoring roles are declared in
`profiles/goal-spec-authoring-profile.json` and documented in
`docs/authoring-agent-roles.md`. The profile maps roles to abstract
`modelClass` values only:

- `collector` → `evidence-collector`
- `judge` → `value-judge`
- `writer` → `spec-writer`
- `explainer` → `explainer-writer`
- `reviewer` → `strict-reviewer`

Concrete provider/model ids are deliberately absent from the profile; runtime
resolution belongs to `goal-runner` harness binding catalogs.

The skill keeps all authoring instructions directly in `SKILL.md`; the role
profile is a machine-readable contract, not a separate prompt reference needed
for normal use. Automation needed by the skill is bundled under `scripts/` and
uses only Python's standard library.

## Role-separated authoring model

The authoring workflow separates evidence collection, value judgment, writing,
explainer generation, and review so one role does not both gather evidence and
approve the value/scope decision. The bundled schema at
`schemas/goal-spec-authoring-profile.schema.json` fixes the expected role →
`modelClass` mapping and rejects concrete-model semantics at the profile layer.

For existing changes, collector/reviewer flows read `source-manifest.json` first
and then authoritative sources only. When a source lacks deterministic shell
validators, `goal-spec` records acceptance criteria instead of inventing
commands.

## BMAD-inspired improvements

The skill incorporates BMAD-style planning practices adapted for OpenSpec:

- discovery before drafting: brain dump, stakes calibration, working mode, concern scan;
- spec kernel: Why, Capabilities, Constraints, Non-goals, Success signal;
- optional elicitation loop: pre-mortem, red-team, stakeholder lens, first principles, edge cases;
- load-bearing preservation pass so source claims are not silently lost;
- quality rubric for decision-readiness, done-ness clarity, scope honesty, downstream usability, boundary fit, and preservation.

## What it is not

This skill is **not** for converting OpenSpec into `/goal` or Goal DAG files.
It is for writing the OpenSpec specification/change package itself.

## Pipeline Role

`goal-spec` is Stage 1 of the goal execution pipeline:

```text
user goal → OpenSpec change package
```

It writes governed OpenSpec sources only. It does not convert OpenSpec into Goal DAG files and does not invoke `/goal`.

Downstream tools such as `goal-dag` must consume the OpenSpec change package through `source-manifest.json` and the listed authoritative sources.

Authoritative sources are `proposal.md`, `design.md`, `tasks.md`, and `specs/**/spec.md`. `change-explainer.html`, `.goal-spec/` workflow state, and generated temporary context files are non-authoritative.

See `docs/pipeline-boundaries.md` for the full Stage 1 boundary and handoff contract.

## Use with Pi

Load directly:

```bash
pi --skill <path-to-goal-spec>
```

Install once from GitHub:

```bash
pi install git:github.com/a5345534/goal-spec
```

After installation, update through Pi package management instead of manually
editing the installed skill checkout:

```bash
pi update --extensions
# or update this package explicitly
pi update git:github.com/a5345534/goal-spec
```

Avoid installing with a pinned git ref such as `@v1` or `@<commit>` if you want
`pi update` to track the latest package revision. Pinned refs are reconciled but
not moved by `pi update`; use `pi install git:github.com/a5345534/goal-spec@<new-ref>` only when intentionally changing pins.

Or add it to Pi settings as a skill path/package path when doing local
contributor development.

## Typical use

```text
/skill:goal-spec write an OpenSpec change for <goal>
```

Expected output is an OpenSpec change under:

```text
openspec/changes/<change-name>/
```

## Response Lint

`goal-spec` includes a `lint-response` command that validates natural-language
agent responses against stage-specific routing rules. It ensures agents follow
the one-question discipline, bounded options format, same-language visible
labels, internal-reasoning boundaries, and content boundaries required at each
stage.

Available stages:

| Stage | When to use | What it enforces |
|-------|------------|------------------|
| `pre-confirmation` | Stage 1.5 Problem & Scope Grilling Output | Exactly one blocking question, recommended answer, bounded options, localized `Not doing yet`, no premature PMA/Spec Kernel/OpenSpec writing |
| `scope-selected` | Stage 1.7 Scope Confirmation | Three valid decisions, numbered choices, rejects Stage 5 tokens |
| `invalid-decision` | Invalid Stage 5 approval at 1.7 | Rejection language + valid 1.7 choices |
| `digest-check` | Missing input digests | Blocking/failing language on freshness |
| `grilling` | Problem-scope grilling or value challenge phase | Exactly one question including CJK `？`, recommended answer, bounded options, localized `Not doing yet`, same-language visible labels, no internal reasoning, no premature content |

Example — lint a grilling-phase response:

```bash
<script-dir>/scripts/goal-spec-workflow lint-response --stage grilling --response-text "
I have reviewed your proposal. My recommended answer is to start with scope A (filters only)
because it keeps the first slice minimal and verifiable.

Blocking clarification:
Should we include bulk actions in the initial scope, or defer them to a follow-up?

Options:
A. Include bulk actions now — broader first slice, longer delivery.
B. Defer bulk actions — narrower scope, faster verification.

Not doing yet:
- no Proposal Meaning Analysis
- no Spec Kernel or OpenSpec writing
" --project-root ./
```

For non-English user-facing responses, localize headings/field labels (for
example, use `期望成果` rather than `Intended outcome` in Traditional Chinese) while
preserving canonical SSOT identifiers such as file names, function names, schema
fields, paths, commands, and decision tokens.

The linter returns exit 0 (pass) or exit 20 (blocked) with a JSON report.

## Value-gated workflow helper (new)

`goal-spec` now uses a structured pre-spec workflow before starting OpenSpec
writing. Use `scripts/goal-spec-workflow` to make value challenge,
phase progress, claim preservation, loop guards, and readiness checks explicit,
recordable, and reviewable.

Use this helper when:

- The user goal is new/unclear or hard to prove as valuable.
- You need to compare `no-build` and `smaller-scope` alternatives before
  choosing scope.
- You need an auditable decision surface before `proposal.md`/`design.md`/
  `tasks.md` scaffolding.
- You must decide whether to continue with acknowledged assumptions.

For simple "validation-only" or "explainer-only" modes, you can skip these helper
`init/gate/write-spec` steps and run the OpenSpec validation wrappers directly.

## Bundled helpers

Run these from the skill directory, or resolve them relative to `SKILL.md` when
the skill is installed by Pi:

```bash
# Start or refresh workspace-local value-gated workflow state
scripts/goal-spec-workflow init <change-name> --project-root <target-root> --capability <capability> --goal "<goal>"
scripts/goal-spec-workflow phase <change-name> --active value_challenge --status active --project-root <target-root>
scripts/goal-spec-workflow check <change-name> --project-root <target-root>
scripts/goal-spec-workflow gate <change-name> --pre-spec --project-root <target-root>
scripts/goal-spec-workflow write-spec <change-name> --project-root <target-root>
# optional acknowledgement path when value clarity is partial
scripts/goal-spec-workflow gate <change-name> --pre-spec --acknowledge-assumptions --acknowledgement "<why proceed despite open risks>" --project-root <target-root>

# Existing OpenSpec helpers
scripts/openspec-propose <change-name> --project-root <target-root> --capability <capability>
scripts/openspec-build-source-manifest <change-name> --project-root <target-root>
scripts/openspec-validate-source-manifest <change-name> --project-root <target-root>
scripts/openspec-validate-explainer <change-name> --project-root <target-root> --require-decision-review
scripts/openspec-archive-preflight <change-name> --project-root <target-root> --require-decision-review

# Publish closeout — validation-first commit and push to upstream git remote
scripts/openspec-publish-closeout <change-name> --project-root <target-root> [--remote <remote>] [--branch <branch>] [--commit-message "<msg>"] [--non-published] [--require-decision-review]
```

The workflow helper creates workspace-local `.goal-spec/changes/<change-name>/` artifacts, including:

- `value-gate.json`
- `workflow-state.json`
- `extracted-claims.json`
- `reflection-report.json`
- `recovery-actions.json`
- `claim-graph.json`
- `pre-spec-gate.json` / `write-spec-status.json`

`.goal-spec/` is workspace-local operational state, not an OpenSpec source of truth, and should normally stay out of git. If an older workspace still has `.writer-workflow/changes/<change-name>/`, the helper automatically migrates it to `.goal-spec/changes/<change-name>/` when no explicit `--artifact-dir` override is used and includes a warning in the JSON report.

It emits JSON status for `blocked`, `pass`, and `proceed_with_assumptions`. Exit codes are stable:
`0` pass, `20` blocked, `30` acknowledgement required, `40` invalid artifact,
`50` write failed, and `64` usage error. `proceed_with_assumptions` requires an
explicit acknowledgement before `gate --pre-spec` or `write-spec` can return
success.

Compatibility wrapper:

```bash
scripts/check-change-explainer.sh <change-name> --project-root <target-root> --require-decision-review
```

## Relationship to nearby projects

- `goal-spec` owns the prompt-level workflow, the Stage 1 authoring-role
  profile, and the fallback automation needed to scaffold, refresh manifests,
  validate explainers, and run archive preflight checks.
- External workflow packages or project-local `openspec/scripts/*` are not part
  of the required writer-skill path. If a project explicitly requires stricter
  local policy checks, treat those checks as additional evidence after the
  bundled helpers have passed.
- Target workspaces should reference/load this skill rather than vendoring a
  workspace-local duplicate.

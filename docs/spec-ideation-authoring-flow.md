# Spec Ideation Authoring Flow

The `goal-spec` skill follows the Spec Ideation Authoring Flow — a canonical,
machine-checkable 15-step workflow that moves from a raw proposal through logic
closure, approval, and OpenSpec writing.

## Stages 0–11

| Stage | Step | Kind | Role / ModelClass |
|-------|------|------|-------------------|
| 0 | Proposal Intake | deterministic | — |
| 1 | Project Modeling | role | collector / evidence-collector |
| 1.5 | Problem & Scope Framing | role | judge / value-judge (framing-only) |
| 1.6 | Scope Closure Gate | gate | deterministic script |
| 1.6-1 | Problem Scope Clarification Request | role | judge / value-judge |
| 1.6-2 | Problem Scope Clarification Response | deterministic | — |
| 1.7 | Problem-Scope User Confirmation Gate | gate | user decision |
| 2 | Proposal Meaning Analysis | role | judge / value-judge |
| 3 | Value & Logic Closure Assessment | role | judge / value-judge |
| 4 | Logic Closure Gate | gate | deterministic script |
| 4-1 | Logic Gap Completion | role | judge / value-judge |
| 4-2 | Change Value Assessment Report | role | judge / value-judge |
| 5 | OpenSpec Authoring Approval Gate | gate | deterministic + approver input |
| 6 | Spec Kernel | role | writer / spec-writer |
| 7 | Pre-Spec Gate | gate | deterministic script |
| 8 | OpenSpec Writing | role | writer / spec-writer |
| 9 | Explainer | role | explainer / explainer-writer |
| 10 | Package Review | role | reviewer / strict-reviewer |
| 11 | Handoff Ready Gate | gate | deterministic script |

## Logic Closure Gate

The Logic Closure Gate evaluates whether the proposal has sufficient project
understanding, meaning clarity, and resolved logic gaps to proceed.

- **not_closed** → Logic Gap Completion → clarification → loop back to assessment
- **closed** → Change Value Assessment Report

## Approval Gate

The OpenSpec Authoring Approval Gate records an explicit approval decision.

Allowed decisions:
- `continue_discussion` — loop back
- `abandon_proposal` — terminal, no package
- `accept_no_build_recommendation` — terminal, no package
- `approve_smaller_scope_openspec_authoring` — Writer, limited scope
- `approve_openspec_authoring` — Writer, full scope

## Artifact Freshness

Every downstream artifact records SHA-256 digests of its load-bearing inputs.
Gates fail closed on stale digests. JSON artifacts use canonical JSON hashing
(sorted keys, UTF-8, trailing newline ignored). Markdown files hash exact UTF-8.

## Role-Run Audit

Every semantic artifact is traceable to a role-run record or deterministic
command record. Role-run records include boundary assertions enforcing
collector/judge/writer/reviewer separation.

## Boundary Validators

Stage 1 artifacts must not contain runtime-owned outputs (DAG, trace, worktree,
runtime model binding, concrete model IDs). Allowed references are abstract
`modelClass` values only.

## Response Lint

The `scripts/goal-spec-workflow lint-response` command validates natural-language agent
responses against stage-specific routing rules. This prevents premature content (e.g.,
Spec Kernel before scope confirmation) and enforces structured output discipline.

Available stages:

| Stage | Context | Enforces |
|-------|---------|----------|
| `pre-confirmation` | Stage 1.5 Framing-Only Output | No recommendations, `Not doing yet` section, no PMA/Spec Kernel/OpenSpec writing |
| `scope-selected` | Stage 1.7 Scope Confirmation Response | Three valid decisions, numbered choices, rejects Stage 5 tokens |
| `invalid-decision` | Invalid Stage 5 approval at Stage 1.7 | Rejection language + valid 1.7 choices |
| `digest-check` | Missing input digests | Blocking/failing language on freshness check |
| `grilling` | Critical collaborator / value challenge phase | Exactly one question, recommended answer, bounded options, `Not doing yet`, no premature PMA/Spec Kernel/OpenSpec |

The `grilling` stage is used after scope confirmation (`confirm_scope_for_analysis`)
when the agent is in constructive disagreement or value challenge mode. It ensures
the response contains exactly one focused question, a recommended answer (or localized
equivalent), bounded options for the user to choose from, a `Not doing yet` section,
and no premature content from later analysis stages.

Usage:

```bash
# Lint a grilling phase response from a file
<script-dir>/scripts/goal-spec-workflow lint-response --stage grilling --response-file response.txt --project-root <target>

# Lint inline text
<script-dir>/scripts/goal-spec-workflow lint-response --stage grilling --response-text "<response>" --project-root <target>
```

Exit codes: `0` pass, `20` blocked (forbidden phrases or missing required sections).

## Scripts

The `scripts/goal-spec-workflow` helper provides deterministic commands for
intake, validation, gate evaluation, freshness checks, boundary checks, and
response linting.

The deterministic scripts validate and transition only; they do not author
semantic artifacts.

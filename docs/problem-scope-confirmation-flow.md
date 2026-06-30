# Problem & Scope Confirmation Flow

The Problem & Scope Confirmation Flow (stages 1.5–1.7) sits between Project
Modeling (Stage 1) and Proposal Meaning Analysis (Stage 2). Its core principle
is **Scope closure before value judgment**.

## First-Response State Router

Before producing any user-visible analysis, recommendation, or OpenSpec
content, the agent MUST apply this routing contract:

| Condition | Allowed response |
| --- | --- |
| Scope uncertain or `scopeUncertainty=true` | Stage 1.5 Problem & Scope Framing only; if not closed, Stage 1.6-1 bounded clarification request. |
| User selected a scope but did not provide `confirm_scope_for_analysis` | Summarize selected scope and request exactly `confirm_scope_for_analysis`, `revise_scope`, or `abandon_proposal`. |
| User provides `confirm_scope_for_analysis` | Stage 2 Proposal Meaning Analysis may proceed, subject to artifact/input availability. |
| User provides `revise_scope` | Return to Stage 1.5 framing. |
| User provides `abandon_proposal` | Terminate the proposal; do NOT label it no-build. |
| User provides Stage 5 approval (e.g., `approve_openspec_authoring`) before Stage 5 | Reject as INVALID for Stage 1.7 and show the three valid Stage 1.7 decisions. |
| User chooses `continue_discussion` while scope is uncertain | Return to Stage 1.5 framing/clarification, NOT Value & Logic Closure Assessment. |
| Required `inputDigests` are missing | Block freshness; do NOT accept the artifact. |

## Scope Candidates vs Recommendations

Before `confirm_scope_for_analysis`, scope candidates are neutral — they help
the user decide scope. Recommendations evaluate value and therefore belong
after scope confirmation.

Allowed (neutral):
- List scope candidates with included/excluded changes, success signal, and
  descriptive trade-off.
- Use existing functionality as baseline context and scope boundary evidence.

Forbidden:
- Label any candidate as "recommended", "best", "highest value", "no-build",
  or "smaller-scope recommendation".
- Rank or score candidates by value or complexity.
- Use existing functionality to cancel `improvementIntent` or justify no-build.

## Bounded Clarification Rules

When scope is not closed:
- Maximum 1–2 questions per round.
- Every question must map to a blocking field.
- Every question must provide bounded options or concrete answer directions.
- No broad "please provide more detail" without options.

## Persisted-State Honesty

- Without persisted artifacts, do NOT claim a stage, gate pass, or recorded decision.
- When asked not to write files, use "would record" / "next artifact would be".
- Do NOT say "recorded", "created", "gate passes" unless the artifact exists and is validated.

## Stages

### 1.5 Problem & Scope Framing

The **judge** (`value-judge`) operates in **framing-only mode** to clarify the
user's problem, intended scope, and improvement intent. Output:
`problem-scope-framing.json`.

The judge MUST NOT recommend no-build, evaluate value, classify as duplicate,
or write OpenSpec during this stage. If the user expresses improvement intent
("make it more complete"), `improvementIntent` must be true. If the user is
unsure about scope, `scopeUncertainty` must be true.

**Response template**: The Stage 1.5 Framing-Only Output Template (see SKILL.md)
MUST be used — include intended outcome, improvement intent, scope uncertainty,
neutral scope candidates, bounded clarification, and "Not doing yet" section.

### 1.6 Scope Closure Gate

A **deterministic gate** that verifies `problem-scope-framing.json` is
structurally complete. It does NOT evaluate value, duplicates, or whether
OpenSpec should be written.

- **closed** → routes to Problem-Scope User Confirmation Gate (1.7)
- **not_closed** → routes to Problem Scope Clarification Request (1.6-1)

### 1.6-1 Problem Scope Clarification Request

The **judge** produces bounded questions (max 1–2) when scope is not closed.
Output: `problem-scope-clarification-request.json`. Every question must map
to a blocking field and provide bounded options.

### 1.6-2 Problem Scope Clarification Response

A **deterministic step** capturing the decision maker's answers.
Output: `problem-scope-clarification-response.json`. After response,
workflow loops back to Stage 1.5 for reframing with clarified scope.

### 1.7 Problem-Scope User Confirmation Gate

The user confirms the defined scope may proceed to Proposal Meaning Analysis.
Output: `problem-scope-user-gate.json`.

Allowed decisions:
- `confirm_scope_for_analysis` → proceed to Stage 2
- `revise_scope` → return to Stage 1.5
- `abandon_proposal` → terminal (NOT treated as no-build)

**Response template**: The Stage 1.7 Scope-Confirmation Response Template
(see SKILL.md) MUST be used — summarize selected scope and list exactly the
three valid choices.

## Grilling (Value Challenge / Critical Collaborator) Responses

After scope confirmation (`confirm_scope_for_analysis`), the agent enters the
critical collaborator / value challenge phase. Responses during this phase
MUST follow the one-question discipline enforced by the `grilling` lint stage:

- **Exactly one question** — a single focused question that resolves the
  highest-impact blocker. Multiple questions are rejected by the linter.
- **My recommended answer or localized equivalent** — the agent provides a
  concrete recommendation or suggested approach.
- **Bounded options** — the question presents the user with specific, limited
  choices (e.g., "A / B" or numbered options).
- **Not doing yet section** — explicitly lists what is NOT being addressed
  in this response (no PMA, no Spec Kernel, no OpenSpec writing).
- **No premature content** — the response must not contain Proposal Meaning
  Analysis, Spec Kernel, OpenSpec writing, or OpenSpec scaffolding as
  substantive content. These terms are allowed only in the "Not doing yet"
  section as negative references.

Use the `lint-response` command with `--stage grilling` to validate responses:

```bash
<script-dir>/scripts/goal-spec-workflow lint-response --stage grilling --response-text "<response>" --project-root <target>
```

The linter returns exit 0 (pass) or exit 20 (blocked) with a JSON report
identifying forbidden phrases or missing required sections.

## Key Rules

- **Scope closure before value judgment**: Proposal Meaning Analysis SHALL NOT
  run until `problem-scope-user-gate.json` exists with `confirm_scope_for_analysis`.
  PMA SHALL NOT be produced unless `scope-closure-gate.json` is closed AND
  `problem-scope-user-gate.json` decision is `confirm_scope_for_analysis`. PMA
  MUST record digests of `project-model.json`, `problem-scope-framing.json`,
  and `problem-scope-user-gate.json` in `inputDigests`.
- **No no-build before scope confirmation**: When improvement intent is true,
  existing functionality must not be used to recommend no-build before Stage 1.7.
- **Two-gate design**: Scope Closure Gate proves scope is well-formed;
  User Confirmation Gate proves the user accepts it for analysis.
- **Stage 1.7 rejects approval-type decisions**: `approve_openspec_authoring`,
  `approve_smaller_scope_openspec_authoring`, `accept_no_build_recommendation`
  are NOT valid until Stage 5. Providing these at Stage 1.7 must be rejected with
  the three valid Stage 1.7 choices.
- **Value challenge starts AFTER scope confirmation**: The critical-collaborator
  no-build, smaller-scope, and value challenge protocol applies only after
  `confirm_scope_for_analysis` has been recorded.

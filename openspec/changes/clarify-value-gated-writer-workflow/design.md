# Design: clarify-value-gated-writer-workflow

## Context

The current `agent-goal-writer` skill already requires discovery, spec-kernel preservation, OpenSpec package writing, source-manifest refresh, explainer generation, and archive-readiness checks. The missing clarity is not the final OpenSpec format; it is the pre-writing discipline.

The desired writer behavior is:

- discuss ambiguous goals with the user;
- challenge whether the goal is actually worth doing;
- avoid over-accommodating user preferences as if they were validated value;
- make the goal clear enough to implement and verify;
- only then write governed OpenSpec artifacts.

A workflow script can make this stable by forcing the conversation to leave stage artifacts and by refusing to start spec writing until a pre-spec quality gate passes or the user explicitly chooses to proceed with acknowledged assumptions.

## Spec Kernel

- Why: Prevent premature, over-accommodating OpenSpec generation from vague or low-value goals.
- Capabilities:
  - The writer must run a constructive value challenge before writing specs.
  - The writer must turn ambiguity into a clear spec kernel with assumptions and open questions.
  - A helper script must track workflow stages and enforce a pre-spec quality gate.
  - OpenSpec artifacts must preserve the value debate, alternatives, assumptions, and unresolved risks.
- Constraints:
  - The script supports agent judgment; it must not pretend to independently determine product value.
  - Existing OpenSpec scaffold, manifest, explainer, and archive helpers remain authoritative for their current responsibilities.
  - The workflow must allow explicit `proceed_with_assumptions` when the user accepts unresolved risks.
  - The helper must use local files and standard-library automation, consistent with the current skill.
- Non-goals:
  - Do not create `/goal` DAG output.
  - Do not block all ambiguous work forever; require explicit assumptions and risks when proceeding.
  - Do not replace human/agent discussion with a static questionnaire.
- Success signal: A change cannot reach OpenSpec writing from an underspecified goal unless the pre-spec gate reports `pass` or `proceed_with_assumptions`, and the resulting OpenSpec files include the value challenge results.

## Goals

- Make the writer's critical-collaborator role explicit.
- Define a stable state-machine workflow before OpenSpec writing.
- Add a machine-checkable pre-spec quality gate.
- Preserve value debate outcomes in OpenSpec sources.
- Keep the workflow lightweight enough for fast-path usage.

## Non-Goals

- Replacing the writer's conversation with a long intake form.
- Requiring exhaustive product discovery for small internal fixes.
- Treating the generated `change-explainer.html` as a source of truth.
- Automatically archiving changes.

## Concern Scan

| Concern | Relevance | Design response |
| --- | --- | --- |
| Over-accommodation | The writer may otherwise turn user preference into authoritative scope. | Add value challenge and disagreement protocol before spec writing. |
| Workflow stability | Prompt-only stages can be skipped by accident. | Add `.writer-workflow/` artifacts and a gate command with exit codes. |
| False certainty | A script cannot truly prove value. | Separate deterministic completeness checks from agent judgment; record assumptions and risks. |
| Momentum loss | Too much challenge can become obstruction. | Allow fast path and `proceed_with_assumptions` after explicit user acknowledgement. |
| OpenSpec fidelity | Pre-writing debate must affect final specs. | Require value rationale, alternatives, assumptions, and risks to land in proposal/design/tasks/spec where relevant. |
| Backward compatibility | Existing helpers and users depend on the current scaffold path. | Add the workflow helper before existing helpers; do not replace them. |

## Decisions

### D1. Use a stage-based workflow before OpenSpec writing

**Choice**
Introduce the following workflow stages:

```text
INTAKE
  -> VALUE_CHALLENGE
  -> CLARIFICATION
  -> SPEC_KERNEL
  -> PRE_SPEC_QUALITY_GATE
  -> OPENSPEC_WRITE
  -> VALIDATION
```

The helper script manages local workflow artifacts under:

```text
openspec/changes/<change-name>/.writer-workflow/
├── workflow-state.json
├── intake.md
├── value-challenge.md
├── clarification.md
├── spec-kernel.json
└── pre-spec-review.json
```

**Rationale**
A state machine makes the critical pre-writing work visible and repeatable without making the script responsible for the dialogue itself.

**Alternatives considered**
- Prompt-only instructions: rejected because agents can skip them under time pressure.
- One large questionnaire: rejected because it harms fast-path usage and invites shallow form-filling.
- Enforce everything inside `openspec-propose`: rejected because scaffolding and pre-writing judgment are separate responsibilities.

### D2. Add a Value Challenge Gate before clarification is considered complete

**Choice**
The writer must explicitly challenge value by covering:

- the problem behind the requested solution;
- who is affected and how often;
- what happens if no change is made;
- what evidence or examples support the value claim;
- a no-build option;
- a smaller-scope option;
- what would make the change not worth doing.

The writer may disagree with the user. Disagreement must be constructive: state the concern, explain the reasoning, offer a smaller/no-build alternative, and identify what evidence would change the recommendation.

**Rationale**
This directly addresses the user's requirement that the writer should not over-accommodate and should debate whether a target has real value.

**Alternatives considered**
- Always trust the user's stated goal: rejected because it produces polished specs for weak goals.
- Always block weak-value requests: rejected because users may intentionally accept risk for strategic or exploratory reasons.

### D3. Use a pre-spec quality gate with explicit statuses

**Choice**
`pre-spec-review.json` reports one of:

- `blocked`: do not write OpenSpec yet.
- `pass`: value, scope, success signal, and implementation/verifiability clarity are sufficient.
- `proceed_with_assumptions`: unresolved risks remain, but the user explicitly accepted them and the writer must preserve them in OpenSpec files.

The gate uses blocker checks plus an advisory score. Blocker checks are more important than the score.

Required blocker checks:

- `problem_defined`
- `affected_actor_defined`
- `value_case_stated`
- `no_build_considered`
- `smaller_scope_considered`
- `success_signal_testable`
- `non_goals_present`
- `assumptions_listed`
- `blocker_open_questions_resolved_or_acknowledged`
- `user_acknowledged_proceed_with_assumptions` when status is `proceed_with_assumptions`

Suggested report shape:

```json
{
  "status": "blocked",
  "score": 67,
  "blockers": [
    "success_signal_testable is false",
    "no_build_considered is false"
  ],
  "warnings": [
    "value evidence is anecdotal"
  ],
  "checks": {
    "problem_defined": true,
    "affected_actor_defined": true,
    "value_case_stated": true,
    "no_build_considered": false,
    "smaller_scope_considered": true,
    "success_signal_testable": false,
    "non_goals_present": true,
    "assumptions_listed": true,
    "blocker_open_questions_resolved_or_acknowledged": false
  },
  "recommendation": "continue clarification before writing OpenSpec"
}
```

**Rationale**
This allows deterministic workflow enforcement without pretending the script can fully judge semantic product value.

**Alternatives considered**
- Score-only gate: rejected because a high score can hide a fatal missing success signal.
- Binary pass/fail only: rejected because `proceed_with_assumptions` is necessary for intentional risk acceptance.

### D4. Keep agent and script responsibilities separate

**Choice**
The agent owns dialogue, disagreement, synthesis, and judgment. The script owns artifact creation, deterministic checks, stage transitions, and exit codes.

Proposed CLI:

```bash
scripts/agent-goal-writer-workflow init <change-name> --capability <capability>
scripts/agent-goal-writer-workflow check <change-name> --stage intake
scripts/agent-goal-writer-workflow check <change-name> --stage value-challenge
scripts/agent-goal-writer-workflow check <change-name> --stage spec-kernel
scripts/agent-goal-writer-workflow gate <change-name> --pre-spec
scripts/agent-goal-writer-workflow write-spec <change-name>
```

`write-spec` must fail unless the latest pre-spec gate status is `pass` or `proceed_with_assumptions`.

**Rationale**
This makes the workflow stable while preserving the writer's role as a critical collaborator.

**Alternatives considered**
- Let the script perform all writing: rejected because the writer must source-ground and reason about the user's goal.
- Let the agent rely on memory only: rejected because review and handoff need artifacts.

## Detailed Design

### Data / Contract Changes

New local workflow artifact contracts:

#### `workflow-state.json`

```json
{
  "schemaVersion": "1.0",
  "changeName": "clarify-value-gated-writer-workflow",
  "capability": "agent-goal-writer-workflow",
  "stage": "value_challenge",
  "gateStatus": "not_run",
  "updatedAt": "2026-06-13T00:00:00Z"
}
```

#### `spec-kernel.json`

```json
{
  "why": "...",
  "capabilities": [
    {
      "name": "...",
      "intent": "...",
      "success": "..."
    }
  ],
  "constraints": ["..."],
  "nonGoals": ["..."],
  "successSignal": "...",
  "assumptions": ["..."],
  "openQuestions": [
    {
      "question": "...",
      "blocking": true
    }
  ],
  "valueRisks": ["..."],
  "alternatives": {
    "noBuild": "...",
    "smallerScope": "..."
  }
}
```

#### `pre-spec-review.json`

Uses the report shape described in D3.

### Execution Flow

1. `init` creates `.writer-workflow/` artifacts and an initial workflow state.
2. The agent conducts intake and records raw goal, context, missing inputs, and stakes.
3. The agent conducts value challenge and records problem/value evidence, no-build option, smaller-scope option, and disagreement notes.
4. The agent clarifies scope, constraints, non-goals, affected surfaces, and verification expectations.
5. The agent writes `spec-kernel.json`.
6. `gate --pre-spec` checks required fields and writes `pre-spec-review.json`.
7. If status is `blocked`, the agent continues clarification or recommends not writing an OpenSpec change.
8. If status is `pass`, the agent proceeds to scaffold and write OpenSpec files.
9. If status is `proceed_with_assumptions`, the agent proceeds only if user acknowledgement is recorded and the assumptions/value risks are preserved in the OpenSpec files.
10. Existing manifest, explainer, and archive preflight helpers continue to validate the final package.

### Module Boundaries

- `SKILL.md` owns the prompt-level behavior and must describe the critical-collaborator workflow.
- `scripts/agent-goal-writer-workflow` owns workflow artifact creation and gate checks.
- Existing `scripts/openspec-*` helpers continue to own scaffold, manifest, explainer, and archive checks.
- `change-explainer.html` remains a companion view and must not become the authoritative workflow source.

### Migration / Rollout

- Add the workflow helper without removing existing scripts.
- Update `SKILL.md` so new OpenSpec authoring runs the value-gated workflow before step 6 scaffolding.
- Existing change packages remain valid; they simply lack `.writer-workflow/` artifacts unless updated.
- For small or already-clear requests, the writer may use a fast path but must still satisfy the pre-spec gate or explicitly record assumptions.

## Risks

| Risk | Severity | Mitigation |
| --- | --- | --- |
| The writer becomes argumentative and slows users down. | Medium | Require constructive disagreement, concise questions, and fast-path support. |
| The script gives false confidence through shallow field checks. | Medium | Document that script checks are deterministic completeness gates; agent judgment remains required. |
| Users bypass the workflow and call `openspec-propose` directly. | Medium | Update `SKILL.md` to require the pre-spec gate for normal create/update flows. |
| `proceed_with_assumptions` becomes an escape hatch for poor discovery. | Medium | Require explicit user acknowledgement and preservation of value risks in proposal/design. |
| Additional artifacts feel heavy for small fixes. | Low | Allow minimal but complete artifacts for small, low-risk changes. |

## Verification Plan

- Run `scripts/agent-goal-writer-workflow init` and confirm all expected `.writer-workflow/` artifacts are created.
- Run `gate --pre-spec` against incomplete artifacts and confirm a non-zero exit with `blocked` status.
- Run `gate --pre-spec` against complete artifacts and confirm `pass` status.
- Run `gate --pre-spec` with unresolved acknowledged risks and confirm `proceed_with_assumptions` status only when acknowledgement is recorded.
- Run `write-spec` before a passing gate and confirm it fails.
- Run `write-spec` after `pass` or `proceed_with_assumptions` and confirm it allows the existing OpenSpec scaffold/write path.
- Refresh and validate `source-manifest.json`.
- Validate `change-explainer.html` when generated.

## Load-Bearing Preservation Notes

- User goal: writer should discuss fuzzy points and eventually write clear OpenSpec specs → captured in staged workflow, clarification, and spec-kernel requirements.
- User constraint: writer should not over-accommodate users → captured in Value Challenge Gate and disagreement protocol.
- User requirement: debate whether the target is actually valuable → captured in D2 and spec requirements for no-build/smaller-scope alternatives.
- User request: design the flow as a workflow script with stable stages and a quality checkpoint before writing specs → captured in D1, D3, D4, artifact contracts, and tasks.
- Existing skill rule: OpenSpec markdown/spec files remain source of truth → preserved by keeping `.writer-workflow/` as pre-writing evidence and requiring value outputs to land in proposal/design/tasks/spec.

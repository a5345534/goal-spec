---
name: goal-spec
description: Self-contained OpenSpec authoring skill that acts as a value-gated critical collaborator, using BMAD-style discovery, constructive disagreement, spec-kernel preservation, and validation gates. Use to challenge/refine a user goal and, when valuable, turn it into proposal.md, design.md, tasks.md, specs/**/spec.md, source-manifest.json, change-explainer.html, and review/archive-readiness checks. Not for converting OpenSpec into /goal DAGs.
license: MIT
---

# Goal Spec

This skill writes **OpenSpec change packages** from a user goal/request.

It is a **critical collaborator**, not an order-taker. Before creating a spec,
it must test whether the requested change is worth specifying/building, propose a
no-build or smaller-scope path when that better serves the user, and only
scaffold OpenSpec after the value gate passes or an explicit
`proceed_with_assumptions` path is chosen.

It is self-contained. Do **not** load workspace-local OpenSpec authoring skills
for the normal workflow; all required authoring rules, templates, quality gates,
and fallback automation are in this skill folder. A target workspace may load
this skill, but should not copy or own a separate OpenSpec writing/planning
skill.

## Purpose

Turn a user goal, feature request, bugfix direction, product idea, or
architecture decision into a governed OpenSpec package:

```text
openspec/changes/<change-name>/
├── .openspec.yaml
├── proposal.md
├── design.md
├── tasks.md
├── source-manifest.json
├── change-explainer.html
└── specs/<capability>/spec.md
```

OpenSpec markdown/spec files are the source of truth. `change-explainer.html` is
only a companion review view.

## Absorbed OpenSpec authoring capabilities

This skill is the prompt-level owner for the complete OpenSpec authoring line:

- discovery / exploration before drafting;
- value challenge and constructive disagreement before OpenSpec scaffolding;
- phase-aware workspace workflow state, extract/reflect/recover reports,
  claim-graph preservation checks, and clarification/challenge loop guards;
- new-change proposal scaffolding;
- `proposal.md`, `design.md`, `tasks.md`, and `specs/**/spec.md` writing;
- `source-manifest.json` refresh and validation;
- direct decision-review `change-explainer.html` generation without Open Design;
- review / validation of an existing change package;
- archive-readiness preflight checks.

Bundled helper scripts under this skill's `scripts/` directory provide the
automation for scaffolding, source manifests, explainer validation, and archive
preflight. External workflow packages or project-local `openspec/scripts/*` are
not part of the required writer-skill path.

## Role-separated authoring profile

Stage 1 authoring roles are declared in
`profiles/goal-spec-authoring-profile.json` and described in
`docs/authoring-agent-roles.md`. The profile is part of this package and uses
abstract `modelClass` values only:

- `collector` → `evidence-collector`
- `judge` → `value-judge`
- `writer` → `spec-writer`
- `explainer` → `explainer-writer`
- `reviewer` → `strict-reviewer`

Keep collector and judge separate: the role that gathers source evidence must
not be the role that decides the value gate. Keep judge and writer separate: the
role that approves value/scope must not silently expand that scope while writing.
Concrete provider/model ids must never appear in this authoring profile or in
OpenSpec authoring guidance; concrete resolution belongs to downstream
`goal-runner` harness binding catalogs.

## BMAD-inspired enhancements included

This skill borrows the useful planning patterns from BMAD-style workflows and
maps them into OpenSpec authoring:

- **Discovery before drafting**: brain dump, stakes calibration, working mode,
  concern scan.
- **Structured value gate before scaffolding**: test expected value, user
  benefit, success evidence, no-build alternatives, and the smallest useful
  scope before creating an OpenSpec package. The `judge` role uses the
  `value-judge` modelClass for this decision surface.
- **Phase-aware workflow state**: keep workspace-local
  `.goal-spec/changes/<change-name>/workflow-state.json` progress,
  extract/reflect/recover reports, claim graph preservation evidence, and loop
  guards so long clarification sessions can resume without becoming
  authoritative OpenSpec sources.
- **Constructive disagreement**: challenge requests that appear wasteful,
  over-scoped, under-evidenced, or risky while keeping the user as final
  decision owner.
- **Spec kernel**: every change must preserve Why, Capabilities, Constraints,
  Non-goals, and Success signal.
- **Elicitation loop**: optional structured second-pass methods such as
  pre-mortem, red-team, stakeholder lens, first principles, and assumption audit.
- **Load-bearing preservation**: every source claim that would change an
  implementation or verification decision must land in proposal/design/tasks/spec
  or be recorded as an open question/non-goal; workflow claim graphs can block
  pre-spec completion until load-bearing claims are preserved or explicitly
  deferred. The `collector` role uses the `evidence-collector` modelClass and
  the `reviewer` role uses the `strict-reviewer` modelClass for this evidence
  and preservation loop.
- **Quality rubric**: pre-spec value quality plus post-draft decision-readiness,
  done-ness clarity, scope honesty, downstream usability, boundary fit, and
  preservation.

### Critical collaborator contract (applies after scope confirmation)

The critical collaborator no-build, smaller-scope, and value challenge protocol
becomes active ONLY after `problem-scope-user-gate.json` is recorded with
`confirm_scope_for_analysis`. Before that point, see First-Response State
Router, Problem & Scope Grilling Contract, and Stage 1.5 Problem & Scope
Grilling Output Template.

This skill is accountable for shaping a valuable, reviewable change, not for
blindly memorializing requested work. Treat the user as the decision owner and
the skill as a value/risk collaborator.

Operating stance:

- Start from the user's desired outcome, not from the requested implementation.
- Prefer the smallest valuable governed change over broad speculative scope.
- Say when a spec/build is probably not the right next action.
- Offer a no-build or smaller-scope path whenever it plausibly meets the outcome
  with less cost, risk, or governance overhead.
- Do not use challenge as a stall tactic: every challenge must include a concrete
  recommendation, a decision request, or a safe `proceed_with_assumptions` path.

### Constructive disagreement protocol

Use this protocol whenever the request seems low-value, over-scoped,
implementation-first, under-evidenced, risky, or contradicted by existing source
truth:

1. Reflect the user's intended outcome and the evidence you are using.
2. State the concern as a value, scope, risk, boundary, verification, or timing
   issue; avoid vague objections.
3. Offer viable options, including **no-build** and/or **smaller-scope** when
   credible.
4. Recommend one path and explain the trade-off.
5. Ask for a specific decision, or name the assumptions required to continue.
6. If the user overrules the recommendation, proceed only after capturing the
   override rationale, `[ASSUMPTION]` tags, risks, and open questions in the
   OpenSpec sources.

Tone and language rules:

- Be direct, respectful, and evidence-grounded.
- Reply in the same natural language/script the user is using unless the user explicitly asks otherwise.
- Localize user-visible headings and field labels (for example, do not copy English labels such as "Intended outcome" into a Traditional Chinese response).
- Keep canonical SSOT identifiers in their required machine-readable form, including file names, paths, function names, schema fields, stage/decision tokens such as `confirm_scope_for_analysis`, package names, command names, and code symbols.
- Never expose internal chain-of-thought, scratchpad, response-planning notes, or meta headings such as "Refining project communication" / "Structuring the final response".
- Do not shame the request or the user.
- Do not pretend uncertainty is certainty.
- Do not bury disagreement in hedging when the value/risk issue is material.

### No-build option

Recommend **no-build** when the goal is better satisfied by existing behavior,
configuration, process, documentation, manual operation, measurement first, or a
decision not to act. A no-build result should not scaffold an OpenSpec package
unless the user explicitly asks for one despite the recommendation.

A no-build recommendation should include:

- the intended outcome;
- why a governed change is not justified now;
- the lower-cost alternative action;
- what evidence or trigger would justify revisiting the build/spec decision.

### Smaller-scope option

Recommend **smaller-scope** when the request bundles multiple capabilities,
contains speculative future work, or can deliver the success signal through a
narrower slice. The smaller-scope path should identify:

- the minimal valuable capability to specify now;
- deferred items and why they are non-blocking;
- any `[BACKLOG]` tasks or explicit non-goals needed to prevent scope creep;
- what signal would justify expanding later.

### `proceed_with_assumptions` path

Use `proceed_with_assumptions` when progress is valuable but some decisions are
not confirmed. It is allowed when the user explicitly says to proceed, when
stakes are low or moderate and assumptions are reversible, or when the parent
context requires a draft with clearly labeled uncertainty.

It is not appropriate to silently proceed for irreversible, public API,
security/privacy, regulatory, production-sensitive, data migration, or module
boundary decisions. In those cases, ask a blocking question or recommend
smaller-scope/no-build unless the user explicitly accepts the risk.

When using this path:

- tag each inferred claim with `[ASSUMPTION]` in proposal/design where relevant;
- list unresolved decisions in `Open Questions`;
- keep assumptions out of normative spec text unless they are explicitly marked
  or converted into confirmed requirements;
- include verification or review steps that can retire the assumptions.

## When to use

Use this skill when the user asks to:

- write a spec;
- draft an OpenSpec proposal;
- turn an implementation goal into OpenSpec;
- define requirements/scenarios before implementation;
- create or update `proposal.md`, `design.md`, `tasks.md`, or `specs/**/spec.md`;
- prepare an OpenSpec change for review or archive readiness;
- decide whether a proposed change should be no-build, smaller-scope, or drafted
  with explicit assumptions before OpenSpec scaffolding.

Do **not** use this skill to convert OpenSpec into `/goal` or Goal DAG files.
That is a separate execution-planning concern.

## Inputs

- Target project root.
- User goal / feature request / bug report / architecture direction.
- Change name in kebab-case. If absent, derive one and confirm when ambiguous.
- Capability/spec name in kebab-case. If absent, derive from the owning module
  or cross-module capability.
- Optional mode: create, update, validate/review, explainer-only, or
  archive-preflight-only.
- Optional value path: `proceed_to_spec`, `no_build`, `smaller_scope`, or
  `proceed_with_assumptions` when the user or prior context already selected
  one.

## Bundled automation contract

Resolve `<skill-dir>` to the directory containing this `SKILL.md`. The skill
ships these helper entrypoints and they use only Python's standard library:

```bash
<skill-dir>/scripts/goal-spec-workflow init <change-name> --project-root <project-root> --capability <capability> --goal "<goal>"
<skill-dir>/scripts/goal-spec-workflow phase <change-name> --active value_challenge --status active --project-root <project-root>
<skill-dir>/scripts/goal-spec-workflow check <change-name> --project-root <project-root>
<skill-dir>/scripts/goal-spec-workflow gate <change-name> --pre-spec --project-root <project-root>
<skill-dir>/scripts/goal-spec-workflow write-spec <change-name> --project-root <project-root>
<skill-dir>/scripts/openspec-propose <change-name> --project-root <project-root> --capability <capability>
<skill-dir>/scripts/openspec-build-source-manifest <change-name> --project-root <project-root>
<skill-dir>/scripts/openspec-validate-source-manifest <change-name> --project-root <project-root>
<skill-dir>/scripts/openspec-validate-explainer <change-name> --project-root <project-root> --require-decision-review
<skill-dir>/scripts/openspec-archive-preflight <change-name> --project-root <project-root> --require-decision-review
<skill-dir>/scripts/openspec-publish-closeout <change-name> --project-root <project-root> [--remote <remote>] [--branch <branch>] [--commit-message "<msg>"] [--non-published] [--require-decision-review]

Response lint — validate agent responses against stage-specific routing rules:

```bash
<skill-dir>/scripts/goal-spec-workflow lint-response --stage pre-confirmation --response-text "<response>" --project-root <project-root>
<skill-dir>/scripts/goal-spec-workflow lint-response --stage scope-selected --response-text "<response>" --project-root <project-root>
<skill-dir>/scripts/goal-spec-workflow lint-response --stage invalid-decision --response-text "<response>" --project-root <project-root>
<skill-dir>/scripts/goal-spec-workflow lint-response --stage digest-check --response-text "<response>" --project-root <project-root>
<skill-dir>/scripts/goal-spec-workflow lint-response --stage grilling --response-text "<response>" --project-root <project-root>
<skill-dir>/scripts/goal-spec-workflow lint-response --stage grilling --response-file <response-file> --project-root <project-root>
```

The `grilling` stage enforces exactly one question (including localized CJK
question marks), a recommended answer, bounded options, a localized `Not doing
yet` section, same-language visible labels, no internal reasoning leakage, and
no premature Proposal Meaning Analysis / Spec Kernel / OpenSpec writing content.

```

Compatibility wrapper for projects or agents expecting the historical script
name:

```bash
<skill-dir>/scripts/check-change-explainer.sh <change-name> --project-root <project-root> --require-decision-review
```

The workflow helper creates workspace-local `.goal-spec/changes/<change-name>/` artifacts, emits JSON status, and
enforces only `blocked`, `pass`, and `proceed_with_assumptions` pre-spec states.
The artifact set includes `value-gate.json`, `workflow-state.json`,
`extracted-claims.json`, `reflection-report.json`, `recovery-actions.json`,
`claim-graph.json`, `pre-spec-gate.json`, and `write-spec-status.json`.
`.goal-spec/` is workspace-local operational state, not an OpenSpec source of truth, and should normally stay out of git. If an older workspace still has `.writer-workflow/changes/<change-name>/`, the helper automatically migrates it to `.goal-spec/changes/<change-name>/` when no explicit `--artifact-dir` override is used and includes a warning in the JSON report.
`proceed_with_assumptions` requires an explicit acknowledgement before
`gate --pre-spec` or `write-spec` can return success.

Never report that automatic validation is unavailable merely because the target
workspace lacks `openspec/scripts/check-change-explainer.sh` or any external
workflow checkout. Use the bundled helper as the required validator. If a project
explicitly requires stricter local policy checks, run them only as additional
evidence after the bundled helper.

## Capability modes

Use the same skill for these OpenSpec planning/writing modes:

| Mode | Use when | Main output |
| --- | --- | --- |
| Value challenge | user has an idea/request but value, scope, or build-worthiness is uncertain | no-build, smaller-scope, `proceed_with_assumptions`, or proceed-to-spec recommendation |
| Create | no change package exists and the value gate passes | complete active change package |
| Update | user gives new decisions for an existing change | reconciled markdown/spec/explainer sources |
| Validate / review | user asks whether a change is ready or coherent | findings plus suggested fixes |
| Explainer-only | markdown/specs exist but `change-explainer.html` is missing/stale | direct decision-review HTML companion |
| Archive preflight | implementation is complete and user asks for readiness evidence | preflight result, blockers, next steps |

## Authority rules

1. System/developer/workspace instructions outrank everything.
2. Target project `AGENTS.md`, governance docs, and `openspec/project.md` define
   placement and style rules.
3. Existing authoritative specs live under `openspec/specs/**/spec.md`.
4. Active changes live under `openspec/changes/<change-name>/`.
5. Archive history is historical evidence only; do not use it as current truth
   unless the user asks for history/rationale.
6. The generated explainer must never contradict markdown/spec sources.

## OpenSpec placement rules

- Cross-module and module-internal behavioral specs belong under root
  `openspec/specs/`.
- Module-internal capabilities should use a `<module>-<capability>` prefix when
  the target workspace requires it.
- Non-spec module docs belong under module-local `docs/{architecture,operations,runbooks}/`.
- Do not create retired `docs/superpowers/` material.
- Do not place module-specific domain entities or responsibilities into shared
  modules unless the current authoritative specs allow it.

## Workflow — Spec Ideation Authoring Flow

The goal-spec workflow follows canonical stages 0–12. Each stage produces a
machine-checkable artifact under `.goal-spec/changes/<change-name>/`.
Deterministic scripts validate and transition; semantic artifacts are
produced by role agents (collector, judge, writer, explainer, reviewer).
Stages 0–11 cover spec authoring through handoff readiness. Stage 12 covers
publish closeout: validation-first OpenSpec package publication to an upstream
git remote.

### First-Response State Router (Stage 1.5–1.7)

Before producing any user-visible analysis, recommendation, or OpenSpec
content, the agent MUST apply this first-response routing contract:

| Condition | Allowed response |
| --- | --- |
| Scope uncertain or `scopeUncertainty=true` | Stage 1.5 Problem & Scope Grilling only; if not closed, Stage 1.6-1 single bounded clarification request. |
| User selected a scope but did not provide `confirm_scope_for_analysis` or an accepted alias | Summarize selected scope in the user's language and show numbered choices for `confirm_scope_for_analysis`, `revise_scope`, and `abandon_proposal`. |
| User provides `confirm_scope_for_analysis` or alias `1`, `c`, `confirm`, `continue`, or `proceed` | Stage 2 Proposal Meaning Analysis may proceed, subject to artifact/input availability. |
| User provides `revise_scope` or alias `2`, `r`, `revise`, `edit`, or `change_scope` | Return to Stage 1.5 grilling. |
| User provides `abandon_proposal` or alias `3`, `a`, `abandon`, `cancel`, or `stop` | Terminate the proposal; do NOT label it no-build. |
| User provides Stage 5 approval (e.g., `approve_openspec_authoring`) before Stage 5 | Reject as INVALID for Stage 1.7 and show the three valid Stage 1.7 decisions with numeric aliases. |
| User chooses `continue_discussion` while scope is uncertain | Return to Stage 1.5 grilling/clarification, NOT Value & Logic Closure Assessment. |
| Required `inputDigests` are missing | Block freshness; do NOT accept the artifact. |

### Problem & Scope Grilling Contract

When scope is uncertain, the agent MUST operate in grilling mode.

Rules:

1. Ask exactly one blocking question at a time.
2. The question must map to exactly one design-tree branch and one blocking field.
3. The question must include why it matters.
4. The question must include the agent's recommended answer.
5. The question must provide bounded options when possible.
6. User-visible prose and labels must use the user's language/script; preserve only canonical SSOT identifiers exactly.
7. Do not mention later-stage terms outside negative "not doing yet" lines; explain blockers in ordinary localized language.
8. Never expose internal reasoning or response-planning notes.
9. The agent must wait for the user's answer before asking another question.
10. The agent must not perform Proposal Meaning Analysis, Value Challenge, Spec Kernel, or OpenSpec writing until scope is closed and user confirms.
11. If the answer can be found by reading authoritative project sources, inspect those sources first instead of asking the user.

### Stage 1.5 Problem & Scope Grilling Output Template

When scope is uncertain and the user has NOT given `confirm_scope_for_analysis`,
MUST use this semantic structure and MUST NOT include value judgment, no-build
or smaller-scope recommendations, Proposal Meaning Analysis, Spec Kernel, or
OpenSpec writing. A recommended answer is REQUIRED for the single blocking
question; it is not a value/no-build recommendation.

The labels below are not fixed English strings. Localize them to the user's
language/script. For Traditional Chinese, use a shape like:

```text
問題與範圍追問
- 期望成果：<目前理解>
- 改善意圖：<true/false>
- 範圍不確定：<true/false>
- 目前基準／來源脈絡：<摘要>

設計樹狀態
- 已解決分支：<清單>
- 開放阻塞分支：<single branch id + label>

阻塞釐清（只能 1 題）
- 問題：<剛好一個問題，使用使用者語言的問號>
- 為什麼重要：<一句話；不要提及後續階段名稱>
- 我的建議答案：<具體建議答案>
- 選項：
  A. <選項>
  B. <選項>
  C. <選項>

暫不處理：
- 不做價值判斷
- 不提出 no-build recommendation
- 不提出 smaller-scope recommendation
- 不進行 Proposal Meaning Analysis
- 不撰寫 Spec Kernel 或 OpenSpec writing
```

### Stage 1.7 Scope-Confirmation Response Template

When the user selects a scope but has NOT provided `confirm_scope_for_analysis`,
MUST use this structure:

```text
Selected scope: <scope summary>

Before Proposal Meaning Analysis, choose one:
[1] Confirm scope and continue → confirm_scope_for_analysis
[2] Revise scope → revise_scope
[3] Abandon proposal → abandon_proposal

You may reply with 1/2/3, c/r/a, or the canonical token.
```

Localize the visible labels to the user's language, but keep the canonical tokens unchanged.

### Persisted-State Honesty

- If the user says "continuing" but no `.goal-spec/changes/<change-name>/workflow-state.json` exists, MUST NOT claim a stage, gate pass, or recorded decision. Say "I do not see persisted workflow state…" or "Based on your message, I would route this to <stage>."
- When the user asks not to write files, MUST use prospective wording ("would record", "next artifact would be") — NEVER claim "recorded", "created", "gate passes" unless the artifact already exists and is validated.

### 0. Proposal Intake

Capture the raw proposal as `proposal-intake.json`. Preserve the original
proposal text. Do not add value judgment or OpenSpec source content.

### 1. Project Modeling Step

The **collector** (`evidence-collector`) builds a baseline project model
from source evidence. Output: `project-model.json`.

Must include: project purpose, stage boundary, core components, existing
capabilities, known boundaries, and source references. Must not contain
value judgment, recommended path, approval decision, or OpenSpec draft.


### 1.5 Problem & Scope Grilling

The **judge** (`value-judge`) operates in **grilling mode** to clarify
the user's problem, intended scope, and improvement intent before Proposal
Meaning Analysis. Output: `problem-scope-framing.json` and durable design-tree
state under `.goal-spec/changes/<change-name>/design-tree.json`.

Must not recommend no-build, evaluate value, classify as duplicate, or write
OpenSpec during this stage. The response MUST ask exactly one blocking question,
include why it matters, include the agent's recommended answer, include bounded
options when possible, and follow the Stage 1.5 Problem & Scope Grilling Output
Template. Any recommendation in this stage is limited to the answer for the
active blocking question; it is not a value judgment, no-build recommendation,
or scope-ranking decision.

#### Improvement intent rule

If the user expresses intent to improve, complete, refine, or extend,
`improvementIntent` MUST be true. Existing functionality may be cited as
baseline context or scope boundary evidence during framing, but MUST NOT be
used to cancel `improvementIntent` or justify a no-build recommendation before
scope closure and user confirmation.

#### Active-question recommendation boundary

The single active grill question MUST include `My recommended answer` (or a
localized equivalent). This recommendation is allowed only to help the user
answer the blocking question. It MUST NOT label any whole scope candidate as
"best", "highest value", "no-build path", or "smaller-scope recommendation",
and MUST NOT rank or score scope candidates before scope closure and user
confirmation.

### 1.6 Scope Closure Gate

A **deterministic script** verifies that `problem-scope-framing.json` is
structurally complete. It does NOT evaluate value or duplicates.
Output: `scope-closure-gate.json`.

- **not_closed** → routes to Problem Scope Clarification Request (1.6-1)
- **closed** → routes to Problem-Scope User Confirmation Gate (1.7)

### 1.6-1 Problem Scope Clarification Request

The **judge** produces a single bounded question when scope is not closed.
Output: `problem-scope-clarification-request.json`. The question maps to one
blocking field and one design-tree branch, provides bounded options when
possible, and provides the agent's recommended answer.

### 1.6-2 Problem Scope Clarification Response

A **deterministic step** captures the decision maker's answers.
Output: `problem-scope-clarification-response.json`. Workflow loops back to
Stage 1.5 for grilling/reframing.

### 1.7 Problem-Scope User Confirmation Gate

The user explicitly confirms the defined scope may proceed to Proposal Meaning
Analysis. Output: `problem-scope-user-gate.json`.

Allowed decisions: `confirm_scope_for_analysis` (proceed), `revise_scope`
(back to 1.5), `abandon_proposal` (terminal — NOT no-build).

Proposal Meaning Analysis SHALL NOT run until this gate passes with
`confirm_scope_for_analysis`.

**Harness-neutral choice/action contract.** The gate's decision options MAY be
expressed as a `ChoiceActionRequest` so capable harnesses can render the same
decision surface as selectors, buttons, or menus without hard-coding Pi
presentation. Harnesses that lack interactive UI SHALL render the equivalent
text fallback (numbered choices with aliases). The selected
`ChoiceActionSelectionResult` MUST be normalized to the canonical gate decision
before persistence. Existing canonical decisions, numeric aliases (`1`, `2`,
`3`), short aliases (`c`, `r`, `a`, `confirm`, `revise`, `abandon`), canonical
text inputs (`confirm_scope_for_analysis`, `revise_scope`, `abandon_proposal`),
and persisted artifact values MUST remain backward-compatible. See
[Choice-Action Contract Integration](#choice-action-contract-integration) below.

### 2. Proposal Meaning Analysis Step

The **judge** (`value-judge`) analyzes the proposal against the project model.
Output: `proposal-meaning-analysis.json`.

Must include: proposal summary, meaning-to-project classification, duplicate
points, conflict points, enhancement points, gap points, boundary fit, and
candidate paths. Must cite `project-model.json`.

### 3. Value & Logic Closure Assessment Step

The **judge** (`value-judge`) assesses whether the proposal is logically
closed. Output: `value-logic-closure-assessment.json`.

Must include: per-field closure assessment (project modeled, meaning clear,
duplicates handled, conflicts handled, enhancements clear, gaps known, success
signal defined, boundary fit, no-build considered, smaller scope considered,
approval options clear), value assessment, closure problems, and recommended
next step.

If blocking closure problems exist, `recommendedNext` must be
`logic_gap_completion`.

### 4. Logic Closure Gate

A **deterministic script** evaluates the closure assessment.
Output: `logic-closure-gate.json`.

- **not_closed** → routes to Logic Gap Completion (4-1)
- **closed** → routes to Change Value Assessment Report (4-2)

### 4-1. Logic Gap Completion Step

The **judge** produces a concise gap brief when logic is not closed.
Output: `logic-gap-brief.json`.

Every question must map to a blocking field and provide options or concrete
answer direction. No broad "please provide more detail" questions.

After the decision maker responds (`clarification-response.json`), the
workflow loops back to stage 3 for reassessment.

### 4-2. Change Value Assessment Report Step

The **judge** produces the final value assessment when logic is closed.
Output: `change-value-assessment-report.json`.

Must include: verdict, summary, project meaning, recommended path, and
alternatives. Must not be named or framed as an implementation value report.
This report prepares the OpenSpec Authoring Approval Gate.

### 5. OpenSpec Authoring Approval Gate

A **deterministic command** records an explicit approval decision from an
authorized approver. Output: `openspec-authoring-approval-gate.json`.

Allowed decisions:

| Decision | Effect |
|----------|--------|
| `continue_discussion` | Loop back to assessment or gap completion |
| `abandon_proposal` | Terminal — no OpenSpec package |
| `accept_no_build_recommendation` | Terminal — no package, preserve rationale |
| `approve_smaller_scope_openspec_authoring` | Writer proceeds within approvedScope |
| `approve_openspec_authoring` | Writer proceeds with full scope |

The gate must reference the current change value report digest. The gate
must not use `execute_implementation` or any implementation-implying language.
Approver types: `human`, `role`, `orchestrator`, `policy`.

**Harness-neutral choice/action contract.** The gate's decision options MAY be
expressed as a `ChoiceActionRequest` so capable harnesses can render the same
decision surface as selectors, buttons, or menus. Harnesses that lack
interactive UI SHALL render the equivalent text fallback (numbered choices with
aliases). The selected `ChoiceActionSelectionResult` MUST be normalized to the
canonical gate decision before persistence. Existing canonical decisions,
numeric aliases (`1`–`5`), short aliases (`c`, `a`, `s`, `n`, `x`, `continue`,
`approve`, `smaller`, `no_build`, `abandon`), canonical text inputs, and
persisted artifact values MUST remain backward-compatible. See
[Choice-Action Contract Integration](#choice-action-contract-integration) below.

### Choice-Action Contract Integration

Goal-spec gates MAY express their bounded decision options as harness-neutral
`ChoiceActionRequest` instances so capable harnesses can render the same
decision surface with their native affordances (selectors, buttons, menus)
while limited harnesses remain conformant through equivalent text fallback.

**Contract ownership.** The shared `ChoiceActionRequest` and
`ChoiceActionSelectionResult` schemas/types belong to `goal-contract` as
reusable cross-repo contracts. Harness rendering adapters belong to
`goal-runner`. Goal-spec owns which gate choices exist and how selected
canonical decisions are recorded in workflow artifacts.

**Gate-to-request mapping.** Each gate's canonical decisions map to a
`ChoiceActionRequest` as follows:

- `requestId`: stable id derived from the gate name (e.g.,
  `problem-scope-user-gate`, `openspec-authoring-approval-gate`).
- `title`: user-facing title localizable by the producer or presentation layer.
- `body`: optional explanatory text describing the decision to the user.
- `choices`: ordered array of choices, one per canonical decision.
  - `id`: stable choice id unique within the request.
  - `label`: visible label, localizable.
  - `canonicalValue`: the canonical decision token persisted in the gate
    artifact (e.g., `confirm_scope_for_analysis`, `approve_openspec_authoring`).
  - `aliases`: accepted numeric and short text aliases.
  - `description`: optional supporting text.
  - `disabled`, `disabledReason`: optional availability state.
- `fallbackPrompt`: text representation for non-interactive surfaces rendering
  the numbered choices and accepted aliases.
- `defaultChoiceId`: optional default for timeout or default behavior.
- `allowTextAliases`: whether aliases may be accepted as input (SHOULD be
  `true` for goal-spec gates).

**Stage 1.7 gate choices** map to a three-choice request:

| `id` | `canonicalValue` | Numeric alias | Short aliases |
|------|-----------------|---------------|---------------|
| `confirm` | `confirm_scope_for_analysis` | `1` | `c`, `confirm`, `continue`, `proceed` |
| `revise` | `revise_scope` | `2` | `r`, `revise`, `edit`, `change_scope` |
| `abandon` | `abandon_proposal` | `3` | `a`, `abandon`, `cancel`, `stop` |

**Stage 5 gate choices** map to a five-choice request:

| `id` | `canonicalValue` | Numeric alias | Short aliases |
|------|-----------------|---------------|---------------|
| `continue` | `continue_discussion` | `1` | `c`, `continue`, `discuss` |
| `approve` | `approve_openspec_authoring` | `2` | `a`, `approve`, `full` |
| `smaller` | `approve_smaller_scope_openspec_authoring` | `3` | `s`, `smaller`, `smaller_scope` |
| `no_build` | `accept_no_build_recommendation` | `4` | `n`, `no_build`, `no-build` |
| `abandon` | `abandon_proposal` | `5` | `x`, `abandon`, `cancel`, `stop` |

**Result normalization.** When a harness returns a
`ChoiceActionSelectionResult`, the consumer normalizes the selected
`canonicalValue` or `choiceId` to the canonical gate decision before
persistence:

- If `inputMode` is `text_alias`, the alias is mapped to the canonical decision
  using the same alias tables the deterministic gate commands use.
- If `inputMode` is `canonical_text`, the value is validated against the
  canonical decision set.
- If `inputMode` is `interactive`, the selected `choiceId` or `canonicalValue`
  maps directly.
- If `inputMode` is `defaulted`, the default choice's canonical value is used.
- `renderMode` records whether the harness used `interactive`,
  `text_fallback`, or `unsupported` presentation. This metadata is
  non-authoritative; the persisted canonical decision is the same regardless
  of render mode.

**Backward compatibility.** The choice/action contract is additive. Existing
numbered text prompts, short aliases, canonical text inputs, and persisted
artifact values remain valid. Harnesses without interactive UI continue to
render the fallback numbered text prompt. Canonical gate decisions stored in
`problem-scope-user-gate.json` and `openspec-authoring-approval-gate.json` are
unchanged.

**Helper commands.** The `goal-spec-workflow` script provides:

```bash
# Generate a ChoiceActionRequest from a gate's decision options
<skill-dir>/scripts/goal-spec-workflow choice-action-request <gate-name> --project-root <project-root>

# Normalize a ChoiceActionSelectionResult to a canonical decision
<skill-dir>/scripts/goal-spec-workflow choice-action-result --gate <gate-name> --result <result-json> --project-root <project-root>
```

### 6. Spec Kernel Step

The **writer** (`spec-writer`) distills the approved proposal into the spec
kernel. Output: `spec-kernel.json`.

Preserves: Why, Capabilities, Constraints, Non-goals, Success signal,
assumptions, and open questions.

### 7. Pre-Spec Gate

A **deterministic script** validates freshness and boundary compliance
before writing. Output: `pre-spec-gate.json`.

Checks: all upstream artifacts have matching digests, no runtime leakage,
no concrete model IDs.

### 8. OpenSpec Writing Step

The **writer** (`spec-writer`) authors the OpenSpec change package.
Output: `write-spec-status.json`.

`write-spec` requires all prerequisites: closed logic gate, fresh change
value report, approval gate with `approve_openspec_authoring` or
`approve_smaller_scope_openspec_authoring`, approval referencing current
report digest, valid spec-kernel, passing pre-spec gate, no runtime
leakage, no concrete model IDs.

### 9. Explainer Step

The **explainer** (`explainer-writer`) generates the decision-review
`change-explainer.html` from OpenSpec sources.

### 10. Package Review Step

The **reviewer** (`strict-reviewer`) reviews the complete OpenSpec package.
Output: `package-review.json`.

The reviewer must not silently rewrite sources unless explicitly invoked in
fix mode.

### 11. Handoff Ready Gate

A **deterministic script** performs final validation. Output: `handoff-ready.json`.

The change is ready for downstream Stage 2 planning via `goal-dag`.

### 12. Publish Closeout

After successful validation (Stage 11), the agent may run publish closeout to
commit and push the OpenSpec change package to its upstream git remote.
Publish closeout is **validation-first**: owned outputs are not staged until
source-manifest.json and required change-explainer.html pass validation.

**Deterministic script:**

```bash
<skill-dir>/scripts/openspec-publish-closeout <change-name> --project-root <project-root> [--remote <remote>] [--branch <branch>] [--commit-message "<msg>"] [--require-decision-review] [--non-published]
```

#### Owned-output-only staging

Only files under `openspec/changes/<change-name>/` are considered owned outputs.
Files under `.goal-spec/` (operational artifacts) are explicitly excluded from
staging even when they fall under the owned path prefix.

Required owned outputs (must pass validation before staging):

- `source-manifest.json` — validated via `openspec-validate-source-manifest`
- `change-explainer.html` — validated via `openspec-validate-explainer` (when required)

#### Blocked conditions (fail closed with diagnostics)

The script fails closed on any of these conditions and returns a JSON report
with the blocked diagnostics:

| Condition | Diagnostic code |
|-----------|----------------|
| Invalid or missing `source-manifest.json` | `invalid_source_manifest` |
| Invalid or missing `change-explainer.html` | `invalid_change_explainer` |
| Change directory not found | `change_directory_not_found` |
| Unrelated dirty files outside owned paths | `unrelated_dirty_files` |
| Ambiguous owned paths | `unrelated_dirty_files` |
| Missing upstream tracking branch | `missing_upstream` |
| Detached HEAD | `detached_head` |
| Remote not configured | `missing_remote` |
| Auth/network failure during push | `auth_failure` / `network_failure` |
| Push rejection (non-fast-forward) | `push_rejected_non_fast_forward` |
| Push rejection (other) | `push_rejected` |
| Remote verification fails | `remote_verification_failed` |
| Remote verification times out | `remote_verify_timeout` |
| Push times out | `push_timeout` |
| Commit creation fails | `commit_failed` |

#### Workflow

1. **Validation-first**: validate `source-manifest.json` and required
   `change-explainer.html`. Fail closed with diagnostics if either is invalid.
2. **Owned-path computation**: compute owned paths as
   `openspec/changes/<change-name>/**`, excluding `.goal-spec/` paths.
3. **Staging**: `git add` only owned paths.
4. **Block check**: scan `git status --porcelain` for unrelated dirty files.
   Block with diagnostics listing each unexpected modified/untracked path.
5. **Commit**: create a git commit with a generated or provided message.
6. **Non-force push**: `git push --no-force <remote> <branch>`.
7. **Remote verification**: `git ls-remote <remote> <branch>` and confirm the
   commit SHA is present in the remote ref output.
8. **Final cleanliness check**: re-run `git status --porcelain` to confirm the
   worktree is clean (excluding `.goal-spec/` paths).

#### Non-published mode

When `--non-published` is passed, the script skips all commit and push
operations. The result is labeled `non_published` and diagnostics indicate
that the closeout was explicitly non-published. This mode is useful for CI,
dry-run validation, or workspaces where publishing is handled externally.

#### Result modes

| Mode | Meaning |
|------|---------|
| `published` | Owned outputs validated, committed, pushed, and verified on remote |
| `no_changes` | Worktree was already clean; nothing to commit |
| `blocked` | A blocking condition was detected; inspect `diagnostics[]` |
| `non_published` | `--non-published` was set; commit/push skipped by explicit choice |

#### Exit codes

| Exit code | Meaning |
|-----------|--------|
| 0 | Mode is `published`, `no_changes`, or `non_published` |
| 1 | Mode is `blocked` or a runtime error occurred |

#### Stages boundary

Publish closeout is a deterministic, non-role operation. It does not:

- Generate Stage 2 execution-plan artifacts (`.dag.json`, `GoalDagSpec`, etc.).
- Modify `goal-dag`, `goal-runner`, or `goal-contract`.
- Execute implementation tasks or runtime behavior.
- Decide worktree allocation, model routing, subagent scheduling, or runtime
  validation.
- Modify `.goal-spec/` operational state.

### Artifact freshness

Every downstream artifact records SHA-256 digests of its load-bearing inputs
in `inputDigests`. JSON artifacts use canonical JSON hashing (sorted keys,
UTF-8, trailing newline ignored). Markdown files hash exact UTF-8 content.
Gates fail closed on stale digests.

### Role-run audit

Every semantic artifact is traceable to a role-run record
(`.goal-spec/changes/<change-name>/role-runs/<role>/<run-id>.json`) or a
deterministic command record. Role-run records include boundary assertions.

### Boundary validators

Stage 1 artifacts must not contain runtime-owned outputs (DAG sidecars,
trace sidecars, GoalDagSpec, goal invocation, workspace strategy, worktree
allocation, controller/subagent scenarios, completion gates, runtime node
definitions, subagent scheduling, runtime validation policy, runtime model
binding, concrete model selection). These terms are allowed only when
explicitly framed as prohibited "must not" text.

No concrete provider/model IDs. Hard-block known concrete prefixes.
Contextual-block provider/model patterns only near model/provider/binding
keys. Allowed Stage 1 references: `modelClass`, `evidence-collector`,
`value-judge`, `spec-writer`, `explainer-writer`, `strict-reviewer`.


Before Proposal Meaning Analysis, the agent MUST close and confirm the
problem/scope frame. Scope Closure Gate only proves the scope is well-formed.
Problem-Scope User Confirmation Gate proves the user accepts the scope for
analysis. If the user expresses intent to improve, complete, refine, or extend,
treat improvement intent as provisionally established. The agent MUST NOT
recommend no-build before scope closure and user confirmation when the user
has expressed improvement intent.

### Compatibility

The existing `proceed_with_assumptions` path is preserved as an escape hatch
alongside the new formal gates. Existing helper artifacts (`value-gate.json`,
`claim-graph.json`) may remain as compatibility projections generated from
canonical artifacts, but are never the primary value-decision source.

### 7. Build the Spec Kernel

Before writing OpenSpec files, distill the request into this kernel. Keep it in
working notes or include it explicitly in `design.md` when useful.

```text
Why: <force behind the change>
Capabilities: <what users/systems must be able to do; WHAT, not HOW>
Constraints: <non-negotiables that bend design decisions>
Non-goals: <explicit out-of-scope items>
Success signal: <observable proof the change worked>
Assumptions: <inferences not directly confirmed>
Open questions: <human decisions still needed>
```

Kernel rules:

- Every capability needs an intent and a testable success statement.
- Capabilities describe WHAT; implementation HOW belongs in design decisions.
- A constraint must rule something out or force a design choice. Otherwise it is
  decorative and should be removed.
- At least one non-goal is expected for non-trivial changes.
- Success signal must be concrete enough to test, demo, or inspect.
- Preserve stable terms. If a domain noun appears, define it once in design or
  the spec and reuse it consistently.
- **Preserve for downstream triage**: every assumption, non-goal, success criterion,
  and open question in the kernel is input to downstream DAG planning and runtime
  controller-answer context. If a downstream subagent asks a question whose answer
  is already recorded here, the controller SHOULD answer it without re-escalating
  to the user.

### 8. Pick the change name and capability name

Change name rules:

- kebab-case;
- specific enough to survive review;
- starts with a verb when possible: `add-`, `fix-`, `move-`, `harden-`,
  `standardize-`, `deprecate-`, `replace-`, `split-`.

Capability/spec name rules:

- kebab-case;
- use an existing capability if the change modifies current behavior;
- create a new capability only when no existing spec owns the behavior;
- for module-internal behavior, include the owning module prefix when required.

### 9. Scaffold the OpenSpec change

Use the bundled workflow helper first to materialize workspace-local `.goal-spec/changes/<change-name>/` state, record
and check the pre-spec gate, and only then write the starter OpenSpec package:

```bash
<skill-dir>/scripts/goal-spec-workflow init <change-name> --project-root <project-root> --capability <capability> --goal "<goal>"
<skill-dir>/scripts/goal-spec-workflow phase <change-name> --active value_challenge --status active --project-root <project-root>
<skill-dir>/scripts/goal-spec-workflow check <change-name> --project-root <project-root>
<skill-dir>/scripts/goal-spec-workflow gate <change-name> --pre-spec --project-root <project-root>
<skill-dir>/scripts/goal-spec-workflow write-spec <change-name> --project-root <project-root>
```

`gate --pre-spec` must report `pass`, or acknowledged
`proceed_with_assumptions`, before files are written. Before that point, inspect
`workflow-state.json`, `reflection-report.json`, `recovery-actions.json`, and
`claim-graph.json`; do not repeat blocked clarification/challenge prompts, and
ensure load-bearing claims are preserved or explicitly deferred. The helper creates the
standard package, including `.openspec.yaml`, `proposal.md`, `design.md`,
`tasks.md`, `source-manifest.json`, and a starter `specs/<capability>/spec.md`.
Rewrite the generated markdown/spec content with the source-grounded templates
below; the scaffold is only a starting point. The legacy `openspec-propose`
helper remains available for compatibility when the value gate has already been
recorded elsewhere.

Do not depend on any external scaffold tool being present. If a project
explicitly requires stricter local policy checks, run them only as additional
evidence after this bundled scaffold/write path.

### 10. Write `proposal.md`

`proposal.md` explains **why this change exists**, **what scope review is
approving**, and **why the value gate allowed this package to proceed**. Keep it
concise and decision-oriented.

Template:

```markdown
# <change-name>

## Why

<Problem, user need, risk, opportunity, mandate, or architectural pressure.
Explain the current failure mode and why it matters now.>

## Value Gate

- Outcome: `<proceed_to_spec | smaller_scope | proceed_with_assumptions>`
- No-build considered: <why no-build was rejected, or why the user overrode it>
- Smaller-scope considered: <selected minimal scope, or why broader scope is justified>
- Assumption posture: <confirmed, `[ASSUMPTION]`-tagged, or requires review>

## What Changes

- <Change 1>
- <Change 2>
- <Change 3>

## Impact

- Affected specs: `<capability>`
- Affected modules/repos: `<module-or-repo>`
- Affected APIs/events/data: `<surface or none>`
- Migration/deployment impact: `<impact or none>`
- User-visible impact: `<impact or none>`

## Non-Goals

- <Explicitly out-of-scope item>
- <Explicitly out-of-scope item>

## Pipeline Handoff Boundary

- Stage 1 output: governed OpenSpec sources only.
- Downstream consumer: `goal-dag` reads `source-manifest.json` plus the authoritative markdown/spec sources.
- No Goal DAG JSON or execution runtime plan is produced by this package.

## Success Signal

<Observable proof that the change achieved its goal.>

## Assumptions

- <[ASSUMPTION] item, or `None`>

## Open Questions

- [ ] <Question needing human decision, or `None`>
```

Rules:

- Do not hide risky scope in vague wording.
- Preserve the Value Challenge Gate outcome and any no-build/smaller-scope
  reasoning that affected scope.
- Include non-goals when there is any chance of scope creep.
- If the user request is ambiguous, ask before writing irreversible scope.
- **Preserve for downstream planning and runtime triage**: Non-Goals, Success Signal,
  Assumptions, and Open Questions MUST be explicit enough that a downstream DAG
  planner or runtime controller can answer subagent questions without re-escalating
  to the user. Mark each `[ASSUMPTION]` with enough context for a downstream agent
  to apply or challenge it. Every open question SHOULD identify who must resolve it
  and what decision is blocked until it is resolved.

### 11. Write `design.md`

`design.md` records the technical direction, trade-offs, and concern scan. It
should be sufficient for another agent/developer to implement without
re-litigating core decisions.

Template:

```markdown
# Design: <change-name>

## Context

<Current architecture/state and relevant constraints.>

## Spec Kernel

- Why: <why>
- Value gate outcome: <proceed_to_spec, smaller_scope, or proceed_with_assumptions>
- Capabilities:
  - <capability intent + success>
- Constraints:
  - <constraint>
- Non-goals:
  - <non-goal>
- Success signal: <signal>

## Goals

- <Goal 1>
- <Goal 2>

## Non-Goals

- <Non-goal 1>
- <Non-goal 2>

## Concern Scan

| Concern | Relevance | Design response |
| --- | --- | --- |
| <concern> | <why it matters> | <how the design handles it> |

## Decisions

### D0. Value path

**Choice**
<Proceed to spec, smaller-scope, or proceed_with_assumptions.>

**Rationale**
<Why this path is better than no-build or broader/narrower alternatives.>

**Alternatives considered**
- No-build: <why rejected/deferred or why user overrode it>
- Smaller/larger scope: <why selected/deferred>

### D1. <Decision title>

**Choice**
<Selected design.>

**Rationale**
<Why this choice fits the constraints.>

**Alternatives considered**
- <Alternative>: <why rejected or deferred>

## Detailed Design

### Data / Contract Changes

<APIs, events, schemas, DB tables, DTOs, config, or `None`.>

### Execution Flow

<Step-by-step flow, sequence, ownership, and failure handling.>

### Module Boundaries

<Which module owns what; what must not move across boundaries.>

### Migration / Rollout

<Compatibility, data migration, deployment order, rollback.>

## Risks

| Risk | Severity | Mitigation |
| --- | --- | --- |
| <risk> | <low/medium/high> | <mitigation> |

## Verification Plan

- <unit/schema validation>
- <integration/API validation>
- <manual/E2E validation>

## Execution Handoff Notes

This section records execution-planning evidence for downstream tools. It is not a DAG and does not assign runtime scheduling.

### Candidate Execution Slices

- <slice name>: <source-grounded reason this can be implemented independently>

### Ordering / Dependency Evidence

- <dependent work> depends on <upstream work> because <source-grounded reason>
- If no dependency is source-grounded, state that slices may be parallelized by downstream planning.

### Validation Signals

- <validator command or observable acceptance signal>
- If no deterministic validator exists, record acceptance criteria or open question.

### Open Questions Affecting Execution

- [ ] <question that must become a downstream blocker, decision node, or human-confirmation gate>

### Non-Goals for Execution

- <things downstream execution must not implement>

### Controller-Answer Context

This subsection captures context that a runtime controller may need to answer
subagent questions during execution without re-escalating to the user. Each entry
SHOULD describe a likely subagent question and the answer that the controller
can provide from spec context.

- <Likely subagent question> → <Answer grounded in proposal/design/spec sources>
- <Likely subagent question> → <Answer grounded in proposal/design/spec sources>

## Load-Bearing Preservation Notes

- <Source claim> → <where it landed>
- <Dropped wrapper-only/prose content> → <why not load-bearing>
```

Rules:

- Record decisions, not just implementation notes.
- Make ownership and boundaries explicit.
- Include rollback/migration when behavior, data, deployment, or public contract
  changes.
- Keep `Execution Handoff Notes` limited to evidence for downstream planning; do not include DAG runtime fields, node definitions, model routing, workspace strategy, completion gates, or JSON DAG output.
- **Populate Controller-Answer Context** with concrete question/answer pairs that
  downstream planning and runtime stages are likely to encounter. A well-populated
  section lets the controller answer subagent questions from spec context alone,
  reserving human escalation for genuinely new or unresolved decisions.
- **Preserve assumptions, non-goals, success criteria, and open questions** as
  first-class sections that downstream planning can consume without re-reading
  the full proposal. Every `[ASSUMPTION]` SHOULD include enough rationale for a
  downstream agent to evaluate whether the assumption still holds.

### 12. Write `tasks.md`

`tasks.md` is the implementation checklist. It should be actionable and
verifiable.

Template:

```markdown
# Tasks: <change-name>

## 1. Spec and Contract

- [ ] 1.1 Update `<capability>` spec delta.
- [ ] 1.2 Confirm affected APIs/events/data contracts.
- [ ] 1.3 Fill or confirm `design.md` Execution Handoff Notes with source-grounded slices, dependency evidence, validation signals, execution-affecting open questions, and execution non-goals.

## 2. Implementation

- [ ] 2.1 <Implementation step>
- [ ] 2.2 <Implementation step>

## 3. Verification

- [ ] 3.1 Run `<command>`.
- [ ] 3.2 Verify `<behavior>`.

## 4. Documentation / Closeout

- [ ] 4.1 Update relevant docs if user-visible behavior, API contracts,
  deployment, module responsibility, or cross-module interaction changed.
- [ ] 4.2 Refresh `source-manifest.json`.
- [ ] 4.3 Validate `change-explainer.html` if required.
- [ ] 4.4 Run archive preflight when implementation is complete.
- [ ] 4.5 Confirm Stage 1 produced only OpenSpec package sources and did not generate downstream execution-plan artifacts.

## Backlog / Follow-ups

- [ ] [BACKLOG] <deferred item with rationale, or omit section>
```

Rules:

- Every task should have a clear done condition.
- Do not include speculative tasks that are not required by the proposal/design.
- Use `[BACKLOG]` only for explicit non-blocking follow-ups.
- Unchecked non-backlog tasks are archive blockers.

### 13. Write `specs/<capability>/spec.md`

Spec deltas describe required behavior. Use RFC 2119 style (`SHALL`, `MUST`,
`MAY`, `SHOULD`) and scenario blocks.

Template:

```markdown
# <capability> Specification

## Purpose

<One paragraph describing what this capability owns.>

## Requirements

### Requirement: <requirement title>

<Normative behavior. Use SHALL/MUST for required behavior.>

#### Scenario: <scenario title>

- **GIVEN** <initial state>
- **WHEN** <action/event>
- **THEN** <expected result>
- **AND** <additional expected result>
```

Quality rules:

- Requirements are behavioral contracts, not implementation tasks.
- Each requirement should have at least one scenario.
- Scenarios should be testable.
- Avoid vague words like “support”, “handle”, or “improve” unless followed by
  observable outcomes.
- Do not duplicate an existing authoritative requirement; modify or extend the
  owning capability instead.
- Preserve terminology consistently. If the same concept appears under multiple
  names, choose one term and mention the alias only once if necessary.

### 14. Optional structured elicitation pass

For high-stakes or ambiguous sections, offer an elicitation menu after drafting a
section. Apply the chosen lens, show the improvement, and ask whether to apply
it before editing the document.

Suggested menu:

```text
Advanced Elicitation Options
Choose a number, r to reshuffle, or x to proceed:
1. Pre-mortem Analysis: imagine this change failed and identify preventions.
2. Red Team vs Blue Team: attack and defend the proposal/design.
3. Stakeholder Lens Rotation: inspect user/operator/security/dev/reviewer views.
4. First Principles: strip assumptions and rebuild the requirement.
5. Boundary & Edge Case Sweep: test nulls, max/min, auth, retries, concurrency.
r. Reshuffle with other methods.
x. Proceed.
```

Other useful methods:

- Assumption Audit: list assumptions, rate confidence/impact, shore up weak ones.
- Second-Order Thinking: trace downstream consequences.
- Inversion: ask what would guarantee failure.
- Comparative Analysis Matrix: score alternatives against explicit criteria.
- Architecture Decision Review: force choice, rationale, alternatives, trade-offs.
- Source Triangulation: require multiple source types for risky claims.

Rules:

- Do not apply elicitation changes silently.
- Keep the section source-grounded. If a method reveals a gap, record an open
  question instead of inventing an answer.
- Return to the main workflow after the user accepts, rejects, or skips.

### 15. Load-bearing preservation pass

Before validation, walk the source material claim by claim.

A claim is load-bearing if an implementer, reviewer, or verifier would make a
different decision without it.

For each load-bearing claim, ensure it landed in one of:

- `proposal.md` for why/scope/impact/non-goals;
- `design.md` for decisions, constraints, risks, migration, boundaries;
- `tasks.md` for implementation/verification work;
- `specs/**/spec.md` for normative behavior and scenarios;
- `Open Questions` when unresolved.

**Preservation targets for downstream planning and runtime triage:**

| Element | Required preservation location | Why downstream needs it |
|---------|-------------------------------|------------------------|
| Assumptions | `proposal.md#Assumptions`, `design.md#Decisions` or `design.md#Spec Kernel` | Downstream planning applies `[ASSUMPTION]`-tagged items as default behavior; runtime triage re-evaluates them when context changes. |
| Non-goals | `proposal.md#Non-Goals`, `design.md#Non-Goals`, `design.md#Execution Handoff Notes#Non-Goals for Execution` | DAG decomposition uses non-goals to bound node scope; runtime controller rejects out-of-scope subagent proposals. |
| Success criteria | `proposal.md#Success Signal`, `specs/**/spec.md` scenarios | Downstream verification nodes prove completion; runtime controller evaluates gate conditions. |
| Open questions | `proposal.md#Open Questions`, `design.md#Execution Handoff Notes#Open Questions Affecting Execution` | DAG planning inserts decision nodes or human-confirmation gates; runtime controller escalates unresolved questions. |
| Controller-answer context | `design.md#Execution Handoff Notes#Controller-Answer Context` | Runtime controller answers subagent questions without re-escalating to the user. |

Wrapper-only content, rhetoric, duplicate prose, and process metadata can be
dropped, but record important drops in `design.md` preservation notes when the
choice may be questioned later.

### 16. Refresh `source-manifest.json`

After writing markdown/spec files, refresh and validate the manifest with the
bundled helper:

```bash
<skill-dir>/scripts/openspec-build-source-manifest <change-name> --project-root <project-root>
<skill-dir>/scripts/openspec-validate-source-manifest <change-name> --project-root <project-root>
```

Never skip the manifest gate solely because the target workspace lacks
`openspec/scripts/*`. If a project explicitly requires stricter local policy
checks, run them only as additional evidence after the bundled manifest gate.

### 17. Generate `change-explainer.html`

For create and update modes, generate `change-explainer.html` directly from
OpenSpec sources. It is part of the standard OpenSpec change package and is not
a substitute for markdown/specs.

#### Non-negotiable decision-review gate

The output is a **decision-review explainer**, not a generic summary page. A
tool or wrapper returning `ok` is not sufficient proof of success. Success means
the final `change-explainer.html` passes the bundled strict validator (and any
stricter target-project validator when present) and visibly contains the
governed decision-review affordances defined by this skill and project policy.

Do **not** use these shortcuts as the generation path when decision-review HTML
is required:

- `openspec_workflow` / `openspec-workflow` `generate-explainer` with the
  template backend or unspecified backend;
- `openspec-workflow --backend template`;
- copied fixed/basic summary templates that only extract Why / What / Impact /
  Scope;
- any generated file missing
  `<meta name="openspec-explainer-mode" content="decision-review">`.

These paths may produce responsive HTML and may pass loose presentation checks,
but they are known to regress to basic companion pages. If such a file is
created accidentally, discard or rewrite it before declaring the task complete.

#### Direct generation workflow

For Beyourself-style explainers:

1. Refresh source manifest:

   ```bash
   <skill-dir>/scripts/openspec-build-source-manifest <change-name> --project-root <project-root>
   ```

   If the target project has a context-preparation helper, it may be used as an
   optional convenience, but the writer skill does not depend on it.

2. Use the governed explainer rules in this section as the prompt contract. If
   the target project also provides `openspec/prompts/opendesign-change-explainer.md`,
   read it in full and apply any stricter project-local requirements. The
   historical file name may mention Open Design; the prompt rules still apply to
   direct agent generation.

3. Read `openspec/changes/<change-name>/source-manifest.json`, then read every
   file listed in its `sources` array, typically:

   - `proposal.md` — why, what changes, impact, scope;
   - `design.md` — context, goals, decisions, risks, migration;
   - `tasks.md` — implementation plan, tasks, backlog;
   - `specs/*/spec.md` — spec deltas.

4. Write a single self-contained HTML file directly in this agent session:

   ```text
   openspec/changes/<change-name>/change-explainer.html
   ```

Required explainer qualities:

- self-contained HTML, no CDN/remote assets;
- `<html lang="zh-Hant">`;
- `<meta name="openspec-explainer-mode" content="decision-review">`;
- responsive layout, not a fixed 1920×1080 slide stage;
- Traditional Chinese reader-facing prose;
- primary navigation or equivalent segmented navigation;
- before/after comparison when source-grounded;
- source-grounded architecture/flow visual, preferably inline SVG;
- decision points with options, trade-offs, recommendation, risks, confidence;
- implementation slices with acceptance criteria, dependencies, and rollback
  notes when source-grounded;
- verification plan;
- risk register and high-risk filter;
- copyable implementation/review/verification agent prompts;
- copy controls for decision summary and task JSON export when source-grounded.

Before validation, inspect the HTML as prose. If it reads like a generic static
summary page, rewrite it; do not rely on validators alone.

Strict Beyourself validation:

```bash
<skill-dir>/scripts/openspec-validate-explainer <change-name> --project-root <project-root> --require-decision-review
```

Compatibility command for agents expecting the historical script name:

```bash
OPENSPEC_CHANGE_EXPLAINER_REQUIRE_DECISION_REVIEW=1 \
  <skill-dir>/scripts/check-change-explainer.sh <change-name> --project-root <project-root>
```

Expected strict output includes `status=ok` plus individual decision-review
checks for primary navigation, before/after, decision points, implementation
slices, verification plan, risk register, high-risk filter, copy controls, task
JSON export, implementation/review/verification agent prompts, SVG visual, and
responsive/mobile-tablet-desktop layout. If validation fails, fix the issues and
re-validate. Do not report completion until the strict validator passes.

If a project explicitly requires stricter local policy checks, run them only as
additional evidence after the bundled strict validator has passed; never replace
or skip the bundled validator.

Clean up generated context temp files if optional project-local helpers created
them:

```bash
rm -f temp/explainer-contexts/<change-name>-context.md
```

Guardrails:

- Do not introduce requirements, promises, risks, or migrations absent from
  source files.
- Do not create `planning-brief.json` or `visual-script.json` for this path.
- Do not ask Open Design discovery questions or emit `question-form` blocks.
- If a section cannot be grounded in source files, mark it not applicable or
  source-unspecified rather than inventing content.

### 18. Quality validation rubric

Run this rubric before handing off. Fix issues when the source supports a fix;
otherwise record assumptions/open questions.

#### Decision-readiness

- Are trade-offs surfaced honestly?
- Are decisions stated as decisions?
- Are open questions real, not hidden answers?
- Would a reviewer know what they are approving?

#### Done-ness clarity

- Does each requirement/scenario have observable outcomes?
- Are vague words replaced with thresholds, states, or examples?
- Do tasks have clear done conditions?
- Does the verification plan prove the success signal?

#### Scope honesty

- Are non-goals explicit?
- Are assumptions tagged and indexed in proposal/design?
- Are deferred items marked `[BACKLOG]` with rationale?
- Is scope creep blocked at module/API/data boundaries?

#### Downstream usability

- Can an implementer find ownership, files/modules, constraints, and validators?
- Can a tester derive tests from scenarios?
- Are terms consistent across proposal/design/tasks/spec?
- Are cross-references valid?

#### Boundary fit

- Does the spec shape fit the change type?
- Small fix: not over-formalized.
- API/event/data change: contract and compatibility are explicit.
- Regulatory/security change: traceability and risk are explicit.
- UX/user-visible change: user journey and acceptance behavior are explicit.

#### Runtime triage readiness

- Are assumptions explicit enough for a downstream agent to evaluate whether they still hold during execution?
- Are non-goals stated clearly enough for a runtime controller to reject out-of-scope subagent proposals?
- Are success criteria observable and evaluable by a downstream verification node?
- Are open questions identified with enough context for a DAG planner to insert a decision node or human-confirmation gate?
- Does `design.md` contain a Controller-Answer Context subsection with concrete question/answer pairs?
- Can a runtime controller answer likely subagent questions from spec context alone, without re-escalating to the user?
- If the spec were handed to a runtime controller today, would any subagent question be unanswerable with available context?

#### Preservation

- Every load-bearing source claim landed somewhere.
- Dropped content was non-load-bearing or recorded as intentionally omitted.
- Existing authoritative specs were extended, not contradicted.

### 19. Archive-readiness check

Only run archive preflight as readiness evidence. Do not archive unless the user
explicitly asks to close/archive.

Run the bundled archive preflight first:

```bash
<skill-dir>/scripts/openspec-archive-preflight <change-name> --project-root <project-root> --require-decision-review
```

If a project explicitly requires stricter local policy checks, run them only as
additional evidence after the bundled archive preflight; never replace or skip
the bundled preflight.

Treat as blockers unless policy says otherwise:

- unchecked tasks not marked `[BACKLOG]` / explicitly deferred;
- missing or stale `source-manifest.json`;
- missing or invalid required `change-explainer.html`;
- failing spec/explainer/layout validation;
- archive target already exists.

## Output contract

When done, report:

- change path;
- files created/updated;
- capability/spec name(s);
- Value Challenge Gate outcome, including no-build, smaller-scope, or `proceed_with_assumptions` rationale when applicable;
- validations run and results;
- skipped validations and why;
- assumptions and open questions;
- quality-rubric verdict;
- recommended next step: no-build action, revise scope, review, implement, archive readiness, or publish closeout.

After handoff readiness, the recommended next step may be **publish closeout**,
which commits and pushes the validated OpenSpec change package to its upstream
git remote. Use `scripts/openspec-publish-closeout` for the deterministic
publish step.

## Hard guardrails

- Do not convert the change into `/goal` or Goal DAG output from this skill.
- Do not produce `GoalDagSpec`, `.dag.json`, `.trace.json`, or `/goal` commands.
- Do not decide node decomposition, model routing, worktree allocation, subagent scheduling, or runtime validation.
- Do not put concrete provider/model ids in the authoring role profile or OpenSpec authoring guidance; use abstract `modelClass` roles only.
- When preparing a change for downstream execution planning, make implementation-relevant claims explicit in proposal/design/tasks/specs, not only in `change-explainer.html`.
- Do not invent requirements absent from user input or source evidence.
- Do not scaffold an OpenSpec package before the Value Challenge Gate passes,
  yields a smaller-scope target, or records an explicit `proceed_with_assumptions`
  path.
- Do not hide ambiguity; ask a clarifying question or put it in Open Questions.
- Do not create implementation tasks that contradict module boundaries.
- Do not create docs in retired paths such as `docs/superpowers/`.
- Do not treat `change-explainer.html` as authoritative over markdown/specs.
- Do not claim validation is unavailable only because the target repo lacks
  `openspec/scripts/*`; use the bundled writer helper.
- Do not archive without explicit user instruction.
- Do not publish closeout without validation passing first. Run publish closeout
  as a deterministic final step after handoff readiness is confirmed.
- Do not use archive history as current authority unless asked for historical
  rationale.

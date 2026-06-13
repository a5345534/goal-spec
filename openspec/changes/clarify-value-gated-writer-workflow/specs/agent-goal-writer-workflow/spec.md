# agent-goal-writer-workflow Specification

## Purpose

This capability defines the pre-OpenSpec authoring workflow for `agent-goal-writer`. It ensures the writer clarifies ambiguity, challenges whether a goal is worth doing, records assumptions and alternatives, and only writes OpenSpec artifacts after a pre-spec quality gate passes or the user explicitly chooses to proceed with acknowledged assumptions.

## Requirements

### Requirement: Critical collaborator stance

The writer SHALL act as a critical collaborator before writing OpenSpec artifacts. It SHALL distinguish the user's stated solution from the underlying problem, identify ambiguity, and challenge weak value claims constructively instead of automatically converting the request into a specification.

#### Scenario: Vague solution request is not accepted as scope

- **GIVEN** the user asks for a vague solution such as “make the writer produce better plans”
- **WHEN** the writer begins the OpenSpec authoring workflow
- **THEN** the writer SHALL ask or infer what problem the solution is meant to solve
- **AND** the writer SHALL identify at least one ambiguity, assumption, or missing success signal before writing OpenSpec files.

#### Scenario: Constructive disagreement

- **GIVEN** the writer believes the requested goal has weak value or unclear evidence
- **WHEN** the writer challenges the request
- **THEN** the writer SHALL state the concern, explain the reasoning, and offer a path to resolve the concern
- **AND** the writer SHALL avoid personal criticism or unbounded debate.

### Requirement: Value Challenge Gate

Before a goal is treated as ready for spec-kernel finalization, the writer SHALL run a Value Challenge Gate. The gate SHALL cover the problem, affected actor, value evidence, cost of doing nothing, no-build alternative, smaller-scope alternative, and conditions that would make the change not worth doing.

#### Scenario: No-build and smaller-scope alternatives are considered

- **GIVEN** the user proposes a feature, workflow, or architecture change
- **WHEN** the writer performs the value challenge
- **THEN** the writer SHALL record a no-build option
- **AND** the writer SHALL record a smaller-scope option
- **AND** the writer SHALL explain why the proposed change is preferred, deferred, or not recommended.

#### Scenario: Weak value blocks spec writing recommendation

- **GIVEN** the value challenge finds no affected actor, no cost of inaction, and no testable success signal
- **WHEN** the writer reports the next step
- **THEN** the writer SHALL recommend continued clarification, discovery, prototype, or no-build instead of immediately writing OpenSpec artifacts.

### Requirement: Stage-based workflow artifacts

The workflow SHALL maintain local stage artifacts for intake, value challenge, clarification, spec kernel, and pre-spec review before OpenSpec writing. These artifacts SHALL be stored under `openspec/changes/<change-name>/.writer-workflow/` for the active change.

#### Scenario: Workflow initialization creates artifacts

- **GIVEN** a change name and capability name
- **WHEN** `scripts/agent-goal-writer-workflow init <change-name> --capability <capability>` runs
- **THEN** the workflow SHALL create `.writer-workflow/workflow-state.json`
- **AND** it SHALL create templates for `intake.md`, `value-challenge.md`, `clarification.md`, `spec-kernel.json`, and `pre-spec-review.json`.

#### Scenario: Stage checks report missing evidence

- **GIVEN** a stage artifact is missing required fields
- **WHEN** `scripts/agent-goal-writer-workflow check <change-name> --stage <stage>` runs
- **THEN** the command SHALL report the missing fields
- **AND** it SHALL return a non-zero exit code.

### Requirement: Pre-spec quality gate

The workflow SHALL run a pre-spec quality gate before OpenSpec writing. The gate SHALL produce `pre-spec-review.json` with status `blocked`, `pass`, or `proceed_with_assumptions`. OpenSpec writing SHALL NOT start when the latest gate status is `blocked` or missing.

#### Scenario: Gate blocks untestable goals

- **GIVEN** the spec kernel lacks a testable success signal
- **WHEN** `scripts/agent-goal-writer-workflow gate <change-name> --pre-spec` runs
- **THEN** `pre-spec-review.json` SHALL report status `blocked`
- **AND** the blockers SHALL include the missing or untestable success signal.

#### Scenario: Gate passes sufficiently clear goals

- **GIVEN** the workflow artifacts define the problem, affected actor, value case, no-build alternative, smaller-scope alternative, testable success signal, non-goals, assumptions, and no unresolved blocker questions
- **WHEN** the pre-spec gate runs
- **THEN** `pre-spec-review.json` SHALL report status `pass`
- **AND** OpenSpec writing MAY proceed.

### Requirement: Proceed with assumptions path

The workflow MAY allow `proceed_with_assumptions` when unresolved value risks or open questions remain, but only when the user explicitly acknowledges those risks. The writer SHALL preserve acknowledged assumptions and value risks in the resulting `proposal.md` and `design.md`.

#### Scenario: User acknowledgement is required

- **GIVEN** blocker questions or value risks remain unresolved
- **AND** no explicit user acknowledgement is recorded
- **WHEN** the pre-spec gate runs
- **THEN** the gate SHALL report status `blocked`.

#### Scenario: Acknowledged risks allow constrained progress

- **GIVEN** unresolved value risks remain
- **AND** explicit user acknowledgement is recorded
- **WHEN** the pre-spec gate runs
- **THEN** the gate MAY report status `proceed_with_assumptions`
- **AND** OpenSpec writing MAY proceed only if the writer preserves those risks as assumptions, open questions, or risks in the OpenSpec files.

### Requirement: OpenSpec output preserves value debate

When OpenSpec writing proceeds after the pre-spec gate, the resulting OpenSpec package SHALL preserve the load-bearing outputs of the value challenge and spec kernel.

#### Scenario: Proposal preserves value rationale

- **GIVEN** the value challenge identified a cost of inaction, no-build alternative, smaller-scope alternative, and success signal
- **WHEN** the writer creates `proposal.md`
- **THEN** the proposal SHALL include the reason for change, success signal, non-goals, and assumptions
- **AND** it SHALL not present unresolved value risks as validated facts.

#### Scenario: Design preserves alternatives and risks

- **GIVEN** the value challenge identified trade-offs, rejected options, or acknowledged risks
- **WHEN** the writer creates `design.md`
- **THEN** the design SHALL include alternatives considered, relevant risks, and preservation notes for load-bearing claims.

### Requirement: Existing OpenSpec helpers remain authoritative after the gate

After the pre-spec gate allows writing, the workflow SHALL continue to use the bundled OpenSpec helpers for scaffolding, source-manifest refresh, explainer validation, and archive preflight according to the existing skill rules.

#### Scenario: Gate does not replace manifest and explainer validation

- **GIVEN** the pre-spec gate reports `pass`
- **WHEN** the writer creates or updates the OpenSpec package
- **THEN** the writer SHALL still refresh and validate `source-manifest.json`
- **AND** the writer SHALL generate and validate `change-explainer.html` when required by the skill or target project.

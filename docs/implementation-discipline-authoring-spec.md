# Implementation Discipline Authoring Spec

Status: draft  
Owner: `goal-spec`  
Applies to: Stage 1 OpenSpec authoring, ideation, approval gates, and source-manifest-backed change packages

## Purpose

Front-load the Karpathy-inspired implementation discipline during specification authoring so downstream DAG and runtime stages receive bounded, verifiable goals instead of vague implementation requests.

## Decisions

1. `goal-spec` should incorporate the discipline as authoring behavior, not as a dependency on `andrej-karpathy-skills`.
2. The authoring workflow should preserve a goal kernel: objective, non-goals, assumptions, success criteria, verification expectations, and scope boundaries.
3. Material ambiguity should be clarified with the user before producing an approved OpenSpec change.
4. Minor ambiguity may be resolved with a recommended default only if it is documented as an assumption and does not materially alter product behavior or compatibility.
5. The output should prepare downstream `goal-dag` to emit `implementation-discipline` quality profiles for implementation nodes.

## Authoring Rules

### 1. Think Before Coding

During discovery and proposal drafting, identify:

- conflicting interpretations of the user goal;
- product semantics not specified by the request;
- compatibility or migration decisions;
- external dependencies or permissions;
- validation gaps.

If a decision changes user-visible behavior, API compatibility, data safety, or implementation scope, ask before locking the spec.

### 2. Simplicity First

The proposed design should prefer the smallest change that delivers the stated value. Avoid speculative extensibility, unnecessary abstraction, and features that are not part of the approved goal.

### 3. Surgical Changes

The spec should define boundaries clearly enough for downstream implementation:

- in-scope capabilities;
- out-of-scope capabilities;
- expected touched modules or artifacts;
- forbidden areas when known;
- migration and cleanup limits.

### 4. Goal-Driven Verification

Each requirement should be paired with acceptance criteria or verification evidence. Bugfix-oriented specs should include reproduction criteria when possible. Implementation specs should identify tests, validators, demos, or review artifacts that prove completion.

## Clarification Policy

The authoring agent should classify uncertainty:

- **Must ask user**: product behavior, compatibility tradeoff, data/security decision, or irreversible migration.
- **Can decide with documented assumption**: naming, local organization, or implementation detail with a clearly safer default.
- **Can defer to runner/controller**: low-level execution detail that does not affect spec semantics.

## Downstream Handoff

When producing proposal/design/tasks/spec artifacts, include enough context for Stage 2 (DAG planning) and Stage 3 (runtime execution) to avoid direct user interruption:

- assumptions and rationale;
- accepted non-goals;
- success criteria and how they will be verified;
- validation expectations;
- open questions that remain intentionally unresolved;
- recommended default behavior for minor choices;
- **controller-answer context**: likely subagent questions and answers the runtime
  controller can provide from spec context alone, so Stage 3 can resolve execution
  questions without re-escalating to the user.

These elements MUST be recorded in the authoritative OpenSpec sources
(`proposal.md`, `design.md`, `tasks.md`, `specs/**/spec.md`) — not only in
workflow artifacts or the explainer — because downstream planning and runtime
stages consume authoritative sources only.

If the change is ready for DAG production, tasks should be decomposable into nodes with clear success criteria and path scope. Implementation tasks should be eligible for the `implementation-discipline` quality profile.

## Acceptance Criteria

- Approved OpenSpec changes expose material assumptions instead of hiding them.
- Non-goals are explicit enough to bound DAG node scope and reject out-of-scope execution proposals.
- Success criteria are observable and evaluable without re-interviewing the user.
- Tasks are verifiable and bounded enough for DAG decomposition.
- Downstream subagent questions can usually be answered by the controller from spec context.
- Human escalation during execution is reserved for genuinely new or unresolved decisions.
- `design.md` controller-answer context entries map likely subagent questions to grounded answers from proposal/design/spec sources.

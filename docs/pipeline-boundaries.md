# Pipeline Boundaries

This document defines the boundary for `goal-spec` in the goal execution pipeline and the handoff contract consumed by downstream execution-planning tools.

## Stage 1: goal-spec

`goal-spec` is Stage 1 of the pipeline:

```text
user goal -> OpenSpec change package
```

Stage 1 authoring uses the role profile in
`profiles/goal-spec-authoring-profile.json`. The profile maps collector, judge,
writer, explainer, and reviewer roles to abstract `modelClass` values only;
concrete provider/model ids are not Stage 1 source truth.

### Input

`goal-spec` accepts a user goal, feature request, architecture decision, bug direction, or comparable product/engineering intent.

### Output

`goal-spec` writes a governed OpenSpec change package under:

```text
openspec/changes/<change-name>/
```

The package contains:

- `.openspec.yaml`
- `proposal.md`
- `design.md`
- `tasks.md`
- `specs/**/spec.md`
- `source-manifest.json`
- optional `change-explainer.html`

### Authoritative sources

Downstream tools must treat these files as the authoritative OpenSpec sources:

- `proposal.md`
- `design.md`
- `tasks.md`
- `specs/**/spec.md`

`source-manifest.json` is the handoff index for locating and verifying the authoritative sources. It is not a replacement for reading those sources.

### Non-authoritative sources

The following files and directories are not authoritative OpenSpec sources:

- `change-explainer.html`
- `.goal-spec/` workflow state
- generated temporary context files
- scratch notes, extracted-claim reports, reflection reports, recovery reports, or other local operational artifacts

These artifacts may help reviewers understand context, but downstream planning must not treat them as source-of-truth requirements unless the claims also appear in the authoritative OpenSpec sources.

### Consumer

The downstream consumer is `goal-dag`.

`goal-dag` reads the OpenSpec change package through `source-manifest.json` and the listed authoritative sources, then performs Stage 2 planning.

## Must not

`goal-spec` must not:

- produce Goal DAG JSON;
- produce `GoalDagSpec`;
- produce `.dag.json`;
- call `/goal`;
- execute implementation tasks;
- decide runtime scheduling, model routing, worktree allocation, subagent execution, concrete model binding, or runtime validation;
- treat `change-explainer.html` as an authoritative source;
- treat `.goal-spec/` workflow state as an OpenSpec source of truth.

## Execution handoff evidence

When execution planning context is useful, `goal-spec` may include execution-planning evidence in the authoritative OpenSpec markdown, especially `design.md`. This evidence should describe:

- candidate execution slices and why they can be implemented independently;
- source-grounded ordering or dependency evidence;
- validation commands or observable acceptance signals;
- open questions that should become a downstream blocker, decision node, or human-confirmation gate;
- non-goals that downstream execution must not implement.

## Controller-answer context

In addition to execution-planning evidence, `goal-spec` SHOULD include
**controller-answer context** in `design.md#Execution Handoff Notes#Controller-Answer Context`.
Controller-answer context captures likely subagent questions and the answers the
runtime controller can provide from spec context alone. This lets the controller
resolve subagent questions during execution without re-escalating to the user.

Each entry SHOULD be a concrete question/answer pair:

```markdown
### Controller-Answer Context

- <Likely subagent question> → <Answer grounded in proposal/design/spec sources>
```

Controller-answer context is evidence for downstream runtime triage only. It must
not contain DAG runtime fields such as `after`, `modelScenario`, `workspaceStrategy`,
`completionGates`, node definitions, model routing, or JSON DAG output.

## Must-not summary

`goal-spec` must not:

- produce Goal DAG JSON;
- produce `GoalDagSpec`;
- produce `.dag.json`;
- call `/goal`;
- execute implementation tasks;
- decide runtime scheduling, model routing, worktree allocation, subagent execution, concrete model binding, or runtime validation;
- treat `change-explainer.html` as an authoritative source;
- treat `.goal-spec/` workflow state as an OpenSpec source of truth.

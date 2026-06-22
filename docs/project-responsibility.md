# Project Responsibility

Status: authoritative project-boundary document for this repository.

This document defines what this repository owns, what it must not own, and which artifact contracts it must honor. The repository should not need to know which concrete repository implements an upstream or downstream stage.

## Pipeline contract

```text
Stage 1: Specification Authoring   user intent -> governed specification package
Stage 2: Execution Planning        specification/development document -> runtime DAG JSON + optional planning trace
Stage 3: Runtime Execution         runtime DAG JSON or single objective -> durable execution state
```

This repository implements **Stage 1: Specification Authoring**.

It must know the Stage 1 output contract. It may describe downstream handoff evidence and the shared modelClass ownership boundary. It must not depend on or call into a concrete downstream planning or runtime repository.

## Owns

This repository owns:

- value challenge before writing a specification;
- discovery, assumptions, alternatives, non-goals, risks, and success signals;
- governed specification package authoring;
- Stage 1 authoring-role profile that maps collector/judge/writer/explainer/reviewer to abstract `modelClass` values;
- proposal/design/tasks/spec-delta structure;
- `source-manifest.json` creation and validation;
- optional human-readable explainer generation and validation when the target project requires it;
- Stage 1 operational workflow artifacts under local workflow state;
- execution handoff notes as source-grounded evidence for downstream planning.

## Does not own

This repository must not own or perform:

- runtime DAG spec creation;
- `.dag.json` or `.trace.json` generation;
- runtime command invocation;
- subagent planning or scheduling;
- runtime model routing or concrete model binding;
- worktree allocation;
- runtime validation policy;
- execution, implementation, merge, or cleanup behavior;
- goal completion, blocked-state decisions, or lifecycle ledger behavior.

## Inputs

Valid Stage 1 inputs include:

- user goal;
- feature request;
- bugfix direction;
- product idea;
- architecture decision;
- existing specification package for update/review/archive-preflight modes.

## Outputs

The primary output is a governed specification package:

```text
openspec/changes/<change-name>/
├── .openspec.yaml
├── proposal.md
├── design.md
├── tasks.md
├── source-manifest.json
├── change-explainer.html        # optional / non-authoritative
└── specs/<capability>/spec.md
```

Authoritative downstream sources are:

- `proposal.md`;
- `design.md`;
- `tasks.md`;
- `specs/**/spec.md`.

The handoff index is:

- `source-manifest.json`.

Non-authoritative downstream sources are:

- `change-explainer.html`;
- local workflow state;
- scratch notes;
- extracted-claim reports;
- reflection reports;
- recovery reports;
- temporary context files.

Non-authoritative files may help humans review context, but downstream planning must not treat them as source-of-truth requirements unless the same claim is preserved in an authoritative specification source.

## Handoff contract

When this repository hands work to any downstream execution-planning implementation, it must provide a complete governed specification package and a current `source-manifest.json`.

This repository may add execution handoff notes inside `design.md` to help downstream planning. Those notes may describe:

- candidate execution slices;
- source-grounded ordering or dependency evidence;
- validation commands or observable acceptance signals;
- execution-affecting open questions;
- execution non-goals.

Execution handoff notes must not contain runtime DAG fields or ready-to-execute DAG definitions. In particular, do not write:

- runtime dependency edges as DAG JSON;
- model scenario assignments;
- runtime model routing tables;
- workspace strategy;
- completion gates;
- runtime node definitions;
- `.dag.json` output;
- runtime execution commands.

## Drift prevention rules

A change to this repository is suspicious and requires boundary review if it:

- adds a dependency on a concrete execution-planning or runtime-execution implementation package;
- creates or validates `.dag.json` files;
- invokes runtime execution commands;
- creates worktrees or subagent sessions;
- executes validators as runtime controller policy;
- decides model routing;
- treats human-readable explainers as source of truth;
- treats local workflow state as governed specification source of truth;
- moves implementation execution into the Stage 1 workflow.

## Reviewer checklist

Before merging a change to this repository, verify:

- the output is still a governed specification package, not a runtime plan;
- authoritative sources remain `proposal.md`, `design.md`, `tasks.md`, and `specs/**/spec.md`;
- `source-manifest.json` remains the handoff index;
- no `.dag.json` or `.trace.json` generation was introduced;
- no runtime execution command invocation was introduced;
- human-readable explainers remain non-authoritative;
- execution handoff content is evidence for downstream planning, not a substitute for downstream planning.

# clarify-value-gated-writer-workflow

## Why

`agent-goal-writer` currently describes discovery, spec-kernel creation, OpenSpec writing, and validation, but the workflow can still be interpreted as a mostly cooperative document-generation path. That leaves two failure modes:

1. The writer may accept a vague or low-value user goal too early and convert it into polished OpenSpec artifacts before the target is worth doing.
2. The workflow has no explicit machine-checkable checkpoint that prevents spec writing when the problem, value case, success signal, non-goals, or unresolved assumptions are still weak.

This change clarifies that the writer is a critical collaborator, not an order-taker. It must help the user debate whether the goal is valuable, distinguish problem statements from preferred solutions, consider no-build and smaller-scope alternatives, and only then convert a sufficiently clear target into OpenSpec.

## What Changes

- Define a value-gated writer workflow with explicit stages: intake, value challenge, clarification, spec kernel, pre-spec quality gate, OpenSpec write, and validation.
- Introduce a bundled workflow-state helper script contract, tentatively `scripts/agent-goal-writer-workflow`, that creates stage artifacts, checks required fields, and blocks OpenSpec writing before the pre-spec gate is satisfied.
- Require the writer to challenge goals constructively instead of over-accommodating user requests.
- Add a pre-spec quality gate with three possible outcomes: `blocked`, `pass`, and `proceed_with_assumptions`.
- Require value debate outputs, assumptions, no-build/smaller-scope alternatives, and unresolved value risks to be preserved in the eventual OpenSpec package.

## Impact

- Affected specs: `agent-goal-writer-workflow`
- Affected modules/repos: `agent-goal-writer` skill instructions and bundled `scripts/` helpers
- Affected APIs/events/data: New local CLI/helper contract and local workflow artifacts under `.writer-workflow/`
- Migration/deployment impact: Existing OpenSpec helper scripts remain compatible; this adds a stricter pre-writing path rather than replacing scaffold/manifest/explainer helpers.
- User-visible impact: Users experience more constructive challenge before spec generation, especially for vague, high-cost, or low-evidence goals.

## Non-Goals

- Do not make the script decide product value by itself; the agent remains responsible for judgment and dialogue.
- Do not convert OpenSpec changes into `/goal` DAGs.
- Do not prevent explicitly acknowledged `proceed_with_assumptions` cases when the user chooses to continue after value risks are surfaced.
- Do not replace existing `openspec-propose`, source-manifest, explainer, or archive-preflight helpers.

## Success Signal

A vague request such as “make writer produce better plans” no longer proceeds directly to `proposal.md`/`design.md`/`tasks.md`/`spec.md`. The writer first records a value challenge, clarifies the problem and success signal, evaluates no-build and smaller-scope alternatives, and receives either a passing pre-spec gate or an explicit `proceed_with_assumptions` result before OpenSpec writing starts.

## Assumptions

- [ASSUMPTION] The first implementation can use template-backed Markdown/JSON artifacts and deterministic field checks; deeper semantic scoring remains the agent's responsibility.
- [ASSUMPTION] The helper script may be implemented in Python with only the standard library, consistent with the existing bundled helper scripts.

## Open Questions

- None

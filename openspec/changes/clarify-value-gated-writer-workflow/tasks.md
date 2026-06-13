# Tasks: clarify-value-gated-writer-workflow

## 1. Spec and Skill Contract

- [ ] 1.1 Update `SKILL.md` purpose/workflow text to define the writer as a critical collaborator rather than an order-taker.
- [ ] 1.2 Add the value-gated workflow stages before the current OpenSpec scaffold/write steps.
- [ ] 1.3 Document the Value Challenge Gate, constructive disagreement protocol, no-build option, smaller-scope option, and `proceed_with_assumptions` path.
- [ ] 1.4 Update the quality rubric so pre-spec quality is checked before `proposal.md`, `design.md`, `tasks.md`, and `specs/**/spec.md` are written.

## 2. Workflow Helper Script

- [ ] 2.1 Add `scripts/agent-goal-writer-workflow` using only the Python standard library or a thin wrapper around a standard-library Python module.
- [ ] 2.2 Implement `init <change-name> --capability <capability>` to create `.writer-workflow/` artifacts.
- [ ] 2.3 Implement `check <change-name> --stage <stage>` for intake, value-challenge, clarification, and spec-kernel artifact completeness.
- [ ] 2.4 Implement `gate <change-name> --pre-spec` to write `pre-spec-review.json` with `blocked`, `pass`, or `proceed_with_assumptions`.
- [ ] 2.5 Implement `write-spec <change-name>` so it fails unless the latest pre-spec gate status is `pass` or `proceed_with_assumptions`.
- [ ] 2.6 Return stable non-zero exit codes for blocked/missing-artifact/error states and machine-readable status output for automation.

## 3. Artifact Templates and Preservation

- [ ] 3.1 Add templates for `intake.md`, `value-challenge.md`, `clarification.md`, `spec-kernel.json`, `pre-spec-review.json`, and `workflow-state.json`.
- [ ] 3.2 Ensure templates distinguish problem, proposed solution, affected actor, value evidence, no-build alternative, smaller-scope alternative, non-goals, assumptions, and open questions.
- [ ] 3.3 Ensure `proceed_with_assumptions` requires explicit user acknowledgement and lists unresolved value risks.
- [ ] 3.4 Ensure OpenSpec writing guidance requires value challenge outputs to land in `proposal.md` and `design.md`.

## 4. Tests and Validation

- [ ] 4.1 Add script-level tests or fixture-driven checks for `init` artifact creation.
- [ ] 4.2 Add blocked-gate coverage for missing success signal, missing no-build alternative, missing non-goal, and unresolved blocker questions.
- [ ] 4.3 Add passing-gate coverage for a complete spec kernel.
- [ ] 4.4 Add `proceed_with_assumptions` coverage that fails without explicit acknowledgement and passes with acknowledgement.
- [ ] 4.5 Add `write-spec` coverage proving OpenSpec writing cannot start before the gate passes.
- [ ] 4.6 Run the repository's relevant validation/test command.

## 5. Documentation and Closeout

- [ ] 5.1 Update `README.md` to describe the new workflow helper and when to use it.
- [ ] 5.2 Refresh `source-manifest.json`.
- [ ] 5.3 Generate and validate `change-explainer.html` with the bundled writer helper if required.
- [ ] 5.4 Run archive preflight only after implementation tasks are complete and the user explicitly asks for archive readiness.

## Backlog / Follow-ups

- [ ] [BACKLOG] Add richer semantic scoring or LLM-assisted pre-spec critique after deterministic artifact gating is working.

# Authoring Agent Roles

`goal-spec` Stage 1 authoring uses role-separated model classes. The profile is
machine-readable at `profiles/goal-spec-authoring-profile.json`; this document is
the human-facing contract.

## Role mapping

| Authoring role | Abstract modelClass | Responsibility |
| --- | --- | --- |
| `collector` | `evidence-collector` | Gather and cite source truth without judging value or writing final prose. |
| `judge` | `value-judge` | Decide the value gate, challenge no-build/smaller-scope options, and require assumptions to be explicit. |
| `writer` | `spec-writer` | Write authoritative OpenSpec sources from the approved kernel and collected evidence. |
| `explainer` | `explainer-writer` | Generate non-authoritative `change-explainer.html` from authoritative sources. |
| `reviewer` | `strict-reviewer` | Review preservation, boundary fit, manifest/explainer freshness, and archive readiness. |

The profile intentionally contains only abstract `modelClass` values. Concrete
provider/model ids such as provider-specific model names are not authoring-role
truth and must not appear in the profile. Runtime resolution belongs to
`goal-runner` harness binding catalogs.

## Separation rules

- `collector` and `judge` MUST remain separate roles. Evidence collection does
  not decide whether the change is worth specifying.
- `judge` and `writer` MUST remain separate roles. The judge approves the value
  path and scope; the writer drafts within that approved kernel.
- `explainer` MUST treat `change-explainer.html` as a review companion only.
  Markdown/spec sources remain authoritative.
- `reviewer` performs the final gate after writer/explainer work and blocks on
  unpreserved claims, stale manifests, invalid explainers, unsupported evidence,
  or unchecked archive-blocking tasks.

## Source-truth rules

For an existing OpenSpec change, read `source-manifest.json` first, then read the
authoritative sources listed there:

- `proposal.md`
- `design.md`
- `tasks.md`
- `specs/**/spec.md`

`.goal-spec/` workflow state, scratch notes, and `change-explainer.html` are
non-authoritative. If a deterministic validator is not present in the sources,
record acceptance criteria rather than inventing shell commands.

## Handoff boundary

`goal-spec` produces governed OpenSpec source files only. It does not create Goal
DAG JSON, choose runtime scheduling, assign worktrees, or select concrete model
ids. Downstream `goal-dag` may assign `modelScenario`/`modelClass` values for
execution planning; downstream `goal-runner` resolves those classes through
harness bindings at runtime.

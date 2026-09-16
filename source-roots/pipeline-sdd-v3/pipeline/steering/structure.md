# Workspace structure

Resolve roots explicitly in the run's scope artifact:

- `FRAMEWORK_ROOT`: this candidate's `pipeline/`; reusable rules, templates and tools, not research answers.
- `RUN_ROOT`: a separate directory for the new capability run; specs, metadata, decisions, prompts and outputs.
- `CORPUS_ROOT`: the approved immutable input set, governed by a relative-path/hash manifest.
- evaluation/support directories: outside corpus and extraction context unless explicitly authorized by stage and purpose.

Paths in framework guidance are relative to FRAMEWORK_ROOT unless labelled otherwise. Historical `.sdd/`, case folders and sample paths in the preserved baseline are not active destinations.

One directory per artifact per capability: `RUN_ROOT/specs/[artifact-type]-[capability]/`. Use the eight types from `pipeline.md`. Each includes its authoritative artifact and `spec.json`; requirements/design/tasks/research are supporting documents, never permission to skip a stage. Stage 8 has a plan and separate results report.

`spec.json.phase` describes framework drafting progress, not human research approval. `ready_for_implementation` never authorizes code from an immature stage 1–5 document.

The legacy is read-only. No generated implementation, tests, known answers or unrelated APIs are copied into corpus as source evidence. Shared copybooks retain full relative paths; do not collapse different files with the same basename. Evidence identifiers are scoped to one run/capability; shared meanings require an explicit reconciliation decision.

A changed approved upstream artifact invalidates dependent approvals until review. Record the exact input/output versions and reviewers, preserving prior drafts rather than rewriting their history.

# Pipeline stage map

## Ordered artifacts

| Stage | Artifact | Question |
|---|---|---|
| 1 | Pipeline Scope Spec | Which inputs and boundaries govern this run? |
| 2 | Capability Selection Spec | Which business capability is selected, and why? |
| 3 | Legacy Evidence Spec | What does the source or controlled execution show? |
| 4 | Capability Semantics Spec | What do the observations mean as rules and obligations? |
| 5 | Canonical Data Boundary Spec | What data and state meanings cross the boundary? |
| 6 | API Contract Spec | What surface exposes those meanings and what stays external? |
| 7 | Adapter Behavior Spec | How is the contract realized over the unchanged legacy? |
| 8 | Semantic Validation Spec + separate Validation Report | What is assessed, observed, divergent or still unknown? |
| 9 | Implementation and Executable Qualification Spec | Which implementation is adopted or produced, and what fresh executable evidence qualifies it? |

Stages are cumulative. The validation plan must be approved before execution; the report is not a retroactive plan. Stage 9 is an implementation/execution qualification layer: it may adopt a preexisting SDD implementation with explicit provenance, but it must not pretend that adopted code was generated from scratch.

## Artifact anatomy and identities

Purpose → integrity discipline → upstream authorities/entry condition → stage-specific body → ambiguities → completeness gate and next entry condition. Stage 1 identifies external inputs instead of upstream specs.

Use `E-n`, `A-n`, `R-n`, `D-n`, `G-n`, `V-n`, `DIV-n` as defined in `settings/rules/traceability.md` (FRAMEWORK_ROOT-relative). IDs are stable and scoped per capability/run. One artifact directory per stage: `[artifact-type]-[capability]`. Stage 8 additionally produces its report.

Keep auxiliary requirements/design/tasks separate from the authoritative artifact. Framework phase status is not research approval. A document-first task at stages 1–5 does not authorize API or adapter implementation. Stage 9 requires preserved stage 1–8 hashes, a manifest with pinned upstream/contract/source/toolchain/resource/command inputs, fresh build artifacts produced inside the new run, HTTP/body-schema/audit evidence, and a package launch path; it is not a wrapper around an old PASS receipt or an old isolated preflight directory.

## Gates and revisions

A gate passes only after explicit human review of concrete conditions, not because a model wrote Approve. Record reviewer/authorization reference, exact artifact and upstream versions, decision and blocking gaps in research/review metadata alongside spec.json. Never generate a reviewer signature or authorization.

New v3 run metadata records `run_id`, `artifact_path` and `gate.review` version pins as documented in `tools/gates.md` (FRAMEWORK_ROOT-relative). `tools/check_gate.py` checks freshness across declared upstream dependencies without modifying records or granting approval. Legacy records are not silently upgraded.

Mechanical checks report their limited result separately. If upstream evidence changes, invalidate dependent approval until references and decisions are reviewed again. Blocking ambiguities cannot be removed by fluent prose. Fast-track requires explicit researcher authorization, not convenience.

## Cross-stage obligations

- Evidence before interpretation; semantic uncertainty must remain visible.
- Decisions live where made and inherit explicitly. Reference implementations are not semantic authorities.
- State is per resource: identity, initialization, lifetime, reset, isolation and failure effects travel from stage 5 through contract, adapter and scenario setup. External reset is allowed when declared; inventing a public reset is not.
- Batch sequence, end-of-input and intermediate persistence are investigated when relevant. Do not assume atomicity or safe retries.
- The wrapper invokes the legacy, never silently implements its business rules or compensates defects. Separate later backend construction requires its own scope/approval.
- Scenario type distinguishes contract conformance from legacy characterization. Transferability remains unproven until exercised with the alternative backend and declared support requirements.
- Artifact review cannot establish properties of a runtime it has not exercised. A source anchor passing does not establish that the claim is correct.

See `settings/rules/run-integrity.md` for input isolation, state propagation, failures and question-specific oracle authority.

## Pipeline versus research instruments

The framework is not the complete experiment. Comparative arms, T1–T4 campaigns, coverage, differential evaluation, statistical analysis and publication are separately scoped in each study. Stage 9 may qualify an executable API path for later use, but must not absorb independent T1–T4 evaluation. After Stage 9, use the complementary test-quality gate under `settings/templates/testing/` to qualify test-suite readiness and interpretation discipline: freeze before results, known coverage denominator, independent oracle authority, fixture reset evidence, T1–T4 integrity, mutation-as-checker-evidence only and traceability/gap separation. This is not Stage 10 and does not reopen or approve stages 1–9. No historical result or fixed port/path becomes a default for a new run.

Historical observations and instruments are preserved in `../../baseline/steering/pipeline.md`; they are not current results. The historical differential script's parameterization remains outside this revision. A public AWS run is not the future Phase 2 application, which will use other code and may use a later framework revision.

## Selection versus discovery

Record why a case was selected before reporting what was discovered. Post-hoc contrasts must remain post-hoc; do not rewrite the selection record to imply advance prediction. Shared scope and cross-capability types require explicit reconciliation decisions, not identifier reuse.

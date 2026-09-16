# Purpose and boundaries

Recover a selected COBOL business capability through an ordered, human-reviewed chain of evidence, semantics, canonical data, contract, adapter behavior and validation artifacts. The useful outcome is an executable, assessable integration boundary that can support incremental modernization.

The criterion for later modernization is functional continuity: the same business objective and explicitly agreed observable obligations. This does not require identical internals, formal equivalence or preservation of every legacy defect. Deliberate differences need decisions and validation; the wrapper never silently fixes the legacy.

## Eight artifacts

Pipeline Scope; Capability Selection; Legacy Evidence; Capability Semantics; Canonical Data Boundary; API Contract; Adapter Behavior; Semantic Validation Spec, followed by its separate report.

Evidence precedes interpretation; semantics precedes interface; interface precedes implementation. Early stages are document-first. A capability may span programs and persistent resources; neither a source file nor a batch job is automatically the unit of analysis.

## Non-goals

No optimal microservice decomposition, big-bang migration, source rewrite, automatic human approval, fidelity claim from coverage, or superiority claim without a suitable comparison. A required legacy processing sequence is not forbidden by the non-goal of designing new inter-service orchestration.

## Framework versus application

Each run states its corpus, capability, runtime, permitted inputs and study context. Historical account-balance assumptions and RQ results are not defaults for new runs. A public rehearsal is not the institutional or later Phase 2 case. Version changes between those applications are legitimate when recorded.

The transferable suite is an intended output, not a proven property until exercised with explicit state/setup dependencies on the relevant alternative backend. Backend construction and comparative research are separately scoped activities, not automatic ninth stages.

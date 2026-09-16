# Semantic Validation Report — {{CAPABILITY}}

<!-- Results of executing the semantic-validation-spec plan. Claims here must not exceed what the executed scenarios support. -->

## Summary
<!-- Scenario counts (planned / executed / passed / diverged / excluded), oracle mix, one-paragraph outcome. -->

## Scenario Results
<!-- Mirror the plan's groups. Every executed V-n gets a row; excluded scenarios are listed with reasons. -->

### Group A — {{OPERATION_OR_RULE}} [{{upstream §}}]

| ID | Type | Expected | Observed | Result | Notes |
|----|------|----------|----------|--------|-------|
| V-1 | conformance / characterization | | | pass / diverged / inconclusive | |

<!--
Carry the Type column from the plan. Characterization scenarios encode observed legacy
behavior: against a corrected reimplementation they are EXPECTED to diverge, and that
divergence is a change signal, not a regression. Consumers of this suite must be able to
tell the two apart without reading the scenario bodies.
-->

## Exploratory Campaign Results (if run)
<!--
Report budget, seed and counting unit alongside every count — a bare number is not a
result. Counts obtained under different budgets or different units are not comparable
across capabilities; if such totals are aggregated, say explicitly that the total measures
root-cause coverage and not severity or relative incidence.

State the harness provenance. If harness, contract and adapter share provenance, "zero
contract violations" is a schema self-consistency result — useful as conformance
regression, not an independent attestation of fidelity. Say which one is being claimed.
-->

| Campaign | Budget / seed | Counting unit | Findings | Attribution |
|----------|---------------|---------------|----------|-------------|
| | | | | adapter defect / legacy finding |

## Reachability, Effects and Measurement Limits
<!-- Report HTTP acceptance, actual COBOL reachability, state effects, oracle verdict and infrastructure/tool failures separately. Distinguish operation coverage, model coverage, COBOL-mapped lines and generated C arcs, with denominators/mapping and exclusions. Do not infer business correctness from coverage. Record incomplete observations as inconclusive. -->

## Known Divergences Registry

| ID | Scenario(s) | Expected vs observed | Probable origin | Disposition |
|-------|-------------|----------------------|-----------------|-------------|
| DIV-1 | V-{{n}} | | evidence gap / semantic drift / contract decision / adapter defect / legacy defect / legacy idiosyncrasy | fix in modernization layer / report legacy defect / accept (justify) / escalate upstream |

<!-- A divergence originating upstream must trigger upstream review; do not patch it only at the adapter. Legacy defects are reported, never fixed by the pipeline (rules/legacy-code-policy.md). -->

## Conformance Assessment
<!-- Scoped claim only: which operations/rules show behavioral consistency, for the validated scenarios, with which oracles, given which divergences. Test-level vocabulary only — no "verified", "semantic preservation", or "equivalence" (rules/validation-principles.md). -->

## Scope and Limitations
<!-- What was not validated and why; oracle limitations; ambiguity-driven exclusions; environmental constraints. -->

## Provenance Note
<!-- AI-assistance and execution provenance per rules/ai-assistance.md: tooling, approximate dates, degree of human intervention. -->

## Gate Outcome
- [ ] All planned scenarios executed or explicitly excluded with reasons
- [ ] Scenario types carried through, so characterization results are not read as conformance
- [ ] Divergence registry complete with dispositions
- [ ] Conformance claims scoped to evidence
- [ ] Expected-outcome provenance separated from tool origin
- [ ] Reachability, state effects, oracle verdicts and infrastructure failures distinguished
- [ ] Exploratory counts reported with budget, seed and counting unit; harness provenance stated
- [ ] Upstream-origin divergences escalated
- [ ] Human review outcome: Approve

**Pipeline run status after this report**: {{complete / returned to stage n / partially conformant with registered divergences}}

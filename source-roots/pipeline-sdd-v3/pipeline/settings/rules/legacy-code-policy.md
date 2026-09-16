# Legacy Code Policy

The legacy COBOL code is treated as read-only by the modernization pipeline. Modernization happens by adding a wrapper layer on top of the unmodified legacy core, never by editing it.

This policy is an advisor-aligned research position (June 2026): altering legacy code is risky, changes what is being studied, and is unnecessary for the research objective of exposing functionalities via API.

## Default stance

- No pipeline stage may require a modification to legacy source as a precondition.
- The adapter executes or wraps the legacy core (in the proof of concept, via a Node.js-to-COBOL binding); business rules inside the core are exercised through the calls, not reimplemented.
- If wrapping appears impossible without modification, that is a research finding to document and escalate — not a license to edit.

## Environment vs code

Preparing the execution environment is allowed and is not a code modification:

- populating data files/state so that rules can actually be exercised by tests
- build/runtime configuration needed to execute the legacy system
- test harness and binding infrastructure around the legacy core

The boundary: anything that changes the behavior-bearing source is a modification; anything that feeds or hosts it is environment.

## Defects found in the legacy code

The pipeline may expose defects in decades-old code (evidence work, derived tests, or fuzzing may reveal them, as the overdraft rule case showed in the proof of concept).

Handling policy:

1. **Always register the defect as a finding** — as evidence (`E-n`), divergence (`DIV-n`), or a dedicated defect note, with anchors.
2. **Never fix silently.** A silent fix destroys the evidential value of the finding and breaks traceability.
3. **Proof-of-concept (open-source) context**: proposing a fix upstream (e.g., a pull request, possibly LLM-assisted) is acceptable as an explicit, documented decision (`D-n`). The pipeline run itself still validates against the unmodified behavior it observed.
4. **Institutional context**: defects are only signaled to the system owners. Revision and correction are theirs to decide, typically manually — these are critical operations. No fix attempts, not even suggested patches applied locally.

Whether the pipeline should suggest corrections or only report defects is itself a registered research question for the institutional phase.

## A typology of legacy behavior, and the response each demands

Phase 1 applied the same pipeline to three systems and found three qualitatively different kinds of legacy behavior. The typology is useful because each kind demands a different modernization response, and confusing them produces either a false defect report or a silent overclaim.

| Kind | What the legacy does | What the contract should do | Modernization response |
|------|----------------------|-----------------------------|------------------------|
| **Rule present** | The business rule exists and is correctly applied in the intended domain, but the system carries anomalies at the *edges* — width overflow, precision loss — reachable only under extreme input | Promise the rule; bound the domain to what the legacy actually handles | Characterize and delimit the edges; the ceiling of a canonical type is evidence, not decoration |
| **Rule absent** | A rule the domain requires is missing, and its effect is masked by a representation choice (an unsigned field that renders a negative result as its absolute value) | Expose the *observed* value without correcting it, so the anomaly stays visible to the consumer | Supply the missing rule in the reimplementation — never in the legacy, never silently in the adapter |
| **Property not guaranteed** | The legacy is correct with respect to what it actually promises, but consumers may assume it promises more (a generator whose seed resolution permits collisions) | **Refuse the guarantee explicitly** in the contract text, not merely omit it | State the non-guarantee to the consumer; a collision is then an expected observation, not a defect |

Two disciplines follow.

**Refusing a guarantee is an act, not an omission.** A contract that stays silent about uniqueness and a contract that states uniqueness is not guaranteed behave identically at runtime and differently under review: only the second lets stage 8 classify an observed collision as a legacy finding rather than a contract violation. Where evidence shows a property the legacy does not deliver, record the refusal as a `D-n` at stage 5 and carry it into the contract description.

**Record the refusal before running the test.** In phase 1 the non-guarantee was written at stage 5 and the collision observed at stage 8, in that order — which makes the entry a dated, falsifiable prediction rather than a rationalization of whatever the test happened to show. The order is the evidential value; reversing it discards it.

## Interaction with other rules

- Divergences whose origin is a legacy defect follow this policy: the disposition is "report", not "fix in legacy" (see `validation-principles.md`).
- Adapter behavior must not compensate for a legacy defect silently; if it deliberately masks or surfaces the defect at the API level, that is a design decision (`D-n`) with rationale.
- Evidence and semantics artifacts must describe the legacy as it is, defects included — not as it should be.

## Desired outcome

The pipeline should be able to say, at any point: the legacy core is bit-identical to what was studied, every known defect is registered and traceable, and every deliberate response to a defect is a documented decision.

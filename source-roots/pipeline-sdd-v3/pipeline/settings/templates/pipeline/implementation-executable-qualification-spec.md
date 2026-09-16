# Implementation and Executable Qualification Spec — Stage 9

## 1. Purpose

Qualify an executable implementation path for the already approved SDD artifacts. This stage adopts or builds an implementation only after stages 1–8 are current and explicitly records whether the implementation was generated now or requalified from preexisting SDD work.

## 2. Integrity discipline

- Do not regenerate stages 1–8.
- Pin the exact stage 1–8 spec hashes before and after execution.
- Record implementation source paths, hashes, copied isolation roots and runtime commands.
- Preserve technical non-zero exits and COBOL/HTTP evidence; do not rewrite them as semantic success.
- Do not absorb independent evaluation campaigns T1–T4.

## 3. Upstream authority and entry condition

- Required approved upstream: Stage 8 Semantic Validation Spec and its complete recorded chain to stages 1–7.
- Required implementation inputs: API contract, adapter behavior, validation plan, implementation source/adoption provenance, fixture/source pins and execution environment.
- If upstream approval is missing or stale, stop with diagnostic evidence instead of inventing review metadata.

## 4. Implementation provenance

- Implementation mode: `source_adoption_and_build` / `generated_now` / `manual_adapter`.
- Required input manifest: upstream run and stage spec paths, implementation source files, contract files, toolchain, fixture/resource files and build/start/qualify/package commands, all with byte hashes where local files are used.
- Source authority: paths and hashes; generated code must be labelled generated only when new generation actually occurred.
- Adoption statement: what is reused as source, what is copied for isolation, what is built freshly, and which old build/run outputs are forbidden.
- Explicit non-claim: do not say preexisting code was generated from scratch in Stage 9.

## 5. Executable qualification

For each exposed track or endpoint:

| Track | Command/HTTP request | Status | Evidence path | Reached implementation | Reached legacy/runtime | Limits |
|---|---|---:|---|---|---|---|
| {{TRACK}} | {{COMMAND_OR_HTTP}} | {{STATUS}} | {{EVIDENCE}} | {{YES_NO}} | {{YES_NO}} | {{LIMITS}} |

## 6. Completeness gate

The stage is complete only if:

- stage 1–8 hashes are preserved;
- upstream gates are current at entry;
- the input manifest explicitly pins upstream specs, implementation sources, contract files, toolchain, resources and build/start/qualify/package commands;
- implementation provenance is explicit and does not depend on copied old binaries or previous run directories;
- code/HTTP was executed freshly in this run;
- evidence includes response bodies/statuses and runtime/audit paths;
- packaging includes a launch/reproduction path tied to the pinned inputs;
- limits distinguish technical qualification from semantic fidelity and campaign evaluation.

## 7. Required handoff: API ready for testing

Stage 9 must deliver the same operational boundary that the external operationalization step delivers for zero-shot and few-shot: an executable API ready to receive tests. It must not leave a further SDD-specific operationalization step to the test team.

Require evidence and a reproducible handoff for:
- build and server startup from declared inputs and toolchain;
- original routes and request/response schemas, with requests actually reaching the legacy program;
- documented errors and non-zero exits preserved rather than disguised as successes;
- local resource/fixture configuration used by the program, fresh state/reset and bounded lifecycle;
- launch commands, contract pins, dependency versions, audit locations and known operational limitations usable by the downstream test runner.

Record `api_ready_for_testing` separately from `campaign_ready` and human gate review. Missing test generation, T3 model-to-case mappings, official suite freezing, T1 provider authorization or T4 union scheduling do not block API operational readiness. Conversely, a remaining build, transport, resource-selection, isolation or response-conformance defect does block it. Do not set readiness from HTTP 200 alone or demand business-semantic perfection before evaluation.

T1–T4 generation, independent expectations, campaign configuration and execution belong to the downstream testing stage. This handoff does not approve those campaigns, publish results or create an independent oracle.

## 8. Downstream test-quality handoff

When `api_ready_for_testing=true`, instantiate the complementary Post-Stage-9 Test Quality and Coverage Gate (`settings/templates/testing/test-quality-gate.md` and `test-quality-gate-manifest.json`) before freezing or interpreting T1–T4 campaign evidence.

That gate must preserve Stage 9 as the technical API handoff and separately test whether the test suites are ready for review: independent business-oracle authority, wrong-output counterexamples, fixture/resource reset per case, known coverage denominator, explicit not-executed/inconclusive/N/A/gap accounting, T1–T4 integrity rules and mutation scope. It is not a new numbered pipeline stage, does not regenerate stages 1–8, does not edit this Stage 9 artifact, and does not grant campaign approval.

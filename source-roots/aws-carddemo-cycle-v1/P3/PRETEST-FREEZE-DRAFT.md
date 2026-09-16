# P3 Pre-Experimental Freeze Package — DRAFT

Status: **ready for human review, not approved**. This package prepares the P3 decision only. It does not execute T1/T2/T3/T4, run models, generate tests, read quarantine/baselines, or certify semantic outcomes.

## Scope and authorities

Cycle root: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1`.

Primary upstream sources pinned in `pretest-freeze-draft-manifest.json`:

- `PROTOCOLO.md` — P3 must freeze T1–T4 inputs/oracles, MBT model, budgets, seeds, resets, union, denominators and analysis before official cells.
- `P2a/plan-binding.md` — INV/RES/CAP/CONV/FAIL/STATE/RESP duties and pending deployment choices.
- `P2b/FINAL-PRETEST-READINESS.md` and `P2b/final-pretest-checklist.json` — technical smoke pass, official P3 still blocked.
- Approved Stage 7 r2 and Stage 8 records — documentary approvals only; no implementation/runtime/test approval.

## Existing decisions reused exactly

| Source | Reused decision |
|---|---|
| `PROTOCOLO.md` | Compare zero-shot, few-shot and SDD over posting, interest and reporting; T1 LLM scenarios, T2 OpenAPI fuzzing, T3 MBT, T4 union; every gate requires human decision. |
| `P2a/plan-binding.md` | Binding must preserve INV, RES, CAP, CONV, FAIL, STATE and RESP distinctions; actual resource/capture/reset/deployment choices remain pending. |
| `stage-7-r2-authorization.json` | Stage7 r2 documentary adapter behavior approved; no implementation, COBOL execution or experimental tests authorized. |
| `stage-8-authorization.json` | Stage8 documentary semantic validation approved; it closes the documentary SDD chain but does not certify runtime validity or executed tests. |
| `P2b/FINAL-PRETEST-READINESS.md` | P2b smoke is technical pretest evidence only; official T1/T2/T3/T4 remains blocked on P3 approval. |

## Draft requirements for P3 decision

### Fixtures

**Upstream basis:** `PROTOCOLO.md:13-18,43`, `P2a/plan-binding.md:38-49`, Stage7 RES/STATE.

**Draft proposal pending approval:** create an official fixture registry before campaigns. Each fixture record must include track, intended suite use, corpus/input provenance, exposure class, content hash, reset recipe, stateful-sequence label if any, and oracle-visibility label.

**Current blocker:** P2b fixture materialization is hardcoded smoke infrastructure in `P2b/p2b_binding.py`, not an official fixture-selection mechanism.

### Reset and isolation

**Upstream basis:** `PROTOCOLO.md:43`, Stage7 STATE, Stage8 V-12/V-33.

**Draft proposal pending approval:** default to a fresh run directory and fresh materialized resources per official case/seed. A T3/MBT stateful sequence may override this only with an explicit ordered-sequence declaration. Record before/after hashes for every bound persistent resource. Process restart is not reset evidence.

### Capture requirements

**Upstream basis:** Stage7 CAP, Stage8 V-3..V-11, P2b residual parsing evidence.

Every official invocation must retain raw bytes/digests, stdout/stderr, exit status, timing, record size/framing classification, source span evidence, and CAP/CONV/RESP disposition. Distinguish positive-empty from zero-length/missing/stale/truncated/malformed/failed capture. Known presentation records and unknown meaningful records must remain in audit evidence even when not public schema records.

### Conversion requirements

**Upstream basis:** Stage7 CONV, Stage8 V-11/V-14/V-20/V-26.

Every represented field requires source span/path/pin/line, declaration, framing/encoding/sign basis, observed padding/width, mapped value and loss/conflict disposition. Unsupported conversion is not guessed; it becomes technical failure, unrepresentable content, or upstream-review issue according to the frozen policy.

**P2b implementation note:** the local technical binding now treats report-only and mixed known+unknown meaningful `TRANREPT` captures as `500 technical_failure`; mixed cases preserve parsed public records under `availableContent` and retain unknown raw evidence in audit classifications. This closes the narrow local capture-conversion defect only. Official P3 still must freeze the campaign policy for mixed/unrepresentable content before experimental execution.

## Oracle-design independence matrix

This is an independence design, not expected answers.

| Oracle role | Independent from | Authority | Allowed use | Not allowed |
|---|---|---|---|---|
| O-schema | Generated tests and COBOL runtime outcomes | Stage6 r3 OpenAPI/schema | Structural response validation | Legacy fidelity claim |
| O-documentary-legacy | Candidate contracts and generated tests | Approved Stage3-r2/4/5/8 and source anchors | Obligation/counterexample design | Invent concrete output values |
| O-adapter-evidence | Public schema success | Stage7 r2 INV/RES/CAP/CONV/FAIL/STATE/RESP | Evidence admissibility and response justification | Business oracle by itself |
| O-MBT-reference-model | Contract under evaluation and observed results | Separately reviewed capability model | T3 transitions/guards/properties | Generated solely from evaluated OpenAPI |
| O-analysis-adjudication | Tool-generated verdicts | Frozen rubric and human/recorded review | Final failure/limit classification | Changing expectations after performance is seen |

## Proposed T1/T2/T3/T4 freeze items

All entries are **proposals pending human approval**.

| Item | Draft proposal | Upstream/proposal distinction |
|---|---|---|
| T1 | Freeze model/version, input visibility, categories, scenario budget, repetitions, retry and seed policy if supported. | Protocol requires these; exact numbers/tool choices are proposal/pending. |
| T2 | Freeze fuzzer/tool version, OpenAPI source, operation budget, checker set, seeds and sequence/reset policy. | Protocol requires compatibility and seeds; exact tool/budget pending. |
| T3 | Freeze independently reviewed MBT model with states/transitions/guards and non-expressible obligations recorded. | Protocol requires independent MBT oracle; model not yet approved. |
| T4 | Union T1/T2/T3 by case identity/provenance; dedupe by normalized operation+payload+state precondition+oracle target; preserve provenance and dependent-analysis label. | Protocol defines T4 as union, not independent replicate; dedupe key pending approval. |
| Order | Proposed outer order: strategy/contract, then condition T1/T2/T3/T4, then track order posting→interest→reporting unless a randomized blocked order is approved. | Protocol requires order/reset freeze; exact order pending. |
| Analysis | Separate contract validity, operationalization reach, observed content/effects, schema conformance, legacy obligation fidelity, infrastructure failure, coverage, cost/latency/interventions. Preserve invalid/non-operationalizable cases in denominator. | Protocol requires these separations; thresholds/rubric pending. |

## Missing executable infrastructure and concrete next tasks

1. **Fixture registry/selector drafted, not frozen.** `P3/fixture-registry.sample.json` and `P3/pretest_config.py` provide a non-executing local interface with hashes/provenance/exposure labels, but official fixture contents and real frozen hashes are still pending.
2. **Suite config schema drafted, not executable.** `P3/campaign-config.sample.json` validates as schema-only and rejects execution until human freeze; exact budgets/seeds/model/oracle/order remain pending.
3. **Independent MBT model missing.** Draft the model/oracle authority package for human review without deriving it solely from any evaluated contract.
4. **Mixed known+unknown report policy implemented locally, campaign policy still pending.** P2b now maps report-only and mixed unknown meaningful `TRANREPT` content to `500 technical_failure` with available public content preserved where present. P3 must still approve the official policy before campaigns.
5. **Lifecycle/reset proof missing.** Define official reset/read-back requirements before any campaign harness claims reset, isolation, durability or repetition safety.

## Human decisions required

- Fixture exposure policy and registry contents.
- Per-case fresh reset versus approved stateful sequences.
- T1 model/version, visibility, budget, repetitions, retries and seeds.
- T2 fuzzer/tool/version, budget, seeds, checkers and sequence policy.
- Independent T3 MBT model/oracle authority.
- T4 union order, duplicate policy, provenance and dependent-analysis treatment.
- Analysis denominator/failure taxonomy, including invalid/non-operationalizable contracts and infrastructure failures.
- Mixed known+unknown meaningful report-record policy.

## Status

This draft is ready for review only. No human approval is recorded here and no official cell is authorized by this package.

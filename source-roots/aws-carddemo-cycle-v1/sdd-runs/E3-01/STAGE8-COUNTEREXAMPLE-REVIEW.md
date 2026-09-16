# Stage 8 Counterexample Review — E3-01

Recommendation: **ACCEPT FOR HUMAN STAGE 8 REVIEW; no approval granted**.

## Inspected scope

- RUN root: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01`
- Materialized Stage8 artifact: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/specs/semantic-validation-carddemo/requirements.md`
- Completed attempt02 parsed output: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/prepared/semantic-validation-carddemo/execution/parsed.json`
- Completed attempt02 raw receipt: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/prepared/semantic-validation-carddemo/execution/response.sse`
- Attempt02 authorization: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/stage8-attempt02-generation-authorization.json`
- Preserved interrupted attempt: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/prepared/semantic-validation-carddemo/execution-attempt01-interrupted`
- Upstream inspected: Stage7 r2 `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/specs/adapter-behavior-carddemo-r2/requirements.md`, Stage6 r3 `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md`, Stage4 `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/specs/capability-semantics-carddemo/requirements.md`.

## Counterexample audit

No source-grounded blocker was found in the completed Stage8 attempt02 text. The artifact consistently treats scenarios as documentary obligations, not observed runtime results, and repeatedly states that actual invocation, resources, captures, failures, reset/isolation, durability, EOF behavior, and response delivery remain unestablished.

Concrete counterexample classes requested by the review are present and not blanket-passed:

- stale or misattributed capture: V-7/V-8;
- truncation and damaged framing: V-9;
- absent, zero-length, and unreadable capture distinct from positive empty: V-10;
- unavailable/503 distinct from observed empty/200: V-4/V-5/V-22/V-29;
- known technical failure/500 distinct from unknown failure: V-6/V-30/V-32;
- reset, isolation, durable state, repetition, restart, and live-resource claims rejected without evidence: V-12/V-23/V-24/V-28/V-33;
- internal reason 109 not promoted to public or preliminary-rejection evidence: V-16;
- EOF/final-account limitations retained rather than repaired: V-23/V-28;
- multiplicity/order and circular snapshot-oracle risks controlled: V-19/V-25/V-31;
- conversion and representability conflicts handled without fabricated values: V-11/V-20/V-26.

## Reverse completeness

Mechanical counts from the materialized Stage8 artifact:

- V IDs: `35` unique (`V-1`..`V-35`) across `219` mentions; `35` scenario table rows.
- R IDs: `20` unique (`R-1`..`R-20`) across `78` mentions.
- C IDs: `14` unique (`C-1`..`C-14`) across `130` mentions.
- Stage7 protocols are covered in Section 4.1 and scenario obligations: INV/RES/CAP/CONV/FAIL/STATE/RESP.

The Stage8 text includes explicit reverse-completeness tables for every Stage7 protocol, every Stage6 clause C-1..C-14, and every Stage4 rule/effect R-1..R-20. It also states that identifier mentions are insufficient by themselves (V-34), which avoids treating the mechanical count as the substantive oracle.

## Boundary and claim-strength audit

Pass for documentary materialization:

- expected conditions are phrased as acceptance criteria, rejection criteria, or deferred empirical obligations, not as observed outcomes;
- conformance, legacy characterization, insufficient evidence, unresolved empirical uncertainty, and upstream conflict are distinguished;
- input/resource control remains external or unresolved where Stage6/Stage7 left it unresolved;
- no E1/E2 or quarantine comparison was used as a gate condition;
- no false implementation, COBOL execution, runtime coverage, branch coverage, or empirical validation claim was introduced;
- public Stage6 boundaries and Stage7 protocols are not silently weakened: internal accountability records remain non-public, and missing evidence remains inconclusive rather than pass.

## Remaining human decision

The artifact may proceed to human Stage8 review. It must not be marked approved, ready for implementation, pipeline-complete, or experiment-complete until a human accepts Stage8.

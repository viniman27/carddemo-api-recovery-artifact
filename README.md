# CardDemo API recovery: execution evidence

Execution records of an empirical case study on recovering callable APIs from COBOL batch programs of the public [AWS CardDemo](https://github.com/aws-samples/aws-mainframe-modernization-carddemo) system (revision `59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e`) and evaluating them through generated test campaigns.

Programs in scope: `CBTRN02C` (transaction posting), `CBACT04C` (interest generation), `CBTRN03C` (transaction reporting), compiled with GnuCOBOL 3.2.0.

## Study at a glance

| Element | Contents |
|---|---|
| Recovered contracts | 7: three zero-shot (`E1-1..3`), three few-shot (`E2-1..3`) LLM outputs, one staged specification-driven trajectory (`E3-SDD-stage6r3`) |
| Official campaign | 12,700 applications: T1 LLM scenarios (88), T2 OpenAPI fuzzing (5,868), T3 model-based (394), T4 union replay (6,350) |
| Source-guided complement | 84 applications: 12 situations x 7 contracts |
| Retrospective analysis | Invocation-linked observations, source-derived checks, declared invariants, checker qualification probes |

## Layout, in execution order

All paths are under `source-roots/`.

| Step | Location | Role |
|---|---|---|
| 1. Case preparation | `aws-carddemo-preparation/` | Upstream COBOL/copybooks/JCL, slice selection, fixtures, local GnuCOBOL qualification |
| 2. Specification pipeline | `pipeline-sdd-v3/` | Eight-stage specification-driven pipeline: rules, templates, gates, tests |
| 3. Extraction inputs | `aws-carddemo-cycle-v1/P1/` | 19-file corpus allowlist, zero-/few-shot prompts, the three few-shot demonstrations (`few-shot-candidate/`), request parameters |
| 4. Extraction | `aws-carddemo-cycle-v1/collection-01/`, `sdd-runs/` | Model requests, raw responses (SSE), receipts; SDD stage specifications, approvals and revisions |
| 5. API operationalization | `aws-carddemo-cycle-v1/P2a/`, `P2b/`, `P2c-zero-shot/`, `P2c-few-shot/` | OpenAPI materialization, local HTTP facades over the unmodified COBOL programs, per-invocation audits |
| 6. Test generation and campaigns | `aws-carddemo-cycle-v1/P3/` (`t1-generation-*`, `t2-*`, `t3-*`, `campaign-*`, `official-campaign-large12k-run-v2/`) | T1–T4 suites, freezes, campaign runner, raw campaign evidence |
| 7. Complement | `aws-carddemo-cycle-v1/P3/complementary-validation-v2/`, `complementary-matrix-v2/` | Obligation catalogue with source line anchors, 12x7 matrix and its execution evidence |
| 8. Analysis | `aws-carddemo-cycle-v1/P3/official-analysis-v1/`, `retrospective-analysis-v2/`, `retrospective-analysis-v3/` | Coverage unions, case-level records, checkers, qualification probes; v3 revises the reporting relation (loop exit at the first out-of-range record) and adds a completeness clause to the reporting invariant |

### Key records

| Record | Path (under `source-roots/aws-carddemo-cycle-v1/`) |
|---|---|
| Case-level official records (12,700) | `P3/retrospective-analysis-v2/run-01/official-cases.jsonl` |
| Case-level complementary records (84) | `P3/retrospective-analysis-v2/run-01/complementary-cases.jsonl` |
| Checkers | `P3/retrospective-analysis-v2/evidence.py`, `collector.py`, `analysis.py` |
| Reporting re-derivation v3 | `P3/retrospective-analysis-v3/reporting_v3.py`, `reporting-verdicts-v3.jsonl`, `SUMMARY-v3.json` |
| Checker qualification (35 probes) | `P3/retrospective-analysis-v2/oracle-qualification.json`, `oracle-sensitivity.csv` |
| Signed DISPLAY trials (13) | `P3/retrospective-analysis-v2/signed-probe/` |
| Few-shot facade request rejections | `P3/official-campaign-large12k-run-v2/p2b-preparation/isolated-cycle/aws-carddemo-cycle-v1/P2c-few-shot/outputs/http-rejections.jsonl` |
| Line-coverage unions (gcov over GnuCOBOL-generated C) | `P3/official-analysis-v1/coverage_union_by_arm_condition_track.csv`, `P3/complementary-matrix-coverage-v1/evidence/current/coverage-summary.csv` |
| Obligation catalogue | `P3/complementary-validation-v2/scenario-catalog.json` |

## Recompute the reported counts

Requires Python 3.10+ and no third-party packages:

    python3 analysis/verify_reported_counts.py

The script reads only preserved records. It does not invoke any business API, COBOL program or LLM. It checks:

- HTTP status and admission by condition and strategy;
- causes of non-admitted HTTP 500 responses and few-shot HTTP 400 rejections, including `multipleOf` false rejections re-checked with exact decimal arithmetic;
- presence of the `multipleOf` idiom in demonstrations and contracts;
- documentation of the end-of-file behaviors in all recovered contracts;
- partition reach and divergence-condition reach;
- the assertion matrix (with the v3 reporting verdicts), the a priori obligation denominator, qualification probes, coverage unions and COBOL line anchors;
- the raw bytes of the worked reporting example (`analysis/worked-example.json`).

It writes `analysis/REPORTED-COUNTS.json`.

The portable checker unit tests and the v3 reporting re-derivation run with:

    cd source-roots/aws-carddemo-cycle-v1/P3/retrospective-analysis-v2
    python3 -m unittest test_evidence test_qualify test_gaps test_models
    cd ../retrospective-analysis-v3 && python3 reporting_v3.py

## Reproduction boundary

This is a complete evidence snapshot, not a one-command re-execution of the campaigns. Re-running the extraction requires access to the recorded model endpoint. Re-running the campaigns requires GnuCOBOL 3.2 and the Python environments described in each package; virtual environments, caches and compiled binaries are omitted. Historical scripts, receipts and hash manifests are kept as evidence of what was run. Absolute machine paths were replaced by placeholders such as `<REDACTED_LOCAL_PATH>`, `<WORKSPACE>` and `<UPSTREAM_CHECKOUT>`, so some historical commands are not portable as written.

## Anonymization

See `ANONYMIZATION.md`. Identity-related text was replaced in 2,852 text files and 681 fixture/record files. Every modified file is listed with its before/after SHA-256 in `ANONYMIZATION-LEDGER.jsonl`. As a result, hash pins recorded inside historical receipts and ledgers refer to the pre-anonymization bytes of those files.

## Third-party material

CardDemo sources, copybooks and JCL are © Amazon.com, Inc. or its affiliates and remain under their original Apache-2.0 license. The license files are kept in their source locations. No relicensing of third-party material is implied.

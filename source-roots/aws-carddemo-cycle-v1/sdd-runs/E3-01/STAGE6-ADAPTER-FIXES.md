# Stage 6 adapter fixes — F1-F5

Scope: code/test changes only under `casos/aws-carddemo-cycle-v1/sdd-command-adapter`, plus this report. No real Stage 6 init, prepare, execute, API contract generation, model call, gate approval, corpus/quarantine edit, framework edit, or approved Stage 5 metadata migration was performed.

## Changes implemented

- F1: added structured Stage 5 authorization validation in `stage6_adapter.py`:
  - `decision: reject` fails even when `approved: true` is also present;
  - approval accepts only `decision: approve` or `approved: true`;
  - optional `stage` and `run_id` are checked when present;
  - Stage 5 artifact path/hash is required and checked against `specs/canonical-data-boundary-carddemo/requirements.md`;
  - `review_reference` and `findings_reference` are mandatory and bound exactly to the real root-relative authorities `STAGE5-COUNTEREXAMPLE-REVIEW.md` and `stage5-counterexample-findings.json`;
  - prose scope is not treated as consent authentication and Stage7 prohibition text is not itself rejected.
- F2: changed Stage 6 prompt rules to allow traceable `D-n` representation choices for method/route/schema/status/error categories while still forbidding unsupported business/semantic guarantees.
- F3: production Stage 6 now enforces exact real corpus retention with `EXPECTED_REAL_CORPUS_FILE_COUNT = 19`; synthetic tests use a test-only `mock.patch` of that constant, with no user-accessible bypass or approval-path marker.
- F4: updated Stage 6 synthetic fixture to use root-relative Stage 5 findings path and added regression coverage for reference mismatches.
- F5: added structural tests for exact source `content`, `numbered_lines`, derived hash preservation, the full 13-doc framework context, authorization contradictions, corpus reduction refusal, and preservation of original input pins.

Synthetic fixtures added under `tests/fixtures/framework/...` are explicitly labeled synthetic and exist only to make the Stage 6 framework-context invariant testable.

## TDD evidence

RED command:

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-command-adapter"
python3 -m unittest tests.test_stage6_adapter -v
```

Observed before production fixes: failed as expected, including missing `EXPECTED_REAL_CORPUS_FILE_COUNT` and new Stage 6 invariant failures. Full log: `<REDACTED_LOCAL_PATH>/.run-cache/cache/terminal-output/out-1789251911-94583-52d0.log`.

GREEN/regression commands:

```bash
python3 -m unittest tests.test_stage6_adapter -v
python3 -m unittest discover -s tests -v
python3 -m py_compile adapter.py stage3_adapter.py stage4_adapter.py stage5_adapter.py stage6_adapter.py tests/test_stage6_adapter.py
```

Results:

- Stage 6 focused suite: exit 0; full log `<REDACTED_LOCAL_PATH>/.run-cache/cache/terminal-output/out-1789252013-94583-3750.log`.
- Full regression: `Ran 45 tests in 22.879s`, `OK`; full log `<REDACTED_LOCAL_PATH>/.run-cache/cache/terminal-output/out-1789252036-94583-9190.log`.
- `py_compile`: exit 0.
- Static added-line scan for obvious secrets/shell/eval/pickle/SQL patterns: no matches.

## Read-only real Stage 6 input-pins validation

Command executed read-only by importing `stage6_adapter.stage6_current_input_pins(...)` against the real run roots. No files were written. Additional check confirmed real `specs/api-contract-carddemo` and `prepared/api-contract-carddemo` are absent.

Observed real counts/integrity:

- `source_bodies_count`: 19
- `expected_real_corpus_file_count`: 19
- `actual_corpus_file_count`: 19
- upstream specs: 5
- upstream artifacts: 5
- authorizations: 5
- review attachments: 3
- framework docs: 13
- gate check: `status=current`, `ok=true`
- Stage 5 authorization decision: `approve`
- Stage 5 artifact pin: `specs/canonical-data-boundary-carddemo/requirements.md` / `208d04fe6f9cae665dfa4cb514de5d4ad9eaf0ebc169dfae0fd8a6ba209e66f3`
- Stage 5 review reference: `STAGE5-COUNTEREXAMPLE-REVIEW.md` / `0dadcd665b1e4cb71765003c22655f7b04a3430bf92077f9d63d33053aa2fdfe`
- Stage 5 findings reference: `stage5-counterexample-findings.json` / `caa6418e2ebec9e52a795e1bafd9ca304a21d55a0c28e73e86b06162c33ec84e`
- First source byte pin sampled: `LICENSE` / `09e8a9bcec8067104652c168685ab0931e7868f9c8284b66f5ae6edae5f1130b`; derived numbered hash recomputed OK.

## Residual limits

- This does not approve Stage 6, approve Stage 7, generate an API contract, or authorize execution/model calls.
- The production corpus count is intentionally fixed to this AWS CardDemo Stage 6 adapter (`19`); synthetic reduced fixtures remain valid only through test-side mocking.
- The adapter validates structured authorization fields and exact pins; it does not infer consent from prose scope.

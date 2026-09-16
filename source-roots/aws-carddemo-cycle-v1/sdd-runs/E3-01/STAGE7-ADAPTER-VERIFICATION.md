# Stage7 Adapter Verification

Date: 2026-09-13
Scope: review/fix of `sdd-command-adapter/stage7_adapter.py` before any real Stage7 generation.

## Outcome

Stage7 adapter is ready for offline initialization/request preparation review. No real Stage7 init, request preparation, execution, network/model call, COBOL execution, Stage8 generation, or implementation was performed against the real run.

## Changes made

Modified adapter subtree only:

- `sdd-command-adapter/stage7_adapter.py`
  - `collect_stage7_framework_context()` now fails closed for all 13 mandatory framework documents instead of silently skipping missing files.
  - `validate_stage6_r3_authorization()` no longer treats prose token presence/absence as authorization semantics. Authorization validation is structured: reject-wins approval decision, stage, run id, exact artifact pin, exact review pin, exact findings pin, plus the separately pinned authorization file hash checked by `stage7_current_input_pins()`.
- `sdd-command-adapter/tests/test_stage7_adapter.py`
  - Expanded denial coverage so any explicit non-`approve` decision (including `reject` or `deny`) blocks even if `approved: true` is present.
  - Added regression proving Stage7 authorization is not inferred from prose tokens.
  - Added regression proving a missing mandatory framework rule stops Stage7.

Created this authorized report:

- `sdd-runs/E3-01/STAGE7-ADAPTER-VERIFICATION.md`

## Real read-only compatibility check

Command run from `sdd-command-adapter`:

```bash
python3 - <<'PY'
from pathlib import Path
import stage7_adapter
run=Path('<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01')
framework=Path('<REDACTED_LOCAL_PATH>/pipeline-sdd-v3/pipeline')
corpus=Path('<REDACTED_LOCAL_PATH>/casos/aws-carddemo-preparation/research-corpus')
package=Path('<REDACTED_LOCAL_PATH>/casos/aws-carddemo-preparation/evidence/research-package.json')
upstream,pins,source_bodies,framework_docs=stage7_adapter.stage7_current_input_pins(run, framework, corpus, package)
print('stage7_current_input_pins real read-only ok')
print('stage', pins['stage'])
print('corpus', len(source_bodies), pins['actual_corpus_file_count'], pins['expected_real_corpus_file_count'])
print('framework', len(framework_docs), len(pins['framework_context']))
print('stage6_r3_feature', upstream['stage6_r3_spec_json']['feature_name'])
print('stage6_r3_artifact_sha', pins['upstream_artifacts'][-1]['sha256'])
print('stage6_r3_auth_sha', pins['authorizations'][-1]['sha256'])
print('review_sha', pins['stage6_r3_review_reference']['sha256'])
print('findings_sha', pins['stage6_r3_findings_reference']['sha256'])
print('r2_revision_history_count', len(pins['stage6_r3_revision_history']))
print('upstream_specs_count', len(pins['upstream_specs']))
print('authorizations_count', len(pins['authorizations']))
PY
```

Output:

```text
stage7_current_input_pins real read-only ok
stage 7
corpus 19 19 19
framework 13 13
stage6_r3_feature api-contract-carddemo-r3
stage6_r3_artifact_sha 6cba102f8335843b46e75a77b1a71d4e56373a95d5ac63cf645491556c443b27
stage6_r3_auth_sha 0c5228634cb0f3b3c779fafe2e7e9ae5109aebeb24b116268e73a9a00dd8213e
review_sha a8e41764b56018f530a2df96d75bff483086e84b2462fca156175b0f91be7159
findings_sha 69a59af451a700f8de1d4711f64149ce5bd295ced79bcee1747caf2aefee0193
r2_revision_history_count 8
upstream_specs_count 6
authorizations_count 6
```

This proves compatibility with the actual approved Stage6 r3 metadata and pins without mutating the real run.

## Verification commands

Focused RED/GREEN regression command after adding the tests:

```bash
python3 -m unittest tests.test_stage7_adapter.Stage7AdapterTests.test_stage7_authorization_decision_hash_stage_mismatches_and_approved_r2_are_blocked tests.test_stage7_adapter.Stage7AdapterTests.test_stage7_authorization_is_structured_not_prose_token_based tests.test_stage7_adapter.Stage7AdapterTests.test_stage7_missing_mandatory_framework_doc_fails_closed -v
```

Result:

```text
Ran 3 tests in 5.525s
OK
```

Full suite:

```bash
python3 -m unittest discover -s tests -v
```

Result:

```text
Ran 95 tests in 93.232s
OK
```

Caveat: the unittest discovery total includes inherited test duplication across adapter test subclasses; the Stage6-era parent run reported 93 tests before these 2 Stage7 regressions.

Pycompile:

```bash
python3 -m py_compile adapter.py stage3_adapter.py stage4_adapter.py stage5_adapter.py stage6_adapter.py stage7_adapter.py tests/test_stage7_adapter.py
```

Result: exit code 0.

## Review notes

Checked and retained:

- Stage7 only accepts `adapter-behavior-carddemo` and `--stage 7`; Stage8 is refused by parser-stage validation.
- Stage7 preserves current predecessor identity: `api-contract-carddemo-r3`, pipeline stage 6, artifact type `api-contract`, revision of `api-contract-carddemo-r2`, mandatory tracks `posting`, `interest`, `reporting`, upstream Stage5 pin.
- Stage7 rejects stale/mutated Stage6 r3 artifact, authorization, review, findings, stale recorded input pins, wrong feature, wrong stage, and reduced corpus without CLI bypass.
- Original Stage6/r2 provenance remains pinned through `require_stage6_r3_revision_history()` and does not require Stage6 r3 itself to be unapproved. The unapproved-recursion requirement applies to Stage6 r2 revision inputs, not the approved current r3 predecessor.
- Prompt/request construction remains prepare-only/offline unless an explicit execution authorization file matches stage/run/model/base_url/request hash. Existing execute path rechecks current pins before delegating.
- Payload still prohibits implementation/code/COBOL execution/Stage8/E1/E2 and retains adapter behavior documentary scope, but those prohibitions are prompt constraints, not authorization heuristics.

## Residuals

- Stage7 has not been generated, materialized, or human-reviewed.
- No network/model call was made; no execution authorization was consumed.
- Full suite output is noisy because negative-path tests intentionally print `ERROR:` lines while asserting return code 2; final unittest result is OK.

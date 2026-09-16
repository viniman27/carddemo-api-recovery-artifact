# Fixture integration technical QA — P2b/P3

Date: 2026-09-14T20:56:47Z

Scope: local technical integration only. This is not an official T1/T2/T3/T4 campaign, not an oracle run, and not an authenticated freeze/authorization gate.

## Implemented

- Added explicit external local fixture selection through `P2B_FIXTURE_REGISTRY`.
- Selection is local configuration only; public API requests remain the closed empty JSON object `{}` and no endpoint field/contract was added.
- Added descriptor-hash verification for selected local technical fixtures.
- Added per-invocation reset evidence using file-tree hashes before/after execution, not only run-directory names.
- Kept internal smoke fixtures available as development default when no external registry is configured.
- Strengthened P3 execution gating: `execution_decision()` remains fail-closed because no official runner/authenticated execution gate exists.
- Added internal OpenAPI-subset schema validation fallback because `jsonschema` was not installed in the active `python3` environment.

## External technical fixture registry

- Registry: `P3/local-technical-fixtures.json`
- Registry SHA-256: `bed546f5f3be4873329a778af20a69bbf75cee8e3d28467cb1b51c397e4529d6`
- Tracks covered:
  - `posting` / `CBTRN02C/POSTTRAN`: `posting-local-technical-smoke-v1`, descriptor hash `8ca59206b4e7de0aba26cf55c4fecca2bd7bce9860a570eb4879297b163d0761`
  - `interest` / `CBACT04C/INTCALC`: `interest-local-technical-smoke-v1`, descriptor hash `eb811e53b0782a6d9e1c0abfb4d511cbd68e36581b47ff723caea5793a2ef05b`
  - `reporting` / `CBTRN03C/TRANREPT`: `reporting-local-technical-smoke-v1`, descriptor hash `8cc44c7add0efe9c4bd69fc3629c13b93b77c1ecc3c0944281abc09544b952de`

## Commands executed

```bash
python3 -m unittest discover -s P2b/tests -v && python3 -m unittest discover -s P3/tests -v
python3 P3/pretest_config.py > P3/latest-pretest-config.stdout.json
python3 - <<'PY'  # validate P3/local-technical-fixtures.json and write local-technical-fixtures.validation.json
...
PY
P2B_FIXTURE_REGISTRY="$(pwd)/P3/local-technical-fixtures.json" python3 P2b/p2b_binding.py smoke > P2b/latest-smoke.stdout.json
python3 P2b/validate_p2b.py > P2b/latest-schema.stdout.json
python3 - <<'PY'  # negative hash validation + QA summary
...
PY
```

## Measured results

Evidence summary: `P3/fixture-integration-qa-summary.json`

- `readiness-manifest.json` SHA-256: `8f78c4f909cfeb53f9ee7d40aad8cfa0af7909307e96b8e81eaaefcc5657736f`
- `schema-validation-report.json` SHA-256: `283bf09d9db37b14f4db13aa31f25f833876e92a459bc9e8ca3ab157cee099dc`
- Schema QA: `overall_passed=true`, validator `internal-openapi-subset`
- Unit tests: P2b `14` tests OK; P3 `5` tests OK

Track executions through external local registry:

| Track | Status | Public item/record count | Audit evidence | Audit SHA-256 | Reset evidence |
|---|---:|---:|---|---|---|
| posting | 200 | 1 output item | `P2b/runs/posting-q88qbl6j/audit.json` | `e55c3f627a0c06e9a08bd2e7c26c61f44401ad5746c77761c75d234164a7b4e0` | before entries `0`, after entries `14`, resetEffective `true` |
| interest | 200 | 1 output item | `P2b/runs/interest-4habgnp3/audit.json` | `834d5dbb00edc21ff20b659480337c1790be9d48dbacd27f9f4ee706d6df4ed4` | before entries `0`, after entries `6`, resetEffective `true` |
| reporting | 200 | 4 public records | `P2b/runs/reporting-tkb0lzyk/audit.json` | `a30c6355e55bdcb9df02d4ffc9ab59e3c20f1e52e7e80347f16bcf812d32e357` | before entries `0`, after entries `6`, resetEffective `true` |

Additional measured framing:

- Reporting `TRANREPT`: `1064` bytes captured = `8` physical records at `133` bytes each; public mapping produced 4 records and retained raw classifications in audit.
- Posting/interest transaction parsing remains fixed at `350` bytes per transaction record.
- `missing`, `known_empty`, `truncated`, and `malformed` are tested as distinct capture classifications; `missing != empty` remains enforced by tests.
- Mixed known + unknown `TRANREPT` remains `technical_failure` with `availableContent` for recognized content and raw unknown audit evidence retained.

## Negative checks

- Hash adulteration check: `P3/negative-fixture-hash-validation.json`
  - Result: rejected with `FixtureConfigError`
  - Message: descriptor hash mismatch for `posting`
- Reset/isolation check: `P3/fixture-integration-qa-summary.json`
  - `uniqueAuditWorkdirs=3`
  - `allBeforeEmpty=true`
  - `allResetEffective=true`
  - Before/after tree hashes are recorded per audit.

## Archived prior evidence before overwrite

- Archive manifest: `P2b/evidence-archive/20260914T205418Z/archive-manifest.json`
- Also archived previous P3 pretest stdout under `P3/evidence-archive/20260914T205418Z/latest-pretest-config.stdout.json`

## Files changed or created

Code/tests:

- `P2b/p2b_binding.py`
- `P2b/validate_p2b.py`
- `P2b/tests/test_p2b_contract.py`
- `P3/pretest_config.py`
- `P3/tests/test_pretest_config.py`

Technical evidence/config:

- `P3/local-technical-fixtures.json`
- `P3/local-technical-fixtures.validation.json`
- `P3/local-technical-fixtures.tampered-hash.json`
- `P3/negative-fixture-hash-validation.json`
- `P3/fixture-integration-qa-summary.json`
- `P3/latest-pretest-config.stdout.json`
- `P3/FIXTURE-INTEGRATION-TECHNICAL.md`
- `P2b/readiness-manifest.json`
- `P2b/latest-smoke.stdout.json`
- `P2b/schema-validation-report.json`
- `P2b/latest-schema.stdout.json`
- new `P2b/runs/*/audit.json` evidence for the three technical invocations
- `P2b/evidence-archive/20260914T205418Z/*`
- `P3/evidence-archive/20260914T205418Z/*`

## Limits

- No official fixture, expected answer, model oracle, campaign, coverage claim, or cross-arm comparison was created.
- The external registry selects existing local technical materializers; it does not certify business semantics.
- `execution_decision()` is explicitly not an authorization mechanism and remains fail-closed without an official runner/authenticated gate.
- Active environment lacked `jsonschema`; schema QA used the internal validator over the OpenAPI subset present in P2a.

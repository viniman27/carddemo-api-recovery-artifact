# Revisão independente final — unified-preflight v2

Status: **PARTIAL** (preflight representativo qualificado, não campanha/autorização).

## Vereditos

- **modules_effective_adapter_freeze_load_replay_api_cobol**: PASS
- **ten_invocations_artifacts_pins_rawbytes_gcov_time_run**: PASS
- **fresh_gcda_and_parser_correct_scope**: PARTIAL
- **resetComparison_proves_resources_before_after**: PARTIAL
- **fresh_clone_fewshot**: PASS
- **process_tree_quiet_deadline**: PASS
- **exit4_nonzero_preserved**: PASS
- **absence_vs_zero_distinction**: PARTIAL
- **synthetic_mutants_against_old_evidence_wrong_attribution**: PASS
- **representative_preflight_limits_real**: PASS
- **no_authorization_created**: PASS

## Evidência mecânica

- Invocações verificadas: 10 (5 union-first + 5 reset).
- Raw response bytes/hash OK: 10/10.
- GCOV_PREFIX/cwd/exit/run vinculados: 10/10.
- Audit time/run id presente: 10/10.
- Business .gcda pinado e presente: 10/10.
- Parser seleciona main generated-C correto: 10/10.
- Quiet lifecycle: 10/10.
- Recursos pre-COBOL batem pins nos audits: 10/10; after observado: 10/10.
- Mutantes sintéticos mortos: 4/4.

## Limites materiais atuais

- resetComparison in unified-preflight-report.json does not itself expose resource pre/post hashes; proof exists in per-invocation audit STATE but is not surfaced in the comparison object.
- gcov-11 stderr has stamp mismatch on 8/10 invocations and corrected main-C .gcov shows Runs:0/executed lines 0 on 8/10 despite business .gcda presence; this is usable as fresh artifact/absence-vs-zero evidence, not as official coverage.
- System python cannot run unified-preflight-v2 tests without jsonschema; P2a venv is the real pinned environment.
- Preflight remains representative smoke only: 5 cases replayed twice, not official T1/T2/T3/T4 generation or all 21 operations.

## Próximo mínimo T1–T4

- T1: freeze preserved LLM scenario responses and adapter outputs with outbound/model metadata; do not call generators during campaign replay.
- T2: freeze offline Schemathesis/OpenAPI cases against real contracts, no shrinking side effects; replay each once via harness.
- T3: provide or explicitly block external-path to concrete request mapping; do not promote importers as generators.
- T4: build union only after T1-T3 frozen, then replay through the same API/COBOL target with resource pre/post reset comparison surfaced in report.
- Coverage: rebuild or align gcno/gcda so gcov has no stamp mismatch and nonzero counters can be distinguished from missing artifacts.

## Arquivos

- `review.json`: dados completos da revisão, hashes, mutantes e sumarização por invocação.
- `review_probe.py`: probes sintéticos/read-only usados nesta revisão.

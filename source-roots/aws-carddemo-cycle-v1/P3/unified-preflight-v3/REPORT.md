# unified-preflight-v3 correction report

Status: completed_success

Commands verified:
- `../../P2a/.venv/bin/python -m unittest discover -s tests -v` -> 14 tests OK
- `../../P2a/.venv/bin/python unified_preflight_cli.py --mode preflight --output evidence-20260915T-v3-fixed-current5x2-gcovclean` -> exit 0

Verified counts:
```json
{
  "checks_total": 10,
  "technical_smoke_cases": 5,
  "union_reset_cases": 5,
  "http_completed": 10,
  "checker_ok": 10,
  "reached_cobol": 10,
  "business_gcda_present": 10,
  "gcov_prefix_observed": 10,
  "admissible_preparatory_coverage": 10,
  "gcov_valid_clean": 10,
  "gcov_stderr_clean": 10,
  "gcov_exit_zero": 10,
  "coverage_artifact_links_complete": 10,
  "gcno_gcda_complete_pairs": 10,
  "program_exit_zero": 6,
  "program_exit_nonzero_positive_preserved": 4,
  "program_exit_signal": 0,
  "reset_rows_total": 5,
  "reset_rows_verified": 5,
  "reset_rows_effective_resource_hashes_compared": 5,
  "reset_rows_with_resource_paths": 5,
  "reset_resource_paths_total_across_rows": 47,
  "generated_p2b_py_compile_exit": 0,
  "generated_p2b_py_compile_stderr": ""
}
```

Output artifacts:
- report: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/unified-preflight-v3/evidence-20260915T-v3-fixed-current5x2-gcovclean/unified-preflight-report.json`
- candidate manifest: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/unified-preflight-v3/evidence-20260915T-v3-fixed-current5x2-gcovclean/candidate-manifest.json`
- evidence manifest: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/unified-preflight-v3/evidence-manifest.json`

Notes:
- Generated isolated `P2b/p2b_binding.py` compiles with `py_compile` before startup.
- Startup syntax failures now fail immediately with stderr rather than waiting for the port timeout.
- All 10 current 5×2 checks have complete gcno/gcda link pairs and clean gcov stderr before admissibility.
- Non-zero program exits are preserved: posting returned programExit=4 in 4 checks; not rewritten to success.
- resetComparison uses real resource hash sets: 5/5 rows verified beyond distinct directories.

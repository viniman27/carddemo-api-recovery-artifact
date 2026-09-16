# Complementary validation runtime-v2 corrected report

Scope: preserved runtime-v1 three-track API/COBOL observations enriched with real byte provenance; no API/COBOL re-execution.

Reusable command: `python3 <REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/complementary-validation-runtime-v2/tools/enrich_and_check.py --runtime-v1 <REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/complementary-validation-runtime-v1 --checker <REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/complementary-validation-implementation-v3 --out-root <REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/complementary-validation-runtime-v2/evidence`

Status counts over the 25-record catalog: {"inconclusive": 2, "pass": 6, "pending": 17}.

Interpretation: PASS is limited to implemented obligations whose observed semantics and byte provenance were sufficient. INCONCLUSIVE means missing trace/evidence, not failure. PENDING means checker not implemented in this representative slice.

## Implemented-obligation outcomes
- POSTTRAN-OBL-003: pass (pass)
- POSTTRAN-OBL-004: pass (pass)
- POSTTRAN-OBL-006: pass (pass)
- POSTTRAN-OBL-009: inconclusive (transaction POST-PRESENT-001 observed effect records missing; effectOrder flags are not accepted as COBOL write evidence)
- INTCALC-OBL-005: pass (pass)
- INTCALC-OBL-006: pass (pass)
- TRANREPT-OBL-002: pass (pass)
- TRANREPT-OBL-006: inconclusive (totals branch not observed before EOF; missing totals are inconclusive evidence, not semantic mismatch)

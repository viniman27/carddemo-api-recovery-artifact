# Complementary runner binding v1 STATUS

Status: executable binding exercised on preserved real essential-case artifacts.

- Cases bound: 12 ({'posting': 6, 'interest': 2, 'reporting': 4})
- Checker statuses: {'pass': 14, 'inconclusive': 7}
- API/COBOL/model reruns: none; all evidence came from pinned preserved P3 files.
- Model classification: shared_source_guided_qualification; no case has a qualified per-case T3 transition tie.
- Missing trace is handled as inconclusive, not semantic failure (posting effect order and reporting EOF totals remain guarded).

Next complete limitation: a future official runner can reuse this binding only prospectively after pinning the checker/source manifest before first official execution; this result does not retroactively promote complementary cases into T1/T2/T3/T4 official campaign evidence.

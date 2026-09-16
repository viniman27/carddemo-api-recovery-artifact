# Coverage report reconciliation v1

Status: corrected limited reconciliation from existing gcov artifacts only; not official campaign coverage.

## Scope and admissibility

- No COBOL/API/campaign/build/gcov rerun was performed by this reconciliation.
- Principal metric scope is the main generated C unit per business program.
- Generated headers are listed separately and are not merged into the principal C denominator.
- Generated-C branch counters are not COBOL business-decision counts.
- Distinct run directories and GCOV_PREFIX values evidence artifact isolation, but do not alone prove reset semantics beyond the observed files.

## Corrected totals by program

| Program | Invocations | Comparable main C denominator (lines/branches/calls) | Matches prequalification |
|---|---:|---:|---|
| CBACT04C | 2 | 1029/266/148 | True |
| CBTRN02C | 2 | 1120/288/154 | True |
| CBTRN03C | 2 | 1192/272/157 | True |

## Per invocation corrected main generated-C counts

| # | Track | Program | Exit | Lines | Branches executed | Branches taken >=1 | Calls | Old mixed totals (L/B/C) |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | posting | CBTRN02C | 4 | 651/1120 | 246/288 | 133/288 | 94/154 | 1134/38/154 |
| 2 | interest | CBACT04C | 0 | 585/1029 | 214/266 | 116/266 | 85/148 | 1043/36/148 |
| 3 | reporting | CBTRN03C | 0 | 655/1192 | 216/272 | 111/272 | 85/157 | 1244/48/2 |
| 4 | posting | CBTRN02C | 4 | 651/1120 | 246/288 | 133/288 | 94/154 | 1134/38/154 |
| 5 | interest | CBACT04C | 0 | 585/1029 | 214/266 | 116/266 | 85/148 | 1043/36/148 |
| 6 | reporting | CBTRN03C | 0 | 655/1192 | 216/272 | 111/272 | 85/157 | 1244/48/2 |

## Artifact manifest

Manifest: `artifact-manifest.json` (18 gcov unit entries pinned).

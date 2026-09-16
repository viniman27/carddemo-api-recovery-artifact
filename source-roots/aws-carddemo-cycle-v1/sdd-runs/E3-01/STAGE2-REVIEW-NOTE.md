# Stage 2 — generated, not approved

The original model response is preserved byte-for-byte in specs/capability-selection-carddemo/requirements.md and prepared/capability-selection-carddemo/execution/scope-original.md (historical output filename reused by bridge). Model gpt-6-astra returned completed, HTTP 200; no retry or response repair. Stage 2 remains unapproved.

Selection proposed: daily transaction posting (CBTRN02C / POSTTRAN). Interest generation and reporting are adjacent alternatives, not selected capabilities. Human review must explicitly consider this narrowing against the cycle-level comparison scope; do not silently equate a posting-only SDD contract with whole-cycle E1/E2 results. No semantic adjudication or comparability claim has been completed.

Stage 3 remains blocked pending explicit approval of this selection and its input visibility. APIs and AWS tests remain unstarted.

Adapter verification: 11 unittest tests passed. Parent review found a text-substitution defect that altered generic exclusion-policy wording while retaining original hashes; a regression test failed, the substitution was removed before preparation/execution, and the suite passed. All 19 source body hashes, framework text hashes, verbatim upstream scope and prepared request hash were checked before sending.

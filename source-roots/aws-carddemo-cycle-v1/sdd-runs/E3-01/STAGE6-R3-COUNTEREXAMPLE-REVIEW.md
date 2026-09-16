# Stage 6 r3 Counterexample Review

## Verdict

**No source-grounded counterexample found that blocks r3 as an unapproved Stage 6 draft.** This is not approval for implementation.

## Criteria review

- AC1: PASS — External input identity/selection/provisioning/readiness track-specific; no invented provisioning endpoints
- AC2: PASS — Deployment/runtime binding choices are proposals/unresolved, not facts
- AC3: PASS — available items: [] distinct from unavailable
- AC4: PASS — zero rate distinct from zero amount/quantity and missing disclosure
- AC5: PASS — Empty/no-generated interest observations not forced into 503
- AC6: PASS — Empty reporting observations not forced into 503 and not complete report/zero totals
- AC7: PASS — Posting progress-only success scoped; not output fulfillment/durability
- AC8: PASS — All-unavailable/no-observation blocked from 200
- AC9: PASS — EOF/date/report limitations intact
- AC10: PASS — r3 unapproved and not ready for implementation

## Source-grounded checks

- `CBTRN02C.cbl:202-230,424-463`: progress/reject counts and write attempts support the r3 limitation that progress-only `200` is not durable output fulfillment. Internal preliminary reason `109` is not exposed as a public rejection reason.
- `CBACT04C.cbl:214-217,415-460,462-515`: zero-rate bypass, missing/default disclosure handling, and generated transaction writes support keeping zero rate, zero amount/quantity, missing disclosure, and unavailable/failure separate.
- `CBTRN03C.cbl:180-206,274-322,343-358`: reporting writes observed records/totals/headers at distinct points; an empty observed records array cannot certify complete report, zero totals, or final account total.

## r2 vs r3 regression review

- Focused diff assessment: r3 changes concentrate on observed-empty vs unavailable/status wording and envelope constraints.
- No unrelated regression found in the three operation routes, empty closed request shapes, external-input responsibility, order preservation, or multiplicity preservation.
- The prior external-input design remains a human design choice, not the r3 blocker.

## Boundaries

- I did not run model generation, network calls, COBOL execution, Stage 7, or OpenAPI generation/validation.
- The statement that the document is OpenAPI-representable was not independently validated here and must not be treated as an OpenAPI validity result.

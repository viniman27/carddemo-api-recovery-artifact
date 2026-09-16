# Stage 6 r2 Directed Feedback — External Inputs and Empty Outputs

## Verdict

**r3 required before Stage 6 acceptance.** Keep the r2 structure and most decisions. Apply a narrow revision to the empty-output response boundary only.

Do not start Stage 7. Do not edit original r1/r2 outputs, approvals, corpus, framework, or upstream specs.

## Version pins

- Current candidate: `specs/api-contract-carddemo-r2/requirements.md`, SHA-256 `163d1d0455f2524e8100e1722b78f255fbca7a4bda1a5caccb45e05fbe362567`.
- Original generated r2: `prepared/api-contract-carddemo-r2/execution/scope-original.md`, SHA-256 `163d1d0455f2524e8100e1722b78f255fbca7a4bda1a5caccb45e05fbe362567`.
- Upstream Stage 5: `specs/canonical-data-boundary-carddemo/requirements.md`, SHA-256 `208d04fe6f9cae665dfa4cb514de5d4ad9eaf0ebc169dfae0fd8a6ba209e66f3`.
- Upstream Stage 4: `specs/capability-semantics-carddemo/requirements.md`, SHA-256 `2f9d3ee52dd7788e206810e38c9173b19d21dfc44270cdd06d05e62dec95eb93`.
- Focused review record: `STAGE6-R2-INPUTS-EMPTY-REVIEW.md`.

## Keep unchanged

Do not revise these unless directly needed to integrate the narrow empty-output fix:

1. Three separate routes: `POST /posting`, `POST /interest`, `POST /reporting` (`requirements.md:117-123`).
2. Empty closed request objects as an interface proposal, not a COBOL fact (`requirements.md:167-175`, `300-303`).
3. No request-level business properties, dataset selector, EOF signal, singleton resource assumption, provisioning facility, reset, retry, status resource, CRUD, rollback, or job scheduling (`requirements.md:167-175`, `207-215`).
4. External/internal accountability tables for posting, interest, and reporting (`requirements.md:388-394`, `420-426`, `450-456`).
5. State/resource table distinguishing external inputs from internal dependencies and unresolved operational resources (`requirements.md:520-552`).
6. Proposal status: HTTP/status/schema choices remain human-gate proposals, not deployment/runtime facts (`requirements.md:40-46`, `159-165`, `487-489`, `673-679`).

The external-input design is not the blocking defect.

## Required r3 change: distinguish observed empty from unavailable

r2 currently creates a narrow contradiction:

- It allows an available sequence with zero items as an observation (`requirements.md:306-313`).
- It then requires interest/reporting `200` envelopes to have `minItems: 1` (`requirements.md:338-342`).
- It assigns no-substantive-content/no-known-failure to `503 content_unavailable`, while explicitly denying that this means empty business result (`requirements.md:491-498`, `503-510`).
- It says legitimate no-output paths are not converted into failures, but future positive zero-output distinction remains blocked (`requirements.md:642-644`).

Revise this boundary so the contract can represent:

1. `available` with `items: []` = observed empty represented sequence;
2. `unavailable` = no item observation represented;
3. zero amount / zero computed quantity = a value, not absence;
4. zero-rate bypass / no generated interest transaction = no transaction generated through that branch, not rejection;
5. known technical failure = `500` only when known at the response boundary.

## Source-grounded counterexamples to preserve

### Interest

- `CBACT04C.cbl:214-217` selects computation/write only when `DIS-INT-RATE NOT = 0`; zero rate bypasses computation and fees.
- `CBACT04C.cbl:462-515` computes, accumulates, constructs, and writes the generated transaction when that branch is selected.
- Stage 4 states nonzero rate selects computation/write even for zero or negative balance/result, while zero rate bypass is not a rejection (`capability-semantics-carddemo/requirements.md:215-221`).
- Stage 5 states missing disclosure is not zero rate and generated transaction output is conditional (`canonical-data-boundary-carddemo/requirements.md:167-171`, `266-271`, `318-325`).

Therefore: do not force a positively observed empty generated-transaction sequence into `503`, and do not confuse it with zero amount or unavailable disclosure.

### Reporting

- `CBTRN03C.cbl:170-206` compares dates before the post-read EOF branch; the date alternative uses `NEXT SENTENCE`; EOF finalization is conditional.
- `CBTRN03C.cbl:293-322` writes page and grand totals at distinct sites; there is no EOF account-total call in the shown finalization path.
- Stage 4 states the date alternative is not skip-and-continue and the EOF finalization has no final account-total call (`capability-semantics-carddemo/requirements.md:231-261`).
- Stage 5 states the boundary must not infer an empty complete report from missing dates, failure, absent detail output, or early loop exit (`canonical-data-boundary-carddemo/requirements.md:231-243`).

Therefore: an observed empty `records` sequence, if represented, must not mean complete empty report, complete date-range processing, zero totals, reconciled totals, or final account total.

### Posting

- `CBTRN02C.cbl:202-230` increments processed/reject counts and displays them after closes; counts are not durable posted/rejected output counts.
- `CBTRN02C.cbl:424-579` attempts category, account, and transaction writes in order; earlier attempts can precede later failures.
- Stage 5 states `PostingProgress` counts concern encountered processing and selected rejection paths, not committed transactions or durable rejects (`canonical-data-boundary-carddemo/requirements.md:157-161`, `209-212`, `253-260`).

Therefore: if progress-only `200` remains allowed, explicitly scope zero counts such as `processedRecordCount: 0`, `preliminaryRejectCount: 0` to progress observation only. It must not prove no effects, full exhaustion, or satisfied transaction/rejection output obligations.

## Minimal revision instructions

1. Keep D-14 external-input batch participation unchanged in substance.
2. Keep D-15 ordered envelopes unchanged in substance.
3. Revise D-16 / §3.4 / §5.2 / §7.3 only as needed to distinguish:
   - all-unavailable/no-observation envelope: not `200`;
   - observed empty sequence: may be `200` with `availability: "available", items: []`, if the response boundary really has that observation;
   - unavailable observation: `503 content_unavailable` if no known technical failure and no representable observation;
   - known technical failure: `500`, with optional already available content.
4. Remove or narrow blanket `minItems: 1` for `InterestEnvelope` and `ReportingEnvelope`.
5. Do not add branch telemetry, file status, dataset IDs, provisioning endpoints, polling resources, or deployment-specific readiness endpoints.
6. Do not claim the API can know every zero-output condition. The point is to permit a represented empty observation when available, not to certify completeness.
7. Keep all status choices labeled as proposals requiring human gate acceptance.

## Acceptance criteria for r3

- [ ] External input identity/selection/provisioning/readiness accountability remains track-specific and does not expose invented provisioning endpoints.
- [ ] Deployment/runtime binding choices are described as proposals or unresolved authority, never facts.
- [ ] `available items: []` is distinct from `unavailable`.
- [ ] Zero rate is distinct from zero amount and missing disclosure.
- [ ] Empty/generated-no-transaction interest observations are not forced into `503`.
- [ ] Empty reporting observations are not forced into `503` and do not certify complete empty reports.
- [ ] Posting progress-only success is explicitly scoped and does not satisfy transaction/rejection output obligations by itself.
- [ ] All-unavailable/no-observation content is still blocked from `200`.
- [ ] EOF date/report limitations remain intact: no final account total, no skip-and-continue repair, no zero missing totals, no complete-range guarantee.
- [ ] r3 remains unapproved and not ready for implementation until external human gate approval.

## Do not do

- Do not blanket-mark all outputs unknown.
- Do not remove valid response proposals just because runtime deployment is unresolved.
- Do not invent dataset selectors, input upload/provisioning APIs, readiness probes, reset endpoints, or polling/status resources.
- Do not expose internal lookup/disclosure/account/category resources as consumer-controlled inputs.
- Do not perform E1/E2 comparison or test alignment.
- Do not execute COBOL or generate implementation/OpenAPI artifacts in this revision task.

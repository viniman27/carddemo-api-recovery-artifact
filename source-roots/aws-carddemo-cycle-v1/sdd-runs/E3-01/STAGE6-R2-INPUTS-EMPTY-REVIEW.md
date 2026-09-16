# Stage6 r2 Focused Review — External Inputs and Legitimately Empty Outputs

## Verdict

**r3 required before Stage 6 human acceptance.** The r2 contract is mostly source-grounded on external-input responsibility and avoids invented provisioning endpoints, but it still has a narrow response-boundary contradiction for legitimately observed empty output sequences.

This review does **not** approve Stage 6, does **not** authorize Stage 7, and does **not** compare E3 with E1/E2.

## Scoped inspection

Inspected only:

- Stage 6 r2 generated/materialized artifact: `specs/api-contract-carddemo-r2/requirements.md`, SHA-256 `163d1d0455f2524e8100e1722b78f255fbca7a4bda1a5caccb45e05fbe362567`.
- Stage 6 r2 original retained output: `prepared/api-contract-carddemo-r2/execution/scope-original.md`, SHA-256 `163d1d0455f2524e8100e1722b78f255fbca7a4bda1a5caccb45e05fbe362567`.
- Stage 5 canonical boundary: `specs/canonical-data-boundary-carddemo/requirements.md`, SHA-256 `208d04fe6f9cae665dfa4cb514de5d4ad9eaf0ebc169dfae0fd8a6ba209e66f3`.
- Stage 4 capability semantics: `specs/capability-semantics-carddemo/requirements.md`, SHA-256 `2f9d3ee52dd7788e206810e38c9173b19d21dfc44270cdd06d05e62dec95eb93`.
- Prior Stage 6 r2 counterexample review: `STAGE6-R2-COUNTEREXAMPLE-REVIEW.md`.
- Actual allowlisted COBOL/JCL excerpts for the three tracks:
  - `app/cbl/CBTRN02C.cbl`, SHA-256 `708f3cadc555acab63f11e2f3238f5372ac7180e6b01197bf960d96bf0d2e83f`.
  - `app/cbl/CBACT04C.cbl`, SHA-256 `5084bb8b0c9a0f0199f737487ae1863f12e43cabbdc459a62b6b67bedc683cc4`.
  - `app/cbl/CBTRN03C.cbl`, SHA-256 `8691e625502b7efcfd7ba4ae61797132e7b68f3fd5fedcdcc7dd6488f6871eef`.
  - `app/jcl/POSTTRAN.jcl`, SHA-256 `ecff62c691e6ce101de08690e72ec065bc98bd845744ddf914899097d37c9191`.
  - `app/jcl/INTCALC.jcl`, SHA-256 `61afa664a807558e58213641d9f3317ab3b354a350c4c1536a630897d194d275`.
  - `app/jcl/TRANREPT.jcl`, SHA-256 `7d8fc0777e6b9fb1c62aee6b4b10a67d127057c84b92203c7152f230b3db9571`.

Not inspected: zero-shot/few-shot outputs, quarantine/evaluation materials, network/model output, generated OpenAPI, COBOL execution, implementation artifacts.

Repository note: the workspace git repository reports `No commits yet on master`; therefore there is no usable git commit pin for this review. Version pins above are file SHA-256 pins.

## Track map — external input responsibility versus internal dependencies

### Posting

r2 treatment is acceptable with no necessary revision on input responsibility.

- Consumer-supplied participation is limited to the operation request: `PostingRequest` is an empty closed JSON object and carries no business fields (`requirements.md:167-175`, `302`, `381-386`, `388-394`).
- The actual daily candidate sequence remains external and unselected by HTTP (`requirements.md:119`, `171`, `391`, `393`, `522`).
- Xref, account, category balance, branch flags, reason 109, file status and snapshots remain internal/not exposed (`requirements.md:392-394`, `523-528`).
- Stage 5 supports this split: daily candidate sequence is encountered source input with unresolved contents/order/cardinality, while card/account/category dependencies are internal resources, not new state-control capabilities (`canonical-data-boundary-carddemo/requirements.md:306-312`).
- COBOL/JCL supports the same accountability split: `POSTTRAN.jcl` binds external datasets `DALYTRAN`, `XREFFILE`, `ACCTFILE`, `TCATBALF` and outputs (`POSTTRAN.jcl:23-42`); `CBTRN02C.cbl` reads `DALYTRAN-FILE`, increments counters only for non-EOF records, then validates and posts/rejects (`CBTRN02C.cbl:202-230`, `345-422`).

No invented provisioning endpoint is exposed: r2 explicitly excludes CRUD, provisioning, reset, rollback, status, scheduling and pagination (`requirements.md:207-215`).

### Interest

r2 treatment is acceptable with no necessary revision on input responsibility.

- Consumer-supplied participation is limited to the operation request (`requirements.md:413-418`, `420-426`).
- The encountered category sequence and identifier parameter text are external bases, not request properties (`requirements.md:120`, `239-243`, `423`, `529`, `533`).
- Account, account-key xref, disclosure basis, group accumulator and suffix remain internal dependencies (`requirements.md:424`, `530-536`).
- Stage 5 supports this split: `InterestCategoryBasis` and `InterestIdentifierBasis` are boundary bases, while account/xref/disclosure/group/suffix state remain internal or unresolved (`canonical-data-boundary-carddemo/requirements.md:167-171`, `218-227`, `318-325`).
- COBOL/JCL supports the split: `INTCALC.jcl` supplies `PARM='2022071800'` and binds `TCATBALF`, `XREFFILE`, `ACCTFILE`, `DISCGRP`, and output `TRANSACT` (`INTCALC.jcl:22-41`); `CBACT04C.cbl` accepts `EXTERNAL-PARMS`, reads category records, performs internal account/xref/disclosure reads, and constructs generated transactions (`CBACT04C.cbl:175-180`, `188-217`, `350-460`, `473-515`).

The deployment choice remains a proposal because r2 labels request shape and status choices as `P` and human-gate dependent (`requirements.md:40-46`, `167-175`, `487-489`).

### Reporting

r2 treatment is acceptable with no necessary revision on input responsibility.

- Consumer-supplied participation is limited to the operation request (`requirements.md:443-448`, `450-456`).
- Reporting transaction sequence, date input, and upstream selection context are external/documentary; the HTTP request does not provide date values, SORT override, EOF, or default dates (`requirements.md:269-278`, `453-456`, `537-539`).
- Card xref, type/category lookup, current-card state, accumulators and presentation counters remain internal (`requirements.md:454`, `540-547`).
- Stage 5 supports this split: reporting transaction/date/upstream selection bases are external or documentary, while xref/lookups/accumulators/output state retain unresolved runtime scope (`canonical-data-boundary-carddemo/requirements.md:177-183`, `231-243`, `331-341`).
- COBOL/JCL supports the split: `TRANREPT.jcl` has a SORT step with literal bounds and a separate `CBTRN03C` step with `TRANFILE`, `CARDXREF`, `TRANTYPE`, `TRANCATG`, `DATEPARM` and `TRANREPT` DDs (`TRANREPT.jcl:23-80`); `CBTRN03C.cbl` separately reads `DATEPARM`, reads transactions, compares dates, and uses internal lookup/output paragraphs (`CBTRN03C.cbl:159-243`, `248-374`, `484-512`).

No invented API-level provisioning, date override, dataset selector, or EOF signal is exposed (`requirements.md:167-175`, `207-215`, `450-456`, `516-552`).

## Empty-output audit

### Distinctions r2 handles correctly

1. **Unavailable observation is not zero output.** r2 defines `availability: "unavailable"` as “No item content is represented; not a claim of zero output or no effects” (`requirements.md:306-313`). This matches Stage 5’s distinction between missing output observation and zero/absence (`canonical-data-boundary-carddemo/requirements.md:185-193`).

2. **Missing disclosure is not zero rate.** r2 states missing disclosure is not zero rate and zero-rate bypass is not rejection (`requirements.md:254-261`, `432-434`, `505-510`). Stage 4 and COBOL support this: disclosure fallback has status-specific behavior, and only a selected rate equal to zero bypasses computation (`capability-semantics-carddemo/requirements.md:207-221`; `CBACT04C.cbl:415-460`, `214-217`).

3. **Zero amount is not zero rate.** r2 keeps nonzero-rate generation even with zero or negative balance/result (`requirements.md:259-260`, `590`). Stage 4 explicitly says nonzero rate selects computation/write including zero or negative balance/result (`capability-semantics-carddemo/requirements.md:215-221`), and COBOL computes then writes when `DIS-INT-RATE NOT = 0` (`CBACT04C.cbl:214-217`, `462-515`).

4. **Posting progress counts are not committed output counts.** r2 treats `processedRecordCount` and `preliminaryRejectCount` as optional observation with no committed-count interpretation and no `postedCount` (`requirements.md:149`, `238`, `252`, `315-320`, `340-346`, `406-407`). Stage 5 supports this: counts are displayed completion information, not durable transactions/rejects (`canonical-data-boundary-carddemo/requirements.md:157-161`, `209-212`, `253-260`). COBOL increments processed/reject counters and later displays them; it does not derive durable posted counts (`CBTRN02C.cbl:202-230`).

5. **Reporting date/EOF limitations are preserved.** r2 does not promise skip-and-continue filtering, complete report, final account total, zero missing totals, or certified empty report (`requirements.md:286-294`, `458-469`, `592-597`, `637-644`). Stage 4 and COBOL support this: the date alternative uses `NEXT SENTENCE`, EOF finalization is conditional and has page/grand calls but no account-total call (`capability-semantics-carddemo/requirements.md:231-261`; `CBTRN03C.cbl:170-206`, `293-322`).

6. **200 content guard blocks all-empty/unavailable success.** r2 says a `200` content response requires substantive output content and that all-empty/all-unavailable envelopes are not content success (`requirements.md:185-193`, `338-346`, `491-498`). This correctly blocks vacuous success for unavailable observations.

### Actual contradiction / under-specified response case

r2 simultaneously says:

- an available sequence may have zero items “as an observation of the represented sequence” (`requirements.md:306-313`), but
- interest and reporting `200` responses require `minItems: 1` (`requirements.md:338-342`), and
- `503 content_unavailable` explicitly denies that it represents an empty business result (`requirements.md:491-498`, `503-510`), while
- r2 later says legitimate no-output paths are not converted into business failures and a future positive zero-output distinction remains blocked (`requirements.md:642-644`).

For posting, the same tension is narrower because `200 PostingEnvelope` may be satisfied by available progress even when transaction/rejection arrays are empty (`requirements.md:340-346`). That is defensible for an observed empty posting input/progress count case, if it remains only a progress observation and not proof of complete consumption or durable no-output. But r2 should make that explicit because `PostingProgress` with `processedRecordCount: 0` and `preliminaryRejectCount: 0` is a legitimate observation, not substantive transaction/rejection output.

For interest and reporting, the contradiction is blocking: an adapter could legitimately observe an available empty generated-transaction sequence or report-record sequence, but r2 gives no non-error response category for it. `503` is reserved for inability to provide substantive content and denies empty business result, so it cannot cleanly represent an observed empty result. This is not a request to certify complete batch/range processing; it is only a need to keep **available empty sequence observation** distinct from **unavailable observation** and **technical failure**.

Concrete source-grounded counterexamples:

- **Interest zero generated transactions can be legitimate without missing observation:** if selected disclosure rates are zero for encountered category records, COBOL bypasses compute/write (`CBACT04C.cbl:214-217`), and Stage 4 classifies this as zero-rate bypass, not rejection (`capability-semantics-carddemo/requirements.md:215-221`). r2 correctly says zero-rate is not an error, but `InterestEnvelope` requires `minItems: 1` for `200` (`requirements.md:341`) and `503` denies empty business result (`requirements.md:497`).
- **Interest nonzero rate with zero computed amount still generates a transaction:** this is already correctly handled and must not be collapsed into the previous case (`requirements.md:259-260`; `CBACT04C.cbl:462-515`).
- **Reporting no represented records can be an observation without a certified complete empty report:** date-input EOF, date alternative exit, or unavailable post-read storage cannot be turned into complete-report claims (`CBTRN03C.cbl:170-243`; `requirements.md:455-469`). But if the response boundary actually observes no representable report records, r2 should allow that observation without calling it `content_unavailable`, while still denying complete range/report guarantees.

## Minimal necessary r3 feedback

Do **not** rewrite the contract wholesale. Preserve the r2 external-input design and all no-provisioning/no-selector/no-EOF limitations. Revise only the empty-output response boundary:

1. Separate these cases explicitly:
   - `available` with `items: []` as an observed empty represented sequence;
   - `unavailable` as no represented observation;
   - zero amount / zero computed quantity;
   - zero-rate bypass / no generated interest transaction;
   - technical failure known to the boundary.
2. Remove or narrow the blanket `minItems: 1` requirement for `InterestEnvelope` and `ReportingEnvelope`; allow `200` for `availability: "available", items: []` only as an **observed empty representation**, not as proof of complete batch/range processing.
3. Keep the all-unavailable guard: all outputs unavailable and no progress/content observation must not become `200`.
4. For posting, state whether `PostingProgress` with zero counts may satisfy `200` as progress observation only, and explicitly deny that it proves no transaction/rejection effects, complete input exhaustion, or durable state.
5. Keep `503 content_unavailable` for lack of substantive observation, not for positively observed empty sequences.
6. Preserve report EOF/date limitations: an empty `records` array must not mean complete empty report, reconciled zero totals, final account total, or successful full date-range processing.

## Acceptance criteria for r3

- [ ] Three tracks still use separate operation requests and no business properties in the request body.
- [ ] No dataset selector, provisioning endpoint, reset, status resource, EOF signal, retry/idempotency, or deployment/runtime binding is introduced.
- [ ] Posting, interest, and reporting each identify external input, internal dependencies, unknown readiness/EOF, and non-exposed state separately.
- [ ] `available items: []`, `unavailable`, zero amount, zero rate, empty posting progress, and technical failure are distinct response concepts.
- [ ] Interest zero-rate/no-generated-transaction observation is not forced into `503` or business failure.
- [ ] Reporting observed empty records are not forced into `503`, but also do not certify a complete empty report or zero totals.
- [ ] Posting progress-only `200`, if retained, is explicitly scoped to observed counts and cannot satisfy transaction/rejection output obligations.
- [ ] `200` remains blocked for all-unavailable/no-observation envelopes.
- [ ] All revised status choices remain labeled as interface proposals requiring human gate acceptance.
- [ ] No original specs, approvals, corpus, framework, or prior generated artifacts are edited.

## Final disposition

External input responsibility: **not falsified**; no broad revision needed.

Legitimately empty outputs: **blocking narrow contradiction found**. r3 is required before human acceptance of Stage 6, limited to empty-output response semantics and the `200`/`503` boundary. Stage 7 remains blocked.

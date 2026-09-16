# API Contract Specification

## Purpose

This Stage 6 specification drafts the API contract for the AWS CardDemo public cycle from the approved Stage 5 canonical data boundary. **Posting, interest, and reporting are mandatory, separately traceable tracks.**

| Attribute | Value |
|---|---|
| Run | `E3-01` |
| Stage | `6` |
| Feature | `api-contract-carddemo` |
| Artifact path relative to `RUN_ROOT` | `specs/api-contract-carddemo/requirements.md` |
| Exact inherited capability identity | `unselected-stage-1-scope-only` |
| Mandatory tracks | `posting`, `interest`, `reporting` |
| Status | Draft with explicit blocking contract gaps |
| Human approval granted by this document | `false` |
| Completeness gate passed | `false` |
| Ready for implementation | `false` |

The document defines traceable method, route, and schema representation choices where permitted. It does **not** turn source-path distinctions into guaranteed observations, output attempts into durable receipts, or unresolved input policies into validation rules.

The operation contracts below are **incomplete where expressly marked by G-21–G-24**. Their concrete routes and component schemas are draft representation choices, not a claim that a complete callable contract has been established.

This response supplies `requirements.md` text only. It does not persist files, change metadata, execute COBOL, implement anything, or approve a gate.

## Contract Integrity Discipline

- Every contract element derives from a canonical element or a recorded design decision (`D-n`); nothing enters the surface from implementation convenience.
- Outcome-variant mappings follow Stage 5’s mapping notes.
- Error strategy decisions are recorded, justified, and traceable.
- EARS phrasing is used only for already-grounded conditional obligations.
- The contract is representable in OpenAPI, the preferred contract format.
- Schema representability does not establish an accepted business input domain.
- Internal states and branches are not public observations merely because Stage 5 named them.
- All inherited uncertainty remains visible. No conventional financial behavior substitutes for the approved rules.
- No generated implementation, runtime binding, storage design, recovery mechanism, or execution result is included.

## Section 1: Upstream Authority and Entry Condition

### 1.1 Upstream Authority and Scope Inheritance

The immediate authority is the approved Canonical Data Boundary Specification:

`specs/canonical-data-boundary-carddemo/requirements.md`

SHA-256: `208d04fe6f9cae665dfa4cb514de5d4ad9eaf0ebc169dfae0fd8a6ba209e66f3`.

The supplied Stage 5 authorization permits Stage 6 API contract specification for all three tracks, with explicit unresolved gaps. It directs that unsupported guarantees must not close those gaps and that a concrete contract decision requiring invention must stop for human decision.

The current authority chain is retained as supplied:

| Stage | Artifact SHA-256 | Current `spec.json` SHA-256 |
|---|---|---|
| 1 | `1362fab5d55b77ef6121328606ae974295cd5723849520e9a246f4bd45e64cc9` | `c71fe711834fec66fb417335a2f60cde5b9f3b5b63968849c71ecc513b465978` |
| 2-r2 | `abdb59180f379d9e14eb86dfa1d8226ec50c981346767e808fd382eb7462bbc4` | `7d218739f4f338d568805051ec2e7f9ce70128d832c0dfbcdc11c34f704d2973` |
| 3-r2 | `4566786600b60e9377c1e369e67765098d06b0153ba973361d2065614a6c9b7b` | `d34866601d0156c103dc850148e32748da75c0134dbb6b6f6d4b58324a7d61a7` |
| 4 | `2f9d3ee52dd7788e206810e38c9173b19d21dfc44270cdd06d05e62dec95eb93` | `0cc4b961f75d95c86e34fa7269ed6a74c1da4b6f7d5ed9e6b4cde43c4e82bbcb` |
| 5 | `208d04fe6f9cae665dfa4cb514de5d4ad9eaf0ebc169dfae0fd8a6ba209e66f3` | `4f6005cba97aa29d3a73e6cc4e36d2b0401fe159bcdfc5f28b0c2447080a10ef` |

Authorization pins:

| Path relative to `RUN_ROOT` | SHA-256 |
|---|---|
| `reviews/stage-1-authorization.json` | `0ec9d89962c088507775523f266816b5c3c13f7631c7a6409b45bc13352542da` |
| `reviews/stage-2-r2-authorization.json` | `22294af2fb12235297e57e4b084a729695864af895d4047eb4a630d7286ec1c9` |
| `reviews/stage-3-r2-authorization.json` | `d8cdf343b5ed63cdd2e83e1627a50673acdb34930ae0c63e29be0e8fb122941e` |
| `reviews/stage-4-authorization.json` | `405caf0960e1a13dfbc8a8965340e9f4957571b8eea0b895b09b125e21025ee9` |
| `reviews/stage-5-authorization.json` | `a2f73337b5ec123d62ab41e9c058a3065f1ccf133c48e5b81f54f9a2610bfe23` |

Review attachments used:

| Path relative to `RUN_ROOT` | SHA-256 |
|---|---|
| `STAGE4-COUNTEREXAMPLE-REVIEW.md` | `56f32db0669f3c738ed83ee0294929ca1ee0f5c76e663eb2abdbecab7e319e29` |
| `STAGE5-COUNTEREXAMPLE-REVIEW.md` | `0dadcd665b1e4cb71765003c22655f7b04a3430bf92077f9d63d33053aa2fdfe` |
| `stage5-counterexample-findings.json` | `caa6418e2ebec9e52a795e1bafd9ca304a21d55a0c28e73e86b06162c33ec84e` |

The historical Stage 5 metadata hash `8e869738d9fe897f3118b5495775ec091f909d79d6a9aeddd36e2baadbbfcc5c` in the review findings is retained as review-time provenance. It does not replace the current Stage 6 input pin.

The supplied gate-check result reports `current`, `ok: true`, and `human_approval_granted: false`. No new check or approval is claimed here. Historical draft-status wording in approved upstream artifacts remains unchanged.

#### Source and framework retention

The governing template is:

`settings/templates/pipeline/api-contract-spec.md`

SHA-256: `c6eb797f8acb57cf943662d8ba4bb694f584ad84542d0c634799798587f09e7a`.

The source package is:

`<REDACTED_LOCAL_PATH>/casos/aws-carddemo-preparation/evidence/research-package.json`

SHA-256: `63ba5c47ecb21349549744b912af3b150654e7e435724dba499e3c88369f15a2`.

The complete supplied `input_pins` register is incorporated by reference without changing any path or digest. This includes every original-file pin, all 19 derived-representation pins, framework pins, authorizations, and review attachments. The exact supplied request, source `content`, and stable `numbered_lines` must accompany retention of this document; this specification is not a replacement source package.

Source anchors resolve through approved Stage 3 `E-n` entries to full corpus-relative paths and original-file hashes. Derived numbered-representation hashes remain separate. No checksum computation, filesystem inspection, or new mechanical verification was performed.

### 1.2 Inherited Model Constraints

The following Stage 5 decisions remain binding:

| Decision | Contract inheritance |
|---|---|
| D-2 | Track-qualified types; no common transaction lifecycle or shared live resource identity |
| D-3 | Internal account, category, disclosure, and lookup resources do not become consumer-controlled state APIs |
| D-4 | No atomicity, rollback, durable partial-state, complete diagnosis, or repeat-safety guarantee |
| D-5 | No invented units, rounding, calendar validity, global identity, or certified numeric domain |
| D-6 | No repaired interest flush, reporting final account total, ordinary skip-and-continue filtering, or reconciled totals |
| D-7 | Report presentation and operational context remain bounded; no API pagination derived from line counting |
| D-8 | No new business meaning for filler, declaration-only fields, or the fee placeholder |

## Section 2: API Operation Surface

### 2.1 Operation Inventory

| Clause | Track | Draft operation | Canonical boundary | Completion status |
|---|---|---|---|---|
| C-1 | posting | `POST /posting` | Stage 5 §4.1: candidate sequence, transaction/rejection content, conditional progress | Request participation and response availability remain blocked by G-21–G-23 |
| C-2 | interest | `POST /interest` | Stage 5 §4.2: category basis, identifier basis, generated transaction content | Request participation, numeric domain, and response availability remain blocked by G-21–G-23 |
| C-3 | reporting | `POST /reporting` | Stage 5 §4.3: reporting transaction/date basis, detail/header/total content | Input/date participation and response finalization remain blocked by G-21–G-24 |

These are three separate operations under the unchanged capability identity. They do not establish a required invocation sequence or a unified “run cycle” operation.

### 2.2 Method and Route Structure

#### D-9 — Separate POST operation names

**Choice:** Use the three method/route pairs in §2.1, with OpenAPI operation identifiers `posting`, `interest`, and `reporting` and matching track tags.

**Basis:** Stage 5 D-2, §4.1–§4.3; R-1, R-7, R-12, R-19, R-20.

**Rationale:** POST expresses requested processing without suggesting resource replacement, safe retrieval, or idempotency. The literal route names are representation choices; they do not identify jobs, storage resources, or globally unique operation instances.

**Limits:** No job identifier, status-resource route, polling, asynchronous acceptance promise, or completion deadline is introduced. Request granularity and completion semantics are not settled by choosing POST.

#### D-10 — OpenAPI 3.1 component representation

**Choice:** Describe public content using OpenAPI 3.1 object schemas and explicitly named properties. Preserve the 17 Stage 5 type identities in the disposition register, including types excluded from the public schema surface.

**Basis:** Stage 5 D-2, D-3, D-5, D-7, D-8; types in §3 and mappings in §4.

**Limits:** A component definition is not itself an operation input permission or a promise that its content will be observable. Unresolved requiredness, collection completion, and validation behavior are recorded as gaps, not silently treated as optional fields.

#### D-11 — Textual values without stronger business domains

**Choice:** Represent references, classification codes, temporal text, descriptive values, and report presentation values as JSON strings. Represent signed quantities as decimal text rather than binary floating-point JSON numbers. Represent progress counts as integers without claiming a newly certified counter range.

**Basis:** Stage 5 D-5; R-2, R-3, R-5, R-10, R-11, R-12, R-14, R-16.

**Limits:** Decimal text does not choose calculation precision, rounding, units, input scale, or overflow behavior. No pattern, date/date-time format, length bound, trimming, padding, coercion, or normalization policy is selected merely from a source declaration. G-22 records the remaining input-domain problem.

#### D-12 — Outcome content is not branch telemetry

**Choice:** Public schema content is limited to canonical input/output meanings. `PostingAttemptState`, `InterestAttemptState`, and `ReportingAttemptState` remain descriptive/internal treatments, not returned event streams or required response discriminators.

**Basis:** Stage 5 D-3, D-4, outcome-model preamble, §6; R-4–R-18.

**Limits:** No optional “debug” field is used to evade this restriction. Any later proposed branch observation needs explicit authority.

#### D-13 — Separate domain rejection from technical failure

**Choice:** Preliminary posting rejection remains domain content. Technical failures remain distinct categories, with status/body mappings withheld where they would require an unsupported observation or completion guarantee.

**Basis:** Stage 5 D-4, §5; R-1, R-5, R-6, R-9, R-13, R-18.

**Limits:** Source reasons and file statuses are not HTTP statuses. No universal error-response guarantee follows from a `CEE3ABD` call site.

All five decisions are Stage 6 draft representation decisions, not human approvals. Their applicability is limited to this public run.

### 2.3 Scope Constraint

**C-4 — Excluded surface.** No account/category/disclosure/xref CRUD, state snapshots, reset, rollback, compensation, retry, idempotency-key, backup, combination, job scheduling, fee computation, or API pagination operation is defined.

This exclusion follows Stage 5 D-3, D-4, D-7, D-8 and R-4–R-11, R-16, R-19, R-20. It is not a claim that those resources or activities are absent from the application.

Authentication and authorization policy are **unspecified**, not “none required.” No security scheme or anonymous-access guarantee is selected.

## Section 3: Shared Type Schemas

“Shared” denotes a schema register, not shared business identity. Public schema components below use the exact canonical type names.

Every property listed in a row independently inherits that row’s Stage 5 field mapping and R-n references. No unlisted business property is introduced.

### 3.1 Posting Schemas

| Component | Properties and representation | Stage 5 field/type source | Rules |
|---|---|---|---|
| `PostingCandidate` | Strings: `transactionId`, `typeCode`, `categoryCode`, `source`, `description`, `merchantId`, `merchantName`, `merchantCity`, `merchantPostalText`, `cardReference`, `originalTimestamp`, `suppliedProcessingTimestamp`; decimal-text string: `amount` | §3.1; §4.1 candidate identity/classification, descriptive/merchant, amount/card, temporal context | R-1–R-3 |
| `PostingTransaction` | Strings: `transactionId`, `typeCode`, `categoryCode`, `source`, `description`, `merchantId`, `merchantName`, `merchantCity`, `merchantPostalText`, `cardReference`, `originalTimestamp`, `processingTimestamp`; decimal-text string: `amount` | §3.1; §4.1 prepared posting transaction | R-3, R-6 |
| `PostingRejection` | `candidate`: reference to `PostingCandidate`; `reason`: string; `description`: string | §3.1; §4.1 preliminary rejection; §5.1 | R-1–R-3 |
| `PostingProgress` | `processedRecordCount`, `preliminaryRejectCount`: integers | §3.1; §4.1 progress counts; §6.2 processing control/counts | R-1, R-6 |

**C-5 — Posting value distinctions.**

- `PostingTransaction.processingTimestamp` denotes the newly constructed value, not `PostingCandidate.suppliedProcessingTimestamp`.
- Rejection preserves the original candidate’s canonical context; this is not a byte-for-byte full-record echo guarantee.
- `PostingRejection.reason` denotes the selected source reason, not all failed checks.
- The represented preliminary reason values are `"100"`, `"101"`, `"102"`, and `"103"`. D-11 chooses textual numeric reason labels; no source-padding guarantee follows.
- Reason 109 is not a preliminary rejection variant.
- No `postedCount` is derived from the two progress counts.
- Content construction or count reporting does not certify a durable write.

Traceability: Stage 5 D-4–D-6, D-8; §4.1 and §5.1; R-1–R-6.

### 3.2 Interest Schemas

| Component | Properties and representation | Stage 5 field/type source | Rules |
|---|---|---|---|
| `InterestCategoryBasis` | Strings: `accountReference`, `typeCode`, `categoryCode`; decimal-text string: `categoryBalance` | §3.2; §4.2 encountered category basis | R-7, R-10 |
| `InterestIdentifierBasis` | `parameterText`: string | §3.2; §4.2 identifier parameter | R-11 |
| `GeneratedInterestTransaction` | Strings: `transactionId`, `typeCode`, `categoryCode`, `source`, `description`, `cardReference`, `merchantId`, `merchantName`, `merchantCity`, `merchantPostalText`, `originalTimestamp`, `processingTimestamp`; decimal-text string: `amount` | §3.2; §4.2 generated identifier/classification and descriptive/card/merchant/time values | R-10, R-11 |

**C-6 — Interest value distinctions.**

- `parameterText` is identifier-construction text, not a validated date or reporting range.
- The local suffix is not consumer-supplied and is not a public sequence guarantee.
- Generated classification/source fields retain the source assignments documented in Stage 5; no wire padding or category-code normalization is silently inferred.
- Zero/space merchant assignments do not become null or “unknown merchant.”
- Nonzero rate selects computation/write even when balance or result is zero or negative.
- Generated transaction content does not certify account rewriting.
- No fee amount, global uniqueness, or suffix-exhaustion behavior is supplied.

Traceability: Stage 5 D-3–D-6, D-8; §4.2, §5.2; R-7–R-11. The nonzero-rate guard resolves through R-10/E-12 to `app/cbl/CBACT04C.cbl:214-217`, separately from the computation at `app/cbl/CBACT04C.cbl:462-470`, preserving the Stage 5 review’s deferred anchor note.

### 3.3 Reporting Schemas

| Component | Properties and representation | Stage 5 field/type source | Rules |
|---|---|---|---|
| `ReportingTransactionBasis` | Strings: `transactionId`, `cardReference`, `typeCode`, `categoryCode`, `source`, `processingTimestamp`; decimal-text string: `amount` | §3.3; §4.3 transaction basis | R-12, R-13, R-16 |
| `ReportingDateBasis` | `startText`, `endText`: strings | §3.3; §4.3 reporting start/end values | R-12, R-16 |
| `ReportDetail` | Strings: `transactionId`, `accountReference`, `typeCode`, `typeDescription`, `categoryCode`, `categoryDescription`, `source`, `amountText` | §3.3; §4.3 detail output, xref association, report-description receivers | R-13, R-16 |
| `ReportHeaderContext` | `reportIdentityText`, `startText`, `endText`: strings | §3.3; §4.3 header context | R-12, R-16 |
| `ReportTotal` | `label`: string enum `page`, `account`, `grand`; `valueText`: string | §3.3; §4.3 distinct totals | R-13–R-16 |

**C-7 — Reporting representation.** `amountText` and `valueText` represent source-bounded report presentation values, not newly reconstructed unlimited-precision amounts. D-11 retains these as strings to avoid inventing numerical recovery from edited output.

`ReportTotal.label` is D-10’s representation of the three Stage 5 total variants. It does not add account identity, page number, report identity, or grouping cardinality to a total.

**C-8 — Reporting content limits.**

- Detail descriptions denote report receivers, not lossless full lookup descriptions.
- Header dates do not certify that every transaction in the range was processed.
- Account-labelled totals remain card-change-triggered.
- Page-labelled totals do not imply API pages or twenty detail records.
- No final account total, reconciled total, unconditional repeated EOF contribution, or complete-range result is promised.

Traceability: Stage 5 D-5–D-7; §4.3, §5.3; R-12–R-17.

### 3.4 Canonical Types Not Published as Payload Schemas

| Canonical type | Complete element disposition | Stage 5 source / rules |
|---|---|---|
| `PostingAttemptState` | Preliminary selection, ordered category/account/transaction attempts, and local failures remain internal/descriptive; no public state enum or event record | §3.1, §5.1, §6.2; D-3/D-4; R-4–R-6, R-18 |
| `InterestDisclosureBasis` | Account group, type, category, selected rate, and fallback distinction remain internal dependency data; no caller-provided rate or public rate lookup | §3.2, §4.2, §6.3; D-3; R-9/R-10 |
| `InterestAttemptState` | Disclosure selection, bypass/computation, transition update, and normal EOF distinctions remain internal/descriptive | §3.2, §5.2; D-3/D-6; R-7–R-11, R-18 |
| `UpstreamReportSelectionBasis` | Documentary bounds and card-ordering context remain external; no request override or result attestation | §3.3, §4.3, §6.4; D-7; R-17/R-19 |
| `ReportingAttemptState` | Date path/exit, EOF finalization, and lookup/write failure distinctions remain internal/descriptive | §3.3, §5.3; D-3/D-6; R-12–R-18 |

This accounts for all 17 Stage 5 types without converting internal types into consumer-visible telemetry.

### 3.5 Schema Constraints and OpenAPI Translation

**C-9 — Representation is not validation policy.**

The component tables translate to OpenAPI `components.schemas` using `type`, `properties`, `$ref`, and the explicitly listed representation enum. Descriptions shall carry C-5–C-8 and the relevant gaps.

The following are deliberately unresolved for operation requests:

- Required properties and conditional presence.
- Missing versus null handling.
- Accepted lexical forms and value ranges.
- Length handling, padding, trimming, normalization, and coercion.
- Unknown-property behavior.
- Collection size, empty-input participation, and end-of-input representation.

No omission of an OpenAPI keyword may be presented as a decision to accept every corresponding input. Until G-21/G-22 are addressed, these are component-shape drafts rather than complete request validators.

## Section 4: Operation API Contracts

### 4.1 POST /posting — Posting

**Request:** C-1 uses `PostingCandidate` as its candidate content component. The source boundary concerns a candidate sequence. Whether the HTTP request supplies that sequence, selects an externally supplied sequence, or has another explicitly authorized participation model remains G-21. No invented dataset identifier or singleton-per-request semantics is selected.

**Responses:** Permitted content components are `PostingTransaction`, `PostingRejection`, and `PostingProgress`. The response envelope, occurrence cardinality, availability, and HTTP status trigger remain G-23.

**Validation:** G-22. Preliminary legacy rejection must not be described as a newly implemented API validation layer.

**Outcome mapping:**

| Stage 5 §5.1 distinction | Contract destination |
|---|---|
| Preliminary posting selected | C-5 non-guarantee; internal selection, not a durable-success response |
| Preliminary rejection selected | `PostingRejection`; delivery trigger remains G-23 |
| Card lookup rejection, 100 | Selected rejection content; no unguarded account-check promise |
| Account lookup rejection, 101 | Selected rejection content, distinct from account rewrite |
| Comparison rejection, 102/103 | Selected reason only; later 103 replaces 102 under R-2 |
| Account rewrite reason 109 | Internal/descriptive under D-12; never automatically `PostingRejection` |
| Local write/open/close failure | C-12 technical-failure distinction; G-23 |
| Completion information reached | `PostingProgress` content; not guaranteed live progress or committed counts |

**C-10 — Posting effects.** Preliminary acceptance does not promise all posting effects succeed. Category operation, account rewrite, and transaction write are ordered attempts; neither an error response nor rejection content establishes rollback or unchanged balances.

**Traceability:** Stage 5 §3.1, §4.1, §5.1, §6.2; D-2–D-6, D-8; R-1–R-6, R-18, R-20; Stage 6 D-9–D-13.

### 4.2 POST /interest — Interest Transaction Generation

**Request:** Candidate content components are `InterestCategoryBasis` and `InterestIdentifierBasis`. Account, xref, disclosure, and suffix state are not request fields. Sequence participation remains G-21; accepted value domain remains G-22.

**Responses:** `GeneratedInterestTransaction` is the permitted output-content component. No generated-count, account snapshot, fee result, or branch-event list is introduced. Response delivery and status remain G-23.

**Validation:** No positive-balance guard, positive-result guard, rate-unit interpretation, date validation, or default rate is added.

| Stage 5 §5.2 distinction | Contract destination |
|---|---|
| Selected disclosure available | Internal dependency distinction; not public lookup data |
| Zero-rate bypass | C-6; no rejection or fabricated zero-valued transaction |
| Computation/write selected | Generated transaction content, subject to G-23 |
| Previous-group account update selected | Internal effect; no update receipt |
| Normal EOF without final update | C-11 explicit missing-finalization constraint |
| Dependency or write failure | C-12; G-23; no posting-style reject record |

**C-11 — Interest finalization.** Under the approved normal pre-test EOF deduction, no final-account flush is inserted. A returned generated transaction, if made available under a completed contract, must not imply that the corresponding final account was rewritten.

**Traceability:** Stage 5 §3.2, §4.2, §5.2, §6.3; D-2–D-6, D-8; R-7–R-11, R-18, R-20; Stage 6 D-9–D-13.

### 4.3 POST /reporting — Transaction Reporting

**Request:** Candidate content components are `ReportingTransactionBasis` and `ReportingDateBasis`. G-21 retains the unresolved input-participation model, including the distinction between a date value and date-input EOF. The upstream SORT basis is not a caller override.

**Responses:** Permitted content components are `ReportDetail`, `ReportHeaderContext`, and `ReportTotal`. No mandatory header, final total, complete report collection, or empty-report success response is selected. Response assembly/availability remains G-23/G-24.

**Validation:** No calendar validity, start-before-end requirement, common date authority, or conventional filter policy is introduced.

| Stage 5 §5.3 distinction | Contract destination |
|---|---|
| Date-permitted detail path | Report content components; conditional participation |
| Date-alternative exit | C-8; leaves loop sentence, not skip-and-continue |
| Date-input EOF | G-21/G-24; no substitute range or empty-complete-report meaning |
| Conditional EOF finalization | C-8 and G-24; page/grand calls, no final account-total call |
| Card-transition total attempt | C-8/C-12; earlier total attempt may precede failing lookup |
| Lookup or output failure | C-12/G-23; no empty or unchanged-output guarantee |

**Traceability:** Stage 5 §3.3, §4.3, §5.3, §6.4; D-2–D-7; R-12–R-18, R-20; Stage 6 D-9–D-13.

## Section 5: Error Handling Strategy

### 5.1 Response Categories

**C-12 — Category separation.** Domain rejection, request-representation rejection, unavailable dependency, local I/O failure, external failure-call consequences, timeout, and unknown durable effects shall not be collapsed into one business-rejection meaning.

Only the distinctions licensed by Stage 5 are retained. A category’s presence in this register does not guarantee it can be detected or returned.

### 5.2 Category Table

| Category | Condition | HTTP status | Body shape | Upstream source |
|---|---|---|---|---|
| Preliminary posting rejection | Selected nonzero preliminary reason | Unassigned pending G-23 | `PostingRejection` content | Stage 5 §5.1; R-1–R-3 |
| Representable output content | Licensed output becomes available under a defined response boundary | Unassigned pending G-23 | Components in §3 | Stage 5 §4–§5; R-3, R-6, R-11, R-14, R-16 |
| Request-representation rejection | Request falls outside a subsequently established schema policy | Unassigned pending G-22 | Not defined | D-5 and Stage 5 G-17; no new business rule |
| Dependency/local I/O failure | Relevant source failure path | Unassigned pending G-23 | No public diagnostic schema licensed | Stage 5 §5; R-6, R-7, R-9, R-11, R-13, R-18 |
| External failure-call consequence | Behavior following external call | Unsupported guarantee; G-23 | Not defined | Stage 5 §6.5; R-18/A-17 |
| Timeout/process termination | No approved observation or handling contract | Unsupported | Not defined | Stage 5 D-4; R-18 |
| Partial durable effects | Actual persistence unknown | Not a separately reportable status | No state snapshot | Stage 5 D-4; R-6/R-18 |
| Repeat outcome | Repetition safety unknown | No retry-specific status | No idempotency receipt | Stage 5 D-4; R-20 |

### 5.3 Rationale for Non-Obvious Status Decisions

D-13 does not prohibit ordinary HTTP representation choices. It withholds them here because the response-trigger obligations remain unspecified:

- A `201` receipt must not imply durable transaction creation.
- A `202` response would require an acceptance/lifecycle meaning not supplied by Stage 5.
- A `200` response must not silently imply complete processing or complete output.
- Source reason 100 or file status 23 does not mean HTTP 100 or HTTP 423.
- A `500` or `503` guarantee for every external failure path would require an unsupported detection/return obligation.
- Empty collections cannot stand for unknown, unavailable, failed, or unemitted output.

Once an authorized response boundary exists, status numbers may be chosen as traceable representation decisions without inventing durable business success. G-23 does not assert that HTTP representation itself is impossible.

### 5.4 State and Recovery Contract

**C-13 — Common state terms.** For every row below, resource lifetime, persistent initialization, reset, isolation, restart effects, and durable failure consequences remain unknown unless the row records a narrower source-local fact. “External” means outside the public API contract, not an available external facility.

**C-14 — Repetition.** Repetition safety is unknown separately for posting, interest, and reporting. This contract supplies no automatic retry, reset, compensation, rollback, or idempotency mechanism. Unknown safety is not a universal assertion that every repetition is harmful.

| State requirement / resource | Stage 5 source | Contract clause or external/unsupported | Consumer consequence |
|---|---|---|---|
| Posting daily candidate sequence | §6.2; R-1/R-3 | C-1; G-21 | Content type exists; sequence participation unresolved |
| Posting card association | §6.2; R-2 | External/internal; C-4 | No xref provisioning or inspection |
| Posting account state | §6.2; R-2/R-5 | External/internal; C-10/C-13 | No balance snapshot or durable update receipt |
| Posting category balance | §6.2; R-4/R-6 | External/internal; C-10 | Source-local creation distinction is not a creation API |
| Posting transaction output | §6.2; R-3/R-6 | C-5; G-23 | Prepared content is not a durable receipt |
| Posting reject output | §6.2; R-1/R-3/R-6 | C-5; G-23 | Reject counting does not establish persisted output |
| Posting control and counts | §6.2; R-1/R-4–R-6 | Flags internal; progress content only | No live progress or restart token |
| Interest category sequence | §6.3; R-7/R-10 | C-2; G-21 | No global grouping assertion |
| Interest account state | §6.3; R-7/R-8 | External/internal; C-11 | Source cycle resets are not public resets; no final flush |
| Interest account-key xref | §6.3; R-7/R-11 | External/internal | No cardinality or card-selection policy |
| Interest disclosure state | §6.3; R-9/R-10 | External/internal | Missing disclosure is not zero rate |
| Interest identifier parameter | §6.3; R-11 | `InterestIdentifierBasis`; G-21/G-22 | No calendar or lifetime guarantee |
| Interest group accumulation/control | §6.3; R-7/R-8/R-10 | Internal; D-12 | Local initialization/reset is not consumer control |
| Interest suffix | §6.3; R-11/R-20 | Internal; C-6/C-14 | No global uniqueness or exhaustion policy |
| Interest transaction output | §6.3; R-8/R-11/R-20 | C-6; G-23 | Independent of account rewrite |
| Reporting transaction sequence | §6.4; R-12/R-15/R-17 | C-3; G-21 | No actual order or EOF-buffer guarantee |
| Reporting date input | §6.4; R-12/R-16/R-17 | Date component; G-21/G-24 | No default range or EOF substitution |
| Upstream selection result | §6.4; R-17/R-19 | External documentary context | No override or executed-flow attestation |
| Reporting card association | §6.4; R-13/R-18 | External/internal; C-8/C-12 | Previous total attempt can precede lookup failure |
| Reporting type descriptions | §6.4; R-13/R-16 | Internal lookup; detail receiver public content | Full description is not promised |
| Reporting category descriptions | §6.4; R-13/R-16 | Internal lookup; detail receiver public content | Full description is not promised |
| Page accumulation | §6.4; R-14/R-15 | Internal; conditional `ReportTotal` | No accumulator observation |
| Account accumulation | §6.4; R-13–R-15 | Internal; conditional `ReportTotal` | No mandatory EOF account total |
| Grand accumulation | §6.4; R-14/R-15 | Internal; conditional `ReportTotal` | No independent reconciliation |
| Reporting control/presentation | §6.4; R-16 | Internal; C-4/C-8 | No page-size control or twenty-detail guarantee |
| Report output | §6.4; R-13–R-16/R-18/R-20 | Report components; G-23/G-24 | Failure does not imply no earlier output |
| Transaction backup | §6.5; R-19/R-20 | External; C-4/C-13 | No completed backup or reset facility |
| Combined intermediate | §6.5; R-19/R-20 | External; posting/interest only | No completed merged-state guarantee |
| Master lifecycle context | §6.5; R-19/R-20 | External | No shared live instance or restored-state guarantee |
| Procedure control dependency | §6.5; R-19 | External/unavailable | Missing `REPROCT` remains unresolved |
| External failure routine | §6.5; R-18 | External/unavailable; G-23 | No termination, return, or rollback promise |

## Section 6: Traceability Matrix

Schema property mappings in §3 and state mappings in §5.4 form part of this matrix.

| Contract element | Canonical element / treatment | Rule | Decision |
|---|---|---|---|
| C-1, `POST /posting` | Stage 5 §4.1 posting boundary | R-1–R-6 | D-2, D-9 |
| C-2, `POST /interest` | Stage 5 §4.2 interest boundary | R-7–R-11 | D-2, D-9 |
| C-3, `POST /reporting` | Stage 5 §4.3 reporting boundary | R-12–R-17 | D-2, D-9 |
| C-4 excluded state/control surface | Stage 5 §6 internal resources and operational context | R-4–R-11, R-16, R-19/R-20 | D-3/D-4/D-7/D-8 |
| C-5 posting content | Candidate, prepared transaction, rejection, progress | R-1–R-6 | D-4–D-6/D-8/D-10/D-11 |
| C-6 interest content | Identifier basis, generated transaction, internal suffix/disclosure | R-7–R-11 | D-3–D-6/D-8/D-10/D-11 |
| C-7/C-8 report content | Detail/header/total and separate date basis | R-12–R-17 | D-5–D-7/D-10/D-11 |
| C-9 schema-policy boundary | Source widths are provenance, not accepted domain | R-2/R-3/R-5/R-10–R-12/R-16/R-17 | D-5/D-10/D-11 |
| D-12 internal outcome exclusion | All three AttemptState types; Stage 5 outcome preamble | R-4–R-18 | D-3/D-4/D-6/D-12 |
| C-10 posting effects | Ordered attempts and reason-109 distinction | R-4–R-6 | D-4/D-6 |
| C-11 missing interest flush | Normal EOF distinction | R-8 | D-6 |
| C-12 categories | Stage 5 §5 local failures versus rejection | R-1/R-5/R-6/R-9/R-13/R-18 | D-4/D-13 |
| C-13 state terms | Every Stage 5 §6 resource | R-6/R-18/R-19 | D-2–D-4 |
| C-14 repetition | Per-track unknown repetition safety | R-20 | D-4 |
| G-21–G-24 | Stage 5 conditional participation and unresolved guarantees | See gap register | D-3–D-7; no semantic closure |

No new E-n or R-n is created. Source evidence remains subordinate to the approved semantic and canonical interpretations rather than directly generating additional API operations.

## Section 7: Reverse-Completeness Matrix — Contract Destination

| Operation / rule / effect | Evidence | Semantic representation | Stage 5 boundary treatment | Contract destination / justified exclusion / gap |
|---|---|---|---|---|
| Posting selection | E-4/E-7 | R-1 | Candidate, rejection, progress; flags internal | C-1/C-5; selection telemetry excluded by D-12; G-21/G-23 |
| Lookup and comparison precedence | E-7/E-8/E-20/E-21/E-27 | R-2 | Selected reason; internal checks; policy limits | C-5 rejection reason; 103 precedence retained; G-22 |
| Transaction versus rejection content | E-4/E-9/E-26/E-27 | R-3 | Distinct types; filler excluded | §3.1/C-5; no full-byte echo guarantee; G-23 |
| Category accumulation | E-9/E-10/E-22 | R-4 | Internal state and attempt distinction | C-10/§5.4; no category API or branch telemetry |
| Account arithmetic and 109 | E-7/E-9/E-10/E-20 | R-5 | Internal state; distinct later reason | C-5/C-10; signed addition retained; no automatic rejection variant |
| Posting completion/failure | E-7/E-9–E-11/E-29 | R-6 | Counts and ordered attempts; durable effects unknown | C-5/C-10/C-12/C-13; G-23 |
| Interest account transitions | E-5/E-12/E-13/E-20–E-22 | R-7 | Category basis; internal grouping/state | C-2/C-6/§5.4; G-21 |
| Interest normal EOF | E-12/E-14 | R-8 | Missing-final-update distinction; repair excluded | C-11; no flush field or completion receipt |
| Disclosure fallback | E-12/E-13/E-23 | R-9 | Internal dependency and selection distinction | §3.4/C-6/C-12; no caller rate or zero substitution |
| Interest selector and quantity | E-5/E-12/E-14/E-22/E-23 | R-10 | Generated amount; internal accumulator; numeric gap | C-6/C-9; G-22; no positivity restriction |
| Generated transaction and fees | E-5/E-14/E-26/E-30 | R-11 | Identifier/transaction; suffix internal; fee excluded | §3.2/C-6; G-22/G-23; no fee or uniqueness claim |
| Report date gate and exit | E-6/E-16/E-26 | R-12 | Date basis; EOF control internal; storage unknown | C-3/C-8; G-21/G-24; no skip-and-continue |
| Report grouping/lookups | E-6/E-16/E-18/E-21/E-24/E-25 | R-13 | Detail association; internal card grouping | §3.3/C-8/§5.4; no account-card cardinality |
| Report accumulator sites | E-6/E-16–E-18/E-28 | R-14 | Distinct totals; accumulators internal | `ReportTotal`, C-7/C-8; no reconciled aggregate |
| Report EOF finalization | E-16/E-17 | R-15 | Conditional outcome; missing final account total | C-8; G-24; no unconditional numerical duplication |
| Presentation and line counting | E-6/E-17/E-18/E-24–E-26/E-28 | R-16 | Detail/header; internal presentation mechanics | §3.3/C-7/C-8; pagination/control excluded |
| Two date selection sites | E-16/E-31/E-34 | R-17 | Separate documentary upstream basis; configuration gap | §3.4/C-3; G-24; no common override or simple complete intersection |
| Error sites and external routine | E-11/E-15/E-19 | R-18 | Internal diagnostics; external consequences unknown | C-12/§5.2/§5.4; G-23; diagnostic mismatches not repaired |
| Operational resource context | E-29–E-34 | R-19 | External context; identity/schedule unestablished | C-4/§5.4; no cycle, backup, or combination endpoint |
| Repetition | E-5/E-9–E-12/E-14–E-19/E-32–E-34 | R-20 | Unknown per track; explicit non-guarantee | C-14 for posting, interest, reporting separately |

### 7.1 Remaining Evidence and Exclusions

Stage 5 §7.2’s evidence accounting remains inherited:

- E-1–E-3 supply track orientation, not additional operations.
- Declaration-only account fields, xref customer identity, and filler remain excluded under D-8; no customer or unrelated account-management schema is added.
- E-28 presentation separators and spacing remain provenance, not independently supplied business values.
- E-32 concerns posting/interest combination context; E-33/E-34 retain their explicitly shared consumers.
- E-35 remains non-semantic licensing context under A-6. No business R-n or legal-clearance contract is fabricated.

### 7.2 Ambiguity Propagation

A-1–A-17 retain their Stage 5 statuses. This document closes none of them.

| Inherited ambiguity | Stage 6 consequence |
|---|---|
| A-1/A-8 | D-9 and C-4 avoid merged capability, resource identity, and schedule claims |
| A-2/A-16 | Missing dependencies remain external; no executable-cycle assertion |
| A-3 | No deployed text-conversion policy; relevant to G-22 |
| A-4/A-10/A-17 | C-10/C-12/C-13; response guarantees constrained by G-23 |
| A-5/A-6 | No independent-extraction or legal-clearance claim |
| A-7 | Addressed upstream for evidence layout; identity unchanged |
| A-9 | Selected-reason precedence and reason-109 timing remain distinct |
| A-11 | C-11 retains the bounded normal-EOF deduction |
| A-12 | C-6/C-9 and G-22 retain numeric, parameter, and identifier limits |
| A-13 | Fee computation excluded, without application-wide absence claim |
| A-14/A-15 | C-7/C-8 and G-24 retain date, EOF, grouping, and total uncertainty |

### 7.3 Explicit Blocking Contract Gaps

Gap numbering continues after Stage 5 G-20. These blockers concern concrete contract obligations that cannot presently be completed without invention; ordinary naming or method choices are not treated as blockers.

| ID | Blocking scope | Unsupported decision that is not made | Required upstream clarification or authorized decision |
|---|---|---|---|
| G-21 | Request participation for C-1–C-3 | Treat a canonical sequence or date resource as a request array, external selector, singleton call, empty input, or EOF signal without defining its semantic relationship | Specify consumer-supplied versus externally supplied inputs, request granularity, and representation of absence/end-of-input while retaining Stage 5 §4/§6 and R-1/R-7/R-8/R-12/R-15 |
| G-22 | Complete request schemas and validation | Infer accepted domains, requiredness, null policy, numeric scale/range, text conversion, date validity, or rejection behavior from field declarations alone | Establish traceable representation-domain and validation decisions consistent with D-5 and Stage 5 G-17; do not invent business checks |
| G-23 | Response envelopes, occurrence guarantees, and HTTP triggers | Promise branch telemetry, delivery of every output attempt, guaranteed external-failure detection/return, or complete/durable success | Define the consumer-visible response boundary and available output meanings consistent with D-3/D-4, Stage 5 §5/§6, R-3/R-6/R-11/R-14/R-16/R-18 |
| G-24 | Concrete reporting result/finalization obligations | Substitute empty or complete output for date-input EOF, unknown post-read storage, early exit, or unresolved job flow | Delimit reporting response completeness without repairing R-12–R-17; retain Stage 5 G-19 and D-6/D-7 |

G-21–G-24 do not authorize runtime investigation, source repairs, or later-stage work. Human clarification may retain an exclusion or narrow the contract rather than resolve every environmental uncertainty.

Inherited G-17–G-19 remain blockers for stronger claims, not blanket reasons to withhold representable content schemas. Historical review/persistence gaps are not silently reopened or rewritten; this Stage 6 artifact simply has no new approval or persisted output digest.

## Completeness Gate and Stage 7 Entry Condition

All conditions remain unchecked:

- [ ] All canonical operations have complete contracts; no extra surface without D-n.
- [ ] All canonical types are represented or have justified internal/external dispositions.
- [ ] Every schema field has Stage 5 type/field and R-n traceability.
- [ ] Request participation, requiredness, and validation policy are settled without invention.
- [ ] Outcome-variant mappings preserve Stage 5 guards and observability limits.
- [ ] Response categories, status triggers, and body shapes are complete where promised.
- [ ] Every Stage 5 state/reset requirement maps to a clause or an explicit external/unsupported treatment.
- [ ] Failure effects and repetition constraints are derived, not invented.
- [ ] All R-1–R-20 have a contract destination, justified exclusion, external/unsupported status, or gap.
- [ ] Decision-bearing mappings are reviewed against the exact pinned upstream versions.
- [ ] Risk-oriented review records rule reading, bounded absence, failure after earlier effects, and omitted-finalization obligations.
- [ ] Each review sample records passage, objection, conclusion, and resulting clause/exclusion/gap disposition.
- [ ] Review explicitly states that sampling does not establish completeness.
- [ ] G-21–G-24 have been resolved or handled through authorized, explicit contract-scope decisions.
- [ ] The exact Stage 6 artifact and review records are retained and pinned.
- [ ] Human review outcome is recorded externally.

### Provenance and Current Status

AI assistance was limited to drafting this Stage 6 contract from the supplied approved artifacts, both Stage 5 review attachments, exact source text and numbered representations, and generic template/rules. Upstream review findings are inherited review evidence, not checks newly performed here.

No tools, additional model/network calls, COBOL execution, source repairs, implementation, or generated code were used. Provider transport settings, storage configuration such as `store=false`, token usage, and monetary cost are not certified by this document.

**Current Stage 6 status: draft with blocking contract gaps. No gate is approved. Completeness gate remains not passed. Ready for implementation remains `false`.**

The template’s next-stage entry condition requires a passed gate recorded against the exact artifact in `spec.json`. This document neither satisfies nor authorizes that transition.
# API Contract Specification

## Purpose

This Stage 6 revision proposes a concrete, OpenAPI-representable API contract for the AWS CardDemo public cycle, derived from the approved Stage 5 canonical data boundary.

**Posting, interest, and reporting are mandatory, separately traceable tracks.** The proposed HTTP surface does not combine them into a business capability, establish a cycle schedule, or certify runtime outcomes.

| Attribute | Value |
|---|---|
| Run | `E3-01` |
| Stage | `6` |
| Feature | `api-contract-carddemo-r2` |
| Artifact path relative to `RUN_ROOT` | `specs/api-contract-carddemo-r2/requirements.md` |
| Exact inherited capability identity | `unselected-stage-1-scope-only` |
| Revision of | `api-contract-carddemo` |
| Status | `draft/proposed-interface` |
| Human approval granted | `false` |
| Completeness gate passed | `false` |
| Ready for implementation | `false` |

This revision replaces broad withholding of request/schema/status choices with explicit proposals for human review. It does not approve those choices as binding runtime guarantees.

The document supplies requirements text only. It does not persist files, modify metadata, implement an API, specify realization behavior, execute COBOL, or approve any gate.

## Contract Integrity Discipline

- Every contract element derives from a canonical element or a recorded design decision (`D-n`); nothing enters the surface from implementation convenience.
- Outcome-variant mappings follow the Stage 5 mapping notes.
- Error strategy decisions are recorded, justified, and traceable.
- EARS phrasing is used only where it clarifies grounded conditional obligations.
- The contract is representable in OpenAPI 3.1.
- Source-grounded meaning, proposed transport shape, and unresolved runtime authority remain distinct.
- Internal canonical state is not guaranteed public observability.
- Missing disclosure is not zero rate; missing output is not empty success; missing totals are not zero.
- `not_attested` expresses lack of attestation, not confirmed incompleteness.
- No uncertainty label excuses omission of available, licensed output content.
- No source repair, business-rule reimplementation, or later-stage material is included.

Throughout this document:

- **S — source-grounded:** meaning inherited from approved Stage 5 and its R-n mapping.
- **P — interface-proposal-needs-gate:** concrete representation choice proposed here, not a COBOL fact.
- **U — not specified/unsupported:** authority is absent; no default guarantee follows.

Normative contract wording below describes the **proposed contract**, subject to external human acceptance.

## Section 1: Upstream Authority and Entry Condition

### 1.1 Upstream Authority and Scope Inheritance

The immediate authority is `specs/canonical-data-boundary-carddemo/requirements.md`, approved within conditional documentary scope. The supplied Stage 5 authorization permits Stage 6 specification for posting, interest, and reporting, preserving unresolved gaps.

| Approved artifact relative to `RUN_ROOT` | SHA-256 |
|---|---|
| `specs/pipeline-scope-carddemo/requirements.md` | `1362fab5d55b77ef6121328606ae974295cd5723849520e9a246f4bd45e64cc9` |
| `specs/capability-selection-carddemo-r2/requirements.md` | `abdb59180f379d9e14eb86dfa1d8226ec50c981346767e808fd382eb7462bbc4` |
| `specs/legacy-evidence-carddemo-r2/requirements.md` | `4566786600b60e9377c1e369e67765098d06b0153ba973361d2065614a6c9b7b` |
| `specs/capability-semantics-carddemo/requirements.md` | `2f9d3ee52dd7788e206810e38c9173b19d21dfc44270cdd06d05e62dec95eb93` |
| `specs/canonical-data-boundary-carddemo/requirements.md` | `208d04fe6f9cae665dfa4cb514de5d4ad9eaf0ebc169dfae0fd8a6ba209e66f3` |

The exact supplied `input_pins` register is incorporated by reference as part of this artifact’s retention basis, without replacing or normalizing any digest. This includes:

- All five current upstream metadata pins and artifact pins.
- All five authorization pins.
- Both Stage 5 review attachments and the Stage 4 counterexample review.
- All 19 original corpus-file pins and their separately identified derived-representation pins.
- The source-package pin and all 13 framework pins.
- Failed original Stage 6 metadata/artifact pins and both revision-feedback pins.

The current Stage 5 metadata pin is `4f6005cba97aa29d3a73e6cc4e36d2b0401fe159bcdfc5f28b0c2447080a10ef`. The review-time pin `8e869738d9fe897f3118b5495775ec091f909d79d6a9aeddd36e2baadbbfcc5c` remains historical provenance, not its replacement.

Particularly consequential authorities are:

| Authority | SHA-256 |
|---|---|
| `reviews/stage-5-authorization.json` | `a2f73337b5ec123d62ab41e9c058a3065f1ccf133c48e5b81f54f9a2610bfe23` |
| `STAGE5-COUNTEREXAMPLE-REVIEW.md` | `0dadcd665b1e4cb71765003c22655f7b04a3430bf92077f9d63d33053aa2fdfe` |
| `stage5-counterexample-findings.json` | `caa6418e2ebec9e52a795e1bafd9ca304a21d55a0c28e73e86b06162c33ec84e` |
| `settings/templates/pipeline/api-contract-spec.md`, relative to `FRAMEWORK_ROOT` | `c6eb797f8acb57cf943662d8ba4bb694f584ad84542d0c634799798587f09e7a` |

The source package remains the supplied `research-package.json` at the absolute path in `input_pins.source_package`, SHA-256 `63ba5c47ecb21349549744b912af3b150654e7e435724dba499e3c88369f15a2`.

Exact source `content`, stable 1-based `numbered_lines`, and original bytes remain distinct retained evidence objects. The specification’s tables do not replace them. E-n references resolve through approved Stage 3-r2 to full corpus-relative paths, hashes, and ranges.

The supplied gate check reports `current` and `ok: true`; it grants no new approval. No checksums or filesystem checks were performed here.

#### Revision provenance

| Revision input | SHA-256 |
|---|---|
| `specs/api-contract-carddemo/requirements.md` and its original prepared copy | `753a60a5ee7b1fb6d94f6ab982afe415bc01adca040bb3d89e24ffc60342bba7` |
| `specs/api-contract-carddemo/spec.json` | `fdcae1e4ae948611e11720b1abd60eb1a23107b864ed51785a70e4e028b135b2` |
| `reviews/stage-6-r1-directed-feedback.md` | `87a74e6570babd2e5e811ba1c0a6f0ee2d5cd0bdfbe4bdbb5504e3e9bfe4659c` |
| `STAGE6-REVISION-PLAN.md` | `51ce5a1a13ab107b5c6f0df536c371e3337ad79275da0377021c273598a59c35` |

The original remains unapproved and unchanged. This is a human-directed versioned revision, not independent extraction. Original C-1–C-14 and D-9–D-13 identities are retained with explicitly revised definitions below; additional decisions continue at D-14.

### 1.2 Inherited Model Constraints

| Stage 5 decision | Binding contract consequence |
|---|---|
| D-2 | Separate track-qualified meanings; no shared transaction lifecycle or global identity |
| D-3 | Account/category/xref/disclosure/lookups remain internal dependencies, not consumer-controlled resources |
| D-4 | No atomicity, rollback, durable partial-state, complete diagnosis, or repeat-safety guarantee |
| D-5 | No invented units, rounding, calendar validity, numeric domain, or identifier lifetime |
| D-6 | No repaired interest flush, report final account total, conventional date filtering, or reconciled total |
| D-7 | Presentation and operational context stay bounded; no API pagination derived from report line counting |
| D-8 | No business meaning invented for filler, declaration-only fields, or fee placeholder |

These limits apply to all clauses and schemas, including proposed HTTP success responses.

## Section 2: API Operation Surface

### 2.1 Operation Inventory

| Clause | Method and route | Operation ID / tag | Canonical operation | Proposed granularity |
|---|---|---|---|---|
| C-1 | `POST /posting` | `posting` | Stage 5 §4.1 | One batch-processing request against externally supplied daily input |
| C-2 | `POST /interest` | `interest` | Stage 5 §4.2 | One batch-processing request against externally supplied category input and identifier basis |
| C-3 | `POST /reporting` | `reporting` | Stage 5 §4.3 | One batch-processing request against externally supplied transaction/date inputs |

One HTTP request is not one transaction record, one account group, or an atomic batch. No input cardinality, complete consumption, completion deadline, or cross-track sequence is inferred.

### 2.2 Method and Route Structure

#### D-9 — Separate POST operations, retained

**P:** Retain the three routes and operation identifiers above. POST avoids suggesting safe retrieval or idempotent replacement.

**Basis:** Stage 5 D-2, §4; R-1, R-7, R-12, R-19, R-20.

No resource identifier, polling route, asynchronous lifecycle, or combined cycle operation is introduced.

#### D-10 — OpenAPI 3.1 shape, refined

**P:** Use `application/json`, object components, explicit `required` lists, arrays, and `oneOf` unions. Content components retain canonical type names.

All objects described below are closed shapes: `additionalProperties: false`. All listed properties are required unless explicitly marked optional. Null is not a permitted substitute for an absent object or unknown value. These are proposed transport constraints, not source validation rules.

**Basis:** Stage 5 types and §4 mappings; D-2, D-3, D-5, D-7, D-8.

#### D-11 — Conservative value representation, refined

**P:** References, codes, timestamps, dates, identifiers, descriptions, and report presentation values use JSON strings. Signed quantities use strings representing decimal quantities, without binary floating-point conversion.

No regex, length bound, scale, rounding, currency, date format, trimming, padding, or coercion policy is imposed. Structural string conformance does not certify numeric or calendar validity.

Progress counts use JSON integers, with no newly inferred range or committed-count interpretation.

**Basis:** Stage 5 D-5; R-2, R-3, R-5, R-10–R-12, R-14, R-16.

#### D-12 — Content is not branch telemetry, retained

**S/P:** Public output represents canonical content. All three `AttemptState` types remain internal/descriptive. No branch trace, file status, diagnostic stream, or reason-109 observation field is exposed.

**Basis:** Stage 5 D-3/D-4, §5 preamble, §6; R-4–R-18.

#### D-13 — Concrete response categories, revised

**P:** Select HTTP `200`, `400`, `500`, and `503` as described in Section 5. Their meanings are interface-level response cases, not source status codes or certifications of completed business effects.

**Basis:** Stage 5 D-4, §5 outcomes; R-1, R-6, R-9, R-13, R-18; directed feedback for G-23.

The original’s unassigned HTTP statuses are replaced only in this revision.

#### D-14 — External-input batch participation

**P:** Each operation requires a JSON empty object request: object type, no properties, `additionalProperties: false`. The request body is required. Missing body, null, arrays, and supplied business properties do not match this proposed request shape.

The request asks for the named batch operation against inputs supplied outside this API. It does not assert those inputs exist, identify their resource instance, or provide an EOF signal. No dataset selector, singleton resource assumption, or provisioning facility is implied.

**Basis:** Stage 5 §4 and §6 sequence/parameter authority; D-3; R-1, R-7, R-11, R-12, R-17, R-19.

This choice minimizes invented consumer ownership while preserving batch granularity. It is a consequential interface proposal requiring human acceptance.

#### D-15 — Ordered content envelopes

**P:** Represent available content using the envelopes in §3.4. Preserve order and multiplicity within each available output sequence. Do not deduplicate by transaction identifier, group by account, synthesize missing records, or replace ordered records with keyed maps.

No cross-stream ordering is asserted for posting transaction and rejection streams. Reporting uses one mixed record sequence so header/detail/total ordering is not lost.

**Basis:** Stage 5 §4–§6; D-2/D-6/D-7; R-1, R-3, R-7, R-11–R-16.

#### D-16 — Non-attestation and non-vacuous content

**P:** Returned envelopes contain `completeness: "not_attested"` and `durability: "unknown"`.

- Completeness concerns processing of the underlying batch/range and delivery of the complete underlying output—not whether a known represented value may be omitted.
- Durability concerns lasting source-resource effects—not uncertainty about every returned field.
- Neither label is a boolean false or proof of failed/incomplete processing.
- A `200` content response requires substantive output content under §3.4. An all-empty/all-unavailable envelope is not a content success.
- Lack of available content must not be disguised as a confirmed empty report or a zero total.

**Basis:** Stage 5 D-4/D-6, §5; R-6, R-8, R-12, R-15, R-18.

#### D-17 — Optional availability does not erase obligations

**P:** Optional content availability describes the response boundary, not optional capability scope. When licensed content is available for a returned representation, its mapped fields, order, and multiplicity shall be retained. `unavailable` cannot replace known content for convenience.

The contract continues to require representation of posting transactions/rejections, generated interest transactions, and report headers/details/totals where available. Lack of authority to promise universal availability remains G-23, rather than being declared closed by uncertainty tags.

**Basis:** Stage 5 §4 output mappings, §5 observability limits; D-3/D-4; R-3, R-6, R-11, R-14, R-16.

All Stage 6 decisions remain proposals for this public run; none establishes institutional applicability.

### 2.3 Scope Constraint

**C-4 — Excluded surface.** No CRUD, state provisioning, state snapshot, reset, rollback, compensation, retry, idempotency receipt/key, status resource, job scheduling, backup, combination, fee computation, or API pagination is exposed.

Authentication and authorization are unspecified, not absent or unnecessary. No anonymous-access guarantee is made.

Source filler, customer declarations, unrelated account fields, separators, and internal counters do not acquire new business meanings through this API.

Traceability: Stage 5 D-3/D-4/D-7/D-8; §6 and §7.2; R-4–R-11, R-16, R-19, R-20.

## Section 3: Shared Type Schemas

Shared registration does not imply shared business or resource identity.

### 3.1 Field Representation and Authority

For every content schema:

- Each field’s **meaning is S**, through the cited Stage 5 row.
- JSON names, types, requiredness, closed-object shape, and unions are **P**, under D-10/D-11.
- Business-domain validity, physical encoding conversion, and unstated normalization are **U**.
- Requiredness applies **when that content record is represented**; it does not guarantee the record’s availability.
- Unknown required values shall not be fabricated or replaced with null, zero, empty text, or another record’s value. Inability to represent known content faithfully invokes G-22/G-23.

### 3.2 Posting and Interest Components

| Canonical component | Proposed fields | Stage 5 field treatment and rules |
|---|---|---|
| `PostingCandidate` | Strings: `transactionId`, `typeCode`, `categoryCode`, `source`, `description`, `amount`, `merchantId`, `merchantName`, `merchantCity`, `merchantPostalText`, `cardReference`, `originalTimestamp`, `suppliedProcessingTimestamp` | §3.1/§4.1 candidate identity/classification, descriptive/merchant, amount/card, temporal rows; R-1–R-3; D-2/D-5/D-8 |
| `PostingTransaction` | Same fields as candidate except `processingTimestamp` replaces `suppliedProcessingTimestamp` | §3.1/§4.1 prepared transaction; R-3/R-6; D-4/D-5 |
| `PostingRejection` | `candidate`: `PostingCandidate`; strings `reason`, `description` | §3.1/§4.1 rejection and §5.1; R-1–R-3 |
| `PostingProgress` | Integers `processedRecordCount`, `preliminaryRejectCount` | §3.1/§4.1 progress; R-1/R-6 |
| `InterestCategoryBasis` | Strings `accountReference`, `typeCode`, `categoryCode`, `categoryBalance` | §3.2/§4.2 encountered basis; R-7/R-10 |
| `InterestIdentifierBasis` | String `parameterText` | §3.2/§4.2 identifier parameter; R-11 |
| `GeneratedInterestTransaction` | Strings `transactionId`, `typeCode`, `categoryCode`, `source`, `description`, `amount`, `cardReference`, `merchantId`, `merchantName`, `merchantCity`, `merchantPostalText`, `originalTimestamp`, `processingTimestamp` | §3.2/§4.2 generated classification and descriptive/card/merchant/time rows; R-10/R-11 |

`InterestCategoryBasis` and `InterestIdentifierBasis` are registered external-input components, **not request properties** under D-14.

**C-5 — Posting distinctions.**

- `PostingRejection.reason` has proposed string enum `"100"`, `"101"`, `"102"`, `"103"`: the selected preliminary reason, not a list of failed checks.
- R-2’s guarded lookup and later 103-over-102 assignment remain authoritative.
- Reason 109 is excluded from this enum and from public branch telemetry.
- Rejection retains original candidate context; posting retains the original timestamp and a newly constructed processing timestamp.
- No full-byte echo guarantee or filler meaning is implied.
- Counts do not certify durable writes. No `postedCount` is derived.

**C-6 — Interest distinctions.**

- `parameterText` remains identifier-construction text, not a validated calendar date.
- Classification/source assignments and merchant zero/space assignments remain those of R-11; they are not null or missing-value markers.
- Generated identifiers are not globally unique by contract.
- Nonzero rate selects computation/write even for zero or negative balance/result.
- Missing disclosure is not zero rate; zero-rate bypass is not rejection.
- No fee amount or account-update receipt is exposed.

The Stage 5 review’s R-10 anchor note remains explicit: the selector resolves through R-10/E-12 to `app/cbl/CBACT04C.cbl:214-217`; computation resolves through E-14 to `app/cbl/CBACT04C.cbl:462-470`. Neither anchor supplies units or rounding policy.

### 3.3 Reporting Components and Nonpublic Types

| Canonical component | Proposed fields or disposition | Stage 5 source and rules |
|---|---|---|
| `ReportingTransactionBasis` | Strings `transactionId`, `cardReference`, `typeCode`, `categoryCode`, `source`, `amount`, `processingTimestamp`; external-input component only | §3.3/§4.3 transaction basis; R-12/R-13/R-16 |
| `ReportingDateBasis` | Strings `startText`, `endText`; external-input component only | §3.3/§4.3 separate dates; R-12/R-16 |
| `ReportDetail` | Strings `transactionId`, `accountReference`, `typeCode`, `typeDescription`, `categoryCode`, `categoryDescription`, `source`, `amountText` | §3.3/§4.3 detail, xref and description rows; R-13/R-16 |
| `ReportHeaderContext` | Strings `reportShortNameText`, `reportLongNameText`, `startText`, `endText` | §3.3 report identity context and §4.3 header; R-16; E-28, `app/cpy/CVTRA07Y.cpy:4-13` |
| `ReportTotal` | String `label`, enum `page`, `account`, `grand`; string `valueText` | §3.3/§4.3 distinct totals; R-13–R-16 |
| `PostingAttemptState` | All preliminary selection/ordered-attempt/local-failure elements internal/descriptive; no payload schema | §3.1/§5.1/§6.2; R-4–R-6/R-18; D-3/D-4 |
| `InterestDisclosureBasis` | Group/type/category/rate and fallback distinction internal dependency; no public schema or consumer input | §3.2/§4.2/§6.3; R-9/R-10; D-3 |
| `InterestAttemptState` | Disclosure/bypass/computation/update/EOF elements internal/descriptive | §3.2/§5.2; R-7–R-11/R-18; D-3/D-6 |
| `UpstreamReportSelectionBasis` | Bounds and card-ordering context external/documentary; not a request override or runtime attestation | §3.3/§4.3/§6.4; R-17/R-19; D-7 |
| `ReportingAttemptState` | Date path/exit, conditional EOF and failures internal/descriptive | §3.3/§5.3; R-12–R-18; D-3/D-6 |

This register accounts for all 17 canonical types.

**C-7 — Presentation representation.** `amountText` and `valueText` carry report presentation values, not reconstructed unlimited-precision quantities. Description fields carry report receiver values, not lossless full lookup descriptions.

The split header identity fields refine the original Stage 6’s ambiguous `reportIdentityText`; they represent Stage 5’s existing report identity context, not a new report identifier.

**C-8 — Reporting limits.**

- Preserve repeated headers, details, and each page/account/grand total occurrence in order.
- Account-labelled grouping remains card-change-triggered.
- No account identifier or page number is invented for a total.
- Header dates do not attest full-range processing.
- `grand` is a source label, not a certified reconciled global total.
- Absence of details does not establish an empty report; absence of totals does not establish zero.
- No final account total, conventional skip-and-continue filtering, or unconditional duplicate EOF contribution is promised.

### 3.4 Request, Envelope, and Error Components

All fields and constants in this subsection are **P**, traced through D-10 and D-13–D-17 to the indicated canonical content or non-guarantee. They are not legacy fields.

#### Request components

`PostingRequest`, `InterestRequest`, and `ReportingRequest` are distinct named, empty, closed JSON objects under D-14. No body property is consumer-supplied.

#### Availability components

For each output sequence, use `oneOf`:

| Variant | Required properties | Meaning |
|---|---|---|
| Available sequence | `availability: "available"`; `items`: array of the designated canonical component | The listed content is available for representation; order and duplicates retained |
| Unavailable sequence | `availability: "unavailable"` | No item content is represented; not a claim of zero output or no effects |

An available sequence may have zero items only as an observation of the represented sequence, not as proof that the source produced none. It cannot by itself satisfy the `200` substantive-content condition.

`ProgressAvailability` similarly uses either:

- `availability: "available"` and `value: PostingProgress`; or
- `availability: "unavailable"`.

Progress availability is optional observability, not promised telemetry or a live status resource.

#### Batch envelopes

| Component | Required fields |
|---|---|
| `PostingEnvelope` | `track: "posting"`; `completeness: "not_attested"`; `durability: "unknown"`; `outputs`: availability of `PostingTransaction[]`; `rejections`: availability of `PostingRejection[]`; `progress`: `ProgressAvailability` |
| `InterestEnvelope` | `track: "interest"`; `completeness: "not_attested"`; `durability: "unknown"`; `outputs`: availability of `GeneratedInterestTransaction[]` |
| `ReportingEnvelope` | `track: "reporting"`; `completeness: "not_attested"`; `durability: "unknown"`; `records`: availability of `ReportRecord[]` |

`ReportRecord` is a `oneOf` union of closed objects:

- `kind: "header"` and `value: ReportHeaderContext`;
- `kind: "detail"` and `value: ReportDetail`;
- `kind: "total"` and `value: ReportTotal`.

This mixed array preserves order and multiplicity among represented content records. Omitted separators remain excluded presentation mechanics under D-7, not silently converted into new records.

#### Non-vacuous `200` constraints

- `PostingEnvelope`: at least one transaction, one rejection, or available `PostingProgress`.
- `InterestEnvelope`: available outputs with `minItems: 1`.
- `ReportingEnvelope`: available records with `minItems: 1`.

These are proposed response-shape constraints, not minimum business-input cardinalities. Posting progress alone is a meaningful count observation, not proof that transaction/rejection output obligations have been fulfilled.

A response with unavailable outputs cannot establish satisfaction of those output obligations merely because progress exists.

#### `InterfaceError`

Required fields:

- `track`: enum `posting`, `interest`, `reporting`, fixed to the called operation.
- `category`: enum `request_representation`, `technical_failure`, `content_unavailable`.
- `completeness`: constant `not_attested`.
- `durability`: constant `unknown`.

Optional field:

- `availableContent`: the corresponding batch envelope, only when substantive licensed content is available.

No message, internal reason, file status, retry flag, resource identifier, diagnostic key, rollback value, or idempotency receipt is included.

### 3.5 Structural Conformance Is Not Business Validation

**C-9 — Proposed structural boundary.**

| Constraint | Authority |
|---|---|
| Required JSON object request body; no properties; non-null | P: D-10/D-14 |
| Listed response fields required when representing their object | P: D-10/D-15 |
| Closed object shapes; enums and constants | P: D-10/D-13–D-16 |
| Preliminary reason membership and total-label distinctions | S meaning; P spelling/enum encoding: C-5/C-8 |
| Decimal quantity and temporal/reference roles | S meaning; P JSON string representation: D-11 |
| Numeric ranges/scale/rounding, calendar validity, start-before-end, trimming/padding/coercion | U; not imposed |
| Legacy business acceptance inferred from JSON conformance | Unsupported |

The proposed `400` is restricted to request representation. It does not move legacy preliminary checks into HTTP validation.

## Section 4: Operation API Contracts

### 4.1 POST /posting — Posting

- **Request:** Required `PostingRequest`, `application/json`.
- **Responses:** `200 PostingEnvelope`; `400`, `500`, or `503 InterfaceError` under Section 5.
- **Validation:** C-9 only; no candidate business fields are supplied by this request.
- **Traceability:** Stage 5 §3.1/§4.1/§5.1/§6.2; D-2–D-6/D-8; R-1–R-6/R-18/R-20; D-9–D-17.

| Participation category | Posting treatment |
|---|---|
| Consumer-supplied | Operation request only; no business properties |
| Externally supplied | Daily candidate sequence and its candidate values |
| Internal dependency | Xref association, account comparison/balance fields, category balance |
| Unknown/EOF | Actual sequence contents/order/end condition are not supplied by HTTP; request is not EOF |
| Not exposed | Branch flags, reason 109, file statuses, state snapshots |

**C-10 — Posting effects and outcomes.**

| Stage 5 §5.1 outcome | Contract destination |
|---|---|
| Preliminary posting selected | Internal selection; no success receipt |
| Preliminary rejection selected | Available `PostingRejection` content in batch envelope |
| Card rejection 100 | Selected reason content; account lookup remains guarded |
| Account rejection 101 | Selected reason content, distinct from rewrite failure |
| Comparison rejection 102/103 | One selected reason; R-2 precedence retained |
| Account rewrite reason 109 | Internal/descriptive; not preliminary rejection or public diagnostic |
| Local open/write/close failure | `500` only if independently known to response boundary; no universal detection guarantee |
| Completion information reached | Optional `PostingProgress` representation; no committed-count interpretation |

Preliminary rejection is batch content, including in mixed-output `200` responses. It is not HTTP request rejection.

Category, account, and transaction operations remain ordered attempts. Neither a rejection nor an error response implies unchanged balances or rollback.

### 4.2 POST /interest — Interest Transaction Generation

- **Request:** Required `InterestRequest`, `application/json`.
- **Responses:** `200 InterestEnvelope`; `400`, `500`, or `503 InterfaceError`.
- **Validation:** C-9 only; no positivity, date, rate, or currency checks.
- **Traceability:** Stage 5 §3.2/§4.2/§5.2/§6.3; D-2–D-6/D-8; R-7–R-11/R-18/R-20; D-9–D-17.

| Participation category | Interest treatment |
|---|---|
| Consumer-supplied | Operation request only |
| Externally supplied | Encountered category sequence; `InterestIdentifierBasis.parameterText` |
| Internal dependency | Account, account-key xref, disclosure basis, group accumulator, suffix |
| Unknown/EOF | Actual grouping/input contents and external parameter validity unknown; HTTP is not an EOF signal |
| Not exposed | Rate selection trace, zero-rate branch events, account updates, suffix state, fees |

**C-11 — Interest outcomes and finalization.**

| Stage 5 §5.2 outcome | Contract destination |
|---|---|
| Selected disclosure available | Internal dependency; no public rate lookup |
| Zero-rate bypass | No fabricated transaction or rejection; unavailable content is not evidence of this branch |
| Computation/write selected | Available `GeneratedInterestTransaction` sequence, preserving multiplicity |
| Previous-group account update | Internal effect, not an update receipt |
| Normal EOF without final update | Explicit no-final-flush constraint |
| Dependency/write failure | Conditional `500`; no posting-style business rejection |

Under R-8’s normal pre-test EOF assumptions, no final-account update is inserted. Generated transaction content does not attest corresponding account rewriting.

Where no transaction content is available, the contract does not infer whether the cause was zero-rate bypass, empty input, failure, or missing observation.

### 4.3 POST /reporting — Transaction Reporting

- **Request:** Required `ReportingRequest`, `application/json`.
- **Responses:** `200 ReportingEnvelope`; `400`, `500`, or `503 InterfaceError`.
- **Validation:** C-9 only; no range coherence, calendar, default-date, or upstream override policy.
- **Traceability:** Stage 5 §3.3/§4.3/§5.3/§6.4; D-2–D-7; R-12–R-18/R-20; D-9–D-17.

| Participation category | Reporting treatment |
|---|---|
| Consumer-supplied | Operation request only |
| Externally supplied | Reporting transaction sequence; separate reporting start/end input; documentary upstream selection context |
| Internal dependency | Card xref, type/category lookups, current-card state, accumulators and presentation counters |
| Unknown/EOF | Date-input EOF and post-read transaction storage remain unknown; no HTTP substitute/default |
| Not exposed | SORT override, grouping control, counters, EOF branch trace, finalization status |

| Stage 5 §5.3 outcome | Contract destination |
|---|---|
| Date-permitted detail path | Available report header/detail/total content |
| Date-alternative exit | C-8: loop-sentence exit, not skip-and-continue |
| Date-input EOF | No invented range or empty-success meaning; no branch telemetry |
| Conditional EOF finalization | Available page/grand content only where represented; no final account total inserted |
| Card-transition total attempt | Preserve available earlier total before later content; do not erase it due to later failure |
| Lookup/output failure | Conditional `500`, optionally retaining available content |

A header-only or total-only response represents those observations, not a complete report. `not_attested` does not certify partiality; it refuses a completeness claim.

The upstream SORT basis and the separate reporting date basis remain distinct. No complete-output interval-intersection interpretation is introduced.

## Section 5: Error Handling Strategy

### 5.1 Response Categories

**C-12 — Keep domain and interface meanings separate.**

The response boundary distinguishes:

1. Available canonical content.
2. Posting preliminary rejection content.
3. Request-representation rejection.
4. Technical failure known to the boundary.
5. Inability to provide substantive canonical content.

Unknown persistence is not a separate success/failure status. Missing observations are not fabricated technical diagnoses.

### 5.2 Category Table

All status choices are **P**, requiring gate acceptance.

| Response case | Status | Body | Proposed observable trigger | Promise explicitly denied |
|---|---:|---|---|---|
| Substantive licensed content available, with no known technical failure represented | 200 | Track envelope satisfying §3.4 | Actual canonical content available for the response | Complete batch processing, durability, exhaustive underlying outputs |
| Preliminary posting rejection content available | 200 | `PostingEnvelope` containing rejection(s), possibly other content | Selected preliminary rejection content available | HTTP validation failure, all-check list, no earlier/other effects |
| Request does not match empty closed object shape | 400 | `InterfaceError`, category `request_representation` | Request representation mismatch | Legacy business rejection or a claim about source execution |
| Technical failure known at response boundary | 500 | `InterfaceError`, category `technical_failure`; optional available content | Known technical failure, not merely an inferred internal branch | Universal error detection, reliable resource diagnosis, rollback, no effects |
| No substantive content available and no known technical failure | 503 | `InterfaceError`, category `content_unavailable` | Inability to provide a §3.4 content response | Empty business result, source failure, retry safety, future availability |

Known technical failure takes precedence over a content `200`; already available content remains representable in the error body.

No guarantee is made that every process/external failure produces an HTTP response. No `Retry-After`, `Location`, or status-resource link is specified.

### 5.3 Rationale for Non-Obvious Status Decisions

- `200` is successful delivery of licensed content, not durable business completion.
- `503 content_unavailable` prevents an all-empty success. It is not a promise that retry will help or that the condition is temporary.
- `400` concerns only the selected structural request proposal.
- `500` does not translate `CEE3ABD` or a file status into guaranteed observable HTTP behavior.
- `201`, `202`, and `204` are not selected: no creation receipt, asynchronous lifecycle, or empty-success meaning is introduced.
- Interest zero-rate bypass and report date exit are not new HTTP error categories. Their internal occurrence cannot be inferred from unavailable content.

The triggers are proposed consumer-boundary conditions, not specifications of how they are detected or realized. G-23 preserves missing authority for universal observation.

### 5.4 State and Recovery Contract

**C-13 — Common state terms.** For each resource below, actual instance identity, persistent initialization authority, lifetime, isolation, restart effects, and durable failure consequences remain unresolved unless Stage 5 states a narrower local fact. No public facility is inferred from an external requirement.

**C-14 — Repetition.** Repetition safety remains unknown separately for posting, interest, and reporting. No retry, reset, compensation, rollback, or idempotency mechanism is promised. Unknown is not universally safe or universally harmful.

| State requirement / resource | Stage 5 source | Contract or external/unsupported treatment | Consumer consequence |
|---|---|---|---|
| Posting daily sequence | §6.2; R-1/R-3 | External input; C-1/D-14 | No per-record call or HTTP EOF |
| Posting card association | §6.2; R-2 | Internal dependency; C-4 | No provisioning/lookup API |
| Posting account | §6.2; R-2/R-5 | Internal; C-10/C-13 | Signed arithmetic retained; no snapshot or durable receipt |
| Posting category balance | §6.2; R-4/R-6 | Internal | Local create/update distinction is not consumer control |
| Posting transaction output | §6.2; R-3/R-6 | C-5/D-15–D-17 | Content not persistence receipt; output-open effects unknown |
| Posting rejects | §6.2; R-1/R-3/R-6 | C-5 | Counts do not attest persisted rejects |
| Posting control/counts | §6.2; R-1/R-4–R-6 | Flags internal; progress conditionally represented | Local resets not restart tokens |
| Interest category sequence | §6.3; R-7/R-10 | External input | No global grouping guarantee |
| Interest account | §6.3; R-7/R-8 | Internal; C-11 | Cycle clears are local; no final flush |
| Interest account-key xref | §6.3; R-7/R-11 | Internal | No cardinality/card-selection policy |
| Interest disclosure | §6.3; R-9/R-10 | Internal | Missing is not zero |
| Interest identifier parameter | §6.3; R-11 | External basis | No calendar/lifetime validity promise |
| Interest group control/accumulation | §6.3; R-7/R-8/R-10 | Internal | Local transition reset not resource reset |
| Interest suffix | §6.3; R-11/R-20 | Internal | Initialization does not imply cross-run uniqueness |
| Interest transaction output | §6.3; R-8/R-11/R-20 | C-6/D-15–D-17 | Independent of account rewrite |
| Reporting transaction sequence | §6.4; R-12/R-15/R-17 | External | Actual order/EOF storage unresolved |
| Reporting date input | §6.4; R-12/R-16/R-17 | External | No default or EOF substitution |
| Upstream selection result | §6.4; R-17/R-19 | External documentary context | No executed-flow attestation or override |
| Reporting card association | §6.4; R-13/R-18 | Internal | Prior total attempt may precede lookup failure |
| Reporting type descriptions | §6.4; R-13/R-16 | Internal lookup; report receiver represented | No lossless full-description promise |
| Reporting category descriptions | §6.4; R-13/R-16 | Internal lookup; report receiver represented | Same receiver limitation |
| Page accumulation | §6.4; R-14/R-15 | Internal; conditional total content | No accumulator observation |
| Account accumulation | §6.4; R-13–R-15 | Internal; conditional total content | No mandatory EOF account total |
| Grand accumulation | §6.4; R-14/R-15 | Internal; conditional total content | No reconciliation |
| Reporting control/presentation | §6.4; R-16 | Internal | No API pagination or twenty-detail guarantee |
| Report output | §6.4; R-13–R-16/R-18/R-20 | C-7/C-8/D-15–D-17 | Retain represented order; failure not empty/unchanged output |
| Transaction backup | §6.5; R-19/R-20 | External, all three tracks | No reset facility |
| Combined intermediate | §6.5; R-19/R-20 | External, posting/interest | No completed merged state |
| Master lifecycle context | §6.5; R-19/R-20 | External, all three tracks | No confirmed shared live instance |
| Procedure control | §6.5; R-19 | External/unavailable | Missing `REPROCT` remains unresolved |
| External failure routine | §6.5; R-18 | External/unavailable | No termination, return, or rollback semantics |

## Section 6: Traceability Matrix

Field-level mappings in Section 3 and resource-level mappings in §5.4 are integral to this matrix.

| Contract element | Canonical element / treatment | Rule | Decision |
|---|---|---|---|
| C-1–C-3 routes and batch requests | Stage 5 §4 operation boundaries and §6 external sequences | R-1/R-7/R-11/R-12/R-19 | D-2/D-9/D-14 |
| C-4 exclusions | Internal state, operational context, unlicensed fields/fees | R-4–R-11/R-16/R-19/R-20 | D-3/D-4/D-7/D-8 |
| C-5 posting schemas | Candidate, transaction, rejection, progress | R-1–R-6 | D-5/D-10/D-11 |
| C-6 interest schemas | External bases and generated transaction | R-7–R-11 | D-3/D-5/D-10/D-11 |
| C-7/C-8 reporting schemas | External date/transaction basis; header/detail/total | R-12–R-17 | D-5–D-7/D-10/D-11 |
| C-9 structural constraints | Transport-only choice over licensed participation | R-1/R-7/R-12; Stage 5 D-5 | D-10/D-14 |
| C-10/C-11 effect limits | Ordered attempts and omitted finalization | R-4–R-8 | D-4/D-6 |
| C-12 status/error shapes | Domain content versus conditional failures | R-1/R-6/R-9/R-13/R-18 | D-4/D-13 |
| C-13/C-14 state and repetition | Stage 5 §6 | R-6/R-18–R-20 | D-2–D-4 |
| Availability discriminators and arrays | Conditional output participation | R-3/R-6/R-11/R-14/R-16/R-18 | D-15/D-17 |
| Completeness/durability constants | Non-guarantees, not observed branch states | R-6/R-8/R-12/R-15/R-18 | D-4/D-6/D-16 |
| Nonempty content-success constraint | Retained output obligations; no empty-success inference | R-3/R-6/R-11/R-14–R-16 | D-16/D-17 |
| Report mixed-record union | Header/detail/total ordering and multiplicity | R-13–R-16 | D-7/D-15 |
| Nonpublic canonical types | Stage 5 internal/descriptive outcome treatment | R-4–R-18 | D-3/D-12 |

No new E-n or R-n is created.

## Section 7: Reverse-Completeness Matrix — Contract Destination

| Operation / rule / effect | Evidence | Semantic representation | Stage 5 boundary treatment | Contract destination / exclusion / gap |
|---|---|---|---|---|
| Posting selection | E-4/E-7 | R-1 | Candidate/rejection/progress; flags internal | C-1/C-5; batch participation D-14; no selection telemetry |
| Posting precedence | E-7/E-8/E-20/E-21/E-27 | R-2 | Selected rejection and internal checks | C-5; 100–103, later 103 precedence; domain policy remains G-22 |
| Posting versus reject content | E-4/E-9/E-26/E-27 | R-3 | Distinct types; filler excluded | C-5 and posting envelope; D-8 excludes byte/filler invention |
| Category accumulation | E-9/E-10/E-22 | R-4 | Internal state/attempt distinction | C-10/§5.4; no category API or trace |
| Account arithmetic/109 | E-7/E-9/E-10/E-20 | R-5 | Internal signed updates; later reason distinct | C-5/C-10; 109 excluded from preliminary rejection |
| Posting completion/failure | E-7/E-9–E-11/E-29 | R-6 | Counts/ordered attempts; durability gap | Progress represented conditionally; C-10/C-12; G-23 |
| Interest transitions | E-5/E-12/E-13/E-20–E-22 | R-7 | Category basis; internal grouping | C-2/C-6/§5.4; external batch, no update receipt |
| Interest normal EOF | E-12/E-14 | R-8 | No final flush; repair excluded | C-11; no fabricated final update |
| Disclosure fallback | E-12/E-13/E-23 | R-9 | Internal dependency/selection | C-6; missing not zero; no public fallback trace |
| Interest selector/quantity | E-5/E-12/E-14/E-22/E-23 | R-10 | Computed amount; internal accumulator; numeric gap | C-6; generation content retained even for zero/negative result; G-22 |
| Generated transaction/fee limit | E-5/E-14/E-26/E-30 | R-11 | Parameter/output; internal suffix; fee exclusion | §3.2/C-6; external parameter; no fee/global uniqueness |
| Report date gate/exit | E-6/E-16/E-26 | R-12 | Date basis; internal EOF; unknown storage | C-3/C-8; no skip-and-continue/default; G-24 |
| Report grouping/lookups | E-6/E-16/E-18/E-21/E-24/E-25 | R-13 | Detail association; internal card grouping | C-8; ordered mixed records; no account/card cardinality |
| Report totals | E-6/E-16–E-18/E-28 | R-14 | Distinct totals; internal accumulators | `ReportTotal` occurrences retained; no reconciliation |
| Report EOF finalization | E-16/E-17 | R-15 | Conditional; repair excluded; numerical gap | C-8; no missing-total zero or final account total; G-24 |
| Presentation | E-6/E-17/E-18/E-24–E-26/E-28 | R-16 | Header/detail; bounded receivers; mechanics internal | C-7/C-8; repeated content represented; spacing/counters excluded |
| Two date sites | E-16/E-31/E-34 | R-17 | Separate documentary basis/configuration gap | External contexts remain separate; no override/intersection; G-24 |
| External failure semantics | E-11/E-15/E-19 | R-18 | Internal diagnostics; external gap | C-12/C-13; conditional error response only; G-23 |
| Operational resources | E-29–E-34 | R-19 | External context; identity/schedule gap | C-4/§5.4; no cycle/backup/combination surface |
| Repetition | E-5/E-9–E-12/E-14–E-19/E-32–E-34 | R-20 | Unknown per track | C-14 for posting, interest, reporting separately |

### 7.1 Remaining Evidence and Bounded Exclusions

Stage 5 §7.2 remains the evidence-accounting authority:

- E-1–E-3 provide track orientation, not additional operations.
- E-4–E-28 support the mapped data/state/outcome meanings above; declaration-only fields are not promoted.
- E-32 retains posting/interest consumers; E-33/E-34 retain all three consumers without merged resource identity.
- E-35 remains non-semantic licensing context under A-6; no legal-clearance contract or fabricated R-n is supplied.

Both Stage 5 review attachments are used as inherited review evidence. Their `not_falsified` findings are not exhaustive proof, new review, or approval of this revision.

### 7.2 Ambiguity Propagation

No inherited A-n is silently closed.

| Ambiguities | Contract consequence |
|---|---|
| A-1/A-8 | Track/resource identity and chronology remain separate under D-2/D-14 |
| A-2/A-16 | Dependency completeness and executable job flow remain external |
| A-3 | Deployed encoding/conversion remains unresolved; G-22 |
| A-4/A-10/A-17 | No durable effects, isolation, external-return, or universal response guarantee; G-23 |
| A-5/A-6 | No clean-context independence or legal-clearance claim |
| A-7 | Upstream evidence layout remains addressed and unchanged |
| A-9 | Static precedence/109 timing retained without intended-policy invention |
| A-11 | Normal EOF no-final-flush deduction retained |
| A-12 | Numeric, parameter, overflow, and identifier-lifetime limits retained; G-22 |
| A-13 | Fee absence remains local and bounded |
| A-14/A-15 | Date/EOF/report totals and grouping uncertainty retained; G-24 |

### 7.3 Revision Disposition of G-21–G-24

Original gap identities remain stable. Proposed documentary treatments below are **not human closure decisions**.

| Gap | Concrete r2 treatment | Residual blocking scope |
|---|---|---|
| G-21 — participation | D-14 selects required empty-object requests for external-input batch processing; every track has explicit participation categories | Any claim that HTTP identifies/provisions a specific input instance, conveys EOF, guarantees availability, or establishes a runtime batch binding remains unsupported. Such clauses require authority, not an invented selector |
| G-22 — schemas/validation | D-10/D-11 and C-9 specify JSON shape, requiredness, null/unknown-property handling, field authority, and structural error proposal | Faithful representation requiring an unknown conversion, business domain, rounding, padding, date validity, or fabricated field remains blocked. Shape conformance is not business validity |
| G-23 — response boundary | D-13/D-15–D-17 specify envelopes, status triggers, availability and non-vacuous content | Universal output delivery, complete observation of attempts, guaranteed failure response, or durable completion remains blocked. Missing output authority cannot be closed by `unavailable` tags |
| G-24 — reporting finalization | Ordered mixed report content, explicit label meanings and non-attestation; no all-empty `200` | Complete-report, certified empty result, reconciled/final total, resolved EOF storage or executed-flow guarantees remain blocked by R-12–R-17 |

G-21–G-24 no longer withhold every HTTP choice. Each has a concrete proposal and a narrowly stated unsupported guarantee.

Legitimate no-output paths are not converted into business failures by `503 content_unavailable`. If a future contract must positively distinguish zero-output completion from unavailable observation, that distinction remains blocked under G-23/G-24 until supported. No branch telemetry is introduced to force a distinction.

Inherited G-17–G-19 continue to block stronger value, state, and reporting claims. Pending review of legitimate representation proposals is recorded as pending review, not misclassified as absent COBOL evidence.

## Completeness Gate and Entry Condition

All conditions remain unchecked:

- [ ] All three mandatory tracks receive separate substantive review.
- [ ] Exact capability identity and all upstream version pins remain unchanged.
- [ ] All canonical operations have proposed contracts; no extra surface lacks D-n authority.
- [ ] All 17 canonical types have public, external-input, internal, or excluded dispositions.
- [ ] Every field and structural constraint has S/P/U authority classification.
- [ ] Batch participation is accepted without singleton, resource-selector, or EOF invention.
- [ ] Outcome mapping preserves all Stage 5 guards and observability limits.
- [ ] Output order and multiplicity remain representable without deduplication or regrouping.
- [ ] `not_attested`, unknown, false, zero, and absence remain distinct.
- [ ] No all-empty response vacuously satisfies output obligations.
- [ ] Optional observations are not guaranteed telemetry.
- [ ] Every state/reset requirement maps to a clause or explicit external/unsupported treatment.
- [ ] Error categories and status triggers do not imply rollback, no effects, or universal response availability.
- [ ] All R-1–R-20 have accountable destinations.
- [ ] Risk-oriented review records passage, objection, conclusion, and clause/exclusion/gap disposition.
- [ ] Review addresses reason 109, missing interest flush, report EOF/date exit, prior effects before failure, and missing output observations.
- [ ] Review explicitly states that sampling does not establish completeness.
- [ ] Residual G-21–G-24 blockers are handled without unsupported closure.
- [ ] Exact revised artifact, inputs, feedback, and review records are retained and pinned.
- [ ] Human review outcome is recorded externally.

### Provenance and Current Status

AI assistance was limited to drafting this versioned Stage 6 contract from the supplied approved chain, authorizations, both Stage 5 attachments, failed original Stage 6, directed feedback/plan, source text/numbered representations, and generic template/rules.

No tools, additional model/network calls, compilation, COBOL execution, source repair, implementation, or generated code were used. Runtime binding, storage design, and realization behavior are not specified. Provider retention settings, usage, cost, and filesystem persistence are not certified by this document.

**Stage 6 remains an unapproved proposed-interface specification. No gate is approved. No further-stage work or API implementation is authorized.**
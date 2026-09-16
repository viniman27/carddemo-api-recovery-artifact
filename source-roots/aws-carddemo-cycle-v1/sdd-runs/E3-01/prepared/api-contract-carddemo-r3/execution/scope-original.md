# API Contract Specification

## Purpose

This Stage 6 r3 specification proposes the API contract for the AWS CardDemo public cycle from the approved Stage 5 canonical data boundary.

**Posting, interest, and reporting remain mandatory, separately traceable tracks.** The exact inherited capability identity is `unselected-stage-1-scope-only`.

| Attribute | Value |
|---|---|
| Run | `E3-01` |
| Stage | `6` |
| Feature | `api-contract-carddemo-r3` |
| Artifact | `specs/api-contract-carddemo-r3/requirements.md` |
| Revision of | `api-contract-carddemo-r2` |
| Status | `draft/proposed-interface` |
| Human approval granted | `false` |
| Completeness gate passed | `false` |
| Ready for implementation | `false` |

This is a **narrow, versioned revision** of the unapproved r2 contract. It retains the external-input design, routes, request shapes, canonical content schemas, state exclusions, and traceability identities. It changes only the distinction between observed empty sequences and unavailable observations, including consequential envelope, status, and gap wording.

The document is representable in OpenAPI 3.1. It is not a generated OpenAPI artifact, implementation, runtime binding, or authorization to execute anything.

## Contract Integrity Discipline

- Every contract element derives from a Stage 5 canonical element or an explicitly recorded D-n representation decision.
- Stage 5 outcome guards, exclusions, internal-state treatments, and unresolved gaps remain binding.
- Method, route, JSON shape, structural constraints, and HTTP statuses are **proposals for human review**, not recovered COBOL guarantees.
- Internal state does not become public telemetry merely because Stage 5 models it.
- Observed empty sequences, missing observation, zero quantities, zero-rate bypass, and known technical failure remain distinct.
- `not_attested` is not confirmed incompleteness; `unknown` is not false.
- Known licensed content must not be discarded or replaced by uncertainty labels.
- No source repair, invented business validation, stronger persistence guarantee, or automatic gate approval is introduced.

Authority classifications used throughout:

- **S — source-grounded meaning:** inherited through Stage 5 and its R-n mapping.
- **P — proposed representation:** requires external human acceptance.
- **U — unsupported or unresolved:** no default guarantee follows.

Normative wording describes the proposed contract only.

## Section 1: Upstream Authority and Entry Condition

### 1.1 Upstream Authority and Scope Inheritance

The entry basis is the supplied current approved chain: Stages 1, 2-r2, 3-r2, 4, and 5, their authorizations, and both Stage 5 review attachments.

| Artifact relative to `RUN_ROOT` | Supplied SHA-256 |
|---|---|
| `specs/pipeline-scope-carddemo/requirements.md` | `1362fab5d55b77ef6121328606ae974295cd5723849520e9a246f4bd45e64cc9` |
| `specs/capability-selection-carddemo-r2/requirements.md` | `abdb59180f379d9e14eb86dfa1d8226ec50c981346767e808fd382eb7462bbc4` |
| `specs/legacy-evidence-carddemo-r2/requirements.md` | `4566786600b60e9377c1e369e67765098d06b0153ba973361d2065614a6c9b7b` |
| `specs/capability-semantics-carddemo/requirements.md` | `2f9d3ee52dd7788e206810e38c9173b19d21dfc44270cdd06d05e62dec95eb93` |
| `specs/canonical-data-boundary-carddemo/requirements.md` | `208d04fe6f9cae665dfa4cb514de5d4ad9eaf0ebc169dfae0fd8a6ba209e66f3` |
| `reviews/stage-5-authorization.json` | `a2f73337b5ec123d62ab41e9c058a3065f1ccf133c48e5b81f54f9a2610bfe23` |
| `STAGE5-COUNTEREXAMPLE-REVIEW.md` | `0dadcd665b1e4cb71765003c22655f7b04a3430bf92077f9d63d33053aa2fdfe` |
| `stage5-counterexample-findings.json` | `caa6418e2ebec9e52a795e1bafd9ca304a21d55a0c28e73e86b06162c33ec84e` |

Stage 5 approval authorizes this contract specification within conditional documentary scope. It does not resolve numeric/date policy, durable effects, EOF storage, configuration, external routine behavior, or repetition safety.

The exact supplied `input_pins` register is incorporated by reference without alteration. This includes:

- All five current upstream metadata and artifact pins.
- All five authorization pins.
- Stage 4 review and both Stage 5 attachments.
- All 19 original corpus-file pins and their separate derived-representation pins.
- Source-package and all 13 framework pins.
- All six r2 provenance entries and both r3 feedback entries.

The current Stage 5 metadata pin is `4f6005cba97aa29d3a73e6cc4e36d2b0401fe159bcdfc5f28b0c2447080a10ef`. The review-time metadata digest in the Stage 5 findings remains historical, not a substitute.

The source package is the supplied absolute `research-package.json` reference, SHA-256 `63ba5c47ecb21349549744b912af3b150654e7e435724dba499e3c88369f15a2`.

The governing template is `FRAMEWORK_ROOT/settings/templates/pipeline/api-contract-spec.md`, SHA-256 `c6eb797f8acb57cf943662d8ba4bb694f584ad84542d0c634799798587f09e7a`. The supplied generic rules govern this document; their historical examples are not application evidence.

Exact source text, original byte pins, and stable 1-based numbered representations remain distinct evidence objects. Retention of this artifact must include the exact request and pin register; these tables do not replace source bodies. No digest was recomputed.

#### Revision inputs

| Input | Supplied SHA-256 |
|---|---|
| `specs/api-contract-carddemo-r2/spec.json` | `3dd7c64774f75c3155b2e9941f139ca593401887555fd7d7917874c6bc591b54` |
| `specs/api-contract-carddemo-r2/requirements.md` | `163d1d0455f2524e8100e1722b78f255fbca7a4bda1a5caccb45e05fbe362567` |
| `prepared/api-contract-carddemo-r2/execution/scope-original.md` | `163d1d0455f2524e8100e1722b78f255fbca7a4bda1a5caccb45e05fbe362567` |
| `STAGE6-R2-INPUTS-EMPTY-REVIEW.md` | `f670185483e1310f5a9313a75db5d4866bc4cc6c0b9d742b48831bf53d0ac9ec` |
| `reviews/stage-6-r2-directed-feedback.md` | `17f274900d9efc7bf41fcbbc523130d3d3896a5195e81ee2e29fcc72491ccdd8` |

Both new review records are revision instructions, not gate approvals. The r2 artifact remains unapproved and unchanged. This revision retains C-1–C-14, D-9–D-17, and G-21–G-24 without renumbering.

The supplied gate check reports freshness of existing upstream authority only. No new gate check or approval is claimed here.

### 1.2 Inherited Model Constraints

| Stage 5 decision | Contract consequence |
|---|---|
| D-2 | Track-qualified meanings; no global transaction lifecycle, resource identity, or cardinality |
| D-3 | Internal dependencies are not consumer-controlled resources or guaranteed observations |
| D-4 | No atomicity, rollback, durable partial-state, exhaustive diagnosis, or safe repetition guarantee |
| D-5 | No invented units, rounding, numeric domain, calendar validity, encoding conversion, or identifier lifetime |
| D-6 | No final interest flush, repaired report filtering, final account total, or reconciled total |
| D-7 | Bounded report presentation; operational context is not an executable schedule or API pagination |
| D-8 | No new business meaning for filler, declaration-only fields, or the fee placeholder |

## Section 2: API Operation Surface

### 2.1 Operation Inventory

| Clause | Method and route | Operation ID / track | Canonical authority | Granularity |
|---|---|---|---|---|
| C-1 | `POST /posting` | `posting` | Stage 5 §4.1 | Batch operation against externally supplied daily input |
| C-2 | `POST /interest` | `interest` | Stage 5 §4.2 | Batch operation against external category input and identifier basis |
| C-3 | `POST /reporting` | `reporting` | Stage 5 §4.3 | Batch operation against external transaction/date inputs |

One request does not mean one transaction, one account, an atomic batch, or complete input consumption. No deadline, cardinality, or cross-track invocation order is prescribed.

### 2.2 Method and Route Structure

| Decision | Proposed choice, rationale, and consequence | Upstream basis |
|---|---|---|
| D-9 | Retain three POST operations. No safe retrieval, idempotent replacement, combined cycle, or resource lifecycle is implied. | D-2; R-1, R-7, R-12, R-19, R-20 |
| D-10 | Use OpenAPI 3.1-representable JSON objects, arrays, required properties, constants, and unions. Objects are closed with `additionalProperties: false`; null is not an unknown-value substitute. | Stage 5 types; D-2, D-3, D-5, D-7, D-8 |
| D-11 | Use strings for references, codes, temporal values, descriptions, decimal quantities, and report presentation values; integers for progress counts. No new regex, scale, range, length, padding, trimming, or coercion policy. | D-5; R-2, R-3, R-5, R-10–R-12, R-14, R-16 |
| D-12 | Represent canonical content, not internal branch telemetry. All `AttemptState` types remain internal/descriptive. | D-3, D-4; Stage 5 §5–§6 |
| D-13 | Retain proposed statuses 200, 400, 500, and 503; narrow their observation boundary as specified in §5. | D-4; R-1, R-6, R-9, R-13, R-18 |
| D-14 | Retain required empty closed JSON request objects. No consumer business fields, dataset selector, EOF signal, provisioning, singleton assumption, or input-availability assertion. | D-3; Stage 5 §4/§6; R-1, R-7, R-11, R-12, R-17, R-19 |
| D-15 | Retain ordered arrays and duplicates. Posting streams remain separate; reporting uses one mixed header/detail/total sequence. No deduplication, regrouping, invented records, or cross-stream order. | D-2, D-6, D-7; R-1, R-3, R-7, R-11–R-16 |
| D-16 | **Revised:** require an actual represented observation for 200, not nonempty item content. An observed empty sequence qualifies; an all-unavailable/no-observation envelope does not. Non-attestation remains scoped. | D-4, D-6; R-6, R-8–R-12, R-15, R-18; both r3 feedback records |
| D-17 | Availability is optional boundary representation, not optional capability scope or guaranteed telemetry. Retain licensed content whenever available; uncertainty cannot excuse omission. | Stage 5 §4–§5; D-3, D-4; R-3, R-6, R-11, R-14, R-16 |

#### D-16 — Revised observation boundary

Every envelope retains:

- `completeness: "not_attested"`: no attestation of full batch/range processing or exhaustive underlying output delivery.
- `durability: "unknown"`: lasting source-resource effects are not established.

These constants neither invalidate known represented values nor establish false/incomplete outcomes.

An **observation** sufficient for the proposed 200 boundary is:

1. An available output sequence, including a positively observed empty represented sequence; or
2. For posting only, available `PostingProgress`, including zero counts.

A nonempty array is not required to substantiate an empty-sequence observation. Conversely, no observation cannot be relabelled as an empty observation.

All decisions remain public-run interface proposals requiring human review; none establishes institutional applicability.

### 2.3 Scope Constraint

**C-4 — Excluded surface.** No CRUD, input upload/provisioning, state snapshot, dataset selector, reset, rollback, compensation, retry, idempotency key/receipt, status resource, readiness probe, job scheduling, backup, combination, fee computation, or API pagination is exposed.

Authentication and authorization remain unspecified, not declared unnecessary or absent. No anonymous-access guarantee is made.

Filler, customer declarations, unrelated account fields, separators, and internal counters acquire no new business meanings.

Authority: Stage 5 D-3, D-4, D-7, D-8; §6–§7; R-4–R-11, R-16, R-19, R-20.

## Section 3: Shared Type Schemas

### 3.1 Representation Rules

All listed properties are required when their object is represented, except properties expressly marked optional. All objects are closed and non-null under D-10.

Field meanings are **S** through the Stage 5 references below. JSON names, types, requiredness, constants, unions, and closed shapes are **P** under D-10/D-11. Unsupported business domains and conversion policies remain **U** under G-22.

Requiredness does not promise that a content record is observable. Unknown field values must not be fabricated as zero, empty text, null, or copied from another record. Legitimate source zero/space values remain values, not unknown markers.

### 3.2 Posting and Interest Components

| Canonical component | Proposed properties | Stage 5 type/field authority |
|---|---|---|
| `PostingCandidate` | Strings: `transactionId`, `typeCode`, `categoryCode`, `source`, `description`, `amount`, `merchantId`, `merchantName`, `merchantCity`, `merchantPostalText`, `cardReference`, `originalTimestamp`, `suppliedProcessingTimestamp` | §3.1/§4.1 candidate identity, classification, descriptive/merchant, amount/card, and temporal rows; R-1–R-3; D-2, D-5, D-8 |
| `PostingTransaction` | Same listed properties, replacing `suppliedProcessingTimestamp` with `processingTimestamp` | §3.1/§4.1 prepared transaction; R-3, R-6; D-4, D-5 |
| `PostingRejection` | `candidate`: `PostingCandidate`; strings `reason`, `description` | §3.1/§4.1 rejection; §5.1 preliminary outcomes; R-1–R-3 |
| `PostingProgress` | Integers `processedRecordCount`, `preliminaryRejectCount` | §3.1/§4.1 progress; R-1, R-6 |
| `InterestCategoryBasis` | Strings `accountReference`, `typeCode`, `categoryCode`, `categoryBalance` | §3.2/§4.2 encountered basis; R-7, R-10 |
| `InterestIdentifierBasis` | String `parameterText` | §3.2/§4.2 identifier parameter; R-11 |
| `GeneratedInterestTransaction` | Strings `transactionId`, `typeCode`, `categoryCode`, `source`, `description`, `amount`, `cardReference`, `merchantId`, `merchantName`, `merchantCity`, `merchantPostalText`, `originalTimestamp`, `processingTimestamp` | §3.2/§4.2 generated classification and descriptive/card/merchant/time rows; R-10, R-11 |

`InterestCategoryBasis` and `InterestIdentifierBasis` are external-input component descriptions, **not request properties**.

**C-5 — Posting distinctions.**

- `reason` has proposed string enum `"100"`, `"101"`, `"102"`, `"103"`.
- It represents the selected preliminary rejection, not all failed checks.
- Guarded account lookup and later 103-over-102 assignment remain authoritative.
- Reason 109 remains internal, excluded from preliminary rejection and public diagnostic fields.
- Rejection retains original candidate context; posted content has a newly constructed processing timestamp.
- No full-byte echo, filler meaning, or durable receipt is implied.
- Progress is not a committed transaction/rejection count; no `postedCount` is derived.

**C-6 — Interest distinctions.**

- Parameter text is an identifier-construction basis, not a validated date or reporting range.
- R-11 classification/source literals and merchant zero/space assignments remain source assignments.
- Generated IDs carry no global uniqueness guarantee.
- Missing disclosure is not zero rate.
- Selected zero rate bypasses computation/write through that branch and is not rejection.
- Selected nonzero rate can produce a transaction with zero or negative quantity.
- An observed empty generated sequence does not reveal which internal branch caused it.
- No fee amount, suffix state, fallback trace, or account-update receipt is exposed.

The R-10 selector resolves through Stage 5 and R-10/E-12 to `app/cbl/CBACT04C.cbl:214-217`; computation/write resolves through E-14 to `app/cbl/CBACT04C.cbl:462-515`. These do not establish units or rounding policy.

### 3.3 Reporting Components and Nonpublic Types

| Canonical component | Proposed properties or disposition | Stage 5 authority |
|---|---|---|
| `ReportingTransactionBasis` | Strings `transactionId`, `cardReference`, `typeCode`, `categoryCode`, `source`, `amount`, `processingTimestamp`; external-input description only | §3.3/§4.3; R-12, R-13, R-16 |
| `ReportingDateBasis` | Strings `startText`, `endText`; external-input description only | §3.3/§4.3 separate dates; R-12, R-16 |
| `ReportDetail` | Strings `transactionId`, `accountReference`, `typeCode`, `typeDescription`, `categoryCode`, `categoryDescription`, `source`, `amountText` | §3.3/§4.3 detail, xref, descriptions; R-13, R-16 |
| `ReportHeaderContext` | Strings `reportShortNameText`, `reportLongNameText`, `startText`, `endText` | §3.3/§4.3 report identity/header context; R-16; E-28 |
| `ReportTotal` | String `label`, enum `page`, `account`, `grand`; string `valueText` | §3.3/§4.3 distinct totals; R-13–R-16 |
| `PostingAttemptState` | Selection, ordered attempts, and local failures remain internal/descriptive; no payload | §3.1/§5.1/§6.2; R-4–R-6, R-18; D-3, D-4 |
| `InterestDisclosureBasis` | Group/type/category/rate and fallback distinction remain internal dependency; no public schema | §3.2/§4.2/§6.3; R-9, R-10; D-3 |
| `InterestAttemptState` | Disclosure, bypass, computation, transition update, and EOF distinctions remain internal/descriptive | §3.2/§5.2; R-7–R-11, R-18; D-3, D-6 |
| `UpstreamReportSelectionBasis` | Bounds/card-ordering context remains external/documentary; no request override or execution attestation | §3.3/§4.3/§6.4; R-17, R-19; D-7 |
| `ReportingAttemptState` | Date path/exit, conditional EOF, and failures remain internal/descriptive | §3.3/§5.3; R-12–R-18; D-3, D-6 |

All 17 canonical types have explicit dispositions.

**C-7 — Presentation.** Report description properties represent the report receivers, not lossless full lookup descriptions. `amountText` and `valueText` represent bounded report presentation, not reconstructed unlimited-precision quantities. Header identity fields are report context, not a global report identifier.

**C-8 — Reporting limits.**

- Preserve represented header/detail/total occurrence order and multiplicity.
- Account-labelled grouping remains card-change-triggered.
- Do not invent page numbers or account identifiers for totals.
- Header dates do not attest full-range processing.
- `grand` is a source label, not a reconciled global total.
- Missing totals are not zero.
- Empty `records` means only an observed empty represented sequence.
- Empty records do not certify a complete empty report, complete date-range processing, zero totals, reconciled totals, final account total, or skip-and-continue repair.
- EOF duplication remains conditional on unknown storage/date premises, not an asserted result.

### 3.4 Request, Envelope, and Error Components

#### Requests

`PostingRequest`, `InterestRequest`, and `ReportingRequest` are distinct required empty JSON objects: object type, no properties, `additionalProperties: false`.

A missing body, null, array, or object containing properties does not match the proposed shape. The empty object is not an empty business input sequence or EOF signal.

#### Sequence availability

Each sequence availability component is a `oneOf` of these closed objects:

| Variant | Required properties | Meaning |
|---|---|---|
| Available | `availability: "available"`; `items`: array of the designated canonical type | An actual observation of the represented sequence is available |
| Unavailable | `availability: "unavailable"` | No item observation is represented |

**Available arrays allow zero items.** `availability: "available", items: []` means a positively observed empty represented sequence. It is not an inference from missing content and does not attest complete underlying output, input exhaustion, or absence of effects.

The unavailable variant has no `items` property. Null, omitted arrays in an available variant, and invented empty arrays are not substitutes.

`ProgressAvailability` is similarly either:

- `availability: "available"` with `value: PostingProgress`; or
- `availability: "unavailable"` without `value`.

#### Batch envelopes

| Component | Required properties |
|---|---|
| `PostingEnvelope` | `track: "posting"`; `completeness: "not_attested"`; `durability: "unknown"`; `outputs`: availability of `PostingTransaction[]`; `rejections`: availability of `PostingRejection[]`; `progress`: `ProgressAvailability` |
| `InterestEnvelope` | `track: "interest"`; `completeness: "not_attested"`; `durability: "unknown"`; `outputs`: availability of `GeneratedInterestTransaction[]` |
| `ReportingEnvelope` | `track: "reporting"`; `completeness: "not_attested"`; `durability: "unknown"`; `records`: availability of `ReportRecord[]` |

`ReportRecord` is a `oneOf` union:

- `kind: "header"` with `value: ReportHeaderContext`;
- `kind: "detail"` with `value: ReportDetail`;
- `kind: "total"` with `value: ReportTotal`.

Separators remain excluded presentation mechanics under D-7. Repeated canonical content is not collapsed.

#### Proposed 200 observation constraints

| Envelope | Required observation for 200, absent known technical failure |
|---|---|
| Posting | At least one of `outputs`, `rejections`, or `progress` is available |
| Interest | `outputs` is available; `items` may be empty |
| Reporting | `records` is available; `items` may be empty |

There is **no blanket `minItems: 1`** on these output arrays. Available empty sequences count as observations, not as nonempty content.

For posting, available progress with both counts zero may support 200 **as progress observation only**. Zero-count progress does not prove:

- No transaction/rejection effects or prior output attempts.
- Complete input exhaustion.
- Durable state.
- Fulfillment of transaction or rejection output obligations.

An envelope in which every sequence is unavailable and posting progress is also unavailable does not qualify for 200.

These shape predicates are expressible with constants and `anyOf`/`oneOf` constraints. The requirement that an observation actually exists is a contract condition, not something JSON syntax alone establishes.

#### `InterfaceError`

Required properties:

- `track`: the called operation’s track.
- `category`: `request_representation`, `technical_failure`, or `content_unavailable`.
- `completeness: "not_attested"`.
- `durability: "unknown"`.

Optional property:

- `availableContent`: corresponding track envelope containing at least one actual available observation, **including an observed empty sequence or posting progress**.

Known technical failure may therefore retain an empty available sequence in `availableContent`; nonempty items are not required. An all-unavailable envelope is not useful available content and is excluded from this property.

No internal reason, diagnostic stream, file status, retry flag, resource identifier, rollback assertion, or receipt is included.

All envelope/discriminator/error fields are P under D-10 and D-13–D-17, tracing to conditional canonical output participation and Stage 5 D-4/D-6 non-guarantees.

### 3.5 Structural Conformance

**C-9 — Structural constraints are not business validation.**

The required empty request shape, closed objects, property types, enums, and constants are proposed structural constraints only. No JSON conformance result establishes legacy business acceptance.

No new numeric range, decimal scale, currency, rounding, calendar validity, date-range coherence, trimming, padding, or coercion rule is imposed. The proposed 400 concerns request representation only.

## Section 4: Operation API Contracts

### 4.1 POST /posting — Posting

- **Request:** Required `PostingRequest`, `application/json`.
- **Responses:** `200 PostingEnvelope`; `400`, `500`, or `503 InterfaceError`.
- **Validation:** C-9 only.
- **Traceability:** Stage 5 §3.1/§4.1/§5.1/§6.2; R-1–R-6, R-18, R-20; D-2–D-6, D-8–D-17.

| Participation | Treatment |
|---|---|
| Consumer-supplied | Operation request only; no business properties |
| Externally supplied | Daily candidate sequence and candidate values |
| Internal dependency | Xref, account comparison/balance fields, category balance |
| Unknown/EOF | Actual input identity, readiness, contents, order, and end condition are not supplied by HTTP |
| Not exposed | Flags, reason 109, file statuses, snapshots, EOF telemetry |

**C-10 — Posting outcomes and effects.**

| Stage 5 §5.1 outcome | Contract destination |
|---|---|
| Preliminary posting selected | Internal selection, not a success receipt |
| Preliminary rejection selected | Available `PostingRejection` content |
| Card lookup rejection 100 | Selected reason; account lookup remains guarded |
| Account lookup rejection 101 | Selected reason, distinct from rewrite reason |
| Comparison rejection 102/103 | One selected reason with later 103 precedence |
| Account rewrite reason 109 | Internal; no preliminary rejection or diagnostic field |
| Local open/write/close failure | Conditional 500 when known at response boundary |
| Completion information reached | Optional progress representation, including observed zero counts |

Preliminary rejection is batch content, not HTTP request rejection. Transactions and rejections can coexist in one response.

Category, account, and transaction operations remain ordered attempts. Neither 200, rejection content, empty observations, nor an error proves unchanged balances, rollback, or durable partial effects.

### 4.2 POST /interest — Interest Transaction Generation

- **Request:** Required `InterestRequest`, `application/json`.
- **Responses:** `200 InterestEnvelope`; `400`, `500`, or `503 InterfaceError`.
- **Validation:** C-9 only.
- **Traceability:** Stage 5 §3.2/§4.2/§5.2/§6.3; R-7–R-11, R-18, R-20; D-2–D-6, D-8–D-17.

| Participation | Treatment |
|---|---|
| Consumer-supplied | Operation request only |
| Externally supplied | Encountered category sequence and identifier parameter text |
| Internal dependency | Account, account-key xref, disclosure, group accumulator, suffix |
| Unknown/EOF | Actual input identity/readiness/grouping and parameter validity; HTTP provides no EOF |
| Not exposed | Disclosure selection, zero-rate branch events, account updates, suffix state, fees |

**C-11 — Interest outcomes and finalization.**

| Stage 5 §5.2 outcome | Contract destination |
|---|---|
| Selected disclosure available | Internal dependency; no public lookup |
| Zero-rate bypass | No fabricated transaction/rejection; no public branch trace |
| Computation/write selected | Available generated transaction sequence |
| Previous-group account update selected | Internal effect; no receipt |
| Normal EOF without final update | No-final-flush constraint |
| Dependency/write failure | Conditional 500; not posting-style rejection |

An actually observed empty generated sequence may be represented by 200 when no technical failure is known. It is not forced into 503 or business rejection.

This does not claim that every zero-output condition can be observed or that an empty sequence establishes zero-rate bypass. Missing disclosure, zero-rate bypass, and a generated transaction with zero amount remain separate.

Under R-8’s normal pre-test EOF assumptions, no final account update is inserted. Generated transaction observations do not attest account rewriting.

### 4.3 POST /reporting — Transaction Reporting

- **Request:** Required `ReportingRequest`, `application/json`.
- **Responses:** `200 ReportingEnvelope`; `400`, `500`, or `503 InterfaceError`.
- **Validation:** C-9 only.
- **Traceability:** Stage 5 §3.3/§4.3/§5.3/§6.4; R-12–R-18, R-20; D-2–D-7, D-9–D-17.

| Participation | Treatment |
|---|---|
| Consumer-supplied | Operation request only |
| Externally supplied | Transaction sequence, separate reporting dates, upstream documentary selection context |
| Internal dependency | Card xref, type/category lookups, current card, accumulators, presentation counters |
| Unknown/EOF | Input readiness/identity, date contents, date-input EOF, post-read transaction storage |
| Not exposed | SORT override, dataset selector, EOF signal, grouping control, finalization status |

| Stage 5 §5.3 outcome | Contract destination |
|---|---|
| Date-permitted detail path | Available header/detail/total content |
| Date-alternative exit | C-8: loop-sentence exit, not skip-and-continue |
| Date-input EOF | No invented range, branch telemetry, or complete-empty meaning |
| Conditional EOF finalization | Available page/grand content where represented; no final account total inserted |
| Card-transition total attempt | Preserve available earlier total before later content/failure |
| Lookup/output failure | Conditional 500, optionally retaining available observations |

Observed empty `records` may support 200; no-record observation alone is not 503. It remains subject to C-8’s explicit report-completeness and total limitations.

The upstream SORT basis and separately read reporting date basis remain distinct. No common override or complete-output interval-intersection interpretation is introduced.

## Section 5: Error Handling Strategy

### 5.1 Response Categories

**C-12 — Keep domain content, observation availability, and interface errors separate.**

The proposed boundary distinguishes:

1. Available nonempty canonical sequences.
2. Available empty represented sequences.
3. Posting progress observations, including zero counts.
4. Posting preliminary rejection content.
5. Request-representation mismatch.
6. Known technical failure.
7. No representable observation.

Availability is not a source status, completeness claim, or diagnostic cause.

### 5.2 Category Table

All statuses and categories below are **P** under D-13/D-16.

| Category / condition | Status | Body | Upstream basis and limit |
|---|---:|---|---|
| At least one permitted observation is available; no known technical failure | 200 | Track envelope satisfying §3.4 | Stage 5 conditional outputs; D-4/D-6; no durable or complete-batch claim |
| Positively observed empty sequence; no known technical failure | 200 | Track envelope with available `items: []` | D-16; R-10–R-12/R-15 and directed feedback; no complete-empty business claim |
| Posting progress only, including zero counts; no known technical failure | 200 | Posting envelope with available progress | R-1/R-6; progress is not output fulfillment |
| Preliminary posting rejection content | 200 | Posting envelope | R-1–R-3; not structural request rejection |
| Request representation does not match required empty closed object | 400 | `InterfaceError`, `request_representation` | D-10/D-14; no business-validation or source-execution claim |
| Technical failure known at the response boundary | 500 | `InterfaceError`, `technical_failure`; optional `availableContent` | R-18/D-4; may retain empty or nonempty available observations |
| No representable observation and no known technical failure | 503 | `InterfaceError`, `content_unavailable` | D-16/D-17; not an observed empty sequence or inferred source failure |

For the batch response boundary, **known technical failure takes precedence over 200 and 503**, whether available observations are empty, nonempty, or absent.

All-unavailable/no-observation envelopes are not 200. With no known technical failure, they fall under 503; with known technical failure, under 500.

### 5.3 Rationale for Non-Obvious Status Decisions

- 200 concerns delivery of an actual permitted observation, not minimum item cardinality.
- A positively observed empty sequence is an observation; it needs no substantive nonempty item to qualify.
- 503 denotes lack of substantive observation, not lack of nonempty items. It does not classify legitimate no-output behavior as business failure.
- 500 is conditional on known technical failure, not inferred from an internal branch or unavailable content.
- Optional `availableContent` preserves already available observations without negating the failure.
- No guarantee establishes that every external/process failure produces an HTTP response.
- No `Retry-After`, `Location`, polling link, 201 creation receipt, 202 lifecycle, or 204 empty-success response is specified.
- Missing observations do not justify inventing branch causes, including zero-rate bypass or date exit.

These are consumer-visible contract conditions, not instructions for detecting or realizing them.

### 5.4 State and Recovery Contract

**C-13 — Common state limits.** For each resource below, actual instance identity, persistent initialization authority, lifetime, isolation, restart effects, and durable failure consequences remain unresolved except for narrower source-local facts in Stage 5. No resource row creates a public provisioning, reset, or observation facility.

**C-14 — Repetition.** Repetition safety is unknown separately for posting, interest, and reporting. No safe retry, idempotency, compensation, rollback, or reset is promised. Unknown does not mean universally harmful.

| State requirement / resource | Stage 5 source | Contract or external/unsupported treatment | Consumer consequence |
|---|---|---|---|
| Posting daily sequence | §6.2; R-1/R-3 | External; C-1/D-14 | No HTTP input selector or EOF |
| Posting card association | §6.2; R-2 | Internal; C-4 | No provisioning/lookup API |
| Posting account | §6.2; R-2/R-5 | Internal; C-10/C-13 | Signed updates; no snapshot or receipt |
| Posting category balance | §6.2; R-4/R-6 | Internal | Local create-flag reset is not resource reset |
| Posting transaction output | §6.2; R-3/R-6 | C-5/D-15–D-17 | Content observation, not persistence receipt |
| Posting reject output | §6.2; R-1/R-3/R-6 | C-5 | Count does not certify persisted rejection |
| Posting control/counts | §6.2; R-1/R-4–R-6 | Flags internal; optional progress | Local initial/reset values are not restart tokens |
| Interest category sequence | §6.3; R-7/R-10 | External | No actual/global grouping guarantee |
| Interest account | §6.3; R-7/R-8 | Internal; C-11 | Local cycle clears; no final flush |
| Interest account-key xref | §6.3; R-7/R-11 | Internal | No card cardinality/selection policy |
| Interest disclosure | §6.3; R-9/R-10 | Internal | Missing is not zero |
| Interest identifier parameter | §6.3; R-11 | External | No calendar/lifetime guarantee |
| Interest group accumulation/control | §6.3; R-7/R-8/R-10 | Internal | Transition resets are not persistent reset |
| Interest suffix | §6.3; R-11/R-20 | Internal | Zero initialization gives no global uniqueness |
| Generated transaction output | §6.3; R-8/R-11/R-20 | C-6/D-15–D-17 | Independent from account rewrite |
| Reporting transaction sequence | §6.4; R-12/R-15/R-17 | External | Actual order and EOF storage unresolved |
| Reporting dates | §6.4; R-12/R-16/R-17 | External | No default, override, or EOF substitution |
| Upstream selection result | §6.4; R-17/R-19 | External/documentary | No actual flow attestation |
| Reporting card association | §6.4; R-13/R-18 | Internal | Earlier total attempt may precede lookup failure |
| Reporting type descriptions | §6.4; R-13/R-16 | Internal; receiver content represented | No lossless full-description promise |
| Reporting category descriptions | §6.4; R-13/R-16 | Internal; receiver content represented | Same limitation |
| Page accumulation | §6.4; R-14/R-15 | Internal; conditional total | Local transfer/reset only; no accumulator observation |
| Account accumulation | §6.4; R-13–R-15 | Internal; conditional total | Card-change trigger; no final EOF account total |
| Grand accumulation | §6.4; R-14/R-15 | Internal; conditional total | No reconciliation |
| Reporting control/presentation | §6.4; R-16 | Internal | No twenty-detail guarantee or API pagination |
| Report output | §6.4; R-13–R-16/R-18/R-20 | C-7/C-8/D-15–D-17 | Empty observation is not complete empty report |
| Transaction backup | §6.5; R-19/R-20 | External; all three tracks | No reset facility |
| Combined intermediate | §6.5; R-19/R-20 | External; posting/interest | No completed merged state |
| Master lifecycle context | §6.5; R-19/R-20 | External; all three tracks | No confirmed shared live instance |
| Procedure control | §6.5; R-19 | External/unavailable | Missing `REPROCT` remains unresolved |
| External failure routine | §6.5; R-18 | External/unavailable | No termination, return, or rollback guarantee |

Posting update order and output-open effects, interest transition updates, and reporting conditional finalization are not changed by observed empty sequences. Failure still does not imply absent earlier effects.

## Section 6: Traceability Matrix

Field and outcome tables above are integral to this matrix.

| Contract element | Canonical element / treatment | Rule | Decision |
|---|---|---|---|
| C-1–C-3 | Stage 5 operation boundaries/external sequences | R-1/R-7/R-11/R-12/R-19 | D-2/D-9/D-14 |
| C-4 | Internal state, operational context, bounded exclusions | R-4–R-11/R-16/R-19/R-20 | D-3/D-4/D-7/D-8 |
| C-5 | Candidate, transaction, rejection, progress | R-1–R-6 | D-5/D-10/D-11 |
| C-6 | External interest bases/generated transaction | R-7–R-11 | D-3/D-5/D-10/D-11 |
| C-7/C-8 | Reporting bases/header/detail/totals | R-12–R-17 | D-5–D-7/D-10/D-11 |
| C-9 | Structural proposal over licensed participation | R-1/R-7/R-12 | D-5/D-10/D-14 |
| C-10/C-11 | Ordered attempts/omitted finalization | R-4–R-8 | D-4/D-6 |
| C-12/statuses/error category | Conditional content/failure distinction | R-1/R-6/R-9/R-13/R-18 | D-4/D-13/D-16 |
| C-13/C-14 | Stage 5 §6 resource/repetition limits | R-6/R-18–R-20 | D-2–D-4 |
| `availability`, `items`, `value` | Conditional output/progress participation | R-3/R-6/R-11/R-14/R-16/R-18 | D-10/D-15/D-17 |
| `track` | Separate mandatory track attribution | R-19; Stage 5 D-2 | D-9/D-15 |
| `completeness`, `durability` | Scoped non-guarantees | R-6/R-8/R-12/R-15/R-18 | D-4/D-6/D-16 |
| `kind` and mixed record union | Ordered header/detail/total content | R-13–R-16 | D-7/D-10/D-15 |
| Empty available sequence permitted under 200 | Conditional output representation, not complete zero-output guarantee | R-3/R-6/R-10–R-12/R-15/R-16 | Revised D-16; r3 feedback |
| All-unavailable/no-observation barred from 200 | Missing observation does not satisfy output obligations | R-3/R-6/R-11/R-14/R-16/R-18 | D-16/D-17 |
| Zero-count progress-only 200 | Progress remains distinct from outputs | R-1/R-6 | D-16/D-17 |
| Optional error `availableContent` | Available observations despite known failure | R-6/R-13/R-14/R-18 | D-13/D-15/D-16 |
| Nonpublic canonical types | Internal/descriptive outcomes and dependencies | R-4–R-18 | D-3/D-12 |

### Narrow Revision Grounding

| Revised passage | Source-grounded constraint | Consequence |
|---|---|---|
| D-16 and §3.4 interest empty sequence | R-10; `app/cbl/CBACT04C.cbl:214-217`, `462-515` | Zero-rate bypass is not rejection; zero computed quantity remains transaction content when generation is selected |
| D-16 and §3.4 reporting empty sequence | R-12/R-15; `app/cbl/CBTRN03C.cbl:170-243`, `293-322` | Empty observation does not repair filtering or certify totals/finalization |
| §3.4 posting progress | R-1/R-6; `app/cbl/CBTRN02C.cbl:202-230`, `424-579` | Zero counts remain progress only; no no-effects or output-fulfillment inference |
| §5.2/§7.3 status boundary | Stage 5 D-4/D-6 and §5; both r3 feedback records | Known failure: 500; no observation/no known failure: 503; available empty observation: eligible for 200 |

These anchors resolve to the exact original and derived pins in `input_pins.source_bodies`. No new E-n or R-n is created.

## Section 7: Reverse-Completeness Matrix — Contract Destination

| Operation / rule / effect | Evidence | Semantic representation | Stage 5 boundary treatment | Contract destination / justified exclusion / gap |
|---|---|---|---|---|
| Posting selection | E-4/E-7 | R-1 | Candidate/rejection/progress; flags internal | C-1/C-5; no selection telemetry |
| Posting precedence | E-7/E-8/E-20/E-21/E-27 | R-2 | Selected rejection/internal checks | C-5; 100–103 and overwrite precedence; G-22 for stronger domains |
| Transaction versus rejection | E-4/E-9/E-26/E-27 | R-3 | Distinct types; filler excluded | C-5/§3.4; D-8 excludes invented byte/filler meaning |
| Category accumulation | E-9/E-10/E-22 | R-4 | Internal state/attempt distinction | C-10/§5.4; no category API |
| Account arithmetic/reason 109 | E-7/E-9/E-10/E-20 | R-5 | Internal signed changes; later reason distinct | C-5/C-10; 109 not preliminary rejection |
| Posting completion/failure | E-7/E-9–E-11/E-29 | R-6 | Progress/ordered attempts; durability gap | C-10/C-12; observed zero progress permitted but not output fulfillment; G-23 |
| Interest transitions | E-5/E-12/E-13/E-20–E-22 | R-7 | External category basis/internal grouping | C-2/C-6/§5.4; no update receipt |
| Interest normal EOF | E-12/E-14 | R-8 | No final flush; repair excluded | C-11; empty output does not attest final account state |
| Disclosure fallback | E-12/E-13/E-23 | R-9 | Internal dependency/selection | C-6; missing not zero; no fallback trace |
| Interest selector/quantity | E-5/E-12/E-14/E-22/E-23 | R-10 | Computed amount/internal accumulator/numeric gap | C-6; zero amount distinct from zero rate; observed empty allowed; G-22 |
| Generated transaction/fee limit | E-5/E-14/E-26/E-30 | R-11 | Parameter/output; internal suffix; fee exclusion | §3.2/C-6; no global uniqueness or fee; available empty not forced to 503 |
| Reporting date gate/exit | E-6/E-16/E-26 | R-12 | Date basis/internal EOF/storage gap | C-3/C-8; empty records allowed without complete-empty claim; G-24 |
| Reporting grouping/lookups | E-6/E-16/E-18/E-21/E-24/E-25 | R-13 | Detail association/internal card grouping | C-8/D-15; no account cardinality |
| Reporting totals | E-6/E-16–E-18/E-28 | R-14 | Distinct totals/internal accumulators | `ReportTotal` occurrences retained; missing not zero |
| Reporting EOF finalization | E-16/E-17 | R-15 | Conditional; repair excluded; numerical gap | C-8; no final account total or unconditional duplication; G-24 |
| Report presentation | E-6/E-17/E-18/E-24–E-26/E-28 | R-16 | Header/detail/bounded receivers; mechanics internal | C-7/C-8; ordering/multiplicity retained; separators/counters excluded |
| Two date sites | E-16/E-31/E-34 | R-17 | Separate documentary bases/configuration gap | External; no common override or complete intersection; G-24 |
| External failure semantics | E-11/E-15/E-19 | R-18 | Internal diagnostics/external gap | C-12/C-13; known failure 500, no universal response guarantee; G-23 |
| Operational resources | E-29–E-34 | R-19 | External context/identity and schedule gaps | C-4/§5.4; no cycle, backup, or combination surface |
| Repetition | E-5/E-9–E-12/E-14–E-19/E-32–E-34 | R-20 | Unknown per track | C-14 separately for posting, interest, reporting |

No rule is dismissed as wholly inapplicable. Each retains a contract destination, internal/external treatment, bounded exclusion, or gap.

### 7.1 Evidence and Review Inheritance

Stage 5 §7.2 retains the remaining evidence dispositions:

- E-1–E-3 are track orientation, not additional operations.
- E-4–E-28 support the mapped types, fields, state, and outcomes.
- Declaration-only account/customer fields and filler remain excluded under D-8 without claiming absent bytes.
- E-32 retains posting/interest consumers; E-33/E-34 retain all three without merged live resource identity.
- E-35 remains non-semantic licensing context under A-6; no fabricated business rule or legal-clearance guarantee.

Both Stage 5 attachments remain inherited review evidence. Their findings do not establish exhaustive completeness, runtime outcomes, or approval of r3.

### 7.2 Ambiguity Propagation

| Ambiguity | Retained consequence |
|---|---|
| A-1/A-8 | Final business cohesion, cross-track identity, and chronology remain unresolved |
| A-2/A-16 | Dependency closure and executable job flow remain external/unresolved |
| A-3 | Deployed encoding/conversion remains unresolved; G-22 |
| A-4/A-10/A-17 | Durable effects, isolation, external behavior, and universal response remain unestablished; G-23 |
| A-5/A-6 | No independent-clean-context or legal-clearance claim |
| A-7 | Upstream evidence layout remains addressed, unchanged |
| A-9 | Static precedence/109 timing retained; no intended-policy invention |
| A-11 | Normal EOF no-final-flush deduction retained |
| A-12 | Numeric, temporal, parameter, overflow, and identifier lifetime limits retained; G-22 |
| A-13 | Fee absence remains local and bounded |
| A-14/A-15 | Date/EOF, grouping, totals, and presentation uncertainty retained; G-24 |

Permitting an observed empty representation resolves no underlying runtime ambiguity.

### 7.3 G-21–G-24 Revision Disposition

| Gap | Concrete proposal retained or revised | Residual blocking scope |
|---|---|---|
| G-21 — Participation | D-14 retains required empty-object requests and track-specific external/internal accountability | A clause promising input-instance selection, provisioning, readiness, availability, EOF delivery, or runtime binding would require unsupported authority |
| G-22 — Schemas/validation | D-10/D-11/C-9 retain concrete structural choices | Faithful representation that requires invented encoding, rounding, domain, padding, date policy, or unknown field values remains blocked |
| G-23 — Response boundary | **Revised:** observed empty sequences qualify as observations; all-unavailable/no-observation does not qualify for 200; known failure uses 500; no observation/no known failure uses 503 | Universal output delivery, guaranteed observation/detection, complete attempt traces, and durable completion remain blocked |
| G-24 — Reporting finalization | **Revised:** empty available records may be represented without 503; ordering and source-labelled totals remain | Complete empty report, full-range processing, reconciled/zero missing totals, final account total, known EOF storage, and executed job flow remain unsupported |

The r2 empty-observation representation contradiction is addressed by a proposed documentary revision, **not by human gap closure**. Positively representing an empty observed sequence no longer requires future semantic authority merely because the array is empty.

Authority is still absent for claiming that the observation exhausts underlying output or identifies its cause. Those stronger claims remain blocked.

Inherited G-17–G-19 continue to delimit value, state, and reporting guarantees. Pending review of legitimate representation choices is not treated as missing COBOL evidence. No blocker is silently erased by `unavailable`, `unknown`, or `not_attested`.

## Completeness Gate and Entry Condition

All conditions remain unchecked:

- [ ] Posting, interest, and reporting retain separate substantive coverage.
- [ ] Exact capability identity, upstream versions, original pins, source text, and numbered representations remain retained.
- [ ] The unapproved r2 artifact and both r3 feedback records remain explicit revision inputs.
- [ ] All canonical operations have contracts; no extra surface lacks D-n authority.
- [ ] All 17 canonical types and their fields have public, external, internal, or justified excluded treatment.
- [ ] All Stage 5 outcome variants retain their guards and observability limits.
- [ ] External-input responsibility remains unchanged; no provisioning, selector, singleton, or EOF invention.
- [ ] Available empty sequences are distinct from unavailable observations.
- [ ] Zero rate, zero computed quantity, missing disclosure, and technical failure remain distinct.
- [ ] Interest/reporting observed empty sequences are not forced into 503 or business rejection.
- [ ] Posting zero-count progress-only 200 is progress only, not output fulfillment, exhaustion, no-effects, or durability.
- [ ] All-unavailable/no-observation envelopes are excluded from 200.
- [ ] Known technical failure maps to proposed 500, optionally retaining available empty or nonempty observations.
- [ ] Available content order and multiplicity remain preserved.
- [ ] Empty reporting records do not certify complete empty reports, full-range processing, zero/reconciled totals, or final account totals.
- [ ] Every state/reset requirement has a clause or explicit external/unsupported treatment.
- [ ] Failure effects and repetition limits are derived, not invented.
- [ ] All R-1–R-20 have reverse-complete dispositions.
- [ ] Review records risk-oriented passages, objections, conclusions, and clause/exclusion/gap dispositions.
- [ ] Review states that sampled checks do not prove completeness.
- [ ] Remaining blocking guarantees and representation limits receive explicit external disposition.
- [ ] Exact r3 artifact and review versions are retained and pinned.
- [ ] Human review decision is recorded externally.

### Provenance and Current Status

AI assistance is limited to this versioned Stage 6 requirements draft using the supplied approved chain, authorizations, both Stage 5 attachments, unapproved r2, both new feedback records, source text and numbered representations, and generic template/rules.

No tools, additional model/network calls, compilation, COBOL execution, source repair, implementation, generated code, or OpenAPI generation were performed. No E1/E2 content or comparison is included. No later-stage artifact or realization behavior is specified.

Filesystem persistence, provider retention settings such as `store=false`, usage, cost, and generation telemetry are not certified by this document. Unavailable values are not reported as zero.

**Stage 6 r3 remains unapproved. No gate is approved. Ready for implementation remains `false`.**
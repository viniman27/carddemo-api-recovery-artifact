# Adapter Behavior Specification

## Purpose

This Stage 7 r2 specification documents proposed adapter behavior for the AWS CardDemo public cycle in run `E3-01`, subordinate to the approved/current Stage 6 r3 contract.

**Posting, interest, and reporting remain mandatory, separately traceable tracks.** Their order in this document is contract-document order, not an execution schedule.

| Attribute | Value |
|---|---|
| Run | `E3-01` |
| Stage | `7` |
| Feature | `adapter-behavior-carddemo-r2` |
| Artifact | `specs/adapter-behavior-carddemo-r2/requirements.md` |
| Exact inherited capability identity | `unselected-stage-1-scope-only` |
| Immediate upstream | `specs/api-contract-carddemo-r3/spec.json` |
| Revision of | `adapter-behavior-carddemo` |
| Revision character | Narrow, human-directed documentary revision; not an independent replica |
| Status | Proposed documentary adapter behavior |
| Human approval | `false` |
| Completeness gate passed | `false` |
| Ready for implementation | `false` |

This revision specifies internal invocation, resource, capture, conversion, failure, state, and response-association records. These are **documentary responsibilities**, not new public schemas, implemented instrumentation, or fabricated populated evidence.

No runtime binding, capture facility, resource availability, reset, isolation, durable effect, or completed execution is demonstrated here.

## Adapter Integrity Discipline

- The adapter realizes the contract; it never reinterprets it. Any needed deviation requires upstream revision, not an adapter workaround.
- The unchanged legacy remains responsible for business rules. The adapter does not repeat preliminary checks, calculate interest, reconstruct reports, compensate effects, or repair finalization.
- Source and copybooks remain read-only. Generic permission for environment preparation does not authorize preparation in this task.
- Stage 6 r3 governs public representation; Stage 5 governs canonical meaning and state scope; Stage 4 governs semantic rules; Stage 3-r2 supplies documentary evidence.
- A documented source statement is not an executed event. A proposed evidence record is not a populated runtime record.
- Unknown is not false; unavailable is not zero; a stale or damaged capture is not empty business output.
- Required provenance must not become an excuse to discard known licensed content.
- No implementation technology, process topology, provisioning mechanism, selector, readiness service, retry policy, or state lifecycle guarantee is selected.
- All new internal responsibilities below remain proposed until externally reviewed. Documentary closure means the responsibility has been specified, not that a gate or runtime obligation has passed.

## Section 1: Upstream Authority and Entry Condition

### 1.1 Upstream Authority and Scope Inheritance

The entry basis is the supplied approved chain: Stages 1, 2-r2, 3-r2, 4, 5, and Stage 6 r3, with their authorizations and review attachments.

| Current artifact, relative to `RUN_ROOT` | Supplied SHA-256 |
|---|---|
| `specs/pipeline-scope-carddemo/requirements.md` | `1362fab5d55b77ef6121328606ae974295cd5723849520e9a246f4bd45e64cc9` |
| `specs/capability-selection-carddemo-r2/requirements.md` | `abdb59180f379d9e14eb86dfa1d8226ec50c981346767e808fd382eb7462bbc4` |
| `specs/legacy-evidence-carddemo-r2/requirements.md` | `4566786600b60e9377c1e369e67765098d06b0153ba973361d2065614a6c9b7b` |
| `specs/capability-semantics-carddemo/requirements.md` | `2f9d3ee52dd7788e206810e38c9173b19d21dfc44270cdd06d05e62dec95eb93` |
| `specs/canonical-data-boundary-carddemo/requirements.md` | `208d04fe6f9cae665dfa4cb514de5d4ad9eaf0ebc169dfae0fd8a6ba209e66f3` |
| `specs/api-contract-carddemo-r3/requirements.md` | `6cba102f8335843b46e75a77b1a71d4e56373a95d5ac63cf645491556c443b27` |

| Immediate authority or review | Supplied SHA-256 |
|---|---|
| `specs/api-contract-carddemo-r3/spec.json` | `2ec40d54f4d89198ccc9e0cac602ba4192ee063290d9f226c0b1ac101899a0bd` |
| `reviews/stage-6-r3-authorization.json` | `0c5228634cb0f3b3c779fafe2e7e9ae5109aebeb24b116268e73a9a00dd8213e` |
| `STAGE6-R3-COUNTEREXAMPLE-REVIEW.md` | `a8e41764b56018f530a2df96d75bff483086e84b2462fca156175b0f91be7159` |
| `specs/api-contract-carddemo-r3/stage6-r3-verification.json` | `69a59af451a700f8de1d4711f64149ce5bd295ced79bcee1747caf2aefee0193` |

The subsequent Stage 6 r3 authorization establishes current upstream approval without rewriting historical draft-era statements. Its scope authorizes documentary Stage 7 behavior only. The supplied `current` gate-check result is inherited freshness information, not a check performed here.

Where review summaries use imprecise shorthand, the approved contract and source-grounded rules govern: reason 109 is **not preliminary rejection**, and the interest envelope property is `outputs`. No review shorthand changes either boundary.

#### Revision provenance

The following inputs remain separate historical objects; none is approved or modified by this document.

| Revision input | Supplied SHA-256 |
|---|---|
| `specs/adapter-behavior-carddemo/spec.json` | `f561dbeb8c7be74057b98c6e502b82331d684a35b847481f55c2db5cf4ed1e5e` |
| `specs/adapter-behavior-carddemo/requirements.md` | `0125e68e65e38c703e89b0c1b843358da91a5281e20860fb7f59316d3286ecf4` |
| `prepared/adapter-behavior-carddemo/execution/scope-original.md` | `0125e68e65e38c703e89b0c1b843358da91a5281e20860fb7f59316d3286ecf4` |
| `prepared/adapter-behavior-carddemo/execution/response.sse` | `93eb1f0e2ccf447726768f0ce9dfe242a7965434afc01205b03ef3b2b9b9f262` |
| `prepared/adapter-behavior-carddemo/request.json` | `4aba5f791186c4f5cbbd59495b29dbecfc98b1510d46ec545fda168d80ff2b0a` |
| `prepared/adapter-behavior-carddemo/metadata.json` | `a89793d73e1020854af4020f3b617e9528aa85021488f23edd9bd215cf541d12` |
| `stage7-generation-authorization.json` | `0f2e743439454a617121cd1c9adccbe3a11b179f9bca2c3194a537fc4cdc7a5d` |
| `reviews/stage-7-r1-directed-feedback.md` | `960aae5144215cc64dd6f47acb883dd41aecad7d94a45d9cd66f4477ed0a3cc5` |
| `STAGE7-DESIGN-EVIDENCE-REVIEW.md` | `9eeb4f3e46506f1ac185331a42ee26c7f2cfccc424239073a42fbb6d9e17a505` |

The feedback bodies are retained verbatim as supplied revision inputs, not translated replacements or newly authored authorizations. Raw/request/metadata records supplied by pin are referenced as provenance; their unsupplied bodies are not reconstructed.

#### Complete pin and corpus retention

The exact supplied `input_pins` register is incorporated without alteration, including:

- Six upstream metadata pins, six artifact pins, and six authorizations.
- Five review attachments, including Stage 4 and both Stage 5 attachments.
- Eight Stage 6 revision-history entries.
- Seven original Stage 7 provenance entries and both revision-feedback entries.
- All 19 original corpus pins and their separate derived-representation pins.
- Source-package and all 13 framework pins.

The governing template is `settings/templates/pipeline/adapter-behavior-spec.md`, SHA-256 `4a563f2bbb4db976c614cff722a90934041df3b76db0c3695386970871b47687`.

The source-package pin remains `63ba5c47ecb21349549744b912af3b150654e7e435724dba499e3c88369f15a2`.

Every corpus citation resolves by full path to the supplied exact `content`, stable 1-based `numbered_lines`, original-file hash, and separate derived hash. All 19 entries remain retained; no condensed table substitutes for their bytes. No checksum, filesystem, or mechanical-anchor verification is claimed.

### 1.2 Inherited Constraints and Decisions

| Public contract area | Stage 7 r2 treatment | Public change |
|---|---|---|
| C-1–C-3: operations | `POST /posting`, `POST /interest`, `POST /reporting`, separately mapped | None |
| D-14/C-9: requests | Required empty closed objects; no business properties, null substitute, selector, or EOF | None |
| C-5–C-8: content | Exact components, fields, requiredness, strings/integers, and enums retained | None |
| D-15: sequences | Posting streams separate; reporting mixed records; order and duplicates retained | None |
| Revised D-16 | Positive empty observations qualify; all-unavailable does not | None |
| C-12: statuses | 200/400/500/503 and existing categories retained | None |
| C-13/C-14 | Durability, reset, isolation, and repetition guarantees remain absent | None |
| C-4/D-12 | Internal records do not become public fields or operations | None |
| Stage 5 D-5–D-8 | No conversion-policy invention, repair, reconstructed totals, or extra business meanings | None |

## Section 2: Adaptation Model

### 2.1 Adaptation Strategy

The proposed strategy is wrapping the unchanged legacy, with internal documentary accountability for binding and represented observations.

Responsibility roles below do not select actual personnel or deployed components:

- **Consumer:** supplies only the called operation and its existing request representation.
- **External setup owner:** identifies and accounts for resources, parameter supply, preparation provenance, and any externally established availability evidence.
- **Adapter boundary responsibility:** associates the request, invocation, resource context, observations, conversions, and response.
- **Legacy core:** performs the existing business behavior.
- **External human reviewer:** decides documentary acceptance against exact retained versions.

No executable reference layer is supplied. A reference layer cannot be invented as an observation source.

#### Internal evidence records

These record names are local documentary labels, not new E-n evidence items or public schemas. Each actual record would distinguish supported values from unavailable information; none is populated with invented runtime values here.

| Record | Required documentary contents | Responsibility and boundary |
|---|---|---|
| **INV — Invocation record** | Run and exact capability identity; track; internal invocation identity; called contract clause/operation; request-representation evidence; source/runtime binding reference; resource-record links; setup owner; intended observation scope and validity window; actual start/end evidence or unavailable; capture channels; response association | Adapter boundary associates; external setup supplies binding facts. Internal identity is not an idempotency key or receipt |
| **RES — Resource/setup record** | Track; source-local logical name; actual instance identity or unresolved; role/access mode; supplying owner; preparation origin and version; content/generation identity where established; validity window; declared prerequisites and evidence supporting their satisfaction or unknown; reuse/shared-state attribution; missing dependencies | External setup owner supplies facts; adapter must not invent preparation or readiness |
| **CAP — Capture/observation record** | Invocation/resource links; channel and producer; raw evidence reference and actual digest when available; capture scope/start/end; freshness attribution; framing/layout basis; capture condition; represented occurrences and positions; cardinality only if justified; exclusions; empty-observation basis; uncertainty and response destinations | Acquisition responsibility records actual evidence, not source-predicted events |
| **CONV — Field conversion record** | Contract clause/component/field; CAP occurrence and raw field span; source path/pins/line; physical declaration; deployed encoding/sign/framing basis; observed width/padding; proposed or applied mapping; output value; known loss; representability decision and unresolved conflict | Each represented field requires its own attributable mapping |
| **FAIL — Failure-boundary record** | Invocation/channel; raw event and location; event origin; attribution/freshness; time/order known to response boundary; meaning authority; distinction between source, hosting, capture, and representation failure; known versus unestablished assessment; retained observations; selected existing error category | A source error branch alone does not establish actual failure |
| **STATE — State-scope record** | Invocation/resource links; local versus persistent state; preparation/shared/reuse claims and evidence; initial authority; lifetime known or unknown; reset/isolation evidence separately; attempted versus observed versus durable effects; restart/repetition limits | No state-management facility or persistence guarantee |
| **RESP — Response-association record** | Contract version; INV link; structural decision; per-channel CAP/CONV disposition; FAIL assessment; exact existing envelope/error fields; occurrence-to-array-index mapping; unavailable reasons internally; status rationale; unresolved gaps | Records why representation is justified; adds no public metadata |

Unknown record contents remain explicitly unknown internally. Missing provenance does not become a default resource, timestamp, successful invocation, count of zero, or failure diagnosis.

#### External input and dependency accountability

| Track | External setup responsibility | Legacy-internal dependencies | Unknown/EOF limits |
|---|---|---|---|
| posting | Daily candidate sequence and values; actual bindings for daily, transaction, reject, xref, account, category resources | Preliminary checks; account/category changes; reason/flags/counts; timestamp construction | Input instance, contents, order, availability and end condition not conveyed by request |
| interest | Encountered category sequence; identifier parameter; actual category/account/xref/disclosure/output bindings, including alternate-key context | Account transitions; disclosure fallback; arithmetic; suffix; timestamps | Parameter validity, actual grouping, alternate-key multiplicity, availability and EOF unresolved |
| reporting | Transaction sequence; separate date input; provenance of any upstream selected input; lookup/report bindings | Card-based grouping; lookups; accumulators; presentation; date/EOF control | Actual dates/order, upstream flow, date-input EOF and failed-read storage unresolved |

Documentary binding anchors are `app/jcl/POSTTRAN.jcl:23-42`, `app/jcl/INTCALC.jcl:22-41`, and `app/jcl/TRANREPT.jcl:37-80`. They identify intended resource relationships, not live instances. The interest parameter literal is not an adapter default.

### 2.2 Semantic Authority Statement

INV/RES specify **what must be attributable**; CAP/CONV specify **what may be represented**; FAIL/RESP specify **what the response boundary actually knows**; STATE prevents observation from becoming an unsupported state claim.

These responsibilities derive from C-1–C-14, D-10–D-17, and the directed revision feedback. They do not redefine R-1–R-20.

#### Observation admissibility and capture conditions

A represented observation requires:

1. Attribution to the invocation and relevant resource/channel.
2. A supported observation scope and freshness basis.
3. Sufficient framing and field evidence for the represented content.
4. Supported occurrence order and multiplicity.
5. Recorded treatment of gaps, exclusions, and known capture damage.
6. A response association that does not overstate capture scope as business completeness.

| Capture condition | Documentary meaning | Representation responsibility |
|---|---|---|
| Positive nonempty observation | Actual attributable canonical occurrences are supported | Represent those occurrences faithfully; retain duplicates and order |
| Positive empty observation | Actual attributable observation establishes no canonical occurrences within a justified represented scope | Available `items: []`; no complete-business-output claim |
| Zero-length capture | Evidence object has zero length; observation success/scope not established by that fact | Inconclusive evidence state; not automatically empty |
| Truncated capture | Evidence is incomplete, cut off, or has unresolved framing/field loss | Never infer empty. Preserve independently justified complete occurrences; register damaged/unrepresentable content |
| Stale capture | Evidence belongs to another invocation/window or freshness cannot support current attribution | Not current-call content; retain internally as stale evidence |
| Failed capture | Actual capture failure is evidenced | Assess FAIL; do not equate capture failure with legacy failure or empty output |
| Absent/unavailable capture | No suitable evidence is represented | Unavailable observation; not zero and not automatically known technical failure |

A positive-empty CAP record must identify the source scope, successful observation/framing basis, and why zero canonical occurrences is established rather than inferred from silence. A zero-byte object may accompany that evidence but cannot supply it alone.

A capture boundary is not a legacy EOF or completion marker. This document invents neither a marker nor a concrete capture mechanism.

Truncation does not authorize silent deletion of known content. Independently attributable complete occurrences may remain represented under `completeness: "not_attested"`; unrepresentable known records remain explicit internal conflicts. If conversion would require changing the public contract, G-27 remains open rather than being hidden by an empty array.

#### Field-by-field provenance and conversion discipline

All fields below require CONV records. PIC widths are source declarations, **not new public length/range validation**. Physical byte offsets, deployed encoding, sign encoding, and record framing require actual binding evidence; they are not inferred from the supplied UTF-8 source representation.

For text, retain receiver content without silent trimming, padding replacement, calendar parsing, or description restoration. For numeric content, any decimal decoding must document sign and implied-decimal interpretation without rounding or recomputing business quantities. Unknown conversion authority remains G-27.

##### Transaction and original-candidate fields

The table applies separately to:

- Posting output: actual `TRAN-RECORD` observation, `app/cpy/CVTRA05Y.cpy:5-17`.
- Posting rejection candidate: actual daily portion of the rejection, `app/cpy/CVTRA06Y.cpy:5-17`.
- Interest output: actual generated `TRAN-RECORD`, not reconstruction from input or literals.

| Represented field | Transaction source | Rejection candidate source | Declared representation |
|---|---|---|---|
| `transactionId` | `TRAN-ID` | `DALYTRAN-ID` | X(16) |
| `typeCode` | `TRAN-TYPE-CD` | `DALYTRAN-TYPE-CD` | X(02) |
| `categoryCode` | `TRAN-CAT-CD` | `DALYTRAN-CAT-CD` | 9(04) |
| `source` | `TRAN-SOURCE` | `DALYTRAN-SOURCE` | X(10) |
| `description` | `TRAN-DESC` | `DALYTRAN-DESC` | X(100) |
| `amount` | `TRAN-AMT` | `DALYTRAN-AMT` | S9(09)V99 |
| `merchantId` | `TRAN-MERCHANT-ID` | `DALYTRAN-MERCHANT-ID` | 9(09) |
| `merchantName` | `TRAN-MERCHANT-NAME` | `DALYTRAN-MERCHANT-NAME` | X(50) |
| `merchantCity` | `TRAN-MERCHANT-CITY` | `DALYTRAN-MERCHANT-CITY` | X(50) |
| `merchantPostalText` | `TRAN-MERCHANT-ZIP` | `DALYTRAN-MERCHANT-ZIP` | X(10) |
| `cardReference` | `TRAN-CARD-NUM` | `DALYTRAN-CARD-NUM` | X(16) |
| `originalTimestamp` | `TRAN-ORIG-TS` | `DALYTRAN-ORIG-TS` | X(26) |
| `processingTimestamp` | `TRAN-PROC-TS` | Not a candidate field | X(26) |
| `suppliedProcessingTimestamp` | Not an output transaction field | `DALYTRAN-PROC-TS` | X(26) |

Posting construction is anchored at `app/cbl/CBTRN02C.cbl:424-442`; rejection assembly at `app/cbl/CBTRN02C.cbl:446-465`; interest construction at `app/cbl/CBACT04C.cbl:473-515`.

Interest source literals, zero/space merchant assignments, suffix construction, and timestamps explain provenance but do not establish emitted values without capture. Filler has no public destination and must not be used to fill missing values.

| Additional posting field | Acquisition/source | Mapping limit |
|---|---|---|
| `PostingRejection.candidate` | Observed rejection’s daily-record portion | Apply every candidate row above, preserving original context |
| `PostingRejection.reason` | Observed four-digit trailer reason; `app/cbl/CBTRN02C.cbl:180-182`, `446-451` | Decode supported numeric representation to existing `"100"`–`"103"` enum; record representation conversion explicitly; never admit 109 |
| `PostingRejection.description` | Observed 76-character trailer description | No replacement with a model-generated message or a lookup label |
| `processedRecordCount` | Actual display of `WS-TRANSACTION-COUNT`, declared 9(09) | `app/cbl/CBTRN02C.cbl:185`, `227`; integer representation, not array-derived count |
| `preliminaryRejectCount` | Actual display of `WS-REJECT-COUNT`, declared 9(09) | `app/cbl/CBTRN02C.cbl:186`, `228`; not durable reject count |

##### Reporting fields

Every row is acquired from actual emitted report content, not from source literals, input records, lookup files, or recalculated totals.

| Component.field | Physical receiver/source | Declared representation and loss boundary |
|---|---|---|
| `ReportHeaderContext.reportShortNameText` | `REPT-SHORT-NAME`, `app/cpy/CVTRA07Y.cpy:5-6` | X(38); preserve observed padding |
| `ReportHeaderContext.reportLongNameText` | `REPT-LONG-NAME`, `app/cpy/CVTRA07Y.cpy:7-8` | X(41); no synthesized header occurrence |
| `ReportHeaderContext.startText` | `REPT-START-DATE`, `app/cpy/CVTRA07Y.cpy:11` | X(10); no date normalization |
| `ReportHeaderContext.endText` | `REPT-END-DATE`, `app/cpy/CVTRA07Y.cpy:13` | X(10); no default range |
| `ReportDetail.transactionId` | `TRAN-REPORT-TRANS-ID`, `app/cpy/CVTRA07Y.cpy:16` | X(16) |
| `ReportDetail.accountReference` | `TRAN-REPORT-ACCOUNT-ID`, `app/cpy/CVTRA07Y.cpy:18` | X(11); preserve receiver, not inferred account grouping |
| `ReportDetail.typeCode` | `TRAN-REPORT-TYPE-CD`, `app/cpy/CVTRA07Y.cpy:20` | X(02) |
| `ReportDetail.typeDescription` | `TRAN-REPORT-TYPE-DESC`, `app/cpy/CVTRA07Y.cpy:22` | X(15), versus X(50) lookup; do not restore lost text |
| `ReportDetail.categoryCode` | `TRAN-REPORT-CAT-CD`, `app/cpy/CVTRA07Y.cpy:24` | 9(04); record supported string conversion |
| `ReportDetail.categoryDescription` | `TRAN-REPORT-CAT-DESC`, `app/cpy/CVTRA07Y.cpy:26` | X(29), versus X(50) lookup; no restoration |
| `ReportDetail.source` | `TRAN-REPORT-SOURCE`, `app/cpy/CVTRA07Y.cpy:28` | X(10) |
| `ReportDetail.amountText` | `TRAN-REPORT-AMT`, `app/cpy/CVTRA07Y.cpy:30` | `-ZZZ,ZZZ,ZZZ.ZZ`; retain observed sign, spaces, punctuation and bounded display |
| `ReportTotal.label` | Attributable page/account/grand record identity, `app/cpy/CVTRA07Y.cpy:50-66` | Map identified source label to existing enum only |
| `ReportTotal.valueText` — page | `REPT-PAGE-TOTAL`, `app/cpy/CVTRA07Y.cpy:54` | `+ZZZ,ZZZ,ZZZ.ZZ`; no recalculation |
| `ReportTotal.valueText` — account | `REPT-ACCOUNT-TOTAL`, `app/cpy/CVTRA07Y.cpy:60` | Same display boundary; no invented account identifier |
| `ReportTotal.valueText` — grand | `REPT-GRAND-TOTAL`, `app/cpy/CVTRA07Y.cpy:66` | Same display boundary; not a reconciled global total |

Occurrence sources are `app/cbl/CBTRN03C.cbl:293-341`, `343-374`. The header maps the emitted report-name/header context; column labels, blank lines, and separators remain excluded presentation mechanics. CAP must account for exclusions rather than misclassifying them as missing canonical records.

##### External component fields and internal dependencies

These fields remain external descriptions, **not request properties**.

| Component.field | Source/provenance | Supplier |
|---|---|---|
| `InterestCategoryBasis.accountReference` | `TRANCAT-ACCT-ID`, 9(11), `app/cpy/CVTRA01Y.cpy:6` | External category sequence |
| `InterestCategoryBasis.typeCode` | `TRANCAT-TYPE-CD`, X(02), `app/cpy/CVTRA01Y.cpy:7` | Same |
| `InterestCategoryBasis.categoryCode` | `TRANCAT-CD`, 9(04), `app/cpy/CVTRA01Y.cpy:8` | Same |
| `InterestCategoryBasis.categoryBalance` | `TRAN-CAT-BAL`, S9(09)V99, `app/cpy/CVTRA01Y.cpy:9` | Same |
| `InterestIdentifierBasis.parameterText` | `PARM-DATE`, X(10), `app/cbl/CBACT04C.cbl:175-180` | External parameter authority |
| `ReportingTransactionBasis.transactionId` | `TRAN-ID`, X(16), `app/cpy/CVTRA05Y.cpy:5` | External reporting transaction sequence |
| `ReportingTransactionBasis.cardReference` | `TRAN-CARD-NUM`, X(16), `app/cpy/CVTRA05Y.cpy:15` | Same |
| `ReportingTransactionBasis.typeCode` | `TRAN-TYPE-CD`, X(02), `app/cpy/CVTRA05Y.cpy:6` | Same |
| `ReportingTransactionBasis.categoryCode` | `TRAN-CAT-CD`, 9(04), `app/cpy/CVTRA05Y.cpy:7` | Same |
| `ReportingTransactionBasis.source` | `TRAN-SOURCE`, X(10), `app/cpy/CVTRA05Y.cpy:8` | Same |
| `ReportingTransactionBasis.amount` | `TRAN-AMT`, S9(09)V99, `app/cpy/CVTRA05Y.cpy:10` | Same |
| `ReportingTransactionBasis.processingTimestamp` | `TRAN-PROC-TS`, X(26), `app/cpy/CVTRA05Y.cpy:17` | Same |
| `ReportingDateBasis.startText` | `WS-START-DATE`, X(10), `app/cbl/CBTRN03C.cbl:122-125`, `220-243` | External date resource |
| `ReportingDateBasis.endText` | `WS-END-DATE`, X(10), same anchors | External date resource |

Account, xref, category, disclosure, and description dependencies retain their approved copybook identities through E-20–E-25. Their fields are not independently exposed or consumer-supplied. `AttemptState` types, disclosure selection, suffix, grouping control, and upstream selection context remain nonpublic.

##### Envelope and error-field provenance

| Existing field | Documentary origin |
|---|---|
| `track` | Called operation in INV; not inferred from a filename |
| `completeness` | Exact contract constant `not_attested`; not measured completion |
| `durability` | Exact contract constant `unknown`; not a false-valued durability result |
| `outputs`, `rejections`, `records` | Track-specific CAP channels and occurrence mapping |
| `availability` | CAP admissibility determination, not source file status |
| `items` | Ordered represented occurrences with CONV links; empty only with positive-empty evidence |
| `progress` / `value` | Attributable displayed posting counts; unavailable omits `value` |
| `kind` | Supported report occurrence classification as header/detail/total |
| Record `value` | Complete required field mapping for the classified occurrence |
| Error `category` | Existing structural or FAIL/observation classification |
| Error `availableContent` | Corresponding envelope with at least one actual available observation; never all-unavailable |

## Section 3: Operation Behavior Mappings

### 3.1 POST /posting — Posting

**Contract clauses:** C-1, C-5, C-9, C-10, C-12–C-14.

**Proposed ordered responsibilities:**

1. Associate the call with INV and the required empty closed request representation. Missing body, null, arrays, or properties do not match the existing shape; no business validation is added.
2. Associate the external daily input and each legacy resource through RES. An empty request supplies neither empty input nor EOF.
3. Delegate unchanged posting behavior; do not repeat selection or balance arithmetic.
4. Acquire separate transaction, rejection, and progress CAP records.
5. Map actual fields through CONV; preserve each stream’s order and multiplicity without inventing cross-stream ordering.
6. Associate observations and any known technical failure through RESP using Section 5.

| Rule enforcement | Source point | Adapter limit |
|---|---|---|
| R-1/R-2 | `app/cbl/CBTRN02C.cbl:202-219`, `370-422` | Preserve guarded lookup and selected preliminary reasons 100–103; later 103 overwrites 102 |
| R-3 | `app/cbl/CBTRN02C.cbl:424-465` | Posted timestamp differs from original candidate processing timestamp |
| R-4/R-5 | `app/cbl/CBTRN02C.cbl:467-560` | Signed additions remain legacy behavior |
| R-6 | `app/cbl/CBTRN02C.cbl:440-442`, `562-579` | Category, account, transaction are ordered attempts, not atomic success |
| R-18/R-20 | E-11; C-13/C-14 | No external failure or repetition guarantee |

**Reason 109 remains internal.** At `app/cbl/CBTRN02C.cbl:554-560`, rewrite may assign 109 after preliminary selection. Under the approved normal-return deduction, the caller continues to transaction writing without rechecking the reason. The adapter adds no stop, rejection, counter increment, public diagnostic, or 109-specific HTTP mapping.

Transaction output is indexed/random. A final indexed-resource snapshot does not by itself establish invocation-specific write occurrence order or multiplicity. A CAP record must justify both; otherwise G-26 remains open.

**Outcomes:** Any actual available output, rejection sequence, or progress observation supports 200 absent known technical failure. Positively observed empty sequences qualify. Zero-count progress qualifies only as progress: it does not establish no effects, input exhaustion, durable output, or transaction/rejection output fulfillment. All three channels unavailable and no known failure means observations503 none. Known failure means 500 with optional actual available observations.

### 3.2 POST /interest — Interest Transaction Generation

**Contract clauses:** C-2, C-6, C-9, C-11–C-14.

**Proposed ordered responsibilities:**

1. Associate INV with the unchanged empty request.
2. Record category input and identifier parameter separately in RES; do not use the job literal as a default.
3. Delegate unchanged account transitions, disclosure fallback, computation, identifier construction, and timestamp generation.
4. Acquire generated output through CAP, not through formula reconstruction or input console displays.
5. Preserve every represented occurrence and duplicate, including zero/negative quantities, using CONV.
6. Apply the existing response boundary through FAIL/RESP.

| Rule enforcement | Source point | Adapter limit |
|---|---|---|
| R-7/R-8 | `app/cbl/CBACT04C.cbl:188-228`, `325-370` | Normal pre-test EOF does not flush final account; no added update |
| R-9 | `app/cbl/CBACT04C.cbl:415-460` | Missing disclosure is not zero rate |
| R-10 | `app/cbl/CBACT04C.cbl:214-217`, `462-470` | Nonzero rate selects generation; no positivity restriction or adapter arithmetic |
| R-11 | `app/cbl/CBACT04C.cbl:473-520`, `613-626` | Preserve local construction; no global uniqueness or fee output |
| R-18/R-20 | E-15; C-13/C-14 | External behavior and repetition remain unknown |

**Outcomes:** Available generated observations, including positive empty observations, support 200 absent known failure. Empty output does not establish zero-rate bypass or its cause. Zero rate, missing disclosure, and a generated zero amount remain distinct. Unavailable output with no known failure means observations503 none. Known failure means 500, optionally retaining actual available output.

Generated transactions do not attest account rewriting. No suffix, internal record counter, disclosure trace, or final-account receipt is exposed.

### 3.3 POST /reporting — Transaction Reporting

**Contract clauses:** C-3, C-7–C-9, C-12–C-14.

**Proposed ordered responsibilities:**

1. Associate INV with the unchanged empty request.
2. Record the external transaction sequence, separate date resource, and any upstream selection provenance independently.
3. Delegate unchanged reporting; do not merge date authorities or repair sentence-level control flow.
4. Acquire report output through CAP, identifying actual canonical occurrences and excluded presentation records.
5. Map receiver values through CONV into one mixed ordered `records` sequence; retain repeated headers, details, and totals.
6. Apply FAIL/RESP without erasing available earlier content because a later failure is known.

| Rule enforcement | Source point | Adapter limit |
|---|---|---|
| R-12 | `app/cbl/CBTRN03C.cbl:170-243` | Date comparison precedes EOF check; date alternative leaves loop sentence, not skip-and-continue |
| R-13 | `app/cbl/CBTRN03C.cbl:181-196`, `484-512` | Card change triggers account-labelled grouping; prior total may precede failing lookup |
| R-14/R-15 | `app/cbl/CBTRN03C.cbl:197-204`, `293-322` | Conditional EOF addition/page/grand output; no final account-total insertion |
| R-16 | `app/cbl/CBTRN03C.cbl:274-374`; `app/cpy/CVTRA07Y.cpy:4-66` | Receiver text and source-labelled totals, not rebuilt descriptions or arithmetic |
| R-17 | `app/jcl/TRANREPT.jcl:37-74` | SORT dates and program dates remain separate |
| R-18/R-20 | E-19; C-13/C-14 | No durable-output or repetition guarantee |

**Outcomes:** Available mixed records, including a positively observed empty sequence, support 200 absent known failure. Header-only or total-only observations must not be collapsed into empty records. Empty records establish neither a complete empty report nor full-range processing, zero/reconciled totals, final account totals, or input exhaustion.

Post-EOF buffer contents remain unknown. Conditional duplicate contribution is not asserted, removed, or corrected. Unavailable records with no known failure means observations503 none; known failure means 500 with optional actual available records.

## Section 4: State and Session Model

### 4.1 State Realization and Setup Boundary

No session, singleton, process-per-call, concurrency, or persistence architecture is selected.

Every resource below requires a separate RES/STATE instance record when actually bound. The common concrete documentary mechanism is the linked record protocol in Section 2; **runtime supply and observation mechanisms remain unestablished**.

| Resource / requirement | Contract clause or external setup | Concrete documentary treatment | Observable reset/isolation check |
|---|---|---|---|
| Posting daily sequence | C-1; external | RES identifies input instance, origin, order basis and validity | Unavailable |
| Posting card association | C-4/C-13; internal | Card-key xref resource, E-21 | Unavailable |
| Posting account | C-10/C-13; internal | Read/rewrite resource; STATE separates attempts from durable effects | Unavailable |
| Posting category balance | C-10/C-13; internal | Create/update resource; local flag reset separately recorded | Flag reset is not resource reset |
| Posting transaction output | C-5 | CAP plus indexed-order/multiplicity justification | OUTPUT open is not reset evidence |
| Posting reject output | C-5 | Separate sequential CAP channel | Unavailable |
| Posting control/counts | C-5 | Local state; actual displayed counts only | Declared zeros are not observed reset |
| Interest category sequence | C-2; external | RES with encountered-order/grouping limits | Unavailable |
| Interest account | C-11/C-13; internal | Transition-time update distinction | Cycle clearing is not environment reset |
| Interest account-key xref | C-4/C-13 | RES identifies actual alternate-key binding | Unavailable |
| Interest disclosure | C-6; internal | Separate rate resource and fallback context | Unavailable |
| Interest identifier parameter | C-2/C-6; external | Actual parameter origin and validity window | No lifetime/reset claim |
| Interest group/control | C-11; internal | Local transition/accumulation scope | No inter-call isolation evidence |
| Interest suffix | C-6/C-14; internal | Local initialized state, not global identity | No repeat-safety evidence |
| Interest generated output | C-6 | Invocation-attributed sequential CAP | Unavailable |
| Reporting transaction sequence | C-3; external | RES with actual source/order and EOF limits | Unavailable |
| Reporting date resource | C-3/C-8; external | Separate resource/value origin | Unavailable |
| Upstream selection result | C-3/C-13; external | Documentary versus actual-flow provenance | No executed-selection evidence |
| Reporting card association | C-4/C-8; internal | Card-key resource and current-card local state | Initial spaces are not isolation |
| Reporting type descriptions | C-7; internal | Lookup resource distinct from report receiver | Unavailable |
| Reporting category descriptions | C-7; internal | Same distinction, separate resource | Unavailable |
| Reporting page accumulation | C-8; internal | Local add/transfer/reset sites | Local reset only |
| Reporting account accumulation | C-8; internal | Card-triggered total/reset sites | No final EOF reset assertion |
| Reporting grand accumulation | C-8; internal | Page-to-grand accumulation | Initial zero is not runtime evidence |
| Reporting control/presentation | C-7/C-8; internal | First-time/line counter scope | No persistent isolation evidence |
| Report output | C-7/C-8 | Mixed occurrence CAP/CONV | No complete-output/reset evidence |
| Transaction backup | C-4/C-13; all tracks | E-33 documentary resource only | No completed backup/restoration |
| Combined intermediate | C-4/C-13; posting/interest | E-32 documentary combination/load context | No merged-state evidence |
| Master lifecycle context | C-13; all tracks | Separate actual-instance identity required | No shared-instance/reset assertion |
| Procedure control | C-13; all tracks | `REPROCT` unavailable, E-34 | Unavailable |
| External failure routine | C-12/C-13; each track | `CEE3ABD` call sites only | No termination/rollback evidence |

STATE must separately record claims of prepared state, shared state, or unestablished state and their evidence. Recording “prepared” without preparation provenance is not sufficient. Resource reuse is not idempotency. Restarting a process or server is not reset of persistent resources.

`app/jcl/COMBTRAN.jcl:20-48`, `app/jcl/TRANBKP.jcl:19-67`, and `app/proc/REPROC.prc:19-29` establish operational context, not an adapter-owned schedule, reset facility, or completed durable state.

## Section 5: Error and Edge Behavior

### 5.1 Partial Execution and Process Lifecycle

Output observation, capture completion, process completion, business input exhaustion, and durability are separate propositions.

A response does not establish normal exit or flushed counters. A normal-exit message does not establish durable writes or full input processing. A stopped process does not establish rollback. No timeout duration, cancellation semantics, exit-code taxonomy, cleanup mechanism, or universal HTTP-response guarantee is invented.

#### Minimum criterion for known technical failure

A FAIL assessment may classify technical failure as known only when it contains:

1. An actual observable event or diagnostic, with retained evidence reference.
2. Attribution to the current invocation and relevant channel/resource.
3. A supported interpretation that the event establishes technical failure at the response boundary.
4. Separation of the event’s known meaning from unestablished cause, termination, rollback, or durability.
5. The point at which the failure became known and its relation to retained observations.

Candidate sources include attributable legacy error output, an established hosting failure event, or an established acquisition failure. Their concrete decoding and meaning require evidence; none is universally trustworthy by source type alone.

A possible `CEE3ABD` call, numeric exit value, file-status value, diagnostic label, or absence of output is insufficient without that attribution and meaning basis. Posting return code 4 is not automatically technical failure. Internal 109 has no new error mapping.

Preserve diagnostic mismatches in R-18 rather than silently correcting them: posting reject-close uses xref status; interest disclosure-open has a misleading label. A known failure need not imply a known resource-specific root cause.

#### Existing response classification

| Boundary condition | Existing response | Required record basis |
|---|---|---|
| Request does not match required empty closed object | 400 `request_representation` | INV/RESP identifies structural mismatch only |
| Technical failure known at batch response boundary | 500 `technical_failure` | FAIL plus RESP; optional available observations retained |
| No known technical failure; at least one permitted observation available | 200 track envelope | CAP/CONV/RESP; empty sequences permitted |
| No known technical failure; no represented observation | 503 `content_unavailable` | RESP records unavailability; **observations503 none** |

Known technical failure takes precedence over 200 and 503. For 200:

- Posting requires available outputs, rejections, or progress.
- Interest requires available outputs.
- Reporting requires available records.

No `minItems: 1` is introduced. Available empty is a represented observation, not “none.”

Unavailable sequence variants omit `items`; unavailable progress omits `value`. Optional error `availableContent` requires at least one actual available observation, including positive empty or posting progress. A 503 response carries no substantive observation.

A damaged capture may support 500 when failure is known, or unavailability when it is not. It must never be treated as positive empty merely to produce a convenient response. Other independently supported channels remain separately accountable.

### 5.2 Contract-to-Behavior and Record Traceability

Every mapped clause requires RESP provenance or an explicit nonpublic/excluded disposition; it does not require fabricated runtime events.

| Clause | Documentary responsibility and records | Semantic/evidence basis |
|---|---|---|
| C-1 | Posting operation/request association, external daily binding: INV/RES | R-1–R-6; E-4/E-7–E-11/E-29 |
| C-2 | Interest category/parameter association: INV/RES | R-7–R-11; E-5/E-12–E-15/E-30 |
| C-3 | Reporting transaction/date/selection separation: INV/RES | R-12–R-17; E-6/E-16–E-19/E-31 |
| C-4 | RESP exclusion disposition; internal records never public | Stage 5 D-3/D-7/D-8; R-19/R-20 |
| C-5 | Posting field, rejection, progress and 109 boundary: CAP/CONV/RESP | R-1–R-6; E-26/E-27 |
| C-6 | Generated fields, zero/missing distinctions: CAP/CONV/RESP | R-7–R-11; E-22/E-23/E-26 |
| C-7 | Report receiver field provenance and loss: CAP/CONV | R-16; E-24/E-25/E-28 |
| C-8 | Mixed order/multiplicity and bounded finalization: CAP/CONV/RESP | R-12–R-17; E-16–E-18/E-28 |
| C-9 | Structural request decision only: INV/RESP | D-10/D-11/D-14 |
| C-10 | Ordered posting attempts, no atomic receipt: STATE/FAIL/RESP | R-4–R-6; E-9–E-11 |
| C-11 | No interest final flush/update receipt: STATE/RESP | R-7/R-8; E-12/E-14 |
| C-12 | Existing status predicates and failure precedence: FAIL/RESP | R-18; revised D-16/D-17 |
| C-13 | Resource-specific state and external setup accountability: RES/STATE | R-6/R-18/R-19; E-29–E-34 |
| C-14 | Unknown repetition per track: STATE/RESP | R-20 |

R-1–R-20 retain their complete Stage 6 reverse-completeness destinations. This revision adds evidence-record responsibilities, not new rules. E-1–E-3 remain orientation; E-35 remains licensing context. Shared evidence retains its approved consuming tracks.

### 5.3 Bounded Gaps and Ambiguity Propagation

Original G-25–G-31 identities are retained. Documentary and empirical dimensions are separated rather than blanket-closed.

| Gap | Documentary responsibility now specified | Remaining bounded limitation |
|---|---|---|
| G-25 | INV/RES define attribution, owner, preparation, instance identity and validity | Actual invocation mechanism, supplied instances and availability remain undemonstrated |
| G-26 | CAP defines admissibility, positive empty, stale/zero-length/truncated/failed capture and occurrence accounting | Faithful acquisition, freshness, framing and indexed posting order/multiplicity remain undemonstrated |
| G-27 | CONV and field tables define per-field provenance, width/sign/padding/display/loss obligations | Concrete deployed decoding or representability conflicts remain open where unsupported |
| G-28 | FAIL defines minimum known-failure evidence and unchanged status precedence | Actual diagnostic/hosting/capture semantics and response feasibility remain undemonstrated |
| G-29 | STATE and per-resource rows separate local, persistent, shared and preparation claims | Reset, isolation, durable effects and repetition safety remain unknown |
| G-30 | Reporting CAP/CONV protocol preserves mixed order, EOF/date limits and no repair | Actual dates, EOF storage, job flow and numerical output remain unknown |
| G-31 | Exact-version external review requirements are stated | Human approval, retained r2 output digest and bound review remain external and absent |

Inherited A-1–A-17 and G-21–G-24 are not erased:

- A-1/A-8/A-2/A-16 preserve cohesion, identity, schedule and dependency limits.
- A-3/A-12 preserve encoding, numeric, temporal, parameter and identifier limits.
- A-4/A-10/A-17 preserve persistence, isolation and external failure uncertainty.
- A-9 preserves preliminary precedence and internal 109 timing.
- A-11 preserves normal interest EOF without final flush.
- A-13 preserves bounded fee absence.
- A-14/A-15 preserve reporting date, EOF, grouping and total uncertainty.
- A-5/A-6 preserve exposure and licensing limits.
- A-7 remains addressed by upstream layout authority.

Upstream review is required if faithful realization would need public-field additions, changed requests/statuses, a selector, new availability semantics, reset/idempotency promises, a 109-specific public outcome, reconstructed totals/descriptions, or repaired finalization. Stage 7 does not make those changes.

## Section 6: Implementation Notes (non-authoritative)

No code, commands, implementation tasks, component structure, runtime technology, source repairs, or generated adapter is specified.

The record protocol is concrete documentary design; actual populated records require real attributable evidence. It does not promise a persistent logging service or fabricate counters, readiness, reset evidence, retry evidence, durable state, or completion evidence.

No tools, external retrieval, additional model/network calls, COBOL execution, or filesystem modification were performed. Supplied pins and historical findings are not new verification results. Provider retention settings, usage, costs, and actual generation telemetry are not certified.

## Completeness Gate and Entry Boundary

The three states below have deliberately different meanings:

- **closed-by-documentary-design:** this draft specifies the responsibility; no human or runtime approval follows.
- **open-bounded-gap:** a concrete authority, representation, binding, or external-review issue remains unresolved.
- **deferred-empirical-obligation:** the documentary criterion is specified, but satisfaction requires separately authorized actual evidence.

| Area | State | Documentary disposition or remaining obligation |
|---|---|---|
| Exact capability and three mandatory tracks | closed-by-documentary-design | Identity and independent track mappings retained |
| Public contract surface | closed-by-documentary-design | No changes to routes, requests, fields, statuses or availability semantics |
| G-25 attribution/setup protocol | closed-by-documentary-design | INV/RES define required records and ownership boundaries |
| Actual invocation/resources | deferred-empirical-obligation | Establish actual binding and resource attribution without claiming it now |
| G-26 capture/positive-empty protocol | closed-by-documentary-design | CAP separates business observations from evidence-state problems |
| Actual capture/order/multiplicity | deferred-empirical-obligation | Establish channel fidelity, including indexed posting occurrence attribution |
| G-27 field provenance protocol | closed-by-documentary-design | Every mapped public field has source or contract-metadata provenance |
| Unsupported concrete conversions | open-bounded-gap | Encoding/sign/framing or faithful representation conflicts require evidence or upstream disposition |
| G-28 known-failure criterion | closed-by-documentary-design | FAIL criterion and 500 precedence specified |
| Actual failure detection | deferred-empirical-obligation | Establish actual event meaning and response-boundary knowledge |
| G-29 state-accountability protocol | closed-by-documentary-design | Per-resource local/persistent/preparation/reuse distinctions specified |
| Reset/isolation/durability claims | deferred-empirical-obligation | No such claims made; any later assertion requires separate supporting evidence |
| G-30 reporting observation discipline | closed-by-documentary-design | Mixed order, receiver content, EOF limits and no complete-empty claim retained |
| Actual reporting input/EOF/output | deferred-empirical-obligation | Actual dates, flow, buffer behavior and output remain unobserved |
| Changes requiring public-contract or semantic alteration | open-bounded-gap | Escalate upstream; no silent adapter workaround |
| G-31 exact-version human review | open-bounded-gap | External human decision only; not an empirical execution requirement |
| r2 persistence/digest and mechanical checks | open-bounded-gap | Not established by this response |

Documentary decisions need not wait for runtime proof; runtime claims cannot be closed by documentary decisions. No row approves the original Stage 7 artifact or this revision.

**G-31 remains external human approval. Stage 7 r2 is an unapproved documentary draft; no gate is approved, no implementation is authorized, and no further-stage material is created.**
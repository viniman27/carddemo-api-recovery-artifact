# Semantic Validation Specification

## Purpose

This Stage 8 specification documents semantic-validation scenarios, expected obligations, and evidence acceptance criteria for the AWS CardDemo public cycle in run `E3-01`.

It derives from **approved/current Stage 7 r2**, **Stage 6 r3**, and their upstream documentary authorities. **Posting, interest, and reporting are mandatory, separately traceable tracks.** No track’s coverage substitutes for another’s.

| Attribute | Value |
|---|---|
| Run | `E3-01` |
| Pipeline stage | `8` |
| Feature | `semantic-validation-carddemo` |
| Artifact | `specs/semantic-validation-carddemo/requirements.md` |
| Exact inherited capability identity | `unselected-stage-1-scope-only` |
| Immediate upstream | `specs/adapter-behavior-carddemo-r2/spec.json` |
| Mandatory tracks | `posting`, `interest`, `reporting` |
| Status | Documentary specification for external human review |
| Human approval granted by this artifact | `false` |
| Completeness gate passed by this artifact | `false` |
| Ready for implementation | `false` |

The question addressed is whether a **documented mapping** preserves the approved contract’s observable obligations, the adapter’s evidence requirements, and the semantics’ explicit limitations.

**All V-n entries are specification scenarios only.** They are not executed tests, empirical runs, runtime validation, or execution results. Conditional references to observations describe evidence that would be required, not evidence obtained here.

## Validation Integrity Discipline

- Every scenario derives from identified Stage 7 protocols, Stage 6 clauses, canonical constraints, or R-n/E-n authority.
- Each scenario names a question-specific oracle. Contract representation, documentary legacy characterization, and evidence admissibility remain distinct.
- Every scenario is typed **conformance** or **legacy characterization**, separately from its **positive**, **negative**, or **counterexample** family.
- Conformance scenarios concern determinate contract or documentary obligations. Actual outcomes dependent on open ambiguities remain explicitly unresolved and are not conformance-bearing.
- Legacy-characterization scenarios retain conditional source deductions and anomalies without making them acceptance requirements for a different implementation.
- Public expectations remain phrased against the approved surface. INV/RES/CAP/CONV/FAIL/STATE/RESP are supporting documentary evidence obligations, not public interfaces.
- Missing evidence is inconclusive for an empirical claim, not satisfaction of the obligation.
- Source declarations, source statements, upstream reviews, and protocol definitions do not establish actual invocation, capture, state, or response behavior.
- No business rule is reimplemented, no source defect is repaired, and no missing output is reconstructed.
- No runtime, tool, harness, capture mechanism, reset facility, or independent oracle is invented.
- This specification makes no adherence, equivalence, transferability, or behavioral-confidence result claim.

## Section 1: Upstream Authority and Entry Condition

### 1.1 Upstream Authorities

The entry basis is the supplied structured Stage 7 r2 authorization, which approves documentary adapter behavior and authorizes **Stage 8 specification only** for all three tracks.

Structured authorization governs. Prose consent does not enlarge scope, and contradictory or rejecting structured authority would block the affected activity.

| Current artifact relative to `RUN_ROOT` | Supplied SHA-256 |
|---|---|
| `specs/pipeline-scope-carddemo/requirements.md` | `1362fab5d55b77ef6121328606ae974295cd5723849520e9a246f4bd45e64cc9` |
| `specs/capability-selection-carddemo-r2/requirements.md` | `abdb59180f379d9e14eb86dfa1d8226ec50c981346767e808fd382eb7462bbc4` |
| `specs/legacy-evidence-carddemo-r2/requirements.md` | `4566786600b60e9377c1e369e67765098d06b0153ba973361d2065614a6c9b7b` |
| `specs/capability-semantics-carddemo/requirements.md` | `2f9d3ee52dd7788e206810e38c9173b19d21dfc44270cdd06d05e62dec95eb93` |
| `specs/canonical-data-boundary-carddemo/requirements.md` | `208d04fe6f9cae665dfa4cb514de5d4ad9eaf0ebc169dfae0fd8a6ba209e66f3` |
| `specs/api-contract-carddemo-r3/requirements.md` | `6cba102f8335843b46e75a77b1a71d4e56373a95d5ac63cf645491556c443b27` |
| `specs/adapter-behavior-carddemo-r2/requirements.md` | `b53c471116dfa0c3831fc810964bddca3eb1fa0d3b8e7d459181ba71e54b3d8f` |

| Immediate authority or review | Supplied SHA-256 |
|---|---|
| `specs/adapter-behavior-carddemo-r2/spec.json` | `94984c957b3d4aebfb16a613ced217752fc56d04becc81060aaa7fb388210933` |
| `reviews/stage-7-r2-authorization.json` | `3e3315cfb4ae05e65f9627ae3147343259d93eabf31931c3177a105c1615cb60` |
| `STAGE7-R2-COUNTEREXAMPLE-REVIEW.md` | `74b60bb0be83f746ff46a10f1682e0a50a8e09100a36323724d7ff7c5abc476f` |
| `specs/adapter-behavior-carddemo-r2/stage7-r2-verification.json` | `0eed83701b579f719d5864b84ac54db5fa4571675146af63bea491e4f6418aad` |
| `specs/api-contract-carddemo-r3/spec.json` | `2ec40d54f4d89198ccc9e0cac602ba4192ee063290d9f226c0b1ac101899a0bd` |
| `reviews/stage-6-r3-authorization.json` | `0c5228634cb0f3b3c779fafe2e7e9ae5109aebeb24b116268e73a9a00dd8213e` |

The complete supplied `input_pins` register is incorporated by reference **without alteration**, including all seven upstream metadata/artifact pairs, seven authorizations, seven review attachments, source-package pin, 19 original corpus pins and separate derived-representation pins, and 13 framework pins.

The governing supplied template is:

`FRAMEWORK_ROOT/settings/templates/pipeline/semantic-validation-spec.md`

SHA-256: `fd258fed1b1c6cb656f1d88088573b7ec30047824203312ffaaed1c757ea41dd`.

The source-package pin remains:

`63ba5c47ecb21349549744b912af3b150654e7e435724dba499e3c88369f15a2`.

Exact original source text and stable numbered representations remain separate retained objects. Every source path used below resolves to its original and derived pins in `input_pins.source_bodies`. No checksum or filesystem verification is claimed.

#### Revision and review inheritance

- Stage 6 r2 remains historical, unapproved revision context. Stage 6 r3 governs observed-empty versus unavailable representation.
- Original Stage 7 remains historical revision context. Stage 7 r2 governs internal documentary protocols.
- Their revision references and original byte pins remain those recorded in the supplied upstream artifacts; referenced but unsupplied bodies are not reconstructed.
- Stage 4–7 review/findings records supply bounded documentary review provenance, not current runtime evidence.
- Historical draft-era approval wording is not rewritten. Subsequent structured approvals establish the supplied current authority.
- The supplied `current` gate-check result is inherited freshness information, not a new check or approval.
- Stage 7’s shorthand “observations503 none” is read only through its explicit response table and Stage 6 C-12: no represented observation and no known technical failure maps to `503 content_unavailable`. It creates no field or status.

### 1.2 Validation Scope Statement

The public surface remains:

| Track | Surface | Required request meaning |
|---|---|---|
| posting | `POST /posting` | Empty closed object; not daily input, resource selection, or EOF |
| interest | `POST /interest` | Empty closed object; not category data or identifier parameter |
| reporting | `POST /reporting` | Empty closed object; not transaction data, dates, or SORT override |

Scope includes documentary assessment of:

- Invocation/resource attribution and external-input responsibility.
- Capture admissibility, including empty and damaged evidence states.
- Field provenance, conversion limitations, order, and multiplicity.
- Known-failure predicates and response association.
- Internal reason 109, partial effects, EOF limitations, and non-guarantees.
- Reverse completeness across all seven Stage 7 protocols, C-1–C-14, and R-1–R-20.

Excluded are implementation, source changes, generated tests, API generation, COBOL/JCL execution, runtime validation, additional model/network calls, comparative material, and later-stage artifacts.

No concrete environment is selected. The supplied roots remain unchanged and are not inspected.

## Section 2: Oracle Inventory

| Oracle | Claim / question | Expected-obligation origin | Tool origin / data exposure | Limitations |
|---|---|---|---|---|
| **O-C — Approved Stage 6 r3** | Surface and representation conformance | C-1–C-14; schemas; D-9–D-17 | Supplied documentary contract; no tool used | Does not establish actual observations, detection, or execution |
| **O-A — Approved Stage 7 r2** | Evidence admissibility and response justification | INV, RES, CAP, CONV, FAIL, STATE, RESP; §§2–5 | Supplied documentary design and review | Protocol definitions are not populated evidence |
| **O-S — Approved Stage 4 semantics and Stage 5 boundary** | Rule meaning, exclusions, state limits | R-1–R-20; canonical dispositions | Supplied reviewed documents | Conditional deductions retain their assumptions |
| **O-E — Approved Stage 3-r2 and corpus19** | Documentary legacy characterization | E-1–E-35 and exact numbered source | Supplied original text and numbered representations | No observed runtime outcomes or deployed encoding |
| **O-R — Supplied review/authorization chain** | Version, scope, and revision provenance | Structured decisions and bounded findings | Supplied records only | Review counts and historical findings are not new results |

There is **no observed-execution oracle** available for this specification. No reference-layer-only oracle is selected.

Conflicting authorities require explicit upstream review. A convenient oracle must not be selected merely to obtain acceptance.

### Common documentary evidence acceptance criteria

Every scenario inherits these criteria:

1. **Identity:** retain run, exact capability, track, current artifact versions, and scenario identity.
2. **Derivation:** identify the applicable clause, protocol, rule, and source anchor or declared representation decision.
3. **Separation:** label scenario premises as hypothetical documentary conditions; never present them as populated runtime records.
4. **Attribution:** define the required INV→RES→CAP→CONV→RESP links, with FAIL/STATE where applicable.
5. **Completeness of explanation:** account for represented content, exclusions, damaged content, unavailable observations, and unresolved questions.
6. **No unsupported closure:** identify empirical evidence needed separately from documentary adequacy.
7. **No invented values:** source literals, declarations, predicted branches, empty files, and model-generated expectations cannot substitute for observed output values.

A documentary mapping is acceptable only within the stated obligation. It does not establish that the corresponding runtime condition occurred.

## Section 3: Scenario Groups

V-n identifiers are run-scoped and do not restart by track. Shared scenarios require **separate posting, interest, and reporting dispositions**.

### Group A — Shared Contract and Evidence Boundary

| ID | Family / Type | Derived from | Documentary setup and stimulus | Expected obligation and evidence acceptance criterion | Oracle |
|---|---|---|---|---|---|
| **V-1** | Positive / conformance | C-1–C-3, C-9; INV/RES | Describe a valid empty request for each track and its external inputs | Associate only the called operation. INV/RES specify owner, binding reference, resource role, validity window, and unknown prerequisites; no request-derived input identity or EOF | O-C, O-A |
| **V-2** | Negative / conformance | C-9; D-10/D-14; INV/RESP | Consider missing body, null, array, or object with properties | Document `400 request_representation`; identify structural mismatch only. Do not infer legacy rejection, execution, or effects | O-C |
| **V-3** | Positive / conformance | C-5–C-8, C-12; CAP/CONV/RESP | Premise: attributable nonempty canonical observations and no known technical failure | Document eligible 200 with exact track envelope, complete field mappings, occurrence positions, retained duplicates, `not_attested` completeness and `unknown` durability | O-C, O-A |
| **V-4** | Positive / conformance | Revised D-16; CAP positive-empty criterion | Premise: a justified observation scope positively establishes zero canonical occurrences | Permit available `items: []` and eligible 200. Acceptance requires attribution, successful observation/framing basis, scope and exclusions—not silence or file size alone | O-C, O-A |
| **V-5** | Negative / conformance | C-12; CAP/RESP | Premise: all permitted observations unavailable; no known technical failure | Document `503 content_unavailable`, not 200. Unavailable sequences omit `items`; unavailable progress omits `value`; no substantive `availableContent` | O-C, O-A |
| **V-6** | Negative / conformance | C-12; FAIL/RESP | Premise: current attributable evidence meets Stage 7’s known-failure predicate | Document `500 technical_failure`, taking precedence over 200/503. Optional available content may be empty or nonempty but not all-unavailable; separate failure from unknown root cause and effects | O-C, O-A |
| **V-7** | Negative / conformance | INV/RES/CAP; G-25/G-26 | Capture belongs to a previous invocation or validity window | Reject its use as current-call content; retain stale attribution internally. Classify remaining channels independently; staleness alone does not select 500 | O-A, O-C |
| **V-8** | Negative / conformance | INV/RES/CAP/RESP | Capture is assigned to the wrong track, resource, producer, or invocation | Reject the misattributed mapping. Matching filenames, identifiers, or bytes do not repair attribution; no cross-track borrowing | O-A, O-S |
| **V-9** | Negative / conformance | CAP/CONV; G-26/G-27 | Capture contains complete occurrences followed by truncation or damaged framing | Retain independently justified complete occurrences and their order; register damaged/unrepresentable records. Never replace the whole capture with empty output or silently discard known content | O-A, O-C |
| **V-10** | Negative / conformance | CAP empty/zero-length/absent states | Consider absent capture, zero-length object, or capture with no readable content and no positive-empty basis | Treat each as insufficient for positive empty. Record the distinct evidence condition; use remaining observations and FAIL knowledge for response classification | O-A, O-C |
| **V-11** | Negative / conformance | CONV; C-5–C-9; G-27 | A required field lacks encoding, sign, framing, span, or representability support | Reject fabricated null/zero/text, guessed offsets, silent coercion, or reconstructed values. Record the conversion conflict; preserve independently supported content without hiding the gap | O-A, O-C |
| **V-12** | Counterexample / conformance | C-4, C-13/C-14; STATE | A mapping claims restart, declared zeros, OUTPUT open, or local clearing establishes reset/isolation | Such reasoning would falsify the documentary obligation. Require separate evidence for each resource; actual reset, isolation, durability, and repetition remain unresolved | O-C, O-A, O-S |
| **V-13** | Counterexample / conformance | C-4; D-12; all seven protocols | Internal record identifiers, readiness, file status, suffix, or failure details appear as new public fields | Reject the public extension. Internal accountability must not create telemetry, selectors, provisioning, reset, polling, or retry facilities | O-C, O-A |

**Response distinction applicable to V-3–V-11:** “No known technical failure” is not a claim that no failure occurred. Actual failure detection remains deferred. A capture problem may justify 500 only with the required known-failure evidence.

### Group B — Posting

| ID | Family / Type | Derived from | Documentary setup and stimulus | Expected obligation and evidence acceptance criterion | Oracle |
|---|---|---|---|---|---|
| **V-14** | Positive / conformance | C-5/C-10; R-1–R-3; CAP/CONV | Describe separately attributable posted and preliminary-rejection content | Preserve original rejection candidate context and selected reason/description; posted content uses its captured processing timestamp. No full-byte echo or filler meaning; all required fields map to their own occurrence | O-C, O-A |
| **V-15** | Negative / legacy characterization | R-1/R-2; E-7/E-8 | Consider card lookup failure, account lookup failure, equality boundaries, and both comparison alternatives | Retain reason-zero guard, 100/101 distinction, equality passing the displayed comparisons, and later 103 replacing 102 and its description. No multi-error list or conventional calendar policy | O-S, O-E |
| **V-16** | Counterexample / conformance | C-5/C-10; R-5; Stage 7 §3.1 | A proposed mapping turns internal reason 109 into preliminary rejection, extra reject count, public diagnostic, stop, or special HTTP outcome | Reject the mapping. Under the normal-return deduction, no reason recheck precedes transaction writing. Do not require branch telemetry to enforce the documentary exclusion | O-C, O-A, O-S |
| **V-17** | Negative / legacy characterization | R-4–R-6/R-18 | Consider category create/update, signed account addition, then final transaction-write failure | Retain category→account→transaction attempted order, signed negative debit addition, and no inspected local compensation. Do not infer rollback, unchanged balances, or durable partial persistence | O-S, O-E |
| **V-18** | Positive / conformance | C-5/C-10/C-12; CAP progress | Premise: actual attributable displayed counts are available, including both counts zero; other channels unavailable | Progress-only 200 is eligible absent known failure. Counts are not array-derived, committed counts, output fulfillment, exhaustion, or no-effects evidence | O-C, O-A |
| **V-19** | Counterexample / conformance | D-15; CAP; G-26 | An indexed output snapshot is offered as the sole basis for write occurrence order/multiplicity | Reject that inference. Require invocation-specific occurrence evidence; retain separate transaction/rejection streams and no invented cross-stream order | O-A, O-C |

**Posting anchors:** `app/cbl/CBTRN02C.cbl:202-230`, `370-422`, `424-465`, `467-579`; `app/cpy/CVTRA05Y.cpy:5-17`; `app/cpy/CVTRA06Y.cpy:5-17`.

V-15 and V-17 characterize documentary paths only. Concrete I/O outcomes and durable balances are excluded from their expected outcomes.

### Group C — Interest

| ID | Family / Type | Derived from | Documentary setup and stimulus | Expected obligation and evidence acceptance criterion | Oracle |
|---|---|---|---|---|---|
| **V-20** | Positive / conformance | C-6; R-10/R-11; CONV | Premise: generated transaction occurrences are attributable and representable | Preserve captured fields, zero/negative amounts, source-assigned merchant values, order and duplicates. Do not regenerate values from the formula, parameter, suffix, clock, or source literals | O-C, O-A |
| **V-21** | Negative / legacy characterization | R-9/R-10; E-12–E-14 | Consider initial disclosure status 23, failed default reread, selected zero rate, and nonzero rate with zero result | Keep status-specific DEFAULT reread, missing-not-zero, zero-rate bypass-not-rejection, and nonzero-rate generation despite zero/negative quantity. No invented rate units or rounding policy | O-S, O-E |
| **V-22** | Counterexample / conformance | C-6/C-12; revised D-16 | Positive-empty output is forced to 503, or a generated zero amount is removed as “empty” | Reject both mappings. Positive-empty observation permits 200 absent known failure; a zero quantity is content. Empty output does not establish zero-rate cause | O-C, O-A |
| **V-23** | Counterexample / legacy characterization | R-7/R-8; E-12/E-14 | One final account group reaches the documented normal pre-test EOF path | No final-account flush is inserted. Transition-time update and record-time transaction writing remain distinct; actual account persistence is unresolved | O-S, O-E |
| **V-24** | Counterexample / conformance | C-6/C-11/C-14; R-11/R-20 | A mapping asserts global generated-ID uniqueness, uses job parameter as default, exposes fee/suffix state, or treats outputs as account-update receipts | Reject those stronger claims. Require external parameter provenance, retain local construction and bounded fee exclusion, and record unknown identifier lifetime/repetition | O-C, O-A, O-S |

**Interest anchors:** `app/cbl/CBACT04C.cbl:166-180`, `188-228`, `325-370`, `415-460`, `462-520`, `613-626`; `app/jcl/INTCALC.jcl:22-41`; `app/cpy/CVTRA01Y.cpy:5-9`; `app/cpy/CVTRA02Y.cpy:5-9`.

No numerical output is calculated by this specification. Actual arithmetic edge behavior remains unresolved.

### Group D — Reporting

| ID | Family / Type | Derived from | Documentary setup and stimulus | Expected obligation and evidence acceptance criterion | Oracle |
|---|---|---|---|---|---|
| **V-25** | Positive / conformance | C-7/C-8; R-13–R-16; CAP/CONV | Premise: attributable headers, details, and page/account/grand totals occur, including repetitions | Preserve one mixed ordered sequence and multiplicity. Classify each occurrence; account for excluded blanks/column labels/separators. Header-only or total-only content is not empty | O-C, O-A |
| **V-26** | Negative / conformance | C-7; CONV; R-16 | Mapping restores 50-character lookup descriptions, trims presentation spaces, or recalculates displayed totals | Reject substitution. Map actual 15/29-character description receivers and bounded signed amount/total text, recording padding, punctuation, and known loss | O-C, O-A |
| **V-27** | Counterexample / legacy characterization | R-12/R-17; E-16/E-31 | Out-of-range transaction precedes a later eligible record; later date range is wider than upstream SORT bounds | Retain sentence-level exit, not skip-and-continue. Keep two date authorities; under the stated actual-flow premise, later widening cannot restore upstream-removed rows. No complete intersection claim | O-S, O-E |
| **V-28** | Counterexample / legacy characterization | R-14/R-15; E-16/E-17 | Consider EOF with retained prior storage versus unestablished/different storage | Preserve date comparison before EOF test, conditional extra ADD, page/grand calls, and absent EOF account-total call. Neither unconditional duplication nor corrected totals are acceptable expectations | O-S, O-E |
| **V-29** | Counterexample / conformance | C-8/C-12; revised D-16 | Positive-empty records are represented, or dates/details/totals are absent | Positive-empty may support 200; it must not certify complete empty report, full-range processing, zero/reconciled totals, final account total, or exhaustion. Missing observation remains distinct | O-C, O-A |
| **V-30** | Negative / conformance | C-8/C-12; R-13/R-14/R-18 | Premise: earlier total content is available and a later lookup/output technical failure is known | Preserve independently supported earlier content and order; document 500 precedence with optional available content. No unchanged/empty-report inference | O-C, O-A |
| **V-31** | Counterexample / legacy characterization | R-13/R-16 | Two cards can reference one account; non-detail records increment line count | Retain card-change grouping, not account-ID grouping; page-size 20 is not twenty detail records. Actual cardinality and numerical presentation outcomes remain unresolved | O-S, O-E |

**Reporting anchors:** `app/cbl/CBTRN03C.cbl:122-137`, `170-243`, `274-374`, `484-512`; `app/cpy/CVTRA07Y.cpy:4-66`; `app/cpy/CVTRA03Y.cpy:5-6`; `app/cpy/CVTRA04Y.cpy:5-8`; `app/jcl/TRANREPT.jcl:37-74`.

### Group E — Cross-Track Failure, State, and Completeness

| ID | Family / Type | Derived from | Documentary setup and stimulus | Expected obligation and evidence acceptance criterion | Oracle |
|---|---|---|---|---|---|
| **V-32** | Counterexample / conformance | C-12; FAIL; R-18 | Source call site, numeric exit, posting return code 4, misleading diagnostic label, or missing output is offered as sufficient known-failure evidence | Reject automatic classification. Require actual event, current attribution, supported meaning, knowledge timing, and separation of cause/effects. Preserve diagnostic mismatches; no fabricated CEE3ABD semantics | O-A, O-C, O-S |
| **V-33** | Counterexample / conformance | C-13/C-14; RES/STATE; R-19/R-20 | Matching dataset names, backup instructions, or restart are used to claim shared live state, completed cycle, restoration, or safe repetition | Reject stronger claims; retain resource-specific provenance and unknowns. Missing REPROCT and external routine behavior remain explicit | O-C, O-A, O-S |
| **V-34** | Negative / conformance | Traceability rules; all protocols and clauses | A protocol, clause, field, resource, rule, or consuming track lacks an obligation or explicit uncertainty destination | Documentary completeness is not acceptable until the omission is recorded and mapped. Identifier mentions or review counts alone do not establish substantive coverage | O-A, O-C, O-S |
| **V-35** | Counterexample / conformance | Stage 7 G-25–G-31; authorization boundary | A document labels protocol definitions, historical reviews, or scenario premises as actual evidence or gate approval | Reject that claim. Separate documentary design, empirical uncertainty, and external human review; no populated records or outcome claims may be manufactured | O-A, O-R |

R-18 source anchors include `app/cbl/CBTRN02C.cbl:637-653`, `707-727`; `app/cbl/CBACT04C.cbl:270-286`, `628-648`; `app/cbl/CBTRN03C.cbl:626-646`.

R-19 context includes `app/jcl/COMBTRAN.jcl:20-48`, `app/jcl/TRANBKP.jcl:19-67`, and `app/proc/REPROC.prc:19-29`.

## Section 4: Coverage Statement

Coverage below is **planned documentary obligation coverage**, not exercised behavior, source coverage, or empirical completeness.

### 4.1 Reverse Completeness — Every Stage 7 Protocol

| Stage 7 protocol | Validation obligations | Explicit unresolved empirical uncertainty |
|---|---|---|
| INV | V-1/V-2/V-7/V-8/V-13/V-35: identity, request, binding references, windows, channels, response association | Actual invocation, timing, binding and reachability |
| RES | V-1/V-8/V-12/V-24/V-33: owner, preparation, resource role/instance, prerequisites, reuse and dependencies | Actual resources, preparation, availability and instance identity |
| CAP | V-3–V-10/V-19/V-25/V-30: attribution, framing, freshness, conditions, occurrences, exclusions and positive empty | Actual channel fidelity, capture scope, cardinality, indexed occurrence order |
| CONV | V-11/V-14/V-20/V-26: every field’s raw span, declaration, encoding/sign/framing, mapping, loss and representability | Deployed conversion behavior and unresolved physical representation |
| FAIL | V-6/V-9/V-17/V-30/V-32: actual-event predicate, attribution, knowledge point, failure origin and retained content | Actual event meanings, detection and response feasibility |
| STATE | V-12/V-17/V-23/V-24/V-28/V-33: local/persistent distinction, preparation, lifetime, reset/isolation, attempted/observed/durable effects | Reset, isolation, durable effects, EOF storage and repetition safety |
| RESP | V-2–V-6/V-13/V-16/V-18/V-22/V-29/V-34: exact contract version, per-channel dispositions, indices, status rationale and gaps | Actual response association and delivery |

Each required record field in Stage 7 §2.1 remains an acceptance obligation under its row; none is waived because the table is condensed.

### 4.2 Reverse Completeness — Every Stage 6 Clause

| Clause | Scenario destination | Retained boundary |
|---|---|---|
| C-1 | V-1/V-14–V-19 | Posting external-input batch operation |
| C-2 | V-1/V-20–V-24 | Interest external category/parameter responsibility |
| C-3 | V-1/V-25–V-31 | Reporting separate transaction/date/selection bases |
| C-4 | V-13/V-24/V-33 | No added public controls or internal telemetry |
| C-5 | V-14–V-19 | Original/posted/rejected distinction, 100–103, progress, internal 109 |
| C-6 | V-20–V-24 | Generated values, zero/missing distinctions and construction limits |
| C-7 | V-11/V-25/V-26 | Captured report receiver representation |
| C-8 | V-25–V-31 | Mixed order, grouping, totals, dates and EOF limitations |
| C-9 | V-1/V-2/V-11 | Structural conformance is not business acceptance |
| C-10 | V-16–V-18 | Ordered posting attempts and non-atomic limits |
| C-11 | V-23/V-24 | No final interest flush or update receipt |
| C-12 | V-3–V-6/V-18/V-22/V-29/V-30/V-32 | 200/400/500/503 predicates and failure precedence |
| C-13 | V-1/V-12/V-17/V-33 | Per-resource state and external setup |
| C-14 | V-12/V-24/V-33 | Unknown repetition separately for each track |

All Stage 6 schema fields and Stage 7 field-conversion rows fall under V-11/V-14/V-20/V-26/V-34. Requiredness, closed shapes, non-null treatment, enums, constants, and error `availableContent` are included; no field may be silently omitted.

### 4.3 Reverse Completeness — R-1–R-20

| Rule / effect | Evidence | Boundary / contract destination | Scenario obligations | Not empirically established |
|---|---|---|---|---|
| R-1 posting selection | E-4/E-7 | Candidate/rejection/progress; C-5/C-10 | V-14/V-15/V-18 | Actual encountered records/counts |
| R-2 precedence | E-7/E-8/E-20/E-21/E-27 | Selected reason; C-5 | V-15 | Concrete lookup/comparison outcomes |
| R-3 record distinction | E-4/E-9/E-26/E-27 | Separate transaction/rejection; C-5 | V-14 | Captured values and writes |
| R-4 category accumulation | E-9/E-10/E-22 | Internal state; C-10 | V-17 | Actual create/update effects |
| R-5 signed update/109 | E-7/E-9/E-10/E-20 | Internal reason; C-5/C-10 | V-16/V-17 | Rewrite behavior and durable state |
| R-6 ordered attempts/completion | E-7/E-9–E-11/E-29 | Counts/non-atomic limits; C-10/C-12 | V-17–V-19 | Durability, open effects, output fulfillment |
| R-7 interest transitions | E-5/E-12/E-13/E-20–E-22 | Internal grouping; C-6/C-11 | V-23 | Actual grouping/account updates |
| R-8 normal EOF omission | E-12/E-14 | No repair; C-11 | V-23 | Actual final account state |
| R-9 disclosure fallback | E-12/E-13/E-23 | Internal dependency; C-6 | V-21 | Actual rates and reads |
| R-10 selector/formula | E-5/E-12/E-14/E-22/E-23 | Generated amount; C-6 | V-20–V-22 | Numeric edge behavior, units, rounding |
| R-11 local construction/fee limit | E-5/E-14/E-26/E-30 | Output/parameter; C-6 | V-20/V-24 | Actual IDs/timestamps, lifetime, broader fees |
| R-12 date exit | E-6/E-16/E-26 | Dates/EOF; C-8 | V-27/V-29 | Actual date/buffer/branch outcomes |
| R-13 card grouping/lookups | E-6/E-16/E-18/E-21/E-24/E-25 | Detail/internal grouping; C-8 | V-25/V-30/V-31 | Actual card/account cardinality |
| R-14 total sites | E-6/E-16–E-18/E-28 | Distinct totals; C-8 | V-25/V-28/V-30 | Actual totals and persistence |
| R-15 conditional EOF | E-16/E-17 | No final account total; C-8 | V-28/V-29 | EOF storage and duplicate contribution |
| R-16 presentation | E-6/E-17/E-18/E-24–E-26/E-28 | Receiver values; C-7/C-8 | V-25/V-26/V-31 | Actual rendered output and conversion |
| R-17 two date sites | E-16/E-31/E-34 | External selection; C-3/C-8 | V-27/V-33 | Dates, executable flow, SORT outcomes |
| R-18 external failure | E-11/E-15/E-19 | Failure limits; C-12/C-13 | V-6/V-30/V-32 | External routine and actual detection |
| R-19 operational context | E-29–E-34 | External resources; C-4/C-13 | V-1/V-33 | Live identity, dependency closure, schedule |
| R-20 repetition | E-5/E-9–E-12/E-14–E-19/E-32–E-34 | Explicit unknown; C-14 | V-12/V-24/V-33 | Safe/unsafe repetition per environment |

R-18–R-20 require separate dispositions for posting, interest, and reporting. E-32 retains posting/interest consumers; E-33/E-34 retain all three.

E-1–E-3 remain orientation, not extra operations. E-35 remains licensing context under A-6, not a business validation obligation or legal clearance. All E-1–E-35 retain destinations through the upstream matrices and this accounting.

### 4.4 What This Scenario Set Does Not Establish

No operation or rule has been empirically exercised here. The scenario set does not establish:

- Runtime binding, invocation success, resource readiness, or dependency closure.
- Actual empty/nonempty outputs or response delivery.
- Numeric correctness under an unobserved compiler/encoding.
- Durable balances, rollback, isolation, reset, or safe repetition.
- EOF storage values, complete reports, or numerical duplication.
- Full branch coverage, exhaustive semantic completeness, or transferability.

## Section 5: Execution Protocol

**This template section is restricted to documentary prerequisites and evidence acceptance rules. It authorizes no execution and supplies no commands or implementation tasks.**

Any later empirical activity would require separate authorization, an externally reviewed frozen specification, and concrete evidence for the dependencies below. Documentary acceptance cannot satisfy those empirical prerequisites.

### 5.1 Harness Dependencies Not Declared in the Contract

No harness is selected or created.

| Capability needed for a later empirical assertion | How this backend supplies it | Declared in contract? | Upstream owner |
|---|---|---|---|
| Actual invocation/binding and lifecycle attribution | Unestablished; INV requires references and actual evidence | External responsibility; no public control | Stage 7 §2.1; G-25 |
| Daily/category/reporting input supply and identification | Unestablished; RES requires owner and preparation provenance | External; not request properties | Stage 6 D-14; Stage 7 RES |
| Account/xref/category/disclosure/type resource setup | Unestablished | Internal dependencies; no provisioning surface | Stage 5 §6; Stage 6 C-13 |
| Interest parameter and reporting date supply | Unestablished; no job-literal default | External | Stage 6 C-2/C-3/C-6/C-8 |
| Capture channels, framing, freshness and occurrence attribution | Unestablished | No public capture facility | Stage 7 CAP; G-26 |
| Deployed encoding/sign/display interpretation | Unestablished | No new conversion policy | Stage 7 CONV; G-27 |
| Failure-event interpretation and knowledge timing | Unestablished | Response conditions only | Stage 7 FAIL; G-28 |
| Persistent-state observation, reset and isolation | Not demonstrated or promised | Unsupported as public capabilities | Stage 6 C-13/C-14; Stage 7 STATE |
| Clock control or deterministic generated timestamps | Not supplied and not required by these documentary expectations | No | R-3/R-11; Stage 6 C-4 |
| Concrete EOF/configuration/external routine evidence | Unavailable | Not public controls | A-14/A-16/A-17; G-30 |

A different backend would need separately declared means for every applicable external dependency. Their availability and transferability cannot be presumed. A newly required capability absent from upstream scope must be escalated, not silently supplied.

### 5.2 Oracle Convention Pre-Modeling

The following conventions are documented before any empirical use; no executable oracle is constructed.

| Convention | Required documentary treatment | Authority |
|---|---|---|
| Signed quantities | Retain signed additions; no absolute-value debit normalization | R-4/R-5/R-10 |
| Interest arithmetic | Retain literal formula and receiving-field distinction; do not invent rounding, units, overflow results, or a numeric tolerance | R-10; A-12 |
| Numeric-to-string representation | Require supported sign/implied-decimal decoding and raw-span provenance | Stage 7 CONV; C-6/C-9 |
| Text/padding | No silent trimming, padding replacement, date parsing, or restored descriptions | C-7; CONV |
| Report values | Compare represented receiver text within an established conversion basis; do not recalculate totals | R-14/R-16; C-7/C-8 |
| Preliminary reasons | Existing public enum 100–103, selected reason only; 109 remains internal | R-2/R-5; C-5 |
| Order/multiplicity | Occurrence-based, not identifier-set-based; posting streams separate; reporting mixed sequence | D-15; CAP |
| Empty versus unavailable | Positive-empty requires its own evidence basis; zero bytes and silence are insufficient | Revised D-16; CAP |
| Generated identifiers/timestamps | Capture values; do not synthesize from source literals or assume uniqueness | R-3/R-11 |
| EOF | Retain conditional source deductions; no buffer-retention default or finalization repair | R-8/R-12/R-15 |

If a concrete expectation requires an unresolved convention, that expectation remains non-conformance-bearing until appropriately resolved.

### 5.3 State, Failure and Observation Matrix

All resources inherit the requirement to distinguish **preparation evidence, attempted effects, observed effects, and durable effects**. No global “stateful” label replaces resource-specific accounting.

| Resource | Scenario(s) | Contract or external provision | Evidence required for a later claim | Current basis |
|---|---|---|---|---|
| Posting daily sequence | V-1/V-15/V-18 | External; C-1 | RES input identity/origin/order/window; INV association | Unresolved |
| Posting card association | V-15 | Internal; C-13 | RES card-key resource attribution | Unresolved |
| Posting account | V-16/V-17 | Internal; C-10/C-13 | STATE initial authority and separately supported effects | No durable claim |
| Posting category balance | V-17 | Internal; C-10 | Create/update provenance; local flag versus persistent state | No reset claim |
| Posting transaction output | V-14/V-19 | C-5 | CAP occurrence attribution/order plus CONV | Snapshot alone insufficient |
| Posting reject output | V-14/V-15 | C-5 | Separate CAP, original candidate/trailer mapping | Count not write evidence |
| Posting controls/counts | V-18 | Conditional progress; C-5 | Attributable displayed counts | Declarations not observations |
| Interest category sequence | V-20/V-21/V-23 | External; C-2 | RES encountered order/group basis | Global grouping unknown |
| Interest account | V-23 | Internal; C-11 | Transition/update evidence separate from generated output | Final state unknown |
| Interest account-key xref | V-20/V-24 | Internal; C-13 | Actual alternate-key binding and attribution | Multiplicity unknown |
| Interest disclosure | V-21 | Internal; C-6 | Resource/read/rate attribution | Missing not zero |
| Interest identifier parameter | V-24 | External; C-6 | Actual supplier/value/window | No default |
| Interest group accumulation/control | V-23 | Internal; C-11 | Local transition scope | No inter-call isolation |
| Interest suffix | V-24 | Internal; C-14 | Actual construction-state attribution if claimed | No uniqueness/reset claim |
| Interest generated output | V-20/V-22 | C-6 | CAP/CONV, including positive-empty basis | No update receipt |
| Reporting transaction sequence | V-27/V-28 | External; C-3 | Input/order/flow attribution | EOF storage unknown |
| Reporting date resource | V-27/V-29 | External; C-3/C-8 | Separate date provenance | No default range |
| Upstream reporting selection | V-27/V-33 | External/documentary | Actual-flow evidence distinct from JCL text | Unestablished |
| Reporting card association | V-30/V-31 | Internal; C-8 | Card-key association and ordering | No account cardinality |
| Reporting type descriptions | V-26 | Internal; C-7 | Lookup/receiver distinction | No restoration |
| Reporting category descriptions | V-26 | Internal; C-7 | Separate lookup/receiver attribution | No restoration |
| Reporting page accumulation | V-28 | Internal; C-8 | Local add/transfer/reset evidence if claimed | No reconciled total |
| Reporting account accumulation | V-28/V-31 | Internal; C-8 | Card-change total/reset scope | No EOF account total |
| Reporting grand accumulation | V-28 | Internal; C-8 | Page-to-grand provenance | No global completeness |
| Reporting controls/presentation | V-25/V-31 | Internal; C-7/C-8 | Occurrence classification and line-count distinction | No twenty-detail promise |
| Report output | V-25/V-26/V-29/V-30 | C-7/C-8 | Mixed CAP order, exclusions and field mappings | No complete-empty claim |
| Transaction backup | V-33 | External; all tracks | Actual backup/restoration evidence if claimed | Instructions only |
| Combined intermediate | V-33 | External; posting/interest | Actual generation/load provenance | No merged-state claim |
| Master lifecycle context | V-33 | External; all tracks | Separate live-instance and lifecycle evidence | Names not identity |
| Procedure control | V-33 | External; all tracks | Authorized missing-control evidence | REPROCT unavailable |
| External failure routine | V-6/V-32 | External; each track | Actual event meaning and knowledge boundary | Call sites only |

V-7–V-11 apply to every relevant capture or conversion channel above; V-12 applies to every reset/isolation assertion; V-34 requires each resource and consuming track to retain a disposition.

HTTP acceptance, legacy reachability, output observation, effects, and oracle assessment must remain separate propositions. One must not stand in for another.

### 5.4 Evidence Rejection and Uncertainty Handling

The specification distinguishes:

- **Documentary violation:** a proposed mapping contradicts a determinate clause or protocol, such as mapping stale capture to current content.
- **Insufficient evidence:** required attribution, framing, conversion, or observation support is absent.
- **Unresolved empirical uncertainty:** the obligation is specified, but its satisfaction depends on actual evidence unavailable here.
- **Upstream conflict:** faithful representation would require changed semantics, fields, statuses, or controls.

These are prospective classification criteria, not findings issued by this artifact. No DIV-n result is created.

Known licensed content must not be discarded to avoid a conflict. Conversely, a damaged required field must not be invented merely to retain an otherwise incomplete record.

## Section 6: Exploratory Expansion

No exploratory expansion is included or authorized.

No campaign budget, seed, operation count, fuzzer, property generator, fixture set, or instrument is selected. These are **not applicable to this documentary-only scope**, not zero-valued empirical measurements.

Legacy-characterization scenarios identify conditional documentary questions only. Any later empirical exploration would require separately declared scope and provenance; it cannot retroactively alter these expected obligations.

## Ambiguities and Deferred Obligations

Inherited ambiguity identifiers remain unchanged:

| IDs | Stage 8 treatment |
|---|---|
| A-1/A-8 | Preserve separate tracks, unresolved cohesion, live identity and chronology |
| A-2/A-16 | Preserve dependency and operational-flow limits, including missing REPROCT |
| A-3/A-12 | Preserve deployed encoding, numeric/temporal policy and identifier uncertainties |
| A-4/A-10/A-17 | Preserve durability, isolation, partial effects and external-failure uncertainty |
| A-9 | Retain static precedence and internal 109 timing without invented policy |
| A-11 | Retain conditional normal-EOF no-final-flush deduction |
| A-13 | Retain local fee-placeholder limit only |
| A-14/A-15 | Preserve reporting dates, EOF storage, grouping, totals and presentation uncertainty |
| A-5/A-6 | No independent-exposure or legal-clearance claim |
| A-7 | Upstream evidence-layout disposition remains unchanged |

G-21–G-24 retain contract limits. G-25–G-30 retain their documentary versus empirical distinction. The supplied structured Stage 7 r2 approval addresses its historical human-review entry requirement; it does not resolve runtime gaps.

New Stage 8 gaps continue the run-scoped sequence:

| ID | Classification | Required handling |
|---|---|---|
| **G-32** | Blocking for Stage 8 documentary gate | External human review of this exact specification remains absent |
| **G-33** | Blocking for exact-version review finalization | Output persistence/digest and bound Stage 8 review record are not established by this response |
| **G-34** | Deferred empirical obligation | Actual INV/RES/CAP/CONV/FAIL/STATE/RESP evidence remains unavailable; no runtime satisfaction claim |
| **G-35** | Blocking for stronger concrete expectations | Unresolved conversion, numeric, state, failure and EOF premises must not be guessed |
| **G-36** | Blocking for completeness certification | Independent substantive reconciliation of all scenario, field, resource, clause and protocol destinations remains external; no mechanical check was performed |

G-34 is not a requirement to execute now. G-35 does not invalidate determinate documentary criteria; it blocks stronger outcome claims requiring unsupported premises.

## Completeness Gate (Plan) and Execution Entry Condition

All conditions remain unchecked:

- [ ] All scenarios have upstream anchors, named oracles, setup premises, expected obligations, and evidence acceptance criteria.
- [ ] Every scenario is typed conformance or legacy characterization and separately classified positive, negative, or counterexample.
- [ ] Posting, interest, and reporting each receive separate substantive review.
- [ ] Exact capability identity and current upstream authority are retained.
- [ ] INV, RES, CAP, CONV, FAIL, STATE, and RESP each have explicit obligation destinations.
- [ ] Every C-1–C-14 and R-1–R-20 has a scenario or explicit unresolved uncertainty destination.
- [ ] Field and resource accounting contains no silent omissions.
- [ ] Stale, misattributed, truncated, absent, zero-length, inconclusive empty capture, and positive-empty observations remain distinct.
- [ ] Available `items: []`, unavailable/503, and known technical failure/500 retain their different predicates.
- [ ] Known content, order, multiplicity, and partial content are not silently discarded.
- [ ] Internal reason 109 remains outside preliminary rejection and public diagnostics.
- [ ] Interest and reporting EOF limitations are retained without repair.
- [ ] Empty reporting observations do not become complete-empty-report claims.
- [ ] State reset, isolation, durability, and repetition are not presented as demonstrated.
- [ ] Undeclared external dependencies and unresolved oracle conventions remain explicit.
- [ ] Historical reviews and source anchors are not treated as runtime proof.
- [ ] Exact inputs, original pins, numbered representations, revision provenance, and this output are retained for review.
- [ ] External human review records its decision separately.

**No gate is approved by this document.** The present authorization permits specification only; even a future documentary approval would not by itself enlarge that authorization into empirical activity.

### Provenance and Current Status

AI assistance is limited to drafting this specification from the supplied approved/current chain, corpus19 text and numbered representations, pin register, review/findings records, and generic semantic-validation template/rules.

No tools, external retrieval, additional model/network calls, source modifications, implementation, generated tests, COBOL/JCL execution, runtime validation, or filesystem writes were performed. Provider settings, transport retention, timing, usage, and costs are not certified.

**This artifact contains documentary scenarios and acceptance criteria only. It reports no executed outcomes, observed divergences, conformance verdict, or approval.**
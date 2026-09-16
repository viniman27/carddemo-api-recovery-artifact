# Adapter Behavior Specification

## Purpose

This Stage 7 specification documents proposed adapter responsibilities for realizing the approved/current Stage 6 r3 contract over the unchanged AWS CardDemo legacy in run `E3-01`.

**Posting, interest, and reporting are mandatory, separately traceable tracks.** Their presentation order below is contract-document order, not a prescribed cross-job execution schedule.

| Attribute | Value |
|---|---|
| Run | `E3-01` |
| Stage | `7` |
| Feature | `adapter-behavior-carddemo` |
| Artifact | `specs/adapter-behavior-carddemo/requirements.md` |
| Exact inherited capability identity | `unselected-stage-1-scope-only` |
| Immediate upstream | `specs/api-contract-carddemo-r3/spec.json` |
| Status | Documentary draft; proposed adapter responsibilities |
| Human approval | `false` |
| Completeness gate passed | `false` |
| Ready for implementation | `false` |

The specification maps contract clauses to binding, delegation, observation, representation, and error responsibilities. It does not establish an installed adapter, executable binding, actual resource availability, runtime observations, or completed business effects.

## Adapter Integrity Discipline

- The adapter realizes the contract; it never reinterprets it. Any needed deviation requires upstream revision, not an adapter workaround.
- Legacy-facing responsibilities remain subordinate to approved Stages 3-r2, 4, 5, and 6 r3.
- Legacy source and copybooks remain read-only. General framework permission for environment preparation does not authorize preparation in this documentary task.
- Business rules remain in the legacy core. The adapter must not recalculate business outcomes, repeat preliminary checks, compensate partial effects, or repair omitted finalization.
- Implementation technology is not selected here. Framework examples do not establish this run’s process model, runtime, binding, storage, or observation channel.
- Proposed acquisition responsibilities are distinguished from demonstrated acquisition. A source write statement is not an observed output; a source counter declaration is not runtime telemetry.
- Available empty sequences, unavailable observations, zero values, and known technical failures remain distinct.
- No new public fields, operations, provisioning facilities, selectors, readiness assertions, EOF signals, recovery mechanisms, or lifecycle guarantees are introduced.

Normative statements below describe **proposed Stage 7 responsibilities**, not demonstrated runtime behavior. They introduce no new semantic rules or contract decisions.

## Section 1: Upstream Authority and Entry Condition

### 1.1 Upstream Authority and Scope Inheritance

The entry basis is the supplied approved chain comprising Stages 1, 2-r2, 3-r2, 4, 5, and Stage 6 r3, with their authorizations and review records.

| Authority relative to `RUN_ROOT` | Supplied SHA-256 |
|---|---|
| `specs/pipeline-scope-carddemo/requirements.md` | `1362fab5d55b77ef6121328606ae974295cd5723849520e9a246f4bd45e64cc9` |
| `specs/capability-selection-carddemo-r2/requirements.md` | `abdb59180f379d9e14eb86dfa1d8226ec50c981346767e808fd382eb7462bbc4` |
| `specs/legacy-evidence-carddemo-r2/requirements.md` | `4566786600b60e9377c1e369e67765098d06b0153ba973361d2065614a6c9b7b` |
| `specs/capability-semantics-carddemo/requirements.md` | `2f9d3ee52dd7788e206810e38c9173b19d21dfc44270cdd06d05e62dec95eb93` |
| `specs/canonical-data-boundary-carddemo/requirements.md` | `208d04fe6f9cae665dfa4cb514de5d4ad9eaf0ebc169dfae0fd8a6ba209e66f3` |
| `specs/api-contract-carddemo-r3/requirements.md` | `6cba102f8335843b46e75a77b1a71d4e56373a95d5ac63cf645491556c443b27` |
| `specs/api-contract-carddemo-r3/spec.json` | `2ec40d54f4d89198ccc9e0cac602ba4192ee063290d9f226c0b1ac101899a0bd` |
| `reviews/stage-6-r3-authorization.json` | `0c5228634cb0f3b3c779fafe2e7e9ae5109aebeb24b116268e73a9a00dd8213e` |
| `STAGE6-R3-COUNTEREXAMPLE-REVIEW.md` | `a8e41764b56018f530a2df96d75bff483086e84b2462fca156175b0f91be7159` |
| `specs/api-contract-carddemo-r3/stage6-r3-verification.json` | `69a59af451a700f8de1d4711f64149ce5bd295ced79bcee1747caf2aefee0193` |

The supplied Stage 6 r3 authorization approves the documentary contract, including external-input empty requests, ordered observation envelopes, and HTTP status design, and authorizes this Stage 7 specification only.

Historical draft-era statements in Stage 6 and its review remain historical. The supplied subsequent authorization establishes current upstream approval; this document neither rewrites that history nor grants another approval.

The supplied gate-check result is `current`, with `ok: true` and `human_approval_granted: false`. It is an inherited freshness report, not a check performed here.

#### Exact input and revision retention

The complete supplied `input_pins` register is incorporated by reference without alteration. Its six upstream metadata pins, six artifact pins, six authorizations, five review attachments, eight Stage 6 revision-history pins, source-package pin, 19 original/derived source-pin pairs, and 13 framework pins remain distinct.

In particular:

- Current Stage 6 r3 authority must not be replaced by historical materialization-time metadata hashes.
- The r2 artifact, its retained generated copy, request, metadata, generation authorization, empty-output review, and directed feedback remain revision provenance—not current contract authority.
- The r2 nonempty-output restriction must not be reintroduced.
- Stage 4 and Stage 5 review attachments remain inherited documentary review evidence, not newly performed reviews or runtime observations.

The governing template is `settings/templates/pipeline/adapter-behavior-spec.md`, SHA-256 `4a563f2bbb4db976c614cff722a90934041df3b76db0c3695386970871b47687`.

The source package retains SHA-256 `63ba5c47ecb21349549744b912af3b150654e7e435724dba499e3c88369f15a2`.

All 19 supplied corpus entries retain their full paths, exact `content`, stable 1-based `numbered_lines`, original byte pins, and separate derived-representation pins. These documentary mappings do not replace those evidence objects. No hash recomputation or filesystem inspection is claimed.

### 1.2 Inherited Constraints and Decisions

| Upstream decision or clause | Binding Stage 7 responsibility |
|---|---|
| Stage 5 D-2; C-1–C-3 | Keep track-qualified input, dependency, and observation identities; no merged cycle or global transaction lifecycle |
| Stage 5 D-3; C-4; D-12 | Keep internal dependencies and `AttemptState` descriptions out of public payloads |
| Stage 5 D-4; C-13/C-14 | Do not claim atomicity, rollback, durable partial persistence, reset, isolation, or repetition safety |
| Stage 5 D-5; D-10/D-11; C-9 | Preserve contract representation without inventing conversion or business-validation policy |
| Stage 5 D-6; C-8/C-11 | Do not add interest final flush, report final account total, corrected filtering, or reconciled totals |
| Stage 5 D-7/D-8; C-4/C-7 | Preserve bounded report content; exclude unlicensed presentation mechanics and declaration-only meanings |
| D-14 | Required empty closed requests carry no business inputs, resource selectors, or EOF |
| D-15 | Preserve sequence order and multiplicity; no deduplication or regrouping |
| Revised D-16; C-12 | Actual available observations—including empty sequences—may support 200; no observation does not |
| D-17 | Unavailability cannot be used to discard known licensed content |

## Section 2: Adaptation Model

### 2.1 Adaptation Strategy

The proposed strategy is wrapping the unchanged legacy core. The adapter’s responsibilities are limited to:

1. Recognizing the called contract operation and its existing structural request constraints.
2. Connecting that operation to an externally established legacy invocation and resource context, **only where a justified binding exists**.
3. Acquiring actual contract-licensed observations from that context.
4. Representing those observations faithfully using Stage 6 r3 envelopes.
5. Applying the approved response classification to what is actually known.

No concrete invocation or capture mechanism is demonstrated. Missing binding authority is G-25; missing acquisition authority is G-26. These gaps do not authorize a substitute business implementation.

No reference implementation or reference runtime is supplied as an executable observation source. Framework examples of reference layers are not bindings for this run.

#### External input binding responsibilities

“External setup authority” below denotes responsibility outside the HTTP consumer request. Its actual actor, mechanism, resource instance, and availability are unresolved.

| Track | Consumer supplies | External setup supplies | Legacy internally consumes or maintains | Unknown input/EOF boundary |
|---|---|---|---|---|
| posting | Required `PostingRequest`: empty closed object | Daily candidate sequence and its values; hosting/bindings for referenced resources | Card xref, account comparison/balance fields, category balances, reason/flags/counters, timestamp construction | Actual daily input instance, contents, order, readiness, and end condition; request is not EOF |
| interest | Required `InterestRequest`: empty closed object | Encountered category sequence; identifier parameter text; resource hosting/bindings | Account, account-key xref, disclosure reads/fallback, group accumulation, suffix, timestamp construction | Actual grouping, parameter value/validity, alternate-key binding, readiness, and input end condition |
| reporting | Required `ReportingRequest`: empty closed object | Reporting transaction sequence; separate date input; any actual upstream selection result and operational context | Card xref, type/category lookup values, current card, accumulators, report presentation state | Actual order, date contents, date-input EOF, post-read storage, executable upstream flow |

The adapter must not populate missing external values from job literals, request emptiness, prior calls, another track’s output, or model-generated values.

#### Documentary binding references

| Track | Documentary relationship | Limit |
|---|---|---|
| posting | `app/jcl/POSTTRAN.jcl:23-42` names `CBTRN02C`, daily input, xref/account/category resources, transaction output, and rejects | Dataset literals do not establish a live instance, availability, or adapter access |
| interest | `app/jcl/INTCALC.jcl:22-41` names `CBACT04C`, parameter text, category/account/xref/disclosure resources, alternate-index path, and generated output | The literal parameter is not an adapter default; alternate-key access remains an external binding question |
| reporting | `app/jcl/TRANREPT.jcl:37-80` distinguishes SORT selection from the later program’s transaction/date/lookup bindings | No common date override, executed SORT result, or ready input is established |
| posting, interest | `app/jcl/COMBTRAN.jcl:20-48` describes combination and loading | Not adapter-owned orchestration or demonstrated merged state |
| all three | `app/jcl/TRANBKP.jcl:19-67`; `app/proc/REPROC.prc:19-29` | Backup/delete/define instructions are not reset evidence; `REPROCT` remains unavailable |

### 2.2 Semantic Authority Statement

Stage 6 r3 governs the surface and response representation. Stage 5 governs canonical meanings and state exclusions. Stage 4 R-1–R-20 governs inherited semantic limits, grounded in Stage 3-r2 E-1–E-35 and the exact corpus.

The adapter must escalate a conflict rather than resolve it through convenience normalization. No new D-n decision is used here to alter the contract.

#### Observation acquisition and provenance

For each represented observation, the proposed adapter responsibility is to establish its originating legacy invocation/context, source channel or resource, represented occurrence sequence, and faithful field mapping. This is an evidentiary responsibility—not a new public provenance schema, telemetry service, or durable logging guarantee.

All runtime acquisitions below are **currently undemonstrated**.

| Observable | Proposed acquisition responsibility | Source basis | Unavailable/fabrication boundary |
|---|---|---|---|
| Posting `outputs` | Obtain actual transaction output content attributable to the called posting operation; map the observed transaction fields | E-9/E-10/E-26; `app/cbl/CBTRN02C.cbl:424-442`, `562-579`; `app/cpy/CVTRA05Y.cpy:5-17` | Do not reconstruct outputs from daily inputs or presumed successful checks. Indexed-file contents alone do not establish occurrence order/multiplicity; G-26 |
| Posting `rejections` | Obtain actual reject content, preserving original candidate fields and its selected trailer reason/description | E-4/E-9/E-27; `app/cbl/CBTRN02C.cbl:176-182`, `446-465`; `app/cpy/CVTRA06Y.cpy:5-17` | Do not synthesize rejects from internal reasons or failed lookups |
| Posting `progress` | Obtain actual displayed processed/rejected counts attributable to this invocation | E-7; `app/cbl/CBTRN02C.cbl:227-230` | No observed display means unavailable, not declared initial zeros or counts reconstructed from arrays |
| Interest `outputs` | Obtain actual generated transaction records in their represented sequence; map every required field from those observations | E-14/E-26; `app/cbl/CBACT04C.cbl:473-515`; `app/cpy/CVTRA05Y.cpy:5-17` | Do not compute amounts, reconstruct suffix-based identifiers, or generate timestamps in the adapter |
| Reporting header records | Obtain actual emitted report-name/header context and its date fields | E-17/E-28; `app/cbl/CBTRN03C.cbl:274-284`, `324-341`; `app/cpy/CVTRA07Y.cpy:4-13` | Source literals alone do not establish that a header occurred |
| Reporting detail records | Obtain actual report receiver values from observed detail output | E-18/E-28; `app/cbl/CBTRN03C.cbl:361-374`; `app/cpy/CVTRA07Y.cpy:15-31` | Do not replace truncated descriptions with lookup descriptions or rebuild amount presentation |
| Reporting total records | Obtain actual page/account/grand-labelled output values and retain their occurrence positions | E-17/E-28; `app/cbl/CBTRN03C.cbl:293-322`; `app/cpy/CVTRA07Y.cpy:50-66` | No summing details, zero-filling absent totals, invented total account IDs, or page numbers |
| Available empty sequence | Obtain a positive observation that the represented sequence contains no items within its attributable observation scope | Revised D-16; Stage 6 r3 §3.4 | Missing file, absent capture, no console text, or failed acquisition is not evidence of emptiness |
| Known technical failure | Obtain actual evidence establishing technical failure at the response boundary | C-12; R-18; E-11/E-15/E-19 | Source error paths show possible failures, not that one occurred; exact detection remains G-28 |
| Envelope/error metadata | Supply exact contract constants, track attribution, discriminator, and category based on justified observations/classification | D-10, D-13–D-17; C-12 | These are representation fields, not measurements of completion, durability, or readiness |

For all content components, every Stage 6 r3 required field must come from the appropriate observed content. Unknown required fields must not be filled with null, zero, empty text, copied values, or reconstructed business outcomes. Faithful conversion limits remain G-27.

## Section 3: Operation Behavior Mappings

### 3.1 POST /posting — Posting

- **Contract clauses:** C-1, C-5, C-9, C-10, C-12–C-14; D-14–D-17.
- **State interaction:** External daily input; legacy-internal xref, account, category balance, counters and flags; separate transaction/reject output resources.
- **Runtime status:** Proposed delegation/acquisition only; no demonstrated binding.

#### Ordered behavior responsibilities

1. Apply the existing required empty-object representation boundary. No business fields are extracted, inferred, or supplied from the request.
2. Associate the operation with a justified external posting context; do not invent input selection, provisioning, or readiness.
3. Delegate posting to unchanged `CBTRN02C` behavior. Preserve the distinction between preliminary selection and subsequent write attempts.
4. Acquire transaction output, rejection output, and progress independently using Section 2.2’s provenance requirements.
5. Preserve order and duplicates within each available stream. Do not create a cross-stream transaction/rejection order.
6. Represent each channel as actually available or unavailable, then apply Section 5’s status boundary.

#### Rule enforcement points

| Rule | Legacy enforcement point and adapter constraint |
|---|---|
| R-1 | `app/cbl/CBTRN02C.cbl:202-219`: pre-posting selection; adapter does not repeat selection |
| R-2 | `app/cbl/CBTRN02C.cbl:370-422`: guarded account lookup and comparison order; preserve selected 100–103 reason, including later 103 replacing 102 |
| R-3 | `app/cbl/CBTRN02C.cbl:424-465`: posted transaction differs from original candidate/reject context |
| R-4/R-5 | `app/cbl/CBTRN02C.cbl:467-560`: category/account changes remain legacy operations; signed negative amounts are not absolutized |
| R-6 | `app/cbl/CBTRN02C.cbl:440-442`, `562-579`: category, account, transaction attempts remain ordered; no atomicity inference |
| R-18/R-20 | External failure consequences and repetition safety remain unresolved |

**Internal reason 109:** At `app/cbl/CBTRN02C.cbl:554-560`, account rewrite may assign 109. Under the approved normal-return deduction, the caller proceeds to transaction writing without rechecking the reason. The adapter must not turn 109 into a preliminary rejection, increment a reject count, expose a diagnostic field, or impose a new stopping rule. A separately established technical failure follows C-12; no new 109-specific HTTP mapping is created.

#### Outcome mapping

- Available transactions and preliminary rejections may coexist.
- Preliminary rejection is content, not 400.
- An available empty transaction or rejection sequence may support 200 absent known technical failure.
- Available progress alone—including both counts zero—may support 200 **as progress observation only**.
- Zero counts do not establish no effects, input exhaustion, output fulfillment, durable rejects, or durable transactions.
- All three channels unavailable with no known technical failure yields 503 with no represented observation.
- Known technical failure yields 500, optionally retaining actual available observations.
- Source EOF handling at `app/cbl/CBTRN02C.cbl:345-369` does not create an HTTP EOF signal or universal completion observation.

### 3.2 POST /interest — Interest Transaction Generation

- **Contract clauses:** C-2, C-6, C-9, C-11–C-14; D-14–D-17.
- **State interaction:** External category sequence and identifier parameter; internal account/xref/disclosure/group/suffix state; generated transaction output.
- **Runtime status:** Proposed delegation/acquisition only; no demonstrated binding.

#### Ordered behavior responsibilities

1. Apply `InterestRequest`’s required empty closed shape without deriving category records or parameter text.
2. Retain category input and identifier parameter as separately externally supplied dependencies. Do not substitute `INTCALC`’s literal parameter as a default.
3. Delegate unchanged interest behavior; leave account transitions, disclosure selection, arithmetic, suffix construction, and timestamps inside the legacy.
4. Acquire actual generated transaction observations. Do not infer output solely from a rate, input count, diagnostic display, or formula.
5. Preserve output sequence order and multiplicity, including equal identifiers and zero/negative amounts.
6. Represent actual availability and apply Section 5’s status boundary.

#### Rule enforcement points

| Rule | Legacy enforcement point and adapter constraint |
|---|---|
| R-7 | `app/cbl/CBACT04C.cbl:188-213`, `350-413`: encountered account transitions govern prior-group updates |
| R-8 | `app/cbl/CBACT04C.cbl:188-228`, `325-348`: normal pre-test EOF path does not flush final account |
| R-9 | `app/cbl/CBACT04C.cbl:415-460`: status-specific default disclosure reread, not missing-to-zero substitution |
| R-10 | `app/cbl/CBACT04C.cbl:214-217`, `462-470`: nonzero rate selects computation/write; no adapter formula or positivity guard |
| R-11 | `app/cbl/CBACT04C.cbl:473-520`, `613-626`: local record construction and bounded fee placeholder remain unchanged |
| R-18/R-20 | No external failure, persistence, identifier lifetime, or repeat-safety guarantee |

#### Outcome mapping

- Available generated observations support 200 absent known technical failure, including positively observed `items: []`.
- An empty sequence does not disclose whether the cause was zero rate, no encountered records, another source path, or a bounded observation scope.
- Zero rate, missing disclosure, and a generated record with zero quantity remain distinct.
- No interest progress counter, fallback event, suffix state, fee value, or account-update receipt is exposed.
- Generated transaction observations do not attest final-account rewriting.
- Unavailable output and no known technical failure yields 503 with no represented observation.
- Known technical failure yields 500 with optional actual available content.
- The adapter supplies no final flush, EOF repair, or parameter-validity policy.

### 3.3 POST /reporting — Transaction Reporting

- **Contract clauses:** C-3, C-7–C-9, C-12–C-14; D-14–D-17.
- **State interaction:** External transaction/date inputs and upstream selection context; internal lookup/card/accumulation/presentation state; report output.
- **Runtime status:** Proposed delegation/acquisition only; no demonstrated binding.

#### Ordered behavior responsibilities

1. Apply `ReportingRequest`’s empty closed shape without introducing date fields, selectors, or overrides.
2. Keep the reporting date input distinct from the upstream SORT literals and any actual selected transaction sequence.
3. Delegate unchanged reporting behavior, including date comparison before post-read EOF assessment and source-defined sentence exit.
4. Acquire actual report output and identify contract-licensed header, detail, and total occurrences from justified provenance.
5. Produce one mixed `records` sequence retaining represented occurrence order and duplicates. Exclude only the presentation mechanics already excluded upstream.
6. Preserve bounded receiver text and source-labelled totals, then apply Section 5’s status boundary.

#### Rule enforcement points

| Rule | Legacy enforcement point and adapter constraint |
|---|---|
| R-12 | `app/cbl/CBTRN03C.cbl:170-243`: date alternative leaves the loop sentence; no skip-and-continue replacement or default date |
| R-13 | `app/cbl/CBTRN03C.cbl:181-196`, `484-512`: card change triggers account-labelled grouping; no account regrouping |
| R-14 | `app/cbl/CBTRN03C.cbl:287-322`: distinct accumulator/output sites; no adapter reconciliation |
| R-15 | `app/cbl/CBTRN03C.cbl:173-204`: conditional EOF finalization, extra addition, no final account-total call |
| R-16 | `app/cbl/CBTRN03C.cbl:274-374`; `app/cpy/CVTRA07Y.cpy:4-66`: bounded presentation and non-detail counter increments |
| R-17 | `app/jcl/TRANREPT.jcl:37-74`: separate upstream selection and program dates |
| R-18/R-20 | Failure may follow earlier output attempts; no durable output or repetition guarantee |

#### Outcome mapping

- Available records support 200 absent known technical failure, including positively observed empty records.
- Header-only or total-only observations remain those observations; missing details do not license replacing them with an empty sequence.
- Empty records do **not** certify a complete empty report, full-range processing, zero/reconciled totals, final account totals, or input exhaustion.
- Missing totals are not zero; grand totals are not reconstructed from details.
- A prior account-total attempt may precede a failing new-card lookup. Actual available earlier content must not be erased merely because failure is known.
- Unknown post-EOF storage must not be treated as retained, cleared, or zero. Conditional duplicate contribution must not be asserted or corrected.
- Unavailable records and no known technical failure yields 503 with no represented observation.
- Known technical failure yields 500, optionally retaining actual available records.

## Section 4: State and Session Model

### 4.1 State Realization and Setup Boundary

No session model, process-per-request model, shared singleton, concurrency strategy, persistent initialization mechanism, or resource reset is selected.

In the table below, **unestablished** means no concrete runtime mechanism or observation is supplied—not that the resource is absent. For every row, actual lifetime, inter-call isolation, and durable failure effects remain subject to C-13/C-14. Source-local initialization or reset is not persistent-resource restoration.

| Resource / requirement | Contract clause or external setup | Concrete mechanism | Observable reset/isolation check |
|---|---|---|---|
| Posting daily sequence | C-1; external input | Documentary daily-file binding only; actual instance unestablished | Unavailable |
| Posting card association | C-4/C-13; internal xref | Legacy card-key read; external hosting unestablished | Unavailable |
| Posting account | C-10/C-13; internal state | Legacy read/rewrite; actual storage binding unestablished | Unavailable |
| Posting category balance | C-10/C-13; internal state | Legacy create/update sites; no adapter initialization mechanism | Local create-flag reset is not isolation evidence |
| Posting transaction output | C-5; output observation | Indexed output acquisition/order mechanism unestablished | OUTPUT open is not reset evidence |
| Posting reject output | C-5; output observation | Sequential reject acquisition unestablished | Unavailable |
| Posting control/counts | C-5; flags internal, progress conditional | Source initialization and displays; capture unestablished | Declared zeros are not observed reset |
| Interest category sequence | C-2; external input | Sequential category access; actual input binding unestablished | Unavailable |
| Interest account | C-11/C-13; internal state | Legacy transition-time rewrite | Cycle clears are not resource reset |
| Interest account-key xref | C-4/C-13; internal dependency | Alternate-key read; actual index binding unestablished | Unavailable |
| Interest disclosure | C-6; internal dependency | Legacy initial/default reads | Unavailable |
| Interest identifier parameter | C-2/C-6; external basis | Linkage participation documented; actual parameter binding unestablished | No lifetime/reset evidence |
| Interest group accumulation/control | C-11; internal | Source-local transition state/reset | No inter-call isolation evidence |
| Interest suffix | C-6/C-14; internal | Source zero initialization and increment | No global uniqueness/reset evidence |
| Interest transaction output | C-6; observation | Sequential generated output acquisition unestablished | Unavailable |
| Reporting transaction sequence | C-3; external input | Sequential read; actual resource/order unestablished | Unavailable |
| Reporting date input | C-3/C-8; external input | Separate date-file read; contents unestablished | Unavailable |
| Upstream selection result | C-3/C-13; external context | SORT and dataset references only | No executed selection/isolation evidence |
| Reporting card association | C-4/C-8; internal | Legacy card-key lookup | Initial spaces are not inter-call isolation |
| Reporting type descriptions | C-7; internal lookup | Legacy read; actual values unestablished | Unavailable |
| Reporting category descriptions | C-7; internal lookup | Legacy read; actual values unestablished | Unavailable |
| Reporting page accumulation | C-8; internal | Legacy add/transfer/reset sites | Local reset only |
| Reporting account accumulation | C-8; internal | Legacy add/reset at card-triggered total site | Local reset only |
| Reporting grand accumulation | C-8; internal | Legacy page-to-grand accumulation | Initial zero is not runtime evidence |
| Reporting control/presentation | C-7/C-8; internal | Source first-time/line-counter state | No persistent reset/isolation evidence |
| Report output | C-7/C-8; observation | Sequential output; faithful acquisition unestablished | No complete-output/reset evidence |
| Transaction backup | C-4/C-13; external, all tracks | Documentary backup instructions | No completed backup or restoration evidence |
| Combined intermediate | C-4/C-13; external, posting/interest | Documentary combination/loading instructions | No merged-state/isolation evidence |
| Master lifecycle context | C-13; external, all tracks | Documentary delete/define/load references | No shared live identity or reset evidence |
| Procedure control | C-13; external dependency | `REPROCT` unavailable | Unavailable |
| External failure routine | C-12/C-13; each track | `CEE3ABD` call sites only | No termination/rollback evidence |

In-sequence legacy modifications and isolation between separate invocations are different questions. Neither process restart nor an HTTP response establishes persistent-resource reset. No observation from one track closes another track’s state gap.

## Section 5: Error and Edge Behavior

### 5.1 Partial Execution and Process Lifecycle

The proposed adapter must distinguish output acceptance from process completion and lasting state effects.

- Captured content is not proof of normal exit.
- Normal-exit text, if actually observed, is not proof of durable writes, complete input consumption, or flushed instrumentation counters.
- Posting category/account attempts can precede transaction-write failure.
- Interest transaction generation and account rewriting occur at different source sites.
- Reporting content attempts can precede later lookup or write failures.
- No rollback, compensation, automatic retry, or fallback execution is introduced.
- Timeout/crash detection, response feasibility, and process cleanup mechanisms are unestablished. A known technical failure follows C-12; mere missing observation does not establish one.
- No timeout value, cancellation semantics, exit-code taxonomy, or promise that every failure yields an HTTP response is added.

The source’s conditional posting return-code assignment of 4 is not automatically a technical-failure mapping. Likewise, file-status values, internal 109, and external-call arguments are not public HTTP statuses.

#### Response classification

| Boundary condition | Status/body responsibility | Observation treatment |
|---|---|---|
| Request fails the existing required empty closed object representation | 400 `InterfaceError`, `request_representation` | No fabricated legacy execution or output claim |
| Known technical failure at batch response boundary | 500 `InterfaceError`, `technical_failure` | Optional `availableContent` retains actual observations, empty or nonempty |
| No known technical failure; permitted observation available | 200 corresponding envelope | Posting: any output/rejection/progress available; interest: outputs available; reporting: records available |
| No known technical failure; no representable observation | 503 `InterfaceError`, `content_unavailable` | **Observations503: none**; no substantive observation represented |

Known technical failure takes precedence over 200 and 503 at the batch response boundary. Available empty sequences count as observations; they are not “none.”

Every represented envelope retains `completeness: "not_attested"` and `durability: "unknown"`. These are scoped contract constants, not false-valued completion or durability measurements.

#### Representation safeguards

- Available sequences include `items`, which may be empty.
- Unavailable sequences omit `items`; they do not contain fabricated empty arrays.
- Available progress includes actual `PostingProgress`; unavailable progress omits `value`.
- Error `availableContent`, when present, contains at least one actual permitted observation.
- A missing required content value or unjustified conversion remains a gap; it must not be concealed by dropping known records or relabelling a sequence empty.
- No readiness probe, retry hint, polling link, new error field, diagnostic stream, or public state lifecycle is added.

### 5.2 Bounded Gaps and Inherited Ambiguities

Gap identifiers continue after G-24. These are documentary gap records, not metadata edits or implementation tasks.

| ID | Classification and scope | Unjustified claim or missing basis | Required documentary handling |
|---|---|---|---|
| G-25 | Blocking for concrete binding claims; all tracks | No demonstrated invocation/resource binding, external input-instance association, or setup owner/mechanism | Retain track-specific external responsibility; require separately authorized binding evidence before claiming realizability |
| G-26 | Blocking for demonstrated observation acquisition | No exercised acquisition channel, occurrence attribution, order/multiplicity evidence, or positive-empty observation mechanism | Keep each observation source proposed; do not derive output from source statements, resource names, or absence of capture |
| G-27 | Blocking where faithful field representation would require guessing | Deployed encoding, numeric/text conversion, padding/trimming, and incomplete-record handling are unresolved | Preserve G-22; escalate representation conflicts rather than invent transformations or discard known content |
| G-28 | Blocking for concrete failure-detection mappings | No demonstrated response-boundary detection, external routine behavior, timeout/crash classification, or universal response feasibility | Retain C-12 predicates without assigning unsupported file/exit statuses or diagnostic causes |
| G-29 | Blocking for stronger state/lifecycle claims | No reset, isolation, durability, restart, or safe-repetition evidence | Preserve per-resource unknowns and G-23; no mechanisms inferred from local initialization or operational documents |
| G-30 | Blocking for concrete reporting completion claims | EOF storage, actual dates/job flow, and final numerical output remain unresolved | Preserve G-24 and conditional reporting behavior; no complete empty report or repaired totals |
| G-31 | Blocking for Stage 7 completion | No human review of this exact artifact, retained output digest, or new mechanical check is established | Keep approval external and bind any later review to exact retained versions |

Inherited G-21–G-24 are not closed by these mappings. Stage 6 approval accepts the documentary contract design; it does not establish runtime realization.

| Inherited ambiguity | Stage 7 propagation |
|---|---|
| A-1/A-8 | No merged business capability, resource identity, or cross-track schedule |
| A-2/A-16 | Dependency closure and operational executability remain unknown |
| A-3/A-12 | Representation, numeric, temporal, parameter, and identifier limits remain explicit |
| A-4/A-10/A-17 | No durability, isolation, external failure, or recovery guarantees |
| A-9 | Preserve preliminary reason precedence and internal 109 timing |
| A-11 | Preserve normal interest EOF without final-account flush |
| A-13 | Fee absence remains bounded to the inspected placeholder |
| A-14/A-15 | Preserve date/EOF, grouping, presentation, and total uncertainty |
| A-5/A-6 | No clean-exposure independence or legal-clearance claim |
| A-7 | Approved evidence namespace/layout remains unchanged |

Unknown is not false. No ambiguity is resolved merely by assigning an envelope discriminator or an HTTP status.

### 5.3 Contract-to-Behavior Traceability

| Contract authority | Adapter responsibility | Semantic/evidence basis | Gap |
|---|---|---|---|
| C-1 | Posting external binding and unchanged delegation | R-1–R-6; E-4/E-7–E-11/E-29 | G-25 |
| C-2 | Interest external category/parameter binding and delegation | R-7–R-11; E-5/E-12–E-15/E-30 | G-25 |
| C-3 | Reporting external input/date separation and delegation | R-12–R-17; E-6/E-16–E-19/E-31 | G-25/G-30 |
| C-4 | No extra surface or internal-resource exposure | R-18–R-20; Stage 5 D-3/D-7/D-8 | G-29 |
| C-5 | Observed posting fields, original rejection context, progress, internal 109 boundary | R-1–R-6; E-20–E-22/E-26/E-27 | G-26/G-27 |
| C-6 | Observed generated fields; distinguish missing disclosure, zero rate, zero quantity | R-7–R-11; E-20–E-23/E-26 | G-26/G-27 |
| C-7 | Actual report receiver text rather than reconstructed values | R-16; E-24–E-28 | G-26/G-27 |
| C-8 | Mixed ordered records, card-triggered totals, conditional finalization | R-12–R-17; E-16–E-18/E-28/E-31 | G-26/G-30 |
| C-9 | Existing structural request boundary only | D-10/D-11/D-14 | G-27 |
| C-10 | Ordered posting attempts; no atomic receipt | R-4–R-6; E-9–E-11 | G-28/G-29 |
| C-11 | No final interest flush or update receipt | R-7/R-8; E-12/E-14 | G-29 |
| C-12 | Evidence-based 200/400/500/503 classification | R-18; revised D-16/D-17 | G-26/G-28 |
| C-13 | Per-resource external/internal state accountability | R-6/R-18/R-19; E-29–E-34 | G-25/G-29 |
| C-14 | Repetition unknown separately for every track | R-20 | G-29 |

R-1–R-20 all retain a mapped responsibility or explicit limit. E-1–E-3 remain orientation; E-35 remains licensing context, not a business behavior. All other evidence retains its approved consuming-track attribution through the mappings above. This accounting is not proof of completeness.

## Section 6: Implementation Notes (non-authoritative)

No implementation technology, component structure, code, commands, build arrangement, source repair, or implementation task is specified.

The necessary distinction is between a **documented source of potential observations** and a **demonstrated means of acquiring them faithfully**. The former is identified here; the latter remains bounded by G-25–G-30.

AI assistance is limited to documentary mapping using the supplied approved chain, exact corpus text and numbered representations, generic template/rules, authorizations, and revision/review provenance. No tools, additional model/network calls, legacy execution, checksum computation, or filesystem modification were performed.

No runtime telemetry, tokens, costs, completion measurements, or provider retention settings are certified. `store=false` is not something this document can attest.

## Completeness Gate and Entry Boundary

The following conditions remain unchecked:

- [ ] Every contract operation has a separate behavior mapping with rule enforcement points.
- [ ] Every external input and legacy/reference dependency has a responsibility classification or bounded gap.
- [ ] Every public observation has a proposed source and an explicit acquisition/provenance limit.
- [ ] Positive empty observations remain distinct from unavailable observations.
- [ ] Posting progress-only 200 remains progress only, including zero counts.
- [ ] Known technical failure takes precedence over available observations and no-observation classification.
- [ ] 503 represents no substantive observation and no established technical failure.
- [ ] Output order and multiplicity remain intact without fabricated records.
- [ ] Preliminary reasons 100–103 remain distinct from internal reason 109.
- [ ] Interest and reporting EOF limitations remain unrepaired.
- [ ] No complete empty report, durable state, reset, isolation, retry, or completion claim is invented.
- [ ] Every state requirement has documentary treatment; missing concrete mechanisms remain visible.
- [ ] Every contract clause maps to behavior responsibilities, exclusions, or bounded gaps.
- [ ] Exact input/output versions and external review records are retained.
- [ ] Human review of this exact Stage 7 artifact is recorded externally.

**Stage 7 remains an unapproved documentary draft. No gate is approved, no implementation is authorized, and no further-stage material is created.**
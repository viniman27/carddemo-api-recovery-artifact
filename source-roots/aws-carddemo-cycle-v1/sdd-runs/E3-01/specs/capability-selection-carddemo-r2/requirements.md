# Capability Selection Specification

## Purpose

This revised Stage 2 specification proposes a **portfolio of three distinct candidate capabilities** for run `E3-01`:

1. Transaction posting.
2. Interest transaction generation.
3. Transaction reporting.

**All three areas are mandatory study coverage.** None is an optional alternative, a reserve candidate, or deferred scope. Their grouping remains low-commitment and subject to human ratification; this document does not establish recovered business semantics or a single combined business capability.

The explicit human coverage amendment rejects reduction to posting alone and takes precedence over single-focus template guidance for this local revision.

| Attribute | Value |
|---|---|
| Run ID | `E3-01` |
| Pipeline stage | `2` |
| Feature | `capability-selection-carddemo-r2` |
| Artifact type | `capability-selection` |
| Artifact path relative to `RUN_ROOT` | `specs/capability-selection-carddemo-r2/requirements.md` |
| Immutable operational chain identity (`capability`) | `unselected-stage-1-scope-only` |
| Proposed business selection | Three-candidate portfolio described below |
| Persisted `selected_business_capability` | Supplied as `null`; not modified by this response |
| Status | Revised draft for external human review |
| Stage 2 human approval | `false` |
| Stage 2 completeness gate passed | `false` |
| Ready for implementation | `false` |

This is an explicit local adaptation of `/sdd:spec-requirements --stage 2`, not a native slash command. It produces specification text only; it does not persist files, modify metadata, approve Stage 2, or authorize Stage 3.

## Selection Integrity Discipline

- Mandatory study coverage is distinct from the eventual business decomposition. Boundary refinement must not silently remove any of the three areas.
- Candidate business labels and track identifiers do not replace the immutable upstream operational chain identity.
- Programs and jobs are preliminary survey entry points, not definitions of business capability boundaries.
- Source references here justify candidate identification and future investigation only. They are not Stage 3 evidence items or semantic conclusions.
- No runtime sequence, dependency relationship, shared business meaning, or execution feasibility is inferred from the prescribed coverage.
- Independent future evidence tracks mean separate traceability and review responsibility, not independent experiments, isolated runtimes, or statistically independent observations.
- No legacy semantics, canonical data boundary, API contract, adapter behavior, downstream interface materials, or validation claims are produced.
- The corpus remains immutable. No tools, compilation, execution, external retrieval, retries, or fallback actions are performed.

## Section 1: Upstream Authority and Scope Reference

### 1.1 Upstream Authority

This specification derives from the approved Stage 1 Pipeline Scope Spec for `pipeline-scope-carddemo`, together with the explicit human scope amendment supplied for this revision.

| Authority | Path relative to `RUN_ROOT` | Supplied SHA-256 |
|---|---|---|
| Stage 1 metadata | `specs/pipeline-scope-carddemo/spec.json` | `c71fe711834fec66fb417335a2f60cde5b9f3b5b63968849c71ecc513b465978` |
| Stage 1 artifact | `specs/pipeline-scope-carddemo/requirements.md` | `1362fab5d55b77ef6121328606ae974295cd5723849520e9a246f4bd45e64cc9` |
| Stage 1 authorization | `reviews/stage-1-authorization.json` | `0ec9d89962c088507775523f266816b5c3c13f7631c7a6409b45bc13352542da` |

The supplied Stage 1 metadata records approval by Researcher on `2026-09-11` and a passed completeness gate. The supplied gate-check result is `current`, with `ok: true` and `human_approval_granted: false`. This reports freshness of the existing upstream decision; it grants no new approval.

The Stage 1 artifact retains its original draft-era gate wording. The supplied reviewed metadata establishes its subsequent approval status without rewriting that historical text.

The local human amendment requires complete coverage of posting, interest transaction generation, and transaction reporting. It authorizes this revision’s coverage direction, **not approval of the resulting Stage 2 artifact**. No separate amendment artifact path or digest was supplied; the exact request must be retained with revision provenance.

### 1.2 Inherited Constraints and Visibility

The approved roots remain unchanged:

- `RUN_ROOT`: run-specific artifacts and review records.
- `FRAMEWORK_ROOT`: supplied generic framework, rules, and template.
- `CORPUS_ROOT`: immutable research corpus.

Stage 1’s metadata-only permissions are not treated as automatic source-body authorization. This Stage 2 request explicitly supplies the 19 allowlisted bodies and their pins for bounded selection work.

The source package is identified by:

- Path: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-preparation/evidence/research-package.json`
- Supplied SHA-256: `63ba5c47ecb21349549744b912af3b150654e7e435724dba499e3c88369f15a2`

The supplied body path/hash labels agree with the corresponding allowlist and upstream inventory entries. No byte-level checksum computation or filesystem check was performed; this document relies on the supplied package-check context and does not independently certify integrity.

Only the approved upstream material, supplied framework bodies, human amendment, and allowlisted source bodies inform this draft. Historical examples embedded in framework instructions are not application findings. Referenced but unsupplied files, preparation reports, prior generated answers, evaluation material, fixtures, and downstream specifications remain excluded.

## Section 2: Capability Identification

### 2.1 Proposed Candidate Portfolio

The portfolio is an administrative grouping for complete study coverage, not an asserted unified business capability.

| Candidate track | Candidate business label | Preliminary characterization | Mandatory coverage mapping |
|---|---|---|---|
| `E3-01/selection/posting` | Transaction posting | Candidate area concerned with posting daily transactions; exact responsibility boundaries remain open. | Transaction posting — `CBTRN02C` / `POSTTRAN` |
| `E3-01/selection/interest` | Interest transaction generation | Candidate area concerned with interest-related transaction generation; calculation and generation meanings remain open. | Interest transaction generation — `CBACT04C` / `INTCALC` |
| `E3-01/selection/reporting` | Transaction reporting | Candidate area concerned with transaction reporting; report obligations and responsibility boundaries remain open. | Transaction reporting — `CBTRN03C` / `TRANREPT` |

These track identifiers are local selection and traceability labels. They neither instantiate additional pipeline runs nor change `spec_json.capability`.

### 2.2 Constituent Operations at Hypothesis Level

| Candidate | Proposed operation family for later investigation | Commitment limit |
|---|---|---|
| Transaction posting | Posting daily transaction records | No acceptance conditions, effects, outcomes, or guarantees selected |
| Interest transaction generation | Interest calculation and associated transaction generation | No formula, eligibility, timing, or generated-record meaning selected |
| Transaction reporting | Producing transaction reports | No report contents, selection rules, ordering, totals, or presentation obligations selected |

These are investigation headings, not recovered operation definitions. No named paragraph is promoted into a separate business capability merely because it exists in a program.

### 2.3 Preliminary Operational Boundary

The human amendment establishes the mandatory mappings. The supplied source headers provide limited corroboration of the candidate labels:

| Candidate | Preliminary source reference | Selection-level use |
|---|---|---|
| Transaction posting | `app/cbl/CBTRN02C.cbl:1-6`, especially the `Function` header | Header describes posting records from a daily transaction file |
| Interest transaction generation | `app/cbl/CBACT04C.cbl:1-6`, especially the `Function` header | Header describes an interest calculator; the generation scope is explicitly prescribed by the amendment |
| Transaction reporting | `app/cbl/CBTRN03C.cbl:1-6`, especially the `Function` header | Header describes a transaction detail report |

These references describe source labels, not verified behavior. They are not an evidence register.

**Inside the proposed study boundary:**

- All three candidate areas.
- Their allowlisted program, copybook, and operational-document context, where relevant to later authorized investigation.
- Boundary questions that may show a candidate spans more than its initial program/job pair.
- Explicit recording of overlaps and unresolved relationships without merging meanings.

**Outside this selection:**

- Business areas beyond the approved three-area scope.
- Whole-application decomposition or recovery.
- New capabilities inferred solely from utility, backup, combination, or procedure names.
- An assumed end-to-end batch sequence connecting the candidates.
- Behavioral rules, resource definitions, execution arrangements, and interface decisions.

### 2.4 Local Portfolio Exception to Single-Focus Guidance

**`D-1` — Proposed local Stage 2 portfolio organization; awaiting ratification.**

The generic template permits a justified deviation from single-focus selection. The explicit human amendment requires all three areas and rejects posting-only reduction.

Accordingly:

1. This Stage 2 artifact retains one combined selection record.
2. It proposes three distinct candidate tracks.
3. Each track remains mandatory and independently traceable.
4. No single business capability is invented to fit the template.
5. The generic framework is not modified.
6. Any later boundary refinement must retain an explicit mapping for every mandatory area and receive appropriate human review.

This is a human-directed revision, not an independent replica or automatic retry. No prior generated response was supplied or used.

## Section 3: Selection Rationale

### 3.1 Selection Criteria

| Criterion | Portfolio rationale | Limitation |
|---|---|---|
| Scope fidelity | The portfolio preserves every area in the approved scope and explicit amendment. | Coverage inclusion does not establish behavioral completeness. |
| Business significance | Each area has an explicit business-facing study label. | Distinct labels do not prove final business cohesion or separation. |
| Input accessibility | Each area has a supplied program body and corresponding operational-document body. | Availability does not establish complete dependencies or executability. |
| Boundedness | Three named candidates permit focused investigation without whole-application recovery. | Each candidate’s eventual boundary may span additional authorized artifacts. |
| Traceability | Separate tracks prevent one area’s progress from substituting for another’s. | Shared material requires explicit attribution, not automatic shared conclusions. |
| Pipeline study value | The portfolio allows the ordered method to address all prescribed topics without premature consolidation. | No experimental result, superiority, or transferability is claimed. |

### 3.2 Alternatives Not Adopted

| Alternative | Reason not adopted |
|---|---|
| Select posting alone | Directly contradicts the human amendment. |
| Select one area now and treat the other two as optional later work | Narrows mandatory study coverage. |
| Declare one unified business capability | Business cohesion has not been established. |
| Treat every program or job as a capability | Confuses artifact identity with business responsibility. |
| Start three independent experimental replicas | Neither requested nor established by this revision. |

No candidate is ranked as more important or easier to execute. A future work schedule must not be represented as scope exclusion or evidence of runtime ordering.

### 3.3 Proof-of-Concept vs. Institutional Context

This selection applies only to the public AWS CardDemo study in `E3-01`. It does not establish institutional priorities, applicability, environment availability, or a reusable business decomposition.

Institutional selection would require its own scope, permissions, candidate rationale, and human review. The three-area portfolio is justified by this study’s explicit coverage decision, not by a general claim that portfolios are always preferable.

## Section 4: Future Evidence Scope

### 4.1 Primary Source Entry Points

All paths below are relative to `CORPUS_ROOT`.

| Track | Primary program and supplied SHA-256 | Corresponding operational document and supplied SHA-256 |
|---|---|---|
| Posting | `app/cbl/CBTRN02C.cbl` — `708f3cadc555acab63f11e2f3238f5372ac7180e6b01197bf960d96bf0d2e83f` | `app/jcl/POSTTRAN.jcl` — `ecff62c691e6ce101de08690e72ec065bc98bd845744ddf914899097d37c9191` |
| Interest | `app/cbl/CBACT04C.cbl` — `5084bb8b0c9a0f0199f737487ae1863f12e43cabbdc459a62b6b67bedc683cc4` | `app/jcl/INTCALC.jcl` — `61afa664a807558e58213641d9f3317ab3b354a350c4c1536a630897d194d275` |
| Reporting | `app/cbl/CBTRN03C.cbl` — `8691e625502b7efcfd7ba4ae61797132e7b68f3fd5fedcdcc7dd6488f6871eef` | `app/jcl/TRANREPT.jcl` — `7d8fc0777e6b9fb1c62aee6b4b10a67d127057c84b92203c7152f230b3db9571` |

The remaining allowlisted material is retained as a **relevance-assessment pool**, not an asserted dependency graph:

- `app/cpy/CVACT01Y.cpy`
- `app/cpy/CVACT03Y.cpy`
- `app/cpy/CVTRA01Y.cpy`
- `app/cpy/CVTRA02Y.cpy`
- `app/cpy/CVTRA03Y.cpy`
- `app/cpy/CVTRA04Y.cpy`
- `app/cpy/CVTRA05Y.cpy`
- `app/cpy/CVTRA06Y.cpy`
- `app/cpy/CVTRA07Y.cpy`
- `app/jcl/COMBTRAN.jcl`
- `app/jcl/TRANBKP.jcl`
- `app/proc/REPROC.prc`
- `LICENSE`

Their exact versions remain those in the supplied `input_pins.source_bodies` register. Retaining a file in this pool neither makes it relevant to every track nor authorizes access to materials it references.

### 4.2 Independent Future Evidence Tracks

| Track | Future Stage 3 collection target | Required separation |
|---|---|---|
| Posting | Determine the source-supported extent of the posting candidate and relevant supporting context. | Posting observations and unresolved questions must be identifiable without relying on conclusions from the other tracks. |
| Interest | Determine the source-supported extent of interest transaction generation and relevant supporting context. | Interest investigation must not inherit posting meanings merely because labels or artifacts overlap. |
| Reporting | Determine the source-supported extent of transaction reporting and relevant supporting context. | Reporting investigation must not presume what the other candidates produce or how they relate operationally. |

For each track, a future authorized Stage 3 effort would need to distinguish source observations, comments, uncertainty, and any separately authorized execution observations. Questions about accesses, effects, ordering, termination, persistence, and failure remain investigation targets—not findings here.

Shared files must retain full paths and version pins. Any shared citation must name the consuming track; shared business meaning requires later explicit reconciliation. One track’s reviewed progress cannot close another track’s unanswered questions.

The exact Stage 3 artifact layout and identifier namespace must be recorded before evidence drafting. This specification creates no Stage 3 artifacts or `E-n` items.

### 4.3 Complexity and Readiness Limits

The supplied context includes multiple source programs, copybooks, jobs, and a procedure. Their presence motivates careful boundary investigation but does not establish coupling, execution order, or dependency closure.

Future work must not assume:

- A program/job pair exhausts a candidate’s boundary.
- Common names imply common resource identity or meaning.
- All referenced materials are present or authorized.
- The three candidates form an executable chain.
- Source-body availability establishes runtime feasibility.

Any necessary expansion beyond the supplied allowlist requires separate stage-specific authorization.

## Ambiguity Register

Upstream identifiers are retained. Candidate grouping is proposed here, but unresolved questions are not silently closed.

| ID | Description | Basis | Impact and handling | Blocking status |
|---|---|---|---|---|
| `A-1` | Final candidate cohesion and artifact-to-capability boundaries remain unsettled. | Upstream ambiguity; three-area amendment | Ratify the portfolio as provisional; investigate actual boundaries later without dropping coverage. | Blocks final boundary claims, not this draft |
| `A-2` | Inventory completeness and dependency closure are unknown. | Upstream ambiguity | Do not treat the allowlist as the entire application. | Blocks unsupported completeness or execution claims |
| `A-3` | Original corpus encoding is not supplied. | Upstream ambiguity | Preserve bytes and obtain authorized handling information when required. | Conditional blocker for byte-sensitive work |
| `A-4` | Runtime, state, sequence, persistence, and failure properties remain undetermined here. | Upstream ambiguity and Stage 2 boundary | Carry forward without architectural or semantic inference. | Blocks claims about those properties |
| `A-5` | Broader participant exposure is not documented. | Upstream ambiguity | Preserve supplied exposure statements; obtain protocol-required disclosure. | Conditional blocker for clean-context claims |
| `A-6` | Licensing review requirements remain unresolved. | Upstream question; `LICENSE` body now supplied | Body visibility is available, but no legal clearance is asserted. | Conditional on later activity |
| `A-7` | Future evidence artifact layout and track namespaces are not yet ratified. | Local portfolio exception | Record separate traceability ownership under the unchanged chain identity before Stage 3 drafting. | Blocking for Stage 3 entry |
| `A-8` | Relationships among the three candidates are not established. | Mandatory coverage does not establish relationships | Keep overlap and relationship questions explicit; do not infer a runtime chain. | Blocks relationship claims, not portfolio inclusion |

## Review Gaps and Revision Provenance

The original Stage 1 `G-1` approval gap is addressed for entry purposes by the supplied approved metadata and current gate-check report. Stage 1 `G-2` and `G-3` remain historical records; this revision relies on the supplied version pins and explicit Stage 2 body context rather than rewriting them.

| ID | Classification | Current gap | Required action |
|---|---|---|---|
| `G-4` | Blocking for Stage 3 entry | Revised Stage 2 artifact has no recorded human ratification. | Review the exact persisted artifact and record the decision separately. |
| `G-5` | Blocking for review finalization | This response has no persisted output digest or separately pinned amendment record. | Retain the exact request and response, preserve prior revisions, and bind review to concrete versions. |
| `G-6` | Blocking for Stage 3 entry | Portfolio track organization and Stage 3-specific permissions are not recorded. | Resolve `A-7` and record authorized inputs and activities for all three tracks. |

AI assistance is limited to candidate organization, source-label surveying, rationale drafting, and uncertainty registration. No tools or external materials were used. Model configuration, token usage, monetary cost, and transport settings such as `store=false` are not certified by this document. Unavailable telemetry is not reported as zero.

## Completeness Gate and Stage 3 Entry Condition

The following conditions are proposed for external human review and remain unchecked:

- [ ] All three mandatory study areas are retained without optional or deferred status.
- [ ] Candidate labels are characterized as provisional rather than recovered semantics.
- [ ] The local portfolio exception is explicitly accepted without modifying the generic framework.
- [ ] The immutable operational chain identity is preserved separately from business labels.
- [ ] Each mandatory area maps to a distinct future evidence track and primary source entry points.
- [ ] Preliminary boundaries and selection rationale are reviewed.
- [ ] Input visibility, exact version pins, and integrity-check limitations are accepted.
- [ ] Shared-source attribution and future track namespaces are recorded.
- [ ] Ambiguities and blocking gaps are resolved or explicitly handled by authorized review.
- [ ] The exact revised artifact and human amendment are retained and pinned.
- [ ] A human reviewer records the Stage 2 decision, authorization reference, upstream versions, and remaining gaps in the prescribed metadata.

**Current Stage 2 status: not approved; completeness gate not passed.**

Stage 3 may begin only after explicit human approval of the concrete revised Stage 2 artifact, recorded track organization, and appropriate Stage 3 input authorization. This specification grants none of those approvals.
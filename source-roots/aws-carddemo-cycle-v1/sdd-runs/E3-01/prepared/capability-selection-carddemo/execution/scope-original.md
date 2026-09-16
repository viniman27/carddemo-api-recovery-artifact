# Capability Selection Specification

## Purpose

This Stage 2 specification proposes **daily transaction posting** as the low-commitment business capability candidate for run `E3-01` of the AWS CardDemo public cycle.

It establishes a candidate focus, preliminary boundaries, selection rationale, and a bounded scope for later evidence collection. It does **not** ratify the selection, establish legacy behavior or semantics, or authorize Stage 3.

| Attribute | Value |
|---|---|
| Run ID | `E3-01` |
| Pipeline stage | `2` |
| Feature | `capability-selection-carddemo` |
| Artifact type | `capability-selection` |
| Artifact path relative to `RUN_ROOT` | `specs/capability-selection-carddemo/requirements.md` |
| Immutable operational chain identity (`capability`) | `unselected-stage-1-scope-only` |
| Proposed business capability label | Daily transaction posting |
| Recorded `selected_business_capability` | `null`; metadata is not modified by this draft |
| Selection commitment | Low-commitment candidate proposal, pending human ratification |
| Human gate approval | `false` |
| Completeness gate passed | `false` |
| Ready for implementation | `false` |

The operational chain identity is inherited unchanged from Stage 1. The proposed business label neither replaces that identity nor renames the supplied artifact directory.

This document is the Markdown response to an explicit local adaptation of `/sdd:spec-requirements --stage 2`, not execution of a native slash command. No artifact persistence or metadata update is claimed.

## Selection Integrity Discipline

- Business significance motivates selection; a file, program, paragraph, or job is not automatically a capability.
- All candidate characterizations and groupings remain preliminary hypotheses.
- Source references below support selection orientation only. They are not a Stage 3 evidence register.
- No processing rules, calculations, rejection criteria, state effects, ordering guarantees, or failure semantics are established here.
- No canonical data boundary, API contract, adapter behavior, downstream interface material, implementation, or validation claim is produced.
- The corpus remains immutable. No tools, external retrieval, compilation, or execution are used.
- Human ratification remains external. Draft completeness and the supplied upstream freshness result cannot grant approval.

## Section 1: Upstream Authority and Scope Reference

### 1.1 Upstream Authority

This specification derives from the approved **Pipeline Scope Specification**, specifically its supplied study area, visibility discipline, exclusions, and staged review requirements.

| Upstream record | Supplied SHA-256 |
|---|---|
| `specs/pipeline-scope-carddemo/spec.json` | `c71fe711834fec66fb417335a2f60cde5b9f3b5b63968849c71ecc513b465978` |
| `specs/pipeline-scope-carddemo/requirements.md` | `1362fab5d55b77ef6121328606ae974295cd5723849520e9a246f4bd45e64cc9` |
| `reviews/stage-1-authorization.json` | `0ec9d89962c088507775523f266816b5c3c13f7631c7a6409b45bc13352542da` |

The supplied Stage 1 metadata records requirements approval and a passed completeness gate, with a review dated `2026-09-11`. The supplied gate check reports `current`, `ok: true`, and `human_approval_granted: false`.

The historical draft-status statements inside the upstream Markdown are preserved as part of that artifact. Its subsequent approval is established by the supplied review metadata, not by rewriting the upstream text. Neither that approval nor its freshness check approves this Stage 2 draft.

### 1.2 Inherited Constraints and Current Visibility

The approved study area remains **posting, interest transaction generation, and transaction reporting**. Stage 2 narrows the proposed focus within that area; it does not expand the study.

The current request explicitly supplies the 19 allowlisted corpus bodies for selection-level inspection. This is a separate Stage 2 visibility expansion, not a retroactive extension of Stage 1’s metadata-only permissions.

The research-package reference is:

- Path: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-preparation/evidence/research-package.json`
- Supplied SHA-256: `63ba5c47ecb21349549744b912af3b150654e7e435724dba499e3c88369f15a2`

Body-entry paths and declared hashes correspond to the supplied input pins and upstream inventory. These are supplied provenance records: no independent byte hashing or inspection of the research-package file was performed.

The nine supplied framework bodies govern drafting, including the Stage 2 template pinned at `613ff8636e7dfdac9968f2c7384a3ee814aa4fdd84058fe220fdeafc2219d919`. Historical examples embedded in those instructions are not application findings.

All three workspace roots remain as supplied upstream. Unlisted files, preparation reports, prior answers or APIs, support implementations, evaluation materials, and expected outcomes remain excluded. A reference found inside an allowed body does not authorize opening its target.

## Section 2: Capability Identification

### 2.1 Selected Capability — Proposed, Not Ratified

**Proposed label: Daily transaction posting.**

The candidate business focus is the handling of daily transactions for posting within CardDemo. This wording identifies a topic of business significance rather than a recovered behavioral contract. The program header at `app/cbl/CBTRN02C.cbl:1–6` describes posting records from a daily transaction file, providing a preliminary orientation consistent with the upstream “posting” area.

The proposal does not assert what qualifies for posting, what posting changes, or whether the eventual capability boundary corresponds to a complete program or job.

### 2.2 Constituent Operations — Hypotheses Only

| Candidate constituent | Selection-level treatment |
|---|---|
| Daily transaction intake | A topic to investigate within posting, not a defined input contract |
| Posting eligibility and disposition | A candidate concern; no acceptance or rejection rules adopted |
| Posting processing | The central business focus; effects and completion conditions remain undetermined |
| Posting-related outcome recording | A candidate concern; no outcome taxonomy or persistence guarantee defined |

These are investigation headings, not established operations or commitments to expose separate functions.

### 2.3 Operational Boundary

| Boundary area | Proposed treatment | Preliminary orientation |
|---|---|---|
| Daily transaction posting | Primary candidate focus | `app/cbl/CBTRN02C.cbl:1–6`; `app/jcl/POSTTRAN.jcl`, descriptive block and `STEP15` |
| Posting-associated declarations | Include as candidate context, without interpreting layouts | `COPY` references in `app/cbl/CBTRN02C.cbl` |
| Interest transaction generation | Adjacent candidate, not selected | `app/cbl/CBACT04C.cbl:1–6`; `app/jcl/INTCALC.jcl` |
| Transaction reporting | Adjacent candidate, not selected | `app/cbl/CBTRN03C.cbl:1–6`; `app/jcl/TRANREPT.jcl` |
| Combination, backup, and procedure context | Retain as boundary questions, not constituent capabilities by default | `app/jcl/COMBTRAN.jcl`, `app/jcl/TRANBKP.jcl`, `app/proc/REPROC.prc` |
| Other CardDemo business areas | Excluded absent scope revision | Upstream scope |

These references are preliminary locators, not mechanically checked evidence anchors. No batch sequence or dependency closure is inferred from this table.

Excluding adjacent areas from the selected business focus does not establish operational independence from them. Any necessary boundary revision must be explicit and reviewed.

### 2.4 Single-Focus Status

This draft proposes **one capability focus for one run**. Interest generation and reporting are alternatives retained for selection transparency, not additional selected capabilities or replicas.

The supplied program and job are starting points for investigation, not a declaration that capability identity equals artifact identity.

## Section 3: Selection Rationale

### 3.1 Selection Criteria

| Criterion | Selection judgment |
|---|---|
| Business significance | Posting directly corresponds to one of the approved business-area labels. |
| Evidential accessibility | A posting-labelled program, associated job text, and referenced copybooks are present in the supplied selection context. |
| Boundedness | One business focus avoids treating all three upstream areas as an undifferentiated capability. |
| Pipeline-exercising value | The candidate permits later investigation of whether a business boundary spans source and operational artifacts without deciding that question now. |
| Feasibility | A bounded documentary starting set is available. Runtime feasibility, effort, and dependency completeness remain unknown. |

**Proposal rationale:** posting offers an explicitly labelled starting point within approved scope while leaving the other two areas available as context or future alternatives. This is a pragmatic selection judgment, not an optimality ranking or a prediction of findings.

### 3.2 Alternatives and Constraints That Shaped Selection

| Alternative | Disposition and rationale |
|---|---|
| Interest transaction generation | Viable alternative within scope; deferred to keep the proposed run single-focused |
| Transaction reporting | Viable alternative within scope; deferred for the same reason |
| Combined posting–interest–reporting capability | Not proposed because a common study area alone does not justify treating all three as one capability |

No alternative is rejected as less valuable, less correct, or harder to execute. There is no supplied comparative measurement supporting such judgments.

The choice is constrained by the fixed allowlist, absence of runtime observations, prohibition on premature semantics, and requirement for human ratification.

### 3.3 Proof-of-Concept vs. Institutional Context

This is a public CardDemo selection. Convenient access to a small, explicitly supplied artifact set is a local study condition, not proof that the same selection strategy or boundary applies to institutional COBOL.

No institutional priority, representativeness, modernization benefit, or transferability is established.

## Section 4: Downstream Evidence Scope

### 4.1 Proposed Primary Sources

If Stage 2 is approved and Stage 3 inputs are separately authorized, the proposed first inspection set is:

| Priority | Corpus-relative paths | Purpose |
|---|---|---|
| Primary | `app/cbl/CBTRN02C.cbl` | Investigate the proposed posting focus |
| Primary operational context | `app/jcl/POSTTRAN.jcl` | Investigate the candidate operational boundary |
| Associated declarations | `app/cpy/CVTRA06Y.cpy`, `app/cpy/CVTRA05Y.cpy`, `app/cpy/CVACT03Y.cpy`, `app/cpy/CVACT01Y.cpy`, `app/cpy/CVTRA01Y.cpy` | Investigate declarations referenced by the candidate program |
| Conditional boundary context | Remaining allowlisted programs, copybooks, jobs, and procedure | Consult only where justified by a recorded boundary question and Stage 3 permission |

Each path retains its exact supplied `input_pins.source_bodies` hash. This proposal does not authorize unlisted dependencies or declare the first set complete.

### 4.2 Evidence Collection Target

Later authorized work should determine:

- Whether the proposed business grouping is defensible.
- Which artifacts are necessary to characterize the candidate.
- Where its operational scope begins and ends.
- Which unresolved questions prevent a stable characterization.

These are collection questions only. This artifact creates no `E-n`, `R-n`, `V-n`, or `DIV-n` items and supplies no answers belonging to later stages.

### 4.3 Complexity Factors and Entry Limits

Potential complexity includes multi-artifact scope and references to external resources or operational support. Their relevance, completeness, and implications remain unestablished.

Stage 3 must not treat “daily transaction posting” as a settled behavioral definition. Any discovery requiring a different capability grouping must prompt a recorded selection revision rather than silently expanding this proposal.

## Ambiguity Register

Existing run-scoped identifiers are retained.

| ID | Description / status | Basis | Impact | Blocking? |
|---|---|---|---|---|
| `A-1` | Candidate grouping remains open; this draft proposes posting without resolving the final boundary | Upstream ambiguity and current proposal | Human ratification or revision required | Yes, until selection review |
| `A-2` | Allowlist and dependency-closure completeness remain unknown | Restricted inventory | May require separately authorized expansion | Not by itself for low-commitment selection |
| `A-3` | Original corpus encoding remains unspecified | Supplied metadata | Later byte-sensitive handling must not assume encoding | Deferred |
| `A-4` | Runtime and operational properties remain undetermined here | Stage boundary | No feasibility or behavioral guarantees | Deferred |
| `A-5` | Participant exposure beyond supplied declarations is undocumented | Upstream exposure record | Limits independence claims | Protocol-dependent |
| `A-6` | License text is now supplied; legal applicability is not decided by this draft | Current visibility expansion | Any necessary legal review remains external | Not determined |
| `A-7` | Separation of posting from adjacent areas is provisional | Three approved candidate areas | May require explicit boundary revision | Human review required |

The historical Stage 1 gaps `G-1`–`G-3` are not renumbered or rewritten. The supplied later approval metadata and current body visibility address their entry concerns for this drafting context without creating a new approval record.

## Provenance and Readiness Gaps

AI assistance is limited to candidate structuring and rationale drafting using the supplied context. No tools or external materials were used. Requested/reported model identifiers, provider settings, tokens, cost, and human effort are unavailable in the run input; none is inferred. Transport settings such as `store=false` are not certified by this document.

| ID | Classification | Gap / required handling |
|---|---|---|
| `G-4` | Blocking for Stage 3 | No human ratification of this Stage 2 candidate is recorded |
| `G-5` | Blocking for gate finalization | Preserve the exact Stage 2 output and bind review to its version, upstream pins, and actual authorization |
| `G-6` | Blocking for Stage 3 input use | Record Stage 3-specific input permissions; Stage 2 visibility is not automatic carry-forward authorization |

## Completeness Gate and Stage 3 Entry Condition

- [ ] Proposed capability is named, characterized at low commitment, and single-focused.
- [ ] Operational chain identity remains unchanged and separate from the business label.
- [ ] Preliminary operational boundary and locators are reviewed.
- [ ] Selection rationale and alternative dispositions are accepted without unsupported comparative claims.
- [ ] Proposed evidence scope is bounded and does not contain premature findings.
- [ ] Inherited and new ambiguities retain stable identifiers and explicit handling.
- [ ] Input provenance and hash-check limitations are accepted or addressed.
- [ ] Exact output and upstream versions are preserved.
- [ ] An authorized human records the actual selection decision and remaining gaps.
- [ ] Stage 3 input authorization is recorded separately.

**Current status: draft only. Human approval remains `false`; the completeness gate is not passed.**

**Stage 3 entry condition:** explicit human approval of the concrete Stage 2 artifact, recorded against exact versions in the associated review metadata and `spec.json`, with blocking gaps addressed and Stage 3 visibility authorized. This response stops before Stage 3.
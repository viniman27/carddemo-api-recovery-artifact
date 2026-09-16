# Pipeline Scope Specification

## Purpose

This specification bounds Stage 1 of run `E3-01` for the AWS CardDemo public cycle. The supplied study area is **posting, interest transaction generation, and transaction reporting**. This area is a scope declaration, not a selected capability or a description of observed legacy behavior.

The present task is inventory-only: identify supplied inputs, visibility limits, workspace roots, exclusions, and conditions for subsequent human-reviewed stages. No source bodies, operational document bodies, controlled execution observations, or expected outcomes are available as legacy evidence.

| Attribute | Value |
|---|---|
| Run ID | `E3-01` |
| Pipeline stage | `1` |
| Feature | `pipeline-scope-carddemo` |
| Artifact type | `pipeline-scope` |
| Artifact path, relative to `RUN_ROOT` | `specs/pipeline-scope-carddemo/requirements.md` |
| Capability | `unselected-stage-1-scope-only` |
| Upstream specifications | None; Stage 1 records external inputs |
| Language | English |
| Draft status | Draft for external human review |
| Human gate approval | `false` |
| Completeness gate passed | `false` |
| Ready for implementation | `false` |

The command context is an explicit local adaptation of `/sdd:spec-requirements`, not a native slash command. This response supplies the specification text only; it does not establish a persisted artifact or modify run metadata.

## Scope Integrity Discipline

- This artifact bounds the run. Capability selection belongs to Stage 2; legacy evidence and semantic interpretation belong to Stages 3 and 4.
- Corpus visibility is limited to supplied relative paths, hashes, roles, physical line counts, allowed-stage metadata, reasons, and prior-exposure statements.
- File names, extensions, and line counts do not establish program responsibilities, dependencies, record layouts, processing sequence, or business behavior.
- Supplied framework instruction bodies govern drafting. Their embedded historical examples and observations are not evidence about this run.
- The corpus remains immutable. This scope authorizes no source modification, compilation, execution, implementation, test generation, or validation activity.
- Full upstream inventory and the stage-specific input allowlist remain distinct. The supplied visible-input list is not asserted to enumerate the complete CardDemo application or its dependency closure.
- Public proof-of-concept conditions do not establish institutional applicability, functional continuity, equivalence, or transferability.
- Drafting progress and mechanical checks cannot substitute for explicit human gate review.

## External Inputs and Stage 1 Entry Basis

The external inputs are the supplied `spec_json`, `input_manifest`, roots, study scope, negative constraints, and nine framework context entries. No reviewed upstream capability specification exists for this stage.

The supplied framework references below are relative to `FRAMEWORK_ROOT`. Their instruction bodies are visible in the request; hashes are supplied version identifiers, not independently verified checksums.

| Framework input | Supplied SHA-256 |
|---|---|
| `steering/pipeline.md` | `23095cf4ec23f614f0a6d310177c6b27c0054de9245f1d5eb78d1cc1df91b59b` |
| `steering/product.md` | `0ed23027b8f2add658a2d423de4ba30b8bee17a4dcdee0f51a25d6a46e0ce624` |
| `steering/tech.md` | `d6bd1e7ffccc294323905571a331b48668a8c4a49336f35bddcf2bf67694a259` |
| `steering/structure.md` | `0427f1b5d80158ac40f4b0053ebfc16a4c4712e942b2b22da655965a30604d87` |
| `steering/glossary.md` | `27071611c10ae33d66e0bf87d6cdc985eac044bb59c6181462ce9494d1d9c73b` |
| `settings/rules/run-integrity.md` | `a9a2c586fb580e8f72d57709a2d64c5144ba0d0f57679237f695fca955060f54` |
| `settings/rules/ai-assistance.md` | `d91eb3ac354b7c9018e192f14b99bf43e93652b2eadbd5968c403fd925705f53` |
| `settings/rules/traceability.md` | `ffce5e0140b4048ffb2f9fa0df48bd73ef894d5dcad607dc574b245a1dc3d400` |
| `settings/templates/pipeline/pipeline-scope-spec.md` | `d5be3caaf18104b4869db1ababa14f5a7cb01e371c8b1ac6b67ee9f3ef0d280c` |

Other framework files mentioned by these instructions are references only; their bodies were not supplied and have not been inspected.

## Section 1: Source Layer Identification

### 1.1 Legacy Source Programs

The supplied allowlist contains 19 corpus entries:

- Three `app/cbl/` entries with the supplied role `source`.
- Nine `app/cpy/` entries with the supplied role `source`.
- Five `app/jcl/` entries with the supplied role `operational doc`.
- One `app/proc/` entry with the supplied role `operational doc`.
- `LICENSE`, also assigned the supplied role `operational doc`.

The register below preserves these roles without deriving business responsibilities from file names. Physical line counts describe inventory size only; they are not source anchors or measures of behavioral coverage.

### 1.2 Reference Layer

No reference implementation, comparison layer, execution aid, or support implementation is included in the visible corpus allowlist. This means none is authorized as an input here; it does not establish that none exists elsewhere.

Framework descriptions of possible runtimes, wrappers, or historical tooling do not select a reference layer or execution architecture for `E3-01`.

### 1.3 Input Manifest and Visibility

#### Workspace roots

| Root | Supplied absolute location | Scope role |
|---|---|---|
| `RUN_ROOT` | `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01` | Run-specific specifications, metadata, prompts, outputs, and review records |
| `FRAMEWORK_ROOT` | `<REDACTED_LOCAL_PATH>/pipeline-sdd-v3/pipeline` | Reusable v3 instructions, templates, and tool references |
| `CORPUS_ROOT` | `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-preparation/research-corpus` | Immutable corpus identified by relative paths and supplied hashes |

These roots are recorded as supplied, not checked against the filesystem. No evaluation or support directory is authorized by this scope.

#### Visibility terms applying to every corpus row

- **Policy:** `stage-1-inventory-only-no-source-bodies`.
- **Allowed stages:** `[1]`, for metadata visibility only.
- **Reason:** “stage-1 inventory/hash visibility only; source bodies withheld until explicitly escalated.”
- **Prior exposure:** “name and hash from approved research-package inventory only,” as reported in the manifest.
- **Approval boundary:** The supplied input authorizes this Stage 1 metadata context; it does not grant body access or human approval of this specification.
- **Encoding:** Not supplied. No encoding is inferred and no source bytes are transformed.

#### Stage 1 corpus allowlist

All paths below are relative to `CORPUS_ROOT`.

| Path | Supplied SHA-256 | Supplied role | Physical lines | Allowed stages |
|---|---|---|---:|---|
| `LICENSE` | `09e8a9bcec8067104652c168685ab0931e7868f9c8284b66f5ae6edae5f1130b` | operational doc | 175 | `[1]`, metadata only |
| `app/cbl/CBACT04C.cbl` | `5084bb8b0c9a0f0199f737487ae1863f12e43cabbdc459a62b6b67bedc683cc4` | source | 652 | `[1]`, metadata only |
| `app/cbl/CBTRN02C.cbl` | `708f3cadc555acab63f11e2f3238f5372ac7180e6b01197bf960d96bf0d2e83f` | source | 731 | `[1]`, metadata only |
| `app/cbl/CBTRN03C.cbl` | `8691e625502b7efcfd7ba4ae61797132e7b68f3fd5fedcdcc7dd6488f6871eef` | source | 649 | `[1]`, metadata only |
| `app/cpy/CVACT01Y.cpy` | `81a08bad15af5664326a6f0af3650f570821c4857ffdec3a6a39f91f07dca728` | source | 20 | `[1]`, metadata only |
| `app/cpy/CVACT03Y.cpy` | `ffc6079e09b28739e154bf6c1e1c36d408209faa91f6cf7008078dc596a1c370` | source | 11 | `[1]`, metadata only |
| `app/cpy/CVTRA01Y.cpy` | `50637f13692c89b17a2fc60d249dc54e9eb3569d933afca3cdcf65b491a9d5ba` | source | 13 | `[1]`, metadata only |
| `app/cpy/CVTRA02Y.cpy` | `7828fae489c59944b4310e223028a8d3a525ccf4ead113c062bcaff04b52bf9c` | source | 13 | `[1]`, metadata only |
| `app/cpy/CVTRA03Y.cpy` | `fb15dbc4a6924cbddce0704932f9e61c067ac10004cd00839dff0ed7c7bb0667` | source | 10 | `[1]`, metadata only |
| `app/cpy/CVTRA04Y.cpy` | `89803bc13a06347e1f3d8a599a5383b87235b203dce9f18a486bc233186479f8` | source | 12 | `[1]`, metadata only |
| `app/cpy/CVTRA05Y.cpy` | `d7bde0e78ff608497087b9909c889ed39e347269f964bda767b92b547fbb5fec` | source | 21 | `[1]`, metadata only |
| `app/cpy/CVTRA06Y.cpy` | `c5c69f1b86c5a10156d3c5881d7cf387e6b925aae32825360f85bf4056a554a1` | source | 21 | `[1]`, metadata only |
| `app/cpy/CVTRA07Y.cpy` | `72ba597b1a40e1e6cf908e15da9e6a818a0ab899ef1d27d15edeb074963102fa` | source | 73 | `[1]`, metadata only |
| `app/jcl/COMBTRAN.jcl` | `ab60da6cfdc8c4ec66c8b950540553bf35e91dc1e61a1dd4ada5bb888011c85c` | operational doc | 52 | `[1]`, metadata only |
| `app/jcl/INTCALC.jcl` | `61afa664a807558e58213641d9f3317ab3b354a350c4c1536a630897d194d275` | operational doc | 44 | `[1]`, metadata only |
| `app/jcl/POSTTRAN.jcl` | `ecff62c691e6ce101de08690e72ec065bc98bd845744ddf914899097d37c9191` | operational doc | 45 | `[1]`, metadata only |
| `app/jcl/TRANBKP.jcl` | `457cd00d14a1d9ac9983d92212541df3456e8428862b97cf10bab7249b9e6183` | operational doc | 71 | `[1]`, metadata only |
| `app/jcl/TRANREPT.jcl` | `7d8fc0777e6b9fb1c62aee6b4b10a67d127057c84b92203c7152f230b3db9571` | operational doc | 84 | `[1]`, metadata only |
| `app/proc/REPROC.prc` | `4562039d1c7b90f05cc946dd1cd1cb93571bb279740c5c9777acfa3ea23fbc9f` | operational doc | 32 | `[1]`, metadata only |

The supplied hashes are inventory pins, not a claim that file integrity has been checked. No standalone manifest path or manifest digest was provided. The exact manifest and artifact versions must be preserved for external review.

#### Exclusions and escalation

The following are excluded from this Stage 1 extraction context:

- All corpus file bodies, including `LICENSE`, JCL, and procedure contents.
- Files not present in the supplied visible-input list.
- Prior answers, prior capability specifications and APIs, preparation reports, and historical case results.
- Reference implementations, generated support, synthetic fixtures, evaluation material, and expected outcomes.
- External repositories, external documentation, and assumptions drawn from domain conventions or model memory.

Any later expansion requires an explicit, stage-specific authorization recording the input, version, purpose, visibility, and exposure. Stage 1 approval alone would not extend `[1]` permissions to Stage 2 or authorize source-body inspection.

## Section 2: Capability Boundary

### 2.1 Candidate Operation Boundaries

Only the supplied study-area labels are recorded:

| Candidate area | Basis | Stage 1 boundary |
|---|---|---|
| Posting | Supplied study scope | Topic for later selection; no operation or effect asserted |
| Interest transaction generation | Supplied study scope | Topic for later selection; no calculation or generation rule asserted |
| Transaction reporting | Supplied study scope | Topic for later selection; no report content or behavior asserted |

These labels are not three selected capabilities, three pipeline replicas, or a prescribed processing sequence. No mapping from a label to a source file, copybook, job, or procedure is made. Whether the eventual capability spans multiple artifacts remains a Stage 2 question.

### 2.2 Out-of-Scope Capabilities and Activities

- Business areas outside the supplied target area are excluded absent explicit scope revision.
- Whole-application recovery, optimal service decomposition, source rewriting, and big-bang migration are excluded.
- Capability ranking, selection, and ratification are not performed in this artifact.
- Semantic rules, canonical data definitions, API design, adapter behavior, validation scenarios, and validation claims are excluded from this task.
- Runtime setup, dependency discovery through inspection or execution, compilation, and execution are not authorized.
- Alternative backend construction, comparative campaigns, coverage assessment, statistical analysis, and publication claims require separate scope and authorization.

These exclusions preserve the declared stage boundary rather than imply anything about functionality present or absent in CardDemo.

### 2.3 Proof-of-Concept vs. Institutional Scope

This run is a public AWS CardDemo study, not the institutional case or future Phase 2 application. The supplied local roots, restricted inventory, and framework context describe this public run only.

Institutional material may require different input permissions, dependency access, environments, and review arrangements. None is supplied here. No public-run constraint, tooling choice, or future result is presumed to transfer automatically to institutional code.

### 2.4 Architectural Constraints Known at Scope Time

The known constraints are procedural and evidentiary, not recovered architectural properties:

1. The corpus is read-only.
2. Run outputs and any separately authorized future support must remain outside the corpus.
3. No compiler, runtime, storage configuration, binding, process topology, port, or execution environment is established for this run.
4. No record schema, resource identity, persistence model, invocation sequence, end-of-input behavior, restart boundary, atomicity, or retry safety is known.
5. The presence of JCL and procedure paths does not establish job dependencies or an executable batch sequence.
6. Framework references to GnuCOBOL/gcov and other technologies are not evidence that this run has a configured or exercised toolchain.
7. Full corpus-relative paths must be retained; shared basenames cannot substitute for identity.
8. Changes to reviewed inputs or artifacts require renewed review of affected downstream authority.

## Section 3: Pipeline Stage Map

### 3.1 Specification Artifact Stages

The v3 order is retained without fast-tracking.

| Stage | Artifact | Boundary |
|---:|---|---|
| 1 | Pipeline Scope Spec | Inputs and run boundaries; current draft only |
| 2 | Capability Selection Spec | Selection and rationale under human review |
| 3 | Legacy Evidence Spec | Authorized source or controlled-execution observations |
| 4 | Capability Semantics Spec | Evidence-grounded meanings and obligations |
| 5 | Canonical Data Boundary Spec | Data and state meanings crossing the boundary |
| 6 | API Contract Spec | Surface derived from the reviewed canonical boundary |
| 7 | Adapter Behavior Spec | Realization over unchanged legacy |
| 8 | Semantic Validation Spec and separate Validation Report | Approved assessment plan, followed separately by observations |

Listing later stages is a roadmap, not authorization to draft or execute them. The validation plan must receive approval before its execution; a later report cannot retroactively authorize a plan.

### 3.2 Structural Separation Commitments

- Inventory metadata is not legacy behavioral evidence.
- Evidence precedes semantics; semantics precedes canonical boundaries and contracts.
- Contract and adapter specifications remain separate.
- Validation planning remains separate from execution and reporting.
- Framework instructions remain separate from application findings.
- Support and evaluation artifacts remain separate from extraction inputs unless explicitly authorized and disclosed.
- AI drafting, mechanical checks, and human approval remain separate records.
- No `E-n`, `R-n`, `V-n`, or `DIV-n` items are created here because this stage establishes no legacy observations, semantic rules, validation scenarios, or observed divergences.

## Section 4: Research Context

### 4.1 Research Objective

The public cycle provides a bounded context for studying the ordered, human-reviewed pipeline. Stage 1 contributes a record of what was visible, what was withheld, and what work was not yet authorized.

This artifact reports no experimental outcome. Authorization covers only `E3-01`, Stage 1; it does not establish three SDD replicas, repeated capability runs, or measured variance.

### 4.2 Legacy Artifact Constraints

Legacy bodies and operational instructions are withheld. Execution feasibility, dependency completeness, licensing terms, encoding, and environment requirements cannot be established from the visible metadata.

Later authorized work must identify relevant resources and operational dependencies from appropriate evidence. State, ordering, persistence, failure effects, and repetition safety must remain unknown until supported, rather than being filled from conventional accounting or batch-processing assumptions.

### 4.3 LLM Role and Provenance

AI assistance is limited here to structuring supplied metadata, drafting boundaries, and registering unresolved questions. It is not a semantic authority, validation oracle, capability selector, or human reviewer.

| Provenance item | Recorded status |
|---|---|
| Authorization scope | `E3-01`, Stage 1 only |
| Input context | Supplied request, manifest metadata, roots, `spec_json`, and framework instruction bodies |
| Supplied metadata creation/update time | `2026-09-11T13:46:39-03:00`; not treated as a measured response-generation time |
| Tools and external retrieval | None used |
| Source-body inspection or execution | None performed |
| Requested/reported model identifier | Not supplied in the run input |
| Provider configuration and usage | Not established by this document |
| Tokens and monetary cost | Unavailable; not zero |
| Human correction and review | Not supplied |
| Prior exposure | Manifest-reported exposure recorded in Section 1.3; broader participant history is not established |

Exact prompts, responses, attempts, input/output versions, actual provider settings, and human interventions should be preserved in run records. This response does not certify transport settings such as `store=false`, filesystem persistence, or a clean exposure history beyond the supplied record.

## Ambiguities and Readiness Gaps

Identifiers below are scoped to `E3-01` and must not be silently renumbered.

| ID | Open ambiguity | Required handling |
|---|---|---|
| `A-1` | Candidate grouping and artifact-to-capability relationships are unknown. | Leave unselected; address in Stage 2 with authorized inputs and human ratification. |
| `A-2` | Completeness of the visible inventory and dependency closure are unknown. | Do not equate the allowlist with the full corpus; explicitly authorize any expansion. |
| `A-3` | Corpus encodings are not supplied. | Record as unavailable now; obtain through authorized handling without changing bytes before relevant body analysis. |
| `A-4` | Runtime, state, sequencing, persistence, and failure properties are unknown. | Carry forward without architectural or semantic inference. |
| `A-5` | Participant exposure beyond the manifest statements is not documented. | Obtain protocol-required disclosure before treating a later context as clean or independent. |
| `A-6` | `LICENSE` terms are not visible. | Do not infer legal permissions from its path or hash; obtain authorized review when needed. |

| ID | Classification and affected transition | Gap | Required external action |
|---|---|---|---|
| `G-1` | Blocking for Stage 2 entry | No human Stage 1 review or authorization is recorded. | Review the concrete artifact and record the decision with exact version pins and authorization reference. |
| `G-2` | Blocking for review finalization | Persisted exact output version and manifest-level review pin are not supplied. | Preserve the exact artifact and input versions and bind review metadata to them. |
| `G-3` | Blocking for subsequent input use | The supplied corpus permissions cover Stage 1 metadata only. | Establish the next stage’s explicit allowlist and permitted visibility before using corpus inputs there. |

These are draft scope gap records, not claims that the supplied `spec_json.gate.blocking_gaps` has been edited. Deferred evidence questions do not require premature investigation to complete Stage 1; their boundaries and downstream handling require human review.

## Section 5: Artifact Chain and Scope Completion

### 5.1 Intended Artifact Chain

The fixed current artifact location is:

`RUN_ROOT/specs/pipeline-scope-carddemo/requirements.md`

Its associated metadata location is:

`RUN_ROOT/specs/pipeline-scope-carddemo/spec.json`

Later directory names remain conditional on the Stage 2-selected identifier:

| Stage | Intended directory relative to `RUN_ROOT` |
|---:|---|
| 2 | `specs/capability-selection-<selected-capability>/` |
| 3 | `specs/legacy-evidence-<selected-capability>/` |
| 4 | `specs/capability-semantics-<selected-capability>/` |
| 5 | `specs/canonical-data-boundary-<selected-capability>/` |
| 6 | `specs/api-contract-<selected-capability>/` |
| 7 | `specs/adapter-behavior-<selected-capability>/` |
| 8 | `specs/semantic-validation-<selected-capability>/`, with separate plan and report |

`<selected-capability>` is a placeholder, not a selection. Concrete downstream identities must be recorded when legitimately determined. No downstream artifacts are generated by this response.

### 5.2 Scope Completion Gate

The following are proposed checkable review conditions. They remain unchecked because this draft does not perform or approve the human gate.

- [ ] The source and operational-document inventory is reviewed with full relative paths, supplied hashes, roles, and line counts.
- [ ] Roots, metadata-only visibility, per-stage permissions, reasons, and reported prior exposure are recorded and accepted.
- [ ] The visible allowlist is distinguished from the full upstream inventory.
- [ ] Exact input and output versions are preserved for review; supplied hashes are not misrepresented as verified.
- [ ] Candidate scope is not presented as completed capability selection.
- [ ] In-scope and out-of-scope boundaries are explicit and justified.
- [ ] Known constraints and unresolved questions are registered for downstream inheritance.
- [ ] Public-study and institutional boundaries are explicit.
- [ ] The Stage 2 input authorization requirement is addressed without silently expanding source visibility.
- [ ] Blocking gaps are resolved or explicitly handled by authorized review without silently removing them.
- [ ] An external human reviewer records the decision, reviewer/authorization reference, exact artifact and input versions, and remaining gaps in the prescribed review metadata.

## Completeness Gate and Stage 2 Entry Condition

**Current gate status: not passed. Human approval remains `false` and external to this response.**

Stage 2 may begin only after explicit human review passes the Stage 1 gate and the decision is recorded against the exact reviewed versions in `spec.json` and associated review metadata. Its input context must also be explicitly authorized for Stage 2.

No reviewer identity, signature, authorization reference, approval date, approval decision, runtime result, or validation claim is generated here.
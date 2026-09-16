# Pipeline Stage Map

This file is the consolidated project memory of the modernization pipeline: its stages, gates, artifact conventions, and identifier scheme.

It codifies the pattern that emerged and stabilized during the account-balance proof-of-concept run, so that future runs (and the institutional case) do not need to rediscover it.

## The eight stages

| # | Stage | Artifact | Primary question |
|---|-------|----------|------------------|
| 1 | Pipeline Scope | Pipeline Scope Spec | What legacy material and what boundaries govern this run? |
| 2 | Capability Selection | Capability Selection Spec | Which capability, and why this one? |
| 3 | Legacy Evidence | Legacy Evidence Spec | What does the legacy material observably do? |
| 4 | Capability Semantics | Capability Semantics Spec | What does that behavior mean, as rules? |
| 5 | Canonical Data Boundary | Canonical Data Boundary Spec | What are the stable, technology-neutral data meanings? |
| 6 | API Contract | API Contract Spec | What modern surface exposes the capability? |
| 7 | Adapter Behavior | Adapter Behavior Spec | How does the surface connect to legacy-faithful behavior? |
| 8 | Semantic Validation | Semantic Validation Spec + Validation Report | Does modernized behavior adhere to legacy behavior, and where does it diverge? |

Stages are cumulative. Each stage's completeness gate is the entry condition of the next.

## Canonical artifact anatomy

Every pipeline artifact (stages 1–8) follows the same anatomy, in this order:

1. **Purpose** — what question this artifact answers and for which capability run
2. **Integrity Discipline** — the stage-specific rules the artifact commits to (evidence quality, semantic integrity, contract integrity, etc.)
3. **Section 1: Upstream Authority and Entry Condition** — which upstream specs it derives from, the inherited entry condition, and inherited constraints (omitted only in stage 1, which instead states its external inputs)
4. **Numbered body sections** — the stage-specific content
5. **Ambiguity handling** — new ambiguities registered, existing ambiguities disposed
6. **Completeness Gate and Next-Stage Entry Condition** — explicit, checkable conditions; the gate must be passed before the next stage may claim this artifact as authority

This anatomy is enforced by the templates in `settings/templates/pipeline/`.

## Completeness gates

A gate is a short list of explicitly checkable conditions written at the end of the artifact.

Gate rules:
- conditions must be verifiable by reading the artifact and its upstream chain, not by trusting intent
- a gate is passed only after human review (design review outcome: Approve)
- blocking gaps (per `gap-analysis.md`) fail the gate regardless of prose quality
- gate status is recorded in the spec's `spec.json` (`gate` block)

## Identifier scheme

All pipeline runs use the shared identifier conventions defined in `settings/rules/traceability.md`:

`E-n` evidence · `A-n` ambiguity · `R-n` semantic rule · `D-n` design decision · `G-n` gap · `V-n` validation scenario · `DIV-n` divergence

Identifiers are scoped per capability run and stable once assigned.

## Spec directory conventions

- one spec directory per stage per capability: `[artifact-type]-[capability]` (e.g., `legacy-evidence-account-balance`)
- the stage's authoritative artifact lives in a file named after the artifact type (e.g., `legacy-evidence-spec.md`); stage 8 additionally produces `validation-report.md`
- `requirements.md`, `design.md`, `tasks.md`, `research.md` support the SDD phases of producing that artifact and are interpreted stage-appropriately (document-first in stages 1–5)
- `spec.json` records framework phase plus pipeline metadata: `artifact_type`, `pipeline_stage`, `capability`, `upstream_specs`, and `gate` status

## Stage-boundary decisions memory

Lessons stabilized during the proof of concept that apply to all future runs:

- **Design decisions live where they are made.** When a downstream stage must decide something upstream evidence cannot determine (e.g., the account-identifier decision at stage 5), record it as a `D-n` decision in that stage, with rationale, downstream consequences, and institutional applicability notes.
- **Reference layer is never authority.** The Node.js layer may serve execution and comparison, but authority flows only through the specification chain.
- **Constraints inherit explicitly.** A constraint discovered upstream (e.g., absence of account identifier) must be restated in each downstream artifact's upstream-authority section for as long as it remains binding.
- **Institutional applicability notes are worth writing early.** Where the proof of concept diverges from expected institutional conditions, say so in place; these notes become the transfer argument of the research study.
- **Rule reconstruction is documentation, not reimplementation** (advisor alignment, June 2026). Stage 4 documents business rules to support the canonical boundary, contract derivation, and test design (including test data setup) — the legacy core remains the runtime enforcer of those rules through the wrapper. Reconstructed rules are never a mandate to rewrite them in the modern layer.
- **Wrapping is the default adaptation strategy.** Stage 7 wraps the unmodified legacy core (e.g., via runtime binding); reimplementing behavior in the modern layer is exceptional and requires an explicit `D-n` justification. The legacy source is read-only (`rules/legacy-code-policy.md`).
- **Claims stay at test level.** Gate statements and validation conclusions use test-based behavioral-confidence vocabulary, never verification or semantic-preservation vocabulary (`rules/validation-principles.md`).
- **The test suite is a transferable output — and transferability is verified, not assumed.** Stage 8 scenarios are phrased against the contract surface so the same suite can later exercise a reimplementation exposed through the same API. Phrasing is necessary but not sufficient: the suite must also avoid depending on capabilities the contract does not expose, and the only reliable way to find such a dependency is to run the suite against a backend of different provenance. Until that is done, transferability is a design intent (`rules/validation-principles.md`).
- **State scope is a boundary property, decided at stage 5.** Identity, initialization, lifetime, reset and isolation of the capability's state belong in the canonical data boundary, because stage 6 cannot expose what stage 5 did not license and stage 7's state model is defined as *realizing* the canonical state scope. Legacy systems usually supply state lifecycle implicitly — process restart, region recycle, job boundary — so the decision is easy to skip and invisible once skipped.

## Lessons carried from phase 1

Phase 1 executed the full pipeline over three public COBOL systems (account balance, payroll, BAMS). What follows is what the execution changed about the method itself, recorded here so a later run does not have to rediscover it. Run-specific content stays in the specs.

**The comparative hypothesis was not confirmed at small scale.** A pre-registered baseline — one generic prompt, no scaffolding — produced contracts scoring 14 of 15 rubric items against the pipeline's 15, or 14–14 discounting the one item biased toward a pipeline decision. For capabilities that fit in a single reading of the model (100–1100 lines), the framework does not measurably improve semantic fidelity of the contract. It was never tested in the regime where whole-source reading stops being possible, which is where structural decomposition would have to pay for itself. Claim auditability and traceability, which do not depend on the comparison; do not claim fidelity superiority.

**One thing did separate the two arms, outside the instrument.** The baseline fabricated a defect that does not exist — asserting a fill loop leaves a byte unwritten, then building three contract elements on top of it — and the claim was falsified by recompiling the unmodified subprogram. The pipeline fabricated nothing across three cases. With three runs per arm this is an indication, not a measurement, but it is the plane worth instrumenting next, and the anchoring requirement is the plausible mechanism.

**A stage-5 omission survived every gate.** The canonical boundary recorded the singleton state decision but not the state's lifecycle. Stage 6 could not expose a reset it had not been licensed to expose; stage 7 supplied one implicitly by restarting a COBOL process; stage 8 passed 8/8 because the thing it silently depended on was there. The gap surfaced only when the suite met a backend that did not restart processes. Two structural causes, both now addressed: stage 5's template had no slot for state scope, and stage 7's template already required its state model to "realize the canonical state scope" — a reference to a section stage 5 was never asked to produce.

**The generalizable form of that lesson:** a defect that only manifests under a change of provenance cannot be found by artifact review, however careful, because every artifact is coherent and mutually consistent while the accident holds. Gates catch errors of commission; they are weak against the omission of a category no completeness condition names. The cheap countermeasure is not a second implementation but a question at the stage-8 gate — *what does the suite need that the contract does not provide?*

**Anchoring can be mechanized; most gate conditions cannot yet.** Converting the `E-n` anchor requirement into a script moved one condition from asserted to measured (54/54 across three artifacts). The remaining conditions are still inspection-based, and inspection by the artifact's own author is the weakest link in the chain — it is what missed the stage-5 gap.

**Scenario types must be marked.** A derived suite mixes scenarios asserting what the contract promises with scenarios recording legacy behavior the modernization chose not to correct. The second kind fails by design against a corrected reimplementation. Unmarked, a legitimate correction reads as a regression.

**Same-provenance instruments prove self-consistency only.** Harness, contract and adapter written by one process yield "zero contract violations" as a schema regression result, not as evidence the contract describes the legacy.

**Cost is dominated by materialization, not by the intermediate layer.** Across three cases the documental reconstruction stages (3–5) took roughly 17% of output tokens; code and test materialization (7–8 plus operationalization) took roughly 50%. Marginal cost per capability fell to 37% and then 26% of the first run, though that figure mixes template maturation with executor learning and this design cannot separate them.

## Research instruments live outside the pipeline

Some procedures study the method rather than execute it, and they must not be mistaken for stages. They live in `casos/analise/` alongside the artifacts:

| Instrument | What it tests | Where |
|-----------|---------------|-------|
| Pre-registered baseline | Whether the framework improves contract fidelity over an unscaffolded direct jump | `baseline-rq2/` — `PROTOCOLO.md`, frozen `prompt.md`, 15-item `rubrica.md`, dated execution records |
| Transferability experiment | Whether a derived suite discriminates correctly against a second backend behind the same contract | `transferibilidade/` — report, `executar.sh`, reference reimplementations |
| Cost instrumentation | Token consumption per capability and per stage | `custo/` |
| Anchor verifier | That every `E-n` resolves to an existing file and line range | `ancoragem/verificar-ancoras.py` |
| Isolation experiments | Root cause of an observed anomaly, outside the legacy program | `div2/` |

The pipeline is the object of study; these are the instruments. Keeping them separate is what stops the method from validating itself with its own gates. The one exception worth noting: the transferability *procedure* revealed a defect class no artifact review can reach, and the cheap countermeasure was folded back into the stage-8 gate as a question ("what does the suite need that the contract does not provide?") rather than as a required second implementation.

Note also that the transferability script is currently hardcoded to the phase-1 cases (fixed ports and paths). It is reproducible for those cases and not yet a parameterized procedure; generalizing it is pending work, and the reusability claim should be scoped accordingly.

## Selection versus discovery

When cases are chosen for one set of reasons and turn out to contrast along another, say so explicitly and date the sequence.

Phase 1 selected three systems on structural and operational criteria — public availability, GnuCOBOL compilability, distinct domains, a self-contained capability — and only afterwards recognized that they also contrasted semantically: rule present, rule absent, property not guaranteed. That axis was **recognized a posteriori, not designed**, and the artifact record must not be arranged to suggest otherwise.

Why it matters in both directions:

- It **preserves** the value of a prediction that genuinely preceded observation. A non-guarantee written at stage 5 before any test ran, then confirmed at stage 8, is a dated falsifiable claim — but only if the ordering is documented and verifiable.
- It **limits** what a single case supports. A defect found where it was highly exposed does not establish that the method would find it where it was not; that claim would require deliberately varying the exposure, which phase 1 did not do.

## Multi-capability future

When a second capability enters the pipeline:
- stages 1 (scope) may be shared or revised per run — state which explicitly
- identifiers never cross capability runs
- cross-capability canonical types, if any, require an explicit reconciliation decision at stage 5

---
Document stage logic and gate discipline, not run-specific content — that belongs in the specs.

# Run integrity and observable state

## 1. Input boundary before extraction

At stage 1 record each input's relative path, SHA-256, role, allowed stages and reason: original source/dependency; original operational documentation; support; reference implementation; evaluation data/results. Only approved entries enter that stage's context. Record encoding without changing source bytes. The full upstream inventory and the selected input allowlist are different artifacts.

Support, synthetic fixtures, expected outcomes, prior specs/APIs and preparation reports are excluded from extraction by default. An approved exception is an exposure, not independent discovery. Record who already saw evaluation material, including an executor's conversation context; start a clean execution context when required by the protocol. A manifest does not erase prior exposure.

Scope documents identify known candidate boundaries; final capability selection belongs to stage 2. Do not claim that a candidate boundary was selected through the pipeline before that stage occurred.

## 2. State across stages

Stage 3 records anchored accesses/effects. Stage 4 explains their business meaning and dependencies. Stage 5 decides canonical state identity, initial authority, lifetime, reset and isolation. Stage 6 explicitly maps each requirement to the contract or declares it external/unsupported. Stage 7 specifies how it is supplied without changing business rules. Stage 8 names each scenario's setup and the means of observing it.

Use one row per logical resource; a single label 'stateful' is insufficient for multiple files or processes. For batch capabilities record sequence prerequisites, record ordering, end-of-input behavior, intermediate outputs and restart boundaries when relevant. An unknown property stays an ambiguity; N/A needs a reason.

## 3. Failures and repetition

Distinguish business rejection, validation rejection, unavailable dependency, process failure, timeout and partial persistence. State which effects may precede failure and how they are observed. Do not infer atomicity from a non-success response, or from a process being stopped.

State whether repetition is known safe, unsafe or unknown, and on which evidence. No automatic retry, rollback, compensation or idempotency key merely for API convenience. A deliberate contract divergence requires upstream decision/review and cannot be implemented silently in the wrapper.

## 4. Validation authority is question-specific

A reviewed contract is the reference for surface conformance. An observed legacy execution characterizes the legacy under its environment. Reviewed business obligations define the intended continuity question, grounded in evidence and explicit decisions. None is universally 'strongest'. When they conflict, register the conflict and scope the conclusion rather than picking an oracle to get a pass.

Record separately: tool origin, data seen, origin of expected outcomes, and what the check can establish. A third-party fuzzer consuming a generated OpenAPI may detect schema/HTTP failures but cannot independently establish whether that OpenAPI correctly describes COBOL. Different provenance alone does not establish a correct or independent oracle.

Conformance and characterization remain distinct. Report request acceptance, COBOL reachability, observed effects, oracle verdict and tool/infrastructure failures separately. Missing observations are inconclusive, not passing. Coverage of generated C arcs, COBOL-mapped lines, contract operations, model transitions and business obligations are distinct measures; declare denominator and mapping. Coverage never proves functional continuity.

## 5. Revision and review

Each gate review records exact artifact version/hash, upstream versions, reviewer, decision, unresolved gaps and actual authorization. A mechanical pass only removes a mechanical blocker. It neither sets human approval nor authorizes execution.

For new v3 runs use `tools/check_gate.py` (FRAMEWORK_ROOT-relative) to check the recorded review against current artifact bytes, authorization-reference bytes and pinned upstream spec.json files recursively. The metadata contract is documented in `tools/gates.md`. A `current` result is freshness of a recorded decision, never a new human approval. The checker is read-only: preserve its result in the run log rather than editing review history.

If an upstream version changes, suspend dependent approvals pending review; preserve prior drafts and the change reason. Freeze the validation plan before official execution. Later exploration may form a separately identified amended plan, never retroactively repair the original result.

Mechanical source-anchor checks use full relative paths and a frozen manifest. They check membership, integrity and line range, not truth or completeness. Execution anchors instead need run/log identity and environment; do not force them into a fabricated source-line anchor.

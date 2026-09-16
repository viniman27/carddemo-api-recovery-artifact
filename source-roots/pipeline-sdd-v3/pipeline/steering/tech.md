# Technical discipline

## Separate layers

The legacy supplies observed behavior; the reviewed specifications record meaning and decisions; the wrapper exposes the contract; research instruments evaluate claims. None substitutes for the others.

Parser-agnostic means extraction may proceed without a parser, not without evidence. Static analysis may strengthen dependency/anchor recovery but cannot decide business meaning by itself.

## Runtime and tools are per-run decisions

Do not assume console I/O, singleton state, one process, Node.js, a specific model, RESTler, fixed ports or `.sdd/`. Record the actual compiler/runtime, storage, bindings and unavailable dependencies. Successful compilation does not establish successful execution or mainframe fidelity.

OpenAPI remains the preferred contract format, derived at stage 6. Select a compatible fuzzer in the run protocol, recording version, budget, seed support, actual stateful behavior and limits. An external fuzzer is independent tooling, not an independent business oracle.

For the current local preparation, GnuCOBOL/gcov is the existing chain; no gcobol or emulation switch is implied by this revision. Instrumentation requirements belong to the run protocol, not assumed results in the framework.

## Immutable legacy, explicit support

Keep source and copybooks unchanged. Data loaders, reset, wrappers and runtime shims live outside the corpus. Support must not calculate missing business outcomes, compensate partial effects, invent rollback, or silently retry non-idempotent operations.

Preserve raw outputs and state evidence; any normalization is declared before comparison. A process restart is not proof that persistent files were reset. A response is not proof that the process exited normally or counters were flushed.

## Reproducibility

Resolve `FRAMEWORK_ROOT`, `RUN_ROOT` and `CORPUS_ROOT` at run setup. Record permitted inputs, source hashes, model requested/reported, configuration actually supported, raw outputs, timestamps, attempt identity and review changes. Unavailable tokens/cost remain unavailable, not zero. Tokens and human effort are separate measures.

No LLM, server or COBOL execution is triggered merely by copying this framework or running its mechanical anchor tests.

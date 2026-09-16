# COBOL Analysis Guidance

<!-- Custom steering template: instantiate in .sdd/steering/ when COBOL evidence work benefits from persistent language-specific analysis memory. -->

## Purpose

Persistent guidance for extracting evidence from COBOL source in this project. It supports stages 2–4 (selection, evidence, semantics) without replacing them.

## Structural reading order

When approaching an unfamiliar COBOL program, examine in this order:

1. **IDENTIFICATION / ENVIRONMENT DIVISION** — program identity, file assignments, external coupling
2. **DATA DIVISION** — the data model is the semantic backbone:
   - `WORKING-STORAGE` — state, flags, accumulators
   - `FILE SECTION` / record layouts — persistent structures
   - `LINKAGE SECTION` — the program's *de facto* interface (prime capability-boundary evidence)
   - copybooks — shared structures; map which programs include which
3. **PROCEDURE DIVISION** — control flow last, read against the data model:
   - paragraph/section inventory before line-by-line reading
   - `PERFORM` graphs reveal the real operation structure
   - `CALL` statements reveal inter-program protocols

## Evidence-extraction heuristics

- **PIC clauses are constraints.** Field pictures (`PIC 9(6)V99`, `PIC X(20)`) are evidence of ranges, precision, and format expectations — record them as `E-n` items; they feed canonical types in stage 5.
- **Condition names (88-levels) are business vocabulary.** They often name domain states more honestly than paragraph names.
- **`EVALUATE`/`IF` ladders near I/O are dispatch structures.** Distinguish operation dispatch from business rules.
- **Arithmetic with guards is rule material.** A `SUBTRACT ... IF ... NEGATIVE` pattern is rule evidence, not implementation noise.
- **MOVE chains reveal data lineage.** Track where a field's value originates before claiming its meaning.
- **Console I/O (`ACCEPT`/`DISPLAY`) marks the legacy interaction surface.** Document its coupling as a complexity factor; it will not survive modernization but its ordering constraints may carry semantics.

## Common interpretation traps

- assuming a paragraph is a capability (capability-first rule)
- reading `REDEFINES` as two fields instead of one reinterpreted region
- ignoring implicit state carried across paragraphs by WORKING-STORAGE
- treating GO TO-era control flow as if it were structured; map actual reachability
- importing "standard accounting" expectations the source does not evidence (domain-pattern bleed-through)

## Institutional-scale additions

For the institutional case, extend this file with:
- JCL and batch context reading order
- CICS/embedded-SQL surface identification
- copybook governance and versioning observations

---
Keep this file heuristic and stable; per-program findings belong in Legacy Evidence specs.

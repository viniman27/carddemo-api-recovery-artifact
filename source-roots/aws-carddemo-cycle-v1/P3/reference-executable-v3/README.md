# Reference executable v3 — AWS CardDemo P3

Status: `executable_draft_needs_review`.

This directory is an executable finite-abstraction MBT reference draft for `CBTRN02C/POSTTRAN`, `CBACT04C/INTCALC`, and `CBTRN03C/TRANREPT`. It is not an official fixture suite, not a T1-T4 campaign, not COBOL execution output, and not a proof of full source equivalence.

## What changed relative to FAIL-06

- `model.json` contains typed finite domains with explicit partitions, initial values, states, input-driven transitions, structured guard ASTs, and structured effects (`set`, `inc`, `emit`, `assert`).
- `executable_reference.py` provides stdlib-only `validate_model`, `eval_guard`, `apply_effect`, `step`, `traverse`, and `validate_source_pins`. It uses manual interpretation only; no Python `eval`.
- Traversal is bounded BFS with transition-id ordering and explicit `frontier`, `omittedCount`, and `unknown` reporting.
- `UnknownEOF` is an explicit domain value. Ordinary equality with status `00` or `10` is false; it is surfaced only through an unknown path and does not imply receiver retention.
- The three concrete review mutations are source-sensitive obligation tests, separated from generic validator mechanics. This is a targeted check, not an invented automatic proof of semantic fidelity.

## Reproduce

From any safe cwd, run:

```sh
python3 -m unittest discover -s '<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/reference-executable-v3/tests' -v
python3 '<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/reference-executable-v3/executable_reference.py' '<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/reference-executable-v3' --traverse CBTRN02C_POSTTRAN --traverse CBACT04C_INTCALC --traverse CBTRN03C_TRANREPT --max-depth 8 --max-paths 80
```

Observed results in this run:

- Unit tests: 11 tests OK.
- Validator/traversal: exit code `0`, errors `[]`, counts `{'capabilities': 3, 'obligations': 25, 'states': 25, 'transitions': 39}`, source anchors checked `94` with `[]` source-pin errors.

## Scope limits

Effects are observable attempts/control events, not durability, commit, rollback, or post-failure persistence claims. The abstraction models selected finite source obligations and loops; it does not reimplement COBOL arithmetic or a general SAT/equivalence checker.

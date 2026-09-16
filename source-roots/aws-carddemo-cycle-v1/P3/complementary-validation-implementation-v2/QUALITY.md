# Quality contract — complementary validation implementation v1

## User-valued outcome

Executable local semantic checkers and fixtures that prove representative posting, interest, and reporting business expectations can be checked from source-grounded observations, while leaving unimplemented obligations explicitly pending.

## Anti-goals

- No campaign execution.
- No external LLM/API calls.
- No edits to original COBOL, contracts, or frozen campaign artifacts.
- No fake pass for unimplemented obligations.
- No quarantine expected-output reads.

## Mechanical checks

- `../../P2a/.venv/bin/python -m unittest discover -s tests -v`
- CLI execution on success and known-wrong fixtures with `--verify-source`.
- JSON Schema validation for generated result files.

## Outcome checks

- Success fixture returns 8 pass + 17 pending.
- Known-wrong fixture returns 8 failed + 17 pending.
- Each result carries source anchors, boundary partitions, sourceExpected and observed fields.
- Missing bytes are not treated as empty bytes.

## Stop conditions

- Source hash mismatch.
- Any pending obligation reported as pass.
- Any known-wrong representative obligation reported as pass.
- Any external call or original artifact modification required.

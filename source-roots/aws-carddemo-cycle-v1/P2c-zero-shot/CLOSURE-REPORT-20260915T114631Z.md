# P2c zero-shot E1 closure report — 2026-09-15T11:46:31Z

## Outcome

Implemented and verified the remaining P2c zero-shot facade closure items for E1-1, E1-2 and E1-3 within `P2c-zero-shot/` only. No P2a/P2b/P3/SDD/corpus/contract files were edited.

## Verified criteria

- **3 contracts x 3 tracks over real localhost HTTP:** `posting`, `interest`, and `reporting` exercised for E1-1/E1-2/E1-3 using one serial server instance per selected contract and the exact contract path, without `/E1-n` public routing.
- **Full public wire body schema:** nominal HTTP responses validate against the original response schemas; public bodies do not include audit paths or wrapper metadata.
- **E1-1 `parameterLength` transport:** E1-1 interest `parameterLength` is transported through a P2c-local COBOL wrapper into the CBACT04C linkage. Runtime capture measured `S9(4) COMP` as two big-endian bytes; sample test transported value `7` as `0007` followed by the exact `INPUTCHECK` X(10) bytes.
- **Binding closure:** input binding tokens resolve only by exact local map; unknown output binding tokens are explicitly rejected before COBOL invocation. Output resources are mapped by exact per-contract/per-track DD token.
- **Sidecar policy:** interest `XREFFILE.1` remains an explicit local sidecar tied to the selected interest package, not an unrelated prefix/default.
- **Reset/attribution:** repeated identical requests create fresh request package directories with the same pinned resource hashes/bytes. Each request package records materialized files, request hash, contract id, fixture descriptor hash and local-only provenance.
- **Error shape:** malformed request path was checked over HTTP and validated against available contract failure schemas. The E1 contracts here do not define a 400 response; the facade returns schema-valid 500 failure bodies rather than inventing a 400 body.

## Verification commands

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2c-zero-shot"
../P2a/.venv/bin/python -m unittest discover -s tests -v
# Ran 13 tests in 6.594s — OK

RUN_DIR="runs/closure-20260915T114631Z"
../P2a/.venv/bin/python p2c_facade.py qa --output-root "$RUN_DIR"
# summary: implemented_routes=9, exercised_http=9, schema_validated=9, blocked=0
```

## Evidence and hashes

- `p2c_facade.py` — sha256 `a1f6c52c6ab7bf578f1bc09bb67987b7c4a69963665ceac08c5c4a0f3f1dfc00`, 46011 bytes
- `tests/test_contract_facades.py` — sha256 `e54bfba3bb340c41a9c091308542907cabf8fe87b2c3843d777b0769cfa4dbe6`, 5642 bytes
- `tests/test_remaining_closure.py` — sha256 `d6b1f51bfdbb3cbff14d7ad866031f437b2bdad79719f0f44dafd03e165a9259`, 5408 bytes
- `runs/closure-20260915T114631Z/p2c-zero-shot-http-qa-report.json` — sha256 `1ff7d127c25a0a620e39cdfda43b8427c381cd97828f5182fb5c81446c7e5eb5`, 5535 bytes
- `support-generated/p2c_interest_driver.cbl` — sha256 `4cc534b904ce56e5242a59c7747650e9cf43875f380784216482b43c2e3f93d3`, 1568 bytes
- `build-local/P2B_INTEREST_DRIVER` — sha256 `e9bb2c049ac28ebc3465f47db450611f35a1bac51dc166d0012c6d8d52b53e05`, 52960 bytes
- `CLOSURE-REPORT-20260915T114631Z.md` — sha256 `b1d9bd307cb441ae28b838f3e4948c94403babf227520cc9e535b816361addfd`, 4071 bytes before adding this generated-file hash appendix

Original contract hashes observed in QA:

- E1-1 `collection-01/E1-1/response-original.txt` — `776b832ede1a7c5114b04cf335846c6e66b8fa2b23f040084dcffdacedd286a0`
- E1-2 `collection-01/E1-2/response-original.txt` — `33b071ffde1583bda61e96e4ae00ab0aa7299bbba571ea01e5fdf79c7f3b7014`
- E1-3 `collection-01/E1-3/response-original.txt` — `415f9cceb3bc96dff489552c19a916e63ccf14f22741a4b320c970104032faa4`

## Limits / not claimed

- This is implementation and QA closure for the P2c zero-shot facade, not a T1-T4 campaign and not business-semantic fidelity proof.
- HTTP 200 is not counted as fidelity; only schema/wire/transport/reset mechanics were validated here.
- Failure tests verify contract-shaped error bodies; they do not prove a complete inventory of partial persistent effects for every possible COBOL failure.
- P2c still depends on the existing built original COBOL artifacts from P2b; it does not call `p2b.build()`. The only wrapper built in P2c is the local interest linkage wrapper.
- No new oracle, quarantine expected data, E2 reuse, paid fallback, model retry, generation campaign, endpoint setup, telemetry endpoint, calendar/rounding/mainframe semantics, or persistence semantics were added.

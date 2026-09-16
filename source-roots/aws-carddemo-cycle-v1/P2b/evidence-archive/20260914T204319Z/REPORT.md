# P2b — bounded technical binding vertical slice

Scope: local technical binding before experimental tests. This is not official T1/T2/T3/T4, not comparative analysis, and not a semantic oracle.

## Implemented

- Localhost-only callable facade for the frozen P2a routes:
  - `POST /posting`
  - `POST /interest`
  - `POST /reporting`
- Per-invocation isolated work directories under `P2b/runs/`.
- Explicit source pins from preparation manifest commit `59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e`.
- Real GnuCOBOL build/run path for full3track:
  - `CBTRN02C` reached by `/posting`
  - `CBACT04C` reached by `/interest`
  - `CBTRN03C` reached by `/reporting`
- INV/RES/CAP/CONV/FAIL/STATE/RESP audit JSON per invocation, with actual capture paths, byte counts and hashes.
- Synthetic fixtures are labeled as technical smoke fixtures only, not evaluation oracle or extraction inputs.
- Orderly localhost process lifecycle recorded in `server-lifecycle.json`.

## Verification run

Commands actually executed from `P2b/`:

```text
python3 -m unittest discover -s tests -v
python3 p2b_binding.py smoke > latest-smoke.stdout.json
../P2a/.venv/bin/python validate_p2b.py > latest-schema.stdout.json
```

Observed result: exit 0.

Unit QA:

```text
Ran 3 tests in 0.042s
OK
```

Schema QA:

- `PostingEnvelope`: valid
- `InterestEnvelope`: valid
- `ReportingEnvelope`: valid
- `InterfaceError` bad-request shape: valid
- Overall: `true`

Technical smoke result in `readiness-manifest.json`:

- posting: HTTP 200, current body hash `6ce271a2728af697fff9916b5af390361220f8b5396b86330773ec061f40c5fe`
- interest: HTTP 200, current body hash `942ceec5f57cba7db8fbc725803900bf478200017eeb3c8fa0139ef22cea120f`
- reporting: HTTP 200, current body hash `9f875bb919d65e6730e0763e488e07ee13f08563200074186b8ca55f05119433`

Current capture guard: `readiness-manifest.json` records only directories created after the smoke invocation started:

- `runs/posting-9fqne1xr`
- `runs/interest-00sakxae`
- `runs/reporting-7_v3mkz0`
- `runs/reporting-source-iadzh2o9`

Tool versions observed:

```text
Python 3.9.6
cobc (GnuCOBOL) 3.2.0
node v18.18.0
```

## Artifact hashes

```text
94a68901a28a2ac05d81e805c5462b1986b293549cdb0926aaabc148edafed19  p2b_binding.py
bc6d6ef81524f9fda71acdf2d00b589d2798a5ec251a5a2cabdef317a26e8545  validate_p2b.py
ca7fe7d5460affeb21d61abdfffec94a757c630830fc6b8d0f16eb88e2681842  tests/test_p2b_contract.py
4002041f5243e33dada602b9661837d73ae375eb9ec8f39ff218ed8c34d4f082  readiness-manifest.json
0c31c795451b62a55ec2a2467c4ffc54814b21ff8df9f44c5f539aa570ae2a41  schema-validation-report.json
bf96b8853dbc84f72075aa10b3c71550ada78f65cc403ce9d8c8b76ff2b39b93  command-log.jsonl
8b063f70a35f45bb208ab66f122b179c435104584316369728bad217276f6712  server-lifecycle.json
```

## Readiness manifest

Done:

- P2a frozen contract preserved; no P2a/spec/source edits.
- Localhost facade callable for all three routes.
- Full3track technical smoke reached actual COBOL programs.
- Response bodies validated against P2a component schemas.
- Per-invocation audit/captures written.

Blocked:

- None for this bounded P2b technical slice.

Unverified / not claimed:

- No official T1/T2/T3/T4 execution.
- No semantic oracle, comparative analysis, or functional-continuity claim.
- No coverage claim.
- No P2/P3 human gate approval claimed.
- Local BDB/LE support remains a technical compatibility layer, not mainframe equivalence.

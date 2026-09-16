# Applicability mapping v1 review

**Verdict: PARTIAL**

PARTIAL: inventário/cobertura mecânica e guarda SDD{} passam; a matriz não deve ser usada como fonte direta de seleção T3 sem emendas porque há planos de campo semanticamente sobre-amplos e células condicionadas sem bloqueio embora o pacote atual não consiga selecionar as guardas.

## Mechanical checks

- Matrix validator: **PASS** (`PASS applicability matrix integrity`).
- Matrix unit tests: **PASS** (`Ran 5 tests in 0.047s; OK`).
- Static review probes: **PASS** (`probe-results.json` written).
- Programmatic inventory counts: `25` obligations, `7` contracts, `21` operations, `175` cells.
- Status counts: `{"expressible_by_surface": 76, "conditioned_on_external_fixture": 43, "not_expressible": 7, "precondition_indeterminate": 28, "observation_inadmissible": 14, "not_mapped": 7}`.

## PASS findings

1. **Inventory integrity passes.** 25 obligations × 7 contracts = 175 cells; 21 operation pairs are inventoried and mapped; 3 candidate fixtures are present.
2. **SDD{} guard passes.** All 25 E3 cells preserve closed empty request bodies with no field selectors. Source: `P2a/openapi-carddemo-stage6r3.yaml:201-229`.
3. **The matrix does not authorize campaign execution.** It keeps `campaign_authorization=false` and includes non-generative statuses (`not_expressible`, `precondition_indeterminate`, `observation_inadmissible`, `not_mapped`).

## Counterexamples / blockers to direct T3 use

### CE-001 — field-name heuristic produces non-realizable map plans

`applicability-mapping-v1/tools/build_matrix.py:242-243` maps any field containing `file/cross/account/categor/disclosure/output/reject/report` to the whole track resource set. That makes examples like `accountFile -> [XREFFILE, TCATBALF, TRANFILE, DALYREJS]` and `rejectFile -> [ACCTFILE, TCATBALF, TRANFILE, XREFFILE]` appear valid.

But `collection-01/E1-1/response-original.txt:96-105` declares separate bindings for `transactionFile`, `crossReferenceFile`, `accountFile`, `categoryBalanceFile`, and `rejectFile`. The probe found **318 selector/source mismatches**.

Minimum correction: replace token matching with per-field/per-track allowed sources, e.g. `accountFile -> ACCTFILE`, `categoryBalanceFile -> TCATBALF`, `rejectFile -> DALYREJS`, `transactionTypeFile -> TRANTYPE`, `reportOutput -> TRANREPT`.

### CE-002 — 175 inventory cells are not 175 valid/exercised T3 mappings

The current preflight T3 package has **1** synthetic case, path `['/posting']`, body `['e30=']` (`e30=` = `{}`). It does not exercise 175 cells and does not make the 76 `expressible_by_surface` cells admissible expected results.

Minimum correction: add separate dimensions for `inventory_cell`, `surface_expressible`, `fixture_variant_required`, `generative_admissible`, and `exercised_by_package`.

### CE-003 — conditioned fixture cells lack selectable guard variants

The probe found **16** guard-sensitive `conditioned_on_external_fixture` cells without plan blocks. Examples include `POSTTRAN-OBL-004/005/006/007` on E2-1/E2-3, `INTCALC-OBL-004/005/007` on E2-1/E2-3, and `TRANREPT-OBL-004` on E2-1/E2-3.

Source anchors:

- `CBTRN02C.cbl:380-391`: missing XREF sets reason 100.
- `CBTRN02C.cbl:467-542`: TCATBAL read/create/update/write/rewrite branches depend on file status 00/23/other.
- `CBACT04C.cbl:415-460`: DISCGRP uses specific rate, then DEFAULT on status 23, then abends if DEFAULT missing.
- `CBTRN03C.cbl:181-196`: card break and lookup sequence.

Minimum correction: require a named fixture variant/resource-package selector for each such branch, or mark the cell blocked/precondition-indeterminate for T3 generation.

### CE-004 — interest zero-rate/default is data-supported but not request-selectable in E2-1/E2-3

The interest package contains `STANDARD`, `ZERORATE`, and `DEFAULT` DISCGRP keys and two account groups, so it can support candidate data points. But E2-1/E2-3 expose only `transactionIdPrefix`; they cannot select account group/rate branch through the request. `CBACT04C.cbl:210-217` skips compute when `DIS-INT-RATE = 0`; `CBACT04C.cbl:436-459` enters DEFAULT only after status 23.

Minimum correction: require explicit fixture scheduling/variants for STANDARD/ZERORATE/DEFAULT/missing-default; do not infer branch admissibility from `transactionIdPrefix`.

### CE-005 — reporting EOF/raw/order is only partly protected

The blocked statuses are directionally correct, but their plans still contain generic transaction/date selectors. `CBTRN03C.cbl:170-178` tests date after READ, `197-203` adds current `TRAN-AMT` in EOF branch, and `306-316` writes account totals only through `1120`, not as a final EOF action. Transaction/date fields alone must not become expected totals.

Minimum correction: for blocked reporting EOF/raw/order cells, omit executable field selectors or mark them as diagnostics-only.

### CE-006 — posting partial effects/lookup remain non-generative

The source and original contract support the partial-effects concern: `collection-01/E1-1/response-original.txt:69-79`, `CBTRN02C.cbl:440-442`, `554-559`, `562-578`. The matrix correctly blocks `POSTTRAN-OBL-008/009`, but generic map plans should not be usable to generate T3 cases until an authorized observation boundary exists.

Minimum correction: propagate non-generative status to the plan level by suppressing usable selectors for `POSTTRAN-OBL-008/009`.

## Minimal corrections summary

- Do not use mapped_contract_cells=175 as count of valid T3 mappings; report it as inventory coverage only.
- Add dimensions such as inventory_cell, surface_expressible, fixture_variant_required, generative_admissible, exercised_by_package.
- Replace has_rich_surface/field-name token matching with obligation-specific required controls and per-field source maps.
- For SDD {}, keep all substantive selection external; because no request selector exists, conditioned cells require named fixture scheduling/variant or must stay blocked.
- For reporting EOF/raw/ordering and posting partial-effect cells, suppress executable map plans unless an authorized observation boundary exists.
- Update validator/tests to fail on overbroad allowedSource and on conditioned guard-sensitive cells without fixture-variant blocks.

## Files

- `review.json` — structured verdict and findings.
- `REVIEW.md` — this human-readable review.
- `review_probes.py` — static probe script.
- `probe-results.json` — programmatic probe output.

#!/usr/bin/env python3
"""Static probes for applicability-mapping-v1 review.

Reads only pre-campaign mapping inputs and static schemas/packages. Does not read
runtime/API results, coverage, oracle outputs, quarantine, or official cases to
define expected behavior.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "applicability-mapping-v1" / "applicability_matrix.json"
BUILD = ROOT / "applicability-mapping-v1" / "tools" / "build_matrix.py"
INVENTORY = ROOT / "suite-adapters-preflight-v1" / "evidence-real-preflight-20260915T-synthetic" / "operation-inventory.json"
T3_SYNTHETIC = ROOT / "suite-adapters-preflight-v1" / "evidence-real-preflight-20260915T-synthetic" / "frozen-synthetic-suites" / "T3.json"
SDD = ROOT.parent / "P2a" / "openapi-carddemo-stage6r3.yaml"
FIXTURE_MANIFEST = ROOT / "fixture-materialization-v2" / "package" / "manifest.json"
OUT = ROOT / "applicability-review-v1" / "probe-results.json"

EXPECTED_BY_FIELD = {
    # posting/interest file-ish fields
    "accountFile": {"ACCTFILE"},
    "accounts": {"ACCTFILE"},
    "categoryBalanceFile": {"TCATBALF"},
    "categoryBalances": {"TCATBALF"},
    "crossReferenceFile": {"XREFFILE", "CARDXREF"},
    "cardCrossReference": {"XREFFILE", "CARDXREF"},
    "disclosureGroupFile": {"DISCGRP"},
    "disclosureGroups": {"DISCGRP"},
    "outputTransactionFile": {"TRANSACT", "TRANFILE"},
    "transactionOutput": {"TRANSACT", "TRANFILE"},
    "transactionFile": {"TRANFILE"},
    "rejectFile": {"DALYREJS"},
    "rejectionOutput": {"DALYREJS"},
    # reporting file-ish fields
    "transactionTypeFile": {"TRANTYPE"},
    "transactionTypes": {"TRANTYPE"},
    "transactionCategoryFile": {"TRANCATG"},
    "transactionCategories": {"TRANCATG"},
    "reportFile": {"TRANREPT"},
    "reportOutput": {"TRANREPT"},
}

# Obligations whose guard requires a missing/error/ordering/finalization state
# not selectably varied by the current fixed candidate package alone.
GUARD_SENSITIVE = {
    "POSTTRAN-OBL-004": "requires choosing XREF present vs missing for a card",
    "POSTTRAN-OBL-005": "requires account/limit/expiration/active-state combinations",
    "POSTTRAN-OBL-006": "requires validation-rejection branch selection",
    "POSTTRAN-OBL-007": "requires TCATBAL status 00 vs 23 and write/rewrite outcomes",
    "INTCALC-OBL-004": "requires DISCGRP specific vs DEFAULT vs missing/default-missing",
    "INTCALC-OBL-005": "requires zero/nonzero rate and balance combinations",
    "INTCALC-OBL-007": "requires category-balance group boundaries/order",
    "TRANREPT-OBL-003": "requires EOF receiver/retention condition control",
    "TRANREPT-OBL-004": "requires card break and lookup-present/missing variants",
    "TRANREPT-OBL-005": "requires page boundary volume/state",
    "TRANREPT-OBL-007": "requires EOF branch with retained/current amount condition",
    "TRANREPT-OBL-008": "requires final account-total observation boundary",
}


def main() -> None:
    matrix = json.loads(MATRIX.read_text())
    inventory = json.loads(INVENTORY.read_text())
    fixture_manifest = json.loads(FIXTURE_MANIFEST.read_text())
    t3 = json.loads(T3_SYNTHETIC.read_text())

    cells = []
    for obl in matrix["obligations"]:
        for cm in obl["contractMappings"]:
            cells.append({"obligation": obl, "mapping": cm})

    status_counts = Counter(c["mapping"]["applicabilityStatus"] for c in cells)
    by_track = Counter((c["obligation"]["track"], c["mapping"]["applicabilityStatus"]) for c in cells)

    selector_mismatches = []
    for c in cells:
        oid = c["obligation"]["obligationId"]
        cm = c["mapping"]
        for sel in cm["t3DeterministicMapping"].get("fieldSelectors", []):
            field = sel.get("field")
            allowed = sel.get("allowedSource")
            if field in EXPECTED_BY_FIELD and isinstance(allowed, list):
                unexpected = sorted(set(allowed) - EXPECTED_BY_FIELD[field])
                missing_expected = sorted(EXPECTED_BY_FIELD[field] - set(allowed))
                if unexpected or missing_expected:
                    selector_mismatches.append({
                        "obligationId": oid,
                        "contractId": cm["contractId"],
                        "field": field,
                        "allowedSource": allowed,
                        "unexpectedSources": unexpected,
                        "missingExpectedSources": missing_expected,
                        "status": cm["applicabilityStatus"],
                    })

    sdd_cells = [c for c in cells if c["mapping"]["contractId"] == "E3-01-SDD-stage6r3"]
    sdd_selector_violations = [
        {"obligationId": c["obligation"]["obligationId"], "plan": c["mapping"]["t3DeterministicMapping"]}
        for c in sdd_cells
        if c["mapping"]["operation"]["requestSchema"].get("properties") != []
        or c["mapping"]["t3DeterministicMapping"].get("requestBody") != {}
        or c["mapping"]["t3DeterministicMapping"].get("fieldSelectors")
    ]

    conditioned_guard_cells_without_block = []
    for c in cells:
        oid = c["obligation"]["obligationId"]
        cm = c["mapping"]
        if cm["applicabilityStatus"] == "conditioned_on_external_fixture" and oid in GUARD_SENSITIVE:
            blocks = cm["t3DeterministicMapping"].get("blocks", [])
            if not blocks:
                conditioned_guard_cells_without_block.append({
                    "obligationId": oid,
                    "contractId": cm["contractId"],
                    "status": cm["applicabilityStatus"],
                    "reason": GUARD_SENSITIVE[oid],
                    "properties": cm["operation"]["requestSchema"].get("properties"),
                })

    operation_pairs = {(op["contractId"], op["operationId"], op["path"]) for op in inventory["operations"]}
    mapped_operation_pairs = {
        (c["mapping"]["contractId"], c["mapping"]["operation"]["operationId"], c["mapping"]["operation"]["path"])
        for c in cells
    }

    build_text = BUILD.read_text()
    result = {
        "verdict_hint": "PARTIAL",
        "input_policy": {
            "runtime_api_coverage_oracle_quarantine_read": False,
            "files_read_by_probe": [
                str(MATRIX.relative_to(ROOT.parent)),
                str(BUILD.relative_to(ROOT.parent)),
                str(INVENTORY.relative_to(ROOT.parent)),
                str(T3_SYNTHETIC.relative_to(ROOT.parent)),
                str(SDD.relative_to(ROOT.parent)),
                str(FIXTURE_MANIFEST.relative_to(ROOT.parent)),
            ],
        },
        "inventory_counts": {
            "obligations": len(matrix["obligations"]),
            "contracts": len(matrix["contracts"]),
            "operations_inventory": inventory["operationCount"],
            "operation_pairs_inventory": len(operation_pairs),
            "operation_pairs_mapped": len(mapped_operation_pairs),
            "cells": len(cells),
            "declared_cells": matrix["denominators"]["mapped_contract_cells"],
            "status_counts": dict(status_counts),
            "by_track_status": {f"{k[0]}:{k[1]}": v for k, v in sorted(by_track.items())},
            "candidate_fixtures": len(fixture_manifest["fixtures"]),
        },
        "sdd_empty_request_guard": {
            "checked_cells": len(sdd_cells),
            "violations": sdd_selector_violations,
            "sdd_request_schema_lines": "P2a/openapi-carddemo-stage6r3.yaml:201-229",
        },
        "t3_current_package": {
            "synthetic_cases": len(t3.get("cases", [])),
            "paths": sorted({case["request"]["path"] for case in t3.get("cases", [])}),
            "body_b64_values": sorted({case["request"].get("body_b64") for case in t3.get("cases", [])}),
            "note": "preflight synthetic T3 exercises one {} request, not 175 obligation/contract mappings",
        },
        "selector_mismatches": {
            "count": len(selector_matches := selector_mismatches),
            "by_field": dict(Counter(m["field"] for m in selector_mismatches)),
            "examples": selector_mismatches[:20],
        },
        "conditioned_guard_cells_without_block": {
            "count": len(conditioned_guard_cells_without_block),
            "by_obligation": dict(Counter(m["obligationId"] for m in conditioned_guard_cells_without_block)),
            "examples": conditioned_guard_cells_without_block[:20],
        },
        "builder_heuristic_evidence": {
            "has_any_token_fieldname_rule": "any(token in field.lower()" in build_text,
            "has_coarse_rich_surface_rule": "def has_rich_surface" in build_text,
            "line_refs": ["applicability-mapping-v1/tools/build_matrix.py:183-193", "applicability-mapping-v1/tools/build_matrix.py:221-255"],
        },
    }
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

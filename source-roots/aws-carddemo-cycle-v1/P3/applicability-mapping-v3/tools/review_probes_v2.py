#!/usr/bin/env python3
"""Static review probes for applicability-mapping-v2.

Reads only pre-campaign mapping inputs and static schemas/packages. Does not read
runtime/API results, coverage, oracle outputs, quarantine, official generated
cases, or model-call outputs to define expected behavior.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
CYCLE = P3.parent
MATRIX = ROOT / "applicability_matrix.json"
BUILD = ROOT / "tools" / "build_matrix.py"
INVENTORY = P3 / "suite-adapters-preflight-v1" / "evidence-real-preflight-20260915T-synthetic" / "operation-inventory.json"
T3_SYNTHETIC = P3 / "suite-adapters-preflight-v1" / "evidence-real-preflight-20260915T-synthetic" / "frozen-synthetic-suites" / "T3.json"
SDD = CYCLE / "P2a" / "openapi-carddemo-stage6r3.yaml"
FIXTURE_MANIFEST = P3 / "fixture-materialization-v2" / "package" / "manifest.json"
OUT = ROOT / "probe-results-v2.json"

EXPECTED_BY_TRACK = {
    "posting": {
        "accountFile": {"ACCTFILE"}, "accounts": {"ACCTFILE"},
        "categoryBalanceFile": {"TCATBALF"}, "categoryBalances": {"TCATBALF"},
        "crossReferenceFile": {"XREFFILE"}, "cardCrossReference": {"XREFFILE"},
        "transactionFile": {"TRANFILE"}, "outputTransactionFile": {"TRANFILE"},
        "transactionOutput": {"TRANFILE"}, "rejectFile": {"DALYREJS"},
        "rejectionOutput": {"DALYREJS"},
    },
    "interest": {
        "accountFile": {"ACCTFILE"}, "accounts": {"ACCTFILE"},
        "categoryBalanceFile": {"TCATBALF"}, "categoryBalances": {"TCATBALF"},
        "crossReferenceFile": {"XREFFILE"}, "cardCrossReference": {"XREFFILE"},
        "disclosureGroupFile": {"DISCGRP"}, "disclosureGroups": {"DISCGRP"},
        "outputTransactionFile": {"TRANSACT"}, "transactionOutput": {"TRANSACT"},
    },
    "reporting": {
        "crossReferenceFile": {"CARDXREF"}, "cardCrossReference": {"CARDXREF"},
        "transactionTypeFile": {"TRANTYPE"}, "transactionTypes": {"TRANTYPE"},
        "transactionCategoryFile": {"TRANCATG"}, "transactionCategories": {"TRANCATG"},
        "reportFile": {"TRANREPT"}, "reportOutput": {"TRANREPT"},
    },
}

GUARD_SENSITIVE = {
    "POSTTRAN-OBL-004", "POSTTRAN-OBL-005", "POSTTRAN-OBL-006", "POSTTRAN-OBL-007",
    "INTCALC-OBL-004", "INTCALC-OBL-005", "INTCALC-OBL-007",
    "TRANREPT-OBL-003", "TRANREPT-OBL-004", "TRANREPT-OBL-005", "TRANREPT-OBL-007", "TRANREPT-OBL-008",
}

DIAGNOSTICS_ONLY = {"POSTTRAN-OBL-008", "POSTTRAN-OBL-009", "TRANREPT-OBL-003", "TRANREPT-OBL-007", "TRANREPT-OBL-008"}


def main() -> None:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    fixture_manifest = json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))
    t3 = json.loads(T3_SYNTHETIC.read_text(encoding="utf-8"))
    build_text = BUILD.read_text(encoding="utf-8")

    cells = [{"obligation": obl, "mapping": cm} for obl in matrix["obligations"] for cm in obl["contractMappings"]]
    selector_mismatches = []
    for c in cells:
        track = c["obligation"]["track"]
        expected = EXPECTED_BY_TRACK[track]
        for sel in c["mapping"]["t3DeterministicMapping"].get("fieldSelectors", []):
            field = sel.get("field")
            if field in expected:
                observed = set(sel.get("allowedSource", []))
                if observed != expected[field]:
                    selector_mismatches.append({
                        "obligationId": c["obligation"]["obligationId"],
                        "contractId": c["mapping"]["contractId"],
                        "field": field,
                        "allowedSource": sorted(observed),
                        "expectedSource": sorted(expected[field]),
                    })

    sdd_cells = [c for c in cells if c["mapping"]["contractId"] == "E3-01-SDD-stage6r3"]
    sdd_selector_violations = [
        {"obligationId": c["obligation"]["obligationId"], "plan": c["mapping"]["t3DeterministicMapping"]}
        for c in sdd_cells
        if c["mapping"]["operation"]["requestSchema"].get("properties") != []
        or c["mapping"]["t3DeterministicMapping"].get("requestBody") != {}
        or c["mapping"]["t3DeterministicMapping"].get("fieldSelectors")
        or c["mapping"]["t3DeterministicMapping"].get("selectionMode") not in {"external_fixture_schedule_only", "blocked_pending_documented_named_variant"}
    ]

    conditioned_guard_cells_without_block = []
    diagnostics_with_executable_selectors = []
    for c in cells:
        oid = c["obligation"]["obligationId"]
        cm = c["mapping"]
        plan = cm["t3DeterministicMapping"]
        if cm["applicabilityStatus"] == "conditioned_on_external_fixture" and oid in GUARD_SENSITIVE:
            if not plan.get("fixtureVariant") and not plan.get("blocks"):
                conditioned_guard_cells_without_block.append({"obligationId": oid, "contractId": cm["contractId"]})
        if oid in DIAGNOSTICS_ONLY and plan.get("fieldSelectors"):
            diagnostics_with_executable_selectors.append({"obligationId": oid, "contractId": cm["contractId"], "fieldSelectors": plan["fieldSelectors"]})

    operation_pairs = {(op["contractId"], op["operationId"], op["path"]) for op in inventory["operations"]}
    mapped_operation_pairs = {
        (c["mapping"]["contractId"], c["mapping"]["operation"]["operationId"], c["mapping"]["operation"]["path"])
        for c in cells
    }
    status_counts = Counter(c["mapping"]["applicabilityStatus"] for c in cells)
    by_track = Counter((c["obligation"]["track"], c["mapping"]["applicabilityStatus"]) for c in cells)
    dims = matrix["denominators"]["dimensions"]

    result = {
        "verdict_hint": "candidate_needs_review",
        "input_policy": {
            "runtime_api_coverage_oracle_quarantine_read": False,
            "official_generated_cases_used_as_expected": False,
            "model_calls_used": False,
            "files_read_by_probe": [
                str(MATRIX.relative_to(CYCLE)), str(BUILD.relative_to(CYCLE)), str(INVENTORY.relative_to(CYCLE)),
                str(T3_SYNTHETIC.relative_to(CYCLE)), str(SDD.relative_to(CYCLE)), str(FIXTURE_MANIFEST.relative_to(CYCLE)),
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
            "dimensions": dims,
            "plan_counts": matrix["denominators"]["plan_counts"],
        },
        "sdd_empty_request_guard": {"checked_cells": len(sdd_cells), "violations": sdd_selector_violations},
        "t3_current_package": {
            "synthetic_cases": len(t3.get("cases", [])),
            "paths": sorted({case["request"]["path"] for case in t3.get("cases", [])}),
            "body_b64_values": sorted({case["request"].get("body_b64") for case in t3.get("cases", [])}),
            "note": "preflight synthetic T3 exercises no official obligation/contract mapping cells in v2",
        },
        "selector_mismatches": {"count": len(selector_mismatches), "examples": selector_mismatches[:20]},
        "conditioned_guard_cells_without_block": {"count": len(conditioned_guard_cells_without_block), "examples": conditioned_guard_cells_without_block[:20]},
        "diagnostics_with_executable_selectors": {"count": len(diagnostics_with_executable_selectors), "examples": diagnostics_with_executable_selectors[:20]},
        "builder_heuristic_evidence": {
            "has_any_token_fieldname_rule": "any(token in field.lower()" in build_text,
            "has_explicit_field_source_table": "FIELD_SOURCE_BY_TRACK" in build_text,
        },
    }
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

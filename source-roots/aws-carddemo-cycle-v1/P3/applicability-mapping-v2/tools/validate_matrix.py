#!/usr/bin/env python3
"""Validate applicability_matrix.json integrity against frozen inputs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
CYCLE = P3.parent
MATRIX = ROOT / "applicability_matrix.json"
REFERENCE = P3 / "reference-executable-v4" / "model.json"
INVENTORY = P3 / "suite-adapters-preflight-v1" / "evidence-real-preflight-20260915T-synthetic" / "operation-inventory.json"
FIXTURES = P3 / "fixture-materialization-v2" / "package" / "manifest.json"

REQUIRED_STATUSES = {
    "expressible_by_surface",
    "conditioned_on_external_fixture",
    "not_expressible",
    "not_mapped",
    "precondition_indeterminate",
    "observation_inadmissible",
}

FIELD_SOURCE_BY_TRACK = {
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


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def error(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    if not MATRIX.exists():
        print(f"FAIL missing {MATRIX}")
        return 1
    matrix = load(MATRIX)
    reference = load(REFERENCE)
    inventory = load(INVENTORY)
    fixtures = load(FIXTURES)

    ref_ids = {o["id"] for o in reference["obligations"]}
    matrix_ids = {o["obligationId"] for o in matrix.get("obligations", [])}
    if ref_ids != matrix_ids:
        error(errors, f"obligation coverage mismatch missing={sorted(ref_ids - matrix_ids)} extra={sorted(matrix_ids - ref_ids)}")

    if matrix.get("status") != "candidate_needs_review" or matrix.get("campaign_authorization") is not False:
        error(errors, "matrix must remain candidate_needs_review and campaign_authorization=false")

    den = matrix.get("denominators", {})
    expected_den = {
        "obligations": len(reference["obligations"]),
        "contracts": len(inventory["contracts"]),
        "operations": len(inventory["operations"]),
        "candidateFixtures": len(fixtures["fixtures"]),
        "obligation_contract_cells": len(reference["obligations"]) * len(inventory["contracts"]),
    }
    for key, value in expected_den.items():
        if den.get(key) != value:
            error(errors, f"denominator {key} expected {value} observed {den.get(key)}")
    mapped = sum(len(o.get("contractMappings", [])) for o in matrix.get("obligations", []))
    if den.get("mapped_contract_cells") != mapped:
        error(errors, f"mapped_contract_cells expected {mapped} observed {den.get('mapped_contract_cells')}")
    if den.get("calculation") != "programmatic":
        error(errors, "denominators.calculation must be programmatic")

    ops = {(op["contractId"], op["method"].lower(), op["path"], op["operationId"]) for op in inventory["operations"]}
    fixture_ids = {f["fixtureId"] for f in matrix.get("fixtures", [])}
    statuses_seen = set()
    status_counts = {}
    for obl in matrix.get("obligations", []):
        if len(obl.get("contractMappings", [])) != len(inventory["contracts"]):
            error(errors, f"{obl.get('obligationId')} has {len(obl.get('contractMappings', []))} mappings")
        for mapping in obl.get("contractMappings", []):
            op = mapping["operation"]
            key = (mapping["contractId"], op["method"].lower(), op["path"], op["operationId"])
            if key not in ops:
                error(errors, f"operation ref not in inventory: {key}")
            status = mapping.get("applicabilityStatus")
            statuses_seen.add(status)
            status_counts[status] = status_counts.get(status, 0) + 1
            if status not in matrix.get("status_taxonomy", {}):
                error(errors, f"unknown status {status}")
            for fx in mapping.get("candidateFixtures", []):
                if fx.get("fixtureId") not in fixture_ids:
                    error(errors, f"unknown fixture {fx.get('fixtureId')}")
            if mapping["contractId"] == "E3-01-SDD-stage6r3":
                t3 = mapping["t3DeterministicMapping"]
                schema = op["requestSchema"]
                if schema.get("properties") != [] or schema.get("additionalProperties") is not False:
                    error(errors, "SDD schema must remain closed empty object")
                if t3.get("requestBody") != {} or t3.get("fieldSelectors") != [] or t3.get("newSelectorsIntroduced") is not False:
                    error(errors, "SDD T3 mapping introduced selector/request mutation")
    all_mappings = [m for o in matrix.get("obligations", []) for m in o.get("contractMappings", [])]
    dims_count = {
        "inventory_cells": len(all_mappings),
        "surface_expressible_cells": sum(1 for m in all_mappings if m.get("applicabilityDimensions", {}).get("surface_expressible")),
        "fixture_variant_required_cells": sum(1 for m in all_mappings if m.get("applicabilityDimensions", {}).get("fixture_variant_required")),
        "generative_admissible_cells": sum(1 for m in all_mappings if m.get("applicabilityDimensions", {}).get("generative_admissible")),
        "exercised_by_package_cells": sum(1 for m in all_mappings if m.get("applicabilityDimensions", {}).get("exercised_by_package")),
    }
    if den.get("dimensions") != dims_count:
        error(errors, f"dimensions mismatch expected {dims_count} observed {den.get('dimensions')}")
    if dims_count["inventory_cells"] != 175 or dims_count["exercised_by_package_cells"] != 0:
        error(errors, "inventory/exercised dimensions must remain 175 inventory cells and 0 officially exercised cells")
    for obligation in matrix.get("obligations", []):
        track = obligation.get("track")
        oid = obligation.get("obligationId")
        for mapping in obligation.get("contractMappings", []):
            dims = mapping.get("applicabilityDimensions", {})
            status = mapping.get("applicabilityStatus")
            if dims.get("inventory_cell") is not True or dims.get("exercised_by_package") is not False:
                error(errors, f"bad inventory/exercised dimensions for {oid} {mapping.get('contractId')}")
            if dims.get("surface_expressible") != (status == "expressible_by_surface"):
                error(errors, f"surface dimension mismatch for {oid} {mapping.get('contractId')}")
            plan = mapping.get("t3DeterministicMapping", {})
            for selector in plan.get("fieldSelectors", []):
                field = selector.get("field")
                if field in FIELD_SOURCE_BY_TRACK.get(track, {}):
                    observed = set(selector.get("allowedSource", []))
                    expected = FIELD_SOURCE_BY_TRACK[track][field]
                    if observed != expected:
                        error(errors, f"selector source mismatch {oid} {mapping.get('contractId')} {field}: {sorted(observed)} != {sorted(expected)}")
            if oid in GUARD_SENSITIVE and status == "conditioned_on_external_fixture" and not plan.get("fixtureVariant") and not plan.get("blocks"):
                error(errors, f"guard-sensitive conditioned cell lacks variant/block {oid} {mapping.get('contractId')}")
            if oid in DIAGNOSTICS_ONLY:
                if plan.get("fieldSelectors"):
                    error(errors, f"diagnostics-only cell has executable selectors {oid} {mapping.get('contractId')}")
                if plan.get("generativeUse") != "diagnostics_only_non_generative":
                    error(errors, f"diagnostics-only cell has wrong generativeUse {oid} {mapping.get('contractId')}")
    if not REQUIRED_STATUSES.issubset(statuses_seen):
        error(errors, f"taxonomy statuses not represented: {sorted(REQUIRED_STATUSES - statuses_seen)}")
    if den.get("status_counts") != status_counts:
        error(errors, f"status_counts mismatch expected {status_counts} observed {den.get('status_counts')}")

    if errors:
        print("FAIL")
        for item in errors:
            print("-", item)
        return 1
    print("PASS applicability matrix integrity")
    print(json.dumps({"denominators": den}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

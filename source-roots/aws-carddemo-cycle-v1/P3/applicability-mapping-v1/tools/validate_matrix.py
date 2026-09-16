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

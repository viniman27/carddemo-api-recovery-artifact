#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

P3 = Path(__file__).resolve().parents[1]
ADAPTER_SRC = P3 / "t3-campaign-adapter-v3" / "src"
MAPPING_SRC = P3 / "t3-mapping-integration-v2" / "src"
if str(ADAPTER_SRC) not in sys.path:
    sys.path.insert(0, str(ADAPTER_SRC))
if str(MAPPING_SRC) not in sys.path:
    sys.path.insert(0, str(MAPPING_SRC))

from mapping_integration import build_enriched_plan  # noqa: E402
from t3_campaign_adapter import (  # noqa: E402
    AdapterBlocked,
    apply_sdd_id_migration,
    build_t3_suite,
    load_contract_registry,
    load_model,
    resolve_contract_source,
    validate_model,
)

OUT = P3 / "t3-sdd-external-selection-v1"
SDD_MATRIX_ID = "E3-01-SDD-stage6r3"
SDD_REGISTRY_ID = "E3-SDD-stage6r3"

SELECTABLE_OBLIGATIONS = {
    "POSTTRAN-OBL-001": {
        "fixtureId": "posting.candidate-v1-physical-v2",
        "resourceChecks": ["posting:DALYTRAN:recordCount>=1", "posting:XREFFILE:recordCount>=1", "posting:ACCTFILE:recordCount>=1", "posting:TCATBALF:recordCount>=1"],
        "guardBasis": ["open_status=00 is selected by package physical-resource presence only", "request body remains {}"],
    },
    "POSTTRAN-OBL-002": {
        "fixtureId": "posting.candidate-v1-physical-v2",
        "resourceChecks": ["posting:DALYTRAN:recordCount>=1"],
        "guardBasis": ["read_status=00 selected by non-empty DALYTRAN sequential input", "EOF/other/UnknownEOF are not selected here"],
    },
    "POSTTRAN-OBL-004": {
        "fixtureId": "posting.candidate-v1-physical-v2",
        "resourceChecks": ["posting:DALYTRAN:recordCount>=1", "posting:XREFFILE:recordCount>=1"],
        "guardBasis": ["xref_exists has concrete present and absent source-bound records in DALYTRAN/CARDXREF family", "no expected result is derived"],
    },
    "POSTTRAN-OBL-005": {
        "fixtureId": "posting.candidate-v1-physical-v2",
        "resourceChecks": ["posting:ACCTFILE:recordCount>=1", "posting:XREFFILE:recordCount>=1"],
        "guardBasis": ["account_exists=true and account state fields are source-bound in ACCTFILE for the present card", "negative/expired variants are not selected"],
    },
    "POSTTRAN-OBL-006": {
        "fixtureId": "posting.candidate-v1-physical-v2",
        "resourceChecks": ["posting:DALYTRAN:recordCount>=1", "posting:XREFFILE:recordCount>=1"],
        "guardBasis": ["reject branch is externally selectable by DALYTRAN record with card absent from XREFFILE", "reject output contents remain outside expected authority"],
    },
    "POSTTRAN-OBL-007": {
        "fixtureId": "posting.candidate-v1-physical-v2",
        "resourceChecks": ["posting:TCATBALF:recordCount>=1"],
        "guardBasis": ["tcatbal_status 00/23 branch has package-local TCATBALF indexed resource and matching category keys", "failure status other is not selected"],
    },
    "INTCALC-OBL-001": {
        "fixtureId": "interest.candidate-v1-physical-v2",
        "resourceChecks": ["interest:TCATBALF:recordCount>=1", "interest:XREFFILE:recordCount>=1", "interest:ACCTFILE:recordCount>=1", "interest:DISCGRP:recordCount>=1", "interest:PARMFILE:bytes=10"],
        "guardBasis": ["open_status=00 is selected by package physical-resource presence and PARMFILE bytes", "request body remains {}"],
    },
    "INTCALC-OBL-002": {
        "fixtureId": "interest.candidate-v1-physical-v2",
        "resourceChecks": ["interest:TCATBALF:recordCount>=1"],
        "guardBasis": ["tcatbal_read_status=00 selected by non-empty TCATBALF sequential input", "EOF/other are not selected here"],
    },
    "INTCALC-OBL-003": {
        "fixtureId": "interest.candidate-v1-physical-v2",
        "resourceChecks": ["interest:TCATBALF:recordCount>=1", "interest:XREFFILE:alternateKeys>=1", "interest:ACCTFILE:recordCount>=1"],
        "guardBasis": ["new group account/xref lookup has matching ACCTFILE primary keys and XREFFILE alternate keys", "missing lookup is not selected"],
    },
    "INTCALC-OBL-004": {
        "fixtureId": "interest.candidate-v1-physical-v2",
        "resourceChecks": ["interest:DISCGRP:keys include STANDARD/DEFAULT/ZERORATE"],
        "guardBasis": ["disc_rate_path specific/default/zero are concretely source-bound by DISCGRP keys", "missing DEFAULT remains blocked"],
    },
    "INTCALC-OBL-005": {
        "fixtureId": "interest.candidate-v1-physical-v2",
        "resourceChecks": ["interest:DISCGRP:keys include nonzero and zero rates", "interest:TCATBALF:recordCount>=1"],
        "guardBasis": ["rate nonzero and zero partitions are selectable by DISCGRP records; formula expected output is not generated"],
    },
    "INTCALC-OBL-006": {
        "fixtureId": "interest.candidate-v1-physical-v2",
        "resourceChecks": ["interest:PARMFILE:bytes=10", "interest:XREFFILE:recordCount>=1"],
        "guardBasis": ["interest transaction field sources are available as parameter and lookup bytes", "write outcome remains unchecked"],
    },
    "TRANREPT-OBL-001": {
        "fixtureId": "reporting.candidate-v1-physical-v2",
        "resourceChecks": ["reporting:TRANFILE:recordCount>=1", "reporting:DATEPARM:recordCount=1", "reporting:CARDXREF:recordCount>=1", "reporting:TRANTYPE:recordCount>=1", "reporting:TRANCATG:recordCount>=1"],
        "guardBasis": ["previous not_mapped for SDD reporting is corrected in the versioned copy: /reporting operation plus external reporting package supply the selectable file context", "SORT/REPROC execution is not claimed"],
    },
    "TRANREPT-OBL-002": {
        "fixtureId": "reporting.candidate-v1-physical-v2",
        "resourceChecks": ["reporting:DATEPARM:recordCount=1", "reporting:TRANFILE:recordCount>=1"],
        "guardBasis": ["DATEPARM 2022-07-01..2022-07-31 and TRANFILE with at least one 2022-07 record select date_window=in_range", "EOF receiver behavior not selected"],
    },
    "TRANREPT-OBL-003": {
        "fixtureId": "reporting.candidate-v1-physical-v2",
        "resourceChecks": ["reporting:DATEPARM:recordCount=1", "reporting:TRANFILE:recordCount>=1"],
        "guardBasis": ["TRANFILE includes an out-of-range August record against July DATEPARM, selecting the skip-detail branch", "empty-input/UnknownEOF is not promoted"],
    },
    "TRANREPT-OBL-004": {
        "fixtureId": "reporting.candidate-v1-physical-v2",
        "resourceChecks": ["reporting:CARDXREF:recordCount>=1", "reporting:TRANTYPE:recordCount>=1", "reporting:TRANCATG:recordCount>=1"],
        "guardBasis": ["lookups for the in-range transaction have matching package-local indexed resources", "absent lookup abend is not selected"],
    },
    "TRANREPT-OBL-005": {
        "fixtureId": "reporting.candidate-v1-physical-v2",
        "resourceChecks": ["reporting:TRANFILE:recordCount>=1", "reporting:DATEPARM:recordCount=1"],
        "guardBasis": ["first-detail/header branch is selectable from one in-range transaction", "page-boundary after 20 lines is not selected"],
    },
    "TRANREPT-OBL-006": {
        "fixtureId": "reporting.candidate-v1-physical-v2",
        "resourceChecks": ["reporting:TRANFILE:recordCount>=1", "reporting:TRANTYPE:recordCount>=1", "reporting:TRANCATG:recordCount>=1"],
        "guardBasis": ["detail/accrual branch has transaction and lookup bytes", "edited-money expected formatting is not asserted"],
    },
}

EXPLICIT_BLOCKERS = {
    "POSTTRAN-OBL-003": "observable posted-record layout depends on accepted path and generated timestamp; request {} + base fixture can select the run but not an independent expected field oracle",
    "POSTTRAN-OBL-008": "ACCOUNT update/order effect needs runtime/internal state authority; not selected by external package alone",
    "POSTTRAN-OBL-009": "TRANFILE write/failure after prior effects remains precondition-indeterminate without execution-state authority",
    "INTCALC-OBL-007": "group-break ACCOUNT update needs multi-group transition outcome; base package alone does not authorize expected effect",
    "INTCALC-OBL-008": "normal EOF final-account absence is a static source finding, not fixture-selectable expected behavior",
    "TRANREPT-OBL-007": "EOF totals depend on receiver/content behavior explicitly treated as conditional/unknown",
    "TRANREPT-OBL-008": "absence of final account total is source-static and observation-inadmissible as external selection without report oracle",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: Any) -> bytes:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def pin(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": sha256_bytes(data)}


def package_resource_summary(fixture_manifest: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for track, pkg in sorted((fixture_manifest.get("packages") or {}).items()):
        resources: dict[str, Any] = {}
        for seq in pkg.get("sequential", []) or []:
            resources[str(seq["dd"])] = {k: seq.get(k) for k in ("bytes", "sha256", "recordCount", "recordSize", "source") if k in seq}
        for idx in pkg.get("indexed", []) or []:
            resources[str(idx["dd"])] = {
                "recordCount": idx.get("recordCount"),
                "recordSize": idx.get("recordSize"),
                "keys": idx.get("keys", []),
                "alternateKeyName": idx.get("alternateKeyName"),
                "alternateKeys": idx.get("alternateKeys", []),
                "physicalFiles": idx.get("physicalFiles", {}),
            }
        out[track] = {"fixtureId": next((f.get("fixtureId") for f in fixture_manifest.get("fixtures", []) if f.get("track") == track), None), "resources": resources}
    return out


def resource_authority_for(track: str, fixture_manifest: dict[str, Any]) -> dict[str, Any]:
    return package_resource_summary(fixture_manifest)[track]


def verify_current_fixture_bytes(fixture_manifest_path: Path) -> dict[str, Any]:
    manifest = load_json(fixture_manifest_path)
    base = fixture_manifest_path.parent
    mismatches = []
    checked = []
    for track, pkg in sorted((manifest.get("packages") or {}).items()):
        for rel, expected in sorted(((pkg.get("inventory") or {}).get("files") or {}).items()):
            path = base / track / rel
            if not path.exists():
                mismatches.append({"track": track, "path": rel, "error": "missing"})
                continue
            data = path.read_bytes()
            got = {"bytes": len(data), "sha256": sha256_bytes(data)}
            checked.append({"track": track, "path": rel, **got})
            if got.get("bytes") != expected.get("bytes") or got.get("sha256") != expected.get("sha256"):
                mismatches.append({"track": track, "path": rel, "expected": expected, "actual": got})
    return {"status": "PASS" if not mismatches else "FAIL", "checkedCount": len(checked), "mismatches": mismatches, "checked": checked}


def sdd_request_schema_is_empty(openapi: dict[str, Any], path: str) -> bool:
    op = ((openapi.get("paths") or {}).get(path) or {}).get("post") or {}
    schema = ((((op.get("requestBody") or {}).get("content") or {}).get("application/json") or {}).get("schema") or {})
    if "$ref" in schema:
        name = str(schema["$ref"]).rsplit("/", 1)[-1]
        schema = ((openapi.get("components") or {}).get("schemas") or {}).get(name) or {}
    return schema.get("type") == "object" and schema.get("additionalProperties") is False and not schema.get("properties") and not schema.get("required")


def amended_sdd_recipes_from_plan(plan: dict[str, Any], registry_source: Any) -> dict[str, Any]:
    recipes = []
    for track, opid, path in (("posting", "posting", "/posting"), ("interest", "interest", "/interest"), ("reporting", "reporting", "/reporting")):
        fixture_id = plan["fixturesByTrack"][track]["fixtureId"]
        recipes.append({
            "recipeId": f"{SDD_MATRIX_ID}:{track}:{opid}:{path}:external-selection-v1",
            "contractId": SDD_MATRIX_ID,
            "track": track,
            "operationId": opid,
            "operation": {"method": "post", "path": path},
            "fixtureSelection": {"fixtureId": fixture_id, "track": track, "status": "candidate_needs_review", "authority": "external-selection-plan-v1 fixtureId, not request fields"},
            "requestBody": {},
            "sddConstantEmptyObject": True,
            "officialCampaign": False,
            "sourcePolicy": {"noOracle": True, "noRuntimeResults": True, "requestBodyPreservedEmpty": True, "externalFixtureSelectionOnly": True},
            "contractPin": registry_source.pin,
        })
    return {"kind": "t3-sdd-external-selection-v1-amended-recipes", "status": "candidate_static_only", "officialCampaign": False, "recipes": recipes}


def build_external_selection_plan(p3: Path = P3) -> dict[str, Any]:
    matrix_path = p3 / "applicability-mapping-v3" / "applicability_matrix.json"
    recipes_path = p3 / "t3-mapping-recipes-v1" / "recipes.json"
    fixture_path = p3 / "fixture-materialization-v2" / "package" / "manifest.json"
    model_path = p3 / "reference-executable-v4" / "model.json"
    openapi_path = p3.parent / "P2a" / "openapi-carddemo-stage6r3.json"
    matrix = load_json(matrix_path)
    fixtures = load_json(fixture_path)
    model = load_json(model_path)
    registry_source = resolve_contract_source(p3, SDD_REGISTRY_ID)
    openapi = registry_source.openapi
    schema_empty = {track: sdd_request_schema_is_empty(openapi, f"/{track}") for track in ("posting", "interest", "reporting")}
    resource_summary = package_resource_summary(fixtures)
    cells = []
    blocked = []
    for obl in matrix.get("obligations", []):
        oid = str(obl.get("obligationId"))
        sdd = next((c for c in obl.get("contractMappings", []) if c.get("contractId") == SDD_MATRIX_ID), None)
        if not sdd:
            continue
        track = str(obl.get("track"))
        op = sdd.get("operation") or {}
        source = {
            "obligationId": oid,
            "title": obl.get("title"),
            "sourceAnchors": obl.get("source_anchors", []),
            "referenceTransitions": ((obl.get("referenceWitness") or {}).get("transitionRefs") or []),
        }
        if oid in SELECTABLE_OBLIGATIONS:
            cfg = SELECTABLE_OBLIGATIONS[oid]
            cells.append({
                "cellId": f"{oid}::{SDD_REGISTRY_ID}::{op.get('operationId')}",
                "matrixCellId": f"{oid}::{SDD_MATRIX_ID}::{op.get('operationId')}",
                "contractId": SDD_REGISTRY_ID,
                "matrixContractId": SDD_MATRIX_ID,
                "operationId": op.get("operationId"),
                "operation": {"method": op.get("method"), "path": op.get("path")},
                "track": track,
                "fixtureId": cfg["fixtureId"],
                "requestBody": {},
                "requestBodyPreservedEmpty": schema_empty.get(track) is True,
                "classification": "externally_selectable_sdd_empty_request",
                "status": "candidate_static_only",
                "source": source,
                "resourceAuthority": resource_authority_for(track, fixtures),
                "guardBasis": cfg["guardBasis"],
                "resourceChecks": cfg["resourceChecks"],
                "noExpected": True,
            })
        else:
            blocked.append({
                "obligationId": oid,
                "contractId": SDD_REGISTRY_ID,
                "operationId": op.get("operationId"),
                "track": track,
                "previousApplicabilityStatus": sdd.get("applicabilityStatus"),
                "reason": EXPLICIT_BLOCKERS.get(oid, "no concrete external fixture/guard authority identified"),
                "source": source,
                "eligible": False,
            })
    return {
        "kind": "t3-sdd-external-selection-v1-plan",
        "status": "candidate_static_only",
        "officialCampaign": False,
        "officialSuiteGenerated": False,
        "runtimeExecuted": False,
        "policy": {
            "sddRequestBodiesRemainEmpty": True,
            "selectionIsExternalByFixtureId": True,
            "noExpectedOutputsDefined": True,
            "noBusinessExecution": True,
            "doesNotUnlockParent44": True,
        },
        "inputs": {"matrix": pin(matrix_path), "recipes": pin(recipes_path), "fixtures": pin(fixture_path), "model": pin(model_path), "openapi": pin(openapi_path), "adapter": pin(ADAPTER_SRC / "t3_campaign_adapter.py")},
        "contract": {"matrixContractId": SDD_MATRIX_ID, "registryContractId": SDD_REGISTRY_ID, "schemaEmptyRequestByTrack": schema_empty, "pin": registry_source.pin},
        "fixturesByTrack": resource_summary,
        "selectedCells": cells,
        "blockedCells": blocked,
        "summary": {"selected": len(cells), "blocked": len(blocked), "totalSddObligations": len(cells) + len(blocked), "byTrack": dict(Counter(c["track"] for c in cells))},
    }


def write_versioned_copies(plan: dict[str, Any], p3: Path = P3, out: Path = OUT) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    matrix_path = p3 / "applicability-mapping-v3" / "applicability_matrix.json"
    recipes_path = p3 / "t3-mapping-recipes-v1" / "recipes.json"
    fixture_path = p3 / "fixture-materialization-v2" / "package" / "manifest.json"
    matrix = load_json(matrix_path)
    recipes = load_json(recipes_path)
    registry_source = resolve_contract_source(p3, SDD_REGISTRY_ID)
    amended_recipes = copy.deepcopy(recipes)
    amended_recipes.setdefault("externalSelectionAmendments", []).append({"path": "external-selection-plan.json", "policy": "adds fixtureSelection to SDD empty-body recipes only"})
    existing = [r for r in amended_recipes.get("recipes", []) if r.get("contractId") != SDD_MATRIX_ID]
    amended_recipes["recipes"] = existing + amended_sdd_recipes_from_plan(plan, registry_source)["recipes"]
    selected_by_matrix_cell = {c["matrixCellId"]: c for c in plan["selectedCells"]}
    changed = []
    for obl in matrix.get("obligations", []):
        for cell in obl.get("contractMappings", []):
            if cell.get("contractId") != SDD_MATRIX_ID:
                continue
            op = cell.get("operation") or {}
            cid = f"{obl.get('obligationId')}::{SDD_MATRIX_ID}::{op.get('operationId')}"
            if cid in selected_by_matrix_cell:
                before = cell.get("applicabilityStatus")
                if before in {"not_mapped", "precondition_indeterminate"}:
                    cell["applicabilityStatus"] = "conditioned_on_external_fixture"
                dims = cell.setdefault("applicabilityDimensions", {})
                dims["external_fixture_selection_admissible"] = True
                dims["request_body_selector_admissible"] = False
                dims["generative_admissible"] = False
                cell["externalSelectionV1"] = {
                    "fixtureId": selected_by_matrix_cell[cid]["fixtureId"],
                    "requestBody": {},
                    "reason": "fixtureId selects data/precondition externally; SDD public request remains {}",
                    "guardBasis": selected_by_matrix_cell[cid]["guardBasis"],
                }
                changed.append({"matrixCellId": cid, "before": before, "after": cell.get("applicabilityStatus")})
    (out / "applicability_matrix.sdd-external-selection-v1.json").write_bytes(json_bytes(matrix))
    (out / "recipes.sdd-external-selection-v1.json").write_bytes(json_bytes(amended_recipes))
    (out / "external-selection-plan.json").write_bytes(json_bytes(plan))
    bytes_report = verify_current_fixture_bytes(fixture_path)
    (out / "fixture-byte-structural-check.json").write_bytes(json_bytes(bytes_report))
    return {"changedMatrixCells": changed, "outputs": {"matrix": pin(out / "applicability_matrix.sdd-external-selection-v1.json"), "recipes": pin(out / "recipes.sdd-external-selection-v1.json"), "plan": pin(out / "external-selection-plan.json"), "fixtureByteCheck": pin(out / "fixture-byte-structural-check.json")}}


def local_sdd_id_migration_proof(p3: Path, out: Path) -> dict[str, Any]:
    source = resolve_contract_source(p3, SDD_REGISTRY_ID)
    artifact = {
        "kind": "t3-sdd-external-selection-v1-local-sdd-id-migration",
        "version": "sdd-external-selection-v1-id-migration",
        "policy": "versioned adapter-local ID migration for copied inputs only; no upstream alias, no source edit",
        "fromContractId": SDD_MATRIX_ID,
        "toContractId": SDD_REGISTRY_ID,
        "operationIdentity": {
            "identical": True,
            "operations": [
                {"operationId": "posting", "method": "POST", "path": "/posting"},
                {"operationId": "interest", "method": "POST", "path": "/interest"},
                {"operationId": "reporting", "method": "POST", "path": "/reporting"},
            ],
        },
        "sourcePins": {"targetContract": source.pin},
        "officialCampaign": False,
    }
    path = out / "sdd-id-migration.external-selection-v1.json"
    path.write_bytes(json_bytes(artifact))
    artifact["migrationArtifactPin"] = pin(path)
    return artifact


def enrich_with_external_selection(plan: dict[str, Any], p3: Path = P3, out: Path = OUT) -> dict[str, Any]:
    matrix = load_json(out / "applicability_matrix.sdd-external-selection-v1.json")
    recipes = load_json(out / "recipes.sdd-external-selection-v1.json")
    enriched = build_enriched_plan(matrix, recipes)
    migration = local_sdd_id_migration_proof(p3, out)
    enriched = apply_sdd_id_migration(enriched, migration)
    selected: dict[str, dict[str, Any]] = {}
    for item in plan["selectedCells"]:
        selected[item["cellId"]] = item
        selected[item["matrixCellId"]] = item
    changed = 0
    denied = []
    for cell in enriched.get("cells", []):
        if cell.get("contractId") != SDD_REGISTRY_ID:
            continue
        cell_key = str(cell.get("cellId"))
        if cell_key in selected:
            ext = selected[cell_key]
            cell["classification"] = "recipe_available_unexercised"
            cell["status"] = "candidate"
            cell["executableEligible"] = True
            cell["fixtureId"] = ext["fixtureId"]
            cell["selectorObjects"] = {}
            cell["sddConstantEmptyObject"] = True
            cell["reason"] = "external fixture selection authority; public SDD request body remains {}"
            cell["externalSelectionAuthority"] = ext
            changed += 1
        elif cell.get("contractId") == SDD_REGISTRY_ID:
            denied.append({"cellId": cell.get("cellId"), "classification": cell.get("classification"), "status": cell.get("status"), "executableEligible": cell.get("executableEligible"), "reason": cell.get("reason")})
    enriched.setdefault("adapterLocalMigrations", []).append({"version": "sdd-external-selection-v1", "changedCells": changed, "authority": "external-selection-plan.json", "requestBodyPreservedEmpty": True})
    (out / "integrated-mapping.sdd-external-selection-v1.json").write_bytes(json_bytes(enriched))
    return {"enriched": enriched, "changedCells": changed, "deniedCells": denied, "migration": migration}


def static_adapter_check(enriched: dict[str, Any], p3: Path = P3, out: Path = OUT) -> dict[str, Any]:
    contract_source = resolve_contract_source(p3, SDD_REGISTRY_ID)
    suite, report = build_t3_suite(
        SDD_REGISTRY_ID,
        p3 / "reference-executable-v4" / "model.json",
        enriched,
        p3 / "fixture-materialization-v2" / "package" / "manifest.json",
        contract_source,
        capabilities=["CBTRN02C_POSTTRAN", "CBACT04C_INTCALC", "CBTRN03C_TRANREPT"],
        max_depth=6,
        max_paths_per_capability=12,
    )
    cases = []
    for case in suite.cases:
        body = json.loads(base64.b64decode(case.request.body_b64).decode("utf-8"))
        cases.append({"caseId": case.case_id, "path": case.request.path, "body": body, "fixtureId": case.resource_package_id, "cellRef": case.parameters.get("cellRef"), "transitionId": case.parameters.get("transitionId")})
    bad_bodies = [c for c in cases if c["body"] != {}]
    result = {
        "kind": "t3-sdd-external-selection-v1-adapter-static-check",
        "status": "PASS" if not bad_bodies and cases else "FAIL",
        "officialCampaign": False,
        "officialSuiteGenerated": False,
        "runtimeExecuted": False,
        "adapterReportSummary": {k: report.get(k) for k in ("acceptedCount", "blockedCount", "inconclusiveTransitionCount", "status")},
        "caseCount": len(cases),
        "cases": cases,
        "badBodies": bad_bodies,
        "blockedSample": report.get("blocked", [])[:20],
    }
    (out / "adapter-static-check.json").write_bytes(json_bytes(result))
    return result


def static_fairness_check(enriched: dict[str, Any], p3: Path = P3, out: Path = OUT) -> dict[str, Any]:
    cells = enriched.get("cells", [])
    sdd = [c for c in cells if c.get("contractId") == SDD_REGISTRY_ID]
    nonsdd = [c for c in cells if c.get("contractId") != SDD_REGISTRY_ID]
    sdd_ok = [c for c in sdd if c.get("executableEligible")]
    nonsdd_ok = [c for c in nonsdd if c.get("executableEligible")]
    result = {
        "kind": "t3-sdd-external-selection-v1-static-fairness-check",
        "status": "PASS",
        "officialCampaign": False,
        "runtimeExecuted": False,
        "checks": {
            "sddUsesOnlyEmptyRequestBodies": all(c.get("selectorObjects") == {} and c.get("sddConstantEmptyObject") is True for c in sdd_ok),
            "nonSddUnchangedByExternalSelection": all("externalSelectionAuthority" not in c for c in nonsdd),
            "noBlockedSddMadeEligibleWithoutAuthority": all((not c.get("executableEligible")) or isinstance(c.get("externalSelectionAuthority"), dict) for c in sdd),
        },
        "counts": {"sddEligible": len(sdd_ok), "nonSddEligible": len(nonsdd_ok), "sddBlocked": len(sdd) - len(sdd_ok), "nonSddBlocked": len(nonsdd) - len(nonsdd_ok)},
    }
    if not all(result["checks"].values()):
        result["status"] = "FAIL"
    (out / "static-fairness-check.json").write_bytes(json_bytes(result))
    return result


def run_all(p3: Path = P3, out: Path = OUT) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    plan = build_external_selection_plan(p3)
    copies = write_versioned_copies(plan, p3, out)
    enriched_info = enrich_with_external_selection(plan, p3, out)
    adapter_check = static_adapter_check(enriched_info["enriched"], p3, out)
    fairness = static_fairness_check(enriched_info["enriched"], p3, out)
    report = {
        "kind": "t3-sdd-external-selection-v1-report",
        "status": "candidate_static_only" if adapter_check["status"] == "PASS" and fairness["status"] == "PASS" else "needs_correction",
        "officialCampaign": False,
        "officialSuiteGenerated": False,
        "runtimeExecuted": False,
        "summary": {"selectedCells": plan["summary"]["selected"], "blockedCells": plan["summary"]["blocked"], "adapterCases": adapter_check["caseCount"], "changedMatrixCells": len(copies["changedMatrixCells"])},
        "outputs": {**copies["outputs"], "sddIdMigration": pin(out / "sdd-id-migration.external-selection-v1.json")},
        "adapterStaticCheck": pin(out / "adapter-static-check.json"),
        "staticFairnessCheck": pin(out / "static-fairness-check.json"),
        "blockersRemaining": plan["blockedCells"],
    }
    (out / "REPORT.json").write_bytes(json_bytes(report))
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--p3", default=str(P3))
    ap.add_argument("--out", default=str(OUT))
    ns = ap.parse_args(argv)
    report = run_all(Path(ns.p3), Path(ns.out))
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["status"] == "candidate_static_only" else 1


if __name__ == "__main__":
    raise SystemExit(main())

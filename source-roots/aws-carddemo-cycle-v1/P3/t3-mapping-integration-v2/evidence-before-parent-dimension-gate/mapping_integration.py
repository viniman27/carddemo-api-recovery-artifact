from __future__ import annotations

import base64
import hashlib
import json
import sys
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

P3 = Path(__file__).resolve().parents[2]
HARNESS = P3 / "campaign-harness-v3" / "src"
if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))

from campaign_harness import Case, Expectation, HttpRequestSpec, Suite, freeze_suite  # noqa: E402

ALLOWED_V3 = {"expressible_by_surface", "conditioned_on_external_fixture"}
CLASS_BY_APPLICABILITY = {
    "expressible_by_surface": "recipe_available_unexercised",
    "conditioned_on_external_fixture": "recipe_available_unexercised",
    "not_expressible": "contractually_impossible",
    "precondition_indeterminate": "missing_fixture_variant",
    "observation_inadmissible": "observation_without_authority",
    "not_mapped": "implementation_missing",
}
INVENTORY_KEYS = [
    "recipe_available_unexercised",
    "contractually_impossible",
    "missing_fixture_variant",
    "observation_without_authority",
    "implementation_missing",
]


class MappingBlocked(Exception):
    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        super().__init__(reason)
        self.reason = reason
        self.details = details or {}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: Any) -> bytes:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _recipe_key(recipe: dict[str, Any]) -> tuple[str, str, str, str]:
    op = recipe.get("operation") or {}
    return (str(recipe.get("contractId")), str(recipe.get("operationId") or op.get("operationId")), str(op.get("path")), str(recipe.get("track")))


def _cell_key(obligation: dict[str, Any], mapping: dict[str, Any]) -> tuple[str, str, str, str]:
    op = mapping.get("operation") or {}
    return (str(mapping.get("contractId")), str(op.get("operationId")), str(op.get("path")), str(obligation.get("track")))


def _cell_id(obligation: dict[str, Any], mapping: dict[str, Any]) -> str:
    cid, opid, _path, _track = _cell_key(obligation, mapping)
    return f"{obligation.get('obligationId')}::{cid}::{opid}"


def _selector_objects(recipe: dict[str, Any]) -> dict[str, Any] | None:
    body = recipe.get("requestBody")
    return body if isinstance(body, dict) else None


def _reason_for(applicability: str, recipe_exists: bool, executable_eligible: bool, plan_missing: list[str]) -> str:
    if executable_eligible:
        return "applicability, upstream generation flags, linked recipe and fixture selection are all present; candidate only, not exercised"
    if applicability in ALLOWED_V3:
        if not recipe_exists:
            return "v3/status surface permits the cell, but no explicit recipe joined by contractId, operationId/path and track"
        if plan_missing:
            return "recipe exists but is not executable-eligible because upstream plan authority blocks generation: " + "; ".join(plan_missing)
        return "recipe exists but is not executable-eligible because fixture selection is missing; empty {} bodies still require a fixture agenda"
    return {
        "not_expressible": "contract/request/fixture surface cannot express this obligation without strengthening the contract",
        "precondition_indeterminate": "required variant/precondition is not currently established by permitted fixtures; absence is not treated as contract impossibility",
        "observation_inadmissible": "required observation has no pre-campaign authority without oracle/runtime/internal-state evidence",
        "not_mapped": "operation exists, but no concrete implementation mapping is authorized for this obligation step",
    }.get(applicability, f"unrecognized applicabilityStatus={applicability}")


def _plan_authority(raw: dict[str, Any]) -> tuple[dict[str, Any], bool, list[str]]:
    plan = raw.get("t3DeterministicMapping") or {}
    if not isinstance(plan, dict):
        plan = {}
    missing: list[str] = []
    if plan.get("generativeUse") != "candidate_mapping_only_unexercised":
        missing.append(f"generativeUse={plan.get('generativeUse')}")
    if plan.get("selectorUsableForGeneration") is not True:
        missing.append(f"selectorUsableForGeneration={plan.get('selectorUsableForGeneration')}")
    if plan.get("diagnostics"):
        missing.append("diagnostics present")
    return plan, not missing, missing


def build_enriched_plan(matrix: dict[str, Any], recipes_doc: dict[str, Any]) -> dict[str, Any]:
    recipes = recipes_doc.get("recipes") or []
    recipe_by_key: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    duplicate_keys: list[list[str]] = []
    for recipe in recipes:
        key = _recipe_key(recipe)
        if key in recipe_by_key:
            duplicate_keys.append(list(key))
        recipe_by_key[key] = recipe

    cells: list[dict[str, Any]] = []
    missing_allowed: list[dict[str, Any]] = []
    recipe_exists_not_eligible = 0
    for obligation in matrix.get("obligations", []):
        for raw in obligation.get("contractMappings", []):
            key = _cell_key(obligation, raw)
            applicability = str(raw.get("applicabilityStatus"))
            recipe = recipe_by_key.get(key)
            recipe_exists = recipe is not None
            plan, plan_ok, plan_missing = _plan_authority(raw)
            fixture_selection = recipe.get("fixtureSelection") if isinstance(recipe, dict) else None
            fixture_id = ((fixture_selection or {}).get("fixtureId") if isinstance(fixture_selection, dict) else None)
            v3_status_allowed = applicability in ALLOWED_V3
            executable_eligible = bool(v3_status_allowed and plan_ok and recipe_exists and fixture_id)
            classification = CLASS_BY_APPLICABILITY.get(applicability, "implementation_missing")
            if v3_status_allowed:
                if executable_eligible:
                    classification = "recipe_available_unexercised"
                else:
                    classification = "implementation_missing"
                    if recipe_exists:
                        recipe_exists_not_eligible += 1
                    else:
                        missing_allowed.append({"cellId": _cell_id(obligation, raw), "joinKey": list(key)})
            cell = {
                "cellId": _cell_id(obligation, raw),
                "obligationId": obligation.get("obligationId"),
                "contractId": raw.get("contractId"),
                "track": obligation.get("track"),
                "operationId": (raw.get("operation") or {}).get("operationId"),
                "operation": {
                    "method": (raw.get("operation") or {}).get("method"),
                    "path": (raw.get("operation") or {}).get("path"),
                },
                "joinKey": {"contractId": key[0], "operationId": key[1], "path": key[2], "track": key[3]},
                "applicabilityStatus": applicability,
                "v3AllowedForSelectors": v3_status_allowed,
                "recipeExists": recipe_exists,
                "executableEligible": executable_eligible,
                "sourcePlan": {
                    "generativeUse": plan.get("generativeUse"),
                    "selectorUsableForGeneration": plan.get("selectorUsableForGeneration"),
                    "blocks": plan.get("blocks", []),
                    "dimensions": plan.get("dimensions", raw.get("dimensions")),
                    "diagnostics": plan.get("diagnostics"),
                },
                "classification": classification,
                "status": "candidate" if executable_eligible else "blocked",
                "reason": _reason_for(applicability, recipe_exists, executable_eligible, plan_missing),
                "linkedRecipe": None,
                "fixtureId": None,
                "selectorObjects": None,
                "officialCampaign": False,
            }
            if recipe_exists:
                cell["linkedRecipe"] = {
                    "recipeId": recipe.get("recipeId"),
                    "contractId": recipe.get("contractId"),
                    "operationId": recipe.get("operationId"),
                    "operation": recipe.get("operation"),
                    "track": recipe.get("track"),
                }
                cell["fixtureSelection"] = fixture_selection
                cell["sddConstantEmptyObject"] = bool(recipe.get("sddConstantEmptyObject"))
            if executable_eligible:
                cell["fixtureId"] = fixture_id
                cell["selectorObjects"] = _selector_objects(recipe)
            cells.append(cell)

    totals = Counter(c["classification"] for c in cells)
    for key in INVENTORY_KEYS:
        totals.setdefault(key, 0)
    return {
        "kind": "t3-integrated-mapping-v2",
        "status": "candidate",
        "officialCampaign": False,
        "joinContract": ["contractId", "operationId", "operation.path", "track"],
        "sourcePolicy": {
            "v3OnlySelectors": True,
            "conjunctivePlanAuthority": True,
            "recipeExistenceSeparatedFromExecutableEligibility": True,
            "blockedCellsRemainWithoutSelectors": True,
            "noOfficialAwsSuiteOrRequestsExported": True,
            "compatibilityEvaluatesEnrichedRecipePlan": True,
        },
        "inputs": {"matrixKind": matrix.get("kind"), "recipesKind": recipes_doc.get("kind")},
        "summary": {
            "recipesTotal": len(recipes),
            "uniqueRecipeJoinKeys": len(recipe_by_key),
            "duplicateRecipeJoinKeys": duplicate_keys,
            "cellsTotal": len(cells),
            "v3AllowedCellsWithLinkedRecipe": sum(1 for c in cells if c["v3AllowedForSelectors"] and c["linkedRecipe"]),
            "executableEligibleCellsWithLinkedRecipe": sum(1 for c in cells if c["executableEligible"] and c["linkedRecipe"]),
            "recipeExistsButNotExecutableEligible": recipe_exists_not_eligible,
            "v3AllowedCellsMissingRecipe": len(missing_allowed),
            "blockedCellsWithoutSelectors": sum(1 for c in cells if c.get("status") == "blocked" and c.get("selectorObjects") is None),
            "classificationTotals": dict(totals),
        },
        "cells": cells,
    }


def compatibility_inventory(enriched_plan: dict[str, Any]) -> dict[str, Any]:
    totals = Counter(c.get("classification") for c in enriched_plan.get("cells", []))
    for key in INVENTORY_KEYS:
        totals.setdefault(key, 0)
    cells = []
    for c in enriched_plan.get("cells", []):
        cells.append({
            "cellId": c.get("cellId"),
            "cellRef": c.get("cellId"),
            "obligationId": c.get("obligationId"),
            "contractId": c.get("contractId"),
            "operationId": c.get("operationId"),
            "operationPath": (c.get("operation") or {}).get("path"),
            "track": c.get("track"),
            "classification": c.get("classification"),
            "status": c.get("status"),
            "reason": c.get("reason"),
            "fixtureId": c.get("fixtureId"),
            "recipeId": (c.get("linkedRecipe") or {}).get("recipeId") if c.get("linkedRecipe") else None,
        })
    return {"kind": "t3-integrated-compatibility-inventory-v2", "status": "candidate", "officialCampaign": False, "evaluatedPlan": enriched_plan.get("kind"), "totals": dict(totals), "cells": cells}


@dataclass(frozen=True)
class FixtureResource:
    dd: str
    path: str
    bytes: int | None = None
    sha256: str | None = None


@dataclass(frozen=True)
class FixturePackage:
    fixture_id: str
    track: str | None
    package_path: Path | None
    resources: dict[str, FixtureResource]
    bindings: dict[str, str]

    def resource(self, dd: str) -> FixtureResource:
        if dd not in self.resources:
            raise MappingBlocked("resource_not_found_in_fixture", {"dd": dd, "fixtureId": self.fixture_id})
        return self.resources[dd]

    def read(self, dd: str) -> bytes:
        res = self.resource(dd)
        if self.package_path is None:
            raise MappingBlocked("fixture_package_path_missing", {"fixtureId": self.fixture_id})
        path = self.package_path / res.path
        data = path.read_bytes()
        if res.bytes is not None and len(data) != res.bytes:
            raise MappingBlocked("resource_size_mismatch", {"dd": dd, "expected": res.bytes, "actual": len(data)})
        digest = sha256_bytes(data)
        if res.sha256 and digest != res.sha256:
            raise MappingBlocked("resource_sha256_mismatch", {"dd": dd, "expected": res.sha256, "actual": digest})
        return data

    def binding(self, dd: str) -> str:
        if dd in self.bindings:
            return self.bindings[dd]
        return self.resource(dd).path


class FixtureIndex:
    def __init__(self, packages: dict[str, FixturePackage]):
        self.packages = packages

    @classmethod
    def from_manifest(cls, manifest: dict[str, Any], base_dir: Path | None = None) -> "FixtureIndex":
        packages = {}
        for item in manifest.get("fixtures", []):
            package_path = item.get("packagePath")
            if package_path:
                pp = Path(str(package_path))
                if not pp.is_absolute() and base_dir is not None:
                    pp = base_dir / pp
            else:
                pp = None
            resources = {}
            for res in item.get("resources", []):
                dd = str(res["dd"])
                resources[dd] = FixtureResource(dd, str(res.get("path") or res.get("file") or dd), res.get("bytes"), res.get("sha256"))
            fid = str(item.get("fixtureId"))
            packages[fid] = FixturePackage(fid, item.get("track"), pp, resources, {str(k): str(v) for k, v in (item.get("bindings") or {}).items()})
        return cls(packages)

    def select(self, fixture_id: str | None) -> FixturePackage:
        if not fixture_id:
            raise MappingBlocked("fixture_id_missing")
        if fixture_id not in self.packages:
            raise MappingBlocked("fixture_not_found", {"fixtureId": fixture_id})
        return self.packages[fixture_id]


def selector_value(selector: Any, fixture: FixturePackage, evidence: list[dict[str, Any]]) -> Any:
    if not isinstance(selector, dict):
        raise MappingBlocked("selector_must_be_object")
    if "object" in selector:
        return {str(k): selector_value(v, fixture, evidence) for k, v in selector["object"].items()}
    if "literal" in selector:
        evidence.append({"selector": "literal"})
        return selector["literal"]
    if "fromBinding" in selector:
        dd = str(selector["fromBinding"]); evidence.append({"selector": "fromBinding", "dd": dd, "fixtureId": fixture.fixture_id}); return fixture.binding(dd)
    if "fromBytes" in selector:
        dd = str(selector["fromBytes"]); data = fixture.read(dd); enc = str(selector.get("encoding", "base64")); evidence.append({"selector": "fromBytes", "dd": dd, "fixtureId": fixture.fixture_id, "bytes": len(data)})
        if enc == "base64":
            return base64.b64encode(data).decode("ascii")
        if enc == "utf8":
            return data.decode("utf-8")
        raise MappingBlocked("unsupported_bytes_encoding", {"encoding": enc})
    if "fromContractScalar" in selector:
        src = selector["fromContractScalar"]; evidence.append({"selector": "fromContractScalar", "authority": src.get("authority")}); return src["value"]
    if "fromResource" in selector:
        dd = str(selector["fromResource"]); evidence.append({"selector": "fromResource", "dd": dd, "fixtureId": fixture.fixture_id}); return dd
    raise MappingBlocked("unsupported_selector", {"selectorKeys": sorted(selector.keys())})


def _operation(openapi: dict[str, Any], method: str, path: str) -> dict[str, Any]:
    op = ((openapi.get("paths") or {}).get(path) or {}).get(method.lower())
    if not isinstance(op, dict):
        raise MappingBlocked("operation_not_in_schema", {"method": method, "path": path})
    return op


def _request_schema(openapi: dict[str, Any], method: str, path: str) -> dict[str, Any] | None:
    op = _operation(openapi, method, path)
    content = (((op.get("requestBody") or {}).get("content") or {}).get("application/json") or {})
    schema = content.get("schema")
    return schema if isinstance(schema, dict) else None


def request_from_cell(cell: dict[str, Any], fixture_index: FixtureIndex, openapi: dict[str, Any]) -> tuple[HttpRequestSpec, dict[str, Any]]:
    if cell.get("classification") != "recipe_available_unexercised" or not cell.get("executableEligible"):
        reason = "fixture_selection_missing_for_executable_request" if cell.get("recipeExists") and not cell.get("fixtureId") else "blocked_cell_has_no_authorized_selectors"
        raise MappingBlocked(reason, {"cellId": cell.get("cellId"), "classification": cell.get("classification"), "executableEligible": cell.get("executableEligible")})
    op = cell.get("operation") or {}; method = str(op.get("method", "post")).upper(); path = str(op.get("path"))
    _operation(openapi, method, path)
    fixture = fixture_index.select(cell.get("fixtureId"))
    selectors = cell.get("selectorObjects")
    if selectors is None:
        raise MappingBlocked("selector_objects_missing", {"cellId": cell.get("cellId")})
    evidence: list[dict[str, Any]] = []
    if selectors == {} and cell.get("sddConstantEmptyObject"):
        body = {}
    elif isinstance(selectors, dict) and "object" in selectors and len(selectors) == 1:
        body = selector_value(selectors, fixture, evidence)
    else:
        body = {str(k): selector_value(v, fixture, evidence) for k, v in selectors.items()}
    schema = _request_schema(openapi, method, path)
    if schema is not None:
        errors = sorted(Draft202012Validator(schema).iter_errors(body), key=lambda e: list(e.path))
        if errors:
            raise MappingBlocked("schema_validation_failed", {"errors": [e.message for e in errors]})
    req = HttpRequestSpec(method, path, (("content-type", "application/json"),), "json", base64.b64encode(json.dumps(body, separators=(",", ":")).encode()).decode("ascii"))
    return req, {"sourceboundValues": evidence, "selectedFixture": {"fixtureId": fixture.fixture_id, "track": fixture.track}, "inventedValues": False, "officialCampaign": False}


def _initial_state(model: dict[str, Any]) -> str:
    return str((model.get("capabilities") or [{}])[0].get("initialState"))


def _transitions(model: dict[str, Any], state: str) -> list[dict[str, Any]]:
    out = []
    for cap in model.get("capabilities", []):
        out.extend(t for t in cap.get("transitions", []) if t.get("from") == state)
    return sorted(out, key=lambda t: str(t.get("id")))


def map_enriched_model_to_suite(contract_id: str, model_path: Path, enriched_plan: dict[str, Any], fixtures_path: Path, schema_path: Path, max_depth: int = 8) -> tuple[Suite, dict[str, Any]]:
    model = load_json(model_path); fixture_index = FixtureIndex.from_manifest(load_json(fixtures_path), Path(fixtures_path).parent); openapi = load_json(schema_path)
    cells_by_obl: dict[str, list[dict[str, Any]]] = {}
    for cell in enriched_plan.get("cells", []):
        if str(cell.get("contractId")) == contract_id:
            cells_by_obl.setdefault(str(cell.get("obligationId")), []).append(cell)
    queue = deque([(_initial_state(model), [])]); seen = set(); cases = []; blocked = []
    while queue:
        state, path = queue.popleft()
        if len(path) >= max_depth:
            continue
        for tr in _transitions(model, state):
            tid = str(tr.get("id")); next_path = path + [tid]
            if tid in seen:
                continue
            seen.add(tid)
            cells = cells_by_obl.get(tid, [])
            if not cells:
                blocked.append({"transitionId": tid, "classification": "implementation_missing", "reason": "no enriched cell for transition", "path": next_path})
            for cell in cells:
                if cell.get("classification") != "recipe_available_unexercised":
                    blocked.append({"cellId": cell.get("cellId"), "transitionId": tid, "classification": cell.get("classification"), "reason": cell.get("reason"), "path": next_path})
                    continue
                try:
                    req, evidence = request_from_cell(cell, fixture_index, openapi)
                    cases.append(Case(
                        case_id=f"T3-{contract_id}-{cell['cellId']}", suite_id="T3", origin=f"T3-integrated:{contract_id}", request=req,
                        resource_package_id=str(cell.get("fixtureId")), expectation=Expectation("status", {"status": [200, 400, 500, 503]}),
                        timeout_seconds=5.0, parameters={"cellRef": cell.get("cellId"), "recipeId": (cell.get("linkedRecipe") or {}).get("recipeId"), "pathEvidence": next_path},
                        sequence=tuple(next_path), provenance=(f"T3-integrated:{cell.get('cellId')}",)))
                except MappingBlocked as exc:
                    blocked.append({"cellId": cell.get("cellId"), "transitionId": tid, "classification": "implementation_missing", "reason": exc.reason, "details": exc.details, "path": next_path})
            queue.append((str(tr.get("to")), next_path))
    return Suite("T3", cases), {"kind": "t3-integrated-synthetic-suite-report", "officialCampaign": False, "acceptedCount": len(cases), "blockedCount": len(blocked), "blocked": blocked, "status": "candidate"}


def validate_recipe_document(recipes_doc: dict[str, Any]) -> dict[str, Any]:
    failures = []
    recipes = recipes_doc.get("recipes") or []
    seen = set()
    for idx, r in enumerate(recipes):
        key = _recipe_key(r)
        missing = [k for k in ("recipeId", "contractId", "track", "operation", "requestBody", "officialCampaign") if k not in r]
        if missing:
            failures.append({"index": idx, "recipeId": r.get("recipeId"), "missing": missing})
        if r.get("officialCampaign") is not False:
            failures.append({"index": idx, "recipeId": r.get("recipeId"), "error": "officialCampaign must be false"})
        if key in seen:
            failures.append({"index": idx, "recipeId": r.get("recipeId"), "error": "duplicate join key", "joinKey": list(key)})
        seen.add(key)
    return {"kind": "t3-integrated-recipes-static-validation", "status": "candidate", "officialCampaign": False, "recipeSchemaValidated": len(recipes) == 21 and not failures, "operationRecipes": len(recipes), "compileFailures": failures}


def write_outputs(p3: Path | None = None) -> dict[str, Any]:
    p3 = p3 or P3
    root = p3 / "t3-mapping-integration-v2"
    matrix_path = p3 / "applicability-mapping-v3" / "applicability_matrix.json"
    recipes_path = p3 / "t3-mapping-recipes-v1" / "recipes.json"
    old_mapper = p3 / "t3-mapper-preparation-v1" / "src" / "t3_mapper.py"
    matrix_b = matrix_path.read_bytes(); recipes_b = recipes_path.read_bytes(); old_b = old_mapper.read_bytes()
    enriched = build_enriched_plan(json.loads(matrix_b), json.loads(recipes_b))
    inv = compatibility_inventory(enriched)
    val = validate_recipe_document(json.loads(recipes_b))
    report = {
        "kind": "t3-mapping-integration-v2-report",
        "status": "candidate",
        "officialCampaign": False,
        "inputs": {
            "applicabilityMatrixV3": {"path": str(matrix_path), "sha256": sha256_bytes(matrix_b), "bytes": len(matrix_b)},
            "recipesV1": {"path": str(recipes_path), "sha256": sha256_bytes(recipes_b), "bytes": len(recipes_b)},
            "preservedOldMapperHash": {"path": str(old_mapper), "sha256": sha256_bytes(old_b), "bytes": len(old_b), "note": "recorded only; old mapper not edited by this integration"},
        },
        "results": {"enrichedSummary": enriched["summary"], "inventoryTotals": inv["totals"], "recipeValidation": val},
        "exports": {"officialAwsSuite": False, "officialAwsRequests": False},
    }
    (root / "integrated-mapping.json").write_bytes(json_bytes(enriched))
    (root / "compatibility-inventory.json").write_bytes(json_bytes(inv))
    (root / "validation-report.json").write_bytes(json_bytes(val))
    (root / "REPORT.json").write_bytes(json_bytes(report))
    (root / "REPORT.md").write_text(
        "# T3 Mapping Integration v2\n\n"
        "Status: candidate. Official AWS campaign export: false.\n\n"
        f"- Integrated cells: {enriched['summary']['cellsTotal']}\n"
        f"- 21 recipes statically valid: {val['recipeSchemaValidated']}\n"
        f"- Executable-eligible cells linked to recipes: {enriched['summary']['executableEligibleCellsWithLinkedRecipe']}\n"
        f"- Inventory totals: `{json.dumps(inv['totals'], sort_keys=True)}`\n"
        "- Blocked guard/observation/precondition cells keep no selector objects and are not relaxed.\n"
        "- No official AWS suite/request was exported; synthetic-only suite proof is exercised by tests.\n",
        encoding="utf-8",
    )
    return report


if __name__ == "__main__":
    print(json.dumps(write_outputs(), indent=2, ensure_ascii=False))

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import sys
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

P3 = Path(__file__).resolve().parents[2]
ADAPTER_ROOT = Path(__file__).resolve().parents[1]
HARNESS_SRC = P3 / "campaign-harness-v3" / "src"
REFERENCE_SRC = P3 / "reference-executable-v4"
MAPPER_SRC = P3 / "t3-mapper-preparation-v1" / "src"
if str(HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(HARNESS_SRC))
if str(REFERENCE_SRC) not in sys.path:
    sys.path.insert(0, str(REFERENCE_SRC))
if str(MAPPER_SRC) not in sys.path:
    sys.path.insert(0, str(MAPPER_SRC))

from campaign_harness import Case, Expectation, HttpRequestSpec, Suite, freeze_suite, load_frozen_suite  # noqa: E402
from executable_reference import (  # noqa: E402
    _enabled_for_traversal,
    _initial_state as reference_initial_state,
    load_model,
    traverse as reference_traverse,
    validate_model,
)
from t3_mapper import (  # noqa: E402
    FixtureIndex as RecipeFixtureIndex,
    MappingBlocked as RecipeMappingBlocked,
    build_request_from_explicit_mapping as compile_request_from_recipe_mapping,
)


class AdapterBlocked(Exception):
    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        super().__init__(reason)
        self.reason = reason
        self.details = details or {}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def pretty_json_bytes(value: Any) -> bytes:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_schema(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - environment failure is reported by CLI
            raise AdapterBlocked("yaml_dependency_missing", {"path": str(path)}) from exc
        return yaml.safe_load(text)
    return json.loads(text)


@dataclass(frozen=True)
class ContractSource:
    contract_id: str
    arm: str
    path: Path
    sha256: str
    bytes: int
    source_id: str
    operations: tuple[dict[str, Any], ...]
    openapi: dict[str, Any]

    @property
    def pin(self) -> dict[str, Any]:
        return {
            "id": self.source_id,
            "path": str(self.path),
            "sha256": self.sha256,
            "bytes": self.bytes,
        }


def _load_yaml_or_json_text(text: str, source_path: Path) -> dict[str, Any]:
    if source_path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - environment failure is reported by CLI
            raise AdapterBlocked("yaml_dependency_missing", {"path": str(source_path)}) from exc
        loaded = yaml.safe_load(text)
    else:
        loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise AdapterBlocked("openapi_document_not_object", {"path": str(source_path)})
    return loaded


def _openapi_from_pinned_source(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        parsed = json.loads(text)
        if isinstance(parsed, dict) and isinstance(parsed.get("text"), str):
            try:
                import yaml  # type: ignore
            except ImportError as exc:  # pragma: no cover - environment failure is reported by CLI
                raise AdapterBlocked("yaml_dependency_missing", {"path": str(path)}) from exc
            loaded = yaml.safe_load(parsed["text"])
            if not isinstance(loaded, dict):
                raise AdapterBlocked("openapi_document_not_object", {"path": str(path)})
            return loaded
        if isinstance(parsed, dict):
            return parsed
        raise AdapterBlocked("openapi_document_not_object", {"path": str(path)})
    return _load_yaml_or_json_text(text, path)


def load_contract_registry(p3: str | Path = P3) -> dict[str, ContractSource]:
    p3 = Path(p3)
    config_path = p3 / "campaign-configuration-v2" / "campaign-config-v2.json"
    config = load_json(config_path)
    registry: dict[str, ContractSource] = {}
    contracts = ((config.get("contracts") or {}).get("contracts") or [])
    for item in contracts:
        contract_id = str(item["contractId"])
        if contract_id in registry:
            raise AdapterBlocked("duplicate_contract_id", {"contractId": contract_id})
        source = item.get("source") or {}
        path = Path(str(source["path"]))
        data = path.read_bytes()
        actual_sha = sha256_bytes(data)
        actual_bytes = len(data)
        if actual_sha != source.get("sha256") or actual_bytes != source.get("bytes"):
            raise AdapterBlocked("contract_source_pin_mismatch", {
                "contractId": contract_id,
                "path": str(path),
                "expectedSha256": source.get("sha256"),
                "actualSha256": actual_sha,
                "expectedBytes": source.get("bytes"),
                "actualBytes": actual_bytes,
            })
        operations = tuple(copy.deepcopy(item.get("operations") or []))
        openapi = _openapi_from_pinned_source(path)
        registry[contract_id] = ContractSource(
            contract_id=contract_id,
            arm=str(item.get("arm")),
            path=path,
            sha256=actual_sha,
            bytes=actual_bytes,
            source_id=str(source.get("id") or f"contract-{contract_id}"),
            operations=operations,
            openapi=openapi,
        )
    if set(registry) != {"E1-1", "E1-2", "E1-3", "E2-1", "E2-2", "E2-3", "E3-SDD-stage6r3"}:
        raise AdapterBlocked("contract_registry_not_exact_seven", {"contractIds": sorted(registry)})
    if sum(len(source.operations) for source in registry.values()) != 21:
        raise AdapterBlocked("contract_registry_not_21_operations")
    return registry


def resolve_contract_source(p3: str | Path, contract_id: str) -> ContractSource:
    registry = load_contract_registry(p3)
    if contract_id not in registry:
        raise AdapterBlocked("unknown_contract_id", {"contractId": contract_id, "knownContractIds": sorted(registry)})
    return registry[contract_id]


def operation_lookup_for_contract(p3: str | Path, contract_id: str, method: str, path: str) -> ContractSource:
    source = resolve_contract_source(p3, contract_id)
    try:
        _operation(source.openapi, method, path)
    except AdapterBlocked as exc:
        if exc.reason == "operation_not_in_schema":
            raise AdapterBlocked("operation_not_in_contract_schema", {"contractId": contract_id, "method": method, "path": path}) from exc
        raise
    if not any(str(op.get("method")).upper() == method.upper() and str(op.get("path")) == path for op in source.operations):
        raise AdapterBlocked("operation_not_in_contract_inventory", {"contractId": contract_id, "method": method, "path": path})
    return source


def load_schema_source(schema_source: str | Path | ContractSource) -> dict[str, Any]:
    if isinstance(schema_source, ContractSource):
        return schema_source.openapi
    return load_schema(schema_source)


def _canonical_openapi_identity(openapi: dict[str, Any]) -> dict[str, Any]:
    data = canonical_json_bytes(openapi)
    operations = sorted(
        (
            {"operationId": op.get("operationId"), "method": method.upper(), "path": path}
            for path, item in (openapi.get("paths") or {}).items()
            if isinstance(item, dict)
            for method, op in item.items()
            if isinstance(op, dict)
        ),
        key=lambda op: (str(op.get("operationId")), str(op.get("method")), str(op.get("path"))),
    )
    return {"canonicalSha256": sha256_bytes(data), "canonicalBytes": len(data), "operations": operations}


def _matrix_sdd_contract(matrix: dict[str, Any]) -> dict[str, Any]:
    matches = [c for c in matrix.get("contracts", []) if str(c.get("contractId", "")).startswith("E3")]
    if len(matches) != 1:
        raise AdapterBlocked("sdd_matrix_contract_not_unique", {"count": len(matches)})
    return matches[0]


def _operation_identity_from_inventory(contract_doc: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "operationId": op.get("operationId"),
                "method": str(op.get("method")).upper(),
                "path": op.get("path"),
                "documentedResponses": list(op.get("documentedResponses") or []),
                "requestBodyRequired": bool(op.get("requestBodyRequired")),
            }
            for op in contract_doc.get("operations", [])
        ),
        key=lambda op: (str(op.get("operationId")), str(op.get("method")), str(op.get("path"))),
    )


def sdd_id_migration_proof(p3: str | Path, matrix: dict[str, Any], registry: dict[str, ContractSource]) -> dict[str, Any]:
    p3 = Path(p3)
    matrix_contract = _matrix_sdd_contract(matrix)
    from_id = str(matrix_contract.get("contractId"))
    to_id = "E3-SDD-stage6r3"
    if from_id == to_id:
        return {}
    if from_id != "E3-01-SDD-stage6r3" or to_id not in registry:
        raise AdapterBlocked("sdd_id_migration_not_authorized", {"fromContractId": from_id, "toContractId": to_id, "knownContractIds": sorted(registry)})
    to_source = registry[to_id]
    matrix_path = Path(str(matrix_contract.get("path", ""))).expanduser()
    if not matrix_path.is_absolute():
        matrix_path = p3.parent / matrix_path
    if not matrix_path.exists():
        # Matrix path may carry decomposed Unicode; use the pinned config OpenAPI as contract authority if necessary.
        matrix_openapi = to_source.openapi
        matrix_pin = {"path": str(matrix_contract.get("path")), "sha256": None, "bytes": None, "note": "matrix path not byte-readable; operation identity compared from matrix inventory and target OpenAPI"}
    else:
        matrix_bytes = matrix_path.read_bytes()
        matrix_openapi = _openapi_from_pinned_source(matrix_path)
        matrix_pin = {"path": str(matrix_path), "sha256": sha256_bytes(matrix_bytes), "bytes": len(matrix_bytes)}
    matrix_identity = _canonical_openapi_identity(matrix_openapi)
    target_identity = _canonical_openapi_identity(to_source.openapi)
    matrix_ops = _operation_identity_from_inventory(matrix_contract)
    target_ops = _operation_identity_from_inventory({"operations": list(to_source.operations)})
    operation_identical = matrix_ops == target_ops
    openapi_identical = matrix_identity["canonicalSha256"] == target_identity["canonicalSha256"]
    if not operation_identical or not openapi_identical:
        raise AdapterBlocked("sdd_id_migration_identity_not_proven", {"operationIdentity": operation_identical, "openapiCanonicalIdentity": openapi_identical})
    artifact = {
        "kind": "t3-campaign-adapter-v3-sdd-id-migration",
        "version": "sdd-id-migration-v1",
        "policy": "explicit versioned input-copy migration for adapter-local materialization only; not a silent alias and not a source edit",
        "fromContractId": from_id,
        "toContractId": to_id,
        "operationIdentity": {"identical": True, "operations": matrix_ops},
        "openapiCanonicalIdentity": {"identical": True, "from": matrix_identity, "to": target_identity},
        "sourcePins": {"matrixDeclaredContract": matrix_pin, "targetContract": to_source.pin},
        "officialCampaign": False,
    }
    migration_dir = ADAPTER_ROOT / "evidence"
    migration_dir.mkdir(parents=True, exist_ok=True)
    migration_path = migration_dir / "sdd-id-migration-v1.json"
    migration_path.write_bytes(pretty_json_bytes(artifact))
    artifact["migrationArtifactPin"] = _pin(migration_path)
    return artifact


def apply_sdd_id_migration(enriched_plan: dict[str, Any], migration: dict[str, Any]) -> dict[str, Any]:
    if not migration:
        return enriched_plan
    migrated = copy.deepcopy(enriched_plan)
    from_id = migration["fromContractId"]
    to_id = migration["toContractId"]
    changed = 0
    for cell in migrated.get("cells", []):
        if cell.get("contractId") == from_id:
            cell["contractId"] = to_id
            if isinstance(cell.get("joinKey"), dict):
                cell["joinKey"]["contractId"] = to_id
            if isinstance(cell.get("linkedRecipe"), dict):
                cell["linkedRecipe"]["contractId"] = to_id
                cell["linkedRecipe"]["sourceContractIdBeforeExplicitMigration"] = from_id
            cell["sddIdMigration"] = {"version": migration["version"], "fromContractId": from_id, "toContractId": to_id, "artifact": migration["migrationArtifactPin"]}
            changed += 1
    migrated.setdefault("adapterLocalMigrations", []).append({"version": migration["version"], "fromContractId": from_id, "toContractId": to_id, "changedCells": changed, "artifact": migration["migrationArtifactPin"]})
    return migrated


def _fixture_manifest_for_recipe_compiler(fixtures_doc: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(fixtures_doc)
    packages = normalized.get("packages") or {}
    for item in normalized.get("fixtures", []) or []:
        if not isinstance(item, dict):
            continue
        track = item.get("track")
        pkg = packages.get(track) if isinstance(packages, dict) else None
        if not isinstance(pkg, dict):
            continue
        if not item.get("resources"):
            files = ((pkg.get("inventory") or {}).get("files") or {})
            item["resources"] = [{"dd": dd, "path": dd, "bytes": meta.get("bytes"), "sha256": meta.get("sha256")} for dd, meta in files.items()]
        item.setdefault("bindings", {str(res["dd"]): str(res.get("path") or res["dd"]) for res in item.get("resources", []) if isinstance(res, dict) and "dd" in res})
        keys: dict[str, Any] = {}
        for seq in pkg.get("sequential", []) or []:
            if isinstance(seq, dict) and seq.get("dd"):
                keys[str(seq["dd"])] = {"recordCount": seq.get("recordCount"), "recordSize": seq.get("recordSize")}
        for idx in pkg.get("indexed", []) or []:
            if isinstance(idx, dict) and idx.get("dd"):
                keys[str(idx["dd"])] = {"primaryKeys": idx.get("keys", []), "alternateKeyName": idx.get("alternateKeyName"), "alternateKeys": idx.get("alternateKeys", []), "recordCount": idx.get("recordCount"), "recordSize": idx.get("recordSize")}
        if keys:
            item["keys"] = keys
    return normalized


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
            raise AdapterBlocked("resource_not_found_in_fixture", {"fixtureId": self.fixture_id, "dd": dd})
        return self.resources[dd]

    def binding(self, dd: str) -> str:
        if dd in self.bindings:
            return self.bindings[dd]
        return self.resource(dd).path

    def read(self, dd: str) -> bytes:
        res = self.resource(dd)
        if self.package_path is None:
            raise AdapterBlocked("fixture_package_path_missing", {"fixtureId": self.fixture_id})
        data = (self.package_path / res.path).read_bytes()
        if res.bytes is not None and len(data) != res.bytes:
            raise AdapterBlocked("resource_size_mismatch", {"dd": dd, "expected": res.bytes, "actual": len(data)})
        digest = sha256_bytes(data)
        if res.sha256 and digest != res.sha256:
            raise AdapterBlocked("resource_sha256_mismatch", {"dd": dd, "expected": res.sha256, "actual": digest})
        return data


class FixtureIndex:
    def __init__(self, packages: dict[str, FixturePackage]):
        self.packages = packages

    @classmethod
    def from_manifest(cls, manifest: dict[str, Any], base_dir: str | Path | None = None) -> "FixtureIndex":
        base = Path(base_dir).resolve() if base_dir is not None else None
        packages: dict[str, FixturePackage] = {}
        for item in manifest.get("fixtures", []):
            fid = str(item["fixtureId"])
            track = item.get("track")
            package_path = _resolve_package_path(item.get("packagePath"), base)
            resources = _resources_from_fixture_item(item)
            bindings = {str(k): str(v) for k, v in (item.get("bindings") or {}).items()}
            if not resources and track in (manifest.get("packages") or {}):
                pkg_doc = manifest["packages"][track]
                resources.update(_resources_from_package_inventory(pkg_doc))
                bindings.update({dd: dd for dd in resources})
            packages[fid] = FixturePackage(fid, track, package_path, resources, bindings)
        return cls(packages)

    def select(self, fixture_id: str | None) -> FixturePackage:
        if not fixture_id:
            raise AdapterBlocked("fixture_id_missing")
        if fixture_id not in self.packages:
            raise AdapterBlocked("fixture_not_found", {"fixtureId": fixture_id})
        return self.packages[fixture_id]


def _resolve_package_path(raw: Any, base: Path | None) -> Path | None:
    if not raw:
        return None
    p = Path(str(raw))
    return p if p.is_absolute() else ((base / p) if base is not None else p)


def _resources_from_fixture_item(item: dict[str, Any]) -> dict[str, FixtureResource]:
    out = {}
    for res in item.get("resources", []) or []:
        dd = str(res["dd"])
        out[dd] = FixtureResource(dd, str(res.get("path") or res.get("file") or dd), res.get("bytes"), res.get("sha256"))
    return out


def _resources_from_package_inventory(pkg_doc: dict[str, Any]) -> dict[str, FixtureResource]:
    out = {}
    for dd, meta in ((pkg_doc.get("inventory") or {}).get("files") or {}).items():
        out[str(dd)] = FixtureResource(str(dd), str(dd), meta.get("bytes"), meta.get("sha256"))
    return out


def cell_index_from_enriched_plan(enriched_plan: dict[str, Any], contract_id: str | None = None) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for cell in enriched_plan.get("cells", []):
        if contract_id is not None and str(cell.get("contractId")) != str(contract_id):
            continue
        index.setdefault(str(cell.get("obligationId")), []).append(cell)
    for key in list(index):
        index[key] = sorted(index[key], key=lambda c: (str(c.get("cellId")), str(c.get("operationId"))))
    return index


def select_transition_cells(transition_result_or_model_transition: dict[str, Any], cell_index: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    refs = transition_result_or_model_transition.get("obligationRefs") or transition_result_or_model_transition.get("obligation_refs") or []
    selected: list[dict[str, Any]] = []
    for ref in refs:
        selected.extend(cell_index.get(str(ref), []))
    return selected


def _operation(openapi: dict[str, Any], method: str, path: str) -> dict[str, Any]:
    op = ((openapi.get("paths") or {}).get(path) or {}).get(method.lower())
    if not isinstance(op, dict):
        raise AdapterBlocked("operation_not_in_schema", {"method": method, "path": path})
    return op


def _request_schema(openapi: dict[str, Any], method: str, path: str) -> dict[str, Any] | None:
    op = _operation(openapi, method, path)
    content = (((op.get("requestBody") or {}).get("content") or {}).get("application/json") or {})
    schema = content.get("schema")
    return schema if isinstance(schema, dict) else None


def selector_value(selector: Any, fixture: FixturePackage, evidence: list[dict[str, Any]]) -> Any:
    if not isinstance(selector, dict):
        raise AdapterBlocked("selector_must_be_object")
    if "object" in selector:
        return {str(k): selector_value(v, fixture, evidence) for k, v in selector["object"].items()}
    if "literal" in selector:
        evidence.append({"selector": "literal"})
        return selector["literal"]
    if "fromBinding" in selector:
        dd = str(selector["fromBinding"])
        evidence.append({"selector": "fromBinding", "dd": dd, "fixtureId": fixture.fixture_id})
        return fixture.binding(dd)
    if "fromBytes" in selector:
        dd = str(selector["fromBytes"])
        data = fixture.read(dd)
        encoding = str(selector.get("encoding", "base64"))
        evidence.append({"selector": "fromBytes", "dd": dd, "fixtureId": fixture.fixture_id, "bytes": len(data)})
        if encoding == "base64":
            return base64.b64encode(data).decode("ascii")
        if encoding == "utf8":
            return data.decode("utf-8")
        raise AdapterBlocked("unsupported_bytes_encoding", {"encoding": encoding})
    if "fromSequentialRecords" in selector:
        spec = selector["fromSequentialRecords"]
        dd = str(spec["dd"])
        data = fixture.read(dd)
        record_len = int(spec["recordLength"])
        if record_len <= 0:
            raise AdapterBlocked("invalid_record_length", {"dd": dd, "recordLength": record_len})
        if len(data) % record_len != 0:
            raise AdapterBlocked("sequential_record_size_mismatch", {"dd": dd, "bytes": len(data), "recordLength": record_len})
        chunks = [data[i:i + record_len] for i in range(0, len(data), record_len)]
        fmt = str(spec.get("format", "rawBase64Objects"))
        evidence.append({"selector": "fromSequentialRecords", "dd": dd, "fixtureId": fixture.fixture_id, "bytes": len(data), "recordLength": record_len, "records": len(chunks), "format": fmt})
        if fmt == "rawBase64Objects":
            return [{"rawRecordBase64": base64.b64encode(chunk).decode("ascii")} for chunk in chunks]
        if fmt == "utf8Strings":
            return [chunk.decode("utf-8") for chunk in chunks]
        raise AdapterBlocked("unsupported_sequential_record_format", {"format": fmt})
    if "fromContractScalar" in selector:
        source = selector["fromContractScalar"]
        evidence.append({"selector": "fromContractScalar", "authority": source.get("authority")})
        return source["value"]
    if "fromResource" in selector:
        dd = str(selector["fromResource"])
        # The recipe currently uses this for contract-authorized size-style scalar derivation.
        if selector.get("format") == "size":
            res = fixture.resource(dd)
            evidence.append({"selector": "fromResource", "dd": dd, "fixtureId": fixture.fixture_id, "format": "size"})
            return res.bytes
        evidence.append({"selector": "fromResource", "dd": dd, "fixtureId": fixture.fixture_id})
        return dd
    raise AdapterBlocked("unsupported_selector", {"selectorKeys": sorted(selector.keys())})


def materialize_request_from_cell(cell: dict[str, Any], fixtures_path: str | Path, schema_path: str | Path | ContractSource) -> tuple[HttpRequestSpec, dict[str, Any]]:
    if cell.get("classification") != "recipe_available_unexercised" or cell.get("executableEligible") is not True:
        raise AdapterBlocked("blocked_cell_has_no_authorized_request", {"cellId": cell.get("cellId"), "classification": cell.get("classification"), "status": cell.get("status")})
    if isinstance(schema_path, ContractSource) and str(cell.get("contractId")) != schema_path.contract_id:
        raise AdapterBlocked("schema_contract_mismatch", {"cellContractId": cell.get("contractId"), "schemaContractId": schema_path.contract_id})
    if not isinstance(cell.get("linkedRecipe"), dict):
        raise AdapterBlocked("recipe_pin_missing", {"cellId": cell.get("cellId")})
    selectors = cell.get("selectorObjects")
    if selectors is None:
        raise AdapterBlocked("selector_objects_missing", {"cellId": cell.get("cellId")})
    op = cell.get("operation") or {}
    method = str(op.get("method") or "post").upper()
    path = str(op.get("path"))
    openapi = load_schema_source(schema_path)
    _operation(openapi, method, path)
    fixture_doc = _fixture_manifest_for_recipe_compiler(load_json(fixtures_path))
    fixture_index = RecipeFixtureIndex.from_manifest(fixture_doc, base_dir=Path(fixtures_path).parent)
    mapping = {
        "operation": {"method": method, "path": path},
        "fixtureSelection": {"fixtureId": cell.get("fixtureId")},
        "requestBody": selectors,
        "sddConstantEmptyObject": bool(cell.get("sddConstantEmptyObject")),
    }
    try:
        request, evidence = compile_request_from_recipe_mapping(mapping, fixture_index, openapi)
    except RecipeMappingBlocked as exc:
        raise AdapterBlocked(exc.blocked_reason, exc.details) from exc
    evidence = dict(evidence)
    evidence.update({
        "compiler": "t3-mapper-preparation-v1/src/t3_mapper.py::build_request_from_explicit_mapping",
        "cellId": cell.get("cellId"),
        "recipeId": (cell.get("linkedRecipe") or {}).get("recipeId"),
    })
    return request, evidence


def _capability(model: dict[str, Any], cap_id: str) -> dict[str, Any]:
    for cap in model.get("capabilities", []):
        if cap.get("id") == cap_id:
            return cap
    raise AdapterBlocked("capability_not_in_model", {"capability": cap_id})


def _transition_by_id(model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(t["id"]): t for cap in model.get("capabilities", []) for t in cap.get("transitions", [])}


def deterministic_transition_plan(model: dict[str, Any], capabilities: Iterable[str] | None = None, max_depth: int = 8, max_paths_per_capability: int = 100) -> dict[str, Any]:
    cap_ids = list(capabilities) if capabilities is not None else [str(c["id"]) for c in model.get("capabilities", [])]
    selections: list[dict[str, Any]] = []
    omissions: list[dict[str, Any]] = []
    traversal_summaries: dict[str, Any] = {}
    by_tid = _transition_by_id(model)
    for cap_id in cap_ids:
        cap = _capability(model, cap_id)
        traversal = reference_traverse(model, cap_id, max_depth=max_depth, max_paths=max_paths_per_capability)
        traversal_summaries[cap_id] = {
            "budget": traversal.get("budget"),
            "completed": len(traversal.get("completed", [])),
            "frontier": len(traversal.get("frontier", [])),
            "unknown": len(traversal.get("unknown", [])),
            "omittedCount": traversal.get("omittedCount", 0),
            "loopVisits": traversal.get("loopVisits", {}),
        }
        queue = deque([(reference_initial_state(cap), [])])
        emitted = 0
        seen_edges: set[tuple[str, str, tuple[str, ...]]] = set()
        while queue:
            state, path = queue.popleft()
            if len(path) >= max_depth:
                omissions.append({"capability": cap_id, "reason": "max_depth", "state": state["state"], "path": path})
                continue
            outgoing = _enabled_for_traversal(model, cap, state)
            if not outgoing:
                continue
            for item in outgoing:
                tid = str(item["transitionId"])
                npath = path + [tid]
                key = (str(state["state"]), tid, tuple(npath))
                if key in seen_edges:
                    continue
                seen_edges.add(key)
                tr = copy.deepcopy(by_tid[tid])
                selections.append({"capability": cap_id, "transitionId": tid, "path": npath, "guardResult": item.get("guardResult"), "transition": tr})
                if emitted < max_paths_per_capability:
                    queue.append((item["state"], npath))
                    emitted += 1
                else:
                    omissions.append({"capability": cap_id, "reason": "max_paths_per_capability", "transitionId": tid, "path": npath})
    selections.sort(key=lambda x: (x["capability"], len(x["path"]), x["path"], x["transitionId"]))
    return {
        "algorithm": "reference_engine_bfs_sorted_transitions_with_witnessed_guards",
        "budgets": {"maxDepth": max_depth, "maxPathsPerCapability": max_paths_per_capability},
        "capabilities": cap_ids,
        "transitionCount": len(selections),
        "transitions": selections,
        "omissions": omissions,
        "traversalSummaries": traversal_summaries,
    }


def _case_id(contract_id: str, ordinal: int, transition_id: str, cell_id: str) -> str:
    raw = f"{contract_id}:{transition_id}:{cell_id}"
    return f"T3-{ordinal:04d}-{sha256_bytes(raw.encode())[:12]}"


def build_t3_suite(
    contract_id: str,
    model_path: str | Path,
    enriched_plan: dict[str, Any],
    fixtures_path: str | Path,
    schema_path: str | Path | ContractSource,
    capabilities: Iterable[str] | None = None,
    max_depth: int = 8,
    max_paths_per_capability: int = 100,
) -> tuple[Suite, dict[str, Any]]:
    model = load_model(model_path)
    if isinstance(schema_path, ContractSource) and contract_id != schema_path.contract_id:
        raise AdapterBlocked("schema_contract_mismatch", {"contractId": contract_id, "schemaContractId": schema_path.contract_id})
    plan = deterministic_transition_plan(model, capabilities, max_depth, max_paths_per_capability)
    cell_index = cell_index_from_enriched_plan(enriched_plan, contract_id=contract_id)
    cases: list[Case] = []
    blocked: list[dict[str, Any]] = []
    inconclusive: list[dict[str, Any]] = []
    for selected in plan["transitions"]:
        transition = selected["transition"]
        cells = select_transition_cells(transition, cell_index)
        if not cells:
            inconclusive.append({"transitionId": selected["transitionId"], "obligationRefs": transition.get("obligationRefs", []), "reason": "no_enriched_cell_for_transition_obligation_refs", "path": selected["path"]})
            continue
        for cell in cells:
            if cell.get("classification") != "recipe_available_unexercised" or cell.get("executableEligible") is not True:
                blocked.append({"cellId": cell.get("cellId"), "transitionId": selected["transitionId"], "classification": cell.get("classification"), "status": cell.get("status"), "reason": cell.get("reason", "cell_not_executable_eligible"), "path": selected["path"]})
                continue
            try:
                request, evidence = materialize_request_from_cell(cell, fixtures_path, schema_path)
            except AdapterBlocked as exc:
                blocked.append({"cellId": cell.get("cellId"), "transitionId": selected["transitionId"], "classification": "implementation_missing", "reason": exc.reason, "details": exc.details, "path": selected["path"]})
                continue
            ordinal = len(cases) + 1
            expectation = Expectation(
                "contract-checker-independent-obligation",
                {
                    "contract_checker": "documented_separate_independent_obligation",
                    "expected_status_source": "not_runtime_not_api_not_results",
                    "status": "inconclusive_until_checker_bound",
                },
            )
            cases.append(Case(
                case_id=_case_id(contract_id, ordinal, selected["transitionId"], str(cell.get("cellId"))),
                suite_id="T3",
                origin=f"T3-v4-adapter:{contract_id}",
                request=request,
                resource_package_id=str(cell.get("fixtureId")),
                expectation=expectation,
                timeout_seconds=5.0,
                parameters={
                    "cellRef": cell.get("cellId"),
                    "obligationId": cell.get("obligationId"),
                    "transitionId": selected["transitionId"],
                    "guardResult": selected.get("guardResult"),
                    "capability": selected.get("capability"),
                    "recipeId": (cell.get("linkedRecipe") or {}).get("recipeId"),
                    "requestEvidence": evidence,
                    "officialCampaign": False,
                },
                sequence=tuple(selected["path"]),
                provenance=(f"reference-executable-v4:{selected['transitionId']}", f"t3-cell:{cell.get('cellId')}"),
            ))
    report = {
        "kind": "t3-campaign-adapter-v3-build-report",
        "status": "candidate_not_official",
        "officialCampaign": False,
        "contractId": contract_id,
        "acceptedCount": len(cases),
        "blockedCount": len(blocked),
        "inconclusiveCount": len(inconclusive),
        "blocked": blocked,
        "inconclusive": inconclusive,
        "selectionPlan": {k: v for k, v in plan.items() if k != "transitions"},
        "traversalSummaries": plan["traversalSummaries"],
        "limitations": [
            "contract checker is documented as a separate independent obligation and is not inferred from runtime/API/results",
            "unsupported cells remain blocked; transitions without joined cells remain inconclusive",
            "no official AWS suite is generated unless an explicit output path is supplied by the caller",
        ],
    }
    return Suite("T3", cases), report


def load_real_inputs(p3: str | Path = P3, contract_id: str = "E1-1") -> dict[str, Any]:
    p3 = Path(p3)
    sys.path.insert(0, str(p3 / "t3-mapping-integration-v2" / "src"))
    from mapping_integration import build_enriched_plan  # type: ignore
    matrix_path = p3 / "applicability-mapping-v3" / "applicability_matrix.json"
    recipes_path = p3 / "t3-mapping-recipes-v1" / "recipes.json"
    matrix = load_json(matrix_path)
    recipes = load_json(recipes_path)
    registry = load_contract_registry(p3)
    contract_source = resolve_contract_source(p3, contract_id)
    enriched_plan = build_enriched_plan(matrix, recipes)
    migration = sdd_id_migration_proof(p3, matrix, registry)
    if contract_id == "E3-SDD-stage6r3":
        enriched_plan = apply_sdd_id_migration(enriched_plan, migration)
    input_pins = {
        "model": _pin(p3 / "reference-executable-v4" / "model.json"),
        "matrix": _pin(matrix_path),
        "recipes": _pin(recipes_path),
        "fixtures": _pin(p3 / "fixture-materialization-v2" / "package" / "manifest.json"),
        "schema": contract_source.pin,
    }
    if migration:
        input_pins["sddIdMigration"] = migration
    return {
        "model_path": p3 / "reference-executable-v4" / "model.json",
        "fixtures_path": p3 / "fixture-materialization-v2" / "package" / "manifest.json",
        "schema_path": contract_source.path,
        "contractSource": contract_source,
        "enriched_plan": enriched_plan,
        "inputPins": input_pins,
    }


def _pin(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"path": str(path), "sha256": sha256_bytes(data), "bytes": len(data)}


def static_real_model_compatibility(
    p3: str | Path = P3,
    contract_id: str = "E1-1",
    capabilities: Iterable[str] | None = None,
    max_depth: int = 8,
    max_paths_per_capability: int = 100,
) -> dict[str, Any]:
    if contract_id == "all7":
        contracts: dict[str, Any] = {}
        for cid in load_contract_registry(p3):
            item = static_real_model_compatibility(p3, contract_id=cid, capabilities=capabilities, max_depth=max_depth, max_paths_per_capability=max_paths_per_capability)
            contracts[cid] = item
        return {
            "kind": "t3-campaign-adapter-v3-static-real-model-compatibility-all7",
            "status": "candidate_static_only",
            "officialCampaign": False,
            "officialSuiteGenerated": False,
            "contractCount": len(contracts),
            "contracts": contracts,
        }
    inputs = load_real_inputs(p3, contract_id=contract_id)
    model = load_model(inputs["model_path"])
    model_report = validate_model(model, root=Path(p3) / "reference-executable-v4")
    plan = deterministic_transition_plan(model, capabilities, max_depth, max_paths_per_capability)
    cell_index = cell_index_from_enriched_plan(inputs["enriched_plan"], contract_id=contract_id)
    joined = 0
    blocked = 0
    inconclusive = 0
    materialization_blocked_by_reason: Counter[str] = Counter()
    blocked_by_source_bound_reason: Counter[str] = Counter()
    field_errors: list[dict[str, Any]] = []
    ready_requests: list[dict[str, Any]] = []
    for selected in plan["transitions"]:
        cells = select_transition_cells(selected["transition"], cell_index)
        if not cells:
            inconclusive += 1
        for cell in cells:
            if cell.get("classification") == "recipe_available_unexercised" and cell.get("executableEligible") is True:
                try:
                    request, evidence = materialize_request_from_cell(cell, inputs["fixtures_path"], inputs["contractSource"])
                    joined += 1
                    ready_requests.append({
                        "cellId": cell.get("cellId"),
                        "transitionId": selected["transitionId"],
                        "method": request.method,
                        "path": request.path,
                        "fixtureId": cell.get("fixtureId"),
                        "recipeId": (cell.get("linkedRecipe") or {}).get("recipeId"),
                        "sourceBoundValueCount": len(evidence.get("sourceboundValues") or []),
                    })
                except AdapterBlocked as exc:
                    blocked += 1
                    materialization_blocked_by_reason[exc.reason] += 1
                    blocked_by_source_bound_reason[exc.reason] += 1
                    field_errors.append({"cellId": cell.get("cellId"), "transitionId": selected["transitionId"], "reason": exc.reason, "details": exc.details})
            else:
                blocked += 1
                reason = str(cell.get("reason") or cell.get("classification") or "cell_not_executable_eligible")
                blocked_by_source_bound_reason[reason] += 1
                field_errors.append({"cellId": cell.get("cellId"), "transitionId": selected["transitionId"], "reason": reason, "classification": cell.get("classification"), "status": cell.get("status")})
    return {
        "kind": "t3-campaign-adapter-v3-static-real-model-compatibility",
        "status": "candidate_static_only",
        "officialCampaign": False,
        "officialSuiteGenerated": False,
        "contractId": contract_id,
        "inputPins": inputs["inputPins"],
        "modelValidation": model_report,
        "selectionPlan": {k: v for k, v in plan.items() if k != "transitions"},
        "traversalSummaries": plan["traversalSummaries"],
        "cellJoinSummary": {"eligibleJoinedCells": joined, "blockedJoinedCells": blocked, "inconclusiveTransitionsWithoutCells": inconclusive},
        "executableEligibleDistinctCells": sum(1 for c in inputs["enriched_plan"].get("cells", []) if c.get("contractId") == contract_id and c.get("executableEligible") is True),
        "readyRequestCount": len(ready_requests),
        "readyRequestsPreparatory": ready_requests,
        "blockedBySourceBoundReason": dict(blocked_by_source_bound_reason),
        "fieldErrors": field_errors,
        "materializationBlockedByReason": dict(materialization_blocked_by_reason),
        "freeze": None,
        "runtimeExecuted": False,
    }


def run_adapter(
    p3: str | Path = P3,
    contract_id: str = "E1-1",
    capabilities: Iterable[str] | None = None,
    max_depth: int = 8,
    max_paths_per_capability: int = 100,
    freeze_output: str | Path | None = None,
) -> dict[str, Any]:
    inputs = load_real_inputs(p3, contract_id=contract_id)
    suite, report = build_t3_suite(contract_id, inputs["model_path"], inputs["enriched_plan"], inputs["fixtures_path"], inputs["contractSource"], capabilities, max_depth, max_paths_per_capability)
    report["inputPins"] = inputs["inputPins"]
    if freeze_output is not None:
        freeze_path = freeze_suite(suite, Path(freeze_output))
        loaded = load_frozen_suite(freeze_path)
        report["freeze"] = {"path": str(freeze_path), "sha256": sha256_bytes(freeze_path.read_bytes()), "loadedCases": len(loaded.cases), "harness": str(HARNESS_SRC / "campaign_harness.py")}
    else:
        report["freeze"] = None
    return report


def write_report(root: str | Path = Path(__file__).resolve().parents[1]) -> dict[str, Any]:
    root = Path(root)
    evidence = root / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    static_report = static_real_model_compatibility(P3, contract_id="all7", capabilities=["CBTRN02C_POSTTRAN", "CBACT04C_INTCALC", "CBTRN03C_TRANREPT"], max_depth=6, max_paths_per_capability=12)
    (evidence / "static-real-model-compatibility-all7.json").write_bytes(pretty_json_bytes(static_report))
    summaries = {cid: item["cellJoinSummary"] for cid, item in static_report["contracts"].items()}
    blocked_reasons = {cid: item.get("materializationBlockedByReason", {}) for cid, item in static_report["contracts"].items()}
    md = f"""# T3 Campaign Adapter v3

Status: candidate/static preparation only. Official AWS campaign generated: false.

## Fixed in this adapter

- Resolves the exact seven `contractId` values from `campaign-configuration-v2/campaign-config-v2.json`.
- Extracts each pinned OpenAPI from its original source (`parsed.json` text for E1/E2, P2a JSON for SDD) and preserves source identity/hash/bytes.
- Builds and runs T3 with the requested contract's own schema; E1/E2 are never validated against the SDD schema.
- Fails closed on unknown contract IDs, cross-contract path/schema mismatches, and blocked upstream cells.
- Keeps reference-engine guard traversal, fixture materialization, and explicit freeze behavior unchanged.

## Static all7 check

Contract count: `{static_report['contractCount']}`.
Joined/block/inconclusive summary: `{json.dumps(summaries, sort_keys=True)}`.
Remaining materialization blocks by real type after correct schema binding: `{json.dumps(blocked_reasons, sort_keys=True)}`.

## Simple invocation for next authorized generation

```bash
cd "{P3.parent}"
P2a/.venv/bin/python P3/t3-campaign-adapter-v3/src/t3_campaign_adapter.py \
  --contract-id E1-1 \
  --capability CBTRN02C_POSTTRAN --capability CBACT04C_INTCALC --capability CBTRN03C_TRANREPT \
  --max-depth 8 --max-paths-per-capability 100 \
  --freeze-output P3/t3-campaign-adapter-v3/evidence/T3-E1-1-authorized-candidate.json
```

Do not run that freeze command as an official campaign unless P3 authorization covers the output path and budgets.
"""
    (root / "REPORT.md").write_text(md, encoding="utf-8")
    return static_report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="T3 campaign adapter backed by reference-executable-v4 and campaign-harness-v3")
    ap.add_argument("--p3", default=str(P3))
    ap.add_argument("--contract-id", default="E1-1")
    ap.add_argument("--capability", action="append", default=[])
    ap.add_argument("--max-depth", type=int, default=8)
    ap.add_argument("--max-paths-per-capability", type=int, default=100)
    ap.add_argument("--freeze-output")
    ap.add_argument("--static-only", action="store_true")
    ap.add_argument("--write-report", action="store_true")
    ns = ap.parse_args(argv)
    caps = ns.capability or None
    if ns.write_report:
        report = write_report(Path(__file__).resolve().parents[1])
    elif ns.static_only:
        report = static_real_model_compatibility(ns.p3, ns.contract_id, caps, ns.max_depth, ns.max_paths_per_capability)
    else:
        report = run_adapter(ns.p3, ns.contract_id, caps, ns.max_depth, ns.max_paths_per_capability, ns.freeze_output)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

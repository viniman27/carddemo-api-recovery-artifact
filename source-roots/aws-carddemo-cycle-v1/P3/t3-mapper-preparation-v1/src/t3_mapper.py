from __future__ import annotations

import base64
import hashlib
import json
import sys
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

from jsonschema import Draft202012Validator, RefResolver

P3 = Path(__file__).resolve().parents[2]
HARNESS_SRC = P3 / "campaign-harness-v1" / "src"
if str(HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(HARNESS_SRC))

from campaign_harness import Case, Expectation, HttpRequestSpec, Suite, UnionBuilder, freeze_suite, load_frozen_suite  # noqa: E402


class MappingBlocked(Exception):
    def __init__(self, blocked_reason: str, *, details: dict[str, Any] | None = None):
        super().__init__(blocked_reason)
        self.blocked_reason = blocked_reason
        self.details = details or {}


class T3MapperError(Exception):
    pass


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json_or_yaml(path: Path) -> Any:
    text = Path(path).read_text(encoding="utf-8")
    if Path(path).suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise T3MapperError("yaml input requires PyYAML")
        return yaml.safe_load(text)
    return json.loads(text)


def _json_b64(value: Any) -> str:
    return base64.b64encode(json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).decode("ascii")


def _json_bytes(data: Any) -> bytes:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _resolve_ref(document: dict[str, Any], ref: str) -> Any:
    if not ref.startswith("#/"):
        raise T3MapperError(f"unsupported non-local schema ref: {ref}")
    node: Any = document
    for raw in ref[2:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        node = node[key]
    return node


def _operation(openapi: dict[str, Any], method: str, path: str) -> dict[str, Any]:
    path_item = (openapi.get("paths") or {}).get(path)
    if not isinstance(path_item, dict):
        raise MappingBlocked("operation_not_in_contract", details={"path": path})
    operation = path_item.get(method.lower())
    if not isinstance(operation, dict):
        raise MappingBlocked("method_not_in_contract", details={"method": method, "path": path})
    return operation


def request_schema_for_operation(openapi: dict[str, Any], method: str, path: str) -> dict[str, Any] | None:
    operation = _operation(openapi, method, path)
    request_body = operation.get("requestBody")
    if not isinstance(request_body, dict):
        return None
    content = request_body.get("content") or {}
    app_json = content.get("application/json") if isinstance(content, dict) else None
    if not isinstance(app_json, dict):
        return None
    schema = app_json.get("schema")
    if not isinstance(schema, dict):
        return None
    if "$ref" in schema:
        resolved = _resolve_ref(openapi, str(schema["$ref"]))
        if not isinstance(resolved, dict):
            raise T3MapperError(f"schema ref did not resolve to object: {schema['$ref']}")
        return resolved
    return schema


def validate_request_against_openapi(request: HttpRequestSpec, openapi: dict[str, Any]) -> dict[str, Any]:
    schema = request_schema_for_operation(openapi, request.method, request.path)
    required_body = bool(_operation(openapi, request.method, request.path).get("requestBody", {}).get("required", False))
    if schema is None:
        if required_body and request.body_kind == "absent":
            raise MappingBlocked("schema_requires_body_but_request_absent")
        return {"valid": True, "schemaPresent": False}
    if request.body_kind != "json":
        raise MappingBlocked("request_body_not_json_for_json_schema", details={"body_kind": request.body_kind})
    try:
        body = json.loads(base64.b64decode(request.body_b64 or "", validate=True).decode("utf-8"))
    except Exception as exc:
        raise MappingBlocked("request_body_json_decode_failed", details={"error": str(exc)}) from exc
    validator = Draft202012Validator(schema, resolver=RefResolver.from_schema(openapi))
    errors = sorted(validator.iter_errors(body), key=lambda e: list(e.path))
    if errors:
        raise MappingBlocked("schema_validation_failed", details={"errors": [e.message for e in errors]})
    return {"valid": True, "schemaPresent": True, "schemaType": schema.get("type"), "bodyKeys": sorted(body.keys()) if isinstance(body, dict) else None}


def _is_closed_empty_object_schema(schema: dict[str, Any] | None) -> bool:
    if not isinstance(schema, dict) or schema.get("type") != "object":
        return False
    props = schema.get("properties", {})
    if props == []:  # matrix summary represents no properties as []
        props = {}
    return props == {} and schema.get("additionalProperties") is False and schema.get("required", []) in ([], None)


@dataclass(frozen=True)
class FixtureResource:
    dd: str
    rel_path: str
    bytes: int | None
    sha256: str | None


@dataclass(frozen=True)
class FixturePackage:
    fixture_id: str
    track: str | None
    package_path: Path | None
    resources: dict[str, FixtureResource]
    bindings: dict[str, str]
    keys: dict[str, Any]

    def resource(self, dd: str) -> FixtureResource:
        if dd not in self.resources:
            raise MappingBlocked("resource_not_found_in_fixture", details={"dd": dd, "fixtureId": self.fixture_id})
        return self.resources[dd]

    def binding(self, dd: str) -> str:
        if dd in self.bindings:
            return self.bindings[dd]
        if dd in self.resources:
            return self.resources[dd].rel_path
        raise MappingBlocked("binding_not_found_in_fixture", details={"dd": dd, "fixtureId": self.fixture_id})

    def read_resource_bytes(self, dd: str) -> bytes:
        resource = self.resource(dd)
        if self.package_path is None:
            raise MappingBlocked("fixture_package_path_missing", details={"fixtureId": self.fixture_id})
        path = self.package_path / resource.rel_path
        if not path.exists():
            raise MappingBlocked("resource_path_missing", details={"dd": dd, "path": str(path)})
        data = path.read_bytes()
        if resource.bytes is not None and len(data) != resource.bytes:
            raise MappingBlocked("resource_size_mismatch", details={"dd": dd, "expected": resource.bytes, "actual": len(data)})
        if resource.sha256 and _sha256_bytes(data) != resource.sha256:
            raise MappingBlocked("resource_sha256_mismatch", details={"dd": dd, "expected": resource.sha256, "actual": _sha256_bytes(data)})
        return data


class FixtureIndex:
    def __init__(self, packages: dict[str, FixturePackage]):
        self.packages = packages

    @classmethod
    def from_manifest(cls, manifest: dict[str, Any], *, base_dir: Path | None = None) -> "FixtureIndex":
        packages: dict[str, FixturePackage] = {}
        for item in manifest.get("fixtures", []):
            fixture_id = str(item.get("fixtureId", ""))
            if not fixture_id:
                continue
            package_raw = item.get("packagePath")
            package_path = None
            if isinstance(package_raw, str):
                candidate = Path(package_raw)
                if not candidate.is_absolute() and base_dir is not None:
                    candidate = base_dir / candidate
                package_path = candidate
            bindings = {str(k): str(v) for k, v in (item.get("bindings") or {}).items()} if isinstance(item.get("bindings"), dict) else {}
            resources: dict[str, FixtureResource] = {}
            raw_resources = item.get("resources")
            if isinstance(raw_resources, dict):
                iterable = [{"dd": k, **(v if isinstance(v, dict) else {})} for k, v in raw_resources.items()]
            else:
                iterable = raw_resources or []
            for res in iterable:
                if not isinstance(res, dict) or "dd" not in res:
                    continue
                dd = str(res["dd"])
                rel = str(res.get("path") or res.get("file") or bindings.get(dd) or dd)
                resources[dd] = FixtureResource(dd, rel, res.get("bytes"), res.get("sha256"))
            keys = item.get("keys") or item.get("concreteKeys") or {}
            packages[fixture_id] = FixturePackage(fixture_id, item.get("track"), package_path, resources, bindings, keys if isinstance(keys, dict) else {})
        return cls(packages)

    def select(self, selection: dict[str, Any] | str | None) -> FixturePackage | None:
        if selection is None:
            return None
        fixture_id = selection if isinstance(selection, str) else selection.get("fixtureId")
        if not isinstance(fixture_id, str) or not fixture_id:
            raise MappingBlocked("fixture_selection_without_fixture_id")
        if fixture_id not in self.packages:
            raise MappingBlocked("fixture_not_found", details={"fixtureId": fixture_id})
        return self.packages[fixture_id]


def _transaction_object_from_350(raw: bytes, *, numeric_fields: set[str] | None = None) -> dict[str, Any]:
    if len(raw) != 350:
        raise MappingBlocked("transaction_record_length_mismatch", details={"expected": 350, "actual": len(raw)})
    text = raw.decode("ascii")
    fields = {
        "transactionId": text[0:16],
        "typeCode": text[16:18],
        "categoryCode": text[18:22],
        "source": text[22:32],
        "description": text[32:132].rstrip(),
        "amount": int(text[132:143]) / 100,
        "merchantId": text[143:152],
        "merchantName": text[152:202].rstrip(),
        "merchantCity": text[202:252].rstrip(),
        "merchantZip": text[252:262],
        "cardNumber": text[262:278],
        "originalTimestamp": text[278:304],
        "processingTimestamp": text[304:330],
        "filler": text[330:350],
    }
    numeric_fields = numeric_fields or set()
    if "categoryCode" in numeric_fields:
        fields["categoryCode"] = int(str(fields["categoryCode"]))
    if "merchantId" in numeric_fields:
        fields["merchantId"] = int(str(fields["merchantId"]))
    return fields


def _records_from_resource(selector: dict[str, Any], fixture: FixturePackage | None, evidence: list[dict[str, Any]]) -> list[Any]:
    if fixture is None:
        raise MappingBlocked("record_selector_without_fixture")
    spec = selector["fromSequentialRecords"]
    if not isinstance(spec, dict):
        raise MappingBlocked("fromSequentialRecords_must_be_object")
    dd = str(spec.get("dd"))
    record_length = int(spec.get("recordLength", 0))
    if record_length <= 0:
        raise MappingBlocked("recordLength_missing")
    data = fixture.read_resource_bytes(dd)
    if len(data) % record_length != 0:
        raise MappingBlocked("sequential_resource_not_integral_records", details={"dd": dd, "bytes": len(data), "recordLength": record_length})
    fmt = str(spec.get("format", "rawBase64Objects"))
    records = [data[i : i + record_length] for i in range(0, len(data), record_length)]
    out: list[Any] = []
    numeric = set(map(str, spec.get("numericFields", []))) if isinstance(spec.get("numericFields", []), list) else set()
    for idx, rec in enumerate(records):
        span = {"dd": dd, "recordIndex": idx, "byteStart": idx * record_length, "byteEndExclusive": (idx + 1) * record_length, "fixtureId": fixture.fixture_id}
        if fmt == "rawBase64Objects":
            out.append({"recordBase64": base64.b64encode(rec).decode("ascii")})
            evidence.append({"selector": "fromSequentialRecords", "format": fmt, **span})
        elif fmt == "base64Strings":
            out.append(base64.b64encode(rec).decode("ascii"))
            evidence.append({"selector": "fromSequentialRecords", "format": fmt, **span})
        elif fmt == "utf8Strings":
            out.append(rec.decode("utf-8"))
            evidence.append({"selector": "fromSequentialRecords", "format": fmt, **span})
        elif fmt == "transactionObjects":
            obj = _transaction_object_from_350(rec, numeric_fields=numeric)
            out.append(obj)
            for name in obj:
                evidence.append({"selector": "fromSequentialRecords", "format": fmt, "field": name, **span})
        else:
            raise MappingBlocked("unsupported_sequential_record_format", details={"format": fmt})
    return out


def _selector_value(selector: Any, fixture: FixturePackage | None, evidence: list[dict[str, Any]] | None = None) -> Any:
    if evidence is None:
        evidence = []
    if not isinstance(selector, dict):
        raise MappingBlocked("selector_must_be_object")
    if "object" in selector:
        value = selector["object"]
        if not isinstance(value, dict):
            raise MappingBlocked("object_selector_must_wrap_object")
        return {str(k): _selector_value(v, fixture, evidence) for k, v in value.items()}
    if "array" in selector:
        value = selector["array"]
        if not isinstance(value, list):
            raise MappingBlocked("array_selector_must_wrap_array")
        return [_selector_value(v, fixture, evidence) for v in value]
    if "literal" in selector:
        value = selector["literal"]
        if isinstance(value, (str, int, float, bool)) or value is None:
            evidence.append({"selector": "literal", "authority": selector.get("authority", "recipe-scalar")})
            return value
        raise MappingBlocked("literal_selector_must_be_scalar")
    if "fromContractScalar" in selector:
        source = selector["fromContractScalar"]
        if not isinstance(source, dict) or "value" not in source or "authority" not in source:
            raise MappingBlocked("fromContractScalar_requires_value_and_authority")
        value = source["value"]
        if isinstance(value, (str, int, float, bool)) or value is None:
            evidence.append({"selector": "fromContractScalar", "authority": source["authority"]})
            return value
        raise MappingBlocked("contract_scalar_must_be_scalar")
    if "fromResource" in selector:
        if fixture is None:
            raise MappingBlocked("resource_selector_without_fixture")
        dd = str(selector["fromResource"])
        resource = fixture.resource(dd)
        fmt = str(selector.get("format", "ddName"))
        evidence.append({"selector": "fromResource", "dd": dd, "format": fmt, "fixtureId": fixture.fixture_id})
        if fmt == "ddName":
            return dd
        if fmt == "sha256":
            return resource.sha256
        if fmt == "size":
            return resource.bytes
        raise MappingBlocked("unsupported_resource_format", details={"format": fmt})
    if "fromBinding" in selector:
        if fixture is None:
            raise MappingBlocked("binding_selector_without_fixture")
        dd = str(selector["fromBinding"])
        value = fixture.binding(dd)
        evidence.append({"selector": "fromBinding", "dd": dd, "fixtureId": fixture.fixture_id})
        return value
    if "fromBytes" in selector:
        if fixture is None:
            raise MappingBlocked("bytes_selector_without_fixture")
        dd = str(selector["fromBytes"])
        data = fixture.read_resource_bytes(dd)
        encoding = str(selector.get("encoding", "base64"))
        evidence.append({"selector": "fromBytes", "dd": dd, "encoding": encoding, "byteStart": 0, "byteEndExclusive": len(data), "fixtureId": fixture.fixture_id})
        if encoding == "base64":
            return base64.b64encode(data).decode("ascii")
        if encoding == "utf8":
            return data.decode("utf-8")
        raise MappingBlocked("unsupported_bytes_encoding", details={"encoding": encoding})
    if "fromSequentialRecords" in selector:
        return _records_from_resource(selector, fixture, evidence)
    if "fromScalar" in selector:
        if fixture is None:
            raise MappingBlocked("scalar_selector_without_fixture")
        source = selector["fromScalar"]
        if not isinstance(source, dict):
            raise MappingBlocked("fromScalar_must_be_object")
        dd = str(source.get("dd"))
        attr = str(source.get("attribute"))
        index = int(source.get("index", 0))
        values = (((fixture.keys.get(dd) or {}).get(attr)) if isinstance(fixture.keys.get(dd), dict) else None)
        if not isinstance(values, list) or index >= len(values):
            raise MappingBlocked("scalar_source_not_found", details={"dd": dd, "attribute": attr, "index": index})
        value = values[index]
        if isinstance(value, (str, int, float, bool)) or value is None:
            evidence.append({"selector": "fromScalar", "dd": dd, "attribute": attr, "index": index, "fixtureId": fixture.fixture_id})
            return value
        raise MappingBlocked("scalar_source_not_scalar")
    raise MappingBlocked("unsupported_selector", details={"selectorKeys": sorted(map(str, selector.keys()))})


def _body_from_mapping(request_body: Any, fixture: FixturePackage | None, evidence: list[dict[str, Any]] | None = None) -> Any:
    if not isinstance(request_body, dict):
        raise MappingBlocked("insufficient_request_body_plan", details={"requestBody": request_body})
    if "object" in request_body and len(request_body) == 1:
        return _selector_value(request_body, fixture, evidence)
    body: dict[str, Any] = {}
    for field, selector in request_body.items():
        body[str(field)] = _selector_value(selector, fixture, evidence)
    return body


def build_request_from_explicit_mapping(mapping: dict[str, Any], fixture_index: FixtureIndex, openapi: dict[str, Any]) -> tuple[HttpRequestSpec, dict[str, Any]]:
    if "request" in mapping:
        raise MappingBlocked("request_dict_not_allowed_use_explicit_operation_and_selectors")
    operation = mapping.get("operation")
    if not isinstance(operation, dict):
        raise MappingBlocked("operation_mapping_missing")
    method = str(operation.get("method", "")).upper()
    path = operation.get("path")
    if method == "" or not isinstance(path, str):
        raise MappingBlocked("operation_method_path_missing")
    _operation(openapi, method, path)
    fixture = fixture_index.select(mapping.get("fixtureSelection"))
    body_plan = mapping.get("requestBody")
    schema = request_schema_for_operation(openapi, method, path)
    sdd_constant = bool(mapping.get("sddConstantEmptyObject")) or (_is_closed_empty_object_schema(schema) and body_plan == {})
    sourcebound_values: list[dict[str, Any]] = []
    if sdd_constant:
        if not _is_closed_empty_object_schema(schema):
            raise MappingBlocked("sdd_empty_object_not_sustained_by_schema")
        body = {}
    else:
        body = _body_from_mapping(body_plan, fixture, sourcebound_values)
    request = HttpRequestSpec(method, path, (("content-type", "application/json"),), "json", _json_b64(body))
    schema_validation = validate_request_against_openapi(request, openapi)
    evidence = {
        "schemaValidation": schema_validation,
        "sddConstantEmptyObject": sdd_constant,
        "selectedFixture": {"fixtureId": fixture.fixture_id, "track": fixture.track} if fixture else None,
        "sourceboundValues": sourcebound_values,
        "inventedValues": False,
        "officialCampaign": False,
    }
    return request, evidence


def _load_cells(mapping_doc: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(mapping_doc.get("cells"), list):
        return [c for c in mapping_doc["cells"] if isinstance(c, dict)]
    cells: list[dict[str, Any]] = []
    for obl in mapping_doc.get("obligations", []):
        for cm in obl.get("contractMappings", []):
            if not isinstance(cm, dict):
                continue
            t3 = cm.get("t3DeterministicMapping") or {}
            cell = {
                "cellId": f"{obl.get('obligationId')}::{cm.get('contractId')}::{(cm.get('operation') or {}).get('operationId')}",
                "obligationId": obl.get("obligationId"),
                "contractId": cm.get("contractId"),
                "track": obl.get("track"),
                "operation": {"method": (cm.get("operation") or {}).get("method"), "path": (cm.get("operation") or {}).get("path")},
                "requestBody": t3.get("requestBody"),
                "fixtureSelection": None,
                "matrixGenerativeUse": t3.get("generativeUse"),
                "selectorUsableForGeneration": t3.get("selectorUsableForGeneration"),
                "fieldSelectors": t3.get("fieldSelectors", []),
                "candidateFixtures": cm.get("candidateFixtures", []),
                "applicabilityStatus": cm.get("applicabilityStatus"),
            }
            if t3.get("requestBody") == {} and (
                (cm.get("contractId") or "").startswith("E3")
                or _is_closed_empty_object_schema((cm.get("operation") or {}).get("requestSchema"))
            ):
                cell["sddConstantEmptyObject"] = True
            cells.append(cell)
    return cells


def _transition_order(model: dict[str, Any], state: str) -> list[dict[str, Any]]:
    transitions: list[dict[str, Any]] = []
    for cap in model.get("capabilities", []):
        transitions.extend(t for t in cap.get("transitions", []) if t.get("from") == state)
    return sorted(transitions, key=lambda t: str(t.get("id")))


def _initial_state(model: dict[str, Any]) -> str:
    caps = model.get("capabilities") or []
    if not caps:
        raise T3MapperError("model has no capabilities")
    return str(caps[0].get("initialState"))


def bfs_map_model_to_suite(contract_id: str, model_path: Path, mapping_path: Path, fixtures_path: Path, schema_path: Path, *, max_depth: int = 8, max_paths: int = 50) -> tuple[Suite, dict[str, Any]]:
    model_bytes = Path(model_path).read_bytes(); mapping_bytes = Path(mapping_path).read_bytes(); fixtures_bytes = Path(fixtures_path).read_bytes(); schema_bytes = Path(schema_path).read_bytes()
    model = json.loads(model_bytes.decode("utf-8")); mapping_doc = json.loads(mapping_bytes.decode("utf-8")); fixture_doc = json.loads(fixtures_bytes.decode("utf-8")); openapi = _read_json_or_yaml(Path(schema_path))
    fixture_index = FixtureIndex.from_manifest(fixture_doc, base_dir=Path(fixtures_path).parent)
    cells_by_transition: dict[str, list[dict[str, Any]]] = {}
    for cell in _load_cells(mapping_doc):
        tid = cell.get("transitionId") or cell.get("obligationId") or cell.get("cellId")
        cells_by_transition.setdefault(str(tid), []).append(cell)
    queue = deque([(_initial_state(model), [])])
    seen: set[str] = set()
    cases: list[Case] = []
    blocked: list[dict[str, Any]] = []
    examined = 0
    while queue and examined < max_paths:
        state, path = queue.popleft()
        if len(path) >= max_depth:
            continue
        for tr in _transition_order(model, state):
            tid = str(tr.get("id"))
            if tid in seen:
                continue
            seen.add(tid); examined += 1
            next_path = path + [tid]
            cells = cells_by_transition.get(tid)
            if not cells:
                blocked.append({"transitionId": tid, "path": next_path, "classification": "blocked_no_mapping_cell", "blocked_reason": "no explicit mapping cell for BFS path"})
            for cell in cells or []:
                cell_id = str(cell.get("cellId", tid))
                if cell.get("blocked_reason"):
                    blocked.append({"cellId": cell_id, "transitionId": tid, "path": next_path, "classification": "blocked_by_mapping", "blocked_reason": str(cell["blocked_reason"])})
                    continue
                try:
                    request, evidence = build_request_from_explicit_mapping(cell, fixture_index, openapi)
                    cases.append(Case(
                        case_id=f"T3-{contract_id}-{cell_id}", suite_id="T3", origin=f"T3:{contract_id}", request=request,
                        resource_package_id=str((cell.get("fixtureSelection") or {}).get("fixtureId", "external-fixture") if isinstance(cell.get("fixtureSelection"), dict) else "external-fixture"),
                        expectation=Expectation("status", {"status": [200, 400, 500, 503]}), timeout_seconds=float(cell.get("timeoutSeconds", 5.0)),
                        parameters={"transitionId": tid, "cellId": cell_id, "pathEvidence": next_path, "SDD": {}} if evidence.get("sddConstantEmptyObject") else {"transitionId": tid, "cellId": cell_id, "pathEvidence": next_path},
                        sequence=tuple(next_path), provenance=(f"T3:{contract_id}:{cell_id}",)))
                except MappingBlocked as exc:
                    blocked.append({"cellId": cell_id, "transitionId": tid, "path": next_path, "classification": exc.blocked_reason.split("_")[0] if exc.blocked_reason else "blocked", "blocked_reason": exc.blocked_reason, "details": exc.details})
            queue.append((str(tr.get("to")), next_path))
    suite = Suite("T3", cases)
    report = {"kind": "t3-real-parametric-mapper-report", "contractId": contract_id, "modelPath": str(model_path), "modelSha256": _sha256_bytes(model_bytes), "mappingPath": str(mapping_path), "mappingSha256": _sha256_bytes(mapping_bytes), "fixturesPath": str(fixtures_path), "fixturesSha256": _sha256_bytes(fixtures_bytes), "schemaPath": str(schema_path), "schemaSha256": _sha256_bytes(schema_bytes), "selection": "BFS over explicit mapping cells only", "acceptedCount": len(cases), "blockedCount": len(blocked), "blocked": blocked, "officialCampaign": False, "inventedValues": False}
    return suite, report


def compatibility_inventory(matrix: dict[str, Any]) -> dict[str, Any]:
    cells = []
    totals = Counter()
    structural_not_expressible = {"not_expressible", "precondition_indeterminate", "observation_inadmissible", "not_mapped"}
    for cell in _load_cells(matrix):
        t3_use = cell.get("matrixGenerativeUse")
        selector_ok = cell.get("selectorUsableForGeneration") is True
        body = cell.get("requestBody")
        applicability = cell.get("applicabilityStatus")
        sdd = bool(cell.get("sddConstantEmptyObject")) or (body == {} and str(cell.get("contractId", "")).startswith("E3"))
        missing: list[str] = []
        classification = "supported"
        if applicability in structural_not_expressible:
            classification = "not_expressible"
            missing.append(f"applicabilityStatus={applicability}")
        elif applicability == "conditioned_on_external_fixture" and not cell.get("candidateFixtures"):
            classification = "missing_fixture_variant"
            missing.append("candidate fixture variant")
        else:
            if t3_use != "candidate_mapping_only_unexercised":
                missing.append("generativeUse=candidate_mapping_only_unexercised")
            if not selector_ok:
                missing.append("selectorUsableForGeneration")
            if body == "deterministic_from_allowed_schema_fields_when_case_is_later_frozen":
                classification = "implementation_missing"
                missing.append("explicit requestBody selector object")
            if not sdd and not isinstance(body, dict):
                classification = "implementation_missing"
                missing.append("requestBody object")
            if not cell.get("operation", {}).get("method") or not cell.get("operation", {}).get("path"):
                classification = "implementation_missing"
                missing.append("operation method/path")
            if not sdd and cell.get("candidateFixtures") and not cell.get("fixtureSelection"):
                classification = "implementation_missing"
                missing.append("external fixtureSelection.fixtureId")
            if sdd and cell.get("operation", {}).get("requestSchema") and not _is_closed_empty_object_schema(cell["operation"]["requestSchema"]):
                classification = "implementation_missing"
                missing.append("closed empty object schema evidence")
            if missing and classification == "supported":
                classification = "implementation_missing"
        totals[classification] += 1
        status = "supported" if classification == "supported" else "blocked"
        cells.append({"cellId": cell.get("cellId"), "obligationId": cell.get("obligationId"), "contractId": cell.get("contractId"), "track": cell.get("track"), "operationPath": (cell.get("operation") or {}).get("path"), "status": status, "classification": classification, "sddConstantEmptyObject": sdd and status == "supported", "minimumMissing": missing})
    for key in ("supported", "implementation_missing", "not_expressible", "missing_fixture_variant"):
        totals.setdefault(key, 0)
    return {"kind": "t3-static-compatibility-inventory", "totals": dict(totals), "cells": cells, "officialCampaign": False}


def freeze_load_synthetic(suite: Suite, output_dir: Path) -> tuple[Suite, dict[str, Any]]:
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise T3MapperError(f"refusing to overwrite output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    path = output_dir / "T3.json"
    freeze_suite(suite, path)
    loaded = load_frozen_suite(path)
    report = {"kind": "t3-freeze-load-synthetic-report", "suitePath": str(path), "suiteId": loaded.suite_id, "caseCount": len(loaded.cases), "officialCampaign": False}
    (output_dir / "freeze-load-report.json").write_bytes(_json_bytes(report))
    return loaded, report


def freeze_load_union_synthetic(suites: Iterable[Suite], output_dir: Path) -> tuple[Suite, dict[str, Any]]:
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise T3MapperError(f"refusing to overwrite output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    loaded = []
    counts = {}
    for suite in suites:
        p = output_dir / f"{suite.suite_id}.json"
        freeze_suite(suite, p)
        s = load_frozen_suite(p)
        loaded.append(s); counts[s.suite_id] = len(s.cases)
    union, ledger = UnionBuilder().build(loaded)
    up = output_dir / "T4-union.json"
    freeze_suite(union, up)
    union_loaded = load_frozen_suite(up)
    report = {"kind": "t3-freeze-load-union-synthetic-report", "loadedCounts": counts, "unionSuiteId": union_loaded.suite_id, "unionCaseCount": len(union_loaded.cases), "ledgerCounts": dict(Counter(row["action"] for row in ledger)), "officialCampaign": False}
    (output_dir / "union-report.json").write_bytes(_json_bytes(report))
    return union_loaded, report

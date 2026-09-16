from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml

try:
    from campaign_harness import Case, Expectation, HttpRequestSpec, Suite
except ModuleNotFoundError:  # pragma: no cover - caller should set campaign harness path
    raise


class AdapterError(Exception):
    pass


@dataclass(frozen=True)
class ContractSource:
    contract_id: str
    path: Path


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_bytes(path: Path) -> bytes:
    return Path(path).read_bytes()


def pin_contract_sources(sources: Iterable[ContractSource]) -> List[Dict[str, Any]]:
    pins = []
    for source in sources:
        data = _read_bytes(source.path)
        pins.append({
            "contractId": source.contract_id,
            "path": str(source.path),
            "bytes": len(data),
            "sha256": _sha256(data),
        })
    return pins


def _load_openapi(path: Path) -> Dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise AdapterError(f"contract is not an object: {path}")
    return data


def build_operation_inventory(sources: Iterable[ContractSource]) -> Dict[str, Any]:
    contract_rows = []
    operations = []
    for source in sources:
        data = _load_openapi(source.path)
        contract_ops = []
        for path, path_item in (data.get("paths") or {}).items():
            if not isinstance(path_item, dict):
                continue
            for method, operation in path_item.items():
                lower = str(method).lower()
                if lower not in {"get", "put", "post", "delete", "patch", "head", "options", "trace"}:
                    continue
                if not isinstance(operation, dict):
                    continue
                op = {
                    "contractId": source.contract_id,
                    "path": str(path),
                    "method": lower,
                    "operationId": str(operation.get("operationId", "")),
                    "documentedResponses": sorted(str(k) for k in (operation.get("responses") or {}).keys()),
                    "requestBodyRequired": bool((operation.get("requestBody") or {}).get("required", False)) if isinstance(operation.get("requestBody"), dict) else False,
                    "tags": [str(x) for x in operation.get("tags", [])] if isinstance(operation.get("tags"), list) else [],
                }
                operations.append(op)
                contract_ops.append({k: op[k] for k in ("path", "method", "operationId", "documentedResponses", "requestBodyRequired", "tags")})
        contract_rows.append({"contractId": source.contract_id, "path": str(source.path), "operationCount": len(contract_ops), "operations": contract_ops})
    return {
        "kind": "real-operation-inventory-from-pinned-contracts",
        "contractCount": len(contract_rows),
        "operationCount": len(operations),
        "contracts": contract_rows,
        "operations": operations,
    }


def _extract_first_jsonish(raw: str) -> Any:
    # Preserve raw separately; this only attempts to import explicit JSON from a frozen response.
    fenced = re.search(r"```(?:json)?\s*(.*?)```", raw, flags=re.DOTALL | re.IGNORECASE)
    candidates = [fenced.group(1)] if fenced else []
    candidates.append(raw)
    for text in candidates:
        stripped = text.strip()
        for start in ("[", "{"):
            idx = stripped.find(start)
            if idx < 0:
                continue
            try:
                return json.loads(stripped[idx:])
            except json.JSONDecodeError:
                continue
    raise AdapterError("no parseable JSON found in preserved response")


def _items_from_payload(payload: Any, key: str) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        for candidate in (key, "cases", "requests", "paths", "scenarios"):
            if isinstance(payload.get(candidate), list):
                items = payload[candidate]
                break
        else:
            items = [payload]
    else:
        raise AdapterError("payload is not object/list")
    return [item if isinstance(item, dict) else {"_invalid_item": item} for item in items]


def _body_to_kind_b64(item: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    if "body" not in item and "body_b64" not in item and "bodyBase64" not in item:
        return "absent", None
    body = item.get("body")
    if isinstance(body, dict) and "kind" in body:
        kind = str(body["kind"])
        if kind == "absent":
            return "absent", None
        if kind == "bytes":
            return "bytes", str(body.get("base64", body.get("body_b64", "")))
        if kind == "json":
            if "base64" in body:
                return "json", str(body["base64"])
            return "json", base64.b64encode(json.dumps(body.get("value"), separators=(",", ":"), ensure_ascii=False).encode("utf-8")).decode("ascii")
        raise ValueError(f"unsupported body kind: {kind}")
    if "body_b64" in item or "bodyBase64" in item:
        return str(item.get("body_kind", item.get("bodyKind", "bytes"))), str(item.get("body_b64", item.get("bodyBase64", "")))
    if body is None:
        return "bytes", ""
    if isinstance(body, (dict, list, str, int, float, bool)):
        return "json", base64.b64encode(json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).decode("ascii")
    raise ValueError("unsupported body value")


def _make_request(item: Dict[str, Any]) -> HttpRequestSpec:
    method = str(item.get("method", "POST"))
    path = item.get("path")
    if not isinstance(path, str):
        raise ValueError("missing path")
    headers_raw = item.get("headers", [])
    if isinstance(headers_raw, dict):
        headers = tuple((str(k), str(v)) for k, v in headers_raw.items())
    else:
        headers = tuple((str(k), str(v)) for k, v in headers_raw)
    kind, b64 = _body_to_kind_b64(item)
    return HttpRequestSpec(method, path, headers, kind, b64)


def _expectation(item: Dict[str, Any]) -> Expectation:
    if isinstance(item.get("expectation"), dict):
        exp = item["expectation"]
        return Expectation(str(exp.get("expectation_id", exp.get("id", "status"))), dict(exp.get("checks", {})))
    statuses = item.get("expectedStatus") or item.get("expected_status") or item.get("status") or [200, 400, 500, 503]
    if isinstance(statuses, int):
        statuses = [statuses]
    return Expectation(str(item.get("expectationId", "status")), {"status": [int(x) for x in statuses]})


def _case_from_item(contract_id: str, suite_id: str, item: Dict[str, Any], resource_package_id: str) -> Case:
    request = _make_request(item)
    original_id = str(item.get("id", item.get("case_id", item.get("request_id", len(str(item))))))
    safe_id = f"{suite_id}-{contract_id}-{original_id}"
    return Case(
        case_id=safe_id,
        suite_id=suite_id,
        origin=f"{suite_id}:{contract_id}",
        request=request,
        resource_package_id=str(item.get("resourcePackageId", resource_package_id)),
        expectation=_expectation(item),
        timeout_seconds=float(item.get("timeoutSeconds", item.get("timeout_seconds", 5.0))),
        parameters=dict(item.get("parameters", {})) if isinstance(item.get("parameters", {}), dict) else {},
        sequence=tuple(str(x) for x in item.get("sequence", [])) if isinstance(item.get("sequence", []), list) else (),
        provenance=(f"{suite_id}:{contract_id}:{original_id}",),
    )


def _import_items(contract_id: str, items: List[Dict[str, Any]], suite_id: str, resource_package_id: str, *, t3: bool = False) -> Tuple[Suite, Dict[str, Any]]:
    cases = []
    rejected = []
    for idx, item in enumerate(items):
        if t3 and ("path" not in item or "method" not in item):
            rejected.append({"index": idx, "id": item.get("id"), "classification": "blocked_missing_business_request_mapping", "input_keys": sorted(str(k) for k in item.keys())})
            continue
        if "path" not in item and "method" not in item and "body" not in item:
            rejected.append({"index": idx, "id": item.get("id"), "classification": "not_mapped_missing_request", "input_keys": sorted(str(k) for k in item.keys())})
            continue
        try:
            cases.append(_case_from_item(contract_id, suite_id, item, resource_package_id))
        except Exception as exc:
            rejected.append({"index": idx, "id": item.get("id"), "classification": "invalid_request", "error": str(exc), "input_keys": sorted(str(k) for k in item.keys())})
    report = {
        "contractId": contract_id,
        "suiteId": suite_id,
        "acceptedCount": len(cases),
        "rejectedCount": len(rejected),
        "rejected": rejected,
    }
    return Suite(suite_id, cases), report


def import_t1_preserved_response(contract_id: str, response_path: Path, *, suite_id: str = "T1", default_resource_package_id: str = "default") -> Tuple[Suite, Dict[str, Any]]:
    raw_bytes = _read_bytes(response_path)
    raw = raw_bytes.decode("utf-8")
    payload = _extract_first_jsonish(raw)
    suite, report = _import_items(contract_id, _items_from_payload(payload, "scenarios"), suite_id, default_resource_package_id)
    report.update({
        "sourcePath": str(response_path),
        "source_sha256": _sha256(raw_bytes),
        "source_bytes": len(raw_bytes),
        "raw_response": raw,
        "llm_called": False,
        "repaired_omissions": False,
    })
    return suite, report


def import_t2_frozen_requests(contract_id: str, frozen_path: Path, *, suite_id: str = "T2", default_resource_package_id: str = "default") -> Tuple[Suite, Dict[str, Any]]:
    data = _read_bytes(frozen_path)
    payload = json.loads(data.decode("utf-8"))
    suite, report = _import_items(contract_id, _items_from_payload(payload, "requests"), suite_id, default_resource_package_id)
    report.update({"sourcePath": str(frozen_path), "source_sha256": _sha256(data), "source_bytes": len(data), "http_called": False, "offline_import_only": True})
    return suite, report


def import_t3_external_paths(contract_id: str, paths_path: Path, *, suite_id: str = "T3", default_resource_package_id: str = "default") -> Tuple[Suite, Dict[str, Any]]:
    data = _read_bytes(paths_path)
    payload = json.loads(data.decode("utf-8"))
    suite, report = _import_items(contract_id, _items_from_payload(payload, "paths"), suite_id, default_resource_package_id, t3=True)
    report.update({"sourcePath": str(paths_path), "source_sha256": _sha256(data), "source_bytes": len(data), "oracle_accessed": False, "abstract_id_conversion": "blocked_without_external_mapping"})
    return suite, report

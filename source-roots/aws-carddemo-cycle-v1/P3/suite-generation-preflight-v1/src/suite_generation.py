from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
import time
from collections import Counter, deque
from importlib.metadata import version
from pathlib import Path
from typing import Any, Iterable

import schemathesis
from hypothesis import Phase, given, seed as hyp_seed, settings
from schemathesis.generation import GenerationMode

P3 = Path(__file__).resolve().parents[2]
HARNESS_SRC = P3 / "campaign-harness-v3" / "src"
if str(HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(HARNESS_SRC))

import campaign_harness  # noqa: E402
from campaign_harness import Case, Expectation, HttpRequestSpec, Suite, UnionBuilder, freeze_suite, load_frozen_suite  # noqa: E402


class SuiteGenerationError(Exception):
    pass


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(Path(path).read_bytes())


def _json_bytes(data: Any) -> bytes:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")


def module_evidence() -> dict[str, Any]:
    this = Path(__file__).resolve()
    harness = Path(campaign_harness.__file__).resolve()
    expected = (HARNESS_SRC / "campaign_harness.py").resolve()
    if harness != expected:
        raise SuiteGenerationError(f"wrong harness module path: {harness} != {expected}")
    return {
        "suiteGeneration": {"module": __name__, "file": str(this), "sha256": _sha256_path(this)},
        "harnessV3": {"module": campaign_harness.__name__, "file": str(harness), "sha256": _sha256_path(harness)},
    }


def build_t1_outbound_package(*, contract_id: str, contract_path: Path, output_dir: Path, common_instruction: str, supported_parameters: dict[str, Any]) -> dict[str, Any]:
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise SuiteGenerationError(f"refusing to overwrite output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    contract_bytes = Path(contract_path).read_bytes()
    package = {
        "kind": "t1-outbound-package-preparation-only",
        "version": "suite-generation-preflight-v1.t1.1",
        "contractId": contract_id,
        "contract": {"path": str(contract_path), "bytes": len(contract_bytes), "sha256": _sha256_bytes(contract_bytes), "contentUtf8": contract_bytes.decode("utf-8")},
        "commonInstruction": common_instruction,
        "supportedParameters": supported_parameters,
        "supportedParametersStatus": "declared_pending_not_probed",
        "providerCalled": False,
        "modelAvailability": "not_probed",
        "probeStatus": "not_called",
        "externalPackageStatus": "pending_approval",
        "limits": ["preparation only", "no provider/model call", "no official cases generated"],
    }
    (output_dir / "t1-outbound-package.json").write_bytes(_json_bytes(package))
    return package


def _extract_first_jsonish(raw: str) -> Any:
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
    raise SuiteGenerationError("no parseable JSON found; raw preserved but not repaired")


def _items_from_payload(payload: Any, key: str) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        raw = payload
    elif isinstance(payload, dict):
        for candidate in (key, "cases", "requests", "paths", "scenarios"):
            value = payload.get(candidate)
            if isinstance(value, list):
                raw = value
                break
        else:
            raw = [payload]
    else:
        raise SuiteGenerationError("payload is not object/list")
    return [x if isinstance(x, dict) else {"_invalid_item": x} for x in raw]


def _body_to_kind_b64(item: dict[str, Any]) -> tuple[str, str | None]:
    if "body" not in item and "body_b64" not in item and "bodyBase64" not in item:
        return "absent", None
    if "body_b64" in item or "bodyBase64" in item:
        return str(item.get("body_kind", item.get("bodyKind", "bytes"))), str(item.get("body_b64", item.get("bodyBase64", "")))
    body = item.get("body")
    if isinstance(body, dict) and "kind" in body:
        kind = str(body["kind"])
        if kind == "absent":
            return "absent", None
        if kind in {"bytes", "json"}:
            b64 = body.get("base64") or body.get("body_b64")
            if b64 is None and kind == "json":
                b64 = base64.b64encode(json.dumps(body.get("value"), separators=(",", ":"), ensure_ascii=False).encode()).decode("ascii")
            if b64 is None:
                raise ValueError("present body missing base64")
            return kind, str(b64)
        raise ValueError(f"unsupported body kind: {kind}")
    if body is None:
        return "bytes", ""
    if isinstance(body, (dict, list, str, int, float, bool)):
        return "json", base64.b64encode(json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode()).decode("ascii")
    raise ValueError("unsupported body value")


def _make_request(item: dict[str, Any]) -> HttpRequestSpec:
    if not isinstance(item.get("method"), str) or not isinstance(item.get("path"), str):
        raise ValueError("missing concrete method/path")
    headers_raw = item.get("headers", [("content-type", "application/json")])
    if isinstance(headers_raw, dict):
        headers = tuple((str(k), str(v)) for k, v in headers_raw.items())
    else:
        headers = tuple((str(k), str(v)) for k, v in headers_raw)
    kind, b64 = _body_to_kind_b64(item)
    return HttpRequestSpec(str(item["method"]), str(item["path"]), headers, kind, b64)


def _expectation(item: dict[str, Any]) -> Expectation:
    if isinstance(item.get("expectation"), dict):
        e = item["expectation"]
        return Expectation(str(e.get("expectation_id", e.get("id", "status"))), dict(e.get("checks", {})))
    statuses = item.get("expectedStatus", item.get("expected_status", item.get("status", [200, 400, 500, 503])))
    if isinstance(statuses, int):
        statuses = [statuses]
    return Expectation(str(item.get("expectationId", "status")), {"status": [int(x) for x in statuses]})


def _import_items(contract_id: str, suite_id: str, items: list[dict[str, Any]], *, resource_package_id: str = "synthetic") -> tuple[Suite, dict[str, Any]]:
    cases: list[Case] = []
    invalid: list[dict[str, Any]] = []
    for idx, item in enumerate(items):
        if not (isinstance(item.get("method"), str) and isinstance(item.get("path"), str)):
            invalid.append({"index": idx, "id": item.get("id"), "classification": "not_mapped_missing_request", "inputKeys": sorted(map(str, item.keys()))})
            continue
        try:
            original_id = str(item.get("id", item.get("case_id", idx)))
            cases.append(Case(
                case_id=f"{suite_id}-{contract_id}-{original_id}",
                suite_id=suite_id,
                origin=f"{suite_id}:{contract_id}",
                request=_make_request(item),
                resource_package_id=str(item.get("resourcePackageId", resource_package_id)),
                expectation=_expectation(item),
                timeout_seconds=float(item.get("timeoutSeconds", 5.0)),
                parameters=dict(item.get("parameters", {})) if isinstance(item.get("parameters"), dict) else {},
                sequence=tuple(str(x) for x in item.get("sequence", [])) if isinstance(item.get("sequence"), list) else (),
                provenance=(f"{suite_id}:{contract_id}:{original_id}",),
            ))
        except Exception as exc:
            invalid.append({"index": idx, "id": item.get("id"), "classification": "invalid_request", "error": str(exc), "inputKeys": sorted(map(str, item.keys()))})
    report = {"contractId": contract_id, "suiteId": suite_id, "inputCount": len(items), "acceptedCount": len(cases), "invalidCount": len(invalid), "invalid": invalid}
    return Suite(suite_id, cases), report


def import_t1_preserved_response(contract_id: str, response_path: Path, *, suite_id: str = "T1") -> tuple[Suite, dict[str, Any]]:
    raw_bytes = Path(response_path).read_bytes()
    raw = raw_bytes.decode("utf-8")
    payload = _extract_first_jsonish(raw)
    suite, report = _import_items(contract_id, suite_id, _items_from_payload(payload, "scenarios"))
    report.update({"sourcePath": str(response_path), "sourceSha256": _sha256_bytes(raw_bytes), "sourceBytes": len(raw_bytes), "rawResponse": raw, "providerCalled": False, "repairedOrCompleted": False})
    return suite, report


SYNTHETIC_OPENAPI_31 = {
    "openapi": "3.1.0",
    "info": {"title": "Synthetic 3.1 qualification schema; NOT CardDemo", "version": "1.0.0"},
    "paths": {"/synthetic": {"post": {"operationId": "syntheticPost", "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "additionalProperties": False}}}}, "responses": {"200": {"description": "ok"}, "400": {"description": "synthetic invalid"}, "500": {"description": "documented synthetic error"}}}}},
}


def generate_t2_schemathesis_suite(contract_id: str, schema_path: Path, output_dir: Path, *, seeds: list[int], directions: list[str], max_examples_per_direction: int = 100, qualification_max_examples_per_direction: int = 12) -> dict[str, Any]:
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise SuiteGenerationError(f"refusing to overwrite output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    budget = min(int(max_examples_per_direction), int(qualification_max_examples_per_direction))
    if budget <= 0:
        raise SuiteGenerationError("budget must be positive")
    Path(schema_path).write_text(json.dumps(SYNTHETIC_OPENAPI_31, indent=2), encoding="utf-8")
    schema = schemathesis.openapi.from_dict(SYNTHETIC_OPENAPI_31)
    operation = schema["/synthetic"]["POST"]
    mode_by_name = {"positive": GenerationMode.POSITIVE, "negative": GenerationMode.NEGATIVE}
    requests: list[dict[str, Any]] = []
    generation: list[dict[str, Any]] = []
    http_calls = 0
    for seed_value in seeds:
        for direction in directions:
            if direction not in mode_by_name:
                raise SuiteGenerationError(f"unsupported direction: {direction}")
            batch = []

            @hyp_seed(int(seed_value))
            @settings(max_examples=budget, phases=(Phase.generate,), database=None, deadline=None)
            @given(operation.as_strategy(generation_mode=mode_by_name[direction]))
            def collect(case):
                batch.append(case)

            started = time.monotonic()
            collect()
            generation.append({"seed": seed_value, "direction": direction, "generated": len(batch), "maxExamples": budget, "seconds": time.monotonic() - started})
            for idx, case in enumerate(batch):
                req = case.as_transport_kwargs(base_url="http://127.0.0.1")
                raw_body = req.get("data", req.get("json", None))
                if isinstance(raw_body, bytes):
                    try:
                        body = json.loads(raw_body.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        body = {"kind": "bytes", "base64": base64.b64encode(raw_body).decode("ascii")}
                elif isinstance(raw_body, str):
                    try:
                        body = json.loads(raw_body)
                    except json.JSONDecodeError:
                        body = raw_body
                elif raw_body is None:
                    body = {}
                else:
                    body = raw_body
                requests.append({"id": f"seed{seed_value}-{direction}-{idx}", "method": req["method"], "path": "/synthetic", "headers": {"content-type": "application/json"}, "body": body, "expectedStatus": [200, 400, 500], "parameters": {"seed": seed_value, "direction": direction}})
    frozen = {"kind": "t2-schemathesis-offline-frozen-requests", "schema": "synthetic3.1", "requests": requests}
    frozen_bytes = _json_bytes(frozen)
    (output_dir / "frozen-synthetic3.1-requests.json").write_bytes(frozen_bytes)
    report = {"kind": "t2-schemathesis-offline-generation-report", "contractId": contract_id, "schemathesisVersion": version("schemathesis"), "hypothesisVersion": version("hypothesis"), "schemaPath": str(schema_path), "frozenRequestsPath": str(output_dir / "frozen-synthetic3.1-requests.json"), "frozenRequestsSha256": _sha256_bytes(frozen_bytes), "generation": generation, "directions": directions, "seeds": seeds, "requestedMaxExamplesPerDirection": max_examples_per_direction, "qualificationMaxExamplesPerDirection": qualification_max_examples_per_direction, "effectiveMaxExamplesPerDirection": budget, "hypothesisPhases": ["generate"], "hypothesisDatabase": None, "shrinking": False, "replayDuringGeneration": False, "httpCallsDuringGeneration": http_calls, "officialCampaign": False}
    (output_dir / "t2-report.json").write_bytes(_json_bytes(report))
    return report


def import_t2_frozen_suite(contract_id: str, frozen_path: Path, *, suite_id: str = "T2") -> tuple[Suite, dict[str, Any]]:
    data = Path(frozen_path).read_bytes()
    payload = json.loads(data.decode("utf-8"))
    suite, report = _import_items(contract_id, suite_id, _items_from_payload(payload, "requests"))
    report.update({"sourcePath": str(frozen_path), "sourceSha256": _sha256_bytes(data), "sourceBytes": len(data), "offlineImportOnly": True, "httpReplayExtra": 0})
    return suite, report


def _guard_supported(guard: dict[str, Any]) -> bool:
    return guard.get("op") in {"true", "eq", "ne", "and", "or", "not", "in", "gte", "lte", "unknown"}


def _transition_order(cap: dict[str, Any], state_id: str) -> list[dict[str, Any]]:
    return sorted([t for t in cap.get("transitions", []) if t.get("from") == state_id], key=lambda t: str(t.get("id")))


def _get_cap(model: dict[str, Any], cap_id: str) -> dict[str, Any]:
    for cap in model.get("capabilities", []):
        if cap.get("id") == cap_id:
            return cap
    raise SuiteGenerationError(f"capability not found: {cap_id}")


def generate_t3_bfs_suite(contract_id: str, model_path: Path, mapping_path: Path, *, capability_id: str | None = None, max_depth: int = 8, max_paths: int = 50) -> tuple[Suite, dict[str, Any]]:
    model_bytes = Path(model_path).read_bytes(); mapping_bytes = Path(mapping_path).read_bytes()
    model = json.loads(model_bytes.decode("utf-8")); mapping = json.loads(mapping_bytes.decode("utf-8"))
    cap = _get_cap(model, capability_id or model.get("capabilities", [{}])[0].get("id"))
    allowed = mapping.get("allowed", {})
    guard_sensitive = mapping.get("guardSensitive", {})
    abstract_only = mapping.get("abstractOnly", {})
    queue = deque([(cap["initialState"], [])])
    visited_steps = 0
    cases: list[Case] = []
    blocked: list[dict[str, Any]] = []
    seen_transitions: set[str] = set()
    while queue and visited_steps < max_paths:
        state, path = queue.popleft()
        if len(path) >= max_depth:
            continue
        for tr in _transition_order(cap, state):
            tid = str(tr["id"])
            if tid in seen_transitions:
                continue
            seen_transitions.add(tid)
            visited_steps += 1
            if tid in guard_sensitive and not guard_sensitive[tid].get("supported", False):
                blocked.append({"transitionId": tid, "path": path + [tid], "classification": "blocked_guard_or_variant_without_v3_support", "rule": "applicability-mapping-v3 fail-closed"})
            elif not _guard_supported(tr.get("guard", {})):
                blocked.append({"transitionId": tid, "path": path + [tid], "classification": "blocked_guard_or_variant_without_v3_support", "rule": "unsupported guard op"})
                if tid in abstract_only or tid not in allowed:
                    blocked.append({"transitionId": tid, "path": path + [tid], "classification": "blocked_abstract_without_concrete_mapping", "reason": (abstract_only.get(tid) or {}).get("reason", "no concrete allowed mapping")})
            elif tid in abstract_only or tid not in allowed:
                blocked.append({"transitionId": tid, "path": path + [tid], "classification": "blocked_abstract_without_concrete_mapping", "reason": (abstract_only.get(tid) or {}).get("reason", "no concrete allowed mapping")})
            else:
                item = dict(allowed[tid])
                item.setdefault("id", tid)
                item.setdefault("expectedStatus", [200, 400, 500, 503])
                case = Case(case_id=f"T3-{contract_id}-{tid}", suite_id="T3", origin=f"T3:{contract_id}", request=_make_request(item), resource_package_id=str(item.get("resourcePackageId", "synthetic")), expectation=_expectation(item), timeout_seconds=float(item.get("timeoutSeconds", 5.0)), parameters={"transitionId": tid, "capabilityId": cap["id"]}, sequence=tuple(path + [tid]), provenance=(f"T3:{contract_id}:{tid}",))
                cases.append(case)
            queue.append((str(tr["to"]), path + [tid]))
    suite = Suite("T3", cases)
    report = {"kind": "t3-synthetic-bfs-generation-report", "contractId": contract_id, "capabilityId": cap["id"], "modelPath": str(model_path), "modelSha256": _sha256_bytes(model_bytes), "mappingPath": str(mapping_path), "mappingSha256": _sha256_bytes(mapping_bytes), "selection": "deterministic BFS, lexicographic transition ID", "acceptedCount": len(cases), "blockedCount": len({row["transitionId"] for row in blocked}), "blockedRecordCount": len(blocked), "blocked": blocked, "abstractConversion": "never invent request from abstract transition", "applicabilityV3Rule": "guard/variant without documented support is blocked"}
    return suite, report


def freeze_load_union(suites: Iterable[Suite], output_dir: Path) -> tuple[Suite, dict[str, Any]]:
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise SuiteGenerationError(f"refusing to overwrite output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    evidence = module_evidence()
    loaded: list[Suite] = []
    freeze_paths: dict[str, str] = {}
    loaded_counts: dict[str, int] = {}
    for suite in suites:
        path = output_dir / f"{suite.suite_id}.json"
        freeze_suite(suite, path)
        loaded_suite = load_frozen_suite(path)
        loaded.append(loaded_suite)
        freeze_paths[suite.suite_id] = str(path)
        loaded_counts[suite.suite_id] = len(loaded_suite.cases)
    union, ledger = UnionBuilder().build(loaded)
    union_path = output_dir / "T4-union.json"
    freeze_suite(union, union_path)
    union_loaded = load_frozen_suite(union_path)
    ledger_counts = dict(Counter(row["action"] for row in ledger))
    report = {"kind": "suite-generation-freeze-load-union-report", "harnessModule": evidence["harnessV3"], "freezePaths": freeze_paths, "loadedCounts": loaded_counts, "unionPath": str(union_path), "unionSuiteId": union_loaded.suite_id, "unionCaseCount": len(union_loaded.cases), "ledger": ledger, "ledgerCounts": ledger_counts}
    (output_dir / "union-report.json").write_bytes(_json_bytes(report))
    return union_loaded, report

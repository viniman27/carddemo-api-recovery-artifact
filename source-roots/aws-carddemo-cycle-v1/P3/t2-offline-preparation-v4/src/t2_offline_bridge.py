from __future__ import annotations

import base64
import hashlib
import json
import sys
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

import schemathesis
from hypothesis import Phase, given, seed as hyp_seed, settings
from schemathesis.generation import GenerationMode

try:  # YAML is needed for original OpenAPI files that are not JSON.
    import yaml
except ModuleNotFoundError:  # pragma: no cover - fuzz venv has PyYAML via existing project deps
    yaml = None

THIS = Path(__file__).resolve()
P3 = THIS.parents[2]
HARNESS_SRC = P3 / "campaign-harness-v3" / "src"
ADAPTER_SRC = P3 / "unified-preflight-v3" / "src"
SUITE_GEN_SRC = P3 / "suite-generation-preflight-v1" / "src"
for _path in (HARNESS_SRC, ADAPTER_SRC, SUITE_GEN_SRC):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from campaign_harness import freeze_suite, load_frozen_suite  # noqa: E402
from suite_adapters import import_t2_frozen_requests  # noqa: E402
import suite_generation  # noqa: E402  # imported deliberately to reuse the existing preflight module/evidence path


DEFAULT_SEEDS = [104729, 130363, 155921]
DIRECTIONS = ["positive", "negative"]
MODE_BY_DIRECTION = {"positive": GenerationMode.POSITIVE, "negative": GenerationMode.NEGATIVE}
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
TRACK_FIXTURE_DEFAULTS = {
    "posting": "posting.candidate-v1-physical-v2",
    "interest": "interest.candidate-v1-physical-v2",
    "reporting": "reporting.candidate-v1-physical-v2",
}
TRACK_ALIASES = {
    "posting": "posting",
    "postdailytransactions": "posting",
    "postdailytransaction": "posting",
    "posttransaction": "posting",
    "transactionposting": "posting",
    "interest": "interest",
    "generateinteresttransactions": "interest",
    "generateinteresttransaction": "interest",
    "interesttransaction": "interest",
    "reporting": "reporting",
    "generatetransactionreport": "reporting",
    "transactionreport": "reporting",
}


class T2OfflineBridgeError(Exception):
    pass


def _json_bytes(data: Any) -> bytes:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(Path(path).read_bytes())


def load_current_config(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_openapi(path: Path) -> dict[str, Any]:
    data = Path(path).read_bytes()
    text = data.decode("utf-8")
    if path.suffix.lower() == ".json":
        obj = json.loads(text)
        if isinstance(obj, dict) and isinstance(obj.get("text"), str):
            if yaml is None:
                raise T2OfflineBridgeError("PyYAML unavailable for wrapped OpenAPI text")
            obj = yaml.safe_load(obj["text"])
    else:
        if yaml is None:
            raise T2OfflineBridgeError("PyYAML unavailable for non-JSON OpenAPI")
        obj = yaml.safe_load(text)
    if not isinstance(obj, dict) or "paths" not in obj:
        raise T2OfflineBridgeError(f"not an OpenAPI object: {path}")
    return obj


def _check_pin(row: dict[str, Any]) -> str | None:
    path = Path(str(row.get("path", "")))
    if not path.exists():
        return f"missing: {path}"
    data = path.read_bytes()
    actual_sha = _sha256_bytes(data)
    actual_bytes = len(data)
    if actual_sha != row.get("sha256") or actual_bytes != row.get("bytes"):
        return f"pin mismatch: {path} actual bytes={actual_bytes} sha256={actual_sha}"
    return None


def validate_current_registry(cfg: dict[str, Any], *, expected_contracts: int | None = 7, expected_operations: int | None = 21) -> dict[str, Any]:
    errors: list[str] = []
    failed_pins: list[str] = []
    auth = cfg.get("authorization", {})
    if auth.get("officialCampaignsStarted") is not False:
        errors.append("officialCampaignsStarted must remain false")
    if auth.get("externalT1SendAuthorized") is not False:
        errors.append("externalT1SendAuthorized must remain false without specific consent")
    if auth.get("campaignAuthorized") is not False:
        errors.append("campaignAuthorized must remain boolean false")

    contract_block = cfg.get("contracts", {})
    contracts = contract_block.get("contracts", [])
    op_total = sum(int(c.get("operationCount", 0)) for c in contracts)
    if expected_contracts is not None and (len(contracts) != expected_contracts or contract_block.get("count") != expected_contracts):
        errors.append(f"contract count must be exactly {expected_contracts}")
    if expected_operations is not None and (op_total != expected_operations or contract_block.get("operationsTotal") != expected_operations):
        errors.append(f"operation count must be exactly {expected_operations} total")
    seen_ids: set[str] = set()
    for contract in contracts:
        cid = str(contract.get("contractId", ""))
        if not cid or cid in seen_ids:
            errors.append(f"contractId duplicate/missing: {cid!r}")
        seen_ids.add(cid)
        operations = contract.get("operations", [])
        if int(contract.get("operationCount", -1)) != len(operations):
            errors.append(f"operationCount mismatch for {cid}")
        pin_error = _check_pin(contract.get("source", {}))
        if pin_error:
            failed_pins.append(f"{cid}: {pin_error}")
        for op in operations:
            if str(op.get("method", "")).lower() not in HTTP_METHODS:
                errors.append(f"unsupported method in {cid}: {op.get('method')}")
            if not str(op.get("path", "")).startswith("/"):
                errors.append(f"operation path must be absolute in {cid}: {op.get('path')}")
            if not op.get("documentedResponses"):
                errors.append(f"operation without documentedResponses in {cid}: {op.get('operationId')}")
    for row in cfg.get("sources", []):
        pin_error = _check_pin(row)
        if pin_error:
            failed_pins.append(f"{row.get('id')}: {pin_error}")
    errors.extend(failed_pins)
    return {
        "ok": not errors,
        "errors": errors,
        "failedPins": failed_pins,
        "contractCount": len(contracts),
        "operationCount": op_total,
        "authorization": {
            "officialCampaignsStarted": auth.get("officialCampaignsStarted"),
            "externalT1SendAuthorized": auth.get("externalT1SendAuthorized"),
            "campaignAuthorized": auth.get("campaignAuthorized"),
            "probeAuthorizedNow": auth.get("probeAuthorizedNow"),
        },
    }


def build_plan(cfg: dict[str, Any], *, max_examples_per_direction: int = 50, seeds: list[int] | None = None) -> dict[str, Any]:
    seeds = list(DEFAULT_SEEDS if seeds is None else seeds)
    registry = validate_current_registry(cfg)
    contracts = cfg.get("contracts", {}).get("contracts", [])
    return {
        "kind": "t2-offline-preparation-v4-plan",
        "version": "3.0-local-candidate",
        "officialCampaign": False,
        "networkAllowed": False,
        "dryRunDefault": True,
        "registryValidation": registry,
        "contracts": len(contracts),
        "operations": sum(len(c.get("operations", [])) for c in contracts),
        "policy": {
            "tool": "Schemathesis",
            "schemathesisVersion": version("schemathesis"),
            "hypothesisVersion": version("hypothesis"),
            "seeds": seeds,
            "perOperationPerSeed": {"positive": max_examples_per_direction, "negative": max_examples_per_direction, "total": max_examples_per_direction * 2},
            "budgetUnit": "operation × seed × direction",
            "budgetTransfer": "disabled",
            "retries": "disabled",
            "generationReplay": "disabled",
            "hypothesisDatabase": None,
            "shrinkingDuringGeneration": False,
            "occurrencesAreNotDiversity": True,
        },
        "reset": {"default": "fresh_dir_per_application", "genericRunReset": False, "beforeAfterHashChecks": "required_for_official_freeze"},
        "union": {"order": ["T1", "T2", "T3"], "status": "blocked_until_T1_T2_T3_official_suites_exist", "independentReplica": False},
        "t3Candidate": {"candidate": "P3/t3-mapping-integration-v2", "promoted": False},
        "errorPolicy": {"failClosedOnPinMismatch": True, "noRepairOfGeneratedRequests": True, "generationExceptionsPreservedAsPartial": True, "noSuccessFabrication": True},
        "blockers": [
            "Official release/generation remains gate-closed in this CLI.",
            "No network, campaign replay, external T1 send, COBOL/API request or oracle generation is performed by dry-run.",
            "T3 v2 may be pinned as candidate configuration only; it is not promoted here.",
        ],
    }


def _contract_row(cfg: dict[str, Any], contract_id: str) -> dict[str, Any]:
    rows = [c for c in cfg.get("contracts", {}).get("contracts", []) if c.get("contractId") == contract_id]
    if len(rows) != 1:
        raise T2OfflineBridgeError(f"contractId must resolve to exactly one row: {contract_id}")
    return rows[0]


def _operation_rows(contract: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for op in contract.get("operations", []):
        method = str(op.get("method", "")).lower()
        path = str(op.get("path", ""))
        if method in HTTP_METHODS and path.startswith("/"):
            rows.append(op)
    return rows


def _operation_track(operation: dict[str, Any]) -> str:
    for value in (operation.get("operationId"), operation.get("path"), operation.get("track")):
        if not value:
            continue
        normalized = "".join(ch for ch in str(value).lower() if ch.isalnum())
        if normalized in TRACK_ALIASES:
            return TRACK_ALIASES[normalized]
        for token, track in (("posting", "posting"), ("post", "posting"), ("interest", "interest"), ("report", "reporting")):
            if token in normalized:
                return track
    raise T2OfflineBridgeError(f"cannot infer fixture track for operation: {operation}")


def _resource_package_id_for_operation(cfg: dict[str, Any], operation: dict[str, Any]) -> str:
    try:
        track = _operation_track(operation)
    except T2OfflineBridgeError:
        if int(((cfg.get("contracts") or {}).get("count") or 0)) == 7:
            raise
        return "t2-offline-preparation-v4"
    configured = {str(row.get("track")): str(row.get("fixtureId")) for row in (((cfg.get("fixturesCandidates") or {}).get("fixtures")) or []) if row.get("track") and row.get("fixtureId")}
    package_id = configured.get(track, TRACK_FIXTURE_DEFAULTS[track])
    if package_id not in TRACK_FIXTURE_DEFAULTS.values():
        raise T2OfflineBridgeError(f"unexpected fixture package for {track}: {package_id}")
    return package_id


def _headers_list(headers_raw: Any) -> list[list[str]]:
    if headers_raw is None:
        return []
    if isinstance(headers_raw, dict) or hasattr(headers_raw, "items"):
        return [[str(k), str(v)] for k, v in headers_raw.items()]
    result = []
    for item in headers_raw:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            result.append([str(item[0]), str(item[1])])
        else:
            raise T2OfflineBridgeError(f"unsupported header representation: {item!r}")
    return result


def _body_kind_b64_from_transport(req: dict[str, Any]) -> tuple[str, str | None]:
    if "data" in req:
        raw = req.get("data")
        if raw is None:
            data = b""
        elif isinstance(raw, bytes):
            data = raw
        elif isinstance(raw, str):
            data = raw.encode("utf-8")
        else:
            data = bytes(raw)
        return "bytes", base64.b64encode(data).decode("ascii")
    if "json" in req:
        data = json.dumps(req.get("json"), separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return "json", base64.b64encode(data).decode("ascii")
    return "absent", None


def transport_kwargs_to_frozen_request(contract_id: str, operation: dict[str, Any], case_id: str, req: dict[str, Any], *, seed: int, direction: str, expected_status: list[int]) -> dict[str, Any]:
    method = str(req.get("method", operation.get("method", "GET"))).upper()
    url = str(req.get("url", operation.get("path", "/")))
    parsed = urlsplit(url)
    path = parsed.path or str(operation.get("path", "/"))
    if parsed.query:
        path = f"{path}?{parsed.query}"
    body_kind, body_b64 = _body_kind_b64_from_transport(req)
    headers = _headers_list(req.get("headers"))
    # Schemathesis returns transport kwargs, not a prepared wire request.
    # Materialize query/cookies/JSON/framing locally, without sending it.
    if hasattr(req.get("headers", {}), "items") or not req.get("headers"):
        import requests as http_requests
        preparation_kwargs = dict(req)
        preparation_kwargs["headers"] = dict(headers)
        prepared = http_requests.Request(**preparation_kwargs).prepare()
        path = prepared.path_url
        headers = _headers_list(prepared.headers)
        raw = prepared.body
        if raw is not None:
            if isinstance(raw, str):
                raw = raw.encode("utf-8")
            if not isinstance(raw, bytes):
                raise T2OfflineBridgeError("streaming body not qualified for offline freeze")
            body_b64 = base64.b64encode(raw).decode("ascii")
        elif body_kind != "absent":
            body_b64 = base64.b64encode(b"").decode("ascii")
    elif req.get("params") or req.get("cookies") or "json" in req:
        raise T2OfflineBridgeError("duplicate-header transport must provide already prepared query/body/cookies")
    return {
        "id": str(case_id),
        "method": method,
        "path": path,
        "headers": headers,
        "body_kind": body_kind,
        "body_b64": body_b64,
        "expectedStatus": [int(x) for x in expected_status],
        "parameters": {"contractId": contract_id, "operationId": operation.get("operationId"), "seed": int(seed), "direction": direction},
    }


def _write_partial(output_dir: Path, report: dict[str, Any], requests: list[dict[str, Any]]) -> None:
    frozen = {"kind": "t2-offline-preparation-v4-frozen-requests", "officialCampaign": False, "networkCallsDuringGeneration": 0, "requests": requests}
    (output_dir / "frozen-t2-requests.partial.json").write_bytes(_json_bytes(frozen))
    (output_dir / "generation-report.partial.json").write_bytes(_json_bytes(report))


def generate_t2_offline_suite_for_contract(cfg: dict[str, Any], contract_id: str, output_dir: Path, *, seeds: list[int] | None = None, directions: list[str] | None = None, max_examples_per_direction: int = 50) -> dict[str, Any]:
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise T2OfflineBridgeError(f"refusing to overwrite output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    if max_examples_per_direction <= 0:
        raise T2OfflineBridgeError("max_examples_per_direction must be positive")
    seeds = list(DEFAULT_SEEDS if seeds is None else seeds)
    directions = list(DIRECTIONS if directions is None else directions)
    unsupported = [d for d in directions if d not in MODE_BY_DIRECTION]
    if unsupported:
        raise T2OfflineBridgeError(f"unsupported directions: {unsupported}")
    contract = _contract_row(cfg, contract_id)
    pin_error = _check_pin(contract.get("source", {}))
    if pin_error:
        raise T2OfflineBridgeError(f"{contract_id}: {pin_error}")
    contract_path = Path(str(contract["source"]["path"]))
    openapi = _load_openapi(contract_path)
    schema = schemathesis.openapi.from_dict(openapi)
    contract_copy_path = output_dir / "original-openapi.json"
    contract_copy_path.write_bytes(_json_bytes(openapi))
    requests: list[dict[str, Any]] = []
    generation: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    started_all = time.monotonic()
    try:
        for op in _operation_rows(contract):
            op_path = str(op["path"])
            method = str(op["method"]).upper()
            resource_package_id = _resource_package_id_for_operation(cfg, op)
            try:
                track = _operation_track(op)
            except T2OfflineBridgeError:
                track = None
            operation = schema[op_path][method]
            expected = [int(x) for x in op.get("documentedResponses", [200, 400, 500]) if str(x).isdigit()]
            for seed_value in seeds:
                for direction in directions:
                    batch = []

                    @hyp_seed(int(seed_value))
                    @settings(max_examples=max_examples_per_direction, phases=(Phase.generate,), database=None, deadline=None)
                    @given(operation.as_strategy(generation_mode=MODE_BY_DIRECTION[direction]))
                    def collect(case):
                        batch.append(case)

                    started = time.monotonic()
                    try:
                        collect()
                    except Exception as exc:
                        errors.append({"contractId": contract_id, "path": op_path, "method": method, "seed": seed_value, "direction": direction, "error": repr(exc), "partialGeneratedBeforeException": len(batch)})
                    generation.append({"contractId": contract_id, "path": op_path, "method": method, "seed": seed_value, "direction": direction, "generated": len(batch), "maxExamples": max_examples_per_direction, "seconds": time.monotonic() - started})
                    for idx, case in enumerate(batch):
                        req = case.as_transport_kwargs(base_url="http://127.0.0.1")
                        item = transport_kwargs_to_frozen_request(contract_id, op, f"{contract_id}-{method}-{op.get('operationId', idx)}-seed{seed_value}-{direction}-{idx}", req, seed=int(seed_value), direction=direction, expected_status=expected)
                        item["resourcePackageId"] = resource_package_id
                        if track is not None:
                            item["parameters"]["track"] = track
                            item["parameters"]["fixtureBindingStatus"] = "candidate_not_official"
                            item["parameters"]["fixtureBindingAuthority"] = "campaign-config-v2 fixturesCandidates bytes; no oracle promotion"
                        requests.append(item)
    except Exception as exc:
        report = {"kind": "t2-offline-preparation-v4-generation-report", "contractId": contract_id, "officialCampaign": False, "success": False, "networkCallsDuringGeneration": 0, "originalContractPath": str(contract_path), "originalContractSha256": _sha256_path(contract_path), "requestOccurrences": len(requests), "generation": generation, "errors": errors + [{"error": repr(exc), "classification": "generation_aborted_partial_preserved"}], "seconds": time.monotonic() - started_all}
        _write_partial(output_dir, report, requests)
        raise

    frozen = {"kind": "t2-offline-preparation-v4-frozen-requests", "officialCampaign": False, "networkCallsDuringGeneration": 0, "requests": requests}
    frozen_path = output_dir / "frozen-t2-requests.json"
    frozen_path.write_bytes(_json_bytes(frozen))
    suite, import_report = import_t2_frozen_requests(contract_id, frozen_path, suite_id="T2", default_resource_package_id="t2-offline-preparation-v4")
    suite_path = output_dir / "T2-suite.json"
    freeze_suite(suite, suite_path)
    loaded = load_frozen_suite(suite_path)
    report = {
        "kind": "t2-offline-preparation-v4-generation-report",
        "contractId": contract_id,
        "officialCampaign": False,
        "success": not errors,
        "networkCallsDuringGeneration": 0,
        "originalContractPath": str(contract_path),
        "originalContractBytes": contract_path.stat().st_size,
        "originalContractSha256": _sha256_path(contract_path),
        "copiedOriginalOpenApiPath": str(contract_copy_path),
        "copiedOriginalOpenApiSha256": _sha256_path(contract_copy_path),
        "frozenRequestsPath": str(frozen_path),
        "frozenRequestsSha256": _sha256_path(frozen_path),
        "suitePath": str(suite_path),
        "suiteSha256": _sha256_path(suite_path),
        "seeds": seeds,
        "directions": directions,
        "perOperationPerSeed": {"positive": max_examples_per_direction, "negative": max_examples_per_direction, "total": max_examples_per_direction * 2},
        "resourcePackageIds": {track: package_id for track, package_id in TRACK_FIXTURE_DEFAULTS.items() if any((r.get("resourcePackageId") == package_id) for r in requests)},
        "hypothesisPhases": ["generate"],
        "hypothesisDatabase": None,
        "shrinking": False,
        "replayDuringGeneration": False,
        "requestOccurrences": len(requests),
        "frozenSuiteLoadCount": len(loaded.cases),
        "generation": generation,
        "errors": errors,
        "importReport": import_report,
        "suiteGenerationModuleReused": str(Path(suite_generation.__file__).resolve()),
        "seconds": time.monotonic() - started_all,
    }
    (output_dir / "generation-report.json").write_bytes(_json_bytes(report))
    return report

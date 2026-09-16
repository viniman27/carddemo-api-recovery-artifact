from __future__ import annotations

import base64
import hashlib
import json
import sys
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import schemathesis
from hypothesis import Phase, given, seed as hyp_seed, settings
from schemathesis.generation import GenerationMode

THIS = Path(__file__).resolve()
P3 = THIS.parents[2]
CYCLE = P3.parent
HARNESS_SRC = P3 / "campaign-harness-v3" / "src"
ADAPTER_SRC = P3 / "unified-preflight-v3" / "src"
for _path in (HARNESS_SRC, ADAPTER_SRC):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from campaign_harness import freeze_suite, load_frozen_suite  # noqa: E402
from suite_adapters import import_t2_frozen_requests  # noqa: E402

DEFAULT_SEEDS = [104729, 130363, 155921]
DIRECTIONS = ["positive", "negative"]
MODE_BY_DIRECTION = {"positive": GenerationMode.POSITIVE, "negative": GenerationMode.NEGATIVE}


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


def validate_current_registry(cfg: dict[str, Any]) -> dict[str, Any]:
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
    if len(contracts) != 7 or contract_block.get("count") != 7:
        errors.append("contract count must be exactly 7")
    if op_total != 21 or contract_block.get("operationsTotal") != 21:
        errors.append("operation count must be exactly 21 total")
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
            if str(op.get("method", "")).lower() not in {"get", "post", "put", "patch", "delete"}:
                errors.append(f"unsupported method in {cid}: {op.get('method')}")
            if not str(op.get("path", "")).startswith("/"):
                errors.append(f"operation path must be absolute in {cid}: {op.get('path')}")
            if not op.get("documentedResponses"):
                errors.append(f"operation without documentedResponses in {cid}: {op.get('operationId')}")

    for row in cfg.get("sources", []):
        pin_error = _check_pin(row)
        if pin_error:
            failed_pins.append(f"{row.get('id')}: {pin_error}")

    t1_payloads = cfg.get("t1DecisionPackage", {}).get("localPackageAlreadyExists", {}).get("payloads", [])
    if len(t1_payloads) != 7:
        errors.append("T1 local payload count must be exactly 7")
    for row in t1_payloads:
        if row.get("sendStatus") != "not_sent" or row.get("providerCalled") is not False:
            errors.append(f"T1 payload must remain not_sent/providerCalled=false: {row.get('contractId')}")
        pin_error = _check_pin(row.get("payload", {}))
        if pin_error:
            failed_pins.append(f"T1 {row.get('contractId')}: {pin_error}")

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
        "kind": "t2-offline-preparation-v2-plan",
        "version": "2.0-local-candidate",
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
        "reset": {"default": "fresh_dir_per_run", "source": "current config / campaign protocol", "beforeAfterHashChecks": "required_for_official_freeze"},
        "union": {"order": ["T1", "T2", "T3"], "builder": "campaign-harness-v3 UnionBuilder", "status": "blocked_until_T1_T2_T3_official_suites_exist", "independentReplica": False},
        "errorPolicy": {"failClosedOnPinMismatch": True, "noRepairOfGeneratedRequests": True, "noReplayDuringGeneration": True},
        "blockers": [
            "T1 specific external-send consent is still missing; no provider call or probe is allowed here.",
            "T3 v2 selection remains unbound because current pins are t3-campaign-adapter-v3 + sdd-external-selection-v1 + substantive-review-v1; do not invent a v2 pin.",
            "This runner prepares/generates candidate offline T2 artifacts only; it does not authorize or start official AWS freeze/campaign.",
        ],
    }


def _synthetic_openapi_from_contracts(contracts: Iterable[dict[str, Any]]) -> dict[str, Any]:
    paths: dict[str, Any] = {}
    for contract in contracts:
        cid = str(contract.get("contractId"))
        for op in contract.get("operations", []):
            path = str(op["path"])
            method = str(op["method"]).lower()
            documented = {str(code): {"description": f"synthetic documented {code}"} for code in op.get("documentedResponses", ["200", "400", "500"])}
            documented.setdefault("400", {"description": "synthetic invalid"})
            schema = {
                "type": "object",
                "properties": {"syntheticCase": {"type": "string"}},
                "required": ["syntheticCase"],
                "additionalProperties": False,
            }
            paths.setdefault(path, {})[method] = {
                "operationId": f"{cid}_{op.get('operationId') or method}_{len(paths.get(path, {}))}",
                "x-source-contract-id": cid,
                "requestBody": {"required": bool(op.get("requestBodyRequired", True)), "content": {"application/json": {"schema": schema}}},
                "responses": documented,
            }
    return {"openapi": "3.1.0", "info": {"title": "Synthetic AWS T2 offline bridge fixture; NOT an official CardDemo contract", "version": "0.0-candidate"}, "paths": paths}


def _body_from_transport_kwargs(req: dict[str, Any]) -> Any:
    raw_body = req.get("data", req.get("json", None))
    if isinstance(raw_body, bytes):
        try:
            return json.loads(raw_body.decode("utf-8"))
        except Exception:
            return {"kind": "bytes", "base64": base64.b64encode(raw_body).decode("ascii")}
    if isinstance(raw_body, str):
        try:
            return json.loads(raw_body)
        except json.JSONDecodeError:
            return raw_body
    if raw_body is None:
        return {}
    return raw_body


def generate_synthetic_t2_suite(contracts: list[dict[str, Any]], output_dir: Path, *, seeds: list[int] | None = None, max_examples_per_direction: int = 50) -> dict[str, Any]:
    output_dir = Path(output_dir)
    if output_dir.exists():
        existing = {item.name for item in output_dir.iterdir()}
        allowed_existing = {"plan.json"}
        if existing - allowed_existing:
            raise T2OfflineBridgeError(f"refusing to overwrite non-empty output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    if max_examples_per_direction <= 0:
        raise T2OfflineBridgeError("max_examples_per_direction must be positive")
    seeds = list(DEFAULT_SEEDS if seeds is None else seeds)
    openapi = _synthetic_openapi_from_contracts(contracts)
    schema_path = output_dir / "synthetic-openapi.json"
    schema_path.write_bytes(_json_bytes(openapi))
    schema = schemathesis.openapi.from_dict(openapi)
    requests: list[dict[str, Any]] = []
    generation: list[dict[str, Any]] = []
    started_all = time.monotonic()
    for contract in contracts:
        cid = str(contract.get("contractId"))
        for op in contract.get("operations", []):
            op_path = str(op["path"])
            method = str(op["method"]).upper()
            operation = schema[op_path][method]
            for seed_value in seeds:
                for direction in DIRECTIONS:
                    batch = []

                    @hyp_seed(int(seed_value))
                    @settings(max_examples=max_examples_per_direction, phases=(Phase.generate,), database=None, deadline=None)
                    @given(operation.as_strategy(generation_mode=MODE_BY_DIRECTION[direction]))
                    def collect(case):
                        batch.append(case)

                    started = time.monotonic()
                    collect()
                    generation.append({"contractId": cid, "path": op_path, "method": method, "seed": seed_value, "direction": direction, "generated": len(batch), "maxExamples": max_examples_per_direction, "seconds": time.monotonic() - started})
                    for idx, case in enumerate(batch):
                        req = case.as_transport_kwargs(base_url="http://127.0.0.1")
                        parsed_path = urlparse(str(req.get("url", op_path))).path or op_path
                        requests.append({
                            "id": f"{cid}-{method}-{op_path.strip('/').replace('/', '_')}-seed{seed_value}-{direction}-{idx}",
                            "method": method,
                            "path": parsed_path,
                            "headers": {"content-type": "application/json"},
                            "body": _body_from_transport_kwargs(req),
                            "expectedStatus": [int(x) for x in op.get("documentedResponses", [200, 400, 500]) if str(x).isdigit()],
                            "parameters": {"contractId": cid, "operationId": op.get("operationId"), "seed": seed_value, "direction": direction},
                        })
    frozen = {"kind": "t2-offline-preparation-v2-synthetic-frozen-requests", "officialCampaign": False, "networkCallsDuringGeneration": 0, "requests": requests}
    frozen_path = output_dir / "frozen-t2-requests.json"
    frozen_path.write_bytes(_json_bytes(frozen))
    suite, import_report = import_t2_frozen_requests("SYNTHETIC-AWS-T2-CANDIDATE", frozen_path, suite_id="T2-SYNTHETIC", default_resource_package_id="synthetic-offline")
    suite_path = output_dir / "T2-synthetic-suite.json"
    freeze_suite(suite, suite_path)
    loaded = load_frozen_suite(suite_path)
    stimuli = {case.request.stimulus_key() for case in loaded.cases}
    report = {
        "kind": "t2-offline-preparation-v2-synthetic-generation-report",
        "officialCampaign": False,
        "networkCallsDuringGeneration": 0,
        "contractCount": len(contracts),
        "operationCount": sum(len(c.get("operations", [])) for c in contracts),
        "seeds": seeds,
        "directions": DIRECTIONS,
        "perOperationPerSeed": {"positive": max_examples_per_direction, "negative": max_examples_per_direction, "total": max_examples_per_direction * 2},
        "requestOccurrences": len(requests),
        "uniqueRequestStimuli": len(stimuli),
        "occurrencesAreNotDiversity": True,
        "schemaPath": str(schema_path),
        "schemaSha256": _sha256_path(schema_path),
        "frozenRequestsPath": str(frozen_path),
        "frozenRequestsSha256": _sha256_path(frozen_path),
        "suitePath": str(suite_path),
        "suiteSha256": _sha256_path(suite_path),
        "importReport": import_report,
        "frozenSuiteLoadCount": len(loaded.cases),
        "generation": generation,
        "seconds": time.monotonic() - started_all,
    }
    (output_dir / "generation-report.json").write_bytes(_json_bytes(report))
    return report

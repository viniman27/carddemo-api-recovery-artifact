from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, ValidationError
from jsonschema.validators import validator_for

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
CYCLE = P3.parent
HARNESS_SRC = P3 / "campaign-harness-v3" / "src"
PREFLIGHT_SRC = P3 / "unified-preflight-v3" / "src"
sys.path.insert(0, str(HARNESS_SRC))
sys.path.insert(0, str(PREFLIGHT_SRC))

from campaign_harness import Case, Expectation, HttpRequestSpec, Suite, freeze_suite, load_frozen_suite  # noqa: E402
import suite_adapters  # noqa: E402

CONTRACT_IDS = ["E1-1", "E1-2", "E1-3", "E2-1", "E2-2", "E2-3", "E3-SDD-stage6r3"]
FIXTURE_BY_TRACK = {
    "posting": "posting.candidate-v1-physical-v2",
    "interest": "interest.candidate-v1-physical-v2",
    "reporting": "reporting.candidate-v1-physical-v2",
    "unknown": "track-unresolved-no-fixture",
}


@dataclass(frozen=True)
class ContractSchema:
    contract_id: str
    source_path: Path
    source_bytes: int
    source_sha256: str
    openapi_text_sha256: str
    document: dict[str, Any]
    operations: dict[tuple[str, str], dict[str, Any]]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_bytes(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_t1_payload(parsed_path: Path) -> dict[str, Any]:
    wrapper = json.loads(Path(parsed_path).read_text(encoding="utf-8"))
    text = wrapper.get("text")
    if not isinstance(text, str):
        raise ValueError(f"parsed T1 response has no text string: {parsed_path}")
    payload = json.loads(text)
    if not isinstance(payload, dict) or not isinstance(payload.get("scenarios"), list):
        raise ValueError(f"T1 payload is not strict top-level scenarios object: {parsed_path}")
    return payload


def _load_openapi_from_collection_parsed(path: Path) -> tuple[dict[str, Any], str]:
    wrapper = json.loads(path.read_text(encoding="utf-8"))
    text = wrapper.get("text")
    if not isinstance(text, str):
        raise ValueError(f"contract parsed file lacks text: {path}")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"contract text did not parse as object: {path}")
    return data, text


def _load_openapi_yaml(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"contract yaml did not parse as object: {path}")
    return data, text


def _operation_map(doc: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    ops: dict[tuple[str, str], dict[str, Any]] = {}
    for path, path_item in (doc.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, op in path_item.items():
            m = str(method).upper()
            if m in {"GET", "POST", "PUT", "PATCH", "DELETE"} and isinstance(op, dict):
                ops[(m, str(path))] = op
    return ops


def build_contract_schema_index(cycle: Path = CYCLE) -> dict[str, ContractSchema]:
    index: dict[str, ContractSchema] = {}
    for cid in CONTRACT_IDS:
        if cid == "E3-SDD-stage6r3":
            path = cycle / "P2a" / "openapi-carddemo-stage6r3.yaml"
            doc, text = _load_openapi_yaml(path)
        else:
            path = cycle / "collection-01" / cid / "parsed.json"
            doc, text = _load_openapi_from_collection_parsed(path)
        raw = path.read_bytes()
        index[cid] = ContractSchema(
            contract_id=cid,
            source_path=path,
            source_bytes=len(raw),
            source_sha256=sha256_bytes(raw),
            openapi_text_sha256=sha256_bytes(text.encode("utf-8")),
            document=doc,
            operations=_operation_map(doc),
        )
    return index


def _resolve_pointer(doc: dict[str, Any], ref: str) -> Any:
    if not ref.startswith("#/"):
        raise ValueError(f"external ref not supported for local qualification: {ref}")
    cur: Any = doc
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        cur = cur[part]
    return cur


def _inline_local_refs(schema: Any, doc: dict[str, Any], seen: set[str] | None = None) -> Any:
    seen = seen or set()
    if isinstance(schema, dict):
        if set(schema.keys()) == {"$ref"} and isinstance(schema.get("$ref"), str):
            ref = schema["$ref"]
            if ref in seen:
                return schema
            return _inline_local_refs(copy.deepcopy(_resolve_pointer(doc, ref)), doc, seen | {ref})
        out = {}
        for k, v in schema.items():
            if k == "$ref" and isinstance(v, str):
                # Preserve siblings by expanding under allOf.
                expanded = _inline_local_refs(copy.deepcopy(_resolve_pointer(doc, v)), doc, seen | {v})
                siblings = {sk: _inline_local_refs(sv, doc, seen) for sk, sv in schema.items() if sk != "$ref"}
                return {"allOf": [expanded, siblings]} if siblings else expanded
            out[k] = _inline_local_refs(v, doc, seen)
        return out
    if isinstance(schema, list):
        return [_inline_local_refs(x, doc, seen) for x in schema]
    return schema


def request_schema_for_operation(contract: ContractSchema, method: str, path: str) -> dict[str, Any] | None:
    op = contract.operations.get((method.upper(), path))
    if not op:
        return None
    rb = op.get("requestBody")
    if not isinstance(rb, dict):
        return None
    content = rb.get("content")
    if not isinstance(content, dict):
        return None
    media = content.get("application/json") or next(iter(content.values()), None)
    if not isinstance(media, dict) or not isinstance(media.get("schema"), dict):
        return None
    return _inline_local_refs(media["schema"], contract.document)


def documented_statuses(contract: ContractSchema, method: str, path: str) -> list[int]:
    op = contract.operations.get((method.upper(), path)) or {}
    statuses: list[int] = []
    for key in (op.get("responses") or {}).keys():
        if str(key).isdigit():
            statuses.append(int(key))
    return sorted(set(statuses)) or [200, 400, 500, 503]


def _extract_method_path(scenario: dict[str, Any]) -> tuple[str | None, str | None]:
    op = scenario.get("operation")
    if isinstance(op, dict):
        method, path = op.get("method"), op.get("path")
        return (str(method).upper() if method is not None else None, str(path) if path is not None else None)
    return (str(scenario.get("method")).upper() if scenario.get("method") is not None else None, str(scenario.get("path")) if scenario.get("path") is not None else None)


def _body_from_request(req: Any) -> dict[str, Any]:
    if not isinstance(req, dict):
        return {"kind": "absent"}
    kind = req.get("bodyKind") or req.get("body_kind")
    if "bodyJson" in req:
        return {"kind": "json", "value": req["bodyJson"]}
    if "body" in req:
        body = req["body"]
        if kind == "absent":
            return {"kind": "absent"}
        if isinstance(body, str) and (kind == "bytes" or req.get("bodyEncoding") == "base64"):
            return {"kind": "bytes", "base64": body}
        return {"kind": "json", "value": body}
    if kind == "absent":
        return {"kind": "absent"}
    return {"kind": "absent"}


def _headers_from_request(req: Any) -> tuple[list[list[str]], str]:
    if not isinstance(req, dict) or "headers" not in req:
        return [], "absent"
    headers = req.get("headers")
    if isinstance(headers, dict):
        return [[str(k), str(v)] for k, v in headers.items()], "present"
    if isinstance(headers, list):
        out = []
        for pair in headers:
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                out.append([str(pair[0]), str(pair[1])])
        return out, "present"
    return [], "present_invalid"


def normalize_scenario_to_import_item(contract_id: str, scenario: dict[str, Any]) -> dict[str, Any]:
    method, path = _extract_method_path(scenario)
    req = scenario.get("request")
    body = _body_from_request(req)
    headers, headers_state = _headers_from_request(req)
    if body.get("kind") == "json" and headers_state == "absent":
        # Runtime helper header for JSON bytes; ledger still records source headers as absent.
        headers = [["content-type", "application/json"]]
    item = {
        "id": str(scenario.get("id", "missing-id")),
        "method": method,
        "path": path,
        "headers": headers,
        "body": body,
        "timeoutSeconds": 180.0,
        "parameters": {
            "contractId": contract_id,
            "originalScenarioId": str(scenario.get("id", "missing-id")),
            "category": scenario.get("category"),
            "sourceHeadersState": headers_state,
            "sourceQueryState": "present" if isinstance(req, dict) and "query" in req else "absent",
            "expectedAssertionsQuarantined": "expectedFromContract" in scenario or "expected" in scenario,
        },
    }
    return item


def track_for_path(path: str | None) -> str:
    p = (path or "").lower()
    if "interest" in p:
        return "interest"
    if "report" in p:
        return "reporting"
    if "post" in p or "transaction" in p:
        return "posting"
    return "unknown"


def _body_value_for_schema(item: dict[str, Any]) -> tuple[bool, Any, str | None]:
    body = item.get("body") or {"kind": "absent"}
    kind = body.get("kind")
    if kind == "absent":
        return False, None, None
    if kind == "json":
        return True, body.get("value"), None
    if kind == "bytes":
        try:
            raw = base64.b64decode(str(body.get("base64", "")), validate=True)
            return True, json.loads(raw.decode("utf-8")), None
        except Exception as exc:
            return True, None, f"bytes body is not JSON-decodable for schema validation: {exc}"
    return True, None, f"unsupported body kind: {kind}"


def validate_against_original_schema(contract: ContractSchema, item: dict[str, Any]) -> dict[str, Any]:
    method, path = item.get("method"), item.get("path")
    if not isinstance(method, str) or not isinstance(path, str):
        return {"operationAdmissibility": "operation_missing", "schemaAdmissibility": "schema_not_checked", "errors": ["missing method/path"]}
    if (method.upper(), path) not in contract.operations:
        return {"operationAdmissibility": "operation_not_in_original_contract", "schemaAdmissibility": "schema_not_checked", "errors": [f"{method} {path} not found in {contract.contract_id}"]}
    schema = request_schema_for_operation(contract, method, path)
    present, value, body_error = _body_value_for_schema(item)
    op = contract.operations[(method.upper(), path)]
    body_required = bool((op.get("requestBody") or {}).get("required")) if isinstance(op.get("requestBody"), dict) else False
    if body_error:
        return {"operationAdmissibility": "operation_in_original_contract", "schemaAdmissibility": "schema_invalid", "errors": [body_error]}
    if schema is None:
        if present:
            return {"operationAdmissibility": "operation_in_original_contract", "schemaAdmissibility": "schema_invalid", "errors": ["body present but original operation has no JSON request schema"]}
        return {"operationAdmissibility": "operation_in_original_contract", "schemaAdmissibility": "schema_valid", "errors": []}
    if not present:
        return {"operationAdmissibility": "operation_in_original_contract", "schemaAdmissibility": "schema_invalid" if body_required else "schema_valid", "errors": ["request body absent but required"] if body_required else []}
    try:
        validator_cls = validator_for(schema)
        validator_cls.check_schema(schema)
        validator_cls(schema).validate(value)
        return {"operationAdmissibility": "operation_in_original_contract", "schemaAdmissibility": "schema_valid", "errors": []}
    except ValidationError as exc:
        return {"operationAdmissibility": "operation_in_original_contract", "schemaAdmissibility": "schema_invalid", "errors": [exc.message], "jsonPath": list(exc.path), "schemaPath": list(exc.schema_path)}


def classification_for(category: Any, validation: dict[str, Any]) -> str:
    cat = str(category or "").lower()
    if validation["operationAdmissibility"] != "operation_in_original_contract":
        return "erroneous_operation_unmapped_preserved"
    if validation["schemaAdmissibility"] == "schema_valid" and "negative" in cat:
        return "valid_negative_intentional"
    if validation["schemaAdmissibility"] == "schema_valid":
        return "admissible_schema_valid"
    if "negative" in cat:
        return "erroneous_schema_invalid_negative_preserved"
    return "erroneous_schema_invalid_preserved"


def make_case(contract: ContractSchema, suite_id: str, item: dict[str, Any]) -> Case:
    method = str(item["method"]).upper()
    path = str(item["path"])
    body = item.get("body") or {"kind": "absent"}
    kind = body.get("kind")
    b64 = None
    if kind == "json":
        b64 = base64.b64encode(json.dumps(body.get("value"), separators=(",", ":"), ensure_ascii=False).encode("utf-8")).decode("ascii")
    elif kind == "bytes":
        b64 = str(body.get("base64", ""))
    elif kind == "absent":
        b64 = None
    else:
        raise ValueError(f"unsupported body kind: {kind}")
    track = track_for_path(path)
    scenario_id = str(item["id"])
    return Case(
        case_id=f"{suite_id}-{contract.contract_id}-{scenario_id}",
        suite_id=suite_id,
        origin=f"T1-real-import:{contract.contract_id}",
        request=HttpRequestSpec(method, path, tuple((str(k), str(v)) for k, v in item.get("headers", [])), str(kind), b64),
        resource_package_id=FIXTURE_BY_TRACK[track],
        expectation=Expectation("documented-status-no-independent-oracle", {"status": documented_statuses(contract, method, path)}),
        timeout_seconds=float(item.get("timeoutSeconds", 180.0)),
        parameters={**dict(item.get("parameters", {})), "track": track, "fixtureStatus": "candidate_needs_review", "oracleExpectedOutputs": "quarantined_not_used"},
        sequence=(),
        provenance=(f"t1-generation-real:{contract.contract_id}:{scenario_id}",),
    )


def original_adapter_attempt(contract_id: str, parsed_path: Path) -> dict[str, Any]:
    try:
        _suite, report = suite_adapters.import_t1_preserved_response(contract_id, parsed_path, suite_id=f"T1-ORIGINAL-ADAPTER-{contract_id}")
        return {k: v for k, v in report.items() if k != "raw_response"}
    except Exception as exc:
        return {"contractId": contract_id, "sourcePath": str(parsed_path), "adapterRaised": type(exc).__name__, "error": str(exc)}


def source_entries(cycle: Path) -> list[dict[str, Any]]:
    consolidated = json.loads((cycle / "P3" / "t1-generation-03" / "CONSOLIDATED-SEVEN-VERIFIED.json").read_text(encoding="utf-8"))
    out = []
    for row in consolidated["items"]:
        parsed = cycle / row["parsedPath"]
        payload = load_t1_payload(parsed)
        out.append({**row, "parsedAbsPath": str(parsed), "parsedSha256": sha256_path(parsed), "loadedScenarioCount": len(payload["scenarios"])})
    return out


def run_import_qualification(cycle: Path = CYCLE, out: Path | None = None) -> dict[str, Any]:
    out = Path(out or (cycle / "P3" / "t1-import-qualification-v1")).resolve()
    candidates = out / "CANDIDATES"
    candidates.mkdir(parents=True, exist_ok=True)
    contracts = build_contract_schema_index(cycle)
    sources = source_entries(cycle)
    ledger_cases: list[dict[str, Any]] = []
    suites: list[dict[str, Any]] = []
    original_attempts: list[dict[str, Any]] = []
    freeze_loadable = 0

    for src in sources:
        cid = src["contractId"]
        parsed = Path(src["parsedAbsPath"])
        payload = load_t1_payload(parsed)
        contract = contracts[cid]
        original_attempts.append(original_adapter_attempt(cid, parsed))
        cases: list[Case] = []
        suite_id = f"T1-REAL-{cid}"
        for idx, scenario in enumerate(payload["scenarios"]):
            item = normalize_scenario_to_import_item(cid, scenario)
            validation = validate_against_original_schema(contract, item)
            cls = classification_for(scenario.get("category"), validation)
            track = track_for_path(item.get("path"))
            accepted = cls in {"valid_negative_intentional", "admissible_schema_valid"}
            case_id = f"{suite_id}-{item['id']}"
            if accepted:
                case = make_case(contract, suite_id, item)
                cases.append(case)
                case_id = case.case_id
            ledger_cases.append({
                "contractId": cid,
                "sourceParsedPath": str(parsed),
                "sourceTextSha256": src["textSha256"],
                "scenarioIndex": idx,
                "originalScenarioId": scenario.get("id"),
                "category": scenario.get("category"),
                "method": item.get("method"),
                "path": item.get("path"),
                "track": track,
                "resourcePackageId": FIXTURE_BY_TRACK[track],
                "bodyState": (item.get("body") or {}).get("kind"),
                "sourceHeadersState": item["parameters"]["sourceHeadersState"],
                "sourceQueryState": item["parameters"]["sourceQueryState"],
                "operationAdmissibility": validation["operationAdmissibility"],
                "schemaAdmissibility": validation["schemaAdmissibility"],
                "classification": cls,
                "acceptedIntoHarnessSuite": accepted,
                "candidateCaseId": case_id if accepted else None,
                "expectedAssertionsQuarantined": item["parameters"]["expectedAssertionsQuarantined"],
                "schemaErrors": validation.get("errors", []),
                "jsonPath": validation.get("jsonPath"),
                "schemaPath": validation.get("schemaPath"),
            })
        suite = Suite(suite_id, cases)
        freeze_path = candidates / f"{suite_id}.json"
        freeze_suite(suite, freeze_path)
        loaded = load_frozen_suite(freeze_path)
        if len(loaded.cases) == len(cases):
            freeze_loadable += 1
        suites.append({
            "contractId": cid,
            "suiteId": suite_id,
            "freezePath": str(freeze_path),
            "freezeSha256": sha256_path(freeze_path),
            "sourceScenarioCount": len(payload["scenarios"]),
            "acceptedCount": len(cases),
            "preservedInvalidCount": len(payload["scenarios"]) - len(cases),
            "loadVerifiedCount": len(loaded.cases),
        })

    contract_pins = []
    for c in contracts.values():
        contract_pins.append({
            "contractId": c.contract_id,
            "sourcePath": str(c.source_path),
            "sourceBytes": c.source_bytes,
            "sourceSha256": c.source_sha256,
            "openapiTextSha256": c.openapi_text_sha256,
            "operationCount": len(c.operations),
            "operations": [{"method": m, "path": p} for (m, p) in sorted(c.operations)],
        })

    counts = {
        "contract_count": len(sources),
        "source_scenario_occurrences": len(ledger_cases),
        "accepted_harness_cases": sum(1 for c in ledger_cases if c["acceptedIntoHarnessSuite"]),
        "preserved_invalid_cases": sum(1 for c in ledger_cases if not c["acceptedIntoHarnessSuite"]),
        "schema_valid_cases": sum(1 for c in ledger_cases if c["schemaAdmissibility"] == "schema_valid"),
        "schema_invalid_cases": sum(1 for c in ledger_cases if c["schemaAdmissibility"] == "schema_invalid"),
        "valid_negative_intentional": sum(1 for c in ledger_cases if c["classification"] == "valid_negative_intentional"),
        "erroneous_cases_preserved": sum(1 for c in ledger_cases if str(c["classification"]).startswith("erroneous")),
        "harness_freeze_loadable_suites": freeze_loadable,
        "campaign_started": False,
        "model_regeneration_performed": False,
        "synthetic_replacement_performed": False,
        "runtime_executed": False,
    }
    by_contract = []
    for cid in [s["contractId"] for s in sources]:
        rows = [r for r in ledger_cases if r["contractId"] == cid]
        by_contract.append({
            "contractId": cid,
            "source": next(s for s in sources if s["contractId"] == cid),
            "counts": {
                "source": len(rows),
                "accepted": sum(1 for r in rows if r["acceptedIntoHarnessSuite"]),
                "preservedInvalid": sum(1 for r in rows if not r["acceptedIntoHarnessSuite"]),
                "schemaValid": sum(1 for r in rows if r["schemaAdmissibility"] == "schema_valid"),
                "schemaInvalid": sum(1 for r in rows if r["schemaAdmissibility"] == "schema_invalid"),
                "validNegativeIntentional": sum(1 for r in rows if r["classification"] == "valid_negative_intentional"),
                "erroneousPreserved": sum(1 for r in rows if str(r["classification"]).startswith("erroneous")),
            },
        })

    ledger = {
        "kind": "t1-real-import-per-case-admissibility-ledger-v1",
        "createdUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cases": ledger_cases,
    }
    (out / "admissibility-ledger.json").write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "original-suite-adapter-attempts.json").write_text(json.dumps({"attempts": original_attempts}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = {
        "kind": "t1-real-import-qualification-v1-report",
        "scope": "import and qualification only; no runtime campaign execution",
        "authorization": {
            "source": "P3/resumption-local-review-v1/TEST-PHASE-AUTHORIZATION.md",
            "literalAuthority": "Pode seguir com toda a fase de testes ate o fim",
            "doesNotAuthorizeNewT1ExternalGeneration": True,
        },
        "counts": counts,
        "contractPins": contract_pins,
        "fixturePolicy": {
            "packageManifest": str(cycle / "P3" / "fixture-materialization-v2" / "package" / "manifest.json"),
            "packageManifestSha256": sha256_path(cycle / "P3" / "fixture-materialization-v2" / "package" / "manifest.json"),
            "status": "candidate_needs_review_not_official_fixture",
            "resourcePackageIdsByTrack": FIXTURE_BY_TRACK,
        },
        "suites": suites,
        "byContract": by_contract,
        "limits": [
            "No model regeneration and no synthetic replacement performed.",
            "Invalid scenarios are preserved in the ledger, not repaired or silently omitted.",
            "Model-provided expectedFromContract assertions are quarantined and not treated as independent oracle outputs.",
            "Harness suites include only operation-mapped schema-valid requests with documented-status expectations.",
            "No runtime/campaign execution was performed in this import qualification artifact.",
        ],
        "artifactPaths": {
            "ledger": str(out / "admissibility-ledger.json"),
            "originalAdapterAttempts": str(out / "original-suite-adapter-attempts.json"),
            "candidatesDir": str(candidates),
        },
    }
    (out / "import-qualification-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest = {
        "kind": "t1-import-qualification-v1-manifest",
        "report": str(out / "import-qualification-report.json"),
        "reportSha256": sha256_path(out / "import-qualification-report.json"),
        "ledger": str(out / "admissibility-ledger.json"),
        "ledgerSha256": sha256_path(out / "admissibility-ledger.json"),
        "suites": suites,
        "counts": counts,
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md = [
        "# T1 import qualification v1",
        "",
        "Import-only candidate freeze artifacts for the seven completed real T1 generations.",
        "",
        f"- source scenarios: {counts['source_scenario_occurrences']}",
        f"- harness accepted cases: {counts['accepted_harness_cases']}",
        f"- invalid/preserved ledger cases: {counts['preserved_invalid_cases']}",
        f"- loadable candidate suites: {counts['harness_freeze_loadable_suites']}/7",
        "- model regeneration: false",
        "- runtime campaign execution: false",
        "",
        "Model expected assertions are quarantined; candidate cases use documented HTTP status expectations only.",
    ]
    (out / "REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycle", default=str(CYCLE))
    parser.add_argument("--output", default=str(ROOT))
    args = parser.parse_args(argv)
    report = run_import_qualification(Path(args.cycle), Path(args.output))
    print(json.dumps({"output": str(Path(args.output).resolve()), "counts": report["counts"], "report": report["artifactPaths"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import importlib.util
import json
import sys
import time
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from jsonschema import Draft202012Validator, RefResolver

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
CYCLE = P3.parent
HARNESS_SRC = P3 / "campaign-harness-v3" / "src"
UNIFIED_V3 = P3 / "unified-preflight-v3"
CAMPAIGN_CONFIG = P3 / "campaign-configuration-v2" / "campaign-config-v2.json"
P2A_PY = CYCLE / "P2a" / ".venv" / "bin" / "python"
EXPECTED_HARNESS_SHA256 = "0e5a9606b7d1ec10c2c07929a2fd18b72748e90ebdc4987a937bdc8fed5dd36e"
TRACK_BY_OPERATION = {
    "postDailyTransactions": "posting",
    "generateInterestTransactions": "interest",
    "generateTransactionReport": "reporting",
    "posting": "posting",
    "interest": "interest",
    "reporting": "reporting",
}
BUSINESS_BY_TRACK = {"posting": "CBTRN02C", "interest": "CBACT04C", "reporting": "CBTRN03C"}

if str(HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(HARNESS_SRC))

from campaign_harness import Case, Suite, VerificationError, load_frozen_suite, replay_suite  # noqa: E402


class CampaignBlocked(RuntimeError):
    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        super().__init__(reason)
        self.reason = reason
        self.details = details or {}


@dataclass(frozen=True)
class ContractPin:
    contract_id: str
    arm: str
    path: Path
    sha256: str
    bytes: int
    openapi: dict[str, Any]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_pin(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    data = p.read_bytes()
    return {"path": str(p), "sha256": sha256_bytes(data), "bytes": len(data)}


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_openapi(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        parsed = json.loads(text)
        if isinstance(parsed, dict) and isinstance(parsed.get("text"), str):
            import yaml  # type: ignore
            loaded = yaml.safe_load(parsed["text"])
        else:
            loaded = parsed
    else:
        import yaml  # type: ignore
        loaded = yaml.safe_load(text)
    if not isinstance(loaded, dict):
        raise CampaignBlocked("openapi_document_not_object", {"path": str(path)})
    return loaded


def load_contract_registry(config_path: str | Path = CAMPAIGN_CONFIG) -> dict[str, ContractPin]:
    config = _load_json(config_path)
    registry: dict[str, ContractPin] = {}
    for item in ((config.get("contracts") or {}).get("contracts") or []):
        contract_id = str(item.get("contractId"))
        source = item.get("source") or {}
        path = Path(str(source.get("path")))
        pin = file_pin(path)
        if pin["sha256"] != source.get("sha256") or pin["bytes"] != source.get("bytes"):
            raise CampaignBlocked("contract_source_pin_mismatch", {"contractId": contract_id, "expected": source, "actual": pin})
        registry[contract_id] = ContractPin(
            contract_id=contract_id,
            arm=str(item.get("arm")),
            path=path,
            sha256=pin["sha256"],
            bytes=pin["bytes"],
            openapi=_load_openapi(path),
        )
    if len(registry) != 7:
        raise CampaignBlocked("contract_count_not_7", {"count": len(registry)})
    op_count = sum(_operation_count(pin.openapi) for pin in registry.values())
    if op_count != 21:
        raise CampaignBlocked("operation_count_not_21", {"count": op_count})
    return registry


def _operation_count(openapi: dict[str, Any]) -> int:
    return sum(1 for item in (openapi.get("paths") or {}).values() if isinstance(item, dict) for method in item if method.lower() in {"get", "post", "put", "patch", "delete"})


def harness_import_pin() -> dict[str, Any]:
    import campaign_harness  # noqa: E402
    actual = Path(campaign_harness.__file__).resolve()
    expected = (HARNESS_SRC / "campaign_harness.py").resolve()
    pin = file_pin(actual)
    if actual != expected:
        raise CampaignBlocked("wrong_campaign_harness_import", {"actual": str(actual), "expected": str(expected)})
    if pin["sha256"] != EXPECTED_HARNESS_SHA256:
        raise CampaignBlocked("campaign_harness_hash_mismatch", {"actual": pin, "expectedSha256": EXPECTED_HARNESS_SHA256})
    return {"module": "campaign_harness", **pin}


def patch_replay_body_capture() -> dict[str, Any]:
    import campaign_harness  # noqa: E402
    original = campaign_harness._send_once
    if getattr(original, "aws_campaign_body_capture", False):
        return {"patched": False, "reason": "already patched"}

    def _send_once_with_body(base_url: str, req: Any, timeout_seconds: float) -> dict[str, Any]:
        import http.client
        import socket
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        if parsed.scheme != "http":
            raise VerificationError("only http loopback targets are supported")
        host = parsed.hostname or "127.0.0.1"
        if host not in {"127.0.0.1", "localhost"}:
            raise VerificationError("only loopback targets are supported")
        body = req.body_bytes_or_none()
        conn = http.client.HTTPConnection(host, parsed.port or 80, timeout=timeout_seconds)
        try:
            conn.putrequest(req.method, req.path, skip_accept_encoding=True)
            has_cl = any(k.lower() == "content-length" for k, _ in req.headers)
            for key, value in req.headers:
                conn.putheader(key, value)
            if body is not None and not has_cl:
                conn.putheader("Content-Length", str(len(body)))
            conn.endheaders(body if body is not None else None)
            resp = conn.getresponse()
            payload = resp.read()
            return {"status": resp.status, "content_type": resp.getheader("Content-Type"), "response_bytes": len(payload), "response_sha256": sha256_bytes(payload), "response_body_b64": base64.b64encode(payload).decode("ascii"), "failure_class": None}
        except socket.timeout:
            return {"status": None, "content_type": None, "response_bytes": 0, "response_sha256": None, "response_body_b64": None, "failure_class": "deadline"}
        except OSError as exc:
            failure = "deadline" if "timed out" in str(exc).lower() else "transport"
            return {"status": None, "content_type": None, "response_bytes": 0, "response_sha256": None, "response_body_b64": None, "failure_class": failure, "error": str(exc)}
        finally:
            conn.close()

    _send_once_with_body.aws_campaign_body_capture = True  # type: ignore[attr-defined]
    campaign_harness._send_once = _send_once_with_body
    return {"patched": True, "patchedFunction": "campaign_harness._send_once", "reason": "preserve raw response bytes for official structural measurement without editing harness-v3 file"}


class StructuralChecker:
    def __init__(self, contracts: dict[str, ContractPin]):
        self.contracts = contracts

    def check(self, contract_id: str, operation_id: str, method: str, path: str, status: int | None, content_type: str | None, body_b64: str | None) -> dict[str, Any]:
        if contract_id not in self.contracts:
            return {"ok": False, "classification": "unknown_contract", "detail": {"contractId": contract_id}}
        spec = self.contracts[contract_id].openapi
        op = ((spec.get("paths") or {}).get(path) or {}).get(method.lower())
        if not isinstance(op, dict):
            return {"ok": False, "classification": "route_violation", "detail": {"contractId": contract_id, "method": method, "path": path}}
        if operation_id and op.get("operationId") != operation_id:
            return {"ok": False, "classification": "operation_id_violation", "detail": {"expected": operation_id, "actual": op.get("operationId")}}
        if status is None:
            return {"ok": False, "classification": "infra_transport", "detail": {"reason": "no HTTP status"}}
        responses = op.get("responses") or {}
        if str(status) not in responses:
            return {"ok": False, "classification": "status_violation", "detail": {"status": status, "documented": sorted(responses)}}
        if (content_type or "").lower().split(";")[0].strip() != "application/json":
            return {"ok": False, "classification": "content_type_violation", "detail": {"contentType": content_type}}
        raw = base64.b64decode(body_b64 or "") if body_b64 else b""
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            return {"ok": False, "classification": "json_violation", "detail": {"error": repr(exc)}}
        schema = (((responses[str(status)].get("content") or {}).get("application/json") or {}).get("schema"))
        if schema is not None:
            errors = [e.message for e in Draft202012Validator(schema, resolver=RefResolver.from_schema(spec)).iter_errors(payload)]
            if errors:
                return {"ok": False, "classification": "schema_violation", "detail": {"status": status, "errors": errors}}
        return {"ok": True, "classification": "documented_500_schema_valid" if int(status) == 500 else "schema_valid", "detail": {"status": status}}


def derive_case_metadata_from_contract_operation(case: Case, contracts: dict[str, ContractPin]) -> dict[str, Any]:
    """Derive T3 routing only from exact contract id + OpenAPI path/method.

    This is a fallback for frozen per-contract T3 suites: the contract id must be
    present in origin/provenance/recipeId text, and operationId comes only from
    the matched OpenAPI operation for the request path and method.
    """
    haystack = " ".join([str(case.origin), *[str(x) for x in case.provenance], json.dumps(case.parameters or {}, sort_keys=True)])
    matches = [cid for cid in contracts if cid in haystack]
    if len(matches) != 1:
        raise CampaignBlocked("case_contract_id_not_derivable", {"caseId": case.case_id, "matches": matches})
    cid = matches[0]
    spec = contracts[cid].openapi
    op = ((spec.get("paths") or {}).get(case.request.path) or {}).get(case.request.method.lower())
    if not isinstance(op, dict):
        raise CampaignBlocked("case_operation_not_in_contract", {"caseId": case.case_id, "contractId": cid, "method": case.request.method, "path": case.request.path})
    operation_id = str(op.get("operationId") or "")
    track = TRACK_BY_OPERATION.get(operation_id)
    if not track:
        raise CampaignBlocked("case_track_not_derivable", {"caseId": case.case_id, "contractId": cid, "operationId": operation_id})
    return {"contractId": cid, "operationId": operation_id, "track": track, "derivation": "contract-id-token-plus-openapi-exact-method-path"}


def _metadata_for_case(case: Case, case_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return case metadata plus explicit parent-supplied overrides."""
    params = dict(case.parameters or {})
    if case_metadata:
        explicit = case_metadata.get(f"{case.suite_id}:{case.case_id}") or case_metadata.get(case.case_id)
        if explicit:
            params.update(dict(explicit))
    return params


def case_contract_id(case: Case, case_metadata: dict[str, Any] | None = None) -> str:
    params = _metadata_for_case(case, case_metadata)
    for key in ("contractId", "contract_id", "contract"):
        if params.get(key):
            return str(params[key])
    raise CampaignBlocked("case_missing_contract_id", {"caseId": case.case_id, "suiteId": case.suite_id, "required": "explicit metadata; do not infer T3 aliases from arbitrary origin text"})


def case_operation_id(case: Case, case_metadata: dict[str, Any] | None = None) -> str:
    params = _metadata_for_case(case, case_metadata)
    if params.get("operationId"):
        return str(params["operationId"])
    return ""


def _track_for_case(case: Case, case_metadata: dict[str, Any] | None = None) -> str | None:
    params = _metadata_for_case(case, case_metadata)
    if params.get("track"):
        return str(params["track"])
    op = case_operation_id(case, case_metadata)
    return TRACK_BY_OPERATION.get(op)


def _body_pin(case: Case) -> dict[str, Any]:
    body = case.request.body_bytes_or_none()
    if body is None:
        return {"body_kind": "absent", "bytes": 0, "sha256": None, "body_b64": None}
    return {"body_kind": case.request.body_kind, "bytes": len(body), "sha256": sha256_bytes(body), "body_b64": case.request.body_b64}


def build_execution_plan(suite_paths: Iterable[str | Path], contracts: dict[str, ContractPin], *, official_ready: bool, case_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    suites = []
    total_cases = 0
    for suite_path in suite_paths:
        path = Path(suite_path)
        suite = load_frozen_suite(path)
        cases = []
        for case in suite.cases:
            cid = case_contract_id(case, case_metadata)
            if cid not in contracts:
                raise CampaignBlocked("case_contract_not_in_registry", {"caseId": case.case_id, "contractId": cid})
            track = _track_for_case(case, case_metadata)
            cases.append({
                "caseId": case.case_id,
                "suiteId": suite.suite_id,
                "contractId": cid,
                "operationId": case_operation_id(case, case_metadata),
                "track": track,
                "businessProgram": BUSINESS_BY_TRACK.get(track or ""),
                "request": case.request.to_dict(),
                "caseRequestPins": _body_pin(case),
                "timeoutSeconds": case.timeout_seconds,
                "provenance": list(case.provenance),
            })
        total_cases += len(cases)
        suites.append({"suiteId": suite.suite_id, "path": str(path), "sha256": file_pin(path)["sha256"], "cases": cases, "caseCount": len(cases)})
    return {
        "kind": "aws-carddemo-official-campaign-plan-v2",
        "scope": "plan only; no API/COBOL execution in plan mode",
        "officialReady": bool(official_ready),
        "totals": {"suites": len(suites), "cases": total_cases},
        "suites": suites,
        "prerequisites": prerequisite_report(contracts),
        "policies": policy_report(),
    }


def prerequisite_report(contracts: dict[str, ContractPin] | None = None) -> dict[str, Any]:
    contracts = contracts or {}
    return {
        "python": {"required": str(P2A_PY), "exists": P2A_PY.exists(), "reason": "jsonschema/PyYAML qualified environment; do not use system python3 for campaign wrapper"},
        "harnessV3": harness_import_pin(),
        "campaignConfig": file_pin(CAMPAIGN_CONFIG) if CAMPAIGN_CONFIG.exists() else {"path": str(CAMPAIGN_CONFIG), "missing": True},
        "contracts": {"count": len(contracts), "operationCount": sum(_operation_count(c.openapi) for c in contracts.values())},
        "frozenSuites": "parent-supplied absolute suite paths required; this runner does not generate or invent T1/T2/T3/T4",
        "officialReadiness": "execute requires an explicit readiness JSON with officialReady=true and campaignAuthorized=true",
        "coverage": "uses unified-preflight-v3 coverage helpers; gcov errors/stamp mismatches/missing denominator are inadmissible, never fake zero",
        "oraclePolicy": "no evaluation-quarantine/model expected-output files are read by this runner during plan/execute",
    }


def policy_report() -> dict[str, Any]:
    return {
        "lifecycle": "Per-application target start/stop for each case; stop must prove quiet or campaign stops",
        "execution": "serial, one attempt per case, no retries, redirects disabled by http.client harness path",
        "stopPolicy": "transport/deadline/startup/lifecycle quietness stops; experimental expectation/structural violations are recorded and execution continues; measurement inadmissibility is recorded without fake zero",
        "resume": "--resume loads prior receipts and constructs a subset containing only never-attempted case IDs; failed attempts are not replayed",
        "resources": "fresh physical resources every case through P2b fixture registry; DD bindings reset in the isolated invocation environment",
        "measurement": "raw response bytes, request body bytes, application lifecycle, audit path, same-invocation coverage and gcov denominator links are recorded",
    }


def _attempted_case_ids(run_root: Path, suite_id: str) -> set[str]:
    roots = [run_root / suite_id / "replay" / "receipts.json"]
    cases_root = run_root / suite_id / "cases"
    if cases_root.is_dir():
        roots.extend(sorted(cases_root.glob("*/replay/receipts.json")))
    attempted: set[str] = set()
    for receipts_path in roots:
        if not receipts_path.is_file():
            continue
        rows = json.loads(receipts_path.read_text(encoding="utf-8"))
        for r in rows:
            cid = r.get("case_id")
            if cid and r.get("failure_class") != "not_executed":
                attempted.add(str(cid))
    return attempted


def _subset_suite_for_resume(suite: Suite, run_root: Path, resume: bool) -> tuple[Suite, int]:
    if not resume:
        return suite, len(suite.cases)
    attempted = _attempted_case_ids(run_root, suite.suite_id)
    remaining = [copy.deepcopy(c) for c in suite.cases if c.case_id not in attempted]
    return Suite(suite.suite_id, remaining), len(remaining)


def _import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise CampaignBlocked("module_import_failed", {"path": str(path), "name": name})
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def prepare_real_p2b_target(output_dir: Path, contracts: dict[str, ContractPin], case_metadata: dict[str, Any] | None = None) -> tuple[Callable[[Case], Any], dict[str, Any]]:
    unified = _import_module(UNIFIED_V3 / "unified_preflight_cli.py", "aws_campaign_unified_preflight_v3")
    prep_root = output_dir / "p2b-preparation"
    prep_root.mkdir(parents=True, exist_ok=True)
    prepared = unified.prepare_isolated_workspace(prep_root)
    cycle = Path(prepared["cycle"])
    copied_contracts = []
    for contract_id in ["E1-1", "E1-2", "E1-3", "E2-1", "E2-2", "E2-3"]:
        src = CYCLE / "collection-01" / contract_id / "response-original.txt"
        dst = cycle / "collection-01" / contract_id / "response-original.txt"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied_contracts.append({"contractId": contract_id, "source": str(src), "isolated": str(dst), "sha256": sha256_bytes(dst.read_bytes()), "bytes": dst.stat().st_size})
    prepared["isolatedContractSourceCopy"] = {"count": len(copied_contracts), "contracts": copied_contracts, "reason": "P2c facades load all E1/E2 response-original contracts by id inside isolated cycle"}
    registry = Path(prepared["registry"])
    py = Path(prepared.get("python") or P2A_PY)
    build_proc = subprocess.run([str(py), str(cycle / "P2b/p2b_binding.py"), "build"], cwd=cycle / "P2b", text=True, capture_output=True, timeout=180)
    prepared["isolatedP2bBuild"] = {"argv": [str(py), str(cycle / "P2b/p2b_binding.py"), "build"], "cwd": str(cycle / "P2b"), "returncode": build_proc.returncode, "stdoutTail": build_proc.stdout[-4000:], "stderrTail": build_proc.stderr[-4000:]}
    if build_proc.returncode != 0:
        raise CampaignBlocked("isolated_p2b_build_failed", prepared["isolatedP2bBuild"])

    def factory(case: Case) -> Any:
        contract_id = case_contract_id(case, case_metadata)
        pin = contracts[contract_id]
        arm = pin.arm.lower().replace("_", "-")
        if arm == "zero-shot":
            return unified.PosixSpawnServer([str(py), str(cycle / "P2c-zero-shot/p2c_facade.py"), "serve", "--contract", contract_id, "--output-root", "{workdir}/zero-shot-runs", "--registry", str(registry), "--port-file", "{port_file}"], cwd=cycle / "P2c-zero-shot")
        if arm == "few-shot":
            return unified.PosixSpawnServer([str(py), str(cycle / "P2c-few-shot/p2c_facade.py"), "serve", "--contract-id", contract_id, "--port-file", "{port_file}"], cwd=cycle / "P2c-few-shot")
        if arm == "sdd":
            return unified.target_p2b(cycle, registry)
        raise CampaignBlocked("unsupported_contract_arm", {"contractId": contract_id, "arm": pin.arm})

    return factory, prepared


def _audit_track(path: Path) -> str | None:
    name = path.parent.name
    for track in BUSINESS_BY_TRACK:
        if name == track or name.startswith(track + "-") or ("/" + track + "-") in str(path):
            return track
    try:
        audit = json.loads(path.read_text(encoding="utf-8"))
        workdir = str(audit.get("INV", {}).get("workdir", ""))
        base = Path(workdir).name if workdir else ""
        for track in BUSINESS_BY_TRACK:
            if base == track or base.startswith(track + "-"):
                return track
    except Exception:
        return None
    return None


def _audit_snapshot(cycle: Path) -> set[Path]:
    return {p.resolve() for p in cycle.rglob("audit.json") if p.is_file()}


def _audit_delta(cycle: Path, before: set[Path]) -> list[Path]:
    return sorted([p for p in _audit_snapshot(cycle) if p not in before], key=lambda p: p.stat().st_mtime)


def _select_current_audit(prepared: dict[str, Any], track: str, run_dir: Path) -> Path | None:
    candidates = [Path(p) for p in prepared.get("auditDelta", [])]
    matches = [p for p in candidates if p.is_file() and _audit_track(p) == track]
    if matches:
        return sorted(matches, key=lambda p: p.stat().st_mtime)[0]
    if run_dir.exists():
        local = [p for p in run_dir.rglob("audit.json")]
        track_local = [p for p in local if _audit_track(p) == track]
        if track_local:
            return sorted(track_local, key=lambda p: p.stat().st_mtime)[-1]
        if len(local) == 1:
            return local[0]
    return None


def _collect_measurement(receipt: dict[str, Any], app: dict[str, Any], prepared: dict[str, Any] | None, case: Case, case_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    track = _track_for_case(case, case_metadata)
    if not prepared or track not in BUSINESS_BY_TRACK:
        return {"admissibility": "not_collected_for_synthetic_or_unmapped_target", "track": track}
    unified = sys.modules.get("aws_campaign_unified_preflight_v3")
    if not unified:
        unified = _import_module(UNIFIED_V3 / "unified_preflight_cli.py", "aws_campaign_unified_preflight_v3")
    cycle = Path(prepared["cycle"])
    run_dir = Path(app.get("workdir", ""))
    audit = _select_current_audit(prepared, track, run_dir)
    if not audit:
        return {"admissibility": "inadmissible_or_limited", "reasons": ["audit_missing_for_current_case_track"], "track": track, "runDir": str(run_dir), "auditDelta": prepared.get("auditDelta", [])}
    cov = unified.collect_fresh_coverage_evidence(cycle / "P2b", audit, track)
    cov["admissibility"] = cov.get("measurementAdmissibility")
    cov["auditSelection"] = {"auditPath": str(audit), "source": "current_replay_delta_or_case_workdir", "track": track}
    return cov


def _target_for_case(target_factory: Callable[..., Any] | None, case: Case) -> Any:
    if target_factory is None:
        return None
    try:
        return target_factory(case)
    except TypeError as exc:
        # Backward-compatible only for old synthetic unit factories. Real v2
        # factories must accept the case so they can route per contract.
        try:
            return target_factory()  # type: ignore[misc]
        except TypeError:
            raise exc


def _safe_case_dir_name(case_id: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in case_id)[:180]


def execute_campaign(
    suite_paths: Iterable[str | Path],
    contracts: dict[str, ContractPin],
    output_dir: str | Path,
    *,
    target_factory: Callable[..., Any] | None = None,
    official_ready: bool = False,
    official_execution: bool = True,
    resume: bool = False,
    prepared: dict[str, Any] | None = None,
    case_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if official_execution and not official_ready:
        raise CampaignBlocked("official_readiness_not_asserted")
    out = Path(output_dir)
    if out.exists() and not resume:
        raise CampaignBlocked("output_exists_without_resume", {"output": str(out)})
    out.mkdir(parents=True, exist_ok=True)
    harness = harness_import_pin()
    body_patch = patch_replay_body_capture()
    checker = StructuralChecker(contracts)
    suite_reports = []
    stopped = False
    stop_reason = None
    experimental_violations: list[str] = []
    measurement_warnings: list[dict[str, Any]] = []
    totals = {"planned": 0, "attempted": 0, "completed": 0, "structural_ok": 0, "measurement_admissible": 0}

    if target_factory is None:
        target_factory, prepared = prepare_real_p2b_target(out, contracts, case_metadata)

    for suite_path in suite_paths:
        suite = load_frozen_suite(Path(suite_path))
        loaded_count = len(suite.cases)
        totals["planned"] += loaded_count
        if stopped:
            suite_reports.append({"suite_id": suite.suite_id, "path": str(suite_path), "loaded_case_count": loaded_count, "attempted_case_count": 0, "skippedReason": "previous_infra_stop_policy"})
            continue
        suite_to_run, attempt_count = _subset_suite_for_resume(suite, out, resume)
        suite_out = out / suite.suite_id
        if suite_out.exists() and attempt_count and not resume:
            raise CampaignBlocked("suite_output_exists", {"path": str(suite_out)})
        if attempt_count == 0:
            suite_reports.append({"suite_id": suite.suite_id, "path": str(suite_path), "loaded_case_count": loaded_count, "attempted_case_count": 0, "resume": True, "checks": []})
            continue

        checks = []
        applications_inline = []
        suite_totals = {"planned": attempt_count, "attempted": 0, "completed": 0, "deadline_failures": 0, "transport_failures": 0, "http_failures": 0, "not_executed": 0, "expectation_passes": 0, "expectation_violations": 0, "expectation_inconclusive": 0}

        for case in suite_to_run.cases:
            if stopped:
                break
            # Validate explicit routing metadata before invoking anything.
            contract_id = case_contract_id(case, case_metadata)
            if contract_id not in contracts:
                raise CampaignBlocked("case_contract_not_in_registry", {"caseId": case.case_id, "contractId": contract_id})
            case_dir = suite_out / "cases" / _safe_case_dir_name(case.case_id) / "replay"
            if case_dir.exists():
                if resume:
                    # This case was selected as unattempted, so an existing dir means
                    # the attempted ledger and filesystem disagree. Stop safely.
                    raise CampaignBlocked("case_output_exists_for_unattempted_resume_case", {"caseId": case.case_id, "path": str(case_dir)})
                raise CampaignBlocked("case_output_exists", {"caseId": case.case_id, "path": str(case_dir)})
            target = _target_for_case(target_factory, case)
            audit_before = _audit_snapshot(Path(prepared["cycle"])) if prepared and prepared.get("cycle") else set()
            result = replay_suite(Suite(suite.suite_id, [copy.deepcopy(case)]), target=target, output_dir=case_dir)
            prepared_for_case = prepared
            if prepared and prepared.get("cycle"):
                prepared_for_case = dict(prepared)
                prepared_for_case["auditDelta"] = [str(p) for p in _audit_delta(Path(prepared["cycle"]), audit_before)]
            for key, value in result.totals.items():
                suite_totals[key] = suite_totals.get(key, 0) + value
            totals["attempted"] += result.totals.get("attempted", 0)
            totals["completed"] += result.totals.get("completed", 0)
            applications_inline.extend(result.applications)
            app_by_case = {a.get("case_id"): a for a in result.applications}
            for receipt in result.receipts:
                # A one-case replay should produce exactly one attempted receipt; keep
                # this loop to preserve future harness additions without dropping data.
                structural = checker.check(contract_id, case_operation_id(case, case_metadata), receipt["method"], receipt["path"], receipt.get("status"), receipt.get("content_type"), receipt.get("response_body_b64"))
                app = app_by_case.get(receipt["case_id"], {})
                measurement = _collect_measurement(receipt, app, prepared_for_case, case, case_metadata)
                admissible = measurement.get("admissibility") in {"admissible_preparatory", "admissible_official"}
                if structural.get("ok"):
                    totals["structural_ok"] += 1
                else:
                    experimental_violations.append(f"experimental_structural_violation:{structural.get('classification')}")
                if admissible:
                    totals["measurement_admissible"] += 1
                elif prepared:
                    measurement_warnings.append({"case_id": receipt.get("case_id"), "track": measurement.get("track"), "admissibility": measurement.get("admissibility"), "reasons": measurement.get("inadmissibilityReasons") or measurement.get("reasons")})
                if receipt.get("expectation_result") == "violation":
                    experimental_violations.append("experimental_expectation_violation")
                row = {"case_id": receipt["case_id"], "contractId": contract_id, "operationId": case_operation_id(case, case_metadata), "track": _track_for_case(case, case_metadata), "receipt": receipt, "application": app, "structuralCheck": structural, "measurement": measurement, "replayDir": str(result.output_dir)}
                checks.append(row)
                failure = receipt.get("failure_class")
                if failure is not None:
                    stopped = True; stop_reason = f"wire_failure:{failure}"; break
                if app.get("target_quiet") is False:
                    stopped = True; stop_reason = "target_not_quiet"; break
        suite_reports.append({"suite_id": suite.suite_id, "path": str(suite_path), "loaded_case_count": loaded_count, "attempted_case_count": len(checks), "totals": suite_totals, "caseReplayRoot": str(suite_out / "cases"), "applications_inline": applications_inline, "checks": checks})
    report = {"kind": "aws-carddemo-official-campaign-runner-v3-report" if official_execution else "aws-carddemo-local-readiness-runner-v3-report", "createdUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "scope": "official-capable wrapper; execution only when parent supplies frozen suites, explicit routing metadata where needed, and explicit readiness" if official_execution else "bounded local readiness qualification only; not an official campaign run and not a T4 result", "harnessImport": harness, "bodyCapturePatch": body_patch, "preparedTarget": prepared, "policies": policy_report(), "prerequisites": prerequisite_report(contracts), "stopPolicy": {"stopped": stopped, "reason": stop_reason}, "experimentalViolations": sorted(set(experimental_violations)), "measurementWarnings": measurement_warnings, "totals": totals, "suiteReports": suite_reports, "officialExecutionStarted": bool(official_execution and totals["attempted"]), "localReadinessExecution": bool((not official_execution) and totals["attempted"])}
    (out / "campaign-report.json").write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def _readiness(path: str | None) -> bool:
    if not path:
        return False
    data = _load_json(path)
    return bool(data.get("officialReady") is True and data.get("campaignAuthorized") is True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Official-capable AWS CardDemo campaign wrapper over qualified harness/API/coverage integration")
    ap.add_argument("--mode", required=True, choices=["plan", "execute"])
    ap.add_argument("--suite", action="append", default=[], help="Frozen T1/T2/T3/T4 suite JSON path; repeat in desired official order")
    ap.add_argument("--config", default=str(CAMPAIGN_CONFIG))
    ap.add_argument("--output", required=True)
    ap.add_argument("--official-ready-json")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--case-metadata", help="JSON mapping keyed by suite_id:case_id or case_id for parent-supplied contractId/operationId/track; required for suites that omit metadata")
    args = ap.parse_args(argv)
    try:
        contracts = load_contract_registry(args.config)
        ready = _readiness(args.official_ready_json)
        case_metadata = _load_json(args.case_metadata) if args.case_metadata else None
        if not args.suite:
            raise CampaignBlocked("no_frozen_suites_supplied")
        if args.mode == "plan":
            report = build_execution_plan(args.suite, contracts, official_ready=ready, case_metadata=case_metadata)
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
            print(json.dumps({"ok": True, "mode": "plan", "output": str(Path(args.output).resolve()), "officialExecutionStarted": False}, ensure_ascii=False))
            return 0
        report = execute_campaign(args.suite, contracts, args.output, official_ready=ready, resume=args.resume, case_metadata=case_metadata)
        print(json.dumps({"ok": not report["stopPolicy"]["stopped"], "mode": "execute", "output": str(Path(args.output).resolve()), "attempted": report["totals"]["attempted"], "stopPolicy": report["stopPolicy"]}, ensure_ascii=False))
        return 0 if not report["stopPolicy"]["stopped"] else 3
    except CampaignBlocked as exc:
        print(json.dumps({"ok": False, "blocked": exc.reason, "details": exc.details}, indent=2, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

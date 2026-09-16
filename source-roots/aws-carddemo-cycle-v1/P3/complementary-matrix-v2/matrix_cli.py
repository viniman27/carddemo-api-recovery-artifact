#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
P3 = ROOT.parent
CYCLE = P3.parent
RUNNER_ROOT = P3 / "aws-campaign-runner-v3"
RUNNER_CLI = RUNNER_ROOT / "aws_campaign_runner_cli.py"
RUNNER_SRC = RUNNER_ROOT / "src" / "aws_campaign_runner.py"
CONFIG = P3 / "campaign-configuration-v2" / "campaign-config-v2.json"
PY = CYCLE / "P2a" / ".venv" / "bin" / "python"
if PY.exists() and Path(sys.executable).resolve() != PY.resolve() and os.environ.get("MATRIX_V2_REEXEC") != "1":
    os.environ["MATRIX_V2_REEXEC"] = "1"
    os.execv(str(PY), [str(PY), *sys.argv])
if not PY.exists():
    PY = Path(sys.executable)

import yaml
from jsonschema import Draft202012Validator, RefResolver, validators, exceptions as jsonschema_exceptions


def _exact_multiple_of(validator: Any, divisor: Any, instance: Any, schema: dict[str, Any]):
    if not isinstance(instance, (int, float)):
        return
    try:
        quotient = Decimal(str(instance)) / Decimal(str(divisor))
    except Exception:
        return
    if quotient != quotient.to_integral_value():
        yield jsonschema_exceptions.ValidationError(f"{instance!r} is not a multiple of {divisor!r}")


ExactDraft202012Validator = validators.extend(Draft202012Validator, {"multipleOf": _exact_multiple_of})

TRACKS = {
    "posting": {
        "cases": ["valid-new-tcatbal", "valid-existing-tcatbal", "reject-card-missing", "reject-account-missing", "reject-limit", "reject-expiry"],
        "obligations": ["POSTTRAN-OBL-003", "POSTTRAN-OBL-004", "POSTTRAN-OBL-006", "POSTTRAN-OBL-009"],
        "wire_dds": ["DALYTRAN"],
    },
    "interest": {
        "cases": ["rates-specific-default-zero", "single-final-eof"],
        "obligations": ["INTCALC-OBL-005", "INTCALC-OBL-006"],
        "wire_dds": ["PARMFILE"],
    },
    "reporting": {
        "cases": ["date-boundaries-in-out-v1", "empty-in-range-v1", "card-break-two-groups-v1", "pagination-threshold-20-v1"],
        "obligations": ["TRANREPT-OBL-002", "TRANREPT-OBL-006"],
        "wire_dds": ["TRANFILE", "DATEPARM"],
    },
}
ALL_CASES = [c for spec in TRACKS.values() for c in spec["cases"]]
SUITE_ID = "P3-COMPLEMENTARY-MATRIX-V2-ESSENTIAL12x7"


def canonical(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def encode_body(obj: dict[str, Any]) -> str:
    return base64.b64encode(canonical(obj)).decode("ascii")


def pin(path: Path) -> dict[str, Any]:
    return {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}


def suite_hash(body_without_hash: dict[str, Any]) -> str:
    return sha256_bytes(canonical(body_without_hash))


def load_contract_config() -> list[dict[str, Any]]:
    return json.loads(CONFIG.read_text(encoding="utf-8"))["contracts"]["contracts"]


def load_contract_source(contract: dict[str, Any]) -> dict[str, Any]:
    p = Path(contract["source"]["path"])
    data = json.loads(p.read_text(encoding="utf-8"))
    spec = yaml.safe_load(data["text"]) if isinstance(data, dict) and isinstance(data.get("text"), str) else data
    if not isinstance(spec, dict):
        raise RuntimeError(f"contract source did not parse to object: {p}")
    return spec


def operation_for(contract: dict[str, Any], track: str) -> dict[str, Any]:
    want = {"posting": "postDailyTransactions", "interest": "generateInterestTransactions", "reporting": "generateTransactionReport"}[track]
    matches = [op for op in contract["operations"] if op["operationId"] == want]
    if not matches and contract.get("arm", "").lower() == "sdd":
        matches = [op for op in contract["operations"] if op["operationId"] == track]
    if len(matches) != 1:
        raise RuntimeError(f"operation mismatch {contract['contractId']} {track}")
    return matches[0]


def scenario_source_registry(track: str, case_id: str) -> Path:
    if track == "posting":
        p = P3 / "complementary-posting-essential-v1" / "evidence" / "packages" / case_id / "registry.json"
    elif track == "interest":
        p = P3 / "complementary-interest-essential-v1" / "evidence" / case_id / "registry.json"
    else:
        p = P3 / "complementary-reporting-essential-v1" / "evidence" / "frozen-inputs" / case_id / "fixture-registry.json"
    if not p.is_file():
        raise RuntimeError(f"missing physical fixture registry for {track}:{case_id}: {p}")
    return p


def fixture_from_registry(registry_path: Path, track: str) -> dict[str, Any]:
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    fixtures = [fx for fx in data.get("fixtures", []) if fx.get("track") == track]
    if len(fixtures) != 1:
        raise RuntimeError(f"registry must contain exactly one {track} fixture: {registry_path}")
    return fixtures[0]


def materialize_runtime_registry(out: Path, track: str, case_id: str) -> Path:
    src_reg = scenario_source_registry(track, case_id)
    src_fx = fixture_from_registry(src_reg, track)
    dst_root = out / "fixture-registries" / track / case_id
    if dst_root.exists():
        shutil.rmtree(dst_root)
    dst_root.mkdir(parents=True)
    fx = copy.deepcopy(src_fx)
    for dd, rel in sorted(src_fx["materializer"]["files"].items()):
        src = (src_reg.parent / rel).resolve()
        if not src.is_file():
            raise RuntimeError(f"fixture file missing {track}:{case_id}:{dd}: {src}")
        dst = dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        actual = {"sha256": sha256_file(dst), "bytes": dst.stat().st_size}
        expected = src_fx["materializer"].get("filePins", {}).get(dd)
        if actual != expected:
            raise RuntimeError(f"fixture pin mismatch {track}:{case_id}:{dd}: {actual} != {expected}")
    dst_reg = dst_root / "registry.json"
    dst_reg.write_text(json.dumps({"kind": "p3-local-technical-fixture-selection", "fixtures": [fx]}, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    # Prove copied registry resolves and hashes from its own directory.
    fixture_from_registry(dst_reg, track)
    return dst_reg


def registry_files(registry: Path, track: str) -> dict[str, Path]:
    fx = fixture_from_registry(registry, track)
    out = {}
    for dd, rel in fx["materializer"]["files"].items():
        p = (registry.parent / rel).resolve()
        if not p.is_file():
            raise RuntimeError(f"runtime registry missing physical file {dd}: {p}")
        out[dd] = p
    return out


def wire_input_pins(registry: Path, track: str) -> list[dict[str, Any]]:
    files = registry_files(registry, track)
    pins = []
    for dd in TRACKS[track]["wire_dds"]:
        p = files[dd]
        pins.append({"dd": dd, **pin(p), "base64Sha256": sha256_bytes(base64.b64encode(p.read_bytes()))})
    return pins


def effective_input_hash(pins: list[dict[str, Any]]) -> str:
    return sha256_bytes(canonical([{k: p[k] for k in ("dd", "sha256", "bytes")} for p in pins]))


def _load_zero_facade():
    spec = importlib.util.spec_from_file_location("matrix_v2_zero_facade", CYCLE / "P2c-zero-shot" / "p2c_facade.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def zero_request(contract_id: str, track: str, registry: Path) -> dict[str, Any]:
    return _load_zero_facade().sample_request_for(contract_id, track, registry)


def decode_amount(raw: bytes) -> float:
    text = raw.decode("ascii")
    sign = 1
    zone = "pqrstuvwxy"
    if text[-1] in zone:
        sign = -1
        text = text[:-1] + str(zone.index(text[-1]))
    return float(Decimal(sign * int(text)) / Decimal(100))


def tx_record_to_dict(rec: bytes, *, numeric: bool) -> dict[str, Any]:
    if len(rec) != 350:
        raise ValueError(f"TRAN/DALY record must be 350 bytes, got {len(rec)}")
    def s(a: int, b: int) -> str:
        return rec[a:b].decode("ascii", "replace").rstrip()
    category = s(18, 22)
    merchant = s(143, 152)
    return {
        "transactionId": s(0, 16),
        "typeCode": s(16, 18),
        "categoryCode": int(category) if numeric else category,
        "source": s(22, 32),
        "description": s(32, 132),
        "amount": decode_amount(rec[132:143]),
        "merchantId": int(merchant) if numeric else merchant,
        "merchantName": s(152, 202),
        "merchantCity": s(202, 252),
        "merchantZip": s(252, 262),
        "cardNumber": s(262, 278),
        "originalTimestamp": s(278, 304),
        "processingTimestamp": s(304, 330),
        "filler": s(330, 350),
    }


def records_from_file(path: Path, size: int) -> list[bytes]:
    data = path.read_bytes()
    if len(data) % size:
        raise ValueError(f"fixed file length not divisible by {size}: {path}")
    return [data[i:i+size] for i in range(0, len(data), size)]


def few_request(contract_id: str, track: str, registry: Path) -> dict[str, Any]:
    files = registry_files(registry, track)
    numeric = contract_id in {"E2-2", "E2-3"}
    def txs(dd: str) -> list[dict[str, Any]]:
        return [tx_record_to_dict(r, numeric=numeric) for r in records_from_file(files[dd], 350)]
    def bindings() -> dict[str, str]:
        fields = {
            "posting": ["crossReferences", "accounts", "categoryBalances", "transactionOutput", "rejectionOutput"],
            "interest": ["categoryBalances", "crossReferences", "accounts", "disclosureGroups", "transactionOutput"],
            "reporting": ["crossReferences", "transactionTypes", "transactionCategories", "reportOutput"],
        }[track]
        return {k: "p3-local-technical-fixture-selection:" + k for k in fields}
    if track == "posting":
        key = "dailyTransactions" if contract_id == "E2-1" else "transactions"
        body = {key: txs("DALYTRAN")}
    elif track == "interest":
        prefix = files["PARMFILE"].read_text(encoding="ascii")
        if contract_id == "E2-2":
            body = {"parameterDate": prefix, "parameterLength": 10}
        else:
            body = {"transactionIdPrefix": prefix}
    else:
        tx = txs("TRANFILE")
        date_records = [r.decode("ascii", "replace") for r in records_from_file(files["DATEPARM"], 80)]
        body = {"transactions": tx, "dateParameterRecords": date_records if contract_id == "E2-3" else [d.rstrip() for d in date_records]}
    if contract_id == "E2-2":
        body = {"bindings": bindings(), **body}
    return body


def request_for(contract: dict[str, Any], track: str, registry: Path) -> tuple[dict[str, Any], str]:
    arm = contract["arm"].lower().replace("_", "-")
    cid = contract["contractId"]
    if arm == "zero-shot":
        return zero_request(cid, track, registry), "materialized_from_physical_fixture_bytes"
    if arm == "few-shot":
        return few_request(cid, track, registry), "materialized_from_physical_fixture_bytes"
    if arm == "sdd":
        return {}, "external_physical_fixture_registry_only_public_contract_body_is_empty_object"
    raise RuntimeError(f"unsupported arm: {arm}")


def validate_against_contract(contract: dict[str, Any], op: dict[str, Any], body: dict[str, Any]) -> list[str]:
    spec = load_contract_source(contract)
    schema = (((spec.get("paths") or {}).get(op["path"]) or {}).get(op["method"].lower()) or {}).get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
    validator = ExactDraft202012Validator(schema, resolver=RefResolver.from_schema(spec))
    return [e.message for e in sorted(validator.iter_errors(body), key=lambda e: [str(p) for p in e.path])]


def build_suite(out: Path) -> dict[str, Any]:
    contracts = load_contract_config()
    cases: list[dict[str, Any]] = []
    for contract in contracts:
        cid = contract["contractId"]
        arm = contract["arm"]
        for track, spec in TRACKS.items():
            op = operation_for(contract, track)
            for source_case_id in spec["cases"]:
                reg = materialize_runtime_registry(out, track, source_case_id)
                pins = wire_input_pins(reg, track)
                body, authority = request_for(contract, track, reg)
                errors = validate_against_contract(contract, op, body)
                if errors:
                    raise RuntimeError(f"request schema validation failed {cid}:{track}:{source_case_id}: {errors}")
                case_id = f"ESSENTIAL12x7-V2-{cid}-{source_case_id}"
                case = {
                    "case_id": case_id,
                    "suite_id": SUITE_ID,
                    "origin": "complementary-matrix-v2",
                    "request": {"method": op["method"], "path": op["path"], "headers": [["content-type", "application/json"]], "body_kind": "json", "body_b64": encode_body(body)},
                    "resource_package_id": f"runtime-fixture-registry:{track}:{source_case_id}",
                    "timeout_seconds": 120.0,
                    "parameters": {
                        "contractId": cid,
                        "contractArm": arm,
                        "operationId": op["operationId"],
                        "track": track,
                        "sourceCaseId": source_case_id,
                        "essentialScenarioId": source_case_id,
                        "checkerObligations": spec["obligations"],
                        "runtimeFixtureRegistry": str(reg),
                        "runtimeFixtureRegistryPin": pin(reg),
                        "runtimeFixtureSourceRegistryPin": pin(scenario_source_registry(track, source_case_id)),
                        "wireInputPins": pins,
                        "effectiveInputSha256": effective_input_hash(pins),
                        "requestInputAuthority": authority,
                        "requestSchemaValidation": "jsonschema_Draft202012Validator_full_original_request_schema_allOf_refs",
                        "semanticCheckerPackage": "P3/complementary-validation-implementation-v3",
                        "semanticCheckerMode": "qualified-field-values-not-file-existence",
                        "officialCampaign": False,
                        "resetPolicy": "fresh application/workdir per case; registry selected by v2 target factory, not public JSON",
                    },
                    "provenance": [f"complementary-matrix-v2:{cid}:{track}:{source_case_id}"],
                    "expectation": {"expectation_id": f"qualified-semantic-checker:{track}:{source_case_id}", "checks": {"status": [200, 400, 500, 503]}},
                }
                cases.append(case)
    suite = {"suite_id": SUITE_ID, "cases": cases}
    suite["suite_freeze_sha256"] = suite_hash(dict(suite))
    out.mkdir(parents=True, exist_ok=True)
    suite_path = (out / "suite.freeze.json").resolve()
    suite_path.write_text(json.dumps(suite, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"suite": suite, "suitePath": suite_path}


def verify_plan(plan_path: Path) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    suite_path = Path(plan["suitePath"])
    suite_data = json.loads(suite_path.read_text(encoding="utf-8"))
    recorded = suite_data.pop("suite_freeze_sha256", None)
    actual = suite_hash(suite_data)
    failures = []
    if recorded != actual:
        failures.append("suite_freeze_sha256_mismatch")
    cases = suite_data.get("cases", [])
    if len(cases) != 84:
        failures.append(f"candidate_application_count:{len(cases)}!=84")
    if {c["parameters"]["sourceCaseId"] for c in cases} != set(ALL_CASES):
        failures.append("essential_12_source_case_set_mismatch")
    if len({c["parameters"]["contractId"] for c in cases}) != 7:
        failures.append("contract_count_not_7")
    for case in cases:
        params = case.get("parameters", {})
        b = json.loads(base64.b64decode(case["request"].get("body_b64") or "e30=").decode("utf-8"))
        if "complementaryFixtureSelection" in b:
            failures.append(f"invented_public_fixture_field:{case['case_id']}")
        if params.get("contractArm", "").lower() == "sdd" and b != {}:
            failures.append(f"sdd_body_not_empty_object:{case['case_id']}")
        reg = Path(params.get("runtimeFixtureRegistry", ""))
        if not reg.is_file():
            failures.append(f"runtime_fixture_registry_missing:{case['case_id']}")
            continue
        rpin = params.get("runtimeFixtureRegistryPin") or {}
        if pin(reg) != rpin:
            failures.append(f"runtime_fixture_registry_pin_mismatch:{case['case_id']}")
        for fp in params.get("wireInputPins", []):
            p = Path(fp["path"])
            if not p.is_file() or pin(p)["sha256"] != fp["sha256"] or pin(p)["bytes"] != fp["bytes"]:
                failures.append(f"wire_input_pin_mismatch:{case['case_id']}:{fp.get('dd')}")
    if failures:
        raise RuntimeError(";".join(failures))
    return {"ok": True, "cases": len(cases)}


def plan(out: Path) -> dict[str, Any]:
    built = build_suite(out)
    suite_path = built["suitePath"]
    runner_plan_path = (out / "runner-plan.json").resolve()
    cmd = [str(PY), str(RUNNER_CLI), "--mode", "plan", "--suite", str(suite_path), "--config", str(CONFIG), "--output", str(runner_plan_path)]
    proc = subprocess.run(cmd, cwd=RUNNER_ROOT, text=True, capture_output=True, timeout=180)
    if proc.returncode != 0:
        raise RuntimeError(f"runner plan failed rc={proc.returncode}\nSTDOUT={proc.stdout}\nSTDERR={proc.stderr}")
    runner_plan = json.loads(runner_plan_path.read_text(encoding="utf-8"))
    if runner_plan["totals"]["cases"] != 84:
        raise RuntimeError(f"runner plan case count {runner_plan['totals']['cases']} != 84")
    execute_cmd = [str(PY), str(ROOT / "matrix_cli.py"), "--execute", "--plan-file", str((out / "execution-plan.json").resolve()), "--output", str((out / "FULL-84-RUN").resolve()), "--official-ready-json", str((out / "parent-official-ready.template.json").resolve())]
    manifest = {
        "kind": "complementary-matrix-v2-plan",
        "createdUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "essential 12 x seven contracts with per-scenario physical runtime registries and E1/E2 request bytes materialized from fixture files; not metadata-only",
        "planPath": str((out / "execution-plan.json").resolve()),
        "suitePath": str(suite_path),
        "runnerPlanPath": str(runner_plan_path),
        "totals": {"contracts": 7, "essentialScenarios": 12, "candidateApplications": 84},
        "runnerPlanTotals": runner_plan["totals"],
        "parentOwnedLaunchCommand": execute_cmd,
        "parentReadyJsonTemplate": {"officialReady": True, "campaignAuthorized": True, "scope": "main-process complementary matrix-v2 essential12x7 execution"},
        "requestPolicy": "no invented public fixture selector fields; SDD bodies are {}; zero/few-shot request wire arrays/arguments are materialized from selected physical fixture bytes",
    }
    (out / "execution-plan.json").write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "parent-official-ready.template.json").write_text(json.dumps(manifest["parentReadyJsonTemplate"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    verify_plan(out / "execution-plan.json")
    return manifest


def _load_runner_module():
    spec = importlib.util.spec_from_file_location("matrix_v2_runner", RUNNER_SRC)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["matrix_v2_runner"] = mod
    spec.loader.exec_module(mod)
    return mod


def patch_isolated_fewshot_registry(cycle: Path) -> dict[str, Any]:
    path = cycle / "P2c-few-shot" / "p2c_facade.py"
    text = path.read_text(encoding="utf-8")
    old = 'REGISTRY = CYCLE / "P3" / "technical-packages-v3-argument" / "registry.json"'
    new = 'REGISTRY = Path(os.environ.get("P2C_FEWSHOT_REGISTRY", str(CYCLE / "P3" / "technical-packages-v3-argument" / "registry.json")))'
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return {"patched": True, "path": str(path), "reason": "isolated copy only; allow per-case physical fixture registry without public request fields", "sha256": sha256_file(path)}
    if "P2C_FEWSHOT_REGISTRY" in text:
        return {"patched": False, "path": str(path), "reason": "already patched", "sha256": sha256_file(path)}
    raise RuntimeError("isolated few-shot registry patch target not found")


def execute(plan_file: Path, output: Path, official_ready_json: Path | None, smoke_case_ids: set[str] | None = None) -> dict[str, Any]:
    output = output.resolve()
    manifest = json.loads(plan_file.read_text(encoding="utf-8"))
    verify_plan(plan_file)
    suite_path = Path(manifest["suitePath"])
    runner_output = output
    if smoke_case_ids is not None:
        suite = json.loads(suite_path.read_text(encoding="utf-8"))
        suite.pop("suite_freeze_sha256", None)
        suite["cases"] = [c for c in suite["cases"] if c["case_id"] in smoke_case_ids]
        if len(suite["cases"]) != len(smoke_case_ids):
            raise RuntimeError(f"smoke case selection mismatch: requested {smoke_case_ids}, got {[c['case_id'] for c in suite['cases']]}")
        suite["suite_id"] = SUITE_ID + "-SMOKE"
        suite["suite_freeze_sha256"] = suite_hash({"suite_id": suite["suite_id"], "cases": suite["cases"]})
        output.mkdir(parents=True, exist_ok=True)
        suite_path = output / "smoke-suite.freeze.json"
        suite_path.write_text(json.dumps(suite, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        runner_output = output / "run"
    runner = _load_runner_module()
    contracts = runner.load_contract_registry(CONFIG)
    ready = bool(official_ready_json and json.loads(official_ready_json.read_text()).get("officialReady") is True and json.loads(official_ready_json.read_text()).get("campaignAuthorized") is True)
    target_factory, prepared = runner.prepare_real_p2b_target(runner_output, contracts, None)
    campaign_output = runner_output / "campaign"
    prepared["matrixV2FewshotPatch"] = patch_isolated_fewshot_registry(Path(prepared["cycle"]))
    unified = sys.modules.get("aws_campaign_unified_preflight_v3")
    cycle = Path(prepared["cycle"])
    py = Path(prepared.get("python") or PY)
    def factory(case: Any) -> Any:
        cid = runner.case_contract_id(case)
        arm = contracts[cid].arm.lower().replace("_", "-")
        reg = Path(case.parameters["runtimeFixtureRegistry"])
        if arm == "zero-shot":
            return unified.PosixSpawnServer([str(py), str(cycle / "P2c-zero-shot/p2c_facade.py"), "serve", "--contract", cid, "--output-root", "{workdir}/zero-shot-runs", "--registry", str(reg), "--port-file", "{port_file}"], cwd=cycle / "P2c-zero-shot")
        if arm == "few-shot":
            return unified.PosixSpawnServer([str(py), str(cycle / "P2c-few-shot/p2c_facade.py"), "serve", "--contract-id", cid, "--port-file", "{port_file}"], cwd=cycle / "P2c-few-shot", env={"P2C_FEWSHOT_REGISTRY": str(reg)})
        if arm == "sdd":
            return unified.target_p2b(cycle, reg)
        raise RuntimeError(arm)
    return runner.execute_campaign([suite_path], contracts, campaign_output, target_factory=factory, official_ready=ready, official_execution=smoke_case_ids is None, prepared=prepared)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--smoke-two-sdd-posting", action="store_true")
    ap.add_argument("--output", type=Path)
    ap.add_argument("--plan-file", type=Path)
    ap.add_argument("--official-ready-json", type=Path)
    ap.add_argument("--verify-plan", type=Path)
    args = ap.parse_args(argv)
    try:
        if args.verify_plan:
            print(json.dumps(verify_plan(args.verify_plan), sort_keys=True))
            return 0
        if args.plan:
            if not args.output:
                raise RuntimeError("--output required")
            print(json.dumps(plan(args.output), indent=2, sort_keys=True, ensure_ascii=False))
            return 0
        if args.execute or args.smoke_two_sdd_posting:
            if not args.plan_file or not args.output:
                raise RuntimeError("--plan-file and --output required")
            smoke = None
            if args.smoke_two_sdd_posting:
                smoke = {"ESSENTIAL12x7-V2-E3-SDD-stage6r3-valid-new-tcatbal", "ESSENTIAL12x7-V2-E3-SDD-stage6r3-reject-card-missing"}
            report = execute(args.plan_file, args.output, args.official_ready_json, smoke)
            print(json.dumps({"ok": not report["stopPolicy"]["stopped"], "attempted": report["totals"]["attempted"], "output": str(args.output), "stopPolicy": report["stopPolicy"]}, sort_keys=True))
            return 0 if not report["stopPolicy"]["stopped"] else 3
        raise RuntimeError("choose --plan, --verify-plan, --execute, or --smoke-two-sdd-posting")
    except Exception as exc:
        if hasattr(exc, "details"):
            print(json.dumps({"error": str(exc), "details": getattr(exc, "details")}, indent=2, ensure_ascii=False), file=sys.stderr)
        else:
            print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

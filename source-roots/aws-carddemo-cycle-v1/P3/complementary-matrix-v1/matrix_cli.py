#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
P3 = ROOT.parent
CYCLE = P3.parent
HARNESS_SRC = P3 / "campaign-harness-v3" / "src"
RUNNER = P3 / "aws-campaign-runner-v3" / "aws_campaign_runner_cli.py"
CONFIG = P3 / "campaign-configuration-v2" / "campaign-config-v2.json"
CROSSARM_SUITE = P3 / "complementary-crossarm-v1" / "run-20260916T112642Z" / "freeze" / "suite.freeze.json"
PY = CYCLE / "P2a" / ".venv" / "bin" / "python"
if not PY.exists():
    PY = Path(sys.executable)

TRACKS = {
    "posting": {
        "cases": ["valid-new-tcatbal", "valid-existing-tcatbal", "reject-card-missing", "reject-account-missing", "reject-limit", "reject-expiry"],
        "obligations": ["POSTTRAN-OBL-003", "POSTTRAN-OBL-004", "POSTTRAN-OBL-006", "POSTTRAN-OBL-009"],
    },
    "interest": {
        "cases": ["rates-specific-default-zero", "single-final-eof"],
        "obligations": ["INTCALC-OBL-005", "INTCALC-OBL-006"],
    },
    "reporting": {
        "cases": ["date-boundaries-in-out-v1", "empty-in-range-v1", "card-break-two-groups-v1", "pagination-threshold-20-v1"],
        "obligations": ["TRANREPT-OBL-002", "TRANREPT-OBL-006"],
    },
}
ALL_CASES = TRACKS["posting"]["cases"] + TRACKS["interest"]["cases"] + TRACKS["reporting"]["cases"]


def canonical(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def pin(path: Path) -> dict[str, Any]:
    return {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}


def suite_hash(body_without_hash: dict[str, Any]) -> str:
    return sha256_bytes(canonical(body_without_hash))


def body_obj(case: dict[str, Any]) -> dict[str, Any]:
    b64 = case["request"].get("body_b64")
    if not b64:
        return {}
    return json.loads(base64.b64decode(b64).decode("utf-8"))


def encode_body(obj: dict[str, Any]) -> str:
    return base64.b64encode(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).decode("ascii")


def load_contracts() -> list[dict[str, Any]]:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    return cfg["contracts"]["contracts"]


def load_templates() -> dict[tuple[str, str], dict[str, Any]]:
    data = json.loads(CROSSARM_SUITE.read_text(encoding="utf-8"))
    templates = {}
    for case in data["cases"]:
        params = case["parameters"]
        templates[(params["contractId"], params["track"])] = case
    if len(templates) != 21:
        raise RuntimeError(f"expected 21 crossarm templates, got {len(templates)}")
    return templates


def essential_pin_source(track: str, case_id: str) -> dict[str, Any]:
    if track == "posting":
        p = P3 / "complementary-posting-essential-v1" / "evidence" / "posting-essential-report.json"
    elif track == "interest":
        p = P3 / "complementary-interest-essential-v1" / "evidence" / case_id / "input-freeze.json"
    else:
        p = P3 / "complementary-reporting-essential-v1" / "evidence" / "frozen-inputs" / case_id / "freeze-manifest.json"
    if not p.exists():
        raise RuntimeError(f"missing actual fixture freeze/evidence for {track}:{case_id}: {p}")
    return pin(p)


def case_body_for(template: dict[str, Any], track: str, source_case_id: str, contract_arm: str) -> tuple[dict[str, Any], str | None]:
    obj = body_obj(template)
    if contract_arm.lower() == "sdd":
        # Public SDD Stage 6r3 accepts approved {} external resources only. The
        # source fixture remains pinned in metadata, but cannot be expressed on the
        # public request surface without adding non-contract fields.
        return {}, "sdd_public_contract_accepts_empty_body_only_fixture_specific_inputs_nonexpressible"
    obj["complementaryFixtureSelection"] = {
        "sourceCaseId": source_case_id,
        "track": track,
        "authority": "P3/complementary-matrix-v1 prospective frozen input metadata; business bytes pinned separately",
        "notOracle": True,
    }
    return obj, None


def build_suite(out: Path) -> dict[str, Any]:
    contracts = load_contracts()
    templates = load_templates()
    cases: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    fixture_freeze_pins: list[dict[str, Any]] = []
    for contract in contracts:
        cid = contract["contractId"]
        arm = contract["arm"]
        for track, spec in TRACKS.items():
            template = templates[(cid, track)]
            for source_case_id in spec["cases"]:
                new = json.loads(json.dumps(template))
                body, block = case_body_for(template, track, source_case_id, arm)
                new["case_id"] = f"ESSENTIAL12x7-{cid}-{source_case_id}"
                new["suite_id"] = "P3-COMPLEMENTARY-MATRIX-V1-ESSENTIAL12x7"
                new["origin"] = "complementary-matrix-v1"
                new["request"]["body_b64"] = encode_body(body)
                new["request"]["body_kind"] = "json"
                new["parameters"] = dict(new.get("parameters", {}))
                new["parameters"].update({
                    "contractId": cid,
                    "contractArm": arm,
                    "track": track,
                    "sourceCaseId": source_case_id,
                    "essentialScenarioId": source_case_id,
                    "checkerObligations": spec["obligations"],
                    "prospectiveFrozenInput": True,
                    "fixturePin": essential_pin_source(track, source_case_id),
                    "semanticCheckerPackage": "P3/complementary-validation-implementation-v3",
                    "semanticCheckerMode": "qualified-field-values-not-file-existence",
                    "officialCampaign": False,
                    "resetPolicy": "fresh application/workdir per case by aws-campaign-runner-v3",
                })
                new["provenance"] = [f"complementary-matrix-v1:{cid}:{track}:{source_case_id}"]
                new["expectation"] = {"expectation_id": f"qualified-semantic-checker:{track}:{source_case_id}", "checks": {"status": [200, 400, 500, 503]}}
                if block:
                    new["parameters"]["nonexpressibleBlock"] = block
                    blocks.append({"caseId": new["case_id"], "contractId": cid, "track": track, "sourceCaseId": source_case_id, "blockReason": block})
                cases.append(new)
                fixture_freeze_pins.append(new["parameters"]["fixturePin"])
    suite = {"suite_id": "P3-COMPLEMENTARY-MATRIX-V1-ESSENTIAL12x7", "cases": cases}
    suite["suite_freeze_sha256"] = suite_hash(dict(suite))
    out.mkdir(parents=True, exist_ok=True)
    suite_path = (out / "suite.freeze.json").resolve()
    suite_path.write_text(json.dumps(suite, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    return {"suite": suite, "suitePath": suite_path, "blocks": blocks, "fixtureFreezePins": fixture_freeze_pins}


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
    by_source = {c["parameters"]["sourceCaseId"] for c in cases}
    if by_source != set(ALL_CASES):
        failures.append("essential_12_source_case_set_mismatch")
    by_contract = {c["parameters"]["contractId"] for c in cases}
    if len(by_contract) != 7:
        failures.append(f"contract_count:{len(by_contract)}!=7")
    for case in cases:
        fp = case["parameters"].get("fixturePin") or {}
        p = Path(fp.get("path", ""))
        if not p.exists() or sha256_file(p) != fp.get("sha256") or p.stat().st_size != fp.get("bytes"):
            failures.append(f"fixture_pin_mismatch:{case['case_id']}")
    if failures:
        raise RuntimeError(";".join(failures))
    return {"ok": True, "cases": len(cases), "contracts": len(by_contract), "essentialScenarios": len(by_source)}


def plan(out: Path) -> dict[str, Any]:
    built = build_suite(out)
    suite_path = built["suitePath"]
    runner_plan_path = (out / "runner-plan.json").resolve()
    cmd = [str(PY), str(RUNNER), "--mode", "plan", "--suite", str(suite_path), "--config", str(CONFIG), "--output", str(runner_plan_path)]
    proc = subprocess.run(cmd, cwd=P3 / "aws-campaign-runner-v3", text=True, capture_output=True, timeout=180)
    if proc.returncode != 0:
        raise RuntimeError(f"runner plan failed rc={proc.returncode}\nSTDOUT={proc.stdout}\nSTDERR={proc.stderr}")
    runner_plan = json.loads(runner_plan_path.read_text(encoding="utf-8"))
    if runner_plan["totals"]["cases"] != 84:
        raise RuntimeError(f"runner plan case count {runner_plan['totals']['cases']} != 84")
    ready_path = (out / "parent-official-ready.json").resolve()
    full_run_path = (out / "FULL-84-RUN").resolve()
    launch = [str(PY), str(RUNNER), "--mode", "execute", "--suite", str(suite_path), "--config", str(CONFIG), "--official-ready-json", str(ready_path), "--output", str(full_run_path)]
    manifest = {
        "kind": "complementary-matrix-v1-plan",
        "createdUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "prospective frozen essential 12 x seven contracts; no external generation; plan only unless parent runs launch command",
        "suitePath": str(suite_path),
        "runnerPlanPath": str(runner_plan_path),
        "totals": {"contracts": 7, "essentialScenarios": 12, "candidateApplications": 84, "nonexpressibleBlocks": len(built["blocks"])},
        "nonexpressibleBlocks": built["blocks"],
        "fixtureFreezePins": built["fixtureFreezePins"],
        "semanticCheckers": {"package": str(P3 / "complementary-validation-implementation-v3"), "mode": "qualified semantic checkers; field values and provenance, not file-exists checks"},
        "parentOwnedLaunchCommand": launch,
        "parentReadyJsonTemplate": {"officialReady": True, "campaignAuthorized": True, "scope": "main-process complementary essential12x7 execution"},
        "runnerPlanTotals": runner_plan["totals"],
    }
    (out / "execution-plan.json").write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    ready_payload = {"officialReady": True, "campaignAuthorized": True, "scope": "main-process complementary essential12x7 execution", "planSha256": sha256_file(out / "execution-plan.json") if (out / "execution-plan.json").exists() else None}
    # Write both an executable readiness file and a template. This does not start
    # execution; it lets the parent own the actual launch without another edit.
    ready_path.write_text(json.dumps(ready_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "parent-official-ready.template.json").write_text(json.dumps(manifest["parentReadyJsonTemplate"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    verify_plan(out / "execution-plan.json")
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--execute", action="store_true", help="intentionally not implemented here; parent must run aws-campaign-runner-v3 launch command")
    ap.add_argument("--output", type=Path)
    ap.add_argument("--verify-plan", type=Path)
    args = ap.parse_args(argv)
    try:
        if args.verify_plan:
            result = verify_plan(args.verify_plan)
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.execute:
            raise RuntimeError("child_owned_execute_blocked_use_parentOwnedLaunchCommand_from_execution_plan")
        if args.plan:
            if not args.output:
                raise RuntimeError("--output required")
            result = plan(args.output)
            print(json.dumps({"ok": True, "plan": str(args.output / "execution-plan.json"), "candidateApplications": result["totals"]["candidateApplications"], "launch": result["parentOwnedLaunchCommand"]}, ensure_ascii=False))
            return 0
        raise RuntimeError("choose --plan or --verify-plan")
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

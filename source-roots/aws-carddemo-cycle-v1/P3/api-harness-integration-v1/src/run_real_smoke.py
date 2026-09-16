#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from api_harness_integration import (
    ContractChecker,
    HarnessCase,
    PosixSpawnServer,
    build_fixture_registry_from_copy,
    copy_current_fixture_package,
    send_json,
    sha256_file,
)

ROOT = Path(__file__).resolve().parents[1]
CYCLE = ROOT.parents[1]
PREP = CYCLE.parent / "aws-carddemo-preparation"
ISO = ROOT / "isolated-cycle"
PY = CYCLE / "P2a" / ".venv" / "bin" / "python"
if not PY.exists():
    PY = Path(sys.executable)

TRACKS = ("posting", "interest", "reporting")


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_dir(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=False)


def prepare_isolated_workspace() -> dict[str, Any]:
    if ISO.exists():
        shutil.rmtree(ISO)
    cycle = ISO / "aws-carddemo-cycle-v1"
    prep = ISO / "aws-carddemo-preparation"
    # Contracts and API implementations copied; originals remain untouched.
    copy_file(CYCLE / "P2a" / "openapi-carddemo-stage6r3.yaml", cycle / "P2a" / "openapi-carddemo-stage6r3.yaml")
    copy_file(CYCLE / "P2a" / "openapi-carddemo-stage6r3.json", cycle / "P2a" / "openapi-carddemo-stage6r3.json")
    for rel in ["P2b/p2b_binding.py", "P2b/runtime_observations.py", "P2b/write_observer.c", "P2b/interest_driver.cbl"]:
        copy_file(CYCLE / rel, cycle / rel)
    for arm in ["P2c-zero-shot", "P2c-few-shot"]:
        copy_file(CYCLE / arm / "p2c_facade.py", cycle / arm / "p2c_facade.py")
    for cid in ["E1-3", "E2-2"]:
        copy_file(CYCLE / "collection-01" / cid / "response-original.txt", cycle / "collection-01" / cid / "response-original.txt")
    # COBOL source corpus and support needed by copied P2b build.
    copy_file(PREP / "evidence" / "research-package.json", prep / "evidence" / "research-package.json")
    copy_dir(PREP / "research-corpus", prep / "research-corpus")
    copy_dir(PREP / "expanded-batch" / "support", prep / "expanded-batch" / "support")
    # Current candidate fixture bytes copied into the isolated registry directory.
    package_copy = copy_current_fixture_package(CYCLE / "P3" / "fixture-materialization-v2" / "package", cycle / "P3" / "technical-packages-v3-argument" / "package")
    registry = build_fixture_registry_from_copy(package_copy, cycle / "P3" / "technical-packages-v3-argument" / "registry.json")
    return {
        "cycle": str(cycle),
        "prep": str(prep),
        "registry": str(registry),
        "registry_sha256": sha256_file(registry),
        "python": str(PY),
    }


def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def latest_audit(root: Path, track: str, before: set[Path]) -> Path | None:
    candidates = [p for p in root.rglob("audit.json") if p not in before and f"/{track}-" in str(p)]
    if not candidates:
        candidates = [p for p in root.rglob("audit.json") if p not in before]
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def make_cases(cycle: Path, registry: Path) -> list[HarnessCase]:
    zero = import_module(cycle / "P2c-zero-shot" / "p2c_facade.py", "iso_zero_facade")
    few = import_module(cycle / "P2c-few-shot" / "p2c_facade.py", "iso_few_facade")
    cases: list[HarnessCase] = []
    p2a = cycle / "P2a" / "openapi-carddemo-stage6r3.yaml"
    for track in TRACKS:
        cases.append(HarnessCase("sdd-p2b", "E3-01-stage6r3", track, "POST", f"/{track}", {}, p2a))
    c1 = zero.load_contract("E1-3")
    by_track = {meta["track"]: meta["path"] for meta in zero.load_operation_index(c1).values()}
    for track in TRACKS:
        cases.append(HarnessCase("zero-shot-p2c", "E1-3", track, "POST", by_track[track], zero.sample_request_for("E1-3", track, registry), cycle / "collection-01" / "E1-3" / "response-original.txt"))
    for track in TRACKS:
        cases.append(HarnessCase("few-shot-p2c", "E2-2", track, "POST", few.CONTRACTS["E2-2"].paths[track], few.sample_request("E2-2", track), cycle / "collection-01" / "E2-2" / "response-original.txt"))
    return cases


def server_for(case: HarnessCase, cycle: Path, registry: Path, app_dir: Path) -> PosixSpawnServer:
    if case.arm == "sdd-p2b":
        return PosixSpawnServer([str(PY), str(cycle / "P2b" / "p2b_binding.py"), "serve", "--port-file", "{port_file}"], cwd=cycle / "P2b", env={"P2B_FIXTURE_REGISTRY": str(registry)})
    if case.arm == "zero-shot-p2c":
        return PosixSpawnServer([str(PY), str(cycle / "P2c-zero-shot" / "p2c_facade.py"), "serve", "--contract", "E1-3", "--output-root", str(app_dir / "runs"), "--registry", str(registry), "--port-file", "{port_file}"], cwd=cycle / "P2c-zero-shot", env={})
    if case.arm == "few-shot-p2c":
        return PosixSpawnServer([str(PY), str(cycle / "P2c-few-shot" / "p2c_facade.py"), "serve", "--contract-id", "E2-2", "--port-file", "{port_file}"], cwd=cycle / "P2c-few-shot", env={})
    raise ValueError(case.arm)


def audit_for(case: HarnessCase, cycle: Path, app_dir: Path, response_json: Any, before_audits: set[Path]) -> Path | None:
    if isinstance(response_json, dict):
        for key in ("p2bAuditPath", "auditPath", "audit_path"):
            value = response_json.get(key)
            if value and Path(value).is_file():
                return Path(value)
    if case.arm == "sdd-p2b":
        return latest_audit(cycle / "P2b" / "runs", case.track, before_audits)
    if case.arm == "zero-shot-p2c":
        return latest_audit(app_dir, case.track, before_audits)
    return latest_audit(cycle / "P2c-few-shot" / "runs", case.track, before_audits)


def classify_reach(audit_path: Path | None, cycle: Path, registry: Path) -> dict[str, Any]:
    if not audit_path or not audit_path.is_file():
        return {"audit_found": False, "reached_cobol": False}
    audit = json.loads(audit_path.read_text())
    p2b_path = Path(audit.get("p2bAuditPath", "")) if "p2bAuditPath" in audit else audit_path
    if p2b_path.is_file() and p2b_path != audit_path:
        p2b_audit = json.loads(p2b_path.read_text())
    else:
        p2b_audit = audit
    workdir = p2b_audit.get("INV", {}).get("workdir")
    selected = p2b_audit.get("RES", {}).get("selected_fixture") or {}
    fixture_registry = selected.get("registryPath")
    return {
        "audit_found": True,
        "audit_path": str(audit_path),
        "p2b_audit_path": str(p2b_path) if p2b_path else None,
        "workdir": workdir,
        "workdir_under_isolated_cycle": bool(workdir and str(Path(workdir).resolve()).startswith(str(cycle.resolve()))),
        "fixture_registry": fixture_registry,
        "fixture_registry_isolated": bool(fixture_registry and Path(fixture_registry).resolve() == registry.resolve()),
        "reached_cobol": bool(p2b_audit.get("RESP", {}).get("reached_cobol")),
        "program_exit": p2b_audit.get("RESP", {}).get("program_exit"),
        "response_status_in_audit": p2b_audit.get("RESP", {}).get("status"),
        "failure_events": p2b_audit.get("FAIL", {}).get("events", []),
    }


def main() -> None:
    prep = prepare_isolated_workspace()
    cycle = Path(prep["cycle"]); registry = Path(prep["registry"])
    cases = make_cases(cycle, registry)
    report: dict[str, Any] = {"kind": "api-harness-integration-v1-real-smoke", "scope": "technical smoke only; not official suites/oracles", "prepared": prep, "cases": [], "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    before_all_audits = set(cycle.rglob("audit.json"))
    for idx, case in enumerate(cases, 1):
        app_dir = ROOT / "run-output" / f"{idx:02d}-{case.arm}-{case.track}"
        if app_dir.exists():
            shutil.rmtree(app_dir)
        app_dir.mkdir(parents=True)
        checker = ContractChecker(case.openapi_path)
        before_audits = set(cycle.rglob("audit.json")) | set(app_dir.rglob("audit.json")) | before_all_audits
        target = server_for(case, cycle, registry, app_dir)
        row: dict[str, Any] = {"index": idx, "arm": case.arm, "contract_id": case.contract_id, "track": case.track, "method": case.method, "path": case.path, "request_sha256": __import__('hashlib').sha256(json.dumps(case.body, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), "contract_path": str(case.openapi_path), "contract_sha256": sha256_file(case.openapi_path)}
        try:
            base = target.start(app_dir / "server")
            status, ctype, raw = send_json(base, case.method, case.path, case.body)
            try:
                parsed = json.loads(raw.decode())
            except Exception:
                parsed = None
            check = checker.check(case.method, case.path, status, ctype, raw)
            audit_path = audit_for(case, cycle, app_dir, parsed, before_audits)
            row.update({"base_url": base, "status": status, "content_type": ctype, "response_bytes": len(raw), "response_sha256": __import__('hashlib').sha256(raw).hexdigest(), "checker": check.__dict__, "reach": classify_reach(audit_path, cycle, registry)})
        except Exception as exc:
            row.update({"infra_error": repr(exc)})
        finally:
            row["target_quiet_including_descendants"] = target.stop()
            row["spawn_method"] = target.spawn_method
            row["server_pid"] = target.pid
            row["server_stdout"] = str(target.stdout_path) if target.stdout_path else None
            row["server_stderr"] = str(target.stderr_path) if target.stderr_path else None
        report["cases"].append(row)
    report["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report["summary"] = {
        "planned": len(cases),
        "http_completed": sum(1 for r in report["cases"] if "status" in r),
        "schema_or_documented_500_valid": sum(1 for r in report["cases"] if r.get("checker", {}).get("ok")),
        "reached_cobol": sum(1 for r in report["cases"] if r.get("reach", {}).get("reached_cobol")),
        "quiet": sum(1 for r in report["cases"] if r.get("target_quiet_including_descendants")),
    }
    out = ROOT / "integration-report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report["summary"], indent=2))
    print(out)


if __name__ == "__main__":
    main()

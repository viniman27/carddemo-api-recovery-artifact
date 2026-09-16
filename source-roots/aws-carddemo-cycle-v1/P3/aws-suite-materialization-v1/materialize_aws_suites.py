#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT
T2_SRC = P3 / "t2-offline-preparation-v4" / "src"
T3_SRC = P3 / "t3-campaign-adapter-v3" / "src"
T3_EXT = P3 / "t3-sdd-external-selection-v3"
HARNESS_SRC = P3 / "campaign-harness-v3" / "src"
for path in (T2_SRC, T3_SRC, T3_EXT, HARNESS_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from campaign_harness import Suite, freeze_suite, load_frozen_suite  # noqa: E402
from t2_offline_bridge import DEFAULT_SEEDS, generate_t2_offline_suite_for_contract, load_current_config  # noqa: E402
import t3_campaign_adapter as t3  # noqa: E402
import sdd_external_selection as ext  # noqa: E402

TRACKS = {
    "posting": "posting.candidate-v1-physical-v2",
    "interest": "interest.candidate-v1-physical-v2",
    "reporting": "reporting.candidate-v1-physical-v2",
}
CAPABILITIES = ["CBTRN02C_POSTTRAN", "CBACT04C_INTCALC", "CBTRN03C_TRANREPT"]


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(obj))


def pin(path: Path) -> dict[str, Any]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_path(path)}


def package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def fixture_manifest_readback(manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest_path.parent
    packages = {}
    errors = []
    for fixture in manifest.get("fixtures", []):
        track = str(fixture.get("track"))
        fixture_id = str(fixture.get("fixtureId"))
        package_path = base / track
        pkg = (manifest.get("packages") or {}).get(track) or {}
        files = []
        for rel, expected in sorted(((pkg.get("inventory") or {}).get("files") or {}).items()):
            path = package_path / rel
            if not path.exists():
                errors.append({"track": track, "fixtureId": fixture_id, "path": rel, "error": "missing"})
                continue
            got = {"path": rel, "bytes": path.stat().st_size, "sha256": sha256_path(path)}
            if got["bytes"] != expected.get("bytes") or got["sha256"] != expected.get("sha256"):
                errors.append({"track": track, "fixtureId": fixture_id, "path": rel, "expected": expected, "actual": got})
            files.append(got)
        packages[track] = {
            "fixtureId": fixture_id,
            "packagePath": str(package_path),
            "resetPolicy": fixture.get("resetPolicy") or pkg.get("resetPolicy") or "fresh physical copy per case/application",
            "files": files,
            "logicalResources": {
                "sequential": pkg.get("sequential", []),
                "indexed": pkg.get("indexed", []),
            },
        }
    return {"manifest": pin(manifest_path), "status": "PASS" if not errors else "FAIL", "errors": errors, "packages": packages}


def materialize_t2(cfg: dict[str, Any], out: Path, seeds: list[int], max_examples_per_direction: int) -> dict[str, Any]:
    t2_out = out / "T2"
    contracts_out = t2_out / "contracts"
    contracts_out.mkdir(parents=True, exist_ok=True)
    reports = []
    errors = []
    suites = []
    for contract in (cfg.get("contracts") or {}).get("contracts", []):
        cid = str(contract["contractId"])
        cdir = contracts_out / cid
        if cdir.exists():
            errors.append({"contractId": cid, "classification": "output_exists_not_regenerated", "path": str(cdir)})
            continue
        try:
            report = generate_t2_offline_suite_for_contract(
                cfg,
                cid,
                cdir,
                seeds=seeds,
                directions=["positive", "negative"],
                max_examples_per_direction=max_examples_per_direction,
            )
            suite = load_frozen_suite(cdir / "T2-suite.json")
            suites.append(suite)
            reports.append({**report, "suiteReadbackCases": len(suite.cases), "suitePath": str(cdir / "T2-suite.json")})
        except Exception as exc:
            errors.append({"contractId": cid, "classification": "generation_exception_preserved", "error": repr(exc), "partialReport": str(cdir / "generation-report.partial.json"), "partialRequests": str(cdir / "frozen-t2-requests.partial.json")})
    all_cases = [case for suite in suites for case in suite.cases]
    combined = Suite("T2-AWS-offline-all7", all_cases)
    combined_path = t2_out / "T2-AWS-offline-all7-suite.json"
    freeze_suite(combined, combined_path)
    loaded = load_frozen_suite(combined_path)
    by_resource: dict[str, int] = {}
    for case in loaded.cases:
        by_resource[case.resource_package_id] = by_resource.get(case.resource_package_id, 0) + 1
    underfilled = [g for rep in reports for g in rep.get("generation", []) if int(g.get("generated", -1)) != int(max_examples_per_direction)]
    summary = {
        "kind": "aws-t2-real-offline-materialization-v1",
        "status": "PASS" if not errors and not underfilled else ("UNDERFILLED" if underfilled and not errors else "PARTIAL"),
        "underfilledGenerationCells": underfilled,
        "officialCampaign": False,
        "runtimeExecuted": False,
        "networkCallsDuringGeneration": 0,
        "contractsAttempted": len((cfg.get("contracts") or {}).get("contracts", [])),
        "contractsSucceeded": len(reports),
        "operationCountSucceeded": sum(len(r.get("generation", [])) for r in reports) // (len(seeds) * 2) if seeds else 0,
        "seeds": seeds,
        "directions": ["positive", "negative"],
        "perOperationPerSeed": {"positive": max_examples_per_direction, "negative": max_examples_per_direction, "total": max_examples_per_direction * 2},
        "budgetTransfer": "disabled",
        "retries": "disabled",
        "shrinking": False,
        "replayDuringGeneration": False,
        "requestOccurrences": len(loaded.cases),
        "resourcePackageCounts": by_resource,
        "suite": pin(combined_path),
        "reports": reports,
        "errors": errors,
    }
    write_json(t2_out / "T2-materialization-report.json", summary)
    return summary


def sdd_enriched_for_out(out: Path) -> dict[str, Any]:
    sdd_out = out / "T3" / "sdd-external-selection-v3-readback"
    plan = ext.build_external_selection_plan(P3)
    ext.write_versioned_copies(plan, P3, sdd_out)
    return ext.enrich_with_external_selection(plan, P3, sdd_out)["enriched"]


def filter_sdd_suite(suite: Suite, report: dict[str, Any], enriched: dict[str, Any]) -> tuple[Suite, dict[str, Any]]:
    restrictions = {
        cell["cellId"]: ext.effective_transition_restriction(cell)
        for cell in enriched.get("cells", [])
        if cell.get("contractId") == ext.SDD_REGISTRY_ID and cell.get("executableEligible") is True
    }
    selected = []
    excluded = []
    for case in suite.cases:
        cell_ref = case.parameters.get("cellRef")
        transition_id = str(case.parameters.get("transitionId"))
        allowed = restrictions.get(cell_ref)
        if allowed is None or transition_id in allowed:
            selected.append(case)
        else:
            excluded.append({"caseId": case.case_id, "cellRef": cell_ref, "transitionId": transition_id, "restriction": "explicit_empty_effective_selectable_transitions" if not allowed else "not_in_declared_effective_selectable_transitions"})
    out_report = dict(report)
    out_report.update({"unfilteredAcceptedCount": len(suite.cases), "acceptedCount": len(selected), "excludedCount": len(excluded), "excludedByEffectiveSelection": sorted(excluded, key=lambda x: (str(x["cellRef"]), str(x["transitionId"]), str(x["caseId"])))})
    return Suite("T3", selected), out_report


def materialize_t3(cfg: dict[str, Any], out: Path, max_depth: int, max_paths_per_track_fixture: int) -> dict[str, Any]:
    t3_out = out / "T3"
    contracts_out = t3_out / "contracts"
    contracts_out.mkdir(parents=True, exist_ok=True)
    registry = t3.load_contract_registry(P3)
    sdd_enriched = sdd_enriched_for_out(out)
    reports = []
    errors = []
    suites = []
    for cid in registry:
        cdir = contracts_out / cid
        cdir.mkdir(parents=True, exist_ok=True)
        try:
            source = t3.resolve_contract_source(P3, cid)
            if cid == ext.SDD_REGISTRY_ID:
                enriched = sdd_enriched
            else:
                inputs = t3.load_real_inputs(P3, cid)
                enriched = inputs["enriched_plan"]
            suite, report = t3.build_t3_suite(
                cid,
                P3 / "reference-executable-v4" / "model.json",
                enriched,
                P3 / "fixture-materialization-v2" / "package" / "manifest.json",
                source,
                capabilities=CAPABILITIES,
                max_depth=max_depth,
                max_paths_per_capability=max_paths_per_track_fixture,
            )
            if cid == ext.SDD_REGISTRY_ID:
                suite, report = filter_sdd_suite(suite, report, enriched)
            suite_path = cdir / "T3-suite.json"
            freeze_suite(Suite(f"T3-{cid}", suite.cases), suite_path)
            loaded = load_frozen_suite(suite_path)
            reports.append({**report, "contractId": cid, "budget": {"maxDepth": max_depth, "maxPathsPerTrackFixture": max_paths_per_track_fixture}, "suiteReadbackCases": len(loaded.cases), "suitePath": str(suite_path)})
            suites.append(loaded)
        except Exception as exc:
            errors.append({"contractId": cid, "classification": "t3_materialization_exception_preserved", "error": repr(exc)})
    all_cases = [case for suite in suites for case in suite.cases]
    combined = Suite("T3-AWS-offline-all7", all_cases)
    combined_path = t3_out / "T3-AWS-offline-all7-suite.json"
    freeze_suite(combined, combined_path)
    loaded = load_frozen_suite(combined_path)
    by_contract = {r["contractId"]: r["suiteReadbackCases"] for r in reports}
    by_resource: dict[str, int] = {}
    for case in loaded.cases:
        by_resource[case.resource_package_id] = by_resource.get(case.resource_package_id, 0) + 1
    summary = {
        "kind": "aws-t3-real-offline-materialization-v1",
        "status": "PASS" if not errors else "PARTIAL",
        "officialCampaign": False,
        "runtimeExecuted": False,
        "networkCallsDuringGeneration": 0,
        "contractsAttempted": len(registry),
        "contractsSucceeded": len(reports),
        "budget": {"maxDepth": max_depth, "maxPathsPerTrackFixture": max_paths_per_track_fixture},
        "requestOccurrences": len(loaded.cases),
        "resourcePackageCounts": by_resource,
        "suite": pin(combined_path),
        "byContract": by_contract,
        "reports": reports,
        "errors": errors,
    }
    write_json(t3_out / "T3-materialization-report.json", summary)
    return summary


def verify_materialization(out: Path) -> dict[str, Any]:
    t2 = json.loads((out / "T2" / "T2-materialization-report.json").read_text(encoding="utf-8"))
    t3r = json.loads((out / "T3" / "T3-materialization-report.json").read_text(encoding="utf-8"))
    t2_suite = load_frozen_suite(Path(t2["suite"]["path"]))
    t3_suite = load_frozen_suite(Path(t3r["suite"]["path"]))
    t2_bad = [c.to_dict() for c in t2_suite.cases if c.resource_package_id not in set(TRACKS.values())]
    t3_bad = [c.to_dict() for c in t3_suite.cases if c.resource_package_id not in set(TRACKS.values())]
    underfilled = t2.get("underfilledGenerationCells", [])
    return {
        "kind": "aws-suite-materialization-v1-readback-verification",
        "status": "PASS" if not t2_bad and not t3_bad and t2.get("status") == "PASS" and t3r.get("status") == "PASS" and not underfilled else "FAIL",
        "t2Cases": len(t2_suite.cases),
        "t3Cases": len(t3_suite.cases),
        "t2UnderfilledGenerationCells": len(underfilled),
        "t2BadResourceBindings": len(t2_bad),
        "t3BadResourceBindings": len(t3_bad),
        "t2SuitePin": pin(Path(t2["suite"]["path"])),
        "t3SuitePin": pin(Path(t3r["suite"]["path"])),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(P3 / "aws-suite-materialization-v1" / "run"))
    ap.add_argument("--config", default=str(P3 / "campaign-configuration-v2" / "campaign-config-v2.json"))
    ap.add_argument("--max-examples-per-direction", type=int, default=50)
    ap.add_argument("--t3-max-depth", type=int, default=6)
    ap.add_argument("--t3-max-paths-per-track-fixture", type=int, default=50)
    ap.add_argument("--force-new", action="store_true")
    ns = ap.parse_args(argv)
    out = Path(ns.output).resolve()
    if out.exists():
        if ns.force_new:
            shutil.rmtree(out)
        else:
            raise SystemExit(f"refusing to overwrite output directory: {out}")
    out.mkdir(parents=True)
    started = time.time()
    cfg = load_current_config(Path(ns.config))
    env = {
        "python": sys.version,
        "executable": sys.executable,
        "packages": {name: package_version(name) for name in ["schemathesis", "hypothesis", "jsonschema", "requests", "PyYAML"]},
        "modules": {
            "t2_offline_bridge": pin(T2_SRC / "t2_offline_bridge.py"),
            "t3_campaign_adapter": pin(T3_SRC / "t3_campaign_adapter.py"),
            "sdd_external_selection_v3": pin(T3_EXT / "sdd_external_selection.py"),
            "campaign_harness_v3": pin(HARNESS_SRC / "campaign_harness.py"),
        },
    }
    fixtures = fixture_manifest_readback(P3 / "fixture-materialization-v2" / "package" / "manifest.json")
    write_json(out / "environment-and-input-readback.json", {"environment": env, "fixtures": fixtures})
    t2_report = materialize_t2(cfg, out, list(DEFAULT_SEEDS), int(ns.max_examples_per_direction))
    t3_report = materialize_t3(cfg, out, int(ns.t3_max_depth), int(ns.t3_max_paths_per_track_fixture))
    verification = verify_materialization(out)
    write_json(out / "READBACK-VERIFICATION.json", verification)
    final = {
        "kind": "aws-suite-materialization-v1-final-report",
        "status": "PASS" if verification["status"] == "PASS" and fixtures["status"] == "PASS" else "FAIL",
        "officialCampaign": False,
        "runtimeExecuted": False,
        "networkCallsDuringGeneration": 0,
        "startedAtUnix": started,
        "finishedAtUnix": time.time(),
        "output": str(out),
        "fixturesStatus": fixtures["status"],
        "T2": {k: t2_report[k] for k in ["status", "contractsSucceeded", "operationCountSucceeded", "requestOccurrences", "perOperationPerSeed", "suite", "resourcePackageCounts"]},
        "T3": {k: t3_report[k] for k in ["status", "contractsSucceeded", "requestOccurrences", "budget", "suite", "resourcePackageCounts", "byContract"]},
        "verification": verification,
        "errors": {"T2": t2_report.get("errors", []), "T3": t3_report.get("errors", [])},
    }
    write_json(out / "FINAL-REPORT.json", final)
    print(json.dumps(final, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if final["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

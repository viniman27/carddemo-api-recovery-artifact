from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .materializer import build_crossarm_suite, pin_file, sha256_bytes

ROOT = Path(__file__).resolve().parents[3]
P3 = ROOT / "P3"
RUNNER_V3 = P3 / "aws-campaign-runner-v3" / "src" / "aws_campaign_runner.py"


def _import_runner():
    sys.path.insert(0, str(P3 / "campaign-harness-v3" / "src"))
    spec = importlib.util.spec_from_file_location("crossarm_runner_v3", RUNNER_V3)
    if not spec or not spec.loader:
        raise RuntimeError("cannot import runner v3")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["crossarm_runner_v3"] = mod
    spec.loader.exec_module(mod)
    return mod


def _search_roots(row_or_app: dict[str, Any]) -> list[Path]:
    roots: list[Path] = []
    app = row_or_app.get("application", row_or_app)
    for raw in (app.get("workdir"),):
        if raw:
            p = Path(raw)
            if p.exists():
                roots.append(p)
    measurement = row_or_app.get("measurement") or {}
    audit = measurement.get("auditSelection", {}).get("auditPath")
    if audit:
        p = Path(audit).parent
        if p.exists():
            roots.append(p)
    run_dir = measurement.get("runDir")
    if run_dir:
        p = Path(run_dir)
        if p.exists():
            roots.append(p)
    return roots


def _find_files(row_or_app: dict[str, Any], suffix: str) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for root in _search_roots(row_or_app):
        for p in sorted(root.rglob(suffix)):
            if p.is_file() and p not in seen:
                seen.add(p)
                out.append(p)
    return out


def _file_pin(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": sha256_bytes(data)}


def _business_check(row: dict[str, Any]) -> dict[str, Any]:
    track = row.get("track")
    receipt = row.get("receipt", {})
    app = row.get("application", {})
    structural = row.get("structuralCheck", {})
    evidence: list[dict[str, Any]] = []
    status = receipt.get("status")
    if not structural.get("ok"):
        return {"status": "inconclusive", "checker": "typed-local-byte-check", "reason": f"structural_not_ok:{structural.get('classification')}", "evidence": evidence}
    if status != 200:
        return {"status": "inconclusive", "checker": "typed-local-byte-check", "reason": f"documented_non_200:{status}", "evidence": evidence}
    if track == "posting":
        outputs = _find_files(row, "TRANFILE.after")
        rejects = _find_files(row, "DALYREJS")
        evidence = [_file_pin(p) for p in outputs + rejects]
        if any(p.stat().st_size >= 350 for p in outputs):
            return {"status": "pass", "checker": "posting-byte-effects", "assertion": "posted transaction output bytes observed", "evidence": evidence}
        return {"status": "inconclusive", "checker": "posting-byte-effects", "reason": "no_nonempty_TRANFILE.after", "evidence": evidence}
    if track == "interest":
        outputs = _find_files(row, "TRANSACT")
        evidence = [_file_pin(p) for p in outputs]
        if any(p.stat().st_size >= 350 for p in outputs):
            return {"status": "pass", "checker": "interest-byte-effects", "assertion": "interest transaction bytes observed", "evidence": evidence}
        return {"status": "inconclusive", "checker": "interest-byte-effects", "reason": "no_nonempty_TRANSACT", "evidence": evidence}
    if track == "reporting":
        outputs = _find_files(row, "TRANREPT")
        evidence = [_file_pin(p) for p in outputs]
        if any(p.stat().st_size > 0 for p in outputs):
            return {"status": "pass", "checker": "reporting-byte-effects", "assertion": "report bytes observed", "evidence": evidence}
        return {"status": "inconclusive", "checker": "reporting-byte-effects", "reason": "empty_or_missing_TRANREPT", "evidence": evidence}
    return {"status": "inconclusive", "checker": "typed-local-byte-check", "reason": "unknown_track", "evidence": evidence}


def compare_report(campaign_report: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for suite in campaign_report.get("suiteReports", []):
        rows.extend(suite.get("checks", []))
    cases = []
    for row in rows:
        check = _business_check(row)
        receipt = row.get("receipt", {})
        structural = row.get("structuralCheck", {})
        cases.append({
            "caseId": row.get("case_id"),
            "contractId": row.get("contractId"),
            "operationId": row.get("operationId"),
            "track": row.get("track"),
            "httpStatus": receipt.get("status"),
            "responseSha256": receipt.get("response_sha256"),
            "structural": {"ok": structural.get("ok"), "classification": structural.get("classification")},
            "businessCheck": check,
            "measurementAdmissibility": row.get("measurement", {}).get("admissibility"),
        })
    by_status = Counter(c["businessCheck"]["status"] for c in cases)
    by_track = defaultdict(Counter)
    by_contract = defaultdict(Counter)
    for c in cases:
        by_track[c["track"]][c["businessCheck"]["status"]] += 1
        by_contract[c["contractId"]][c["businessCheck"]["status"]] += 1
    return {
        "kind": "complementary-crossarm-v1-comparison",
        "summary": {
            "attempted": len(cases),
            "businessStatusCounts": dict(by_status),
            "byTrack": {k: dict(v) for k, v in by_track.items()},
            "byContract": {k: dict(v) for k, v in by_contract.items()},
            "boundedLocalApiCallLimit": 21,
            "officialCampaign": False,
        },
        "cases": cases,
    }


def run(cycle_root: Path, out: Path) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=False)
    suite_path, manifest = build_crossarm_suite(cycle_root, out / "freeze")
    runner = _import_runner()
    contracts = runner.load_contract_registry()
    report = runner.execute_campaign([suite_path], contracts, out / "run", official_ready=False, official_execution=False)
    comparison = compare_report(report)
    final = {"kind": "complementary-crossarm-v1-run", "materialization": manifest, "campaignReport": pin_file(out / "run" / "campaign-report.json", cycle_root, "campaign-report"), "comparison": comparison, "scope": "bounded prospective local cross-arm complement; 7 contracts x 3 tracks; one attempt; no external calls; no official campaign promotion"}
    (out / "comparison.json").write_text(json.dumps(comparison, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "RUN-SUMMARY.json").write_text(json.dumps(final, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return final


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycle-root", type=Path, default=ROOT)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    payload = run(args.cycle_root, args.out)
    print(json.dumps({"ok": True, "attempted": payload["comparison"]["summary"]["attempted"], "businessStatusCounts": payload["comparison"]["summary"]["businessStatusCounts"], "out": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

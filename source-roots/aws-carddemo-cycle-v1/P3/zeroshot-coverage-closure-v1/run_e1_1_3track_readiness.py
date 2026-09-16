#!/usr/bin/env python3
"""Bounded zero-shot E1-1 3-track local readiness run.

Uses the amended T3 binding-closure candidate cases, filters only E1-1
posting/interest/reporting, and executes the official-capable runner in local
readiness mode (not official campaign execution). No suites are generated from
contracts here; requests are preserved from the amended candidate.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER_SRC = ROOT / "aws-campaign-runner-v3" / "src"
HARNESS_SRC = ROOT / "campaign-harness-v3" / "src"
for p in [str(RUNNER_SRC), str(HARNESS_SRC)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from campaign_harness import load_frozen_suite, freeze_suite, Suite  # noqa: E402
import aws_campaign_runner as runner  # noqa: E402

OUT_ROOT = ROOT / "zeroshot-coverage-closure-v1"
SOURCE_SUITE = ROOT / "t3-binding-closure-v1" / "amended-candidates" / "T3-BINDING-CLOSURE-V1.json"
SUBSET_SUITE = OUT_ROOT / "inputs" / "T3-BINDING-CLOSURE-V1-E1-1-3TRACK.json"
REPORT_DIR = OUT_ROOT / "real-readiness-E1-1-3track"
SUMMARY = OUT_ROOT / "SUMMARY.json"
TRACKS = {"posting", "interest", "reporting"}


def contract_id(case) -> str | None:
    params = case.parameters or {}
    return params.get("contractId") or params.get("contract_id")


def track(case) -> str | None:
    params = case.parameters or {}
    return params.get("track")


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    SUBSET_SUITE.parent.mkdir(parents=True, exist_ok=True)
    if REPORT_DIR.exists():
        raise SystemExit(f"refusing to overwrite existing report dir: {REPORT_DIR}")
    source = load_frozen_suite(SOURCE_SUITE)
    selected = [c for c in source.cases if contract_id(c) == "E1-1" and track(c) in TRACKS]
    selected_tracks = sorted(str(track(c)) for c in selected)
    if selected_tracks != ["interest", "posting", "reporting"]:
        raise SystemExit(f"expected one E1-1 case for each track, got {selected_tracks}")
    subset = Suite("ZEROSHOT-COVERAGE-CLOSURE-E1-1-3TRACK", selected)
    freeze_suite(subset, SUBSET_SUITE)

    contracts = runner.load_contract_registry()
    report = runner.execute_campaign(
        [SUBSET_SUITE],
        contracts,
        REPORT_DIR,
        official_ready=False,
        official_execution=False,
        resume=False,
    )
    checks = report["suiteReports"][0]["checks"]
    receipts = []
    for check in checks:
        measurement = check.get("measurement", {})
        receipts.append({
            "case_id": check.get("case_id"),
            "contractId": check.get("contractId"),
            "operationId": check.get("operationId"),
            "track": check.get("track"),
            "status": check.get("receipt", {}).get("status"),
            "structuralOk": check.get("structuralCheck", {}).get("ok"),
            "measurementAdmissibility": measurement.get("admissibility") or measurement.get("measurementAdmissibility"),
            "gcovPrefixObservedInCommandLog": measurement.get("gcovPrefixObservedInCommandLog"),
            "businessCommandEnvEvidenceCount": len(measurement.get("businessCommandEnvEvidence") or []),
            "businessGcdaPresent": measurement.get("businessGcdaPresent"),
            "gcovValid": measurement.get("gcovValidation", {}).get("valid"),
            "runDir": measurement.get("runDir"),
            "auditPath": measurement.get("auditSelection", {}).get("auditPath"),
        })
    summary = {
        "kind": "zeroshot-coverage-closure-v1-e1-1-3track-summary",
        "officialCampaign": False,
        "sourceSuite": str(SOURCE_SUITE),
        "subsetSuite": str(SUBSET_SUITE),
        "reportDir": str(REPORT_DIR),
        "totals": report.get("totals"),
        "stopPolicy": report.get("stopPolicy"),
        "experimentalViolations": report.get("experimentalViolations"),
        "measurementWarnings": report.get("measurementWarnings"),
        "receipts": receipts,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report.get("totals", {}).get("measurement_admissible") == 3 else 4


if __name__ == "__main__":
    raise SystemExit(main())

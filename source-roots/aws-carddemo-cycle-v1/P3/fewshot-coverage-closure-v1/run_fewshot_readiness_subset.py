#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
P3 = ROOT.parent
RUNNER = P3 / "aws-campaign-runner-v3"
CYCLE = P3.parent
sys.path.insert(0, str(RUNNER / "src"))
sys.path.insert(0, str(P3 / "campaign-harness-v3" / "src"))

import aws_campaign_runner as runner  # noqa: E402

CONTRACTS = ["E2-1", "E2-3"]
TRACKS = ["posting", "interest", "reporting"]


def main() -> int:
    out = ROOT / f"evidence-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    contracts = runner.load_contract_registry()
    selection_root = RUNNER / "readiness-selection-v1"
    suite_paths = [selection_root / contract / f"{track}.json" for contract in CONTRACTS for track in TRACKS]
    missing = [str(p) for p in suite_paths if not p.is_file()]
    if missing:
        raise SystemExit(f"missing readiness selections: {missing}")
    report = runner.execute_campaign(suite_paths, contracts, out, official_ready=False, official_execution=False)
    checks = [check for suite in report.get("suiteReports", []) for check in suite.get("checks", [])]
    summary = {
        "output": str(out),
        "contracts": CONTRACTS,
        "tracks": TRACKS,
        "totals": report.get("totals"),
        "stopPolicy": report.get("stopPolicy"),
        "measurementWarnings": report.get("measurementWarnings"),
        "fewshotCoverage": [
            {
                "case_id": c.get("case_id"),
                "track": c.get("measurement", {}).get("track"),
                "admissibility": c.get("measurement", {}).get("admissibility"),
                "reasons": c.get("measurement", {}).get("inadmissibilityReasons") or c.get("measurement", {}).get("reasons"),
                "businessProgram": c.get("measurement", {}).get("businessProgram"),
                "businessGcdaPresent": c.get("measurement", {}).get("businessGcdaPresent"),
                "gcovPrefixObserved": c.get("measurement", {}).get("gcovPrefixObservedInCommandLog"),
                "gcovExit": c.get("measurement", {}).get("gcov11", {}).get("exit_code"),
                "gcovLinesTotal": c.get("measurement", {}).get("gcov11", {}).get("summaryParsed", {}).get("linesTotal"),
                "mainGeneratedC": c.get("measurement", {}).get("correctedParser", {}).get("mainGeneratedC"),
                "programExit": c.get("measurement", {}).get("programExit"),
                "normalProcessExitObserved": c.get("measurement", {}).get("normalProcessExitObserved"),
                "auditPath": c.get("measurement", {}).get("auditSelection", {}).get("auditPath"),
                "runDir": c.get("measurement", {}).get("runDir"),
            }
            for c in checks
        ],
    }
    (out / "fewshot-coverage-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if not report.get("stopPolicy", {}).get("stopped") else 3


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CYCLE = ROOT.parent.parent
FREEZE = CYCLE / "P3" / "campaign-freeze-package-v1"
OUT_SELECTION = ROOT / "readiness-selection-v1"
P2A_PY = CYCLE / "P2a" / ".venv" / "bin" / "python"

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(CYCLE / "P3" / "campaign-harness-v3" / "src"))

from campaign_harness import Suite, freeze_suite, load_frozen_suite  # noqa: E402
import aws_campaign_runner as runner  # noqa: E402

CONTRACTS = ["E1-1", "E1-2", "E1-3", "E2-1", "E2-2", "E2-3", "E3-SDD-stage6r3"]
TRACKS = ["posting", "interest", "reporting"]


def file_pin(path: Path) -> dict:
    return runner.file_pin(path)


def select_cases() -> tuple[list[Path], dict]:
    OUT_SELECTION.mkdir(parents=True, exist_ok=True)
    suite_paths: list[Path] = []
    selected = []
    seen = set()
    for contract in CONTRACTS:
        for track in TRACKS:
            selected_case = None
            selected_source = None
            selected_condition = None
            for condition in ("T1", "T3", "T4", "T2"):
                source = FREEZE / contract / f"{condition}.json"
                suite = load_frozen_suite(source)
                matches = [c for c in suite.cases if c.parameters.get("contractId") == contract and c.parameters.get("track") == track]
                positive = [c for c in matches if "positive" in c.case_id.lower()]
                non_negative = [c for c in matches if "negative" not in c.case_id.lower()]
                chosen = (positive or non_negative or matches)
                if chosen:
                    selected_case = chosen[0]
                    selected_source = source
                    selected_condition = condition
                    break
            if selected_case is None or selected_source is None or selected_condition is None:
                raise RuntimeError(f"no frozen case for {contract} {track}")
            case = copy.deepcopy(selected_case)
            original_id = case.case_id
            case.case_id = f"READINESS21-{contract}-{track}-{original_id}"
            case.suite_id = f"READINESS21-{contract}-{track}"
            case.provenance = tuple(list(case.provenance) + [f"local-readiness-v3:selected-from:{selected_source.relative_to(CYCLE)}:{original_id}"])
            out = OUT_SELECTION / contract / f"{track}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            freeze_suite(Suite(case.suite_id, [case]), out)
            body = case.request.body_bytes_or_none()
            selected.append({
                "contractId": contract,
                "track": track,
                "suitePath": str(out),
                "suitePin": file_pin(out),
                "selectedCondition": selected_condition,
                "sourceSuite": str(selected_source),
                "sourceSuitePin": file_pin(selected_source),
                "sourceCaseId": original_id,
                "readinessCaseId": case.case_id,
                "operationId": case.parameters.get("operationId"),
                "method": case.request.method,
                "path": case.request.path,
                "bodyBytes": 0 if body is None else len(body),
                "bodySha256": None if body is None else runner.sha256_bytes(body),
                "resourcePackageId": case.resource_package_id,
            })
            ident = (contract, track)
            if ident in seen:
                raise RuntimeError(f"duplicate selection {ident}")
            seen.add(ident)
            suite_paths.append(out)
    manifest = {
        "kind": "aws-carddemo-local-readiness-21-selection-v1",
        "scope": "one frozen case per contract per track from campaign-freeze-package-v1, preferring T1 positive/non-negative cases for local runtime reachability and falling back to T3/T4/T2 where needed; request bytes preserved; case/suite ids changed only for bounded readiness filesystem uniqueness",
        "officialCampaign": False,
        "sourcePackage": str(FREEZE / "MANIFEST.json"),
        "sourcePackagePin": file_pin(FREEZE / "MANIFEST.json"),
        "counts": {"contracts": len(CONTRACTS), "tracks": len(TRACKS), "cases": len(selected)},
        "selected": selected,
    }
    (OUT_SELECTION / "SELECTION-MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return suite_paths, manifest


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if len(argv) != 1:
        print("usage: local_readiness_21.py OUTPUT_DIR", file=sys.stderr)
        return 2
    output = Path(argv[0]).resolve()
    contracts = runner.load_contract_registry()
    suite_paths, manifest = select_cases()
    report = runner.execute_campaign(suite_paths, contracts, output, official_ready=False, official_execution=False)
    report["selectionManifest"] = str(OUT_SELECTION / "SELECTION-MANIFEST.json")
    report["selectionCounts"] = manifest["counts"]
    (output / "campaign-report.json").write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = {
        "ok": not report["stopPolicy"]["stopped"],
        "output": str(output),
        "selectionManifest": str(OUT_SELECTION / "SELECTION-MANIFEST.json"),
        "totals": report["totals"],
        "stopPolicy": report["stopPolicy"],
        "officialExecutionStarted": report["officialExecutionStarted"],
        "localReadinessExecution": report["localReadinessExecution"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if summary["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())

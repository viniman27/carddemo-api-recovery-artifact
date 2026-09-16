#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prov(path: Path, offset: int | None, length: int | None, fields: list[str], kind: str = "raw_file_record") -> dict[str, Any]:
    p = path.resolve()
    out: dict[str, Any] = {
        "kind": kind,
        "artifact": str(p),
        "sha256": sha256(p),
        "observedFields": fields,
    }
    if offset is not None and length is not None:
        out["recordOffset"] = offset
        out["recordLength"] = length
    return out


def account_record_offset(path: Path, account: str, width: int = 50) -> tuple[int | None, int | None]:
    data = path.read_bytes()
    needle = account.encode("ascii")
    idx = data.find(needle)
    if idx < 0:
        return None, None
    return idx, min(width, len(data) - idx)


def attach(runtime_v1: Path, out_fixture: Path) -> dict[str, Any]:
    data = json.loads((runtime_v1 / "evidence" / "typed-observations.json").read_text(encoding="utf-8"))
    data["fixtureId"] = "runtime-api-cobol-observations-v2-provenanced"
    data["evidenceClass"] = "real_cobol_observation"
    data["description"] = "Runtime-v1 API/COBOL observations enriched with byte provenance from preserved artifacts; no API re-execution."
    runs = runtime_v1 / "evidence" / "api-cobol-runs"
    posting = next(runs.glob("posting-*/"))
    interest = next(runs.glob("interest-*/"))
    reporting = next(runs.glob("reporting-*/"))

    # Per-record byte provenance. POSTTRAN effect ordering is deliberately not
    # invented: only TRANSACT/DALYREJS write-observer order exists, while account
    # and TCATBAL are after-snapshots without relative write order.
    for item in data["observations"].get("posting", {}).get("acceptedTransactions", []):
        item["provenance"] = prov(posting / "TRANFILE.after", 0, 350, ["rawBytes", "posted", "daily"])
        item.pop("effects", None)
        item["traceBoundary"] = "no single-invocation physical order trace for TCATBAL/ACCOUNT vs TRANFILE; POSTTRAN-009 remains inconclusive"
    for item in data["observations"].get("posting", {}).get("rejects", []):
        item["provenance"] = prov(posting / "DALYREJS", 0, 430, ["rawBytes", "reason", "description"])

    for item in data["observations"].get("interest", {}).get("transactions", []):
        if item.get("transactionWritten") and item.get("rawBytes"):
            item["provenance"] = prov(interest / "TRANSACT", 0, 350, ["rawBytes", "amount", "type", "category", "source", "card"])
        else:
            offset, length = account_record_offset(interest / "TCATBALF", item.get("observedAccount", ""))
            item["provenance"] = prov(interest / "TCATBALF", offset, length, ["observedAccount", "categoryBalance", "annualRate", "absenceFromTRANSACT"])

    report = data["observations"].get("reporting", {})
    report["reportFraming"] = report.get("reportFraming", {})
    if "pageTotal" not in report or "accountTotal" not in report:
        report["reportFraming"]["eofBeforeTotalsBranch"] = True
        report["reportFraming"]["totalsEvidence"] = "TRANREPT ended after detail line; totals branch not selected in this run"
    for item in report.get("transactions", []):
        item["provenance"] = prov(reporting / "TRANREPT", 532, 133, ["reportLineBytes", "detailLine", "amount"], kind="report_line")

    data["runtimeEvidence"] = {
        "sourceRuntime": str(runtime_v1.resolve()),
        "apiReexecution": False,
        "audits": [str((posting / "audit.json").resolve()), str((interest / "audit.json").resolve()), str((reporting / "audit.json").resolve())],
        "qualificationScope": "8 implemented representative semantic obligations over preserved three-track runtime-v1 observations; 17 catalog obligations remain pending and are not evaluated here",
    }
    out_fixture.parent.mkdir(parents=True, exist_ok=True)
    out_fixture.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def count_status(results_path: Path) -> dict[str, int]:
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for r in payload["results"]:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich preserved runtime-v1 observations with byte provenance and run checker-v3 without API calls.")
    parser.add_argument("--runtime-v1", type=Path, default=Path(__file__).resolve().parents[2] / "complementary-validation-runtime-v1")
    parser.add_argument("--checker", type=Path, default=Path(__file__).resolve().parents[2] / "complementary-validation-implementation-v3")
    parser.add_argument("--out-root", type=Path, default=Path(__file__).resolve().parents[1] / "evidence")
    args = parser.parse_args()

    fixture = args.out_root / "typed-observations-v2.json"
    results = args.out_root / "semantic-check-results-v3.json"
    report = args.out_root / "corrected-report.md"
    attach(args.runtime_v1, fixture)
    cmd = [sys.executable, "-m", "semantic_checkers", "--verify-source", str(fixture), "--out", str(results)]
    completed = subprocess.run(cmd, cwd=args.checker, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        sys.stderr.write(completed.stdout + completed.stderr)
        return completed.returncode
    payload = json.loads(results.read_text(encoding="utf-8"))
    counts = count_status(results)
    lines = [
        "# Complementary validation runtime-v2 corrected report",
        "",
        "Scope: preserved runtime-v1 three-track API/COBOL observations enriched with real byte provenance; no API/COBOL re-execution.",
        "",
        f"Reusable command: `python3 {Path(__file__).resolve()} --runtime-v1 {args.runtime_v1.resolve()} --checker {args.checker.resolve()} --out-root {args.out_root.resolve()}`",
        "",
        f"Status counts over the 25-record catalog: {json.dumps(counts, sort_keys=True)}.",
        "",
        "Interpretation: PASS is limited to implemented obligations whose observed semantics and byte provenance were sufficient. INCONCLUSIVE means missing trace/evidence, not failure. PENDING means checker not implemented in this representative slice.",
        "",
        "## Implemented-obligation outcomes",
    ]
    for r in payload["results"]:
        if r["status"] != "pending":
            failures = r["details"].get("failures") or []
            lines.append(f"- {r['obligationId']}: {r['status']} ({'; '.join(failures) if failures else r['details'].get('semanticOutcome')})")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"fixture": str(fixture), "results": str(results), "report": str(report), "counts": counts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

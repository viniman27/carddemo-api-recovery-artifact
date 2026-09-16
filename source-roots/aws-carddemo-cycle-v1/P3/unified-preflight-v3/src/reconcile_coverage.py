#!/usr/bin/env python3
"""Reconcile candidate gcov coverage from existing artifacts only.

No COBOL/API/campaign execution is performed here. Inputs are the frozen
coverage-candidate-check-v2 report, its existing .gcov files, and the existing
coverage-prequalification-v1 denominators.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class GcovUnitError(ValueError):
    pass


class MissingGcovUnitError(GcovUnitError):
    pass


class AmbiguousGcovUnitError(GcovUnitError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pct(executed: int, total: int) -> float | None:
    if total == 0:
        return None
    return round((executed / total) * 100, 2)


def metric(executed: int, total: int, *, extra: dict[str, int] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"executed": executed, "total": total, "percent": pct(executed, total)}
    if extra:
        out.update(extra)
    return out


def empty_unit(source: str) -> dict[str, Any]:
    return {
        "source": source,
        "lines": {"executed": 0, "total": 0},
        "branches": {"executed": 0, "taken_at_least_once": 0, "total": 0},
        "calls": {"executed": 0, "total": 0},
        "rawSummaryLines": [],
    }


def parse_gcov_stdout_units(stdout: str) -> list[dict[str, Any]]:
    """Parse gcov stdout per File unit without mixing C/header metrics.

    The old report bug kept the last seen branch/call values while later using
    the aggregate final line count. This parser binds each Lines/Branches/Calls
    line to the current preceding File block and ignores the trailing aggregate.
    """
    units: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in stdout.splitlines():
        m = re.match(r"File '(.+)'", line)
        if m:
            current = empty_unit(m.group(1))
            units.append(current)
            continue
        if current is None:
            continue
        if line.startswith("Creating "):
            current["created"] = line.split("'", 2)[1] if "'" in line else line
            current["rawSummaryLines"].append(line)
            current = None
            continue
        m = re.search(r"Lines executed:([0-9.]+)% of (\d+)", line)
        if m:
            current["lines"] = {"percent": float(m.group(1)), "total": int(m.group(2))}
            current["rawSummaryLines"].append(line)
            continue
        m = re.search(r"Branches executed:([0-9.]+)% of (\d+)", line)
        if m:
            current["branches"]["executedPercent"] = float(m.group(1))
            current["branches"]["total"] = int(m.group(2))
            current["rawSummaryLines"].append(line)
            continue
        m = re.search(r"Taken at least once:([0-9.]+)% of (\d+)", line)
        if m:
            current["branches"]["takenAtLeastOncePercent"] = float(m.group(1))
            current["branches"]["takenTotal"] = int(m.group(2))
            current["rawSummaryLines"].append(line)
            continue
        m = re.search(r"Calls executed:([0-9.]+)% of (\d+)", line)
        if m:
            current["calls"] = {"percent": float(m.group(1)), "total": int(m.group(2))}
            current["rawSummaryLines"].append(line)
            continue
        if line == "No calls":
            current["calls"] = {"percent": None, "total": 0}
            current["rawSummaryLines"].append(line)
    return units


def parse_gcov_file(path: Path) -> dict[str, Any]:
    source = graph = data = None
    runs: int | None = None
    line_total = line_executed = 0
    branch_total = branch_executed = branch_taken = 0
    call_total = call_executed = 0
    line_re = re.compile(r"^\s*([^:]+):\s*(\d+):")
    for raw in path.read_text(errors="replace").splitlines():
        if ":    0:Source:" in raw or ":0:Source:" in raw:
            source = raw.split("Source:", 1)[1]
            continue
        if ":    0:Graph:" in raw or ":0:Graph:" in raw:
            graph = raw.split("Graph:", 1)[1]
            continue
        if ":    0:Data:" in raw or ":0:Data:" in raw:
            data = raw.split("Data:", 1)[1]
            continue
        if ":    0:Runs:" in raw or ":0:Runs:" in raw:
            value = raw.split("Runs:", 1)[1].strip()
            runs = int(value) if value.isdigit() else None
            continue
        m = line_re.match(raw)
        if m:
            count = m.group(1).strip()
            if count not in {"-", "====="}:
                line_total += 1
                if count != "#####":
                    try:
                        if int(count.rstrip("*")) > 0:
                            line_executed += 1
                    except ValueError:
                        pass
            continue
        stripped = raw.strip()
        if stripped.startswith("branch "):
            branch_total += 1
            if "never executed" not in stripped:
                branch_executed += 1
                m_taken = re.search(r"taken\s+(-?\d+)", stripped)
                if m_taken and int(m_taken.group(1)) > 0:
                    branch_taken += 1
            continue
        if stripped.startswith("call "):
            call_total += 1
            if "never executed" not in stripped:
                call_executed += 1
            continue
    if source is None:
        raise MissingGcovUnitError(f"{path} has no Source metadata")
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "source": source,
        "sourceBasename": Path(source).name,
        "graph": graph,
        "data": data,
        "runs": runs,
        "lines": {"executed": line_executed, "total": line_total},
        "branches": {"executed": branch_executed, "taken_at_least_once": branch_taken, "total": branch_total},
        "calls": {"executed": call_executed, "total": call_total},
    }


def classify_unit(program: str, source: str) -> str:
    name = Path(source).name
    if name == f"{program}.c":
        return "main_generated_c"
    if name == f"{program}.c.h":
        return "generated_header_global"
    if name == f"{program}.c.l.h":
        return "generated_header_local"
    return "support_or_other"


def select_units_by_program(program: str, units: list[dict[str, Any]]) -> dict[str, Any]:
    for u in units:
        u["classification"] = classify_unit(program, u["source"])
    mains = [u for u in units if u["classification"] == "main_generated_c"]
    if not mains:
        raise MissingGcovUnitError(f"missing main generated-C gcov unit for {program}; refusing header/support fallback")
    if len(mains) > 1:
        raise AmbiguousGcovUnitError(f"ambiguous main generated-C gcov units for {program}: {[u.get('path') for u in mains]}")
    return {"mainGeneratedC": mains[0], "headersGenerated": [u for u in units if u["classification"].startswith("generated_header")], "supportOrOther": [u for u in units if u["classification"] == "support_or_other"]}


def summarize_old_discrepancy(inv: dict[str, Any], corrected_main: dict[str, Any]) -> dict[str, Any]:
    old = inv.get("gcov11", {}).get("summaryParsed", {})
    return {
        "oldSummaryParsed": {"linesTotal": old.get("linesTotal"), "branchesTotal": old.get("branchesTotal"), "callsTotal": old.get("callsTotal")},
        "correctMainGeneratedC": {
            "linesTotal": corrected_main["lines"]["total"],
            "branchesTotal": corrected_main["branches"]["total"],
            "callsTotal": corrected_main["calls"]["total"],
        },
        "bugClass": "mixed_scope_stdout_summary" if old else "not_present",
        "admissibility": "old mixed-scope summary is retained as stale evidence only and not promoted",
    }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def reconcile_report(base: Path, out_dir: Path) -> dict[str, Any]:
    candidate_path = base / "coverage-candidate-check-v2" / "candidate-coverage-report.json"
    runner_path = base / "coverage-candidate-check-v2" / "run_candidate_coverage_check.py"
    prequal_path = base / "coverage-prequalification-v1" / "evidence-20260915Tprequal-v1" / "denominators-summary.json"
    prequal_manifest_path = base / "coverage-prequalification-v1" / "artifact-manifest.json"
    candidate = load_json(candidate_path)
    prequal = load_json(prequal_path)
    prequal_by_program = {d["program"]: d for d in prequal["denominators"]}

    invocations = []
    all_sources: list[dict[str, Any]] = []
    for inv in candidate.get("invocations", []):
        program = inv["businessProgram"]
        gcov_files = [Path(row["path"]) for row in inv.get("gcov11", {}).get("gcovFiles", [])]
        parsed_units = [parse_gcov_file(p) for p in gcov_files]
        selected = select_units_by_program(program, parsed_units)
        main = selected["mainGeneratedC"]
        preq = prequal_by_program[program]
        comparable = {
            "lines": preq["generatedCLineDenominator"],
            "branches": preq["generatedCBranchDenominator"],
            "calls": preq["generatedCCallDenominator"],
        }
        matches_prequal = comparable == {"lines": main["lines"]["total"], "branches": main["branches"]["total"], "calls": main["calls"]["total"]}
        units_for_report = [selected["mainGeneratedC"], *selected["headersGenerated"], *selected["supportOrOther"]]
        all_sources.extend({"path": u["path"], "sha256": u["sha256"], "bytes": u["bytes"], "role": u["classification"], "invocationIndex": inv["invocationIndex"]} for u in units_for_report)
        invocations.append({
            "invocationIndex": inv["invocationIndex"],
            "track": inv["track"],
            "businessProgram": program,
            "runDir": inv.get("runDir"),
            "programExit": inv.get("programExit"),
            "exitKind": inv.get("exitKind"),
            "normalProcessExitObserved": inv.get("normalProcessExitObserved"),
            "reachedCobol": inv.get("reachedCobol"),
            "gcovPrefixObservedInCommandLog": inv.get("gcovPrefixObservedInCommandLog"),
            "businessGcdaPresent": inv.get("businessGcdaPresent"),
            "measurementAdmissibility": inv.get("measurementAdmissibility"),
            "inadmissibilityReasons": inv.get("inadmissibilityReasons", []),
            "mainGeneratedCComparableDenominator": comparable,
            "mainGeneratedCMatchesPrequalificationDenominator": matches_prequal,
            "correctedMainGeneratedCCounts": {
                "lines": metric(main["lines"]["executed"], main["lines"]["total"]),
                "branchesExecuted": metric(main["branches"]["executed"], main["branches"]["total"]),
                "branchesTakenAtLeastOnce": metric(main["branches"]["taken_at_least_once"], main["branches"]["total"]),
                "calls": metric(main["calls"]["executed"], main["calls"]["total"]),
            },
            "unitBreakdown": units_for_report,
            "oldSummaryDiscrepancy": summarize_old_discrepancy(inv, main),
        })

    totals = []
    for program in sorted(prequal_by_program):
        rows = [i for i in invocations if i["businessProgram"] == program]
        first = rows[0]
        totals.append({
            "program": program,
            "invocationCount": len(rows),
            "tracks": sorted({r["track"] for r in rows}),
            "mainGeneratedCComparableDenominator": first["mainGeneratedCComparableDenominator"],
            "perInvocationMainGeneratedCCounts": [r["correctedMainGeneratedCCounts"] for r in rows],
            "stableDenominatorAcrossInvocations": len({json.dumps(r["mainGeneratedCComparableDenominator"], sort_keys=True) for r in rows}) == 1,
            "matchesPrequalificationDenominatorAllInvocations": all(r["mainGeneratedCMatchesPrequalificationDenominator"] for r in rows),
            "branchInterpretationLimit": "generated-C branch counters are not mapped to COBOL business decisions; no branch C is promoted as a business-decision count",
        })

    reset_evidence = []
    for row in candidate.get("resetEvidence", []):
        reset_evidence.append({
            **row,
            "admissibilityNote": "Distinct runDir/gcovPrefix and gcda presence prove per-invocation file separation only; they do not by themselves prove counter reset semantics beyond the observed isolated artifacts.",
        })

    report = {
        "kind": "coverage-report-reconciliation-v1",
        "status": "corrected-limited-reconciliation-from-existing-gcov-artifacts-only",
        "createdUtc": datetime.now(timezone.utc).isoformat(),
        "inputsPolicy": {
            "noRerunsPerformed": True,
            "inputArtifactsOnly": ["coverage-candidate-check-v2/candidate-coverage-report.json", "coverage-candidate-check-v2 existing per-invocation .gcov files", "coverage-prequalification-v1/evidence-20260915Tprequal-v1/denominators-summary.json"],
            "notOfficialCoverage": True,
            "noBusinessOracleClaim": True,
        },
        "sourceArtifacts": [
            {"role": "candidate_report_stale_mixed_summary_source", "path": str(candidate_path), "sha256": sha256(candidate_path), "bytes": candidate_path.stat().st_size},
            {"role": "candidate_runner_parser_source", "path": str(runner_path), "sha256": sha256(runner_path), "bytes": runner_path.stat().st_size},
            {"role": "prequalification_denominators", "path": str(prequal_path), "sha256": sha256(prequal_path), "bytes": prequal_path.stat().st_size},
            {"role": "prequalification_manifest", "path": str(prequal_manifest_path), "sha256": sha256(prequal_manifest_path), "bytes": prequal_manifest_path.stat().st_size},
        ],
        "invocations": invocations,
        "totalsByProgram": totals,
        "resetEvidenceLimited": reset_evidence,
        "exit4FlushEvidence": {
            "observedProgramExit4Invocations": [i["invocationIndex"] for i in invocations if i.get("programExit") == 4 and i.get("normalProcessExitObserved")],
            "interpretation": "exit code 4 is preserved as a normal process exit for flush/admissibility evidence; it is not rewritten to zero success.",
        },
        "summary": {
            "plannedInvocations": candidate.get("summary", {}).get("plannedInvocations"),
            "invocationsProcessed": len(invocations),
            "invocationsWithMainGcovUnit": sum(1 for i in invocations if i.get("correctedMainGeneratedCCounts")),
            "normalProcessExit": sum(1 for i in invocations if i.get("normalProcessExitObserved")),
            "exit4FlushObserved": sum(1 for i in invocations if i.get("programExit") == 4 and i.get("normalProcessExitObserved")),
            "gcovPrefixObserved": sum(1 for i in invocations if i.get("gcovPrefixObservedInCommandLog")),
            "programs": sorted({i["businessProgram"] for i in invocations}),
        },
        "limitations": [
            "Reconciliation reads existing .gcov units and existing JSON only; it does not reexecute COBOL, API, server, campaign, gcov, or build commands.",
            "Main generated C, generated headers, and support/other units are separated; headers are not merged into the principal C denominator.",
            "Comparable denominator is the main generated-C denominator from coverage-prequalification-v1, not the gcov aggregate line total that includes headers.",
            "Generated-C branches are mechanical coverage counters and are not interpreted as COBOL business decisions.",
            "Old candidate summaryParsed values are stale for mixed-scope branches/calls and are retained only as discrepancy evidence.",
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "coverage-reconciliation-report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    manifest = write_manifest(out_dir, report, all_sources)
    write_markdown(out_dir, report, manifest)
    write_manifest(out_dir, report, all_sources)
    return report


def write_manifest(out_dir: Path, report: dict[str, Any], gcov_sources: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = {
        "kind": "coverage-report-reconciliation-v1-manifest",
        "createdUtc": datetime.now(timezone.utc).isoformat(),
        "originalInputsPinned": report["sourceArtifacts"],
        "gcovUnitsPinned": gcov_sources,
        "generatedArtifacts": [],
        "manifestSelfHashPolicy": "artifact-manifest.json does not embed its own sha256 to avoid self-referential hash instability",
        "admissibility": "limited reconciliation; not official coverage; no reruns; old mixed parser metrics not promoted",
        "discrepancies": [
            {
                "invocationIndex": i["invocationIndex"],
                "program": i["businessProgram"],
                **i["oldSummaryDiscrepancy"],
            }
            for i in report["invocations"]
        ],
    }
    path = out_dir / "artifact-manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    for rel in ["coverage-reconciliation-report.json", "REPORT.md"]:
        p = out_dir / rel
        if p.exists():
            manifest["generatedArtifacts"].append({"path": rel, "sha256": sha256(p), "bytes": p.stat().st_size})
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest


def write_markdown(out_dir: Path, report: dict[str, Any], manifest: dict[str, Any]) -> None:
    lines = [
        "# Coverage report reconciliation v1",
        "",
        "Status: corrected limited reconciliation from existing gcov artifacts only; not official campaign coverage.",
        "",
        "## Scope and admissibility",
        "",
        "- No COBOL/API/campaign/build/gcov rerun was performed by this reconciliation.",
        "- Principal metric scope is the main generated C unit per business program.",
        "- Generated headers are listed separately and are not merged into the principal C denominator.",
        "- Generated-C branch counters are not COBOL business-decision counts.",
        "- Distinct run directories and GCOV_PREFIX values evidence artifact isolation, but do not alone prove reset semantics beyond the observed files.",
        "",
        "## Corrected totals by program",
        "",
        "| Program | Invocations | Comparable main C denominator (lines/branches/calls) | Matches prequalification |",
        "|---|---:|---:|---|",
    ]
    for row in report["totalsByProgram"]:
        d = row["mainGeneratedCComparableDenominator"]
        lines.append(f"| {row['program']} | {row['invocationCount']} | {d['lines']}/{d['branches']}/{d['calls']} | {row['matchesPrequalificationDenominatorAllInvocations']} |")
    lines += ["", "## Per invocation corrected main generated-C counts", "", "| # | Track | Program | Exit | Lines | Branches executed | Branches taken >=1 | Calls | Old mixed totals (L/B/C) |", "|---:|---|---|---:|---:|---:|---:|---:|---:|"]
    for inv in report["invocations"]:
        c = inv["correctedMainGeneratedCCounts"]
        old = inv["oldSummaryDiscrepancy"]["oldSummaryParsed"]
        lines.append(
            f"| {inv['invocationIndex']} | {inv['track']} | {inv['businessProgram']} | {inv['programExit']} | "
            f"{c['lines']['executed']}/{c['lines']['total']} | {c['branchesExecuted']['executed']}/{c['branchesExecuted']['total']} | "
            f"{c['branchesTakenAtLeastOnce']['executed']}/{c['branchesTakenAtLeastOnce']['total']} | {c['calls']['executed']}/{c['calls']['total']} | "
            f"{old.get('linesTotal')}/{old.get('branchesTotal')}/{old.get('callsTotal')} |"
        )
    lines += ["", "## Artifact manifest", "", f"Manifest: `artifact-manifest.json` ({len(manifest['gcovUnitsPinned'])} gcov unit entries pinned).", ""]
    (out_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    out_dir = Path(__file__).resolve().parent
    base = out_dir.parent
    report = reconcile_report(base, out_dir)
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

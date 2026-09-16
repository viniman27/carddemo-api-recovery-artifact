#!/usr/bin/env python3
"""Assemble source-guided complementary essential cases into a non-executing T1-T4 preparation plan.

This CLI reads existing local evidence only. It does not call models, start campaigns,
replay the official 12k package, or promote complementary cases into T1/T2.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TRACK_TO_OPERATION = {
    "posting": "postDailyTransactions",
    "interest": "generateInterestTransactions",
    "reporting": "generateTransactionReport",
}
OPERATION_TO_TRACK = {v: k for k, v in TRACK_TO_OPERATION.items()}

CONTRACT_ORDER = ["E1-1", "E1-2", "E1-3", "E2-1", "E2-2", "E2-3", "E3-SDD-stage6r3"]
CONDITIONS = ["T1", "T2", "T3", "T4"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def file_pin(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": rel(path, root),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def freeze_summary(p3: Path, cycle_root: Path) -> dict[str, Any]:
    freeze = p3 / "campaign-freeze-package-v3"
    verification = load_json(freeze / "VERIFICATION.json")
    readiness = load_json(freeze / "FINAL-READINESS.json")
    op_cells: list[dict[str, str]] = []
    condition_counts = Counter()
    per_contract: list[dict[str, Any]] = []
    for cid in CONTRACT_ORDER:
        cdir = freeze / cid
        if not cdir.exists():
            raise SystemExit(f"missing contract directory in freeze package: {cid}")
        ops_by_condition: dict[str, list[str]] = {}
        case_counts: dict[str, int] = {}
        for cond in CONDITIONS:
            suite = load_json(cdir / f"{cond}.json")
            cases = suite.get("cases", [])
            case_counts[cond] = len(cases)
            condition_counts[cond] += len(cases)
            ops = sorted({case.get("parameters", {}).get("operationId") for case in cases})
            ops_by_condition[cond] = ops
        union_ops = sorted(set().union(*[set(v) for v in ops_by_condition.values()]))
        for op in union_ops:
            op_cells.append({"contractId": cid, "operationId": op, "track": OPERATION_TO_TRACK.get(op, "unknown")})
        per_contract.append({
            "contractId": cid,
            "caseCounts": case_counts,
            "operations": union_ops,
            "operationsByCondition": ops_by_condition,
        })
    return {
        "package": rel(freeze, cycle_root),
        "contractCount": len(CONTRACT_ORDER),
        "operationCellCount": len(op_cells),
        "operationCells": op_cells,
        "conditionCounts": {k: condition_counts[k] for k in CONDITIONS},
        "perContract": per_contract,
        "t1t2ExactCopies": bool(verification.get("t1t2ExactCopies")),
        "verificationSha256": sha256_file(freeze / "VERIFICATION.json"),
        "finalReadinessSha256": sha256_file(freeze / "FINAL-READINESS.json"),
        "officialReadinessDeclaredInVerification": bool(verification.get("officialReadinessDeclared")),
        "officialExecutionStarted": bool(readiness.get("officialExecutionStarted")),
        "officialExecutionAuthorizedOrClaimed": bool(readiness.get("officialExecutionAuthorizedOrClaimed")),
    }


def posting_cases(p3: Path, cycle_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    report_path = p3 / "complementary-posting-essential-v1/evidence/posting-essential-report.json"
    report = load_json(report_path)
    cases = []
    for r in report.get("caseReceipts", []):
        status = r.get("qualification", {}).get("status")
        cases.append({
            "caseId": r["caseId"],
            "track": "posting",
            "condition": "source-guided-complementary-T3",
            "role": "source_guided_complementary_T3_checker_candidate",
            "operationId": TRACK_TO_OPERATION["posting"],
            "officialCampaignStatus": "candidate_not_official_campaign",
            "sourceEvidence": [rel(report_path, cycle_root), rel(Path(r.get("runDir", "")), cycle_root) if r.get("runDir") else "runDir:not-recorded"],
            "sourceMapping": {
                "authority": "COBOL/P2b local runtime evidence and source-computed expected status before run",
                "guard": r.get("guard"),
                "reachedCobol": bool(r.get("reachedCobol")),
                "httpStatus": r.get("httpStatus"),
                "programExit": r.get("programExit"),
            },
            "modelMapping": {
                "transitionBinding": "none_verified_for_this_case",
                "classificationLimit": "source-guided checker battery; not model-generated MBT stimulus and not T1 manual scenario",
            },
            "checkerScope": {
                "qualificationStatus": status,
                "effectTraceQualification": r.get("effectTraceQualification", {}).get("status", "not-recorded"),
                "acceptedCount": r.get("acceptedCount"),
                "rejectCount": len(r.get("rejects", [])),
            },
        })
    obligations = []
    for m in report.get("obligationMatrix", []):
        obligations.append({
            "track": "posting",
            "obligationId": m.get("obligationId") or m.get("obligation"),
            "description": m.get("description"),
            "cases": m.get("cases") or m.get("relatedCases") or [],
            "aggregateClassification": m.get("status", "source-guided-local"),
            "evidenceMeaning": m.get("evidence"),
            "limits": "Posting file/order effects are source-guided local checker evidence; effect trace is inconclusive where internal order is not observed.",
        })
    pins = [file_pin(report_path, cycle_root)]
    return cases, obligations, pins


def interest_cases(p3: Path, cycle_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    matrix_path = p3 / "complementary-interest-essential-v1/RESULTS-MATRIX.json"
    report_path = p3 / "complementary-interest-essential-v1/REPORT.md"
    matrix = load_json(matrix_path)
    case_ids = sorted({cid for row in matrix.get("matrix", []) for cid in row.get("cases", [])})
    cases = []
    for cid in case_ids:
        result_path = p3 / f"complementary-interest-essential-v1/evidence/{cid}/result.json"
        input_freeze = p3 / f"complementary-interest-essential-v1/evidence/{cid}/input-freeze.json"
        result = load_json(result_path) if result_path.exists() else {}
        cases.append({
            "caseId": cid,
            "track": "interest",
            "condition": "source-guided-complementary-T3",
            "role": "source_guided_complementary_T3_checker_candidate",
            "operationId": TRACK_TO_OPERATION["interest"],
            "officialCampaignStatus": "candidate_not_official_campaign",
            "sourceEvidence": [rel(matrix_path, cycle_root), rel(result_path, cycle_root), rel(input_freeze, cycle_root)],
            "sourceMapping": {
                "authority": "COBOL/P2b local runtime evidence plus source monthly-interest formula in essential_interest.py",
                "checkerResult": result.get("checks", {}).get("failures", []),
                "observedTransactionCount": len(result.get("observedTransactions", [])),
            },
            "modelMapping": {
                "transitionBinding": "source_partition_obligations_only; no official MBT transition promotion",
                "classificationLimit": "candidate checker evidence; not model-call generation, not T1, not T2 fuzz",
            },
            "checkerScope": {
                "accountDeltas": result.get("accountDeltas", {}),
                "fileEffects": result.get("fileEffects", {}),
            },
        })
    obligations = []
    for row in matrix.get("matrix", []):
        oid = row.get("obligationId")
        if oid == "INTCALC-OBL-007":
            aggregate = "covered_partition_only"
            meaning = "zero-rate DISCGRP partition generated no matching output transaction while other partitions in the same case generated transactions."
            limits = "This is a zero-rate partition checker, not a count label for all interest behavior and not proof of every no-transaction cause."
        elif oid == "INTCALC-OBL-008":
            aggregate = "source-supported-limitation"
            meaning = "EOF final-account behavior observed: transaction can be written while the final account rewrite delta remains zero."
            limits = "Records legacy limitation; not desired finance behavior and not a business pass for account update completeness."
        else:
            aggregate = "covered_local_source_guided" if row.get("status") == "covered" else row.get("status", "unknown")
            meaning = "; ".join(row.get("evidence", []))
            limits = "Local P3 technical cases only; not official campaign fixtures and not all checker obligations."
        obligations.append({
            "track": "interest",
            "obligationId": oid,
            "description": row.get("description"),
            "cases": row.get("cases", []),
            "aggregateClassification": aggregate,
            "evidenceMeaning": meaning,
            "limits": limits,
        })
    pins = [file_pin(matrix_path, cycle_root), file_pin(report_path, cycle_root)]
    for cid in case_ids:
        for path in [p3 / f"complementary-interest-essential-v1/evidence/{cid}/result.json", p3 / f"complementary-interest-essential-v1/evidence/{cid}/input-freeze.json"]:
            if path.exists():
                pins.append(file_pin(path, cycle_root))
    return cases, obligations, pins


def reporting_cases(p3: Path, cycle_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    results_path = p3 / "complementary-reporting-essential-v1/evidence/reporting-essential-results.json"
    data = load_json(results_path)
    cases = []
    for r in data.get("results", []):
        cases.append({
            "caseId": r["caseId"],
            "track": "reporting",
            "condition": "source-guided-complementary-T3",
            "role": "source_guided_complementary_T3_checker_candidate",
            "operationId": TRACK_TO_OPERATION["reporting"],
            "officialCampaignStatus": "candidate_not_official_campaign",
            "sourceEvidence": [rel(results_path, cycle_root), rel(Path(r.get("rawReportPath", "")), cycle_root), rel(Path(r.get("parsedReportPath", "")), cycle_root)],
            "sourceMapping": {
                "authority": "COBOL/P2b local runtime report output and source-guided parsed record partitions",
                "rawRecordCount": r.get("rawRecordCount"),
                "runtimeStatus": r.get("runtimeStatus"),
                "totalQualification": r.get("totalQualification"),
            },
            "modelMapping": {
                "transitionBinding": "none_verified_for_this_case",
                "classificationLimit": "report partition checker; not retrospective business oracle for totals",
            },
            "checkerScope": {
                "expectedDetailIds": r.get("expectedDetailIds", []),
                "observedDetailIds": r.get("observedDetailIds", []),
                "observedTotalsCount": len(r.get("observedTotals", [])),
                "failures": r.get("failures", []),
            },
        })
    obligations = []
    for row in data.get("obligationPartitionMatrix", []):
        oid = row.get("obligation")
        if oid == "R-TOTALS-EOF-GUARD":
            aggregate = "inconclusive-by-source"
            limits = "EOF totals branch is guarded because the source may add stale TRAN-AMT on EOF path; not a business pass for totals arithmetic."
        else:
            aggregate = row.get("qualification", "runtime-observed")
            limits = "Observed detail/order/framing partition only; prospective official campaign evidence still requires runner-bound checker."
        obligations.append({
            "track": "reporting",
            "obligationId": oid,
            "description": row.get("partition"),
            "cases": row.get("relatedCases", []),
            "aggregateClassification": aggregate,
            "evidenceMeaning": row.get("evidence"),
            "limits": limits,
        })
    pins = [file_pin(results_path, cycle_root)]
    for manifest in data.get("freezeManifests", []):
        path = Path(manifest)
        if path.exists():
            pins.append(file_pin(path, cycle_root))
    return cases, obligations, pins


def assemble(cycle_root: Path, output: Path) -> None:
    cycle_root = cycle_root.resolve()
    p3 = cycle_root / "P3"
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)

    source_freeze = freeze_summary(p3, cycle_root)
    all_cases: list[dict[str, Any]] = []
    obligations: list[dict[str, Any]] = []
    pins: list[dict[str, Any]] = []
    for loader in [posting_cases, interest_cases, reporting_cases]:
        cases, obs, fpins = loader(p3, cycle_root)
        all_cases.extend(cases)
        obligations.extend(obs)
        pins.extend(fpins)

    by_track = Counter(c["track"] for c in all_cases)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    plan = {
        "kind": "complementary-suite-integration-v1",
        "createdUtc": now,
        "cycleRoot": str(cycle_root),
        "officialExecutionStarted": False,
        "nonExecuting": True,
        "roleSeparation": {
            "T1": "existing real LLM scenario stimuli imported from campaign-freeze-package-v3; exact copy only, no new/manual T1 classification",
            "T2": "existing OpenAPI-guided fuzz stimuli imported from campaign-freeze-package-v3; exact copy only, no regeneration in this package",
            "T3": "existing/reference-mapped model-based suite remains campaign-freeze-package-v3 T3; guardResult policy preserved",
            "T4": "existing union remains campaign-freeze-package-v3 T4; no duplicate 12k official run or repeatcampaign",
            "complementaryEssentialCases": "source_guided_complementary_T3_checker_candidate",
            "complementaryLimit": "local essential batteries are checker/coverage-gap evidence; they are not reclassified as T1, T2 fuzz, official MBT generation, or official execution results",
        },
        "sourceFreeze": source_freeze,
        "candidateCountsByTrack": dict(by_track),
        "candidateComplementCases": all_cases,
        "sourceAndModelMapping": {
            "sourceAuthority": "COBOL source/P2b local runtime artifacts and byte-pinned fixtures/checkers listed in artifactPins",
            "modelAuthority": "campaign-freeze-package-v3 T3/reference-executable-v4 remains separate; complementary cases do not invent aliases or promote unbound manual checks to official T3 stimuli",
            "allOfInputSemantics": "This package does not deserialize/rewrite official frozen request bytes; T1/T2 exact-copy status is read from VERIFICATION.json.",
            "emptyObjectSddSemantics": "Existing {} SDD cases remain in freeze package; complementary cases do not reinterpret {} as business diversity.",
        },
        "artifactPins": sorted(pins, key=lambda x: x["path"]),
    }
    ledger = {
        "kind": "complementary-suite-integration-v1-coverage-gap-ledger",
        "createdUtc": now,
        "scope": "candidate preparation ledger only; no official campaign execution and no external/model calls",
        "operationCells": source_freeze["operationCells"],
        "candidateCountsByTrack": dict(by_track),
        "obligations": obligations,
        "materialBlockedCells": [
            {
                "condition": "T1",
                "status": "not materialized by this package",
                "reason": "T1 stimuli are already frozen in campaign-freeze-package-v3; this package does not send providers or create manual T1.",
            },
            {
                "condition": "T2",
                "status": "not regenerated by this package",
                "reason": "T2 stimuli are already frozen in campaign-freeze-package-v3; this package does not synthesize schemas or regenerate fuzz cases.",
            },
            {
                "condition": "T3-complementary-essential",
                "status": "candidate checker binding only",
                "reason": "Complementary essential cases are source-guided local checkers; official MBT transition promotion requires explicit reviewed model binding per case.",
            },
            {
                "condition": "T4",
                "status": "not rebuilt by this package",
                "reason": "T4 official union remains campaign-freeze-package-v3; no duplicate original official 12k run/replay.",
            },
        ],
        "nextGate": "Bind selected complementary checker obligations to the parent runner/checker configuration as source-guided T3 adjuncts, or leave them as shared qualification batteries where no explicit model transition exists.",
    }

    dump_json(output / "candidate-suite-plan.json", plan)
    dump_json(output / "coverage-gap-ledger.json", ledger)
    status = f"""# Complementary suite integration v1 status

Status: candidate preparation complete; non-executing. No official AWS campaign execution is started here.

## Qualified locally
- Read `campaign-freeze-package-v3` as the source of T1/T2/T3/T4, 7 contracts, 21 operation cells, counts T1=88, T2=5868, T3=394, T4=6350.
- Integrated real complementary essential evidence as source-guided checker candidates only: posting=6, interest=2, reporting=4.
- Preserved role separation: no manualT1, no T2 regeneration, no fake model classification, no repeatcampaign.
- Corrected interpretation boundaries: INTCALC-OBL-007 is zero-rate partition coverage only; reporting totals remain EOF-guarded/inconclusive, not a business pass.

## Files
- `candidate-suite-plan.json`: exact source/model/role mapping and candidate case descriptors.
- `coverage-gap-ledger.json`: consolidated obligations, limits, material blockers and next gate.
- `MANIFEST.json`: hashes for this package output.

## Next gate
{ledger['nextGate']}
"""
    (output / "STATUS.md").write_text(status, encoding="utf-8")
    role_mapping = """# Role and source/model mapping

- T1: existing `campaign-freeze-package-v3` LLM-scenario stimuli only; this package creates no manual T1 cases.
- T2: existing `campaign-freeze-package-v3` OpenAPI-guided fuzz stimuli only; this package regenerates no fuzz requests and rewrites no request bytes.
- T3: existing campaign freeze T3 remains the model/reference-mapped suite. Complementary essentials are source-guided checker candidates and stay separate unless a later gate binds them explicitly.
- T4: existing campaign freeze union only; this package does not rebuild or rerun the original official campaign package.
- Complementary evidence: posting, interest, and reporting local P3 essential packages, with byte-pinned evidence and checker limits recorded in `coverage-gap-ledger.json`.
"""
    (output / "ROLE-MAPPING.md").write_text(role_mapping, encoding="utf-8")

    files = []
    for path in sorted(output.iterdir()):
        if path.name == "MANIFEST.json" or not path.is_file():
            continue
        files.append(file_pin(path, output))
    manifest = {
        "kind": "complementary-suite-integration-v1-manifest",
        "createdUtc": now,
        "files": files,
    }
    dump_json(output / "MANIFEST.json", manifest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    assemble_p = sub.add_parser("assemble")
    assemble_p.add_argument("--cycle-root", type=Path, required=True)
    assemble_p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.cmd == "assemble":
        assemble(args.cycle_root, args.output)
        return 0
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    sys.exit(main())

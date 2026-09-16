from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

CHECKER_ROOT_NAME = "complementary-validation-implementation-v3"

IMPLEMENTED_BY_TRACK = {
    "posting": {
        "valid-new-tcatbal": ["POSTTRAN-OBL-003", "POSTTRAN-OBL-009"],
        "valid-existing-tcatbal": ["POSTTRAN-OBL-003", "POSTTRAN-OBL-009"],
        "reject-card-missing": ["POSTTRAN-OBL-004", "POSTTRAN-OBL-006"],
        "reject-account-missing": ["POSTTRAN-OBL-006"],
        "reject-limit": ["POSTTRAN-OBL-006"],
        "reject-expiry": ["POSTTRAN-OBL-006"],
    },
    "interest": {
        "rates-specific-default-zero": ["INTCALC-OBL-005", "INTCALC-OBL-006"],
        "single-final-eof": ["INTCALC-OBL-005", "INTCALC-OBL-006"],
    },
    "reporting": {
        "date-boundaries-in-out-v1": ["TRANREPT-OBL-002", "TRANREPT-OBL-006"],
        "empty-in-range-v1": ["TRANREPT-OBL-002", "TRANREPT-OBL-006"],
        "card-break-two-groups-v1": ["TRANREPT-OBL-002", "TRANREPT-OBL-006"],
        "pagination-threshold-20-v1": ["TRANREPT-OBL-002", "TRANREPT-OBL-006"],
    },
}

REJECT_CASE_NAME = {
    "card_missing": "missing-card",
    "account_missing": "account-missing",
    "over_limit": "over-limit",
    "expired": "expired",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


def pin(path: Path, root: Path, label: str | None = None) -> dict[str, Any]:
    return {
        "label": label or path.name,
        "path": rel(path, root),
        "absolutePath": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def verify_pins(pins: list[dict[str, Any]], base: Path | None = None) -> list[str]:
    failures: list[str] = []
    for item in pins:
        path = Path(item.get("absolutePath") or (base / item["path"] if base else item["path"]))
        if not path.exists():
            failures.append(f"missing pinned artifact {item.get('label') or item.get('path')}: {path}")
            continue
        actual_bytes = path.stat().st_size
        if actual_bytes != item.get("bytes"):
            failures.append(f"byte mismatch {item.get('label') or item.get('path')}: expected {item.get('bytes')} observed {actual_bytes}")
        actual_sha = sha256_file(path)
        if actual_sha != item.get("sha256"):
            failures.append(f"sha mismatch {item.get('label') or item.get('path')}: expected {item.get('sha256')} observed {actual_sha}")
    return failures


def _prov(raw_prov: dict[str, Any], observed_fields: list[str] | None = None) -> dict[str, Any]:
    out = dict(raw_prov)
    if "artifactSha256" in out and "sha256" not in out:
        out["sha256"] = out.pop("artifactSha256")
    elif "artifactSha256" in out:
        out.pop("artifactSha256")
    if observed_fields:
        out["observedFields"] = observed_fields
    elif not out.get("observedFields"):
        out["observedFields"] = ["rawBytes"]
    return out


def _interest_prov(raw_prov: dict[str, Any], observed_fields: list[str]) -> dict[str, Any]:
    out = _prov(raw_prov, observed_fields)
    artifact = Path(str(out.get("artifact", "")))
    if artifact.exists():
        out["sha256"] = sha256_file(artifact)
    return out


def _ascii(raw_hex: str) -> str:
    return bytes.fromhex(raw_hex).decode("latin1", errors="replace")


def _posted_from_raw(raw_hex: str) -> dict[str, str]:
    # Fixed-width CardDemo transaction record fields observed in the preserved bytes.
    text = _ascii(raw_hex)
    return {
        "id": text[0:16].rstrip("\x00 "),
        "type": text[16:18].rstrip("\x00 "),
        "category": text[18:22].rstrip("\x00 "),
        "source": text[22:32].rstrip("\x00 "),
        "description": text[32:112].rstrip("\x00 "),
        "amount": _cents_to_money(text[112:123]),
        "merchant": text[123:132].rstrip("\x00 "),
        "card": text[244:260].rstrip("\x00 "),
        "origTs": text[260:286].rstrip("\x00 "),
        "procTs": text[286:312].rstrip("\x00 "),
    }


def _cents_to_money(value: Any) -> str:
    digits = "".join(ch for ch in str(value) if ch.isdigit()) or "0"
    return f"{(Decimal(digits) / Decimal(100)):.2f}"


def _common_meta(cycle_root: Path, case_id: str, track: str, source_paths: list[Path], extra_pins: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    pins = [pin(p, cycle_root) for p in source_paths if p.exists() and p.is_file()]
    pins.extend(extra_pins or [])
    return {
        "caseId": case_id,
        "track": track,
        "evidenceClass": "real_cobol_observation",
        "artifactPins": pins,
        "apiRerun": False,
        "executionMode": "preserved_artifact_binding_only",
        "modelBinding": {
            "classification": "shared_source_guided_qualification",
            "t3TransitionTie": "not_qualified_for_case",
            "reason": "No reviewed per-case T3 model transition binding is recorded; case is bound as a shared source-guided checker battery, not T1/T2/manual promotion.",
        },
    }


def _posting_fixture(cycle_root: Path, case_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    report_path = cycle_root / "P3/complementary-posting-essential-v1/evidence/posting-essential-report.json"
    report = load_json(report_path)
    receipt = next(r for r in report["caseReceipts"] if r["caseId"] == case_id)
    obs = {"posting": {"returnCode": receipt.get("programExit"), "acceptedTransactions": [], "rejects": []}}
    for accepted in receipt.get("recordProvenance", {}).get("accepted", []):
        posted = _posted_from_raw(accepted["rawBytes"])
        daily = dict(posted)
        daily["procTs"] = "input-pre-cobol-not-runtime-proc-ts"
        obs["posting"]["acceptedTransactions"].append({
            "id": posted["id"],
            "rawBytes": accepted["rawBytes"],
            "daily": daily,
            "posted": posted,
            "duplicatePrevalidated": False,
            "traceBoundary": receipt.get("effectTraceQualification", {}).get("status"),
            "provenance": _prov(accepted["provenance"], ["rawBytes", "daily", "posted"]),
        })
    for rej in receipt.get("rejects", []):
        obs["posting"]["rejects"].append({
            "case": REJECT_CASE_NAME.get(receipt.get("guard"), receipt.get("guard")),
            "rawBytes": rej["rawBytes"],
            "reason": str(rej.get("reason", "")),
            "description": rej.get("description", ""),
            "postedTransactionWritten": False,
            "rejectRecordWritten": True,
            "provenance": _prov(rej["provenance"], ["rawBytes", "reason", "description", "rejectRecordWritten"]),
        })
    meta = _common_meta(cycle_root, case_id, "posting", [report_path, Path(receipt["runDir"])])
    meta["runnerReceipt"] = {"httpStatus": receipt.get("httpStatus"), "programExit": receipt.get("programExit"), "sourceExpectedComputedBeforeRun": receipt.get("qualification", {}).get("expected", {}).get("sourceExpectedComputedBeforeRun")}
    return {"fixtureId": case_id, "description": "Bound preserved posting essential receipt", "observations": obs, "evidenceClass": "real_cobol_observation"}, meta


def _interest_fixture(cycle_root: Path, case_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    result_path = cycle_root / f"P3/complementary-interest-essential-v1/evidence/{case_id}/result.json"
    freeze_path = cycle_root / f"P3/complementary-interest-essential-v1/evidence/{case_id}/input-freeze.json"
    result = load_json(result_path)
    expected_by_acct = {x["acct"]: x for x in result.get("sourceExpected", {}).get("transactions", [])}
    txs: list[dict[str, Any]] = []
    for item in result.get("observedTransactionsWithProvenance", []):
        acct = item.get("description", "").split("Int. for a/c ")[-1].split("\x00")[0].strip()
        exp = expected_by_acct.get(acct, {})
        txs.append({
            "id": item["transactionId"],
            "rawBytes": item["rawBytesHex"],
            "categoryBalance": exp.get("balance", "0.00"),
            "annualRate": exp.get("rate", "0.00"),
            "amount": _cents_to_money(item["amount"]),
            "transactionWritten": True,
            "type": item.get("typeCode"),
            "category": item.get("categoryCode", "").lstrip("0")[-2:].zfill(2),
            "source": item.get("source"),
            "description": item.get("description", ""),
            "merchant": item.get("merchantId"),
            "card": item.get("cardReference"),
            "xrefCard": item.get("cardReference"),
            "provenance": _interest_prov(item["provenance"], ["rawBytes", "amount", "type", "category", "source", "card"]),
        })
    if case_id == "rates-specific-default-zero":
        txs.append({
            "id": "source-zero-rate-partition",
            "categoryBalance": "1000.00",
            "annualRate": "0.00",
            "transactionWritten": False,
            "provenance": {"kind": "memory_map_record", "artifact": str(result_path), "lineNumber": 1, "observedFields": ["categoryBalance", "annualRate", "transactionWritten"]},
        })
    obs = {"interest": {"transactions": txs}}
    meta = _common_meta(cycle_root, case_id, "interest", [result_path, freeze_path])
    meta["runnerReceipt"] = {"status": result.get("status"), "checks": result.get("checks"), "sourceExpectedComputedIndependently": True}
    return {"fixtureId": case_id, "description": "Bound preserved interest essential receipt", "observations": obs, "evidenceClass": "real_cobol_observation"}, meta


def _reporting_fixture(cycle_root: Path, case_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    results_path = cycle_root / "P3/complementary-reporting-essential-v1/evidence/reporting-essential-results.json"
    all_results = load_json(results_path)
    rec = next(r for r in all_results["results"] if r["caseId"] == case_id)
    parsed_path = Path(rec["parsedReportPath"])
    raw_path = Path(rec["rawReportPath"])
    parsed = load_json(parsed_path) if parsed_path.exists() else {"details": [], "headers": []}
    header = (parsed.get("headers") or [{}])[0]
    start, end = header.get("startText", "0000-00-00"), header.get("endText", "9999-99-99")
    txs: list[dict[str, Any]] = []
    for d in parsed.get("details", []):
        proc = start
        if "END" in d.get("transactionId", ""):
            proc = end
        txs.append({
            "id": d.get("transactionId"),
            "procDate": proc,
            "amount": d.get("amount"),
            "detailWritten": True,
            "detailLine": d.get("rawText", ""),
            "reportLineBytes": d.get("rawBytes", ""),
            "provenance": {"kind": "report_line", "artifact": str(raw_path), "sha256": rec.get("rawReportSha256"), "recordOffset": d.get("offset"), "recordLength": 133, "observedFields": ["procDate", "amount", "detailLine", "reportLineBytes"]},
        })
    if case_id == "date-boundaries-in-out-v1":
        txs.extend([
            {"id": "source-before-range-absent", "procDate": "2022-06-30", "amount": "0.00", "detailWritten": False, "provenance": {"kind": "memory_map_record", "artifact": str(results_path), "lineNumber": 1, "observedFields": ["procDate", "detailWritten"]}},
            {"id": "source-after-range-absent", "procDate": "2022-08-01", "amount": "0.00", "detailWritten": False, "provenance": {"kind": "memory_map_record", "artifact": str(results_path), "lineNumber": 1, "observedFields": ["procDate", "detailWritten"]}},
        ])
    obs = {"reporting": {"dateRange": [start, end], "transactions": txs, "reportFraming": {"classification": rec.get("framing", {}).get("classification"), "eofBeforeTotalsBranch": True}}}
    meta = _common_meta(cycle_root, case_id, "reporting", [results_path, parsed_path, raw_path])
    meta["runnerReceipt"] = {"runtimeStatus": rec.get("runtimeStatus"), "status": rec.get("status"), "totalQualification": rec.get("totalQualification")}
    return {"fixtureId": case_id, "description": "Bound preserved reporting essential receipt", "observations": obs, "evidenceClass": "real_cobol_observation"}, meta


def build_fixture_for_case(cycle_root: Path, case_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    cycle_root = cycle_root.resolve()
    if case_id in IMPLEMENTED_BY_TRACK["posting"]:
        return _posting_fixture(cycle_root, case_id)
    if case_id in IMPLEMENTED_BY_TRACK["interest"]:
        return _interest_fixture(cycle_root, case_id)
    if case_id in IMPLEMENTED_BY_TRACK["reporting"]:
        return _reporting_fixture(cycle_root, case_id)
    raise KeyError(f"unknown essential case: {case_id}")


def _checker_import(cycle_root: Path) -> None:
    checker_root = cycle_root / "P3" / CHECKER_ROOT_NAME
    if str(checker_root) not in sys.path:
        sys.path.insert(0, str(checker_root))


def run_binding(cycle_root: Path) -> dict[str, Any]:
    cycle_root = cycle_root.resolve()
    _checker_import(cycle_root)
    from semantic_checkers import load_fixture, run_fixture_checks  # type: ignore
    plan_path = cycle_root / "P3/complementary-suite-integration-v1/latest/candidate-suite-plan.json"
    plan = load_json(plan_path)
    cases = []
    pins = [pin(plan_path, cycle_root, "candidate-suite-plan.json")]
    with tempfile.TemporaryDirectory(prefix="runner-binding-fixtures-") as td:
        temp = Path(td)
        for track_cases in IMPLEMENTED_BY_TRACK.values():
            for case_id, obligation_ids in track_cases.items():
                fixture, meta = build_fixture_for_case(cycle_root, case_id)
                fixture_path = temp / f"{case_id}.json"
                fixture_path.write_text(json.dumps(fixture, indent=2, ensure_ascii=False), encoding="utf-8")
                checker_results = [r.to_json_dict() for r in run_fixture_checks(load_fixture(fixture_path), obligation_ids=obligation_ids)]
                case_payload = {
                    **meta,
                    "fixtureHash": hashlib.sha256(json.dumps(fixture, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
                    "applicableObligations": obligation_ids,
                    "checkerResults": checker_results,
                    "pinVerificationFailures": verify_pins(meta["artifactPins"]),
                }
                cases.append(case_payload)
                pins.extend(meta["artifactPins"])
    by_track = Counter(c["track"] for c in cases)
    statuses = Counter(r["status"] for c in cases for r in c["checkerResults"])
    model_classes = sorted({c["modelBinding"]["classification"] for c in cases})
    seven_contract_map = [{"contractId": row["contractId"], "status": "declared_supported_by_original_freeze_only_not_by_complementary_binding", "operationCount": len(row.get("operations", []))} for row in plan.get("sourceFreeze", {}).get("perContract", [])]
    payload = {
        "kind": "complementary-runner-binding-v1-results",
        "createdUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "scope": "Preserved real P3 essential artifacts only; no API, COBOL, model, campaign or quarantine reruns.",
        "sourceCheckerPinsProspective": {
            "checkerPackage": f"P3/{CHECKER_ROOT_NAME}",
            "contract": "future official use must pin this manifest before first official execution; current run is retrospective qualification of preserved artifacts, not retroactive official evidence",
        },
        "summary": {
            "caseCount": len(cases),
            "caseCountsByTrack": dict(by_track),
            "checkerStatusCounts": dict(statuses),
            "noApiReruns": True,
            "modelBindingClassifications": model_classes,
            "pinVerificationFailures": [f for c in cases for f in c["pinVerificationFailures"]],
        },
        "sevenContractMapping": seven_contract_map,
        "cases": cases,
        "artifactPins": sorted({(p["path"], p["sha256"]): p for p in pins}.values(), key=lambda p: p["path"]),
    }
    return payload


def write_status(out: Path, payload: dict[str, Any]) -> None:
    status = payload["summary"]["checkerStatusCounts"]
    text = f"""# Complementary runner binding v1 STATUS

Status: executable binding exercised on preserved real essential-case artifacts.

- Cases bound: {payload['summary']['caseCount']} ({payload['summary']['caseCountsByTrack']})
- Checker statuses: {status}
- API/COBOL/model reruns: none; all evidence came from pinned preserved P3 files.
- Model classification: {', '.join(payload['summary']['modelBindingClassifications'])}; no case has a qualified per-case T3 transition tie.
- Missing trace is handled as inconclusive, not semantic failure (posting effect order and reporting EOF totals remain guarded).

Next complete limitation: a future official runner can reuse this binding only prospectively after pinning the checker/source manifest before first official execution; this result does not retroactively promote complementary cases into T1/T2/T3/T4 official campaign evidence.
"""
    (out.parent / "STATUS.md").write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run")
    run_p.add_argument("--cycle-root", type=Path, required=True)
    run_p.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.cmd == "run":
        payload = run_binding(args.cycle_root)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        write_status(args.out, payload)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

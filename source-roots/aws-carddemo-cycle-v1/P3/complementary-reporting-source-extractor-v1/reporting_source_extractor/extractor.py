from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

TRANFILE_SPANS = [
    ("id", 0, 16), ("type", 16, 18), ("category", 18, 22), ("source", 22, 32),
    ("description", 32, 132), ("amountRaw", 132, 143), ("merchant", 143, 152),
    ("merchantName", 152, 202), ("merchantCity", 202, 252), ("merchantPostalText", 252, 262),
    ("card", 262, 278), ("origTs", 278, 304), ("procTs", 304, 330),
]

DETAIL_SPANS = [
    ("id", 0, 16), ("account", 17, 28), ("type", 29, 31), ("typeDescription", 32, 47),
    ("category", 48, 52), ("categoryDescription", 53, 82), ("source", 83, 93),
    ("amountText", 97, 113),
]

SOURCE_ANCHORS = {
    "CBTRN03C": {"path": "app/cbl/CBTRN03C.cbl", "sha256": "8691e625502b7efcfd7ba4ae61797132e7b68f3fd5fedcdcc7dd6488f6871eef", "lines": [[170, 204], [274, 289], [293, 322], [361, 372]]},
    "CVTRA07Y": {"path": "app/cpy/CVTRA07Y.cpy", "sha256": "72ba597b1a40e1e6cf908e15da9e6a818a0ab899ef1d27d15edeb074963102fa", "lines": [[15, 31], [50, 66]]},
    "TRANREPT.jcl": {"path": "app/jcl/TRANREPT.jcl", "sha256": "7d8fc0777e6b9fb1c62aee6b4b10a67d127057c84b92203c7152f230b3db9571", "lines": [[35, 48], [65, 79]]},
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pin(path: Path, label: str) -> dict[str, Any]:
    return {"label": label, "path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def verify_pin(p: dict[str, Any]) -> list[str]:
    path = Path(p["path"])
    if not path.exists():
        return [f"missing:{path}"]
    failures = []
    if path.stat().st_size != p.get("bytes"):
        failures.append(f"bytes_mismatch:{path}")
    actual = sha256_file(path)
    if p.get("sha256") and actual != p.get("sha256"):
        failures.append(f"sha256_mismatch:{path}")
    return failures


def _money_from_digits(raw: Any) -> str:
    text = str(raw).strip()
    neg = text.startswith("-")
    digits = "".join(ch for ch in text if ch.isdigit()) or "0"
    value = (Decimal(digits) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if neg and value:
        value = -value
    return f"{value:.2f}"


def _money_from_report(raw: str) -> str:
    text = raw.strip().replace(",", "")
    if not text:
        return "0.00"
    return f"{Decimal(text).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


def selected_by_date_range(proc_date: str, start: str, end: str) -> bool:
    """COBOL uses X(10) comparisons; keep lexical comparison, no calendar validation."""
    return start <= proc_date <= end


def fixed_records(path: Path, size: int) -> list[tuple[int, bytes]]:
    data = path.read_bytes()
    return [(off, data[off:off + size]) for off in range(0, len(data), size) if len(data[off:off + size]) == size]


def parse_dateparm(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    return data[0:10].decode("latin1"), data[11:21].decode("latin1")


def parse_tranfile_record(raw: bytes) -> dict[str, Any]:
    d: dict[str, Any] = {}
    for name, a, b in TRANFILE_SPANS:
        d[name] = raw[a:b].decode("latin1", errors="replace").rstrip("\x00 ")
    d["amount"] = _money_from_digits(d.pop("amountRaw"))
    d["procDate"] = d.get("procTs", "")[:10]
    return d


def _strings(data: bytes, min_len: int = 4) -> list[tuple[int, str]]:
    out = []
    start = None
    buf = bytearray()
    for i, b in enumerate(data):
        if 32 <= b <= 126:
            if start is None:
                start = i
            buf.append(b)
        else:
            if start is not None and len(buf) >= min_len:
                out.append((start, buf.decode("latin1")))
            start = None
            buf = bytearray()
    if start is not None and len(buf) >= min_len:
        out.append((start, buf.decode("latin1")))
    return out


def lookup_account(cardxref: Path, card: str) -> dict[str, Any] | None:
    data = cardxref.read_bytes()
    card_bytes = card.encode("latin1")
    candidates: list[tuple[int, str]] = []
    start = 0
    while True:
        idx = data.find(card_bytes, start)
        if idx < 0:
            break
        if idx + 36 <= len(data):
            rec = data[idx:idx + 36].decode("latin1", errors="replace")
            if rec[16:36].isdigit():
                candidates.append((idx, rec))
        start = idx + 1
    if not candidates:
        return None
    idx, rec = candidates[-1]
    return {"card": rec[0:16], "customerId": rec[16:25], "account": rec[25:36], "sourceOffset": idx}


def lookup_type(trantype: Path, type_code: str) -> dict[str, Any] | None:
    for off, s in _strings(trantype.read_bytes()):
        if s.startswith(type_code) and len(s) >= 3:
            return {"type": s[:2], "description": s[2:17].strip(), "sourceOffset": off}
    return None


def lookup_category(trancatg: Path, type_code: str, category: str) -> dict[str, Any] | None:
    key = f"{type_code}{category}"
    for off, s in _strings(trancatg.read_bytes()):
        if s.startswith(key) and len(s) >= 7:
            return {"type": s[:2], "category": s[2:6], "description": s[6:35].strip(), "sourceOffset": off}
    return None


def expected_detail_from_source(tx: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    acct = lookup_account(run_dir / "CARDXREF", tx["card"])
    typ = lookup_type(run_dir / "TRANTYPE", tx["type"])
    cat = lookup_category(run_dir / "TRANCATG", tx["type"], tx["category"])
    return {
        "id": tx["id"],
        "account": (acct or {}).get("account"),
        "type": tx["type"],
        "typeDescription": (typ or {}).get("description"),
        "category": tx["category"],
        "categoryDescription": (cat or {}).get("description"),
        "source": tx["source"],
        "amount": tx["amount"],
        "lookupEvidence": {"account": acct, "type": typ, "category": cat},
    }


def parse_detail_line(raw: bytes) -> dict[str, Any]:
    txt = raw.decode("latin1", errors="replace")
    d: dict[str, Any] = {"lineText": txt, "reportLineBytes": raw.hex()}
    for name, a, b in DETAIL_SPANS:
        d[name] = txt[a:b].rstrip()
    d["amount"] = _money_from_report(d.pop("amountText"))
    return d


def classify_report_records(report: Path) -> dict[str, Any]:
    if not report.exists():
        return {"recordCoverage": "missing_report", "failures": ["missing_report"], "records": []}
    data = report.read_bytes()
    failures = []
    if len(data) == 0:
        failures.append("report_empty")
    if len(data) % 133 != 0:
        failures.append(f"report_size_not_multiple_of_133:{len(data)}")
    classes = []
    unknown = []
    for index, raw in enumerate([data[i:i + 133] for i in range(0, len(data), 133)]):
        text = raw.decode("latin1", errors="replace")
        kind = None
        if text.startswith("DALYREPT") and "Date Range:" in text:
            kind = "name_date_header"
        elif not text.strip():
            kind = "blank"
        elif text.startswith("Transaction ID"):
            kind = "column_header"
        elif set(text.strip()) == {"-"}:
            kind = "separator"
        elif text.startswith("Page Total"):
            kind = "page_total"
        elif text.startswith("Account Total"):
            kind = "account_total"
        elif text.startswith("Grand Total"):
            kind = "grand_total"
        elif text[:16].strip():
            kind = "detail"
        if kind is None:
            kind = "unknown_meaningful" if text.strip() else "blank"
            unknown.append(index)
        classes.append({"index": index, "offset": index * 133, "kind": kind, "text": text})
    if unknown:
        failures.append(f"unknown_meaningful_records:{unknown}")
    coverage = "all_records_classified" if not failures else "classification_failed"
    return {"recordCoverage": coverage, "failures": failures, "records": classes}


def _record_provenance(path: Path, offset: int, length: int, observed_fields: list[str]) -> dict[str, Any]:
    return {"kind": "raw_file_record", "artifact": str(path), "sha256": sha256_file(path), "recordOffset": offset, "recordLength": length, "observedFields": observed_fields}


def extract_case(case: dict[str, Any]) -> dict[str, Any]:
    run_dir = Path(case["businessCheck"]["evidence"][0]["path"]).parent
    dateparm, tranfile, report = run_dir / "DATEPARM", run_dir / "TRANFILE", run_dir / "TRANREPT"
    start, end = parse_dateparm(dateparm)
    source_records = []
    for offset, raw in fixed_records(tranfile, 350):
        tx = parse_tranfile_record(raw)
        tx["selectedByDateParm"] = selected_by_date_range(tx["procDate"], start, end)
        tx["expectedDetail"] = expected_detail_from_source(tx, run_dir) if tx["selectedByDateParm"] else None
        tx["provenance"] = _record_provenance(tranfile, offset, 350, ["id", "procDate", "amount", "selectedByDateParm"])
        source_records.append(tx)
    classification = classify_report_records(report)
    detail_lines = []
    totals: dict[str, Any] = {}
    if report.exists():
        for rec in classification["records"]:
            raw = report.read_bytes()[rec["offset"]:rec["offset"] + 133]
            if rec["kind"] == "detail":
                detail = parse_detail_line(raw)
                detail["provenance"] = _record_provenance(report, rec["offset"], 133, ["lineText", "reportLineBytes"])
                detail_lines.append(detail)
            elif rec["kind"] in {"page_total", "account_total", "grand_total"}:
                totals[rec["kind"]] = {"text": rec["text"], "amount": _money_from_report(rec["text"][97:114])}
    selected = [r for r in source_records if r["selectedByDateParm"]]
    last_before_eof = source_records[-1] if source_records else None
    return {
        "runDir": str(run_dir),
        "dateRange": [start, end],
        "sourceTransactions": source_records,
        "selectedTransactions": selected,
        "reportClassification": classification,
        "detailLines": detail_lines,
        "totals": totals,
        "eofGuard": {
            "sourceCodePattern": "EOF totals branch is nested after stale TRAN-PROC-TS DATEPARM guard",
            "lastInputRecordSelectedBeforeEof": bool(last_before_eof and last_before_eof["selectedByDateParm"]),
            "lastInputRecordIdBeforeEof": (last_before_eof or {}).get("id"),
            "classification": "would_exercise_stale_addition_if_last_record_selected" if last_before_eof and last_before_eof["selectedByDateParm"] else "not_exercised_last_record_nonselected_by_date_guard",
        },
    }


def verdict(obligation_id: str, verdict_value: str, scope: str, failures: list[str], details: dict[str, Any]) -> dict[str, Any]:
    return {"obligationId": obligation_id, "verdict": verdict_value, "scope": scope, "failures": failures, "details": details, "sourceAnchors": SOURCE_ANCHORS}


def evaluate_extraction(extracted: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    selected = extracted["selectedTransactions"]
    details_by_id = {d["id"]: d for d in extracted["detailLines"]}

    framing_failures = list(extracted["reportClassification"]["failures"])
    for tx in extracted["sourceTransactions"]:
        has_detail = tx["id"] in details_by_id
        if has_detail != tx["selectedByDateParm"]:
            framing_failures.append(f"detail multiplicity for {tx['id']} was {has_detail}, expected {tx['selectedByDateParm']}")
    if [d["id"] for d in extracted["detailLines"]] != [tx["id"] for tx in selected]:
        framing_failures.append("detail order does not match selected TRANFILE order")
    out.append(verdict("TRANREPT-SRC-DETAIL-FRAMING", "pass" if not framing_failures else "failed", "all_records_framing_order_multiplicity", framing_failures, {"dateRange": extracted["dateRange"], "selectedIds": [tx["id"] for tx in selected], "detailIds": [d["id"] for d in extracted["detailLines"]], "recordCoverage": extracted["reportClassification"]["recordCoverage"]}))

    arithmetic_failures = []
    detail_sum = Decimal("0.00")
    for tx in selected:
        detail = details_by_id.get(tx["id"])
        exp = tx["expectedDetail"] or {}
        if detail is None:
            arithmetic_failures.append(f"missing detail for selected transaction {tx['id']}")
            continue
        detail_sum += Decimal(detail["amount"])
        for field in ["account", "type", "typeDescription", "category", "categoryDescription", "source", "amount"]:
            if str(detail.get(field)) != str(exp.get(field)):
                arithmetic_failures.append(f"{tx['id']} field {field} report={detail.get(field)!r} source={exp.get(field)!r}")
    out.append(verdict("TRANREPT-SRC-DETAIL-ARITHMETIC", "pass" if not arithmetic_failures else "failed", "source_expected_amounts_from_INPUT_TRANFILE_DATEPARM_and_support_files", arithmetic_failures, {"sumOfInRangeDetails": f"{detail_sum:.2f}", "selectedCount": len(selected)}))

    totals = extracted["totals"]
    eof = extracted["eofGuard"]
    if not totals and eof["classification"] == "not_exercised_last_record_nonselected_by_date_guard":
        legacy_verdict = "not_exercised"
        legacy_failures: list[str] = []
    elif totals and eof["classification"] == "would_exercise_stale_addition_if_last_record_selected":
        legacy_verdict = "observed_legacy_behavior"
        legacy_failures = []
    else:
        legacy_verdict = "inconclusive"
        legacy_failures = ["EOF/totals observation does not match source guard classification"]
    out.append(verdict("TRANREPT-SRC-EOF-TOTALS-LEGACY-BEHAVIOR", legacy_verdict, "observed_legacy_control_flow_only_not_financial_correctness", legacy_failures, {"eofGuard": eof, "totalsPresent": bool(totals), "observedTotals": totals}))

    if not totals:
        financial_verdict = "not_observable"
        financial_failures = []
    else:
        total_amount = f"{sum(Decimal(d['amount']) for d in extracted['detailLines']):.2f}"
        financial_failures = []
        for name in ["page_total", "account_total"]:
            if name in totals and totals[name]["amount"] != total_amount:
                financial_failures.append(f"{name} {totals[name]['amount']} != sum of in-range details {total_amount}")
        financial_verdict = "pass" if not financial_failures else "failed"
    out.append(verdict("TRANREPT-SRC-TOTALS-FINANCIAL-CORRECTNESS", financial_verdict, "separate_question_sum_of_in_range_details_vs_written_totals", financial_failures, {"sumOfInRangeDetails": f"{sum(Decimal(d['amount']) for d in extracted['detailLines']):.2f}", "observedTotals": totals}))
    return out


def _response_path_from_case(case: dict[str, Any]) -> Path | None:
    run_dir = Path(case["businessCheck"]["evidence"][0]["path"]).parent
    app_root = run_dir
    for parent in run_dir.parents:
        if parent.name == "zero-shot-runs":
            app_root = parent
            break
    hits = list(app_root.glob(f"{case['contractId']}/reporting/*/response.json"))
    return hits[0] if hits else None


def check_case(case: dict[str, Any]) -> dict[str, Any]:
    run_dir = Path(case["businessCheck"]["evidence"][0]["path"]).parent
    pins = []
    for name, label in [("DATEPARM", "input-DATEPARM"), ("TRANFILE", "input-TRANFILE"), ("CARDXREF", "input-CARDXREF"), ("TRANTYPE", "input-TRANTYPE"), ("TRANCATG", "input-TRANCATG"), ("audit.json", "audit")]:
        p = run_dir / name
        if p.exists():
            pins.append(pin(p, label))
    if (run_dir / "TRANREPT").exists():
        pins.append(pin(run_dir / "TRANREPT", "raw-TRANREPT"))
    response_path = _response_path_from_case(case)
    if response_path and response_path.exists():
        pins.append(pin(response_path, "api-response"))
    pin_failures = [failure for p in pins for failure in verify_pin(p)]
    try:
        extracted = extract_case(case)
        obligations = evaluate_extraction(extracted)
    except FileNotFoundError as exc:
        extracted = {"reportClassification": {"recordCoverage": "missing_report", "failures": ["missing_report"]}, "error": str(exc)}
        obligations = [verdict("TRANREPT-SRC-DETAIL-FRAMING", "failed", "input_output_presence", ["missing_report"], extracted)]
    if pin_failures:
        obligations.append(verdict("ARTIFACT-PINS", "failed", "actual_input_bytes_and_outputs", pin_failures, {}))
    verdicts = Counter(o["verdict"] for o in obligations)
    case_verdict = "failed" if verdicts.get("failed") else ("inconclusive" if verdicts.get("inconclusive") else "pass")
    api_contract_visibility = {
        "httpStatus": case.get("httpStatus"),
        "responseSha256DeclaredByComparison": case.get("responseSha256"),
        "responsePath": str(response_path) if response_path else None,
        "businessFieldVisibility": "API envelope/body captured separately; source-qualified TRANREPT checks use raw files, not public response as oracle",
    }
    return {**{k: case.get(k) for k in ["caseId", "contractId", "operationId", "track", "httpStatus", "structural", "measurementAdmissibility"]}, "caseVerdict": case_verdict, "obligationVerdicts": obligations, "reportClassification": extracted.get("reportClassification", {}), "rawSourceObservation": extracted, "apiContractVisibility": api_contract_visibility, "artifactPins": pins, "pinVerificationFailures": pin_failures, "noApiRerun": True}


def run(run_root: Path) -> dict[str, Any]:
    comparison = json.loads((run_root / "comparison.json").read_text(encoding="utf-8"))
    cases = [check_case(c) for c in comparison["cases"] if c.get("track") == "reporting"]
    verdict_counts = Counter(c["caseVerdict"] for c in cases)
    obligation_counts = Counter(v["verdict"] for c in cases for v in c["obligationVerdicts"])
    return {
        "kind": "complementary-reporting-source-extractor-v1-results",
        "createdUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "scope": "Read-only source-qualified checks over preserved seven reporting cross-arm cases from old run-20260916T112642Z; no API reruns and no output-derived oracle.",
        "summary": {"caseCount": len(cases), "caseVerdictCounts": dict(verdict_counts), "obligationVerdictCounts": dict(obligation_counts), "pinVerificationFailureCount": sum(len(c["pinVerificationFailures"]) for c in cases), "noApiReruns": True, "questionsSeparated": ["legacyEofBehavior", "financialCorrectness"]},
        "sourceRunPins": [pin(run_root / "comparison.json", "comparison"), pin(run_root / "run" / "campaign-report.json", "campaign-report")],
        "sourceAnchors": SOURCE_ANCHORS,
        "cases": cases,
    }


def write_status(out: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    text = f"""# complementary-reporting-source-extractor-v1

Status: source-qualified read-only reporting checks over the preserved seven cross-arm reporting cases.

- Cases checked: {s['caseCount']}
- Case verdicts: {s['caseVerdictCounts']}
- Obligation verdicts: {s['obligationVerdictCounts']}
- Pin verification failures: {s['pinVerificationFailureCount']}
- Separation: legacy EOF behavior is reported separately from financial correctness; missing totals with a non-selected stale EOF guard are `not_exercised`, not correct totals.
- Oracle boundary: expected detail values come from actual DATEPARM/TRANFILE/support input bytes and COBOL/JCL source anchors, not from API reruns or report-output-derived expectations.
"""
    (out.parent / "STATUS.md").write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    payload = run(args.run_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    write_status(args.out, payload)
    print(json.dumps({"ok": True, "caseCount": payload["summary"]["caseCount"], "caseVerdictCounts": payload["summary"]["caseVerdictCounts"], "out": str(args.out)}, ensure_ascii=False))
    return 0

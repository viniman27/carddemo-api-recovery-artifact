from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import time
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
P3 = ROOT.parent
CYCLE = P3.parent
P2B = CYCLE / "P2b"
PREP = CYCLE.parent / "aws-carddemo-preparation"
CORPUS = PREP / "research-corpus"
SOURCE_CBTRN03C = CORPUS / "app/cbl/CBTRN03C.cbl"
SOURCE_CVTRA07Y = CORPUS / "app/cpy/CVTRA07Y.cpy"
BASE_LOOKUP_PACKAGE = P3 / "fixture-materialization-v2" / "package" / "reporting"
EVIDENCE = ROOT / "evidence"
RAW_OUT = EVIDENCE / "raw-report-outputs"
FROZEN = EVIDENCE / "frozen-inputs"
RUNS = EVIDENCE / "p2b-runs"
COMMAND_LOG = EVIDENCE / "command-log.jsonl"
REPORT_RECORD_BYTES = 133
TRANSACTION_RECORD_BYTES = 350


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def source_facts() -> dict[str, Any]:
    return {
        "source_root": str(CORPUS),
        "cbtrn03c_path": "app/cbl/CBTRN03C.cbl",
        "cbtrn03c_sha256": sha256_file(SOURCE_CBTRN03C),
        "cvtra07y_path": "app/cpy/CVTRA07Y.cpy",
        "cvtra07y_sha256": sha256_file(SOURCE_CVTRA07Y),
        "report_record_bytes": REPORT_RECORD_BYTES,
        "transaction_record_bytes": TRANSACTION_RECORD_BYTES,
        "page_size_source_value": 20,
        "date_filter_lines": [170, 178],
        "detail_layout_lines": [15, 31],
        "total_layout_lines": [50, 66],
        "eof_total_lines": [197, 204],
        "eof_totals_has_stale_tran_amt_guard": True,
        "qualification": "source-grounded byte/order checks; final totals qualified only as inconclusive under EOF branch unless selected and observed",
    }


@dataclass(frozen=True)
class Txn:
    transaction_id: str
    card: str
    amount_cents: int
    proc_ts: str
    type_code: str = "01"
    category_code: str = "0005"
    source: str = "System"
    description: str = "Reporting boundary fixture"
    merchant: str = "000000001"
    merchant_name: str = "Report Merchant"
    merchant_city: str = "Sometown"
    merchant_postal: str = "70000000"
    orig_ts: str = "2022-07-01-00.00.00.000000"

    def to_bytes(self) -> bytes:
        parts = [
            self.transaction_id.encode("ascii").ljust(16)[:16],
            self.type_code.encode("ascii").ljust(2)[:2],
            self.category_code.encode("ascii").ljust(4)[:4],
            self.source.encode("ascii").ljust(10)[:10],
            self.description.encode("ascii").ljust(100)[:100],
            f"{self.amount_cents:011d}".encode("ascii"),
            self.merchant.encode("ascii").ljust(9)[:9],
            self.merchant_name.encode("ascii").ljust(50)[:50],
            self.merchant_city.encode("ascii").ljust(50)[:50],
            self.merchant_postal.encode("ascii").ljust(10)[:10],
            self.card.encode("ascii").ljust(16)[:16],
            self.orig_ts.encode("ascii").ljust(26)[:26],
            self.proc_ts.encode("ascii").ljust(26)[:26],
            b" " * 20,
        ]
        data = b"".join(parts)
        if len(data) != TRANSACTION_RECORD_BYTES:
            raise AssertionError(len(data))
        return data


@dataclass(frozen=True)
class CaseDefinition:
    case_id: str
    purpose: str
    date_range: tuple[str, str]
    transactions: tuple[Txn, ...]
    expected_detail_ids: list[str]
    partitions: list[str]
    qualified_total_oracle: str = "inconclusive-eof-branch"


def build_case_definitions() -> list[CaseDefinition]:
    start = "2022-07-01"
    end = "2022-07-31"
    card1 = "4111111111111111"
    card2 = "4222222222222222"
    page = tuple(
        Txn(f"PAGE20-{i:08d}"[:16], card1, 100 + i, f"2022-07-{1 + (i % 28):02d}-12.00.00.000000", description="Pagination threshold")
        for i in range(20)
    )
    return [
        CaseDefinition(
            "date-boundaries-in-out-v1",
            "Inclusive start/end date filtering with explicit out-of-range negative controls.",
            (start, end),
            (
                Txn("REPORT-START-001", card1, 100, "2022-07-01-00.00.00.000000"),
                Txn("REPORT-END---001", card1, 200, "2022-07-31-23.59.59.000000"),
                Txn("REPORT-BEFORE001", card1, 300, "2022-06-30-23.59.59.000000"),
                Txn("REPORT-AFTER-001", card1, 400, "2022-08-01-00.00.00.000000"),
            ),
            ["REPORT-START-001", "REPORT-END---001"],
            ["date:start-boundary", "date:end-boundary", "date:before-out-of-range", "date:after-out-of-range"],
        ),
        CaseDefinition(
            "empty-in-range-v1",
            "No transaction qualifies the DATEPARM range; known empty report behavior is preserved without claiming absence as positive business total.",
            ("2022-09-01", "2022-09-30"),
            (
                Txn("REPORT-JULY--001", card1, 500, "2022-07-15-10.00.00.000000"),
                Txn("REPORT-AUG---001", card1, 600, "2022-08-15-10.00.00.000000"),
            ),
            [],
            ["date:none-in-range", "empty-output-qualified-as-no-details-only"],
        ),
        CaseDefinition(
            "card-break-two-groups-v1",
            "Two card/account groups in already sorted input to exercise source account-break branch without asserting final EOF account total correctness.",
            (start, end),
            (
                Txn("GROUP1-ITEM-0001", card1, 111, "2022-07-10-10.00.00.000000"),
                Txn("GROUP1-ITEM-0002", card1, 222, "2022-07-11-10.00.00.000000"),
                Txn("GROUP2-ITEM-0001", card2, 333, "2022-07-12-10.00.00.000000"),
                Txn("GROUP2-ITEM-0002", card2, 444, "2022-07-13-10.00.00.000000"),
            ),
            ["GROUP1-ITEM-0001", "GROUP1-ITEM-0002", "GROUP2-ITEM-0001", "GROUP2-ITEM-0002"],
            ["group:first-card", "group:card-break", "order:multiplicity"],
        ),
        CaseDefinition(
            "pagination-threshold-20-v1",
            "Twenty in-range details to hit the source WS-PAGE-SIZE=20 threshold and preserve raw pagination/totals output for qualification.",
            (start, end),
            page,
            [t.transaction_id for t in page],
            ["pagination:source-page-size-20", "order:multiplicity", "totals:eof-guarded"],
        ),
    ]


def descriptor_sha256(fx: dict[str, Any]) -> str:
    canonical = {k: v for k, v in fx.items() if k != "contentSha256"}
    return sha256_bytes(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode())


def freeze_case(case: CaseDefinition) -> Path:
    case_dir = FROZEN / case.case_id / "reporting"
    case_dir.mkdir(parents=True, exist_ok=True)
    for name in ["CARDXREF", "TRANTYPE", "TRANCATG"]:
        shutil.copy2(BASE_LOOKUP_PACKAGE / name, case_dir / name)
    (case_dir / "DATEPARM").write_bytes((case.date_range[0] + " " + case.date_range[1]).encode("ascii").ljust(80, b" "))
    (case_dir / "TRANFILE").write_bytes(b"".join(t.to_bytes() for t in case.transactions))
    files = {name: f"reporting/{name}" for name in ["CARDXREF", "DATEPARM", "TRANCATG", "TRANFILE", "TRANTYPE"]}
    pins = {name: {"bytes": (case_dir / name).stat().st_size, "sha256": sha256_file(case_dir / name)} for name in files}
    fx = {
        "fixtureId": f"{case.case_id}-technical-reporting",
        "track": "reporting",
        "materializer": {"kind": "local_file_package", "files": files, "filePins": pins},
        "provenance": {"class": "local_physical_fixture_package", "officialFixture": False, "source": "new P3 complementary reporting essential package", "purpose": case.purpose},
        "exposure": {"label": "technical-only", "notOracle": True, "notExtractionInput": True, "notPublicRequest": True},
        "reset": {"default": "fresh_dir_per_run", "statefulSequence": "not_used"},
    }
    fx["contentSha256"] = descriptor_sha256(fx)
    registry = {"kind": "p3-local-technical-fixture-selection", "status": "technical_local_only", "fixtures": [fx]}
    reg_path = FROZEN / case.case_id / "fixture-registry.json"
    reg_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n")
    manifest = {
        "caseId": case.case_id,
        "purpose": case.purpose,
        "dateRange": list(case.date_range),
        "transactions": [t.__dict__ for t in case.transactions],
        "expectedDetailIds": case.expected_detail_ids,
        "partitions": case.partitions,
        "qualifiedTotalOracle": case.qualified_total_oracle,
        "fixtureRegistry": str(reg_path),
        "filePins": pins,
        "sourceFacts": source_facts(),
    }
    (FROZEN / case.case_id / "freeze-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return reg_path


@dataclass(frozen=True)
class ParsedReport:
    framing: dict[str, Any]
    raw_records: list[dict[str, Any]]
    details: list[dict[str, Any]]
    totals: list[dict[str, Any]]
    headers: list[dict[str, Any]]
    unknown_records: list[dict[str, Any]]


def _amount_from_text(text: str) -> str:
    cleaned = text.strip().replace(",", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if not cleaned or set(cleaned) == {"."}:
        return "0.00"
    return f"{Decimal(cleaned):.2f}"


def parse_report_bytes(data: bytes) -> ParsedReport:
    framing: dict[str, Any] = {"bytes": len(data), "recordSize": REPORT_RECORD_BYTES, "eofLimit": "parse stops at physical file byte length"}
    if len(data) == 0:
        framing.update({"classification": "known_empty", "recordCount": 0})
        return ParsedReport(framing, [], [], [], [], [])
    if len(data) % REPORT_RECORD_BYTES != 0:
        framing.update({"classification": "truncated", "recordCount": len(data) // REPORT_RECORD_BYTES, "remainderBytes": len(data) % REPORT_RECORD_BYTES})
        return ParsedReport(framing, [], [], [], [], [])
    raw_records=[]; details=[]; totals=[]; headers=[]; unknown=[]
    for idx in range(0, len(data), REPORT_RECORD_BYTES):
        rec = data[idx:idx+REPORT_RECORD_BYTES]
        raw = rec.decode("ascii", "replace")
        text = raw.rstrip()
        entry = {"index": idx // REPORT_RECORD_BYTES, "offset": idx, "rawBytes": rec.hex(), "rawText": text}
        cls = "unknown_meaningful"
        if not text.strip(): cls = "blank"
        elif set(text.strip()) == {"-"}: cls = "rule"
        elif text.startswith("Transaction ID"): cls = "column_header"
        elif raw.startswith("DALYREPT"):
            cls = "header"; headers.append({**entry, "startText": raw[91:101].strip(), "endText": raw[105:115].strip()})
        elif raw.startswith("Page Total") or raw.startswith("Account Total") or raw.startswith("Grand Total"):
            label = "Page Total" if raw.startswith("Page Total") else "Account Total" if raw.startswith("Account Total") else "Grand Total"
            cls = "total"; totals.append({**entry, "label": label, "amountText": raw[97:112].strip(), "amount": _amount_from_text(raw[97:112])})
        elif len(raw) >= 112 and raw[16] == " " and raw[28] == " " and raw[31] == "-" and raw[47] == " " and raw[52] == "-":
            cls = "detail"; details.append({**entry, "transactionId": raw[0:16].strip(), "accountReference": raw[17:28].strip(), "typeCode": raw[29:31].strip(), "categoryCode": raw[48:52].strip(), "source": raw[83:93].strip(), "amountText": raw[97:112].strip(), "amount": _amount_from_text(raw[97:112])})
        if cls == "unknown_meaningful":
            unknown.append({**entry, "classification": cls})
        raw_records.append({**entry, "classification": cls})
    framing.update({"classification": "unmapped_meaningful" if unknown else "available", "recordCount": len(raw_records)})
    return ParsedReport(framing, raw_records, details, totals, headers, unknown)


def parse_report_file(path: Path) -> ParsedReport:
    return parse_report_bytes(path.read_bytes())


def parsed_summary(parsed: ParsedReport) -> dict[str, Any]:
    return {
        "detail_ids": [d["transactionId"] for d in parsed.details],
        "detail_amounts": {d["transactionId"]: d["amount"] for d in parsed.details},
        "totals": parsed.totals,
        "headers": parsed.headers,
        "framing": parsed.framing,
        "unknown_records": parsed.unknown_records,
        "raw_record_count": len(parsed.raw_records),
    }


def qualify_case_result(case: CaseDefinition, observed: dict[str, Any], runtime_status: int) -> dict[str, Any]:
    failures=[]
    if runtime_status not in (200, 500):
        failures.append(f"unexpected runtime status {runtime_status}")
    if observed.get("framing", {}).get("classification") not in {"available", "known_empty"}:
        failures.append(f"report framing not qualified: {observed.get('framing', {}).get('classification')}")
    if observed.get("unknown_records"):
        failures.append("unknown meaningful report records present")
    if observed.get("detail_ids") != case.expected_detail_ids:
        failures.append("detail order/multiplicity mismatch")
    expected_amounts = {t.transaction_id: f"{Decimal(t.amount_cents) / Decimal(100):.2f}" for t in case.transactions if t.transaction_id in case.expected_detail_ids}
    for tid, amount in expected_amounts.items():
        if observed.get("detail_amounts", {}).get(tid) != amount:
            failures.append(f"detail amount mismatch for {tid}")
    total_qualification = case.qualified_total_oracle
    if case.qualified_total_oracle != "inconclusive-eof-branch":
        detail_sum = sum(Decimal(v) for v in observed.get("detail_amounts", {}).values()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if not observed.get("totals"):
            failures.append("qualified totals absent")
        for total in observed.get("totals", []):
            if Decimal(total["amount"]) != detail_sum:
                failures.append(f"total {total.get('label')} != detail sum {detail_sum:.2f}")
    return {
        "caseId": case.case_id,
        "status": "failed" if failures else "pass",
        "failures": failures,
        "partitions": case.partitions,
        "expectedDetailIds": case.expected_detail_ids,
        "observedDetailIds": observed.get("detail_ids"),
        "totalQualification": total_qualification,
        "observedTotals": observed.get("totals"),
        "framing": observed.get("framing"),
        "rawRecordCount": observed.get("raw_record_count"),
    }


def load_p2b():
    spec = importlib.util.spec_from_file_location("p2b_reporting_essential_binding", P2B / "p2b_binding.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load p2b binding")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.RUNS = RUNS
    mod.COMMAND_LOG = COMMAND_LOG
    return mod


def run_cases() -> dict[str, Any]:
    EVIDENCE.mkdir(exist_ok=True)
    shutil.rmtree(FROZEN, ignore_errors=True)
    shutil.rmtree(RAW_OUT, ignore_errors=True)
    shutil.rmtree(RUNS, ignore_errors=True)
    FROZEN.mkdir(parents=True)
    RAW_OUT.mkdir(parents=True)
    RUNS.mkdir(parents=True)
    COMMAND_LOG.write_text("")
    p2b = load_p2b()
    if not (p2b.BUILD / "CBTRN03C").exists():
        p2b.build()
    cases = build_case_definitions()
    results=[]
    freeze_manifests=[]
    for case in cases:
        reg = freeze_case(case)
        freeze_manifests.append(str((FROZEN / case.case_id / "freeze-manifest.json").resolve()))
        os.environ[p2b.FIXTURE_ENV] = str(reg)
        status, body, audit = p2b.reporting(f"report-essential-{case.case_id}-{int(time.time()*1000)}")
        wd = Path(audit["INV"]["workdir"])
        report_path = wd / "TRANREPT"
        raw_copy = RAW_OUT / f"{case.case_id}.TRANREPT.bin"
        if report_path.exists():
            shutil.copy2(report_path, raw_copy)
            parsed = parse_report_file(raw_copy)
            summary = parsed_summary(parsed)
        else:
            summary = {"detail_ids": [], "detail_amounts": {}, "totals": [], "headers": [], "framing": {"classification": "missing", "recordSize": REPORT_RECORD_BYTES}, "unknown_records": [], "raw_record_count": 0}
        qualification = qualify_case_result(case, summary, status)
        case_result = {
            **qualification,
            "runtimeStatus": status,
            "responseBody": body,
            "auditPath": str((wd / "audit.json").resolve()),
            "rawReportPath": str(raw_copy.resolve()) if raw_copy.exists() else None,
            "rawReportSha256": sha256_file(raw_copy) if raw_copy.exists() else None,
            "parsedReportPath": str((RAW_OUT / f"{case.case_id}.parsed.json").resolve()),
        }
        (RAW_OUT / f"{case.case_id}.parsed.json").write_text(json.dumps({"rawRecords": parsed.raw_records if report_path.exists() else [], "details": parsed.details if report_path.exists() else [], "totals": parsed.totals if report_path.exists() else [], "headers": parsed.headers if report_path.exists() else [], "unknownRecords": parsed.unknown_records if report_path.exists() else [], "summary": summary}, indent=2, sort_keys=True) + "\n")
        results.append(case_result)
    matrix = build_obligation_partition_matrix(results)
    report = {
        "kind": "complementary-reporting-essential-v1-results",
        "createdUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "new package only; REPORTING complementary essentials; local API {} external fixture selection; no COBOL/API/contracts/main study edits",
        "sourceFacts": source_facts(),
        "freezeManifests": freeze_manifests,
        "results": results,
        "statusCounts": {s: sum(1 for r in results if r["status"] == s) for s in sorted({r["status"] for r in results})},
        "obligationPartitionMatrix": matrix,
        "eofLimits": ["parser stops at physical TRANREPT EOF", "CBTRN03C EOF totals branch remains source-qualified as inconclusive unless selected and observed", "missing output is not treated as empty"],
    }
    (EVIDENCE / "reporting-essential-results.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (EVIDENCE / "obligation-partition-matrix.json").write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n")
    return report


def build_obligation_partition_matrix(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        ("R-DATE-START", "date", "inclusive start boundary", "source-grounded", "detail order contains start-date record"),
        ("R-DATE-END", "date", "inclusive end boundary", "source-grounded", "detail order contains end-date record"),
        ("R-DATE-OUT-BEFORE", "date", "exclude before range", "source-grounded", "before-range id absent from details"),
        ("R-DATE-OUT-AFTER", "date", "exclude after range", "source-grounded", "after-range id absent from details"),
        ("R-EMPTY", "date", "empty in-range partition", "runtime-observed", "known empty/no-detail output only, no positive total claim"),
        ("R-GROUP-CARDBREAK", "grouping", "card/account break partition", "runtime-observed/source-limited", "detail order across two cards; totals guarded"),
        ("R-PAGINATION-20", "pagination", "WS-PAGE-SIZE=20 threshold", "source-grounded/runtime-observed", "20 detail records and raw pagination records preserved"),
        ("R-TOTALS-EOF-GUARD", "totals", "EOF totals branch qualification", "inconclusive-by-source", "not used as final arithmetic oracle because source adds stale TRAN-AMT on EOF path"),
    ]
    related_map = {
        "R-DATE-START": ["date-boundaries-in-out-v1"],
        "R-DATE-END": ["date-boundaries-in-out-v1"],
        "R-DATE-OUT-BEFORE": ["date-boundaries-in-out-v1"],
        "R-DATE-OUT-AFTER": ["date-boundaries-in-out-v1"],
        "R-EMPTY": ["empty-in-range-v1"],
        "R-GROUP-CARDBREAK": ["card-break-two-groups-v1"],
        "R-PAGINATION-20": ["pagination-threshold-20-v1"],
        "R-TOTALS-EOF-GUARD": ["date-boundaries-in-out-v1", "card-break-two-groups-v1", "pagination-threshold-20-v1"],
    }
    out=[]
    completed = {r["caseId"]: r["status"] for r in results}
    for oid, group, partition, qualification, evidence in rows:
        related = related_map[oid]
        out.append({"obligation": oid, "group": group, "partition": partition, "qualification": qualification, "evidence": evidence, "relatedCases": related, "caseStatuses": {case_id: completed.get(case_id, "not-run") for case_id in related}, "notCountsProxy": True})
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args(argv)
    if args.run:
        report = run_cases()
        print(json.dumps({"results": str((EVIDENCE / "reporting-essential-results.json").resolve()), "statusCounts": report["statusCounts"], "cases": [r["caseId"] + ':' + r["status"] for r in report["results"]]}, indent=2))
        return 0 if all(r["status"] == "pass" for r in report["results"]) else 1
    print(json.dumps({"sourceFacts": source_facts(), "cases": [c.case_id for c in build_case_definitions()]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

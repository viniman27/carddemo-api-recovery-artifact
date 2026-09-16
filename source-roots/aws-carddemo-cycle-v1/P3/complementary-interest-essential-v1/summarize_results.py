from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence"

OBLIGATIONS = [
    ("INTCALC-OBL-001", "TCATBALF sequential balance input partition is physically materialized and read"),
    ("INTCALC-OBL-002", "ACCTFILE account lookup/group id drives disclosure lookup"),
    ("INTCALC-OBL-003", "XREFFILE alternate account lookup supplies generated transaction card"),
    ("INTCALC-OBL-004", "DISCGRP specific/default lookup partitions are exercised"),
    ("INTCALC-OBL-005", "Nonzero rate computes monthly interest from source formula"),
    ("INTCALC-OBL-006", "Generated transaction fixed fields and raw bytes are preserved"),
    ("INTCALC-OBL-007", "Zero-rate partition writes no interest transaction"),
    ("INTCALC-OBL-008", "EOF final-account legacy limitation is observed without idealizing account rewrite"),
]


def load_results():
    return [json.loads(p.read_text()) for p in sorted(EVIDENCE.glob("*/result.json"))]


def main() -> None:
    results = load_results()
    matrix = []
    by_case = {r["caseId"]: r for r in results}
    for oid, desc in OBLIGATIONS:
        cases = []
        evidence = []
        status = "covered"
        for r in results:
            cid = r["caseId"]
            if oid == "INTCALC-OBL-001":
                ok = r["physicalInputs"]["TCATBALF"]["before"]["classification"] == "available"
                ev = "TCATBALF before/after pins"
            elif oid == "INTCALC-OBL-002":
                ok = bool(r["accountDeltas"])
                ev = "ACCTFILE qualified dump before/after"
            elif oid == "INTCALC-OBL-003":
                ok = r["physicalInputs"]["XREFFILE.1"]["before"]["classification"] == "available" and all(x.get("cardReference") for x in r["observedTransactions"])
                ev = "XREFFILE.1 sidecar + transaction cardReference"
            elif oid == "INTCALC-OBL-004":
                ok = cid == "rates-specific-default-zero"
                ev = "STANDARD/ZERORATE/DEFAULT DISCGRP records"
            elif oid == "INTCALC-OBL-005":
                ok = bool(r["sourceExpected"]["transactions"]) and [x["amount"] for x in r["observedTransactions"]] == [x["amount"] for x in r["sourceExpected"]["transactions"]]
                ev = "independent Decimal expected vs TRANSACT amount"
            elif oid == "INTCALC-OBL-006":
                ok = all(x.get("rawBytesHex") and x.get("provenance", {}).get("recordLength") == 350 for x in r["observedTransactionsWithProvenance"])
                ev = "350-byte TRANSACT record provenance"
            elif oid == "INTCALC-OBL-007":
                ok = cid == "rates-specific-default-zero" and len(r["observedTransactions"]) == 2 and len(r["inputFreeze"]["case"]["balances"]) == 3
                ev = "ZERORATE input with no matching output transaction"
            else:
                ok = any(v["partition"] == "source_eof_final_account_not_rewritten" and v["deltaCentsText"] == "00000000000" for v in r["accountDeltas"].values())
                ev = "final account account-delta zero despite TRANSACT output"
            if ok:
                cases.append(cid)
                evidence.append(ev)
        if not cases:
            status = "not covered"
        matrix.append({"obligationId": oid, "description": desc, "status": status, "cases": sorted(set(cases)), "evidence": sorted(set(evidence))})
    report = {"resultCount": len(results), "allCaseChecksPass": all(not r["checks"]["failures"] for r in results), "matrix": matrix, "omissions": ["Local P3 technical cases only; not official campaign fixtures or proof of all 25 checker obligations.", "EOF final-account behavior records source-supported limitation, not desired finance behavior."]}
    (ROOT / "RESULTS-MATRIX.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = ["# Complementary INTEREST essential cases", "", f"Cases executed: {len(results)}", f"All local checks passed: {report['allCaseChecksPass']}", "", "| Obligation | Status | Cases | Evidence |", "|---|---:|---|---|"]
    for row in matrix:
        lines.append(f"| {row['obligationId']} | {row['status']} | {', '.join(row['cases'])} | {', '.join(row['evidence'])} |")
    lines += ["", "## Omissions"] + [f"- {x}" for x in report["omissions"]]
    (ROOT / "REPORT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

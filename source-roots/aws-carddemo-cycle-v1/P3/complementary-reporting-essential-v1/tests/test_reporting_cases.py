import json
import unittest
from decimal import Decimal
from pathlib import Path

from reporting_essential import build_case_definitions, parse_report_file, qualify_case_result, source_facts


class ReportingEssentialCasesTest(unittest.TestCase):
    def test_source_facts_are_exact_pinned_reporting_boundaries(self):
        facts = source_facts()
        self.assertEqual(facts["cbtrn03c_sha256"], "8691e625502b7efcfd7ba4ae61797132e7b68f3fd5fedcdcc7dd6488f6871eef")
        self.assertEqual(facts["cvtra07y_sha256"], "72ba597b1a40e1e6cf908e15da9e6a818a0ab899ef1d27d15edeb074963102fa")
        self.assertEqual(facts["report_record_bytes"], 133)
        self.assertEqual(facts["transaction_record_bytes"], 350)
        self.assertEqual(facts["page_size_source_value"], 20)
        self.assertEqual(facts["date_filter_lines"], [170, 178])
        self.assertEqual(facts["eof_total_lines"], [197, 204])
        self.assertTrue(facts["eof_totals_has_stale_tran_amt_guard"])

    def test_case_definitions_partition_boundaries_and_freeze_expected_inputs(self):
        cases = build_case_definitions()
        self.assertEqual([c.case_id for c in cases], [
            "date-boundaries-in-out-v1",
            "empty-in-range-v1",
            "card-break-two-groups-v1",
            "pagination-threshold-20-v1",
        ])
        by_id = {c.case_id: c for c in cases}
        self.assertEqual([r.transaction_id for r in by_id["date-boundaries-in-out-v1"].transactions], [
            "REPORT-START-001",
            "REPORT-END---001",
            "REPORT-BEFORE001",
            "REPORT-AFTER-001",
        ])
        self.assertEqual(by_id["date-boundaries-in-out-v1"].expected_detail_ids, ["REPORT-START-001", "REPORT-END---001"])
        self.assertEqual(by_id["empty-in-range-v1"].expected_detail_ids, [])
        self.assertEqual(len(by_id["pagination-threshold-20-v1"].expected_detail_ids), 20)
        self.assertEqual(by_id["pagination-threshold-20-v1"].qualified_total_oracle, "inconclusive-eof-branch")

    def test_parser_distinguishes_missing_empty_known_wrong_unknown_and_preserves_order(self):
        with self.assertRaises(FileNotFoundError):
            parse_report_file(Path("/definitely/not/present"))
        tmp = Path(__file__).resolve().parents[1] / "evidence" / "unit-parser-empty.tmp"
        tmp.parent.mkdir(exist_ok=True)
        tmp.write_bytes(b"")
        parsed = parse_report_file(tmp)
        self.assertEqual(parsed.framing["classification"], "known_empty")
        rec1 = b"REPORT-UNIT-001".ljust(133, b" ")
        rec2 = b"not a known line".ljust(133, b" ")
        tmp.write_bytes(rec1 + rec2)
        parsed = parse_report_file(tmp)
        self.assertEqual(parsed.framing["classification"], "unmapped_meaningful")
        self.assertEqual(parsed.unknown_records[0]["index"], 0)
        self.assertEqual(parsed.unknown_records[1]["index"], 1)
        self.assertEqual([r["index"] for r in parsed.raw_records], [0, 1])
        tmp.unlink()

    def test_qualifier_requires_exact_order_multiplicity_and_qualified_totals(self):
        case = build_case_definitions()[0]
        good = {
            "detail_ids": ["REPORT-START-001", "REPORT-END---001"],
            "detail_amounts": {"REPORT-START-001": "1.00", "REPORT-END---001": "2.00"},
            "totals": [],
            "framing": {"classification": "available", "recordCount": 8},
            "unknown_records": [],
            "raw_record_count": 8,
        }
        result = qualify_case_result(case, good, runtime_status=200)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["totalQualification"], "inconclusive-eof-branch")
        wrong = dict(good)
        wrong["detail_ids"] = ["REPORT-END---001", "REPORT-START-001"]
        result = qualify_case_result(case, wrong, runtime_status=200)
        self.assertEqual(result["status"], "failed")
        self.assertIn("detail order/multiplicity mismatch", result["failures"])


if __name__ == "__main__":
    unittest.main()

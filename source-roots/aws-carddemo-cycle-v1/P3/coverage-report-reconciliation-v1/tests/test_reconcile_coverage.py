import json
import tempfile
import unittest
from pathlib import Path

from reconcile_coverage import (
    AmbiguousGcovUnitError,
    MissingGcovUnitError,
    parse_gcov_stdout_units,
    parse_gcov_file,
    select_units_by_program,
    reconcile_report,
)

BASE = Path(__file__).resolve().parents[2]
CANDIDATE = BASE / "coverage-candidate-check-v2" / "candidate-coverage-report.json"
REPORTING_MAIN = BASE / "coverage-candidate-check-v2" / "isolated-cycle" / "aws-carddemo-cycle-v1" / "P2b" / "runs" / "reporting-ljqnc895" / "gcov" / "CBTRN03C.c.gcov"


class CoverageReconciliationTests(unittest.TestCase):
    def test_stdout_parser_keeps_metrics_bound_to_each_source_unit(self):
        report = json.loads(CANDIDATE.read_text())
        stdout = report["invocations"][2]["gcov11"]["stdout"]
        units = parse_gcov_stdout_units(stdout)
        by_suffix = {Path(u["source"]).name: u for u in units}
        self.assertEqual(by_suffix["CBTRN03C.c"]["lines"]["total"], 1192)
        self.assertEqual(by_suffix["CBTRN03C.c"]["branches"]["total"], 272)
        self.assertEqual(by_suffix["CBTRN03C.c"]["calls"]["total"], 157)
        self.assertEqual(by_suffix["CBTRN03C.c.h"]["lines"]["total"], 50)
        self.assertEqual(by_suffix["CBTRN03C.c.h"]["branches"]["total"], 48)
        self.assertEqual(by_suffix["CBTRN03C.c.h"]["calls"]["total"], 2)

    def test_parse_gcov_file_counts_real_reporting_main_unit_exactly(self):
        unit = parse_gcov_file(REPORTING_MAIN)
        self.assertEqual(Path(unit["source"]).name, "CBTRN03C.c")
        self.assertEqual(unit["lines"], {"executed": 655, "total": 1192})
        self.assertEqual(unit["branches"], {"executed": 216, "taken_at_least_once": 111, "total": 272})
        self.assertEqual(unit["calls"], {"executed": 85, "total": 157})

    def test_select_units_rejects_missing_main_unit_instead_of_header_fallback(self):
        header_only = {"source": "/tmp/CBTRN03C.c.h", "path": "/tmp/CBTRN03C.c.h.gcov"}
        with self.assertRaises(MissingGcovUnitError):
            select_units_by_program("CBTRN03C", [header_only])

    def test_select_units_rejects_ambiguous_main_units(self):
        main_a = {"source": "/tmp/a/CBTRN03C.c", "path": "/tmp/a/CBTRN03C.c.gcov"}
        main_b = {"source": "/tmp/b/CBTRN03C.c", "path": "/tmp/b/CBTRN03C.c.gcov"}
        with self.assertRaises(AmbiguousGcovUnitError):
            select_units_by_program("CBTRN03C", [main_a, main_b])

    def test_reconcile_all_six_invocations_and_preserve_exact_main_denominators(self):
        with tempfile.TemporaryDirectory() as td:
            result = reconcile_report(BASE, Path(td))
        self.assertEqual(result["summary"]["invocationsProcessed"], 6)
        self.assertEqual(result["summary"]["invocationsWithMainGcovUnit"], 6)
        expected = {
            "CBTRN02C": {"lines": 1120, "branches": 288, "calls": 154},
            "CBACT04C": {"lines": 1029, "branches": 266, "calls": 148},
            "CBTRN03C": {"lines": 1192, "branches": 272, "calls": 157},
        }
        for row in result["totalsByProgram"]:
            self.assertEqual(row["mainGeneratedCComparableDenominator"], expected[row["program"]])
        self.assertEqual(result["summary"]["normalProcessExit"], 6)
        self.assertEqual(result["summary"]["exit4FlushObserved"], 2)


if __name__ == "__main__":
    unittest.main()

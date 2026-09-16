import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = ROOT / "P3" / "complementary-reporting-source-extractor-v1"
RUN = ROOT / "P3" / "complementary-crossarm-v1" / "run-20260916T112642Z"

sys.path.insert(0, str(PKG))


class ReportingSourceExtractorTests(unittest.TestCase):
    def _case(self, case_id="CROSSARM-E1-1-reporting"):
        comparison = json.loads((RUN / "comparison.json").read_text(encoding="utf-8"))
        return next(c for c in comparison["cases"] if c["caseId"] == case_id)

    def test_cli_checks_actual_preserved_7_reporting_cases_without_api_reruns(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "results.json"
            completed = subprocess.run(
                [sys.executable, "-m", "reporting_source_extractor", "--run-root", str(RUN), "--out", str(out)],
                cwd=PKG,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            payload = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(7, payload["summary"]["caseCount"])
        self.assertTrue(payload["summary"]["noApiReruns"])
        self.assertEqual(0, payload["summary"]["pinVerificationFailureCount"])
        self.assertNotEqual({"inconclusive": 7}, payload["summary"]["caseVerdictCounts"])
        self.assertEqual({"legacyEofBehavior", "financialCorrectness"}, set(payload["summary"]["questionsSeparated"]))
        for case in payload["cases"]:
            obligations = {item["obligationId"]: item for item in case["obligationVerdicts"]}
            self.assertEqual("pass", obligations["TRANREPT-SRC-DETAIL-FRAMING"]["verdict"])
            self.assertEqual("pass", obligations["TRANREPT-SRC-DETAIL-ARITHMETIC"]["verdict"])
            self.assertEqual("not_exercised", obligations["TRANREPT-SRC-EOF-TOTALS-LEGACY-BEHAVIOR"]["verdict"])
            self.assertEqual("not_observable", obligations["TRANREPT-SRC-TOTALS-FINANCIAL-CORRECTNESS"]["verdict"])
            self.assertEqual("all_records_classified", case["reportClassification"]["recordCoverage"])

    def test_same_length_amount_tamper_is_caught_against_source_input_not_report_oracle(self):
        from reporting_source_extractor.extractor import check_case
        case = self._case()
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "reporting"
            shutil.copytree(Path(case["businessCheck"]["evidence"][0]["path"]).parent, work)
            raw = bytearray((work / "TRANREPT").read_bytes())
            original = bytes(raw)
            idx = original.index(b"12.00")
            raw[idx:idx + 5] = b"13.00"
            self.assertEqual(len(raw), len(original))
            (work / "TRANREPT").write_bytes(raw)
            fake = json.loads(json.dumps(case))
            fake["businessCheck"]["evidence"][0]["path"] = str(work / "TRANREPT")
            result = check_case(fake)
        obligations = {item["obligationId"]: item for item in result["obligationVerdicts"]}
        self.assertEqual("failed", obligations["TRANREPT-SRC-DETAIL-ARITHMETIC"]["verdict"])
        self.assertIn("amount", "; ".join(obligations["TRANREPT-SRC-DETAIL-ARITHMETIC"]["failures"]))

    def test_missing_report_is_not_treated_as_empty_success(self):
        from reporting_source_extractor.extractor import check_case
        case = self._case()
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "reporting"
            shutil.copytree(Path(case["businessCheck"]["evidence"][0]["path"]).parent, work)
            (work / "TRANREPT").unlink()
            fake = json.loads(json.dumps(case))
            fake["businessCheck"]["evidence"][0]["path"] = str(work / "TRANREPT")
            result = check_case(fake)
        self.assertEqual("failed", result["caseVerdict"])
        self.assertIn("missing_report", result["reportClassification"]["failures"])

    def test_date_guard_uses_lexical_boundaries_from_actual_dateparm_not_calendar_strengthening(self):
        from reporting_source_extractor.extractor import selected_by_date_range
        self.assertTrue(selected_by_date_range("2022-07-01", "2022-07-01", "2022-07-31"))
        self.assertTrue(selected_by_date_range("2022-07-31", "2022-07-01", "2022-07-31"))
        self.assertFalse(selected_by_date_range("2022-06-99", "2022-07-01", "2022-07-31"))
        self.assertFalse(selected_by_date_range("2022-08-00", "2022-07-01", "2022-07-31"))
        self.assertTrue(selected_by_date_range("2022-07-AA", "2022-07-01", "2022-07-ZZ"))


if __name__ == "__main__":
    unittest.main()

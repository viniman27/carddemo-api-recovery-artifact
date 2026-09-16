import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = ROOT / "P3" / "complementary-matrix-analysis-v1"
REPORT = ROOT / "P3" / "complementary-matrix-v2" / "parent-full84-v1" / "campaign" / "campaign-report.json"
FREEZE = ROOT / "P3" / "complementary-matrix-v2" / "parent-plan-absolute-v1" / "suite.freeze.json"

sys.path.insert(0, str(PKG))


class MatrixAnalysisTests(unittest.TestCase):
    def test_campaign_check_adapts_to_qualified_extractor_case_without_rerun(self):
        from matrix_analysis import build_extractor_case
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        check = next(c for c in report["suiteReports"][0]["checks"] if c["track"] == "interest")
        case = build_extractor_case(check)
        self.assertEqual(check["case_id"], case["caseId"])
        self.assertEqual("interest", case["track"])
        evidence_path = Path(case["businessCheck"]["evidence"][0]["path"])
        self.assertTrue(evidence_path.is_file())
        self.assertEqual("TRANSACT", evidence_path.name)
        self.assertEqual(check["receipt"]["status"], case["httpStatus"])
        self.assertEqual(check["receipt"]["response_sha256"], case["responseSha256"])

    def test_all_84_are_classified_with_measurement_absence_not_default_failure(self):
        from matrix_analysis import run_analysis
        payload = run_analysis(REPORT, FREEZE, ROOT)
        self.assertEqual(84, payload["summary"]["caseCount"])
        self.assertEqual({"posting": 42, "interest": 14, "reporting": 28}, payload["summary"]["caseCountsByTrack"])
        self.assertEqual(6, payload["summary"]["measurementLimitedCount"])
        self.assertEqual(0, payload["summary"]["pinVerificationFailureCount"])
        self.assertTrue(payload["summary"]["noApiReruns"])
        self.assertEqual(84, len({c["caseId"] for c in payload["cases"]}))
        for case in payload["cases"]:
            self.assertIn(case["semanticVerdict"], {"pass", "failed", "inconclusive"})
            self.assertTrue(case["reason"])
            self.assertTrue(case["proof"])

    def test_cli_writes_json_csv_and_ptbr_report(self):
        with tempfile.TemporaryDirectory() as td:
            outdir = Path(td)
            completed = subprocess.run([
                sys.executable, "-m", "matrix_analysis",
                "--report", str(REPORT),
                "--freeze", str(FREEZE),
                "--cycle-root", str(ROOT),
                "--out-dir", str(outdir),
            ], cwd=PKG, text=True, capture_output=True, check=False)
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue((outdir / "actual84-semantic-analysis.json").is_file())
            self.assertTrue((outdir / "actual84-cases.csv").is_file())
            report = (outdir / "PTBR-ANALISE.md").read_text(encoding="utf-8")
            self.assertIn("84/84", report)
            self.assertIn("sem rerodagem de API", report)
            self.assertIn("defeitos legados", report.lower())


if __name__ == "__main__":
    unittest.main()

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = ROOT / "P3" / "complementary-interest-source-extractor-v1"
RUN = ROOT / "P3" / "complementary-crossarm-v1" / "run-20260916T112642Z"
sys.path.insert(0, str(PKG))


class InterestSourceExtractorTests(unittest.TestCase):
    def test_formula_matches_source_decimal_truncation_not_round_half_up(self):
        from interest_source_extractor.extractor import compute_monthly_interest_cents
        self.assertEqual("00000000000", compute_monthly_interest_cents(Decimal("0.01"), Decimal("6.00")))
        self.assertEqual("00000000006", compute_monthly_interest_cents(Decimal("12.99"), Decimal("6.00")))
        self.assertEqual("00000000500", compute_monthly_interest_cents(Decimal("500.00"), Decimal("12.00")))

    def test_semantic_bdb_dump_extracts_qualified_balance_and_rate_from_copies(self):
        from interest_source_extractor.extractor import extract_inputs_for_run_dir
        comparison = json.loads((RUN / "comparison.json").read_text())
        case = next(c for c in comparison["cases"] if c["caseId"] == "CROSSARM-E3-SDD-stage6r3-interest")
        original = Path(case["businessCheck"]["evidence"][0]["path"]).parent
        with tempfile.TemporaryDirectory() as td:
            copied = Path(td) / "run-copy"
            shutil.copytree(original, copied)
            extraction = extract_inputs_for_run_dir(copied, case_id=case["caseId"])
        self.assertEqual("read_only_dump_on_copy", extraction["method"])
        self.assertEqual(2, len(extraction["balances"]))
        self.assertEqual(3, len(extraction["rates"]))
        by_key = {tuple(x["key"][k] for k in ["accountId", "type", "category"]): x for x in extraction["balances"]}
        self.assertEqual("50.00", by_key[("10000000001", "01", "0005")]["balance"])
        rate_by_key = {(x["key"]["group"].rstrip(), x["key"]["type"], x["key"]["category"]): x for x in extraction["rates"]}
        self.assertEqual("1.50", rate_by_key[("STANDARD", "01", "0005")]["rate"])
        for field in extraction["balances"] + extraction["rates"]:
            prov = field["provenance"]
            self.assertIn("physicalFileSha256", prov)
            self.assertIn("dumpRecordOffset", prov)
            self.assertIn("logicalBytesHex", prov)

    def test_cli_checks_preserved_seven_interest_cases_without_api_reruns(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "results.json"
            completed = subprocess.run([
                sys.executable, "-m", "interest_source_extractor",
                "--run-root", str(RUN),
                "--cycle-root", str(ROOT),
                "--out", str(out),
            ], cwd=PKG, text=True, capture_output=True, check=False)
            self.assertEqual(0, completed.returncode, completed.stderr)
            payload = json.loads(out.read_text())
        self.assertTrue(payload["summary"]["noApiReruns"])
        self.assertEqual(7, payload["summary"]["caseCount"])
        self.assertEqual({"pass": 7}, payload["summary"]["semanticVerdictCounts"])
        self.assertEqual(0, payload["summary"]["pinVerificationFailureCount"])
        for case in payload["cases"]:
            self.assertEqual("pass", case["semanticVerdict"])
            self.assertEqual(["00000000006"], [t["observedAmountCentsText"] for t in case["transactions"]])
            self.assertEqual(["00000000006"], [t["expectedAmountCentsText"] for t in case["transactions"]])
            self.assertEqual("read_only_dump_on_copy", case["sourceInputs"]["method"])
            self.assertIn("apiVisibleEvidence", case)
            self.assertIn("byteProvenance", case)


if __name__ == "__main__":
    unittest.main()

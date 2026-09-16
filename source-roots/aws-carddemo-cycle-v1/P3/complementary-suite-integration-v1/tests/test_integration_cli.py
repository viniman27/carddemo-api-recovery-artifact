import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CYCLE = ROOT.parents[1]
CLI = ROOT / "complementary_suite_integration.py"


class ComplementarySuiteIntegrationTests(unittest.TestCase):
    def run_cli(self, *args):
        out = Path(tempfile.mkdtemp(prefix="complementary-suite-integration-test-")) / "out"
        cmd = [sys.executable, str(CLI), "assemble", "--cycle-root", str(CYCLE), "--output", str(out), *args]
        proc = subprocess.run(cmd, text=True, capture_output=True)
        self.assertEqual(0, proc.returncode, proc.stderr)
        return out, json.loads((out / "candidate-suite-plan.json").read_text()), json.loads((out / "coverage-gap-ledger.json").read_text())

    def test_assembles_all7_contracts_and_21_operations_from_freeze_without_reclassifying_t1_t2(self):
        out, plan, ledger = self.run_cli()
        self.assertEqual("complementary-suite-integration-v1", plan["kind"])
        self.assertEqual(7, plan["sourceFreeze"]["contractCount"])
        self.assertEqual(21, plan["sourceFreeze"]["operationCellCount"])
        self.assertEqual({"T1": 88, "T2": 5868, "T3": 394, "T4": 6350}, plan["sourceFreeze"]["conditionCounts"])
        self.assertTrue(plan["sourceFreeze"]["t1t2ExactCopies"])
        self.assertFalse(plan["officialExecutionStarted"])
        self.assertEqual([], [c for c in plan["candidateComplementCases"] if c["role"] in {"manualT1", "T1", "T2-fuzz", "repeatcampaign"}])
        self.assertEqual(12, len(plan["candidateComplementCases"]))
        self.assertEqual({"posting": 6, "interest": 2, "reporting": 4}, plan["candidateCountsByTrack"])
        self.assertEqual("source_guided_complementary_T3_checker_candidate", plan["roleSeparation"]["complementaryEssentialCases"])

    def test_bindings_are_explicit_and_interest_reporting_limit_claims_are_not_inflated(self):
        out, plan, ledger = self.run_cli()
        for case in plan["candidateComplementCases"]:
            self.assertIn(case["track"], {"posting", "interest", "reporting"})
            self.assertIn(case["operationId"], {"postDailyTransactions", "generateInterestTransactions", "generateTransactionReport"})
            self.assertTrue(case["sourceEvidence"], case)
            self.assertNotEqual("T1", case["condition"])
            self.assertEqual("candidate_not_official_campaign", case["officialCampaignStatus"])
            self.assertIn("modelMapping", case)
        obl007 = [x for x in ledger["obligations"] if x["obligationId"] == "INTCALC-OBL-007"]
        self.assertEqual(1, len(obl007))
        self.assertEqual("covered_partition_only", obl007[0]["aggregateClassification"])
        self.assertIn("zero-rate", obl007[0]["evidenceMeaning"])
        self.assertIn("not a count label for all interest behavior", obl007[0]["limits"])
        totals = [x for x in ledger["obligations"] if x["obligationId"] == "R-TOTALS-EOF-GUARD"]
        self.assertEqual("inconclusive-by-source", totals[0]["aggregateClassification"])
        self.assertIn("not a business pass for totals arithmetic", totals[0]["limits"])

    def test_writes_status_and_manifest_with_hashes(self):
        out, plan, ledger = self.run_cli()
        status = (out / "STATUS.md").read_text()
        manifest = json.loads((out / "MANIFEST.json").read_text())
        self.assertIn("Next gate", status)
        self.assertIn("No official AWS campaign execution is started", status)
        self.assertGreaterEqual(len(manifest["files"]), 4)
        for row in manifest["files"]:
            self.assertRegex(row["sha256"], r"^[0-9a-f]{64}$")
            self.assertGreater(row["bytes"], 0)


if __name__ == "__main__":
    unittest.main()

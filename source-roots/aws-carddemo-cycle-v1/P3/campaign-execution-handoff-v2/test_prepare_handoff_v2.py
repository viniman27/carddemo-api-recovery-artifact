import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "prepare_handoff_v2.py"
REPORT = ROOT / "REPORT.json"
READINESS = ROOT / "FINAL-READINESS.json"
P3 = ROOT.parent


class HandoffV2Tests(unittest.TestCase):
    def test_prepare_handoff_v2_uses_freeze_v3_config_v3_and_guard_clean_counts(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--output", str(P3 / "official-campaign-large12k-run-v2")],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["verdict"], "READY_PLAN_VERIFIED_NO_OFFICIAL_EXECUTION")
        report = json.loads(REPORT.read_text())
        readiness = json.loads(READINESS.read_text())
        self.assertTrue(readiness["officialReady"])
        self.assertFalse(readiness["officialExecutionStarted"])
        self.assertEqual(report["freezePackage"].split("/")[-1], "campaign-freeze-package-v3")
        self.assertEqual(report["config"].split("/")[-2:], ["campaign-configuration-v3", "campaign-config-v3.json"])
        self.assertEqual(report["suites"]["conditionCounts"], {"T1": 88, "T2": 5868, "T3": 394, "T4": 6350})
        self.assertEqual(report["suites"]["totalCases"], 12700)
        self.assertEqual(report["suites"]["order"], ["T1 all contracts", "T2 all contracts", "T3 all contracts", "T4 all contracts"])
        self.assertEqual(report["guards"]["t3GuardNotTrueRemaining"], [])
        self.assertEqual(report["guards"]["t4GuardNotTrueRemaining"], [])
        self.assertEqual(report["guards"]["excludedUnknownGuardCount"], 7)
        self.assertGreater(report["resourceEstimate"]["estimateBytes"]["recommendedFreeBytesBeforeStart"], 67_000_000)
        self.assertTrue(report["planVerification"]["ok"])
        self.assertFalse(report["planVerification"]["officialExecutionStarted"])
        self.assertIn("--mode", report["commands"]["executeParentTrackedOnlyAfterReadinessTrue"])

    def test_no_literal_t3_unknown_guard_search_as_acceptance(self):
        text = SCRIPT.read_text()
        self.assertNotIn("T3unknownguard", text)
        self.assertIn("guardResult", text)
        self.assertIn("is not True", text)


if __name__ == "__main__":
    unittest.main()

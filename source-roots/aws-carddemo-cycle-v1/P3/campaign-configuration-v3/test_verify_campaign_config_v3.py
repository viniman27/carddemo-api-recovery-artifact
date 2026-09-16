import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERIFY = ROOT / "verify_campaign_config_v3.py"
CONFIG = ROOT / "campaign-config-v3.json"


class CampaignConfigV3VerificationTests(unittest.TestCase):
    def test_current_v3_config_verifies_with_freeze_v3_and_updated_coverage_pin(self):
        result = subprocess.run(
            [sys.executable, str(VERIFY), str(CONFIG)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["ok"])
        self.assertEqual(report["contracts"], 7)
        self.assertEqual(report["operations"], 21)
        self.assertEqual(report["official_campaigns_started"], False)
        self.assertEqual(report["provider_calls_allowed_by_config"], False)
        self.assertEqual(report["freeze_package"], "campaign-freeze-package-v3")
        self.assertEqual(report["freeze_counts"], {"T1": 88, "T2": 5868, "T3": 394, "T4": 6350})
        self.assertEqual(report["source_mismatches"], 0)
        self.assertEqual(report["amendments"], 1)

    def test_tampered_updated_pin_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "campaign-config-v3.json"
            data = json.loads(CONFIG.read_text())
            for row in data["sources"]:
                if row["id"] == "coverage-runner-v3":
                    row["sha256"] = "0" * 64
                    break
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VERIFY), str(tmp)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sha256 mismatch coverage-runner-v3", result.stdout + result.stderr)

    def test_freeze_v2_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "campaign-config-v3.json"
            data = json.loads(CONFIG.read_text())
            data["freezePackage"]["path"] = str(ROOT.parent / "campaign-freeze-package-v2")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VERIFY), str(tmp)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("freeze package must be v3", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

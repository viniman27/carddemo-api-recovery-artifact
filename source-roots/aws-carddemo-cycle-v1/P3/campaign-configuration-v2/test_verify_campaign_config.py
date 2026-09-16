import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERIFY = ROOT / "verify_campaign_config.py"
CONFIG = ROOT / "campaign-config-v2.json"


class CampaignConfigVerificationTests(unittest.TestCase):
    def test_current_config_verifies_real_current_pins_and_scope(self):
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
        self.assertEqual(report["t1_payloads"], 7)

    def test_tampered_pin_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "campaign-config-v2.json"
            data = json.loads(CONFIG.read_text())
            data["sources"][0]["sha256"] = "0" * 64
            tmp.write_text(json.dumps(data, indent=2) + "\n")
            result = subprocess.run(
                [sys.executable, str(VERIFY), str(tmp)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sha256 mismatch", result.stdout + result.stderr)

    def test_label_only_authorization_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "campaign-config-v2.json"
            data = json.loads(CONFIG.read_text())
            data["authorization"]["campaignAuthorized"] = "prepared-local-blocked"
            tmp.write_text(json.dumps(data, indent=2) + "\n")
            result = subprocess.run(
                [sys.executable, str(VERIFY), str(tmp)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("campaignAuthorized must be boolean false", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

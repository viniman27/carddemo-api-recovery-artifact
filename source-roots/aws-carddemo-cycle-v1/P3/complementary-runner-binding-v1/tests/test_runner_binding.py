import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BINDING = ROOT / "P3" / "complementary-runner-binding-v1"
CHECKERS = ROOT / "P3" / "complementary-validation-implementation-v3"

sys.path.insert(0, str(BINDING))

from runner_binding.binding import build_fixture_for_case, sha256_file, verify_pins


class RunnerBindingTests(unittest.TestCase):
    def test_builds_real_fixture_from_posting_receipt_and_hash_pins(self):
        fixture, meta = build_fixture_for_case(ROOT, "valid-new-tcatbal")
        self.assertEqual("real_cobol_observation", fixture["evidenceClass"])
        tx = fixture["observations"]["posting"]["acceptedTransactions"][0]
        self.assertEqual(350, len(bytes.fromhex(tx["rawBytes"])))
        self.assertEqual(tx["posted"]["id"], tx["daily"]["id"])
        self.assertNotEqual(tx["posted"]["procTs"], tx["daily"]["procTs"])
        self.assertEqual([], verify_pins(meta["artifactPins"]))

    def test_binding_runs_real_receipts_through_existing_semantic_checkers(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "result.json"
            completed = subprocess.run(
                [sys.executable, "-m", "runner_binding", "run", "--cycle-root", str(ROOT), "--out", str(out)],
                cwd=BINDING,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            payload = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(12, payload["summary"]["caseCount"])
        self.assertEqual({"posting": 6, "interest": 2, "reporting": 4}, payload["summary"]["caseCountsByTrack"])
        self.assertTrue(payload["summary"]["noApiReruns"])
        self.assertIn("shared_source_guided_qualification", payload["summary"]["modelBindingClassifications"])
        valid = next(c for c in payload["cases"] if c["caseId"] == "valid-new-tcatbal")
        statuses = {r["obligationId"]: r["status"] for r in valid["checkerResults"]}
        self.assertEqual("pass", statuses["POSTTRAN-OBL-003"])
        self.assertEqual("inconclusive", statuses["POSTTRAN-OBL-009"])
        card = next(c for c in payload["cases"] if c["caseId"] == "reject-card-missing")
        self.assertEqual("pass", {r["obligationId"]: r["status"] for r in card["checkerResults"]}["POSTTRAN-OBL-004"])

    def test_tampered_preserved_artifact_pin_is_detected_without_modifying_original(self):
        fixture, meta = build_fixture_for_case(ROOT, "rates-specific-default-zero")
        original_pin = next(pin for pin in meta["artifactPins"] if pin["label"] == "result.json")
        with tempfile.TemporaryDirectory() as td:
            tampered = Path(td) / "result.json"
            source = ROOT / original_pin["path"]
            shutil.copy2(source, tampered)
            tampered.write_text(tampered.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            bad_pin = dict(original_pin)
            bad_pin["absolutePath"] = str(tampered)
            failures = verify_pins([bad_pin])
        self.assertTrue(any("sha mismatch" in failure for failure in failures), failures)
        self.assertEqual(original_pin["sha256"], sha256_file(source))


if __name__ == "__main__":
    unittest.main()

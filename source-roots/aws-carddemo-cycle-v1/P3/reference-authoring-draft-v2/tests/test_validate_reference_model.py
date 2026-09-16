import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReferenceModelValidationTests(unittest.TestCase):
    def run_validator(self):
        return subprocess.run(
            [sys.executable, str(ROOT / "validate_reference_model.py"), str(ROOT)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_validator_accepts_complete_v2_model(self):
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["counts"]["capabilities"], 3)
        self.assertEqual(report["counts"]["blocking_findings_resolved"], 6)
        self.assertGreaterEqual(report["counts"]["states"], 20)
        self.assertGreaterEqual(report["counts"]["transitions"], 30)

    def test_model_has_no_free_text_transition_strings(self):
        data = json.loads((ROOT / "model.json").read_text())
        for capability in data["capabilities"]:
            for transition in capability["transitions"]:
                self.assertIn("id", transition)
                self.assertIsInstance(transition["from"], str)
                self.assertIsInstance(transition["to"], str)
                self.assertIsInstance(transition["guard"], dict)
                self.assertIsInstance(transition["effects"], list)
                self.assertIsInstance(transition["sourceAnchors"], list)
                self.assertIsInstance(transition["obligationRefs"], list)

    def test_resolution_matrix_covers_fail_01_to_06(self):
        matrix = json.loads((ROOT / "resolution-matrix.json").read_text())
        ids = [row["id"] for row in matrix["findings"]]
        self.assertEqual(ids, [f"FAIL-{i:02d}" for i in range(1, 7)])
        self.assertTrue(all(row["decision"] == "resolved_in_v2_draft" for row in matrix["findings"]))
        self.assertTrue(all(row["sourceAnchors"] for row in matrix["findings"]))


if __name__ == "__main__":
    unittest.main()

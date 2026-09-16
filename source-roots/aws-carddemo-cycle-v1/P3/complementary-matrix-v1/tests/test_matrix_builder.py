from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MatrixBuilderTests(unittest.TestCase):
    def test_build_plan_creates_84_candidate_applications_and_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out"
            proc = subprocess.run(
                [sys.executable, str(ROOT / "matrix_cli.py"), "--plan", "--output", str(out)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=120,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            plan = json.loads((out / "execution-plan.json").read_text())
            self.assertEqual(plan["totals"]["candidateApplications"], 84)
            self.assertEqual(plan["totals"]["essentialScenarios"], 12)
            self.assertEqual(plan["totals"]["contracts"], 7)
            self.assertGreater(plan["totals"]["nonexpressibleBlocks"], 0)
            suite = json.loads(Path(plan["suitePath"]).read_text())
            self.assertEqual(len(suite["cases"]), 84)
            self.assertEqual(len({c["parameters"]["sourceCaseId"] for c in suite["cases"]}), 12)

    def test_distinct_fixtures_have_distinct_request_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out"
            subprocess.check_call([sys.executable, str(ROOT / "matrix_cli.py"), "--plan", "--output", str(out)], cwd=ROOT)
            plan = json.loads((out / "execution-plan.json").read_text())
            suite = json.loads(Path(plan["suitePath"]).read_text())
            e1_posting = [c for c in suite["cases"] if c["parameters"]["contractId"] == "E1-1" and c["parameters"]["track"] == "posting"]
            self.assertEqual(len(e1_posting), 6)
            self.assertGreaterEqual(len({c["request"]["body_b64"] for c in e1_posting}), 2)

    def test_plan_verification_cli_rejects_mutated_suite(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out"
            subprocess.check_call([sys.executable, str(ROOT / "matrix_cli.py"), "--plan", "--output", str(out)], cwd=ROOT)
            plan_path = out / "execution-plan.json"
            plan = json.loads(plan_path.read_text())
            suite_path = Path(plan["suitePath"])
            suite = json.loads(suite_path.read_text())
            suite["cases"].pop()
            suite_path.write_text(json.dumps(suite, indent=2, sort_keys=True), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(ROOT / "matrix_cli.py"), "--verify-plan", str(plan_path)], cwd=ROOT, text=True, capture_output=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("candidate_application_count", proc.stderr)


if __name__ == "__main__":
    unittest.main()

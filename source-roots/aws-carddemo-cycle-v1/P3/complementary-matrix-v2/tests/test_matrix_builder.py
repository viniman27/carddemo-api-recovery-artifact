from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def body(case: dict) -> dict:
    return json.loads(base64.b64decode(case["request"]["body_b64"]).decode("utf-8"))


class MatrixV2BuilderTests(unittest.TestCase):
    def _plan(self, td: str):
        out = Path(td) / "out"
        proc = subprocess.run(
            [sys.executable, str(ROOT / "matrix_cli.py"), "--plan", "--output", str(out)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=180,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        plan = json.loads((out / "execution-plan.json").read_text())
        suite = json.loads(Path(plan["suitePath"]).read_text())
        return out, plan, suite

    def test_build_plan_materializes_84_with_no_invented_request_fields_and_sdd_empty_body(self):
        with tempfile.TemporaryDirectory() as td:
            _out, plan, suite = self._plan(td)
            self.assertEqual(plan["totals"], {"contracts": 7, "essentialScenarios": 12, "candidateApplications": 84})
            self.assertEqual(len(suite["cases"]), 84)
            forbidden = "complementaryFixtureSelection"
            for case in suite["cases"]:
                b = body(case)
                self.assertNotIn(forbidden, b)
                if case["parameters"]["contractArm"].lower() == "sdd":
                    self.assertEqual(b, {})
                self.assertIn("runtimeFixtureRegistry", case["parameters"])
                self.assertTrue(Path(case["parameters"]["runtimeFixtureRegistry"]).is_file())

    def test_e1_e2_posting_requests_use_actual_scenario_bytes_and_change_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            _out, _plan, suite = self._plan(td)
            selected = [c for c in suite["cases"] if c["parameters"]["contractId"] in {"E1-1", "E2-2"} and c["parameters"]["track"] == "posting" and c["parameters"]["sourceCaseId"] in {"valid-new-tcatbal", "reject-card-missing"}]
            self.assertEqual(len(selected), 4)
            by_contract = {}
            for c in selected:
                by_contract.setdefault(c["parameters"]["contractId"], {})[c["parameters"]["sourceCaseId"]] = c
                self.assertEqual(c["parameters"]["requestInputAuthority"], "materialized_from_physical_fixture_bytes")
                self.assertEqual(len(c["parameters"]["wireInputPins"]), 1)
                self.assertEqual(c["parameters"]["wireInputPins"][0]["dd"], "DALYTRAN")
                self.assertEqual(c["parameters"]["wireInputPins"][0]["bytes"], 350)
            for cid, cases in by_contract.items():
                self.assertNotEqual(cases["valid-new-tcatbal"]["parameters"]["effectiveInputSha256"], cases["reject-card-missing"]["parameters"]["effectiveInputSha256"])
                self.assertNotEqual(cases["valid-new-tcatbal"]["request"]["body_b64"], cases["reject-card-missing"]["request"]["body_b64"])

    def test_verify_plan_rejects_missing_physical_registry_file(self):
        with tempfile.TemporaryDirectory() as td:
            _out, plan, suite = self._plan(td)
            plan_path = Path(plan["planPath"])
            first_registry = Path(suite["cases"][0]["parameters"]["runtimeFixtureRegistry"])
            first_registry.unlink()
            proc = subprocess.run([sys.executable, str(ROOT / "matrix_cli.py"), "--verify-plan", str(plan_path)], cwd=ROOT, text=True, capture_output=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("runtime_fixture_registry_missing", proc.stderr)


if __name__ == "__main__":
    unittest.main()

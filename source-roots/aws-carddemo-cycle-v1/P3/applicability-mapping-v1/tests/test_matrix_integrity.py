import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CYCLE = ROOT.parents[1]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class MatrixIntegrityTests(unittest.TestCase):
    def test_matrix_covers_reference_inventory_and_uses_programmatic_denominators(self):
        matrix = load_json(ROOT / "applicability_matrix.json")
        reference = load_json(CYCLE / "P3" / "reference-executable-v4" / "model.json")
        obligation_ids = {o["id"] for o in reference["obligations"]}
        self.assertEqual(len(obligation_ids), 25)
        self.assertEqual({o["obligationId"] for o in matrix["obligations"]}, obligation_ids)
        self.assertEqual(matrix["denominators"]["obligations"], 25)
        self.assertEqual(matrix["denominators"]["contracts"], 7)
        self.assertEqual(matrix["denominators"]["operations"], 21)
        self.assertEqual(matrix["denominators"]["obligation_contract_cells"], 175)
        self.assertEqual(matrix["denominators"]["calculation"], "programmatic")

    def test_all_operation_references_exist_and_status_does_not_authorize_campaign(self):
        matrix = load_json(ROOT / "applicability_matrix.json")
        inventory = load_json(CYCLE / "P3" / "suite-adapters-preflight-v1" / "evidence-real-preflight-20260915T-synthetic" / "operation-inventory.json")
        ops = {(op["contractId"], op["method"].lower(), op["path"], op["operationId"]) for op in inventory["operations"]}
        self.assertEqual(matrix["status"], "candidate_needs_review")
        self.assertIs(matrix["campaign_authorization"], False)
        for obligation in matrix["obligations"]:
            self.assertEqual(len(obligation["contractMappings"]), 7)
            for mapping in obligation["contractMappings"]:
                op = mapping["operation"]
                self.assertIn((mapping["contractId"], op["method"].lower(), op["path"], op["operationId"]), ops)

    def test_sdd_requests_remain_empty_and_no_selectors_are_introduced(self):
        matrix = load_json(ROOT / "applicability_matrix.json")
        sdd = [m for o in matrix["obligations"] for m in o["contractMappings"] if m["contractId"] == "E3-01-SDD-stage6r3"]
        self.assertTrue(sdd)
        for mapping in sdd:
            schema = mapping["operation"]["requestSchema"]
            self.assertEqual(schema["properties"], [])
            self.assertIs(schema["additionalProperties"], False)
            self.assertEqual(mapping["t3DeterministicMapping"]["requestBody"], {})
            self.assertIs(mapping["t3DeterministicMapping"]["newSelectorsIntroduced"], False)
            self.assertEqual(mapping["t3DeterministicMapping"]["fieldSelectors"], [])

    def test_status_taxonomy_and_fixture_references_are_controlled(self):
        matrix = load_json(ROOT / "applicability_matrix.json")
        allowed = set(matrix["status_taxonomy"].keys())
        fixtures = {f["fixtureId"] for f in matrix["fixtures"]}
        seen = set()
        for obligation in matrix["obligations"]:
            for mapping in obligation["contractMappings"]:
                seen.add(mapping["applicabilityStatus"])
                self.assertIn(mapping["applicabilityStatus"], allowed)
                for fx in mapping["candidateFixtures"]:
                    self.assertIn(fx["fixtureId"], fixtures)
        required = {"expressible_by_surface", "conditioned_on_external_fixture", "not_expressible", "not_mapped", "precondition_indeterminate", "observation_inadmissible"}
        self.assertTrue(required.issubset(seen), seen)

    def test_validator_cli_passes(self):
        result = subprocess.run([sys.executable, str(ROOT / "tools" / "validate_matrix.py")], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()

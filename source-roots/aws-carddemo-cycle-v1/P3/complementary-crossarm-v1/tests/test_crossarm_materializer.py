import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "complementary-crossarm-v1"
sys.path.insert(0, str(PKG))
sys.path.insert(0, str(ROOT / "campaign-harness-v3" / "src"))

from campaign_harness import load_frozen_suite
from crossarm.materializer import build_crossarm_suite, freeze_inputs, pin_file


class CrossarmMaterializerTests(unittest.TestCase):
    def test_freeze_inputs_pins_contracts_registry_runner_checker_and_t3_closure(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            frozen = freeze_inputs(ROOT.parent, out)
        self.assertEqual(frozen["contractCount"], 7)
        self.assertEqual(frozen["operationCount"], 21)
        labels = {p["label"] for p in frozen["pins"]}
        self.assertIn("campaign-config-v2", labels)
        self.assertIn("t3-binding-closure-amended-candidates", labels)
        self.assertIn("complementary-mbt-binding-registry", labels)
        self.assertIn("runner-v3", labels)
        self.assertIn("checker-v3", labels)

    def test_materializes_21_crossarm_cases_one_positive_track_per_contract_with_explicit_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            suite_path, manifest = build_crossarm_suite(ROOT.parent, Path(td))
            suite = load_frozen_suite(suite_path)
        self.assertEqual(21, len(suite.cases))
        cells = {(c.parameters["contractId"], c.parameters["track"]) for c in suite.cases}
        self.assertEqual(21, len(cells))
        self.assertEqual({"posting", "interest", "reporting"}, {c.parameters["track"] for c in suite.cases})
        self.assertEqual(7, len({c.parameters["contractId"] for c in suite.cases}))
        self.assertEqual(len(suite.cases), len({c.case_id for c in suite.cases}))
        for case in suite.cases:
            self.assertEqual(case.parameters["officialCampaign"], False)
            self.assertEqual(case.parameters["sourceGuidedComplement"], True)
            self.assertIn("sourceCaseId", case.parameters)
            self.assertIn("fixtureId", case.parameters)
            self.assertIn(case.parameters["track"], case.resource_package_id)
            body = json.loads(base64.b64decode(case.request.body_b64 or "e30="))
            if case.parameters["contractId"] == "E3-SDD-stage6r3":
                self.assertEqual({}, body)
            else:
                self.assertNotEqual({}, body)
        self.assertEqual(21, manifest["summary"]["caseCount"])

    def test_no_alias_routing_mix_contract_path_matches_operation_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            suite_path, _manifest = build_crossarm_suite(ROOT.parent, Path(td))
            suite = load_frozen_suite(suite_path)
        for case in suite.cases:
            self.assertEqual(case.request.path, case.parameters["contractPath"])
            self.assertEqual(case.parameters["operationId"], case.parameters["contractOperationId"])

    def test_pin_file_detects_hashes_and_sizes(self):
        pin = pin_file(ROOT.parent / "P3/campaign-configuration-v2/campaign-config-v2.json", ROOT.parent, "x")
        self.assertEqual("x", pin["label"])
        self.assertGreater(pin["bytes"], 1000)
        self.assertEqual(64, len(pin["sha256"]))


if __name__ == "__main__":
    unittest.main()

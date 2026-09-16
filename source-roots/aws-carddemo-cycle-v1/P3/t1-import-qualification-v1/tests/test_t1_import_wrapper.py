from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CYCLE = ROOT.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(CYCLE / "P3" / "campaign-harness-v3" / "src"))
sys.path.insert(0, str(CYCLE / "P3" / "unified-preflight-v3" / "src"))

from t1_import_qualification import load_t1_payload, normalize_scenario_to_import_item, build_contract_schema_index
from campaign_harness import Suite, load_frozen_suite


class T1ImportWrapperTests(unittest.TestCase):
    def test_normalizes_nested_t1_scenario_without_losing_absent_vs_empty_body(self):
        payload = load_t1_payload(CYCLE / "P3" / "t1-generation-03" / "parsed" / "E2-2.parsed.json")
        scenario = payload["scenarios"][0]
        item = normalize_scenario_to_import_item("E2-2", scenario)
        self.assertEqual(item["method"], scenario["operation"]["method"])
        self.assertEqual(item["path"], scenario["operation"]["path"])
        self.assertIn(item["body"]["kind"], {"json", "absent", "bytes"})
        if item["body"]["kind"] == "json":
            self.assertIn("value", item["body"])
        self.assertEqual(item["parameters"]["originalScenarioId"], scenario["id"])

    def test_schema_index_uses_original_contract_text_by_contract_id(self):
        index = build_contract_schema_index(CYCLE)
        self.assertEqual(set(index), {"E1-1", "E1-2", "E1-3", "E2-1", "E2-2", "E2-3", "E3-SDD-stage6r3"})
        self.assertTrue(index["E1-1"].source_path.as_posix().endswith("collection-01/E1-1/parsed.json"))
        self.assertTrue(index["E3-SDD-stage6r3"].source_path.as_posix().endswith("P2a/openapi-carddemo-stage6r3.yaml"))

    def test_generated_candidate_freezes_are_harness_loadable(self):
        from t1_import_qualification import run_import_qualification
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            report = run_import_qualification(CYCLE, tmp_path)
            self.assertEqual(report["counts"]["source_scenario_occurrences"], 88)
            self.assertEqual(report["counts"]["contract_count"], 7)
            self.assertEqual(report["counts"]["harness_freeze_loadable_suites"], 7)
            self.assertFalse(report["counts"]["campaign_started"])
            for suite_row in report["suites"]:
                loaded = load_frozen_suite(Path(suite_row["freezePath"]))
                self.assertIsInstance(loaded, Suite)
                self.assertEqual(len(loaded.cases), suite_row["acceptedCount"])
            ledger = json.loads((tmp_path / "admissibility-ledger.json").read_text())
            self.assertEqual(len(ledger["cases"]), 88)
            self.assertTrue(any(c["schemaAdmissibility"] in {"schema_valid", "schema_invalid"} for c in ledger["cases"]))


if __name__ == "__main__":
    unittest.main()

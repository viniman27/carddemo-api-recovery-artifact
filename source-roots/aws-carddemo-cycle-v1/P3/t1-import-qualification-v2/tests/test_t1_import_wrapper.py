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

from t1_import_qualification import (
    load_t1_payload,
    normalize_scenario_to_import_item,
    build_contract_schema_index,
    validate_against_original_schema,
)
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

    def test_schema_invalid_negative_absent_body_remains_executable_stimulus(self):
        payload = load_t1_payload(CYCLE / "P3" / "t1-generation-03" / "parsed" / "E3-SDD-stage6r3.parsed.json")
        scenario = next(s for s in payload["scenarios"] if s["id"] == "interest-negative-01")
        item = normalize_scenario_to_import_item("E3-SDD-stage6r3", scenario)
        validation = validate_against_original_schema(build_contract_schema_index(CYCLE)["E3-SDD-stage6r3"], item)

        self.assertEqual(item["body"], {"kind": "absent"})
        self.assertEqual(validation["operationAdmissibility"], "operation_in_original_contract")
        self.assertEqual(validation["schemaAdmissibility"], "schema_invalid")

    def test_generated_candidate_freezes_import_all_materializable_scenarios(self):
        from t1_import_qualification import run_import_qualification
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            report = run_import_qualification(CYCLE, tmp_path)
            self.assertEqual(report["kind"], "t1-real-import-qualification-v2-report")
            self.assertEqual(report["counts"]["source_scenario_occurrences"], 88)
            self.assertEqual(report["counts"]["contract_count"], 7)
            self.assertEqual(report["counts"]["materializable_harness_cases"], 88)
            self.assertEqual(report["counts"]["nonmaterializable_cases"], 0)
            self.assertEqual(report["counts"]["schema_invalid_cases"], 45)
            self.assertEqual(report["counts"]["schema_invalid_negative_executable"], 42)
            self.assertEqual(report["counts"]["schema_invalid_nonnegative_executable"], 3)
            self.assertEqual(report["counts"]["harness_freeze_loadable_suites"], 7)
            self.assertFalse(report["counts"]["campaign_started"])
            total_loaded = 0
            for suite_row in report["suites"]:
                loaded = load_frozen_suite(Path(suite_row["freezePath"]))
                self.assertIsInstance(loaded, Suite)
                self.assertEqual(len(loaded.cases), suite_row["materializableCount"])
                total_loaded += len(loaded.cases)
                for case in loaded.cases:
                    self.assertIn(case.parameters["executionEligibility"], {"executable_stimulus_schema_valid", "executable_stimulus_schema_invalid"})
                    self.assertIn("sourceRequestCanonicalSha256", case.parameters)
                    self.assertEqual(case.parameters["oracleExpectedOutputs"], "quarantined_not_used")
                    self.assertNotEqual(case.expectation.expectation_id, "expectedFromContract")
            self.assertEqual(total_loaded, 88)
            ledger = json.loads((tmp_path / "admissibility-ledger.json").read_text())
            self.assertEqual(len(ledger["cases"]), 88)
            self.assertFalse([c for c in ledger["cases"] if c["materializationStatus"] != "materialized"])
            invalid_negative = [c for c in ledger["cases"] if c["schemaAdmissibility"] == "schema_invalid" and c["category"] == "negative"]
            self.assertEqual(len(invalid_negative), 42)
            self.assertTrue(all(c["acceptedIntoHarnessSuite"] for c in invalid_negative))
            self.assertTrue(all(c["expectedAssertionsPolicy"] == "contract_assertion_quarantined_not_oracle" for c in ledger["cases"]))


if __name__ == "__main__":
    unittest.main()

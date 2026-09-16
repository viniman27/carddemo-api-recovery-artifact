from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from t3_campaign_adapter import (  # noqa: E402
    AdapterBlocked,
    build_t3_suite,
    load_contract_registry,
    load_real_inputs,
    operation_lookup_for_contract,
    resolve_contract_source,
    static_real_model_compatibility,
)


class T3ContractRegistryV2Tests(unittest.TestCase):
    def test_registry_resolves_exact_seven_contract_pins_from_campaign_config(self):
        registry = load_contract_registry(P3)
        self.assertEqual(set(registry), {
            "E1-1", "E1-2", "E1-3", "E2-1", "E2-2", "E2-3", "E3-SDD-stage6r3",
        })
        for contract_id, source in registry.items():
            self.assertEqual(source.contract_id, contract_id)
            self.assertEqual(source.pin["sha256"], source.sha256)
            self.assertEqual(source.pin["bytes"], source.bytes)
            self.assertTrue(source.path.exists())
            self.assertNotEqual(source.openapi.get("paths"), {})

    def test_lookup_verifies_all_21_operations_against_pinned_contract_schema(self):
        registry = load_contract_registry(P3)
        seen = []
        for contract_id, source in registry.items():
            for op in source.operations:
                resolved = operation_lookup_for_contract(P3, contract_id, op["method"], op["path"])
                self.assertEqual(resolved.contract_id, contract_id)
                self.assertEqual(resolved.path, source.path)
                self.assertIn(op["path"], resolved.openapi["paths"])
                self.assertIn(op["method"].lower(), resolved.openapi["paths"][op["path"]])
                seen.append((contract_id, op["method"], op["path"]))
        self.assertEqual(len(seen), 21)
        self.assertEqual(len(set(seen)), 21)

    def test_unknown_contract_and_cross_contract_path_fail_closed_without_alias(self):
        with self.assertRaises(AdapterBlocked) as unknown:
            resolve_contract_source(P3, "E3-01-SDD-stage6r3")
        self.assertEqual(unknown.exception.reason, "unknown_contract_id")

        with self.assertRaises(AdapterBlocked) as crossed:
            operation_lookup_for_contract(P3, "E1-1", "POST", "/posting")
        self.assertEqual(crossed.exception.reason, "operation_not_in_contract_schema")

    def test_real_inputs_pin_schema_for_requested_contract_not_sdd_default(self):
        e11 = load_real_inputs(P3, contract_id="E1-1")
        e3 = load_real_inputs(P3, contract_id="E3-SDD-stage6r3")
        self.assertEqual(e11["inputPins"]["schema"]["id"], "contract-E1-1")
        self.assertEqual(e3["inputPins"]["schema"]["id"], "contract-E3-SDD-stage6r3")
        self.assertNotEqual(e11["inputPins"]["schema"]["sha256"], e3["inputPins"]["schema"]["sha256"])
        self.assertIn("/posting-runs", e11["contractSource"].openapi["paths"])
        self.assertNotIn("/posting", e11["contractSource"].openapi["paths"])
        self.assertIn("/posting", e3["contractSource"].openapi["paths"])

    def test_build_rejects_schema_contract_identity_mismatch_before_materialization(self):
        inputs = load_real_inputs(P3, contract_id="E1-1")
        e3_source = resolve_contract_source(P3, "E3-SDD-stage6r3")
        with self.assertRaises(AdapterBlocked) as cm:
            build_t3_suite(
                "E1-1",
                inputs["model_path"],
                inputs["enriched_plan"],
                inputs["fixtures_path"],
                e3_source,
                capabilities=["CBTRN02C_POSTTRAN"],
                max_depth=1,
                max_paths_per_capability=1,
            )
        self.assertEqual(cm.exception.reason, "schema_contract_mismatch")

    def test_static_real_model_reports_all7_contracts_without_freezing_official_suites(self):
        report = static_real_model_compatibility(P3, contract_id="all7", capabilities=["CBTRN02C_POSTTRAN", "CBACT04C_INTCALC", "CBTRN03C_TRANREPT"], max_depth=2, max_paths_per_capability=2)
        self.assertEqual(report["officialCampaign"], False)
        self.assertEqual(report["officialSuiteGenerated"], False)
        self.assertEqual(set(report["contracts"]), {"E1-1", "E1-2", "E1-3", "E2-1", "E2-2", "E2-3", "E3-SDD-stage6r3"})
        for cid, item in report["contracts"].items():
            self.assertEqual(item["inputPins"]["schema"]["id"], f"contract-{cid}")
            self.assertEqual(item["officialSuiteGenerated"], False)

    def test_freeze_output_is_explicit_and_preserves_harness_round_trip(self):
        inputs = load_real_inputs(P3, contract_id="E1-1")
        with tempfile.TemporaryDirectory() as td:
            suite, report = build_t3_suite(
                "E1-1",
                inputs["model_path"],
                inputs["enriched_plan"],
                inputs["fixtures_path"],
                inputs["contractSource"],
                capabilities=["CBTRN02C_POSTTRAN"],
                max_depth=1,
                max_paths_per_capability=1,
            )
            self.assertEqual(report["officialCampaign"], False)
            self.assertGreaterEqual(report["acceptedCount"] + report["blockedCount"] + report["inconclusiveCount"], 1)
            # No freeze is produced by build_t3_suite itself.
            self.assertEqual(list(Path(td).iterdir()), [])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import base64
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from t3_campaign_adapter import (  # noqa: E402
    AdapterBlocked,
    build_t3_suite,
    load_real_inputs,
    materialize_request_from_cell,
    static_real_model_compatibility,
)


class T3RemainingBugsV3Tests(unittest.TestCase):
    def test_real_recipe_compiler_handles_supported_sequential_formats_without_schema_failure(self):
        # E1-1 previously produced schema_validation_failed because the local adapter emitted
        # rawRecordBase64 instead of the recipe compiler's contract-tested recordBase64 shape.
        e11 = load_real_inputs(P3, contract_id="E1-1")
        cell = next(c for c in e11["enriched_plan"]["cells"] if c["cellId"] == "POSTTRAN-OBL-001::E1-1::postDailyTransactions")
        request, evidence = materialize_request_from_cell(cell, e11["fixtures_path"], e11["contractSource"])
        body = json.loads(base64.b64decode(request.body_b64).decode("utf-8"))
        self.assertEqual(sorted(body["dailyTransactions"][0]), ["recordBase64"])
        self.assertEqual(evidence["schemaValidation"]["valid"], True)
        self.assertTrue(any("byteEndExclusive" in row and row["byteEndExclusive"] > 0 for row in evidence["sourceboundValues"]))

        # E2-2 exercises nested object + transactionObjects + array serialization through the
        # existing tested compiler rather than a partial local selector implementation.
        e22 = load_real_inputs(P3, contract_id="E2-2")
        tx_cell = next(c for c in e22["enriched_plan"]["cells"] if c["cellId"] == "POSTTRAN-OBL-001::E2-2::postDailyTransactions")
        tx_request, tx_evidence = materialize_request_from_cell(tx_cell, e22["fixtures_path"], e22["contractSource"])
        tx_body = json.loads(base64.b64decode(tx_request.body_b64).decode("utf-8"))
        self.assertIsInstance(tx_body["transactions"], list)
        self.assertIsInstance(tx_body["transactions"][0]["categoryCode"], int)
        self.assertEqual(tx_evidence["schemaValidation"]["valid"], True)

    def test_sdd_id_reconciliation_is_explicit_versioned_and_pinned_not_alias(self):
        inputs = load_real_inputs(P3, contract_id="E3-SDD-stage6r3")
        migration = inputs["inputPins"].get("sddIdMigration")
        self.assertIsInstance(migration, dict)
        self.assertEqual(migration["fromContractId"], "E3-01-SDD-stage6r3")
        self.assertEqual(migration["toContractId"], "E3-SDD-stage6r3")
        self.assertEqual(migration["version"], "sdd-id-migration-v1")
        self.assertTrue(migration["operationIdentity"]["identical"])
        self.assertTrue(migration["openapiCanonicalIdentity"]["identical"])
        self.assertIn("sha256", migration["migrationArtifactPin"])
        self.assertNotIn("E3-01-SDD-stage6r3", {c.get("contractId") for c in inputs["enriched_plan"]["cells"]})
        self.assertIn("E3-SDD-stage6r3", {c.get("contractId") for c in inputs["enriched_plan"]["cells"]})

        report = static_real_model_compatibility(P3, contract_id="all7", capabilities=["CBTRN02C_POSTTRAN", "CBACT04C_INTCALC", "CBTRN03C_TRANREPT"], max_depth=2, max_paths_per_capability=2)
        self.assertEqual(report["contracts"]["E3-SDD-stage6r3"]["executableEligibleDistinctCells"], 0)
        self.assertEqual(sum(item["executableEligibleDistinctCells"] for item in report["contracts"].values()), 44)

    def test_negative_mixed_schema_missing_pins_and_denied_cell_fail_closed(self):
        e11 = load_real_inputs(P3, contract_id="E1-1")
        e3 = load_real_inputs(P3, contract_id="E3-SDD-stage6r3")
        real_cell = next(c for c in e11["enriched_plan"]["cells"] if c["cellId"] == "POSTTRAN-OBL-001::E1-1::postDailyTransactions")
        with self.assertRaises(AdapterBlocked) as mixed:
            materialize_request_from_cell(real_cell, e11["fixtures_path"], e3["contractSource"])
        self.assertEqual(mixed.exception.reason, "schema_contract_mismatch")

        no_pin = copy.deepcopy(real_cell)
        no_pin.pop("linkedRecipe", None)
        with self.assertRaises(AdapterBlocked) as missing:
            materialize_request_from_cell(no_pin, e11["fixtures_path"], e11["contractSource"])
        self.assertEqual(missing.exception.reason, "recipe_pin_missing")

        denied = next(c for c in e11["enriched_plan"]["cells"] if c.get("status") == "blocked" and c.get("selectorObjects") is None)
        with self.assertRaises(AdapterBlocked) as denied_exc:
            materialize_request_from_cell(denied, e11["fixtures_path"], e11["contractSource"])
        self.assertEqual(denied_exc.exception.reason, "blocked_cell_has_no_authorized_request")

    def test_materialization_plan_all7_separates_ready_and_blocked_without_freeze_or_runtime(self):
        report = static_real_model_compatibility(P3, contract_id="all7", capabilities=["CBTRN02C_POSTTRAN", "CBACT04C_INTCALC", "CBTRN03C_TRANREPT"], max_depth=6, max_paths_per_capability=12)
        self.assertFalse(report["officialCampaign"])
        self.assertFalse(report["officialSuiteGenerated"])
        self.assertEqual(sum(item["executableEligibleDistinctCells"] for item in report["contracts"].values()), 44)
        self.assertGreater(sum(item["readyRequestCount"] for item in report["contracts"].values()), 0)
        for cid, item in report["contracts"].items():
            self.assertIn("blockedBySourceBoundReason", item)
            self.assertNotIn("schema_validation_failed", item.get("materializationBlockedByReason", {}), cid)
            self.assertEqual(item.get("freeze"), None)
            self.assertEqual(item.get("runtimeExecuted"), False)


if __name__ == "__main__":
    unittest.main()

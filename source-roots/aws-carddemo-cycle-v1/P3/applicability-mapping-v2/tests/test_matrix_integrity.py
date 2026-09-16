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


    def test_file_selectors_use_explicit_field_resource_map(self):
        matrix = load_json(ROOT / "applicability_matrix.json")
        expected_by_track = {
            "posting": {
                "accountFile": {"ACCTFILE"}, "accounts": {"ACCTFILE"},
                "categoryBalanceFile": {"TCATBALF"}, "categoryBalances": {"TCATBALF"},
                "crossReferenceFile": {"XREFFILE"}, "cardCrossReference": {"XREFFILE"},
                "transactionFile": {"TRANFILE"}, "outputTransactionFile": {"TRANFILE"},
                "transactionOutput": {"TRANFILE"}, "rejectFile": {"DALYREJS"},
                "rejectionOutput": {"DALYREJS"},
            },
            "interest": {
                "accountFile": {"ACCTFILE"}, "accounts": {"ACCTFILE"},
                "categoryBalanceFile": {"TCATBALF"}, "categoryBalances": {"TCATBALF"},
                "crossReferenceFile": {"XREFFILE"}, "cardCrossReference": {"XREFFILE"},
                "disclosureGroupFile": {"DISCGRP"}, "disclosureGroups": {"DISCGRP"},
                "outputTransactionFile": {"TRANSACT"}, "transactionOutput": {"TRANSACT"},
            },
            "reporting": {
                "crossReferenceFile": {"CARDXREF"}, "cardCrossReference": {"CARDXREF"},
                "transactionTypeFile": {"TRANTYPE"}, "transactionTypes": {"TRANTYPE"},
                "transactionCategoryFile": {"TRANCATG"}, "transactionCategories": {"TRANCATG"},
                "reportFile": {"TRANREPT"}, "reportOutput": {"TRANREPT"},
            },
        }
        mismatches = []
        for obligation in matrix["obligations"]:
            for mapping in obligation["contractMappings"]:
                for selector in mapping["t3DeterministicMapping"].get("fieldSelectors", []):
                    field = selector.get("field")
                    expected = expected_by_track[obligation["track"]]
                    if field in expected:
                        self.assertIsInstance(selector.get("allowedSource"), list, selector)
                        observed = set(selector["allowedSource"])
                        if observed != expected[field]:
                            mismatches.append((obligation["obligationId"], mapping["contractId"], field, sorted(observed), sorted(expected[field])))
        self.assertEqual(mismatches, [])

    def test_dimensions_separate_inventory_surface_fixture_generative_and_exercised(self):
        matrix = load_json(ROOT / "applicability_matrix.json")
        dimensions = matrix["denominators"].get("dimensions")
        self.assertIsInstance(dimensions, dict)
        self.assertEqual(dimensions["inventory_cells"], 175)
        self.assertEqual(dimensions["exercised_by_package_cells"], 0)
        self.assertLess(dimensions["generative_admissible_cells"], dimensions["inventory_cells"])
        for obligation in matrix["obligations"]:
            for mapping in obligation["contractMappings"]:
                dims = mapping.get("applicabilityDimensions")
                self.assertIsInstance(dims, dict)
                self.assertIs(dims["inventory_cell"], True)
                self.assertFalse(dims["exercised_by_package"])
                status = mapping["applicabilityStatus"]
                self.assertEqual(dims["surface_expressible"], status == "expressible_by_surface")
                self.assertEqual(dims["fixture_variant_required"], status == "conditioned_on_external_fixture")
                if status in {"not_expressible", "not_mapped", "precondition_indeterminate", "observation_inadmissible"}:
                    self.assertFalse(dims["generative_admissible"])

    def test_guard_sensitive_conditioned_cells_have_named_available_variant_or_block(self):
        matrix = load_json(ROOT / "applicability_matrix.json")
        guard_sensitive = {
            "POSTTRAN-OBL-004", "POSTTRAN-OBL-005", "POSTTRAN-OBL-006", "POSTTRAN-OBL-007",
            "INTCALC-OBL-004", "INTCALC-OBL-005", "INTCALC-OBL-007",
            "TRANREPT-OBL-003", "TRANREPT-OBL-004", "TRANREPT-OBL-005", "TRANREPT-OBL-007", "TRANREPT-OBL-008",
        }
        failures = []
        for obligation in matrix["obligations"]:
            if obligation["obligationId"] not in guard_sensitive:
                continue
            for mapping in obligation["contractMappings"]:
                if mapping["applicabilityStatus"] != "conditioned_on_external_fixture":
                    continue
                plan = mapping["t3DeterministicMapping"]
                variant = plan.get("fixtureVariant")
                blocked = plan.get("generativeUse") == "blocked" or bool(plan.get("blocks"))
                if variant:
                    self.assertIn(variant.get("availability"), {"available_candidate_fixture_variant", "officially_unexercised_candidate"})
                    self.assertTrue(variant.get("variantId"))
                elif not blocked:
                    failures.append((obligation["obligationId"], mapping["contractId"]))
        self.assertEqual(failures, [])

    def test_blocked_reporting_and_posting_partial_effects_have_no_executable_selectors(self):
        matrix = load_json(ROOT / "applicability_matrix.json")
        blocked_obligations = {"TRANREPT-OBL-003", "TRANREPT-OBL-007", "TRANREPT-OBL-008", "POSTTRAN-OBL-008", "POSTTRAN-OBL-009"}
        for obligation in matrix["obligations"]:
            if obligation["obligationId"] not in blocked_obligations:
                continue
            for mapping in obligation["contractMappings"]:
                plan = mapping["t3DeterministicMapping"]
                self.assertEqual(plan.get("generativeUse"), "diagnostics_only_non_generative")
                self.assertEqual(plan.get("fieldSelectors"), [], (obligation["obligationId"], mapping["contractId"]))
                self.assertFalse(mapping["applicabilityDimensions"]["generative_admissible"])

    def test_sdd_external_selection_only_and_no_officially_exercised_cells(self):
        matrix = load_json(ROOT / "applicability_matrix.json")
        sdd = [m for o in matrix["obligations"] for m in o["contractMappings"] if m["contractId"] == "E3-01-SDD-stage6r3"]
        self.assertEqual(len(sdd), 25)
        all_mappings = [m for o in matrix["obligations"] for m in o["contractMappings"]]
        self.assertFalse(any(m["applicabilityDimensions"]["exercised_by_package"] for m in all_mappings))
        for mapping in sdd:
            plan = mapping["t3DeterministicMapping"]
            self.assertEqual(plan["requestBody"], {})
            self.assertEqual(plan["fieldSelectors"], [])
            self.assertEqual(plan.get("selectionMode"), "external_fixture_schedule_only")


if __name__ == "__main__":
    unittest.main()

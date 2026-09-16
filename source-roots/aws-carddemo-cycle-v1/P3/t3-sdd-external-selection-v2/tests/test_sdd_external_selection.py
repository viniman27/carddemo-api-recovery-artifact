from __future__ import annotations

import base64
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
sys.path.insert(0, str(ROOT))

import sdd_external_selection as ext  # noqa: E402


class SddExternalSelectionTests(unittest.TestCase):
    def test_plan_selects_by_fixture_id_while_preserving_empty_request(self):
        plan = ext.build_external_selection_plan(P3)
        self.assertEqual(plan["kind"], "t3-sdd-external-selection-v2-plan")
        self.assertEqual(plan["contract"]["registryContractId"], "E3-SDD-stage6r3")
        self.assertTrue(all(plan["contract"]["schemaEmptyRequestByTrack"].values()))
        self.assertGreater(plan["summary"]["selected"], 0)
        for cell in plan["selectedCells"]:
            self.assertEqual(cell["requestBody"], {})
            self.assertTrue(cell["requestBodyPreservedEmpty"])
            self.assertIn(cell["fixtureId"], {"posting.candidate-v1-physical-v2", "interest.candidate-v1-physical-v2", "reporting.candidate-v1-physical-v2"})
            self.assertTrue(cell["resourceChecks"])
            self.assertTrue(cell["source"]["sourceAnchors"])
            self.assertTrue(cell["source"]["referenceTransitions"])
            self.assertTrue(cell["guardBasis"])
            self.assertTrue(cell["noExpected"])

    def test_v2_qualifies_overbroad_classifications_without_adding_fixtures(self):
        plan = ext.build_external_selection_plan(P3)
        by_obligation = {cell["source"]["obligationId"]: cell for cell in plan["selectedCells"]}
        post = by_obligation["POSTTRAN-OBL-007"]
        self.assertEqual(post["selectionCategory"], "guard_eligible_partial_branch")
        self.assertEqual(post["selectedGuardPartitions"], ["tcatbal_status=00"])
        self.assertEqual(post["unselectedGuardPartitions"], ["tcatbal_status=23", "tcatbal_status=other"])
        self.assertEqual(post["effectiveSelectableTransitions"], ["POSTTRAN-T012", "POSTTRAN-T013"])
        self.assertIn("status 23", " ".join(post["limits"]).lower())

        interest = by_obligation["INTCALC-OBL-004"]
        self.assertEqual(interest["selectionCategory"], "guard_eligible_partial_branch")
        self.assertEqual(interest["selectedGuardPartitions"], ["disc_rate_path=specific", "disc_rate_path=zero"])
        self.assertEqual(interest["unselectedGuardPartitions"], ["disc_rate_path=default", "disc_rate_path=missing"])
        self.assertEqual(interest["effectiveSelectableTransitions"], ["INTCALC-T007", "INTCALC-T009Z"])

    def test_v2_categories_distinguish_preparation_guards_and_missing_oracles(self):
        plan = ext.build_external_selection_plan(P3)
        counts = plan["summary"]["selectionCategories"]
        self.assertEqual(counts["request_preparation_static_only"], 3)
        self.assertEqual(counts["guard_eligible"], 9)
        self.assertEqual(counts["guard_eligible_partial_branch"], 2)
        self.assertEqual(counts["branch_selected_no_output_oracle"], 3)
        self.assertEqual(counts["request_preparation_no_output_oracle"], 1)
        self.assertEqual(plan["summary"]["selected"], 18)
        self.assertEqual(plan["summary"]["blocked"], 7)

    def test_static_adapter_restricts_cases_to_effectively_selectable_transitions(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            ext.run_all(P3, out)
            adapter = json.loads((out / "adapter-static-check.json").read_text())
            by_cell = {}
            for case in adapter["cases"]:
                by_cell.setdefault(case["cellRef"].split("::")[0], set()).add(case["transitionId"])
            self.assertEqual(by_cell["POSTTRAN-OBL-007"], {"POSTTRAN-T012", "POSTTRAN-T013"})
            self.assertEqual(by_cell["INTCALC-OBL-004"], {"INTCALC-T007", "INTCALC-T009Z"})
            self.assertEqual(adapter["excludedByEffectiveSelection"], [
                {"cellRef": "INTCALC-OBL-004::E3-01-SDD-stage6r3::interest", "transitionId": "INTCALC-T008"},
                {"cellRef": "INTCALC-OBL-004::E3-01-SDD-stage6r3::interest", "transitionId": "INTCALC-T008"},
                {"cellRef": "POSTTRAN-OBL-007::E3-01-SDD-stage6r3::posting", "transitionId": "POSTTRAN-T014"},
            ])

    def test_absence_of_external_authority_does_not_make_sdd_cell_eligible(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            plan = ext.build_external_selection_plan(P3)
            # Remove one selected cell from the external authority plan; it must stay blocked after enrichment.
            removed = plan["selectedCells"].pop(0)
            plan["summary"]["selected"] = len(plan["selectedCells"])
            ext.write_versioned_copies(plan, P3, out)
            enriched_info = ext.enrich_with_external_selection(plan, P3, out)
            enriched = enriched_info["enriched"]
            matching = [c for c in enriched["cells"] if c.get("cellId") in {removed["cellId"], removed["matrixCellId"]}]
            self.assertEqual(len(matching), 1)
            self.assertIsNot(matching[0].get("executableEligible"), True)
            self.assertIsNone(matching[0].get("selectorObjects"))
            self.assertNotIn("externalSelectionAuthority", matching[0])

    def test_static_adapter_link_uses_real_adapter_and_generates_empty_sdd_bodies(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            report = ext.run_all(P3, out)
            self.assertEqual(report["status"], "candidate_static_only")
            adapter = json.loads((out / "adapter-static-check.json").read_text())
            self.assertEqual(adapter["status"], "PASS")
            self.assertGreater(adapter["caseCount"], 0)
            self.assertEqual(adapter["badBodies"], [])
            self.assertTrue(all(case["body"] == {} for case in adapter["cases"]))
            self.assertTrue(all(case["path"] in {"/posting", "/interest", "/reporting"} for case in adapter["cases"]))
            fixtures = {case["fixtureId"] for case in adapter["cases"]}
            self.assertTrue({"posting.candidate-v1-physical-v2", "interest.candidate-v1-physical-v2", "reporting.candidate-v1-physical-v2"}.issubset(fixtures))

    def test_static_fairness_does_not_mark_non_sdd_with_external_authority(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            report = ext.run_all(P3, out)
            fairness = json.loads((out / "static-fairness-check.json").read_text())
            self.assertEqual(fairness["status"], "PASS")
            self.assertTrue(fairness["checks"]["sddUsesOnlyEmptyRequestBodies"])
            self.assertTrue(fairness["checks"]["nonSddUnchangedByExternalSelection"])
            self.assertTrue(fairness["checks"]["noBlockedSddMadeEligibleWithoutAuthority"])
            self.assertGreater(fairness["counts"]["nonSddEligible"], 0)
            self.assertGreater(fairness["counts"]["sddEligible"], 0)

    def test_fixture_byte_check_is_structural_only_and_passes_current_pins(self):
        result = ext.verify_current_fixture_bytes(P3 / "fixture-materialization-v2/package/manifest.json")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["checkedCount"], 18)
        self.assertEqual(result["mismatches"], [])


if __name__ == "__main__":
    unittest.main()

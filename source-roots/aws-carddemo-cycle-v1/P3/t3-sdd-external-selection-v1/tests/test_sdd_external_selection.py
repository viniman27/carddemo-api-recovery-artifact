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

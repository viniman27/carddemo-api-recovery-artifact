from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from mapping_integration import (  # noqa: E402
    MappingBlocked,
    build_enriched_plan,
    compatibility_inventory,
    map_enriched_model_to_suite,
    request_from_cell,
    FixtureIndex,
)


class MappingIntegrationV2Tests(unittest.TestCase):
    def test_isolated_import_uses_campaign_harness_v3_not_stale_sys_modules(self):
        code = "\n".join([
            "import json, sys",
            f"sys.path.insert(0, {str(ROOT / 'src')!r})",
            "import mapping_integration",
            "import campaign_harness",
            "print(json.dumps({'mapping': mapping_integration.__file__, 'harness': campaign_harness.__file__}))",
        ])
        out = subprocess.check_output([sys.executable, "-c", code], text=True)
        paths = json.loads(out)
        self.assertIn("t3-mapping-integration-v2/src/mapping_integration.py", paths["mapping"])
        self.assertIn("campaign-harness-v3/src/campaign_harness.py", paths["harness"])
        self.assertNotIn("campaign-harness-v1", paths["harness"])

    def test_real_upstream_blocked_or_diagnostics_cells_cannot_gain_selectors_or_eligible_recipe(self):
        matrix = json.loads((P3 / "applicability-mapping-v3" / "applicability_matrix.json").read_text())
        recipes = json.loads((P3 / "t3-mapping-recipes-v1" / "recipes.json").read_text())
        enriched = build_enriched_plan(matrix, recipes)
        bad = []
        for cell in enriched["cells"]:
            plan = cell.get("sourcePlan") or {}
            upstream_blocked = (
                plan.get("generativeUse") in {"blocked", "diagnostics_only_non_generative"}
                or plan.get("selectorUsableForGeneration") is False
            )
            if upstream_blocked and (
                cell.get("selectorObjects") is not None
                or cell.get("executableEligible") is True
                or cell.get("status") != "blocked"
            ):
                bad.append({"cellId": cell.get("cellId"), "status": cell.get("status"), "eligible": cell.get("executableEligible"), "selectors": cell.get("selectorObjects")})
        self.assertEqual(bad, [])
        posttran = [c for c in enriched["cells"] if c["cellId"].startswith("POSTTRAN-OBL-004::E1")]
        self.assertGreaterEqual(len(posttran), 3)
        self.assertTrue(all((c.get("sourcePlan") or {}).get("generativeUse") == "blocked" for c in posttran))
        self.assertTrue(all(c.get("linkedRecipe") is not None for c in posttran), "recipe existence remains recorded")
        self.assertTrue(all(c.get("executableEligible") is False and c.get("selectorObjects") is None for c in posttran))

    def test_real_inventory_counts_use_conjunctive_plan_authority_not_v1_119_claim(self):
        matrix = json.loads((P3 / "applicability-mapping-v3" / "applicability_matrix.json").read_text())
        recipes = json.loads((P3 / "t3-mapping-recipes-v1" / "recipes.json").read_text())
        enriched = build_enriched_plan(matrix, recipes)
        inv = compatibility_inventory(enriched)
        self.assertEqual(enriched["summary"]["cellsTotal"], 175)
        self.assertEqual(enriched["summary"]["recipesTotal"], 21)
        self.assertEqual(enriched["summary"]["executableEligibleCellsWithLinkedRecipe"], 44)
        self.assertEqual(enriched["summary"]["recipeExistsButNotExecutableEligible"], 75)
        self.assertEqual(inv["totals"]["recipe_available_unexercised"], 44)
        self.assertEqual(inv["totals"]["implementation_missing"], 82)
        self.assertEqual(inv["totals"]["missing_fixture_variant"], 28)
        self.assertEqual(inv["totals"]["observation_without_authority"], 14)
        self.assertEqual(inv["totals"]["contractually_impossible"], 7)
        self.assertNotEqual(inv["totals"]["recipe_available_unexercised"], 119)

    def test_missing_fixture_for_empty_sdd_is_blocked_not_placeholder_fixture(self):
        matrix = {"obligations": [{"obligationId": "SDD-EMPTY", "track": "sdd", "contractMappings": [{"contractId": "E3-SDD", "applicabilityStatus": "expressible_by_surface", "applicabilityDimensions": {"generative_admissible": True}, "operation": {"method": "post", "path": "/empty", "operationId": "empty"}, "t3DeterministicMapping": {"requestBody": {}, "generativeUse": "candidate_mapping_only_unexercised", "selectorUsableForGeneration": True}}]}]}
        recipes = {"recipes": [{"recipeId": "r-empty", "contractId": "E3-SDD", "track": "sdd", "operationId": "empty", "operation": {"method": "post", "path": "/empty"}, "fixtureSelection": None, "requestBody": {}, "sddConstantEmptyObject": True, "officialCampaign": False}]}
        enriched = build_enriched_plan(matrix, recipes)
        cell = enriched["cells"][0]
        self.assertIsNone(cell.get("fixtureId"))
        self.assertFalse(cell.get("executableEligible"))
        self.assertEqual(cell.get("classification"), "implementation_missing")
        self.assertIn("fixture", cell.get("reason", ""))
        with self.assertRaises(MappingBlocked) as cm:
            request_from_cell(cell, FixtureIndex({}), {"paths": {"/empty": {"post": {"requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "properties": {}, "additionalProperties": False}}}}, "responses": {"200": {"description": "ok"}}}}}})
        self.assertIn("fixture", cm.exception.reason)

    def test_synthetic_nonsdd_allowed_case_and_blocked_real_guard(self):
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            fixture_root = tmp / "fixture"; fixture_root.mkdir()
            (fixture_root / "PAYLOAD.bin").write_bytes(b"abc")
            fixtures = tmp / "fixtures.json"
            fixtures.write_text(json.dumps({"fixtures": [{"fixtureId": "fixture-a", "track": "synthetic", "packagePath": str(fixture_root), "resources": [{"dd": "PAYLOAD", "path": "PAYLOAD.bin", "bytes": 3, "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"}], "bindings": {"PAYLOAD": "PAYLOAD.bin"}}]}))
            schema = tmp / "schema.json"
            schema.write_text(json.dumps({"openapi": "3.1.0", "info": {"title": "synthetic", "version": "1"}, "paths": {"/ok": {"post": {"operationId": "op", "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "required": ["payload"], "additionalProperties": False, "properties": {"payload": {"type": "string"}}}}}}, "responses": {"200": {"description": "ok"}}}}}}))
            model = tmp / "model.json"
            model.write_text(json.dumps({"capabilities": [{"id": "S", "initialState": "S0", "transitions": [{"id": "OBL-OK", "from": "S0", "to": "S1"}, {"id": "POSTTRAN-OBL-004", "from": "S0", "to": "S2"}]}]}))
            matrix = {"obligations": [
                {"obligationId": "OBL-OK", "track": "synthetic", "contractMappings": [{"contractId": "C1", "applicabilityStatus": "expressible_by_surface", "applicabilityDimensions": {"generative_admissible": True}, "operation": {"method": "post", "path": "/ok", "operationId": "op"}, "t3DeterministicMapping": {"requestBody": {"payload": {"fromBytes": "PAYLOAD", "encoding": "base64"}}, "generativeUse": "candidate_mapping_only_unexercised", "selectorUsableForGeneration": True}}]},
                {"obligationId": "POSTTRAN-OBL-004", "track": "synthetic", "contractMappings": [{"contractId": "C1", "applicabilityStatus": "expressible_by_surface", "applicabilityDimensions": {"generative_admissible": True}, "operation": {"method": "post", "path": "/ok", "operationId": "op"}, "t3DeterministicMapping": {"requestBody": "deterministic_from_allowed_schema_fields_when_case_is_later_frozen", "generativeUse": "blocked", "selectorUsableForGeneration": False, "blocks": ["guard variant absent"]}}]},
            ]}
            recipes = {"recipes": [{"recipeId": "r1", "contractId": "C1", "track": "synthetic", "operationId": "op", "operation": {"method": "post", "path": "/ok"}, "fixtureSelection": {"fixtureId": "fixture-a", "track": "synthetic"}, "requestBody": {"payload": {"fromBytes": "PAYLOAD", "encoding": "base64"}}, "officialCampaign": False}]}
            enriched = build_enriched_plan(matrix, recipes)
            suite, report = map_enriched_model_to_suite("C1", model, enriched, fixtures, schema)
            self.assertEqual(report["acceptedCount"], 1)
            self.assertEqual(report["blockedCount"], 1)
            self.assertEqual(report["blocked"][0]["cellId"], "POSTTRAN-OBL-004::C1::op")
            self.assertEqual(len(suite.cases), 1)
            body = json.loads(base64.b64decode(suite.cases[0].request.body_b64).decode())
            self.assertEqual(body, {"payload": "YWJj"})


if __name__ == "__main__":
    unittest.main()

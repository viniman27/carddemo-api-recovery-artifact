from __future__ import annotations

import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(P3 / "campaign-harness-v1" / "src"))

from mapping_integration import (  # noqa: E402
    MappingBlocked,
    build_enriched_plan,
    compatibility_inventory,
    map_enriched_model_to_suite,
    validate_recipe_document,
)


class MappingIntegrationTests(unittest.TestCase):
    def test_real_recipes_enrich_v3_inventory_without_stale_9_supported_taxonomy(self):
        matrix = json.loads((P3 / "applicability-mapping-v3" / "applicability_matrix.json").read_text())
        recipes = json.loads((P3 / "t3-mapping-recipes-v1" / "recipes.json").read_text())

        enriched = build_enriched_plan(matrix, recipes)
        inv = compatibility_inventory(enriched)

        self.assertEqual(enriched["summary"]["recipesTotal"], 21)
        self.assertEqual(enriched["summary"]["cellsTotal"], 175)
        self.assertEqual(enriched["summary"]["v3AllowedCellsWithLinkedRecipe"], 119)
        self.assertEqual(inv["totals"]["recipe_available_unexercised"], 119)
        self.assertEqual(inv["totals"]["implementation_missing"], 7)
        self.assertEqual(inv["totals"]["missing_fixture_variant"], 28)
        self.assertEqual(inv["totals"]["observation_without_authority"], 14)
        self.assertEqual(inv["totals"]["contractually_impossible"], 7)
        self.assertNotIn("not_expressible", inv["totals"])
        self.assertGreater(inv["totals"]["recipe_available_unexercised"], 9)
        linked = [c for c in enriched["cells"] if c["classification"] == "recipe_available_unexercised"]
        self.assertTrue(all(c["linkedRecipe"] and c["fixtureId"] for c in linked))
        blocked = [c for c in enriched["cells"] if c["classification"] != "recipe_available_unexercised"]
        self.assertTrue(all(not c.get("selectorObjects") for c in blocked))

    def test_validate_static_recipe_document_counts_21_and_no_compile_failures(self):
        recipes = json.loads((P3 / "t3-mapping-recipes-v1" / "recipes.json").read_text())
        report = validate_recipe_document(recipes)
        self.assertEqual(report["operationRecipes"], 21)
        self.assertEqual(report["compileFailures"], [])
        self.assertEqual(report["officialCampaign"], False)
        self.assertEqual(report["recipeSchemaValidated"], True)

    def test_synthetic_nonsdd_cell_uses_linked_recipe_and_guardblocked_refuses_suite_case(self):
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            fixture_root = tmp / "fixture"; fixture_root.mkdir()
            (fixture_root / "PAYLOAD.bin").write_bytes(b"abc")
            fixtures = tmp / "fixtures.json"
            fixtures.write_text(json.dumps({"fixtures": [{"fixtureId": "fixture-a", "track": "synthetic", "packagePath": str(fixture_root), "resources": [{"dd": "PAYLOAD", "path": "PAYLOAD.bin", "bytes": 3, "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"}], "bindings": {"PAYLOAD": "PAYLOAD.bin"}}]}))
            schema = tmp / "schema.json"
            schema.write_text(json.dumps({"openapi": "3.1.0", "info": {"title": "synthetic", "version": "1"}, "paths": {"/ok": {"post": {"operationId": "op", "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "required": ["payload", "binding"], "additionalProperties": False, "properties": {"payload": {"type": "string"}, "binding": {"type": "string"}}}}}}, "responses": {"200": {"description": "ok"}}}}}}))
            model = tmp / "model.json"
            model.write_text(json.dumps({"capabilities": [{"id": "S", "initialState": "S0", "transitions": [{"id": "OBL-OK", "from": "S0", "to": "S1"}, {"id": "OBL-GUARD", "from": "S0", "to": "S2"}]}]}))
            matrix = {"kind": "synthetic-v3", "obligations": [{"obligationId": "OBL-OK", "track": "synthetic", "contractMappings": [{"contractId": "C1", "applicabilityStatus": "expressible_by_surface", "operation": {"method": "post", "path": "/ok", "operationId": "op"}}]}, {"obligationId": "OBL-GUARD", "track": "synthetic", "contractMappings": [{"contractId": "C1", "applicabilityStatus": "precondition_indeterminate", "operation": {"method": "post", "path": "/ok", "operationId": "op"}}]}]}
            recipes = {"kind": "t3-mapping-recipes-v1", "officialCampaign": False, "recipes": [{"recipeId": "r1", "contractId": "C1", "track": "synthetic", "operationId": "op", "operation": {"method": "post", "path": "/ok"}, "fixtureSelection": {"fixtureId": "fixture-a", "track": "synthetic"}, "requestBody": {"payload": {"fromBytes": "PAYLOAD", "encoding": "base64"}, "binding": {"fromBinding": "PAYLOAD"}}, "officialCampaign": False}]}
            enriched = build_enriched_plan(matrix, recipes)

            suite, report = map_enriched_model_to_suite("C1", model, enriched, fixtures, schema)

            self.assertEqual(report["acceptedCount"], 1)
            self.assertEqual(report["blockedCount"], 1)
            self.assertEqual(report["blocked"][0]["classification"], "missing_fixture_variant")
            self.assertEqual(len(suite.cases), 1)
            case = suite.cases[0]
            self.assertIn("OBL-OK::C1::op", case.case_id)
            body = json.loads(base64.b64decode(case.request.body_b64).decode())
            self.assertEqual(body, {"payload": "YWJj", "binding": "PAYLOAD.bin"})
            self.assertEqual(case.resource_package_id, "fixture-a")

    def test_guardblocked_selector_relaxation_is_rejected_even_when_recipe_exists(self):
        matrix = {"obligations": [{"obligationId": "OBL-G", "track": "synthetic", "contractMappings": [{"contractId": "C", "applicabilityStatus": "observation_inadmissible", "operation": {"method": "post", "path": "/x", "operationId": "op"}}]}]}
        recipes = {"kind": "t3-mapping-recipes-v1", "officialCampaign": False, "recipes": [{"recipeId": "r", "contractId": "C", "track": "synthetic", "operationId": "op", "operation": {"method": "post", "path": "/x"}, "fixtureSelection": {"fixtureId": "f"}, "requestBody": {"a": {"literal": "b"}}, "officialCampaign": False}]}
        enriched = build_enriched_plan(matrix, recipes)
        self.assertEqual(enriched["cells"][0]["classification"], "observation_without_authority")
        self.assertIsNone(enriched["cells"][0]["linkedRecipe"])
        with self.assertRaises(MappingBlocked):
            # Mapper must refuse blocked cells rather than consume their available recipe.
            from mapping_integration import request_from_cell, FixtureIndex
            request_from_cell(enriched["cells"][0], FixtureIndex({}), {"paths": {"/x": {"post": {"responses": {"200": {"description": "ok"}}}}}})


if __name__ == "__main__":
    unittest.main()

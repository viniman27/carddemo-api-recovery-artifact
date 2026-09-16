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

from t3_campaign_adapter import (  # noqa: E402
    AdapterBlocked,
    build_t3_suite,
    cell_index_from_enriched_plan,
    load_real_inputs,
    materialize_request_from_cell,
    select_transition_cells,
    static_real_model_compatibility,
)

HARNESS = P3 / "campaign-harness-v3" / "src"
sys.path.insert(0, str(HARNESS))
from campaign_harness import freeze_suite, load_frozen_suite  # noqa: E402

REF = P3 / "reference-executable-v4"
sys.path.insert(0, str(REF))
from executable_reference import load_model, step, traverse  # noqa: E402


class T3CampaignAdapterTests(unittest.TestCase):
    def synthetic_fixture_files(self, tmp: Path) -> tuple[Path, Path, Path]:
        pkg = tmp / "pkg"
        pkg.mkdir()
        (pkg / "PAYLOAD.bin").write_bytes(b"abc")
        fixtures = tmp / "fixtures.json"
        fixtures.write_text(json.dumps({
            "fixtures": [{
                "fixtureId": "fixture-ok", "track": "synthetic", "packagePath": str(pkg),
                "resources": [{"dd": "PAYLOAD", "path": "PAYLOAD.bin", "bytes": 3, "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"}],
                "bindings": {"PAYLOAD": "PAYLOAD.bin"},
            }]
        }), encoding="utf-8")
        schema = tmp / "schema.json"
        schema.write_text(json.dumps({
            "openapi": "3.1.0", "info": {"title": "synthetic", "version": "1"},
            "paths": {"/ok": {"post": {"operationId": "op", "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "required": ["payload"], "additionalProperties": False, "properties": {"payload": {"type": "string"}}}}}}, "responses": {"200": {"description": "ok"}}}}}
        }), encoding="utf-8")
        return pkg, fixtures, schema

    def synthetic_enriched(self) -> dict:
        return {"cells": [
            {"cellId": "OBL-A::C1::op", "obligationId": "OBL-A", "contractId": "C1", "track": "synthetic", "operationId": "op", "operation": {"method": "post", "path": "/ok"}, "classification": "recipe_available_unexercised", "status": "candidate", "executableEligible": True, "recipeExists": True, "fixtureId": "fixture-ok", "selectorObjects": {"payload": {"fromBytes": "PAYLOAD", "encoding": "base64"}}, "linkedRecipe": {"recipeId": "r-a"}},
            {"cellId": "OBL-B::C1::op", "obligationId": "OBL-B", "contractId": "C1", "track": "synthetic", "operationId": "op", "operation": {"method": "post", "path": "/ok"}, "classification": "recipe_available_unexercised", "status": "candidate", "executableEligible": True, "recipeExists": True, "fixtureId": "fixture-ok", "selectorObjects": {"payload": {"fromBytes": "PAYLOAD", "encoding": "base64"}}, "linkedRecipe": {"recipeId": "r-b"}},
            {"cellId": "OBL-DENIED::C1::op", "obligationId": "OBL-DENIED", "contractId": "C1", "track": "synthetic", "operationId": "op", "operation": {"method": "post", "path": "/ok"}, "classification": "implementation_missing", "status": "blocked", "executableEligible": False, "recipeExists": True, "fixtureId": None, "selectorObjects": None, "reason": "upstream denied"},
        ]}

    def test_real_transition_obligation_refs_select_cells_not_transition_ids(self):
        model = load_model(REF / "model.json")
        transitions = step(model, "CBACT04C_INTCALC", "I_OPENED", {"tcatbal_read_status": "00"})
        self.assertEqual(transitions[0]["transitionId"], "INTCALC-T003")
        real_transition = next(t for c in model["capabilities"] for t in c["transitions"] if t["id"] == "INTCALC-T003")
        enriched = {"cells": [
            {"cellId": "INTCALC-OBL-002::C1::op", "obligationId": "INTCALC-OBL-002", "contractId": "C1"},
            {"cellId": "INTCALC-OBL-003::C1::op", "obligationId": "INTCALC-OBL-003", "contractId": "C1"},
            {"cellId": "INTCALC-T003::C1::op", "obligationId": "INTCALC-T003", "contractId": "C1"},
        ]}
        cells = select_transition_cells(real_transition, cell_index_from_enriched_plan(enriched, contract_id="C1"))
        self.assertEqual([c["obligationId"] for c in cells], ["INTCALC-OBL-002", "INTCALC-OBL-003"])
        self.assertNotIn("INTCALC-T003", [c["obligationId"] for c in cells])

    def test_false_and_unknown_guards_use_reference_engine_step_results(self):
        model = load_model(REF / "model.json")
        false_case = step(model, "CBTRN02C_POSTTRAN", "P_START", {"open_status": "not_00"})
        self.assertEqual([t["transitionId"] for t in false_case], ["POSTTRAN-T002"])
        self.assertNotIn("POSTTRAN-T001", [t["transitionId"] for t in false_case])
        unknown_case = step(model, "CBTRN02C_POSTTRAN", "P_OPENED", {"read_status": "UnknownEOF"})
        self.assertTrue(any(t["guardResult"] == "unknown" for t in unknown_case))

    def test_upstream_denied_cell_is_blocked_and_does_not_materialize_request(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _, fixtures, schema = self.synthetic_fixture_files(tmp)
            denied = self.synthetic_enriched()["cells"][2]
            with self.assertRaises(AdapterBlocked) as cm:
                materialize_request_from_cell(denied, fixtures, schema)
            self.assertIn("blocked", cm.exception.reason)

    def test_synthetic_build_traverses_multiple_capabilities_and_freezes_with_harness_v3(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _, fixtures, schema = self.synthetic_fixture_files(tmp)
            model_path = tmp / "model.json"
            model_path.write_text(json.dumps({"capabilities": [
                {"id": "CAP-A", "initialState": "A0", "variables": {"mode": {"type": "enum", "domain": ["go", "stop"], "initial": "go"}}, "states": [{"id": "A0"}, {"id": "A1"}], "transitions": [{"id": "TA", "from": "A0", "to": "A1", "guard": {"op": "eq", "left": {"var": "mode"}, "right": {"value": "go", "type": "enum"}}, "effects": [], "obligationRefs": ["OBL-A"]}]},
                {"id": "CAP-B", "initialState": "B0", "variables": {"ready": {"type": "bool", "domain": [True, False], "initial": True}}, "states": [{"id": "B0"}, {"id": "B1"}], "transitions": [{"id": "TB", "from": "B0", "to": "B1", "guard": {"op": "eq", "left": {"var": "ready"}, "right": {"value": True, "type": "bool"}}, "effects": [], "obligationRefs": ["OBL-B"]}]},
            ]}), encoding="utf-8")
            suite, report = build_t3_suite("C1", model_path, self.synthetic_enriched(), fixtures, schema, capabilities=["CAP-A", "CAP-B"], max_depth=2, max_paths_per_capability=5)
            self.assertEqual(report["acceptedCount"], 2)
            self.assertEqual(report["blockedCount"], 0)
            self.assertEqual({c.parameters["transitionId"] for c in suite.cases}, {"TA", "TB"})
            self.assertEqual([c.expectation.checks["contract_checker"] for c in suite.cases], ["documented_separate_independent_obligation", "documented_separate_independent_obligation"])
            path = freeze_suite(suite, tmp / "T3.json")
            loaded = load_frozen_suite(path)
            self.assertEqual(len(loaded.cases), 2)
            body = json.loads(base64.b64decode(loaded.cases[0].request.body_b64).decode())
            self.assertEqual(body, {"payload": "YWJj"})

    def test_real_model_static_compatibility_does_not_generate_official_suite(self):
        report = static_real_model_compatibility(P3, contract_id="E1-1", capabilities=["CBTRN02C_POSTTRAN", "CBACT04C_INTCALC", "CBTRN03C_TRANREPT"], max_depth=6, max_paths_per_capability=12)
        self.assertEqual(report["officialCampaign"], False)
        self.assertEqual(report["officialSuiteGenerated"], False)
        self.assertEqual(report["modelValidation"]["errors"], [])
        self.assertGreater(report["selectionPlan"]["transitionCount"], 0)
        self.assertIn("omissions", report["selectionPlan"])
        self.assertIn("CBTRN02C_POSTTRAN", report["traversalSummaries"])


if __name__ == "__main__":
    unittest.main()

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
HARNESS = P3 / "campaign-harness-v1" / "src"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HARNESS))

from campaign_harness import load_frozen_suite  # noqa: E402
from t3_mapper import (  # noqa: E402
    FixtureIndex,
    MappingBlocked,
    build_request_from_explicit_mapping,
    bfs_map_model_to_suite,
    compatibility_inventory,
    freeze_load_synthetic,
    validate_request_against_openapi,
)


class T3MapperPreparationTests(unittest.TestCase):
    def synthetic_openapi(self) -> dict:
        return {
            "openapi": "3.1.0",
            "info": {"title": "synthetic only", "version": "1"},
            "paths": {
                "/synthetic": {
                    "post": {
                        "operationId": "syntheticPost",
                        "requestBody": {
                            "required": True,
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SyntheticRequest"}}},
                        },
                        "responses": {"200": {"description": "ok"}},
                    }
                },
                "/sdd": {
                    "post": {
                        "operationId": "sddPost",
                        "requestBody": {
                            "required": True,
                            "content": {"application/json": {"schema": {"type": "object", "properties": {}, "additionalProperties": False}}},
                        },
                        "responses": {"200": {"description": "ok"}},
                    }
                },
            },
            "components": {
                "schemas": {
                    "SyntheticRequest": {
                        "type": "object",
                        "required": ["resource", "binding", "payload", "scale", "name"],
                        "additionalProperties": False,
                        "properties": {
                            "resource": {"type": "string"},
                            "binding": {"type": "string"},
                            "payload": {"type": "string"},
                            "scale": {"type": "integer"},
                            "name": {"type": "string"},
                        },
                    }
                }
            },
        }

    def test_explicit_mapping_builds_resources_bindings_bytes_scalars_and_validates_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            fixture_root = tmp / "fixture"
            fixture_root.mkdir()
            (fixture_root / "PAYLOAD.bin").write_bytes(b"abc")
            fixture = FixtureIndex.from_manifest(
                {
                    "fixtures": [
                        {
                            "fixtureId": "fixture-a",
                            "track": "synthetic",
                            "packagePath": str(fixture_root),
                            "resources": [{"dd": "PAYLOAD", "bytes": 3, "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"}],
                            "bindings": {"PAYLOAD": "PAYLOAD.bin"},
                        }
                    ]
                }
            )
            mapping = {
                "operation": {"method": "post", "path": "/synthetic"},
                "fixtureSelection": {"fixtureId": "fixture-a"},
                "requestBody": {
                    "resource": {"fromResource": "PAYLOAD", "format": "ddName"},
                    "binding": {"fromBinding": "PAYLOAD"},
                    "payload": {"fromBytes": "PAYLOAD", "encoding": "base64"},
                    "scale": {"literal": 2},
                    "name": {"literal": "ok"},
                },
            }

            request, evidence = build_request_from_explicit_mapping(mapping, fixture, self.synthetic_openapi())

            self.assertEqual(request.method, "POST")
            self.assertEqual(request.path, "/synthetic")
            body = json.loads(base64.b64decode(request.body_b64).decode())
            self.assertEqual(body["resource"], "PAYLOAD")
            self.assertEqual(body["binding"], "PAYLOAD.bin")
            self.assertEqual(body["payload"], "YWJj")
            self.assertEqual(body["scale"], 2)
            self.assertEqual(evidence["schemaValidation"]["valid"], True)
            self.assertEqual(evidence["selectedFixture"]["fixtureId"], "fixture-a")

    def test_refuses_ready_request_dict_and_unevidenced_selection_or_values(self):
        fixture = FixtureIndex.from_manifest({"fixtures": []})
        with self.assertRaises(MappingBlocked) as ready:
            build_request_from_explicit_mapping({"request": {"method": "POST", "path": "/synthetic", "body": {}}}, fixture, self.synthetic_openapi())
        self.assertIn("request_dict_not_allowed", ready.exception.blocked_reason)
        with self.assertRaises(MappingBlocked) as invented:
            build_request_from_explicit_mapping({"operation": {"method": "post", "path": "/synthetic"}, "requestBody": {"name": {"invent": "now"}}}, fixture, self.synthetic_openapi())
        self.assertIn("unsupported_selector", invented.exception.blocked_reason)
        with self.assertRaises(MappingBlocked) as no_fixture:
            build_request_from_explicit_mapping({"operation": {"method": "post", "path": "/synthetic"}, "fixtureSelection": {"fixtureId": "missing"}, "requestBody": {"name": {"literal": "x"}}}, fixture, self.synthetic_openapi())
        self.assertIn("fixture_not_found", no_fixture.exception.blocked_reason)

    def test_sdd_empty_request_constant_when_schema_is_closed_empty_object(self):
        fixture = FixtureIndex.from_manifest({"fixtures": []})
        mapping = {"operation": {"method": "post", "path": "/sdd"}, "requestBody": {}, "sddConstantEmptyObject": True}
        request, evidence = build_request_from_explicit_mapping(mapping, fixture, self.synthetic_openapi())
        self.assertEqual(base64.b64decode(request.body_b64), b"{}")
        self.assertTrue(evidence["sddConstantEmptyObject"])
        bad = {"operation": {"method": "post", "path": "/synthetic"}, "requestBody": {}, "sddConstantEmptyObject": True}
        with self.assertRaises(MappingBlocked) as ctx:
            build_request_from_explicit_mapping(bad, fixture, self.synthetic_openapi())
        self.assertIn("sdd_empty_object_not_sustained_by_schema", ctx.exception.blocked_reason)

    def test_bfs_mapper_blocks_by_cell_without_inventing_and_freezes_loads_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            schema_path = tmp / "schema.json"
            schema_path.write_text(json.dumps(self.synthetic_openapi()))
            model_path = tmp / "model.json"
            model_path.write_text(json.dumps({
                "capabilities": [{
                    "id": "SYNTH", "initialState": "S0", "transitions": [
                        {"id": "A", "from": "S0", "to": "S1", "path": ["A"]},
                        {"id": "B", "from": "S1", "to": "S2", "path": ["A", "B"]},
                        {"id": "C", "from": "S0", "to": "S3", "path": ["C"]},
                    ]
                }]
            }))
            fixture_root = tmp / "fixture"; fixture_root.mkdir(); (fixture_root / "PAYLOAD.bin").write_bytes(b"abc")
            fixtures_path = tmp / "fixtures.json"
            fixtures_path.write_text(json.dumps({"fixtures": [{"fixtureId": "fixture-a", "track": "synthetic", "packagePath": str(fixture_root), "resources": [{"dd": "PAYLOAD", "bytes": 3, "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"}], "bindings": {"PAYLOAD": "PAYLOAD.bin"}}]}))
            mappings_path = tmp / "mappings.json"
            mappings_path.write_text(json.dumps({"cells": [
                {"cellId": "cell-A", "transitionId": "A", "operation": {"method": "post", "path": "/synthetic"}, "fixtureSelection": {"fixtureId": "fixture-a"}, "requestBody": {"resource": {"fromResource": "PAYLOAD", "format": "ddName"}, "binding": {"fromBinding": "PAYLOAD"}, "payload": {"fromBytes": "PAYLOAD", "encoding": "base64"}, "scale": {"literal": 2}, "name": {"literal": "ok"}}},
                {"cellId": "cell-B", "transitionId": "B", "operation": {"method": "post", "path": "/synthetic"}, "fixtureSelection": {"fixtureId": "fixture-a"}, "requestBody": {"name": {"fromBytes": "MISSING"}}},
                {"cellId": "cell-C", "transitionId": "C", "blocked_reason": "matrix lacks concrete mapping"},
            ]}))
            suite, report = bfs_map_model_to_suite("SYNTH", model_path, mappings_path, fixtures_path, schema_path, max_depth=3)
            self.assertEqual([c.case_id for c in suite.cases], ["T3-SYNTH-cell-A"])
            self.assertEqual(report["acceptedCount"], 1)
            self.assertEqual(report["blockedCount"], 2)
            self.assertEqual({b["cellId"] for b in report["blocked"]}, {"cell-B", "cell-C"})
            loaded, freeze_report = freeze_load_synthetic(suite, tmp / "freeze")
            self.assertEqual(len(loaded.cases), 1)
            self.assertTrue((tmp / "freeze" / "T3.json").exists())
            self.assertEqual(freeze_report["officialCampaign"], False)
            self.assertEqual(load_frozen_suite(tmp / "freeze" / "T3.json").suite_id, "T3")

    def test_recipe_builds_nested_nonsdd_request_from_record_bytes_and_sourcebound_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            fixture_root = tmp / "fixture"
            fixture_root.mkdir()
            record = (
                "REPORT-IN---001 "
                + "01"
                + "0005"
                + "Internet  "
                + "candidate purchase".ljust(100)
                + "00000001200"
                + "123456789"
                + "Fixture Merchant".ljust(50)
                + "Sometown".ljust(50)
                + "70000000  "
                + "4111111111111111"
                + "2022-07-05-10.00.00.000000"
                + "2022-07-05-10.05.00.000000"
                + "".ljust(20)
            ).encode("ascii")
            self.assertEqual(len(record), 350)
            (fixture_root / "DALYTRAN").write_bytes(record)
            (fixture_root / "ACCTFILE").write_bytes(b"acct")
            fixture = FixtureIndex.from_manifest({"fixtures": [{"fixtureId": "fixture-a", "track": "posting", "packagePath": str(fixture_root), "resources": [
                {"dd": "DALYTRAN", "path": "DALYTRAN", "bytes": 350, "sha256": "0" * 64},
                {"dd": "ACCTFILE", "path": "ACCTFILE", "bytes": 4, "sha256": "1" * 64},
            ], "bindings": {"ACCTFILE": "ACCTFILE"}}]})
            # real hash validation is exercised elsewhere; this test focuses on recipe compilation
            object.__setattr__(fixture.packages["fixture-a"].resources["DALYTRAN"], "sha256", None)
            object.__setattr__(fixture.packages["fixture-a"].resources["ACCTFILE"], "sha256", None)
            openapi = self.synthetic_openapi()
            openapi["paths"]["/posting"] = {"post": {"operationId": "posting", "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "required": ["bindings", "transactions"], "additionalProperties": False, "properties": {"bindings": {"type": "object", "required": ["accounts"], "additionalProperties": False, "properties": {"accounts": {"type": "string"}}}, "transactions": {"type": "array", "items": {"type": "object", "required": ["transactionId", "categoryCode", "amount", "merchantId"], "properties": {"transactionId": {"type": "string"}, "categoryCode": {"type": "integer"}, "amount": {"type": "number"}, "merchantId": {"type": "integer"}}}}}}}}}, "responses": {"200": {"description": "ok"}}}}
            recipe = {"operation": {"method": "post", "path": "/posting"}, "fixtureSelection": {"fixtureId": "fixture-a"}, "requestBody": {"object": {
                "bindings": {"object": {"accounts": {"fromBinding": "ACCTFILE"}}},
                "transactions": {"fromSequentialRecords": {"dd": "DALYTRAN", "recordLength": 350, "format": "transactionObjects", "numericFields": ["categoryCode", "amount", "merchantId"]}},
            }}}

            request, evidence = build_request_from_explicit_mapping(recipe, fixture, openapi)

            body = json.loads(base64.b64decode(request.body_b64).decode())
            self.assertEqual(body["bindings"], {"accounts": "ACCTFILE"})
            self.assertEqual(body["transactions"][0]["transactionId"], "REPORT-IN---001 ")
            self.assertEqual(body["transactions"][0]["categoryCode"], 5)
            self.assertEqual(body["transactions"][0]["amount"], 12.00)
            self.assertEqual(body["transactions"][0]["merchantId"], 123456789)
            self.assertGreaterEqual(len(evidence["sourceboundValues"]), 5)
            self.assertFalse(evidence["inventedValues"])

    def test_compatibility_inventory_distinguishes_missing_implementation_not_expressible_and_fixture_variant(self):
        matrix = {
            "obligations": [{"obligationId": "OBL", "track": "posting", "contractMappings": [
                {"contractId": "SDD", "operation": {"method": "post", "path": "/sdd", "requestSchema": {"type": "object", "properties": [], "additionalProperties": False}}, "t3DeterministicMapping": {"requestBody": {}, "selectorUsableForGeneration": True, "generativeUse": "candidate_mapping_only_unexercised", "fieldSelectors": []}, "candidateFixtures": [{"fixtureId": "posting.candidate"}]},
                {"contractId": "X", "operation": {"method": "post", "path": "/synthetic", "requestSchema": {"type": "object", "properties": ["name"], "additionalProperties": False}}, "applicabilityStatus": "expressible_by_surface", "t3DeterministicMapping": {"requestBody": "deterministic_from_allowed_schema_fields_when_case_is_later_frozen", "selectorUsableForGeneration": True, "generativeUse": "candidate_mapping_only_unexercised", "fieldSelectors": []}, "candidateFixtures": [{"fixtureId": "posting.candidate"}]},
                {"contractId": "Y", "operation": {"method": "post", "path": "/synthetic", "requestSchema": {"type": "object", "properties": ["name"], "additionalProperties": False}}, "applicabilityStatus": "not_expressible", "t3DeterministicMapping": {"requestBody": "deterministic_from_allowed_schema_fields_when_case_is_later_frozen", "selectorUsableForGeneration": False, "generativeUse": "blocked", "fieldSelectors": []}, "candidateFixtures": [{"fixtureId": "posting.candidate"}]},
                {"contractId": "Z", "operation": {"method": "post", "path": "/synthetic", "requestSchema": {"type": "object", "properties": ["name"], "additionalProperties": False}}, "applicabilityStatus": "conditioned_on_external_fixture", "t3DeterministicMapping": {"requestBody": "deterministic_from_allowed_schema_fields_when_case_is_later_frozen", "selectorUsableForGeneration": True, "generativeUse": "candidate_mapping_only_unexercised", "fieldSelectors": []}, "candidateFixtures": []},
            ]}]
        }
        inv = compatibility_inventory(matrix)
        self.assertEqual(inv["totals"]["supported"], 1)
        self.assertEqual(inv["totals"]["implementation_missing"], 1)
        self.assertEqual(inv["totals"]["not_expressible"], 1)
        self.assertEqual(inv["totals"]["missing_fixture_variant"], 1)
        self.assertEqual(inv["cells"][0]["sddConstantEmptyObject"], True)

    def test_cli_synthetic_only_and_static_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            ok = subprocess.run([sys.executable, str(ROOT / "t3_mapper_cli.py"), "synthetic", "--output", str(tmp / "out")], text=True, capture_output=True)
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            summary = json.loads(ok.stdout)
            self.assertFalse(summary["officialCampaign"])
            self.assertTrue((tmp / "out" / "freeze" / "T3.json").exists())
            bad = subprocess.run([sys.executable, str(ROOT / "t3_mapper_cli.py"), "official", "--output", str(tmp / "official")], text=True, capture_output=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("official T3 generation is gate-closed", bad.stdout + bad.stderr)


if __name__ == "__main__":
    unittest.main()

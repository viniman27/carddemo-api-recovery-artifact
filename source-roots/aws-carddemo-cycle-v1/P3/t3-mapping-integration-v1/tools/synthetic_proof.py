from __future__ import annotations

import base64
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from mapping_integration import build_enriched_plan, map_enriched_model_to_suite, json_bytes  # noqa: E402


def main() -> None:
    out = ROOT / "synthetic-proof.json"
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
        body = json.loads(base64.b64decode(suite.cases[0].request.body_b64).decode()) if suite.cases else None
        proof = {"kind": "t3-integrated-synthetic-proof", "status": "candidate", "officialCampaign": False, "acceptedCaseCount": len(suite.cases), "acceptedBody": body, "acceptedResourcePackageId": suite.cases[0].resource_package_id if suite.cases else None, "blocked": report["blocked"], "noOfficialAwsSuiteOrRequestsExported": True}
    out.write_bytes(json_bytes(proof))
    print(json.dumps(proof, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

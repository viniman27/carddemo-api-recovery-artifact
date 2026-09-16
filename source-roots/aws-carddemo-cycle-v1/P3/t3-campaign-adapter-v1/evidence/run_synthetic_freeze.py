import json
import sys
from pathlib import Path

p3 = Path.cwd() / "P3"
sys.path.insert(0, str(p3 / "t3-campaign-adapter-v1" / "src"))
from t3_campaign_adapter import build_t3_suite  # noqa: E402

sys.path.insert(0, str(p3 / "campaign-harness-v3" / "src"))
from campaign_harness import freeze_suite, load_frozen_suite  # noqa: E402

out = p3 / "t3-campaign-adapter-v1" / "evidence" / "synthetic-freeze"
out.mkdir(parents=True, exist_ok=True)
pkg = out / "pkg"
pkg.mkdir(exist_ok=True)
(pkg / "PAYLOAD.bin").write_bytes(b"abc")
fixtures = out / "fixtures.json"
schema = out / "schema.json"
model = out / "model.json"
fixtures.write_text(json.dumps({"fixtures": [{"fixtureId": "fixture-ok", "track": "synthetic", "packagePath": str(pkg), "resources": [{"dd": "PAYLOAD", "path": "PAYLOAD.bin", "bytes": 3, "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"}], "bindings": {"PAYLOAD": "PAYLOAD.bin"}}]}), encoding="utf-8")
schema.write_text(json.dumps({"openapi": "3.1.0", "info": {"title": "synthetic", "version": "1"}, "paths": {"/ok": {"post": {"operationId": "op", "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "required": ["payload"], "additionalProperties": False, "properties": {"payload": {"type": "string"}}}}}}, "responses": {"200": {"description": "ok"}}}}}}), encoding="utf-8")
model.write_text(json.dumps({"capabilities": [{"id": "CAP-A", "initialState": "S0", "variables": {"x": {"type": "enum", "domain": ["go"], "initial": "go"}}, "states": [{"id": "S0"}, {"id": "S1"}], "transitions": [{"id": "TA", "from": "S0", "to": "S1", "guard": {"op": "eq", "left": {"var": "x"}, "right": {"value": "go", "type": "enum"}}, "effects": [], "obligationRefs": ["OBL-A"]}]}]}), encoding="utf-8")
enriched = {"cells": [{"cellId": "OBL-A::C1::op", "obligationId": "OBL-A", "contractId": "C1", "track": "synthetic", "operationId": "op", "operation": {"method": "post", "path": "/ok"}, "classification": "recipe_available_unexercised", "status": "candidate", "executableEligible": True, "recipeExists": True, "fixtureId": "fixture-ok", "selectorObjects": {"payload": {"fromBytes": "PAYLOAD", "encoding": "base64"}}, "linkedRecipe": {"recipeId": "r-a"}}]}
suite, report = build_t3_suite("C1", model, enriched, fixtures, schema, capabilities=["CAP-A"], max_depth=2, max_paths_per_capability=5)
path = freeze_suite(suite, out / "T3-synthetic.json")
loaded = load_frozen_suite(path)
report["freeze"] = {"path": str(path), "loadedCases": len(loaded.cases)}
(out / "synthetic-freeze-report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
print(json.dumps({"cases": len(suite.cases), "loaded": len(loaded.cases), "path": str(path)}, sort_keys=True))

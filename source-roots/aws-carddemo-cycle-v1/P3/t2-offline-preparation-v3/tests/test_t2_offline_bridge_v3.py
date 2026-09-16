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
HARNESS = P3 / "campaign-harness-v3" / "src"
PY = P3 / ".venv-fuzz-preflight" / "bin" / "python"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HARNESS))

from campaign_harness import load_frozen_suite  # noqa: E402
from t2_offline_bridge import (  # noqa: E402
    build_plan,
    generate_t2_offline_suite_for_contract,
    transport_kwargs_to_frozen_request,
    validate_current_registry,
)


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def _schema(required_name: str, typ: str) -> dict:
    return {
        "openapi": "3.1.0",
        "info": {"title": required_name, "version": "1.0"},
        "paths": {
            "/same": {
                "post": {
                    "operationId": f"make{required_name}",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": [required_name],
                                    "properties": {required_name: {"type": typ}},
                                    "additionalProperties": False,
                                }
                            }
                        },
                    },
                    "responses": {"200": {"description": "ok"}, "400": {"description": "bad"}},
                }
            }
        },
    }


class T2OfflinePreparationV3Tests(unittest.TestCase):
    def test_transport_conversion_preserves_query_duplicate_headers_raw_bytes_and_absent_body(self):
        raw = b'{  "z" : [2,1] }'
        item = transport_kwargs_to_frozen_request(
            "CID",
            {"operationId": "op"},
            "case-1",
            {
                "method": "POST",
                "url": "http://127.0.0.1/same?b=2&a=1&b=3",
                "headers": [("X-Frame", "one"), ("X-Frame", "two"), ("Content-Type", "application/json")],
                "data": raw,
            },
            seed=104729,
            direction="positive",
            expected_status=[200],
        )
        self.assertEqual(item["path"], "/same?b=2&a=1&b=3")
        self.assertEqual(item["headers"], [["X-Frame", "one"], ["X-Frame", "two"], ["Content-Type", "application/json"]])
        self.assertEqual(item["body_kind"], "bytes")
        self.assertEqual(base64.b64decode(item["body_b64"]), raw)
        self.assertNotIn("body", item)

        absent = transport_kwargs_to_frozen_request("CID", {"operationId": "getOp"}, "case-2", {"method": "GET", "url": "http://127.0.0.1/empty", "headers": []}, seed=104729, direction="positive", expected_status=[200])
        self.assertEqual(absent["body_kind"], "absent")
        self.assertIsNone(absent["body_b64"])
        empty = transport_kwargs_to_frozen_request("CID", {"operationId": "emptyOp"}, "case-3", {"method": "POST", "url": "http://127.0.0.1/empty", "headers": [], "data": b""}, seed=104729, direction="positive", expected_status=[200])
        self.assertEqual(empty["body_kind"], "bytes")
        self.assertEqual(base64.b64decode(empty["body_b64"]), b"")
        js = transport_kwargs_to_frozen_request("CID", {"operationId": "jsonOp"}, "case-4", {"method": "POST", "url": "http://127.0.0.1/empty", "headers": [], "json": {}}, seed=104729, direction="positive", expected_status=[200])
        self.assertEqual(js["body_kind"], "json")
        self.assertEqual(base64.b64decode(js["body_b64"]), b"{}")

    def test_generator_reads_original_openapi_per_contract_not_registry_synthetic_or_path_map(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            a = tmp / "a-openapi.json"
            b = tmp / "b-openapi.json"
            _write_json(a, _schema("alpha", "string"))
            _write_json(b, _schema("beta", "integer"))
            cfg = {
                "authorization": {"officialCampaignsStarted": False, "externalT1SendAuthorized": False, "campaignAuthorized": False},
                "contracts": {
                    "count": 2,
                    "operationsTotal": 2,
                    "contracts": [
                        {"contractId": "A", "operationCount": 1, "source": {"path": str(a), "bytes": a.stat().st_size, "sha256": "filled"}, "operations": [{"method": "POST", "path": "/same", "operationId": "makealpha", "documentedResponses": ["200", "400"]}]},
                        {"contractId": "B", "operationCount": 1, "source": {"path": str(b), "bytes": b.stat().st_size, "sha256": "filled"}, "operations": [{"method": "POST", "path": "/same", "operationId": "makebeta", "documentedResponses": ["200", "400"]}]},
                    ],
                },
            }
            import hashlib
            for c in cfg["contracts"]["contracts"]:
                p = Path(c["source"]["path"])
                c["source"]["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
            report_a = generate_t2_offline_suite_for_contract(cfg, "A", tmp / "out-a", seeds=[104729], directions=["positive"], max_examples_per_direction=4)
            report_b = generate_t2_offline_suite_for_contract(cfg, "B", tmp / "out-b", seeds=[104729], directions=["positive"], max_examples_per_direction=4)
            self.assertEqual(report_a["contractId"], "A")
            self.assertEqual(report_b["contractId"], "B")
            self.assertEqual(report_a["originalContractPath"], str(a))
            self.assertEqual(report_b["originalContractPath"], str(b))
            frozen_a = json.loads((tmp / "out-a" / "frozen-t2-requests.json").read_text())
            frozen_b = json.loads((tmp / "out-b" / "frozen-t2-requests.json").read_text())
            keys_a = {tuple(sorted(json.loads(base64.b64decode(r["body_b64"])).keys())) for r in frozen_a["requests"] if r["body_kind"] in {"bytes", "json"} and r["body_b64"]}
            keys_b = {tuple(sorted(json.loads(base64.b64decode(r["body_b64"])).keys())) for r in frozen_b["requests"] if r["body_kind"] in {"bytes", "json"} and r["body_b64"]}
            self.assertIn(("alpha",), keys_a)
            self.assertIn(("beta",), keys_b)
            self.assertNotIn(("syntheticCase",), keys_a | keys_b)
            suite_a = load_frozen_suite(tmp / "out-a" / "T2-suite.json")
            self.assertGreater(len(suite_a.cases), 0)
            self.assertTrue(all(case.request.path == "/same" for case in suite_a.cases))

    def test_closed_empty_object_schema_stays_json_empty_object_not_absent(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            schema = {
                "openapi": "3.1.0",
                "info": {"title": "closed", "version": "1.0"},
                "paths": {"/closed": {"post": {"operationId": "closed", "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "additionalProperties": False}}}}, "responses": {"200": {"description": "ok"}, "400": {"description": "bad"}}}}},
            }
            p = tmp / "closed.json"
            _write_json(p, schema)
            import hashlib
            cfg = {"authorization": {"officialCampaignsStarted": False, "externalT1SendAuthorized": False, "campaignAuthorized": False}, "contracts": {"count": 1, "operationsTotal": 1, "contracts": [{"contractId": "CLOSED", "operationCount": 1, "source": {"path": str(p), "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}, "operations": [{"method": "POST", "path": "/closed", "operationId": "closed", "documentedResponses": ["200", "400"]}]}]}}
            generate_t2_offline_suite_for_contract(cfg, "CLOSED", tmp / "out", seeds=[104729], directions=["positive"], max_examples_per_direction=2)
            requests = json.loads((tmp / "out" / "frozen-t2-requests.json").read_text())["requests"]
            self.assertTrue(requests)
            self.assertTrue(any(r["body_kind"] in {"bytes", "json"} and base64.b64decode(r["body_b64"]) == b"{}" for r in requests))

    def test_cli_dry_run_validates_current_registry_and_blocks_official_generation(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cfg = P3 / "campaign-configuration-v2" / "campaign-config-v2.json"
            result = subprocess.run([str(PY), str(ROOT / "t2_offline_cli.py"), "dry-run", "--config", str(cfg), "--output", str(tmp / "dry")], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads(result.stdout)
            self.assertFalse(summary["officialCampaign"])
            self.assertEqual(summary["registryValidation"]["contractCount"], 7)
            self.assertEqual(summary["registryValidation"]["operationCount"], 21)
            self.assertEqual(summary["policy"]["seeds"], [104729, 130363, 155921])
            self.assertEqual(summary["policy"]["perOperationPerSeed"], {"positive": 50, "negative": 50, "total": 100})
            self.assertTrue((tmp / "dry" / "plan.json").exists())
            bad = subprocess.run([str(PY), str(ROOT / "t2_offline_cli.py"), "official-generate", "--config", str(cfg), "--output", str(tmp / "official")], capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("official release is gate-closed", bad.stdout + bad.stderr)


if __name__ == "__main__":
    unittest.main()

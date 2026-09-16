import base64
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "campaign-harness-v2" / "src"))

from campaign_harness import HttpRequestSpec, Suite, UnionBuilder, freeze_suite, load_frozen_suite  # noqa: E402
from suite_adapters import (  # noqa: E402
    AdapterError,
    ContractSource,
    build_operation_inventory,
    import_t1_preserved_response,
    import_t2_frozen_requests,
    import_t3_external_paths,
    pin_contract_sources,
)


class SuiteAdapterTests(unittest.TestCase):
    def test_t1_preserves_original_response_and_never_repairs_invalid_or_missing_cases(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            response = root / "t1-response.txt"
            raw = "prefix not json\n```json\n[{\"id\": \"a\", \"operationId\": \"post\", \"method\": \"POST\", \"path\": \"/p\", \"body\": {}}, {\"id\": \"no-request\"}, {\"id\": \"bad-path\", \"method\": \"POST\", \"path\": \"p\"}]\n```\ntrailing"
            response.write_text(raw, encoding="utf-8")
            suite, report = import_t1_preserved_response("C-1", response, suite_id="T1", default_resource_package_id="pkg-a")
            self.assertEqual([c.case_id for c in suite.cases], ["T1-C-1-a"])
            self.assertEqual(suite.cases[0].request.body_kind, "json")
            self.assertEqual(base64.b64decode(suite.cases[0].request.body_b64), b"{}")
            self.assertEqual(report["source_sha256"], __import__("hashlib").sha256(raw.encode()).hexdigest())
            self.assertEqual(report["raw_response"], raw)
            self.assertEqual([x["classification"] for x in report["rejected"]], ["not_mapped_missing_request", "invalid_request"])
            self.assertFalse(report["llm_called"])
            self.assertFalse(report["repaired_omissions"])

    def test_t2_imports_frozen_requests_offline_preserving_absent_empty_and_json_object(self):
        frozen = {
            "requests": [
                {"id": "absent", "operationId": "op", "method": "POST", "path": "/x", "headers": [["X-Dup", "1"], ["X-Dup", "2"]], "body": {"kind": "absent"}},
                {"id": "empty", "operationId": "op", "method": "POST", "path": "/x", "body": {"kind": "bytes", "base64": ""}},
                {"id": "obj", "operationId": "op", "method": "POST", "path": "/x", "body": {"kind": "json", "value": {}}},
                {"id": "dup", "operationId": "op", "method": "POST", "path": "/x", "body": {"kind": "json", "value": {}}},
                {"id": "invalid", "operationId": "op", "method": "POST", "path": "x", "body": {"kind": "absent"}},
            ]
        }
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "frozen.json"
            path.write_text(json.dumps(frozen), encoding="utf-8")
            suite, report = import_t2_frozen_requests("C-2", path, suite_id="T2", default_resource_package_id="pkg-a")
            self.assertEqual([c.request.body_kind for c in suite.cases], ["absent", "bytes", "json", "json"])
            self.assertEqual(suite.cases[0].request.headers, (("X-Dup", "1"), ("X-Dup", "2")))
            self.assertEqual(base64.b64decode(suite.cases[2].request.body_b64), b"{}")
            union, ledger = UnionBuilder().build([suite])
            self.assertLess(len(union.cases), len(suite.cases))
            self.assertTrue(any(row["action"] == "duplicate_merged" for row in ledger))
            self.assertEqual(report["rejected"][0]["classification"], "invalid_request")
            self.assertFalse(report["http_called"])

    def test_t3_accepts_external_business_request_paths_but_blocks_abstract_ids_without_mapping(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = root / "paths.json"
            paths.write_text(json.dumps({"paths": [{"id": "p1", "operationId": "post", "method": "POST", "path": "/posting", "body": {"kind": "json", "value": {}}}, {"id": "abstract-only", "transitionId": "T-post-valid"}]}), encoding="utf-8")
            suite, report = import_t3_external_paths("C-3", paths, suite_id="T3", default_resource_package_id="pkg-a")
            self.assertEqual([c.case_id for c in suite.cases], ["T3-C-3-p1"])
            self.assertEqual(report["rejected"][0]["classification"], "blocked_missing_business_request_mapping")
            self.assertIn("transitionId", report["rejected"][0]["input_keys"])
            self.assertFalse(report["oracle_accessed"])

    def test_inventory_counts_real_operations_from_contracts_and_pins_hashes(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            c1 = root / "c1.yaml"
            c2 = root / "c2.yaml"
            c1.write_text("openapi: 3.1.0\npaths:\n  /a:\n    post:\n      operationId: a\n      responses:\n        '200': {description: ok}\n", encoding="utf-8")
            c2.write_text("openapi: 3.1.0\npaths:\n  /b:\n    post:\n      operationId: b\n      responses:\n        '200': {description: ok}\n  /c:\n    get:\n      operationId: c\n      responses:\n        '204': {description: ok}\n", encoding="utf-8")
            sources = [ContractSource("C1", c1), ContractSource("C2", c2)]
            pins = pin_contract_sources(sources)
            inventory = build_operation_inventory(sources)
            self.assertEqual(inventory["contractCount"], 2)
            self.assertEqual(inventory["operationCount"], 3)
            self.assertEqual([op["operationId"] for op in inventory["operations"]], ["a", "b", "c"])
            self.assertEqual(pins[0]["bytes"], c1.stat().st_size)
            self.assertEqual(pins[0]["sha256"], __import__("hashlib").sha256(c1.read_bytes()).hexdigest())

    def test_imported_suite_freezes_loads_and_maps_to_harness_case_suite(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            t2 = root / "frozen.json"
            t2.write_text(json.dumps({"requests": [{"id": "r1", "method": "POST", "path": "/x", "body": {"kind": "absent"}}]}), encoding="utf-8")
            suite, _ = import_t2_frozen_requests("C", t2, suite_id="T2", default_resource_package_id="pkg-a")
            self.assertIsInstance(suite, Suite)
            self.assertIsInstance(suite.cases[0].request, HttpRequestSpec)
            frozen = freeze_suite(suite, root / "suite.json")
            loaded = load_frozen_suite(frozen)
            self.assertEqual(loaded.cases[0].request.body_kind, "absent")


if __name__ == "__main__":
    unittest.main()

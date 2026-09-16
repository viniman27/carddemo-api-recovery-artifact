import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
CYCLE = ROOT.parent
import sys
sys.path.insert(0, str(ROOT))

from p2c_facade import ContractFacade, FacadeServer, load_contract, load_operation_index, sample_request_for


class RemainingClosureTests(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp(prefix="p2c-closure-"))
        self.registry = CYCLE / "P3" / "technical-packages-v3-argument" / "registry.json"

    def test_e1_1_parameter_length_is_transported_as_runtime_comp_linkage(self):
        facade = ContractFacade("E1-1", self.out, self.registry)
        req = sample_request_for("E1-1", "interest", self.registry)
        req["parameterDate"] = "INPUTCHECK"
        req["parameterLength"] = 7
        result = facade.execute("interest", req)
        audit = json.loads(Path(result["audit_path"]).read_text())
        linkage = audit["request_materialization"]["linkage"]
        self.assertEqual(linkage["parameterLength"], 7)
        self.assertEqual(linkage["parameterValueHex"], b"INPUTCHECK".hex())
        self.assertEqual(linkage["capturedRuntimeLinkageHex"][4:], b"INPUTCHECK".hex())
        self.assertEqual(linkage["capturedRuntimeParameterLength"], 7)
        self.assertEqual(linkage["capturedRuntimeParameterLengthCompHex"], linkage["parameterLengthCompHex"])

    def test_unknown_output_binding_token_is_rejected_before_cobol(self):
        facade = ContractFacade("E1-1", self.out, self.registry)
        req = sample_request_for("E1-1", "interest", self.registry)
        req["outputTransactionFile"] = "p3:interest:UNKNOWN"
        with self.assertRaises(ValueError):
            facade.execute("interest", req)
        self.assertFalse((self.out / "p2b-runs").exists())

    def test_repeated_request_uses_fresh_package_with_same_selected_bytes(self):
        facade = ContractFacade("E1-3", self.out, self.registry)
        req = sample_request_for("E1-3", "posting", self.registry)
        first = facade.execute("posting", req)
        second = facade.execute("posting", req)
        a1 = json.loads(Path(first["audit_path"]).read_text())["request_materialization"]
        a2 = json.loads(Path(second["audit_path"]).read_text())["request_materialization"]
        self.assertNotEqual(a1["package"], a2["package"])
        self.assertEqual({k: v["sha256"] for k, v in a1["files"].items()}, {k: v["sha256"] for k, v in a2["files"].items()})
        self.assertEqual({k: v["bytes"] for k, v in a1["files"].items()}, {k: v["bytes"] for k, v in a2["files"].items()})

    def test_server_instance_uses_exact_contract_paths_without_public_namespace(self):
        server = FacadeServer(contract_id="E1-2", output_root=self.out, registry=self.registry)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            exact_path = load_operation_index(load_contract("E1-2"))["generateInterestTransactions"]["path"]
            req_body = sample_request_for("E1-2", "interest", self.registry)
            raw = json.dumps(req_body).encode()
            with urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{server.port}{exact_path}", data=raw, headers={"content-type":"application/json"}, method="POST"), timeout=180) as resp:
                body = json.loads(resp.read())
                self.assertNotIn("audit_path", body)
                ContractFacade("E1-2", self.out, self.registry).validate_response("interest", str(resp.status), body)
            with self.assertRaises(urllib.error.HTTPError) as cm:
                urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{server.port}/E1-2{exact_path}", data=raw, headers={"content-type":"application/json"}, method="POST"), timeout=30)
            self.assertEqual(cm.exception.code, 404)
        finally:
            server.shutdown(); thread.join(timeout=5)

    def test_malformed_request_returns_contract_400_when_available_or_500_schema_valid(self):
        for cid in ["E1-1", "E1-2", "E1-3"]:
            server = FacadeServer(contract_id=cid, output_root=self.out / cid, registry=self.registry)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                contract = load_contract(cid)
                path = load_operation_index(contract)["postDailyTransactions"]["path"]
                try:
                    urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{server.port}{path}", data=b'{"dailyTransactions": ["not-base64"]}', headers={"content-type":"application/json"}, method="POST"), timeout=30)
                    self.fail("malformed request unexpectedly returned 2xx")
                except urllib.error.HTTPError as exc:
                    payload = json.loads(exc.read())
                    self.assertIn(exc.code, [400, 500])
                    status_key = str(exc.code) if str(exc.code) in load_operation_index(contract)["postDailyTransactions"]["operation"]["responses"] else "500"
                    ContractFacade(cid, self.out / cid, self.registry).validate_response("posting", status_key, payload)
            finally:
                server.shutdown(); thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()

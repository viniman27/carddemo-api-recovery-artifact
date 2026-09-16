import base64
import json
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
CYCLE = ROOT.parent

import sys
sys.path.insert(0, str(ROOT))

from p2c_facade import ContractFacade, FacadeServer, load_contract, load_operation_index, sample_request_for


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


class ContractFacadeTests(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp(prefix="p2c-test-"))
        self.registry = CYCLE / "P3" / "technical-packages-v3-argument" / "registry.json"

    def test_all_three_zero_shot_contracts_expose_three_executable_operations(self):
        for cid in ["E1-1", "E1-2", "E1-3"]:
            contract = load_contract(cid)
            index = load_operation_index(contract)
            self.assertEqual(set(index), {"postDailyTransactions", "generateInterestTransactions", "generateTransactionReport"})
            for op in index.values():
                self.assertIn(op["track"], {"posting", "interest", "reporting"})
                self.assertTrue(op["path"].startswith("/"))

    def test_schema_validation_uses_original_refs_and_rejects_extra_fields(self):
        facade = ContractFacade("E1-3", self.out, self.registry)
        valid = sample_request_for("E1-3", "posting", self.registry)
        facade.validate_request("postDailyTransactions", valid)
        invalid = dict(valid)
        invalid["inventedReset"] = True
        with self.assertRaises(jsonschema.ValidationError):
            facade.validate_request("postDailyTransactions", invalid)

    def test_posting_empty_array_materializes_zero_byte_daily_file(self):
        facade = ContractFacade("E1-1", self.out, self.registry)
        req = sample_request_for("E1-1", "posting", self.registry)
        req["dailyTransactions"] = []
        result = facade.execute("posting", req)
        audit = json.loads(Path(result["audit_path"]).read_text())
        daily = audit["request_materialization"]["files"]["DALYTRAN"]
        self.assertEqual(daily["bytes"], 0)
        self.assertEqual(Path(daily["path"]).read_bytes(), b"")

    def test_posting_raw_request_bytes_are_the_materialized_daily_file(self):
        facade = ContractFacade("E1-3", self.out, self.registry)
        raw = b"Z" * 350
        req = sample_request_for("E1-3", "posting", self.registry)
        req["dailyTransactions"] = [_b64(raw)]
        result = facade.execute("posting", req)
        audit = json.loads(Path(result["audit_path"]).read_text())
        daily_path = Path(audit["request_materialization"]["files"]["DALYTRAN"]["path"])
        self.assertEqual(daily_path.read_bytes(), raw)

    def test_interest_parameter_prefix_becomes_exact_parmfile_bytes(self):
        facade = ContractFacade("E1-1", self.out, self.registry)
        req = sample_request_for("E1-1", "interest", self.registry)
        req["parameterDate"] = "INPUTCHECK"
        result = facade.execute("interest", req)
        audit = json.loads(Path(result["audit_path"]).read_text())
        parm = Path(audit["request_materialization"]["files"]["PARMFILE"]["path"])
        self.assertEqual(parm.read_bytes(), b"INPUTCHECK")

    def test_reporting_request_materializes_dateparm_and_tranfile_exactly(self):
        facade = ContractFacade("E1-3", self.out, self.registry)
        tx = b"T" * 350
        dp = b"2020-01-01 2020-12-31".ljust(80, b"X")
        req = sample_request_for("E1-3", "reporting", self.registry)
        req["transactions"] = [_b64(tx)]
        req["dateParameterRecords"] = [_b64(dp)]
        result = facade.execute("reporting", req)
        audit = json.loads(Path(result["audit_path"]).read_text())
        mat = audit["request_materialization"]["files"]
        self.assertEqual(Path(mat["TRANFILE"]["path"]).read_bytes(), tx)
        self.assertEqual(Path(mat["DATEPARM"]["path"]).read_bytes(), dp)

    def test_http_server_receives_real_loopback_requests_on_contract_paths(self):
        server = FacadeServer(contract_id="E1-2", output_root=self.out, registry=self.registry)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            facade = ContractFacade("E1-2", self.out, self.registry)
            path = load_operation_index(load_contract("E1-2"))["generateInterestTransactions"]["path"]
            req_body = sample_request_for("E1-2", "interest", self.registry)
            req_body["idPrefix"] = "INPUTCHECK"
            raw_body = json.dumps(req_body).encode()
            req = urllib.request.Request(
                f"http://127.0.0.1:{server.port}{path}",
                data=raw_body,
                headers={"content-type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read())
                self.assertIn(resp.status, [200, 500, 503])
                ContractFacade("E1-2", self.out, self.registry).validate_response("interest", "200", body)
                self.assertNotIn("audit_path", body)
            http_log = json.loads((self.out / "http-requests.jsonl").read_text().splitlines()[-1])
            self.assertEqual(http_log["method"], "POST")
            self.assertEqual(http_log["contract_id"], "E1-2")
            self.assertEqual(http_log["request_body_sha256"], __import__("hashlib").sha256(raw_body).hexdigest())
        finally:
            server.shutdown()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()

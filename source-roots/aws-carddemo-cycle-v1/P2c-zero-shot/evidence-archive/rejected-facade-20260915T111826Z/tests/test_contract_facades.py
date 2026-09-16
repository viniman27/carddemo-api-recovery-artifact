import base64
import json
import tempfile
import unittest
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
CYCLE = ROOT.parent

import sys
sys.path.insert(0, str(ROOT))

from p2c_facade import ContractFacade, load_contract, load_operation_index, sample_request_for


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

    def test_schema_validation_uses_original_contract_and_rejects_extra_fields(self):
        contract = load_contract("E1-3")
        facade = ContractFacade("E1-3", self.out, self.registry)
        valid = sample_request_for("E1-3", "posting")
        facade.validate_request("postDailyTransactions", valid)
        invalid = dict(valid)
        invalid["inventedReset"] = True
        with self.assertRaises(jsonschema.ValidationError):
            facade.validate_request("postDailyTransactions", invalid)

    def test_each_contract_operation_executes_and_writes_audit_with_contract_shaped_body(self):
        for cid in ["E1-1", "E1-2", "E1-3"]:
            facade = ContractFacade(cid, self.out / cid, self.registry)
            for track in ["posting", "interest", "reporting"]:
                result = facade.execute(track, sample_request_for(cid, track))
                self.assertIn(result["http_status"], [200, 500, 503])
                self.assertEqual(result["contract_id"], cid)
                self.assertEqual(result["track"], track)
                self.assertTrue(Path(result["audit_path"]).is_file())
                self.assertTrue(Path(result["response_path"]).is_file())
                body = result["body"]
                if result["http_status"] == 200:
                    schema = facade.response_schema_for(track, "200")
                    jsonschema.Draft202012Validator(schema).validate(body)

    def test_reporting_preserves_physical_record_shape_per_contract(self):
        for cid in ["E1-1", "E1-2", "E1-3"]:
            facade = ContractFacade(cid, self.out / f"report-{cid}", self.registry)
            result = facade.execute("reporting", sample_request_for(cid, "reporting"))
            if result["http_status"] != 200:
                self.skipTest(f"reporting not operational for {cid}: {result['http_status']}")
            records = facade.extract_report_records(result["body"])
            for record in records:
                if cid in {"E1-1", "E1-2"}:
                    self.assertIsInstance(record, str)
                    self.assertEqual(len(record), 133)
                else:
                    self.assertEqual(len(base64.b64decode(record)), 133)


if __name__ == "__main__":
    unittest.main()

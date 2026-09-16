import json
import sys
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, RefResolver

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import p2c_facade


def validate_response_against_contract(contract_id: str, track: str, status: int, body: dict) -> None:
    spec = yaml.safe_load(p2c_facade.CONTRACTS[contract_id].original_path.read_text())
    operation = spec["paths"][p2c_facade.CONTRACTS[contract_id].paths[track]]["post"]
    response = operation["responses"][str(status)]
    if "$ref" in response:
        cur = spec
        for part in response["$ref"].removeprefix("#/").split("/"):
            cur = cur[part]
        response = cur
    schema = response["content"]["application/json"]["schema"]
    errors = [e.message for e in Draft202012Validator(schema, resolver=RefResolver.from_schema(spec)).iter_errors(body)]
    if errors:
        raise AssertionError(errors)


class E22IntegrationDefectRegressionTests(unittest.TestCase):
    def test_rejected_posting_transaction_preserves_required_processing_timestamp(self):
        p2b_body = {
            "progress": {"value": {"processedRecordCount": 1, "preliminaryRejectCount": 1}},
            "outputs": {"items": []},
            "rejections": {"items": [{"candidate": {
                "transactionId": "TEST000000000001",
                "typeCode": "01",
                "categoryCode": "0001",
                "source": "TEST      ",
                "description": "LOCAL SYNTHETIC FIXTURE".ljust(100),
                "amount": "00000002500",
                "merchantId": "000000001",
                "merchantName": "TEST MERCHANT".ljust(50),
                "merchantCity": "TEST CITY".ljust(50),
                "merchantPostalText": "0000000000",
                "cardReference": "0000000000000001",
                "originalTimestamp": "2025-01-01-00.00.00.000000",
                "suppliedProcessingTimestamp": "2025-01-01-00.00.00.000000",
            }, "reason": "100", "description": "INVALID CARD NUMBER FOUND".ljust(76)}]},
        }
        body = p2c_facade.project_response("E2-2", "posting", 200, p2b_body, [], {"RESP": {"program_exit": 4}})
        rejected_tx = body["rejections"][0]["transaction"]
        self.assertEqual(rejected_tx["processingTimestamp"], "2025-01-01-00.00.00.000000")
        self.assertNotIn("suppliedProcessingTimestamp", rejected_tx)
        validate_response_against_contract("E2-2", "posting", 200, body)

    def test_reporting_abort_records_reached_cobol_and_exact_precondition_failure(self):
        result = p2c_facade.execute("E2-2", "reporting", p2c_facade.sample_request("E2-2", "reporting"))
        self.assertEqual(result["status"], 500)
        audit = json.loads(Path(result["p2bAuditPath"]).read_text())
        self.assertTrue(audit["RESP"]["reached_cobol"])
        events = audit["FAIL"]["events"]
        self.assertTrue(any(e.get("kind") == "local_compatibility_abort" for e in events))
        preconditions = [e for e in events if e.get("kind") == "cobol_precondition_failure"]
        self.assertTrue(preconditions, events)
        self.assertEqual(preconditions[-1]["lookup"], "CARDXREF")
        self.assertEqual(preconditions[-1]["key"], "0000000000000001")
        self.assertEqual(preconditions[-1]["fileStatus"], "23")
        validate_response_against_contract("E2-2", "reporting", 500, result["body"])


if __name__ == "__main__":
    unittest.main()

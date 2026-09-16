import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import p2c_facade

BINDINGS = {
    "crossReferences": "p3-local-technical-fixture-selection:crossReferences",
    "accounts": "p3-local-technical-fixture-selection:accounts",
    "categoryBalances": "p3-local-technical-fixture-selection:categoryBalances",
    "transactionOutput": "p3-local-technical-fixture-selection:transactionOutput",
    "rejectionOutput": "p3-local-technical-fixture-selection:rejectionOutput",
    "disclosureGroups": "p3-local-technical-fixture-selection:disclosureGroups",
    "transactionTypes": "p3-local-technical-fixture-selection:transactionTypes",
    "transactionCategories": "p3-local-technical-fixture-selection:transactionCategories",
    "reportOutput": "p3-local-technical-fixture-selection:reportOutput",
}

TX = {
    "transactionId": "TEST000000000001",
    "typeCode": "01",
    "categoryCode": "0001",
    "source": "TEST",
    "description": "LOCAL SYNTHETIC FIXTURE",
    "amount": 25.00,
    "merchantId": "000000001",
    "merchantName": "TEST MERCHANT",
    "merchantCity": "TEST CITY",
    "merchantZip": "0000000000",
    "cardNumber": "0000000000000001",
    "originalTimestamp": "2025-01-01-00.00.00.000000",
    "processingTimestamp": "2025-01-01-00.00.00.000000",
    "filler": "ORIGINAL-FILLER-1234",
}
TX_INT = dict(TX, categoryCode=1, merchantId=1)
DATE80 = "2025-01-01 2025-12-31".ljust(80)

class FacadeContractTests(unittest.TestCase):
    def test_contract_paths_are_loaded_from_originals(self):
        self.assertEqual(p2c_facade.CONTRACTS["E2-1"].paths["posting"], "/transaction-postings")
        self.assertEqual(p2c_facade.CONTRACTS["E2-2"].paths["interest"], "/interest-generation-runs")
        self.assertEqual(p2c_facade.CONTRACTS["E2-3"].paths["reporting"], "/transaction-report-runs")

    def test_original_jsonschema_allows_parameter_length_and_rejects_bad_shape(self):
        p2c_facade.validate_request("E2-2", "interest", {
            "bindings": {k: BINDINGS[k] for k in ["categoryBalances","crossReferences","accounts","disclosureGroups","transactionOutput"]},
            "parameterDate": "INPUTCHECK",
            "parameterLength": 10,
        })
        with self.assertRaises(p2c_facade.TransportRejection):
            p2c_facade.validate_request("E2-3", "interest", {"transactionIdPrefix": "short"})

    def test_rejects_binding_prefix_instead_of_ignoring_it(self):
        body = {"bindings": {k: BINDINGS[k] for k in ["crossReferences","accounts","categoryBalances","transactionOutput","rejectionOutput"]}, "transactions": []}
        body["bindings"]["accounts"] = "not-local:accounts"
        with self.assertRaises(p2c_facade.TransportRejection):
            p2c_facade.validate_request("E2-2", "posting", body)

    def test_materialize_empty_transactions_writes_empty_dalytran(self):
        result = p2c_facade.execute("E2-1", "posting", {"dailyTransactions": []})
        audit = json.loads(Path(result["p2bAuditPath"]).read_text())
        self.assertEqual((Path(audit["INV"]["workdir"]) / "DALYTRAN").read_bytes(), b"")

    def test_materialize_interest_prefix_writes_exact_parmfile(self):
        result = p2c_facade.execute("E2-3", "interest", {"transactionIdPrefix": "INPUTCHECK"})
        audit = json.loads(Path(result["p2bAuditPath"]).read_text())
        self.assertEqual((Path(audit["INV"]["workdir"]) / "PARMFILE").read_bytes(), b"INPUTCHECK")

    def test_http_dispatch_executes_real_loopback_route(self):
        status, body, evidence = p2c_facade.http_roundtrip("E2-3", "interest", {"transactionIdPrefix": "INPUTCHECK"})
        self.assertIn(status, {200, 500, 503})
        self.assertEqual(evidence["requestBody"], {"transactionIdPrefix": "INPUTCHECK"})
        audit = json.loads(Path(evidence["p2bAuditPath"]).read_text())
        self.assertEqual((Path(audit["INV"]["workdir"]) / "PARMFILE").read_bytes(), b"INPUTCHECK")

if __name__ == "__main__":
    unittest.main()

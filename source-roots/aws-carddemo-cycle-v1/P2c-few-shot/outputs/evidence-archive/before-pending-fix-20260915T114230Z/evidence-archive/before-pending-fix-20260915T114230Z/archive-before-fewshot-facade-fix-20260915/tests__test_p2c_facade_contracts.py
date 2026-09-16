import importlib.util
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
    "filler": ""
}
TX_INT = dict(TX, categoryCode=1, merchantId=1)
DATE80 = "2025-01-01 2025-12-31".ljust(80)

class FacadeContractTests(unittest.TestCase):
    def test_contract_paths_are_loaded_from_originals(self):
        self.assertEqual(p2c_facade.CONTRACTS["E2-1"].paths["posting"], "/transaction-postings")
        self.assertEqual(p2c_facade.CONTRACTS["E2-2"].paths["interest"], "/interest-generation-runs")
        self.assertEqual(p2c_facade.CONTRACTS["E2-3"].paths["reporting"], "/transaction-report-runs")

    def test_e2_1_structural_requests_validate_without_bindings(self):
        p2c_facade.validate_request("E2-1", "posting", {"dailyTransactions": [TX]})
        p2c_facade.validate_request("E2-1", "interest", {"transactionIdPrefix": "2022071800"})
        p2c_facade.validate_request("E2-1", "reporting", {"transactions": [TX], "dateParameterRecords": ["2025-01-01 2025-12-31"]})

    def test_e2_2_structural_requests_validate_with_local_binding_tokens(self):
        p2c_facade.validate_request("E2-2", "posting", {"bindings": {k: BINDINGS[k] for k in ["crossReferences","accounts","categoryBalances","transactionOutput","rejectionOutput"]}, "transactions": [TX_INT]})
        p2c_facade.validate_request("E2-2", "interest", {"bindings": {k: BINDINGS[k] for k in ["categoryBalances","crossReferences","accounts","disclosureGroups","transactionOutput"]}, "parameterDate": "2022071800"})
        p2c_facade.validate_request("E2-2", "reporting", {"bindings": {k: BINDINGS[k] for k in ["crossReferences","transactionTypes","transactionCategories","reportOutput"]}, "transactions": [TX_INT], "dateParameterRecords": ["2025-01-01 2025-12-31"]})

    def test_e2_3_enforces_exact_prefix_and_dateparm_widths(self):
        p2c_facade.validate_request("E2-3", "interest", {"transactionIdPrefix": "2022071800"})
        p2c_facade.validate_request("E2-3", "reporting", {"transactions": [TX_INT], "dateParameterRecords": [DATE80]})
        with self.assertRaises(p2c_facade.TransportRejection):
            p2c_facade.validate_request("E2-3", "interest", {"transactionIdPrefix": "short"})
        with self.assertRaises(p2c_facade.TransportRejection):
            p2c_facade.validate_request("E2-3", "reporting", {"transactions": [], "dateParameterRecords": ["short"]})

    def test_response_projection_uses_contract_specific_names(self):
        p2b_body = {"track":"interest", "outputs": {"availability": "available", "items": [TX]}}
        self.assertIn("transactions", p2c_facade.project_response("E2-1", "interest", 200, p2b_body, []))
        self.assertIn("generatedTransactions", p2c_facade.project_response("E2-2", "interest", 200, p2b_body, []))
        self.assertIn("transactions", p2c_facade.project_response("E2-3", "interest", 200, p2b_body, []))

if __name__ == "__main__":
    unittest.main()

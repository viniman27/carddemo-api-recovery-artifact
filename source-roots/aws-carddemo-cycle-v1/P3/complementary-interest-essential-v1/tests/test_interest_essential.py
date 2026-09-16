import json
import os
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from essential_interest import InterestCase, money_cents_text, run_interest_case, source_monthly_interest


class InterestEssentialTests(unittest.TestCase):
    def test_independent_source_formula_and_cents_text_known_wrong_guard(self):
        self.assertEqual(Decimal("12.50"), source_monthly_interest("1500.00", "10.00"))
        self.assertNotEqual(Decimal("125.00"), source_monthly_interest("1500.00", "10.00"))
        self.assertEqual("00000001250", money_cents_text(Decimal("12.50")))

    def test_nonzero_zero_specific_and_default_rate_partitions_have_real_file_effects(self):
        case = InterestCase(
            case_id="rates-specific-default-zero",
            parm_date="2026091600",
            accounts=[
                {"acct":"00000000001", "group":"STANDARD", "balance":"500.00"},
                {"acct":"00000000002", "group":"ZERORATE", "balance":"700.00"},
                {"acct":"00000000003", "group":"MISSING", "balance":"1000.00"},
            ],
            xrefs=[
                {"card":"4111111111111111", "acct":"00000000001"},
                {"card":"4222222222222222", "acct":"00000000002"},
                {"card":"4333333333333333", "acct":"00000000003"},
            ],
            disc=[
                {"group":"STANDARD", "type":"01", "cat":"0005", "rate":"12.00"},
                {"group":"ZERORATE", "type":"01", "cat":"0005", "rate":"0.00"},
                {"group":"DEFAULT", "type":"01", "cat":"0005", "rate":"6.00"},
            ],
            balances=[
                {"acct":"00000000001", "type":"01", "cat":"0005", "balance":"500.00"},
                {"acct":"00000000002", "type":"01", "cat":"0005", "balance":"700.00"},
                {"acct":"00000000003", "type":"01", "cat":"0005", "balance":"1000.00"},
            ],
        )
        result = run_interest_case(case)
        self.assertEqual(200, result["status"], result)
        self.assertEqual([], result["checks"]["failures"])
        self.assertEqual(["00000000500", "00000000500"], [x["amount"] for x in result["observedTransactions"]])
        self.assertEqual(["4111111111111111", "4333333333333333"], [x["cardReference"] for x in result["observedTransactions"]])
        self.assertEqual("available", result["physicalInputs"]["XREFFILE.1"]["before"]["classification"])
        self.assertTrue(result["fileEffects"]["TRANSACT"]["changed"])
        self.assertTrue(result["fileEffects"]["ACCTFILE"]["changed"])
        self.assertEqual("00000000500", result["accountDeltas"]["00000000001"]["deltaCentsText"])
        # Source EOF limitation: final account is not rewritten after its generated interest.
        self.assertEqual("00000000000", result["accountDeltas"]["00000000003"]["deltaCentsText"])
        self.assertEqual("source_eof_final_account_not_rewritten", result["accountDeltas"]["00000000003"]["partition"])

    def test_single_final_account_eof_partition_writes_transaction_but_not_account_update(self):
        case = InterestCase(
            case_id="single-final-eof",
            parm_date="2026091600",
            accounts=[{"acct":"00000000009", "group":"STANDARD", "balance":"1200.00"}],
            xrefs=[{"card":"4999999999999999", "acct":"00000000009"}],
            disc=[{"group":"STANDARD", "type":"01", "cat":"0005", "rate":"12.00"}],
            balances=[{"acct":"00000000009", "type":"01", "cat":"0005", "balance":"1200.00"}],
        )
        result = run_interest_case(case)
        self.assertEqual([], result["checks"]["failures"])
        self.assertEqual(["00000001200"], [x["amount"] for x in result["observedTransactions"]])
        self.assertTrue(result["fileEffects"]["TRANSACT"]["changed"])
        self.assertEqual("00000000000", result["accountDeltas"]["00000000009"]["deltaCentsText"])
        self.assertEqual("source_eof_final_account_not_rewritten", result["accountDeltas"]["00000000009"]["partition"])


if __name__ == "__main__":
    unittest.main()

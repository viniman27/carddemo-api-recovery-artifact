import base64
import json
import tempfile
import unittest
from pathlib import Path

from scripts.t3_binding_amendment import amend_body, amend_selected_suites


class BindingAmendmentTests(unittest.TestCase):
    def test_e1_zero_shot_dd_names_become_p3_track_tokens(self):
        body = {
            "transactionFile": "TRANFILE",
            "crossReferenceFile": "XREFFILE",
            "accountFile": "ACCTFILE",
            "categoryBalanceFile": "TCATBALF",
            "rejectFile": "DALYREJS",
            "dailyTransactions": [{"recordBase64": "AA=="}],
        }
        amended, changes = amend_body("E1-1", "posting", body)
        self.assertEqual(amended["transactionFile"], "p3:posting:TRANFILE")
        self.assertEqual(amended["crossReferenceFile"], "p3:posting:XREFFILE")
        self.assertEqual(amended["categoryBalanceFile"], "p3:posting:TCATBALF")
        self.assertEqual(amended["rejectFile"], "p3:posting:DALYREJS")
        self.assertEqual(amended["dailyTransactions"], body["dailyTransactions"])
        self.assertEqual(len(changes), 5)

    def test_e2_2_few_shot_nested_bindings_become_local_prefix_tokens(self):
        body = {
            "bindings": {
                "accounts": "ACCTFILE",
                "categoryBalances": "TCATBALF",
                "crossReferences": "XREFFILE",
                "transactionOutput": "TRANFILE",
                "rejectionOutput": "DALYREJS",
            },
            "transactions": [{"transactionId": "POST-PRESENT-001"}],
        }
        amended, changes = amend_body("E2-2", "posting", body)
        self.assertEqual(
            amended["bindings"],
            {
                "accounts": "p3-local-technical-fixture-selection:accounts",
                "categoryBalances": "p3-local-technical-fixture-selection:categoryBalances",
                "crossReferences": "p3-local-technical-fixture-selection:crossReferences",
                "transactionOutput": "p3-local-technical-fixture-selection:transactionOutput",
                "rejectionOutput": "p3-local-technical-fixture-selection:rejectionOutput",
            },
        )
        self.assertEqual(amended["transactions"], body["transactions"])
        self.assertEqual(len(changes), 5)

    def test_e1_output_alias_uses_facade_dd_token_not_generic_output_name(self):
        amended, changes = amend_body("E1-1", "reporting", {"reportFile": "REPORT"})
        self.assertEqual(amended["reportFile"], "p3:reporting:TRANREPT")
        self.assertEqual(changes[0]["from"], "REPORT")

    def test_e1_report_output_does_not_replace_arbitrary_invalid_string(self):
        amended, changes = amend_body("E1-1", "reporting", {"reportFile": "invalidstring"})
        self.assertEqual(amended["reportFile"], "invalidstring")
        self.assertEqual(changes, [])

    def test_e2_2_bindings_do_not_replace_arbitrary_invalid_string_or_already_encoded(self):
        body = {
            "bindings": {
                "accounts": "invalidstring",
                "crossReferences": "p3-local-technical-fixture-selection:crossReferences",
            }
        }
        amended, changes = amend_body("E2-2", "posting", body)
        self.assertEqual(amended, body)
        self.assertEqual(changes, [])

    def test_e1_3_date_parameter_exact_ascii80_record_is_base64_encoded(self):
        record = "2022-07-01 2022-07-31                                                           "
        self.assertEqual(len(record.encode("ascii")), 80)
        amended, changes = amend_body("E1-3", "reporting", {"dateParameterRecords": [record]})
        self.assertEqual(base64.b64decode(amended["dateParameterRecords"][0]).decode("ascii"), record)
        self.assertIn("dateParameterRecords[0]", [change["field"] for change in changes])

    def test_e1_3_date_parameter_preserves_arbitrary_invalid_and_already_encoded_80(self):
        invalid = "not-a-known-date-record"
        raw80 = b"X" * 80
        encoded = base64.b64encode(raw80).decode("ascii")
        amended, changes = amend_body("E1-3", "reporting", {"dateParameterRecords": [invalid, encoded]})
        self.assertEqual(amended["dateParameterRecords"], [invalid, encoded])
        self.assertEqual(changes, [])

    def test_sdd_empty_object_contract_defect_is_not_strengthened(self):
        amended, changes = amend_body("E3-SDD-stage6r3", "posting", {})
        self.assertEqual(amended, {})
        self.assertEqual(changes, [])

    def test_amend_selected_suites_processes_every_t3_case_not_first_per_track(self):
        record = "2022-07-01 2022-07-31                                                           "
        cases = []
        for idx in range(2):
            body = {"reportFile": "REPORT", "dateParameterRecords": [record]}
            cases.append(
                {
                    "case_id": f"c{idx}",
                    "suite_id": "T3",
                    "origin": "unit",
                    "request": {
                        "method": "POST",
                        "path": "/reporting",
                        "headers": [],
                        "body_kind": "json",
                        "body_b64": base64.b64encode(json.dumps(body, separators=(",", ":")).encode()).decode("ascii"),
                    },
                    "resource_package_id": "reporting.pkg",
                    "expectation": {"expectation_id": f"e{idx}", "checks": {}},
                    "timeout_seconds": 5.0,
                    "parameters": {"track": "reporting", "operationId": "op"},
                    "sequence": [],
                    "provenance": [f"T3:c{idx}"],
                }
            )
        suite = {"suite_id": "T3", "cases": cases}
        suite["suite_freeze_sha256"] = "unit-test-no-harness-load"
        with tempfile.TemporaryDirectory() as tmp:
            freeze_root = Path(tmp) / "freeze"
            (freeze_root / "E1-1").mkdir(parents=True)
            (freeze_root / "E1-1" / "T3.json").write_text(json.dumps(suite), encoding="utf-8")
            out = Path(tmp) / "out"
            manifest = amend_selected_suites(freeze_root, out, ["E1-1"])
        self.assertEqual(manifest["outputSuite"]["caseCount"], 2)
        self.assertEqual(len(manifest["cases"]), 2)
        self.assertTrue(all(case["changes"] for case in manifest["cases"]))


if __name__ == "__main__":
    unittest.main()

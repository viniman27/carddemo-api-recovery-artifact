import tempfile
import unittest
from pathlib import Path

import posting_essential as pe


class QualifiedExtractorTests(unittest.TestCase):
    def test_missing_trace_is_inconclusive_not_pass(self):
        result = pe.qualify_effect_trace({}, required=("account", "tcatbal", "tranfile"))
        self.assertEqual(result["status"], "inconclusive")
        self.assertIn("missing trace", "; ".join(result["reasons"]))

    def test_absent_field_is_not_treated_as_empty_field(self):
        absent = pe.require_nonempty_field({}, "rawBytes")
        empty = pe.require_nonempty_field({"rawBytes": ""}, "rawBytes")
        self.assertEqual(absent["status"], "inconclusive")
        self.assertIn("absent", absent["reason"])
        self.assertEqual(empty["status"], "fail")
        self.assertIn("empty", empty["reason"])

    def test_synthetic_bad_record_detects_wrong_card_reject_reason(self):
        bad = {"caseId": "synthetic-bad", "guard": "card_missing", "rejects": [{"reason": "101", "rawBytes": "00"}]}
        check = pe.check_case_expectations(bad, {"expectedRejectReason": "100"})
        self.assertEqual(check["status"], "fail")
        self.assertIn("expected reject reason 100", "; ".join(check["failures"]))

    def test_record_provenance_pins_exact_byte_slice(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "records.bin"
            path.write_bytes(b"abc" + b"def")
            rec = pe.make_provenance_record(path, 3, 3, {"rawBytes": b"def".hex()})
            self.assertEqual(pe.verify_provenance_record(rec), [])
            rec["rawBytes"] = b"deg".hex()
            self.assertTrue(any("slice mismatch" in f for f in pe.verify_provenance_record(rec)))


if __name__ == "__main__":
    unittest.main()

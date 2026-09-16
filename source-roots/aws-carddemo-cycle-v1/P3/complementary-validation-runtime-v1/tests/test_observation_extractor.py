import json
import tempfile
import unittest
from pathlib import Path

from tools.observation_extractor import (
    extract_fixture_from_audits,
    parse_report_capture,
    transaction_record_fields,
)


class ObservationExtractorTests(unittest.TestCase):
    def test_malformed_transaction_bytes_are_not_silently_accepted(self):
        with self.assertRaises(ValueError):
            transaction_record_fields(b"too-short")

    def test_unknown_meaningful_report_bytes_do_not_become_detail(self):
        data = (b"UNMAPPED MEANINGFUL REPORT LINE".ljust(133, b" "))
        parsed = parse_report_capture(data)
        self.assertEqual(parsed["framing"]["classification"], "unmapped_meaningful")
        self.assertEqual(parsed["details"], [])
        self.assertEqual(parsed["totals"], [])

    def test_extract_uses_only_audit_and_raw_files_not_expected_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            post = root / "posting"; post.mkdir()
            raw = (
                b"TXID-0000000001 " + b"01" + b"0005" + b"Internet  " +
                b"purchase".ljust(100) + b"00000001200" + b"123456789" +
                b"Merchant".ljust(50) + b"City".ljust(50) + b"70000000  " +
                b"4111111111111111" + b"2022-07-05-10.00.00.000".ljust(26) +
                b"2026-09-16-12.00.00.000".ljust(26) + b" " * 20
            )
            self.assertEqual(len(raw), 350)
            (post / "DALYTRAN").write_bytes(raw)
            (post / "TRANFILE.after").write_bytes(raw)
            audit = {
                "INV": {"track": "posting", "workdir": str(post)},
                "RESP": {"status": 200, "program_exit": 0, "body": {"progress": {"value": {"processedRecordCount": 1, "preliminaryRejectCount": 0}}}},
                "CONV": {"write_observations": {"events": [{"sequence": 1, "select": "TRANSACT-FILE", "rawHex": raw.hex()}]}},
                "CAP": {"captures": []},
                "STATE": {},
            }
            (post / "audit.json").write_text(json.dumps(audit))
            out = extract_fixture_from_audits("unit", [post / "audit.json"])
            accepted = out["observations"]["posting"]["acceptedTransactions"][0]
            self.assertNotIn("expected", json.dumps(accepted).lower())
            self.assertEqual(accepted["daily"]["id"], "TXID-0000000001")
            self.assertEqual(accepted["posted"]["id"], "TXID-0000000001")
            self.assertEqual(accepted["rawBytes"], raw.hex())


if __name__ == "__main__":
    unittest.main()

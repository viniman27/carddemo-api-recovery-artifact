import copy
import json
import tempfile
import unittest
from pathlib import Path

from semantic_checkers import CheckStatus, load_fixture, run_fixture_checks
from semantic_checkers.evidence import verify_record_provenance

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "synthetic_success_all_tracks.json"


def fixture_data():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["evidenceClass"] = "real_cobol_observation"
    rec = next(r for r in data["observations"]["interest"]["transactions"] if "rawBytes" in r)
    raw = bytes.fromhex(rec["rawBytes"])
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "TRANSACT"
        p.write_bytes(raw)
        rec["provenance"] = {
            "kind": "raw_file_record",
            "artifact": str(p),
            "sha256": __import__("hashlib").sha256(raw).hexdigest(),
            "recordOffset": 0,
            "recordLength": len(raw),
            "observedFields": ["rawBytes", "amount", "type", "category"],
        }
        yield data, p


class RuntimeEvidenceGuardTests(unittest.TestCase):
    def test_record_provenance_verifies_exact_file_hash_and_byte_slice(self):
        for data, _ in fixture_data():
            record = next(r for r in data["observations"]["interest"]["transactions"] if "rawBytes" in r)
            self.assertEqual([], verify_record_provenance(record))

    def test_hash_tampering_is_rejected(self):
        for data, _ in fixture_data():
            record = next(r for r in data["observations"]["interest"]["transactions"] if "rawBytes" in r)
            record["provenance"]["sha256"] = "0" * 64
            failures = verify_record_provenance(record)
            self.assertTrue(any("sha mismatch" in f for f in failures), failures)

    def test_missing_provenance_makes_real_observation_inconclusive_not_failed(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        data["evidenceClass"] = "real_cobol_observation"
        for item in data["observations"]["interest"]["transactions"]:
            item.pop("provenance", None)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        result = run_fixture_checks(load_fixture(path), obligation_ids=["INTCALC-OBL-006"])[0]
        self.assertEqual(CheckStatus.INCONCLUSIVE, result.status)
        self.assertEqual("missing_evidence", result.details["evidenceSufficiency"]["classification"])

    def test_missing_posttran_effect_order_trace_is_inconclusive_not_failed(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        data["evidenceClass"] = "real_cobol_observation"
        tx = data["observations"]["posting"]["acceptedTransactions"][0]
        tx.pop("effects", None)
        tx["traceBoundary"] = "no physical effect order trace captured"
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        result = run_fixture_checks(load_fixture(path), obligation_ids=["POSTTRAN-OBL-009"])[0]
        self.assertEqual(CheckStatus.INCONCLUSIVE, result.status)
        self.assertIn("effect records missing", "; ".join(result.details["failures"]))

    def test_reporting_missing_totals_at_eof_source_guard_is_inconclusive_not_failed(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        data["evidenceClass"] = "real_cobol_observation"
        reporting = data["observations"]["reporting"]
        reporting.pop("pageTotal", None)
        reporting.pop("accountTotal", None)
        reporting["reportFraming"] = {"classification": "available", "eofBeforeTotalsBranch": True}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        result = run_fixture_checks(load_fixture(path), obligation_ids=["TRANREPT-OBL-006"])[0]
        self.assertEqual(CheckStatus.INCONCLUSIVE, result.status)
        self.assertIn("totals branch not observed", "; ".join(result.details["failures"]))


if __name__ == "__main__":
    unittest.main()

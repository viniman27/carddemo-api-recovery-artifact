import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from semantic_checkers import (
    CheckStatus,
    load_fixture,
    run_fixture_checks,
    source_catalog,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


class SemanticCheckerTests(unittest.TestCase):
    def test_catalog_loads_25_obligations_with_explicit_pending(self):
        catalog = source_catalog.load_default_catalog()
        self.assertEqual(25, len(catalog.obligations))
        self.assertEqual(8, len(catalog.implemented_obligation_ids()))
        self.assertEqual(17, len(catalog.pending_obligation_ids()))
        self.assertIn("POSTTRAN-OBL-003", catalog.implemented_obligation_ids())
        self.assertIn("POSTTRAN-OBL-001", catalog.pending_obligation_ids())

    def test_source_anchors_are_verified_against_pinned_hashes(self):
        catalog = source_catalog.load_default_catalog()
        verified = catalog.verify_source_anchors()
        self.assertEqual([], verified.failures)
        self.assertGreaterEqual(len(verified.verified_files), 3)
        self.assertIn("app/cbl/CBTRN02C.cbl", verified.verified_files)
        self.assertIn("app/cbl/CBACT04C.cbl", verified.verified_files)
        self.assertIn("app/cbl/CBTRN03C.cbl", verified.verified_files)

    def test_positive_fixture_passes_representative_posting_interest_reporting_obligations(self):
        fixture = load_fixture(FIXTURES / "synthetic_success_all_tracks.json")
        results = run_fixture_checks(fixture)
        statuses = {result.obligation_id: result.status for result in results}
        for obligation_id in source_catalog.IMPLEMENTED_OBLIGATIONS:
            self.assertEqual(CheckStatus.PASS, statuses[obligation_id], obligation_id)
        self.assertEqual(25, len(results))
        self.assertEqual(17, sum(1 for result in results if result.status is CheckStatus.PENDING))

    def test_known_wrong_fixture_fails_without_false_passes(self):
        fixture = load_fixture(FIXTURES / "synthetic_known_wrong_all_tracks.json")
        results = run_fixture_checks(fixture)
        failed = {result.obligation_id: result for result in results if result.status is CheckStatus.FAILED}
        self.assertIn("POSTTRAN-OBL-003", failed)
        self.assertIn("POSTTRAN-OBL-004", failed)
        self.assertIn("POSTTRAN-OBL-006", failed)
        self.assertIn("POSTTRAN-OBL-009", failed)
        self.assertIn("INTCALC-OBL-005", failed)
        self.assertIn("INTCALC-OBL-006", failed)
        self.assertIn("TRANREPT-OBL-002", failed)
        self.assertIn("TRANREPT-OBL-006", failed)
        self.assertIn("sourceExpected", failed["INTCALC-OBL-005"].details)
        self.assertEqual("12.50", failed["INTCALC-OBL-005"].details["sourceExpected"]["monthlyInterestAmount"])

    def test_interest_formula_uses_decimal_monthly_formula_not_api_replay_or_float(self):
        fixture = load_fixture(FIXTURES / "synthetic_success_all_tracks.json")
        interest = next(item for item in fixture.observations["interest"]["transactions"] if item["id"] == "interest-nonzero")
        self.assertEqual("1500.00", interest["categoryBalance"])
        self.assertEqual("10.00", interest["annualRate"])
        result = run_fixture_checks(fixture, obligation_ids=["INTCALC-OBL-005"])[0]
        self.assertEqual(CheckStatus.PASS, result.status)
        self.assertEqual("12.50", result.details["sourceExpected"]["monthlyInterestAmount"])
        self.assertEqual(Decimal("12.50"), Decimal(result.details["sourceExpected"]["monthlyInterestAmount"]))

    def test_missing_bytes_are_not_treated_as_empty_bytes(self):
        fixture = load_fixture(FIXTURES / "synthetic_success_all_tracks.json")
        del fixture.observations["posting"]["acceptedTransactions"][0]["rawBytes"]
        result = run_fixture_checks(fixture, obligation_ids=["POSTTRAN-OBL-003"])[0]
        self.assertEqual(CheckStatus.FAILED, result.status)
        self.assertIn("rawBytes missing", "; ".join(result.details["failures"]))

    def test_machine_readable_results_have_runner_interface_fields(self):
        fixture = load_fixture(FIXTURES / "synthetic_success_all_tracks.json")
        result = run_fixture_checks(fixture, obligation_ids=["TRANREPT-OBL-006"])[0]
        payload = result.to_json_dict()
        self.assertEqual("TRANREPT-OBL-006", payload["obligationId"])
        self.assertEqual("pass", payload["status"])
        self.assertIn("sourceExpected", payload["details"])
        self.assertIn("observed", payload["details"])
        self.assertIn("sourceAnchors", payload)
        self.assertIn("boundaries", payload)

    def test_cli_creates_parent_directory_for_machine_readable_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "nested" / "results.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "semantic_checkers",
                    "--verify-source",
                    str(FIXTURES / "synthetic_success_all_tracks.json"),
                    "--out",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue(output.exists())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("synthetic-success-all-tracks-v1", payload["fixtureId"])


if __name__ == "__main__":
    unittest.main()

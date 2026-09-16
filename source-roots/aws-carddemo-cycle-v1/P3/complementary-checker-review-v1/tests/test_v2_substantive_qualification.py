import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

REVIEW_ROOT = Path(__file__).resolve().parents[1]
P3_ROOT = REVIEW_ROOT.parent
V1_ROOT = P3_ROOT / "complementary-validation-implementation-v1"
V2_ROOT = P3_ROOT / "complementary-validation-implementation-v2"


def import_package_from(root: Path, alias: str):
    package_dir = root / "semantic_checkers"
    spec = importlib.util.spec_from_file_location(
        alias,
        package_dir / "__init__.py",
        submodule_search_locations=[str(package_dir)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ComplementaryCheckerQualificationTests(unittest.TestCase):
    def test_v1_false_passes_synthetic_success_as_business_pass_without_real_observation_class(self):
        v1 = import_package_from(V1_ROOT, "semantic_checkers_v1_review")
        fixture = v1.load_fixture(V1_ROOT / "fixtures" / "synthetic_success_all_tracks.json")
        result = v1.run_fixture_checks(fixture, ["POSTTRAN-OBL-003"])[0]
        self.assertEqual(v1.CheckStatus.PASS, result.status)
        self.assertNotIn("evidenceSufficiency", result.details)

    def test_v2_does_not_pass_synthetic_success_without_real_cobol_observation_class(self):
        v2 = import_package_from(V2_ROOT, "semantic_checkers_v2_review")
        fixture = v2.load_fixture(V2_ROOT / "fixtures" / "synthetic_success_all_tracks.json")
        result = v2.run_fixture_checks(fixture, ["POSTTRAN-OBL-003"])[0]
        self.assertEqual(v2.CheckStatus.INCONCLUSIVE, result.status)
        self.assertEqual("synthetic_review_not_real_cobol_observation", result.details["evidenceSufficiency"]["classification"])
        self.assertEqual("pass", result.details["semanticOutcome"])

    def test_v2_rejects_order_flags_without_observed_effect_records_and_provenance(self):
        v2 = import_package_from(V2_ROOT, "semantic_checkers_v2_review_order")
        data = json.loads((V2_ROOT / "fixtures" / "synthetic_success_all_tracks.json").read_text(encoding="utf-8"))
        data["evidenceClass"] = "real_cobol_observation"
        # v1-style effectOrder is an assertion flag, not observed COBOL write evidence.
        record = data["observations"]["posting"]["acceptedTransactions"][0]
        record.pop("effects", None)
        record.pop("provenance", None)
        fixture = v2.Fixture(data["fixtureId"], data["description"], data["observations"], data.get("evidenceClass", "synthetic_review"))
        result = v2.run_fixture_checks(fixture, ["POSTTRAN-OBL-009"])[0]
        self.assertEqual(v2.CheckStatus.FAILED, result.status)
        failures = "; ".join(result.details["failures"])
        self.assertIn("observed effect records missing", failures)
        self.assertIn("provenance", failures)

    def test_v2_rejects_interest_amounts_without_raw_observation_provenance_even_if_formula_matches(self):
        v2 = import_package_from(V2_ROOT, "semantic_checkers_v2_review_interest")
        data = json.loads((V2_ROOT / "fixtures" / "synthetic_success_all_tracks.json").read_text(encoding="utf-8"))
        data["evidenceClass"] = "real_cobol_observation"
        for item in data["observations"]["interest"]["transactions"]:
            item.pop("provenance", None)
        fixture = v2.Fixture(data["fixtureId"], data["description"], data["observations"], data.get("evidenceClass", "synthetic_review"))
        result = v2.run_fixture_checks(fixture, ["INTCALC-OBL-005"])[0]
        self.assertEqual(v2.CheckStatus.FAILED, result.status)
        self.assertIn("provenance", "; ".join(result.details["failures"]))

    def test_v2_still_flags_wrong_outputs_as_failed_not_inconclusive(self):
        v2 = import_package_from(V2_ROOT, "semantic_checkers_v2_review_wrong")
        fixture = v2.load_fixture(V2_ROOT / "fixtures" / "synthetic_known_wrong_all_tracks.json")
        results = v2.run_fixture_checks(fixture)
        statuses = {r.obligation_id: r.status for r in results}
        for obligation_id in v2.source_catalog.IMPLEMENTED_OBLIGATIONS:
            self.assertEqual(v2.CheckStatus.FAILED, statuses[obligation_id], obligation_id)


if __name__ == "__main__":
    unittest.main()

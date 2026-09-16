import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = ROOT / "P3" / "complementary-mbt-binding-v1"
sys.path.insert(0, str(PKG))

from mbt_binding import CASE_SPECS, evaluate_all, evaluate_step, load_reference_engine, render_plan


class MbtBindingTests(unittest.TestCase):
    def test_actual_reference_engine_blocks_false_guard(self):
        engine = load_reference_engine(ROOT)
        item = evaluate_step(
            engine,
            "CBTRN02C_POSTTRAN",
            "P_VALIDATE_XREF",
            {"xref_exists": True},
            "POSTTRAN-T007",
        )
        self.assertIs(item["guardResult"], False)
        self.assertIs(item["qualified"], False)
        self.assertEqual(item["blockReason"], "guard_false")

    def test_actual_reference_engine_blocks_unknown_guard(self):
        engine = load_reference_engine(ROOT)
        item = evaluate_step(
            engine,
            "CBTRN03C_TRANREPT",
            "R_LOOP",
            {"read_status": "UnknownEOF"},
            "TRANREPT-T013",
        )
        self.assertEqual(item["guardResult"], "unknown")
        self.assertIs(item["qualified"], False)
        self.assertEqual(item["blockReason"], "guard_unknown")

    def test_all_twelve_essential_cases_are_accounted_for_and_source_persisted(self):
        result = evaluate_all(ROOT)
        self.assertEqual(result["summary"]["essentialCaseCount"], 12)
        self.assertEqual(set(result["summary"]["caseCountsByTrack"].items()), {("posting", 6), ("interest", 2), ("reporting", 4)})
        self.assertIs(result["summary"]["apiReruns"], False)
        self.assertEqual(result["summary"]["modelValidationErrors"], [])
        self.assertEqual(result["summary"]["eligibleT3CandidateCount"], 9)
        self.assertEqual(result["summary"]["sharedOnlyCount"], 3)
        cases = {c["caseId"]: c for c in result["cases"]}
        self.assertEqual(cases["empty-in-range-v1"]["classification"], "shared_only")
        self.assertEqual(cases["empty-in-range-v1"]["sharedOnlyReason"], "unknown_guard_blocked")
        self.assertEqual(cases["card-break-two-groups-v1"]["sharedOnlyReason"], "model_lacks_card_break_transition")
        self.assertEqual(cases["pagination-threshold-20-v1"]["sharedOnlyReason"], "model_lacks_pagination_threshold_transition")
        self.assertEqual(cases["single-final-eof"]["candidateKind"], "source_defect_observation_not_financial_correctness")
        self.assertTrue(all(c["sourceAuthorityChecked"] for c in result["cases"]))
        self.assertTrue(all(c["fixturePins"] for c in result["cases"]))

    def test_plan_mode_is_non_executing_and_mentions_all_cases(self):
        plan = render_plan(ROOT)
        for case_id in CASE_SPECS:
            self.assertIn(case_id, plan)
        self.assertIn("no API/COBOL/model reruns", plan)

    def test_cli_validate_writes_registry(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "registry.json"
            proc = subprocess.run(
                [sys.executable, "-m", "mbt_binding", "validate", "--cycle-root", str(ROOT), "--out", str(out)],
                cwd=str(PKG), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            data = json.loads(out.read_text())
            self.assertEqual(data["summary"]["eligibleT3CandidateCount"], 9)
            self.assertIs(data["candidateRegistryContract"]["prospectiveOnly"], True)
            self.assertIs(data["candidateRegistryContract"]["officialT3"], False)


if __name__ == "__main__":
    unittest.main()

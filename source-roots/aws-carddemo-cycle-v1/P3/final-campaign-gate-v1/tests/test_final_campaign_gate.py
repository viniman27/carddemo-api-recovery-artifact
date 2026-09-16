from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from final_campaign_gate import guard_is_qualified_true, assemble_v3_package, load_suite  # noqa: E402


P3 = ROOT.parent
V2 = P3 / "campaign-freeze-package-v2"


class GuardPolicyTests(unittest.TestCase):
    def test_guard_policy_accepts_only_boolean_true(self):
        self.assertTrue(guard_is_qualified_true({"guardResult": True}))
        for value in ["true", "True", "unknown", False, None, 1]:
            with self.subTest(value=value):
                self.assertFalse(guard_is_qualified_true({"guardResult": value}))


class PackageV3AssemblyTests(unittest.TestCase):
    def test_v2_t3_has_one_unqualified_guard_per_contract(self):
        bad = {}
        for path in sorted(V2.glob("*/T3.json")):
            suite = load_suite(path)
            bad[path.parent.name] = [
                {
                    "caseId": case.case_id,
                    "sourceCaseId": case.parameters.get("bindingClosureAmendment", {}).get("sourceCaseId"),
                    "guardResult": case.parameters.get("guardResult"),
                    "transitionId": case.parameters.get("transitionId"),
                    "obligationId": case.parameters.get("obligationId"),
                }
                for case in suite.cases
                if not guard_is_qualified_true(case.parameters)
            ]
        self.assertEqual(set(bad), {"E1-1", "E1-2", "E1-3", "E2-1", "E2-2", "E2-3", "E3-SDD-stage6r3"})
        for contract_id, rows in bad.items():
            self.assertEqual(len(rows), 1, contract_id)
            self.assertEqual(rows[0]["guardResult"], "unknown")
            self.assertEqual(rows[0]["transitionId"], "POSTTRAN-T006")
            self.assertEqual(rows[0]["obligationId"], "POSTTRAN-OBL-002")

    def test_assemble_v3_excludes_guard_not_true_and_rebuilds_t4(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "campaign-freeze-package-v3"
            report = assemble_v3_package(V2, out)
            self.assertEqual(report["counts"], {"T1": 88, "T2": 5868, "T3": 394, "T4": 6350})
            self.assertEqual(report["excludedT3CasesTotal"], 7)
            self.assertEqual(report["loadedSuiteRows"], 28)
            self.assertTrue(report["t1t2ExactCopies"])
            for row in report["excludedT3Cases"]:
                self.assertEqual(row["guardResult"], "unknown")
                self.assertEqual(row["transitionId"], "POSTTRAN-T006")
            for path in sorted(out.glob("*/T3.json")):
                suite = load_suite(path)
                self.assertTrue(all(guard_is_qualified_true(case.parameters) for case in suite.cases))
            for path in sorted(out.glob("*/T4.json")):
                suite = load_suite(path)
                self.assertFalse(any("POSTTRAN-T006" == case.parameters.get("transitionId") and case.parameters.get("guardResult") != True for case in suite.cases))


if __name__ == "__main__":
    unittest.main()

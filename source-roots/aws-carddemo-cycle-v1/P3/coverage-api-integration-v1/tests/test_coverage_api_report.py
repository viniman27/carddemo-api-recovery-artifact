#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "coverage-api-integration-report.json"


class CoverageApiReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text())

    def test_sdd_three_tracks_exercised_twice_with_real_gcda(self) -> None:
        invocations = self.report["invocations"]
        self.assertEqual(6, len(invocations))
        self.assertEqual({"posting", "interest", "reporting"}, {i["http"]["track"] for i in invocations})
        for inv in invocations:
            self.assertEqual(200, inv["http"]["status"])
            self.assertEqual(0, inv["programExit"])
            self.assertTrue(inv["reachedCobol"])
            self.assertTrue(inv["businessGcdaPresent"])
            self.assertGreater(len(inv["gcdaFiles"]), 0)
            for counter in inv["gcdaFiles"]:
                p = Path(counter["path"])
                self.assertTrue(p.exists(), p)
                self.assertGreater(counter["bytes"], 0)

    def test_reset_is_serially_isolated_per_track(self) -> None:
        pairs = self.report["resetEvidence"]
        self.assertEqual({"posting", "interest", "reporting"}, {p["track"] for p in pairs})
        for pair in pairs:
            self.assertTrue(pair["resetVerified"])
            self.assertTrue(pair["distinctRunDirs"])
            self.assertTrue(pair["distinctGcovPrefixes"])
            self.assertGreater(pair["firstGcdaCount"], 0)
            self.assertGreater(pair["secondGcdaCount"], 0)

    def test_support_counters_are_absent_or_excluded(self) -> None:
        support = self.report["supportExclusion"]["perInvocation"]
        self.assertEqual(6, len(support))
        for item in support:
            self.assertTrue(item["excludedFromBusinessCoverage"])
            self.assertIn(item["classification"], {"absent", "inadmissible_nonzero_support_counter"})
            if item["classification"] == "absent":
                self.assertEqual(0, item["supportGcdaCount"])

    def test_limits_for_comparability_are_explicit(self) -> None:
        text = "\n".join(self.report["limits"])
        self.assertIn("no official suites", text)
        self.assertIn("no claim", text)
        self.assertIn("zero-shot/few-shot", text)


if __name__ == "__main__":
    unittest.main()

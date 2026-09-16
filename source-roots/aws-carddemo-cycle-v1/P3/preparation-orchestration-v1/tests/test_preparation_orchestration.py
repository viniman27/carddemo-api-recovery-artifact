from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

import preparation_orchestration as orch  # noqa: E402


class PreparationOrchestrationTests(unittest.TestCase):
    def test_cli_defaults_do_not_duplicate_when_user_supplies_seed_and_direction(self):
        ns = orch.parse_args([
            "dry-run",
            "--config", str(P3 / "campaign-configuration-v2/campaign-config-v2.json"),
            "--output", "unused",
            "--seed", "7",
            "--direction", "positive",
        ])
        self.assertEqual(orch.effective_seeds(ns.seed), [7])
        self.assertEqual(orch.effective_directions(ns.direction), ["positive"])

    def test_cli_defaults_apply_once_when_omitted(self):
        ns = orch.parse_args([
            "dry-run",
            "--config", str(P3 / "campaign-configuration-v2/campaign-config-v2.json"),
            "--output", "unused",
        ])
        self.assertEqual(orch.effective_seeds(ns.seed), [104729, 130363, 155921])
        self.assertEqual(orch.effective_directions(ns.direction), ["positive", "negative"])

    def test_t2_resource_package_is_bound_per_operation_track(self):
        cfg = json.loads((P3 / "campaign-configuration-v2/campaign-config-v2.json").read_text())
        cases = [
            {"parameters": {"operationId": "postDailyTransactions"}},
            {"parameters": {"operationId": "generateInterestTransactions"}},
            {"parameters": {"operationId": "generateTransactionReport"}},
            {"parameters": {"operationId": "posting"}},
            {"parameters": {"operationId": "interest"}},
            {"parameters": {"operationId": "reporting"}},
        ]
        bound = orch.bind_t2_resource_packages(cases, cfg)
        self.assertEqual([c["resourcePackageId"] for c in bound], [
            "posting.candidate-v1-physical-v2",
            "interest.candidate-v1-physical-v2",
            "reporting.candidate-v1-physical-v2",
            "posting.candidate-v1-physical-v2",
            "interest.candidate-v1-physical-v2",
            "reporting.candidate-v1-physical-v2",
        ])
        self.assertTrue(all(c["parameters"]["fixtureBindingStatus"] == "candidate_not_official" for c in bound))

    def test_t3_budget_is_explicit_final_50_not_preserved_static_12(self):
        cfg = json.loads((P3 / "campaign-configuration-v2/campaign-config-v2.json").read_text())
        plan = orch.build_preparation_plan(cfg, seeds=[104729], directions=["positive"], t3_max_depth=6, t3_max_paths_per_track_fixture=50)
        self.assertEqual(plan["T3"]["budget"], {"maxDepth": 6, "maxPathsPerTrackFixture": 50})
        self.assertEqual(plan["T3"]["entrypoint"], "P3/t3-sdd-external-selection-v3/sdd_external_selection.py::build_selected_t3_suite")
        self.assertEqual(plan["T3"]["preservedStaticEvidence"], {"maxDepth": 6, "maxPathsPerCapability": 12, "realSuiteCases": 65})
        self.assertFalse(plan["T3"]["officialSuiteGenerated"])

    def test_static_dry_run_covers_all_7_contracts_and_21_operations_without_release(self):
        cfg = json.loads((P3 / "campaign-configuration-v2/campaign-config-v2.json").read_text())
        with tempfile.TemporaryDirectory() as td:
            report = orch.write_static_dry_run(cfg, Path(td), seeds=[104729], directions=["positive"], t3_max_paths_per_track_fixture=50)
            self.assertEqual(report["scope"], {"contracts": 7, "operations": 21, "tracks": ["posting", "interest", "reporting"]})
            self.assertFalse(report["authorization"]["campaignAuthorized"])
            self.assertFalse(report["authorization"]["officialCampaignsStarted"])
            self.assertEqual(len(report["contracts"]), 7)
            self.assertEqual(sum(len(c["operations"]) for c in report["contracts"]), 21)
            self.assertEqual(report["T2"]["operationFixturePolicy"], "per-operation candidate fixture binding; placeholder resource ids are forbidden")
            self.assertEqual(report["T3"]["budget"]["maxPathsPerTrackFixture"], 50)

    def test_consolidated_candidate_config_pins_current_t2v4_and_t3selectionv3(self):
        cfg = json.loads((P3 / "campaign-configuration-v2/campaign-config-v2.json").read_text())
        consolidated = orch.build_consolidated_candidate_config(cfg, P3)
        paths = {pin["path"] for pin in consolidated["pins"]}
        self.assertIn("P3/t2-offline-preparation-v4/src/t2_offline_bridge.py", paths)
        self.assertIn("P3/t2-offline-preparation-v4/t2_offline_cli.py", paths)
        self.assertIn("P3/t3-sdd-external-selection-v3/sdd_external_selection.py", paths)
        self.assertNotIn("P3/t3-mapping-integration-v2/src/mapping_integration.py", consolidated["candidateEntrypoints"].get("T3_SDD", ""))
        self.assertEqual(consolidated["candidateEntrypoints"]["T3_SDD"], "P3/t3-sdd-external-selection-v3/sdd_external_selection.py::build_selected_t3_suite")
        self.assertEqual(consolidated["status"], "local_preparation_candidate_not_campaign_release")


if __name__ == "__main__":
    unittest.main()

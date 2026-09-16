from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CYCLE = ROOT.parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from t2_offline_bridge import (  # noqa: E402
    DEFAULT_SEEDS,
    build_plan,
    generate_synthetic_t2_suite,
    load_current_config,
    validate_current_registry,
)


class T2OfflineBridgeTests(unittest.TestCase):
    def test_current_registry_has_seven_contracts_and_total_21_operations_with_pins(self):
        cfg = load_current_config(CYCLE / "P3" / "campaign-configuration-v2" / "campaign-config-v2.json")
        report = validate_current_registry(cfg)
        self.assertEqual(report["ok"], True, report)
        self.assertEqual(report["contractCount"], 7)
        self.assertEqual(report["operationCount"], 21)
        self.assertEqual(report["failedPins"], [])
        self.assertEqual(report["authorization"]["officialCampaignsStarted"], False)
        self.assertEqual(report["authorization"]["externalT1SendAuthorized"], False)

    def test_plan_preserves_candidate_t2_policy_without_generating_campaign(self):
        cfg = load_current_config(CYCLE / "P3" / "campaign-configuration-v2" / "campaign-config-v2.json")
        plan = build_plan(cfg, max_examples_per_direction=50, seeds=DEFAULT_SEEDS)
        self.assertEqual(plan["kind"], "t2-offline-preparation-v2-plan")
        self.assertEqual(plan["officialCampaign"], False)
        self.assertEqual(plan["networkAllowed"], False)
        self.assertEqual(plan["contracts"], 7)
        self.assertEqual(plan["operations"], 21)
        self.assertEqual(plan["policy"]["seeds"], [104729, 130363, 155921])
        self.assertEqual(plan["policy"]["perOperationPerSeed"], {"positive": 50, "negative": 50, "total": 100})
        self.assertEqual(plan["policy"]["budgetTransfer"], "disabled")
        self.assertEqual(plan["policy"]["retries"], "disabled")
        self.assertEqual(plan["policy"]["generationReplay"], "disabled")
        self.assertEqual(plan["reset"]["default"], "fresh_dir_per_run")
        self.assertIn("T3 v2 selection remains unbound", "\n".join(plan["blockers"]))

    def test_synthetic_generation_imports_freezes_and_counts_occurrences_not_diversity(self):
        contract = {
            "contractId": "SYNTH-A",
            "operations": [
                {"method": "post", "path": "/alpha", "operationId": "alpha", "documentedResponses": ["200", "400", "500"], "requestBodyRequired": True},
                {"method": "post", "path": "/beta", "operationId": "beta", "documentedResponses": ["200", "400", "500"], "requestBodyRequired": True},
            ],
        }
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out"
            report = generate_synthetic_t2_suite([contract], out, seeds=[11], max_examples_per_direction=2)
            self.assertEqual(report["officialCampaign"], False)
            self.assertEqual(report["networkCallsDuringGeneration"], 0)
            self.assertEqual(report["contractCount"], 1)
            self.assertEqual(report["operationCount"], 2)
            self.assertEqual(report["requestOccurrences"], 8)  # 2 ops * 1 seed * (2 positive + 2 negative)
            self.assertLessEqual(report["uniqueRequestStimuli"], report["requestOccurrences"])
            self.assertEqual(report["importReport"]["acceptedCount"], 8)
            self.assertEqual(report["frozenSuiteLoadCount"], 8)
            self.assertTrue((out / "synthetic-openapi.json").exists())
            self.assertTrue((out / "frozen-t2-requests.json").exists())
            self.assertTrue((out / "T2-synthetic-suite.json").exists())

    def test_cli_dry_run_writes_plan_only(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "dry"
            cp = subprocess.run([
                sys.executable,
                str(ROOT / "t2_offline_bridge_cli.py"),
                "--config", str(CYCLE / "P3" / "campaign-configuration-v2" / "campaign-config-v2.json"),
                "--output-dir", str(out),
                "--dry-run",
            ], text=True, capture_output=True, check=False)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            plan = json.loads((out / "plan.json").read_text())
            self.assertEqual(plan["officialCampaign"], False)
            self.assertFalse((out / "frozen-t2-requests.json").exists())

    def test_cli_generate_synthetic_writes_plan_and_candidate_artifacts_without_network(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "generate"
            cp = subprocess.run([
                sys.executable,
                str(ROOT / "t2_offline_bridge_cli.py"),
                "--config", str(CYCLE / "P3" / "campaign-configuration-v2" / "campaign-config-v2.json"),
                "--output-dir", str(out),
                "--generate-synthetic",
                "--max-examples-per-direction", "1",
                "--seeds", "104729",
            ], text=True, capture_output=True, check=False)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            stdout = json.loads(cp.stdout)
            self.assertEqual(stdout["officialCampaign"], False)
            self.assertEqual(stdout["requestOccurrences"], 42)  # 21 ops * 1 seed * 2 directions
            report = json.loads((out / "generation-report.json").read_text())
            self.assertEqual(report["networkCallsDuringGeneration"], 0)
            self.assertEqual(report["requestOccurrences"], 42)
            self.assertTrue((out / "plan.json").exists())
            self.assertTrue((out / "T2-synthetic-suite.json").exists())

    def test_negative_invalid_registry_count_fails_closed(self):
        cfg = load_current_config(CYCLE / "P3" / "campaign-configuration-v2" / "campaign-config-v2.json")
        cfg["contracts"]["contracts"] = cfg["contracts"]["contracts"][:6]
        report = validate_current_registry(cfg)
        self.assertEqual(report["ok"], False)
        self.assertTrue(any("contract count" in err for err in report["errors"]))


if __name__ == "__main__":
    unittest.main()

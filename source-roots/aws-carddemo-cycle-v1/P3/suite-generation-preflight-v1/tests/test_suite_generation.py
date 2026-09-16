from __future__ import annotations

import base64
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
HARNESS = P3 / "campaign-harness-v3" / "src"
PY = P3 / ".venv-fuzz-preflight" / "bin" / "python"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HARNESS))

from campaign_harness import load_frozen_suite  # noqa: E402
from suite_generation import (  # noqa: E402
    build_t1_outbound_package,
    import_t1_preserved_response,
    generate_t2_schemathesis_suite,
    import_t2_frozen_suite,
    generate_t3_bfs_suite,
    freeze_load_union,
    module_evidence,
)


class SuiteGenerationPreflightTests(unittest.TestCase):
    def test_t1_exports_pending_package_and_strictly_imports_only_concrete_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            contract = tmp / "synthetic-openapi.json"
            contract.write_text(json.dumps({"openapi": "3.1.0", "paths": {"/synthetic": {"post": {"operationId": "synthetic"}}}}))
            package = build_t1_outbound_package(
                contract_id="SYNTH-T1",
                contract_path=contract,
                output_dir=tmp / "outbound",
                common_instruction="Return JSON only. Do not invent unavailable fields.",
                supported_parameters={"temperature": {"status": "pending_approval"}, "max_output_tokens": {"status": "pending_approval"}},
            )
            self.assertFalse(package["providerCalled"])
            self.assertEqual(package["modelAvailability"], "not_probed")
            self.assertEqual(package["supportedParametersStatus"], "declared_pending_not_probed")
            raw = "preface preserved\n```json\n{\"scenarios\":[{\"id\":\"ok\",\"method\":\"POST\",\"path\":\"/synthetic\",\"body\":{}},{\"id\":\"abstract\",\"obligationId\":\"OBL-1\"},{\"id\":\"badbody\",\"method\":\"POST\",\"path\":\"/synthetic\",\"body\":{\"kind\":\"unsupported\"}}]}\n```\ntrailer"
            response = tmp / "response.txt"
            response.write_text(raw)
            suite, report = import_t1_preserved_response("SYNTH-T1", response)
            self.assertEqual(len(suite.cases), 1)
            self.assertEqual(report["rawResponse"], raw)
            self.assertEqual(report["acceptedCount"], 1)
            self.assertEqual(report["invalidCount"], 2)
            self.assertFalse(report["repairedOrCompleted"])
            self.assertFalse(report["providerCalled"])
            self.assertEqual({r["classification"] for r in report["invalid"]}, {"not_mapped_missing_request", "invalid_request"})

    def test_t2_generates_persists_and_imports_schemathesis_offline_with_budgets(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            schema = tmp / "schema.json"
            out = tmp / "t2"
            report = generate_t2_schemathesis_suite(
                contract_id="SYNTH-T2",
                schema_path=schema,
                output_dir=out,
                seeds=[7, 11],
                directions=["positive", "negative"],
                max_examples_per_direction=3,
                qualification_max_examples_per_direction=2,
            )
            self.assertEqual(report["schemathesisVersion"], "4.27.1")
            self.assertEqual(report["httpCallsDuringGeneration"], 0)
            self.assertEqual(report["hypothesisPhases"], ["generate"])
            self.assertIsNone(report["hypothesisDatabase"])
            self.assertLessEqual(max(row["generated"] for row in report["generation"]), 2)
            suite, import_report = import_t2_frozen_suite("SYNTH-T2", out / "frozen-synthetic3.1-requests.json")
            self.assertGreater(len(suite.cases), 0)
            self.assertEqual(import_report["httpReplayExtra"], 0)
            self.assertTrue(all(case.request.path == "/synthetic" for case in suite.cases))

    def test_t3_bfs_uses_only_allowed_mapping_and_blocks_guard_sensitive_or_abstract(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            model = tmp / "model.json"
            mapping = tmp / "mapping.json"
            model.write_text(json.dumps({
                "status": "synthetic_draft",
                "capabilities": [{
                    "id": "SYNTH_CAP", "initialState": "S0",
                    "states": [{"id": "S0"}, {"id": "S1"}, {"id": "S2"}],
                    "variables": {"flag": {"initial": False, "domain": [False, True], "type": "bool"}},
                    "transitions": [
                        {"id": "A", "from": "S0", "to": "S1", "guard": {"op": "true"}, "effects": []},
                        {"id": "B", "from": "S1", "to": "S2", "guard": {"op": "eq", "left": {"var": "flag"}, "right": {"value": True}}, "effects": []},
                        {"id": "C", "from": "S0", "to": "S2", "guard": {"op": "unsupported_variant"}, "effects": []}
                    ]
                }]
            }))
            mapping.write_text(json.dumps({
                "allowed": {"A": {"method": "POST", "path": "/synthetic", "body": {}}},
                "guardSensitive": {"B": {"requiresVariant": True, "supported": False}},
                "abstractOnly": {"C": {"reason": "no concrete request mapping"}}
            }))
            suite, report = generate_t3_bfs_suite("SYNTH-T3", model, mapping, max_depth=3, max_paths=5)
            self.assertEqual([c.case_id for c in suite.cases], ["T3-SYNTH-T3-A"])
            self.assertEqual(report["acceptedCount"], 1)
            self.assertEqual(report["blockedCount"], 2)
            self.assertIn("blocked_guard_or_variant_without_v3_support", {b["classification"] for b in report["blocked"]})
            self.assertIn("blocked_abstract_without_concrete_mapping", {b["classification"] for b in report["blocked"]})

    def test_freeze_load_union_uses_harness_v3_and_asserts_module_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            contract = tmp / "schema.json"
            t2_report = generate_t2_schemathesis_suite("SYNTH", contract, tmp / "t2", seeds=[1], directions=["positive"], qualification_max_examples_per_direction=1)
            t2, _ = import_t2_frozen_suite("SYNTH", tmp / "t2" / "frozen-synthetic3.1-requests.json")
            raw = tmp / "t1.txt"
            raw.write_text(json.dumps({"scenarios": [{"id": "dup", "method": "POST", "path": "/synthetic", "body": {}}]}))
            t1, _ = import_t1_preserved_response("SYNTH", raw)
            model = tmp / "model.json"; mapping = tmp / "mapping.json"
            model.write_text(json.dumps({"capabilities": [{"id": "SYNTH", "initialState": "S0", "states": [{"id": "S0"}, {"id": "S1"}], "variables": {}, "transitions": [{"id": "A", "from": "S0", "to": "S1", "guard": {"op": "true"}, "effects": []}]}]}))
            mapping.write_text(json.dumps({"allowed": {"A": {"method": "POST", "path": "/synthetic", "body": {}}}}))
            t3, _ = generate_t3_bfs_suite("SYNTH", model, mapping)
            union, report = freeze_load_union([t1, t2, t3], tmp / "union")
            self.assertEqual(Path(report["harnessModule"]["file"]).resolve(), (HARNESS / "campaign_harness.py").resolve())
            self.assertEqual(report["loadedCounts"]["T1"], 1)
            self.assertEqual(report["unionSuiteId"], "T4")
            loaded_union = load_frozen_suite(tmp / "union" / "T4-union.json")
            self.assertEqual(len(loaded_union.cases), len(union.cases))
            self.assertGreaterEqual(report["ledgerCounts"].get("kept", 0), 1)

    def test_cli_only_synthetic_preparation_and_blocks_official(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([str(PY), str(ROOT / "suite_generation_cli.py"), "official", "--output", str(Path(tmp) / "bad")], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("official generation is gate-closed", result.stderr + result.stdout)
            ok = subprocess.run([str(PY), str(ROOT / "suite_generation_cli.py"), "synthetic-preparation", "--output", str(Path(tmp) / "ok")], capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            summary = json.loads(ok.stdout)
            self.assertFalse(summary["officialCampaign"])
            self.assertTrue((Path(tmp) / "ok" / "preflight-report.json").exists())
            self.assertIn("suite_generation.py", summary["moduleEvidence"]["suiteGeneration"]["file"])


if __name__ == "__main__":
    unittest.main()

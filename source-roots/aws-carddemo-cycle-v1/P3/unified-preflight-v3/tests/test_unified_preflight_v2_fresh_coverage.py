import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import unified_preflight_cli as cli


class UnifiedPreflightV2FreshCoverageTests(unittest.TestCase):
    def test_rejects_old_path_injected_audit_even_if_reached_cobol(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            isolated = tmp_path / "isolated"; isolated.mkdir()
            registry = isolated / "registry.json"; registry.write_text("{}")
            old = tmp_path / "old"; old.mkdir()
            audit = old / "audit.json"
            audit.write_text(json.dumps({
                "INV": {"workdir": str(old)},
                "RES": {"selected_fixture": {"registryPath": str(registry)}},
                "RESP": {"reached_cobol": True, "program_exit": 0, "status": 200},
                "FAIL": {"events": []},
            }))
            reach = cli.classify_reach(audit, isolated, registry)
            self.assertFalse(reach["admissibleSameInvocation"])
            self.assertIn("workdir_outside_isolated_cycle", reach["inadmissibilityReasons"])

    def test_rejects_mismatched_invocation_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            isolated = root / "isolated"; isolated.mkdir()
            run = isolated / "P2b" / "runs" / "posting-abc"; run.mkdir(parents=True)
            registry = isolated / "registry.json"; registry.write_text("{}")
            audit = run / "audit.json"
            audit.write_text(json.dumps({
                "INV": {"workdir": str(run)},
                "RES": {"selected_fixture": {"registryPath": str(registry)}},
                "RESP": {"reached_cobol": True, "program_exit": 0, "status": 200},
                "FAIL": {"events": []},
            }))
            reach = cli.classify_reach(audit, isolated, registry, expected_track="interest")
            self.assertFalse(reach["admissibleSameInvocation"])
            self.assertIn("run_dir_track_mismatch", reach["inadmissibilityReasons"])

    def test_v3_declares_fresh_coverage_not_existing_gcov_parser_shortcut(self):
        text = (ROOT / "unified_preflight_cli.py").read_text()
        self.assertIn("unified-preflight-v3-report", text)
        self.assertIn("collect_fresh_coverage_evidence", text)
        self.assertNotIn("parsed-existing-gcov-units-in-preflight-flow", text)
        self.assertNotIn("candidate-coverage-report.json", text)


if __name__ == "__main__":
    unittest.main()

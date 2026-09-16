from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(P3 / "campaign-harness-v3" / "src"))

from campaign_harness import Case, Expectation, HttpRequestSpec
import aws_campaign_runner as runner


class RunnerV3RegressionTests(unittest.TestCase):
    def test_prepare_real_target_copies_all_six_generated_contract_sources_into_isolated_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Avoid expensive full build in this narrow copy regression.
            fake_unified = type("FakeUnified", (), {})()
            def prep(out):
                cycle = root / "isolated" / "aws-carddemo-cycle-v1"
                cycle.mkdir(parents=True)
                (cycle / "P3" / "technical-packages-v3-argument").mkdir(parents=True)
                reg = cycle / "P3" / "technical-packages-v3-argument" / "registry.json"
                reg.write_text("{}", encoding="utf-8")
                return {"cycle": str(cycle), "registry": str(reg), "python": sys.executable}
            fake_unified.prepare_isolated_workspace = prep
            fake_unified.PosixSpawnServer = object
            fake_unified.target_p2b = lambda cycle, registry: object()
            original = runner._import_module
            original_run = runner.subprocess.run
            runner._import_module = lambda path, name: fake_unified
            runner.subprocess.run = lambda *args, **kwargs: types.SimpleNamespace(returncode=0, stdout="{}", stderr="")
            try:
                _factory, prepared = runner.prepare_real_p2b_target(root / "out", {}, {})
            finally:
                runner._import_module = original
                runner.subprocess.run = original_run
            cycle = Path(prepared["cycle"])
            copied = sorted(str(p.relative_to(cycle)) for p in cycle.glob("collection-01/E*/response-original.txt"))
            self.assertEqual(copied, [
                "collection-01/E1-1/response-original.txt",
                "collection-01/E1-2/response-original.txt",
                "collection-01/E1-3/response-original.txt",
                "collection-01/E2-1/response-original.txt",
                "collection-01/E2-2/response-original.txt",
                "collection-01/E2-3/response-original.txt",
            ])
            self.assertEqual(prepared["isolatedContractSourceCopy"]["count"], 6)

    def test_t3_metadata_is_derived_from_contract_directory_and_exact_openapi_operation(self):
        spec = {"openapi":"3.1.0", "paths": {"/interest-runs": {"post": {"operationId": "generateInterestTransactions", "responses": {"200": {"description": "ok"}}}}}}
        pin = runner.ContractPin("E1-1", "zero-shot", Path("/tmp/nope.json"), "sha", 1, spec)
        case = Case(
            case_id="T3-0001",
            suite_id="T3",
            origin="T3-v4-adapter:E1-1",
            request=HttpRequestSpec("POST", "/interest-runs", (("content-type", "application/json"),), "json", "e30="),
            resource_package_id="interest.candidate-v1-physical-v2",
            expectation=Expectation("documented-status", {"status": [200, 500]}),
            timeout_seconds=5,
            parameters={},
            provenance=("x",),
        )
        meta = runner.derive_case_metadata_from_contract_operation(case, {"E1-1": pin})
        self.assertEqual(meta["contractId"], "E1-1")
        self.assertEqual(meta["operationId"], "generateInterestTransactions")
        self.assertEqual(meta["track"], "interest")

    def test_measurement_binds_audit_from_current_delta_matching_exact_track_not_latest_arbitrary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cycle = root / "cycle"
            old = cycle / "P2b" / "runs" / "posting-old" / "audit.json"
            new = cycle / "P2b" / "runs" / "interest-new" / "audit.json"
            for p, track in [(old, "posting"), (new, "interest")]:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps({"INV": {"workdir": str(p.parent)}, "RESP": {"reached_cobol": True, "program_exit": 0}, "RES": {"selected_fixture": {"registryPath": str(cycle / "reg.json")}}}), encoding="utf-8")
            calls = []
            fake = type("FakeUnified", (), {})()
            fake.collect_fresh_coverage_evidence = lambda p2b, audit_path, track: calls.append((str(audit_path), track)) or {"measurementAdmissibility":"admissible_preparatory", "track": track}
            sys.modules["aws_campaign_unified_preflight_v3"] = fake
            try:
                case = Case("c", "T3", "x", HttpRequestSpec("POST", "/interest-runs", (), "json", "e30="), "r", Expectation("x", {}), 5, {"track":"interest"}, ())
                measured = runner._collect_measurement({}, {"workdir": str(root / "app")}, {"cycle": str(cycle), "auditDelta": [str(new), str(old)]}, case)
            finally:
                sys.modules.pop("aws_campaign_unified_preflight_v3", None)
            self.assertEqual(measured["track"], "interest")
            self.assertEqual(Path(calls[0][0]), new)


if __name__ == "__main__":
    unittest.main()

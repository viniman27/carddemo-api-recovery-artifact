from __future__ import annotations

import base64
import inspect
import json
import sys
import tempfile
import types
import unittest
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(P3 / "campaign-harness-v3" / "src"))

from campaign_harness import Case, Expectation, HttpRequestSpec, PerApplicationHttpTarget, Suite, freeze_suite

import aws_campaign_runner as runner


class JsonOkHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("content-length", "0"))
        _body = self.rfile.read(n)
        if self.path == "/bad-status":
            payload = {"ok": True, "path": self.path}
            status = 200
        elif self.path == "/schema-bad":
            payload = {"path": self.path}
            status = 200
        else:
            payload = {"ok": True, "path": self.path}
            status = 200
        raw = json.dumps(payload, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *_args):
        pass


class ExplodingStartupHandler(JsonOkHandler):
    campaign_harness_startup_fail = True


def make_case(case_id: str, path: str, contract_id: str = "C1", operation_id: str = "op", track: str = "posting", allowed=(200,)) -> Case:
    return Case(
        case_id=case_id,
        suite_id="T1",
        origin="unit",
        request=HttpRequestSpec("POST", path, (("content-type", "application/json"),), "json", base64.b64encode(b"{}").decode()),
        resource_package_id="none",
        expectation=Expectation("status", {"status": list(allowed)}),
        timeout_seconds=2.0,
        parameters={"contractId": contract_id, "operationId": operation_id, "track": track},
        provenance=(f"T1:{case_id}",),
    )


class RunnerV2Tests(unittest.TestCase):
    def write_contracts(self, root: Path) -> dict[str, runner.ContractPin]:
        ok_schema = {"type": "object", "required": ["ok"], "properties": {"ok": {"type": "boolean"}, "path": {"type": "string"}}}
        specs = {
            "C1": {"arm": "zero-shot", "paths": {"/ok": "op", "/bad-status": "opBad", "/schema-bad": "opSchema"}},
            "C2": {"arm": "few-shot", "paths": {"/ok2": "op2"}},
        }
        registry = {}
        for cid, item in specs.items():
            spec = {"openapi": "3.1.0", "info": {"title": cid, "version": "1"}, "paths": {}}
            for path, op in item["paths"].items():
                spec["paths"][path] = {"post": {"operationId": op, "responses": {"200": {"description": "ok", "content": {"application/json": {"schema": ok_schema}}}}}}
            if "/bad-status" in spec["paths"]:
                spec["paths"]["/bad-status"]["post"]["responses"] = {"201": {"description": "created", "content": {"application/json": {"schema": {"type": "object"}}}}}
            path = root / f"{cid}.json"
            path.write_text(json.dumps(spec), encoding="utf-8")
            pin = runner.file_pin(path)
            registry[cid] = runner.ContractPin(cid, item["arm"], path, pin["sha256"], pin["bytes"], spec)
        return registry

    def test_execute_routes_each_case_to_its_own_contract_target_and_records_all_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry = self.write_contracts(root)
            suite_path = root / "T1.json"
            freeze_suite(Suite("T1", [make_case("c1", "/ok", "C1", "op"), make_case("c2", "/ok2", "C2", "op2", "interest")]), suite_path)
            routed = []
            def factory(case):
                routed.append(runner.case_contract_id(case))
                return PerApplicationHttpTarget(JsonOkHandler)
            report = runner.execute_campaign([suite_path], registry, root / "run", target_factory=factory, official_ready=True)
            self.assertEqual(routed, ["C1", "C2"])
            self.assertEqual(report["totals"]["attempted"], 2)
            self.assertEqual([c["case_id"] for c in report["suiteReports"][0]["checks"]], ["c1", "c2"])
            self.assertFalse(report["stopPolicy"]["stopped"])

    def test_structural_schema_and_expectation_violations_continue_without_stopping_campaign(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry = self.write_contracts(root)
            suite_path = root / "T1.json"
            freeze_suite(Suite("T1", [
                make_case("status-violation", "/bad-status", "C1", "opBad"),
                make_case("expectation-violation", "/ok", "C1", "op", allowed=(201,)),
                make_case("schema-violation", "/schema-bad", "C1", "opSchema"),
                make_case("later", "/ok2", "C2", "op2", "interest"),
            ]), suite_path)
            report = runner.execute_campaign([suite_path], registry, root / "run", target_factory=lambda case: PerApplicationHttpTarget(JsonOkHandler), official_ready=True)
            checks = report["suiteReports"][0]["checks"]
            self.assertEqual([c["case_id"] for c in checks], ["status-violation", "expectation-violation", "schema-violation", "later"])
            self.assertIn("experimental_structural_violation:status_violation", report["experimentalViolations"])
            self.assertIn("experimental_expectation_violation", report["experimentalViolations"])
            self.assertIn("experimental_structural_violation:schema_violation", report["experimentalViolations"])
            self.assertFalse(report["stopPolicy"]["stopped"])

    def test_infra_startup_failure_stops_after_recording_complete_case_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry = self.write_contracts(root)
            suite_path = root / "T1.json"
            freeze_suite(Suite("T1", [make_case("boom", "/ok", "C1", "op"), make_case("later", "/ok2", "C2", "op2", "interest")]), suite_path)
            def factory(case):
                return PerApplicationHttpTarget(ExplodingStartupHandler if case.case_id == "boom" else JsonOkHandler)
            report = runner.execute_campaign([suite_path], registry, root / "run", target_factory=factory, official_ready=True)
            checks = report["suiteReports"][0]["checks"]
            self.assertEqual([c["case_id"] for c in checks], ["boom"])
            self.assertEqual(checks[0]["receipt"]["failure_class"], "startup")
            self.assertEqual(report["stopPolicy"]["stopped"], True)
            self.assertEqual(report["stopPolicy"]["reason"], "wire_failure:startup")

    def test_resume_skips_every_attempted_case_including_previous_failures(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry = self.write_contracts(root)
            suite_path = root / "T1.json"
            freeze_suite(Suite("T1", [make_case("failed-before", "/ok"), make_case("todo", "/ok2", "C2", "op2", "interest")]), suite_path)
            existing = root / "run" / "T1" / "cases" / "failed-before" / "replay" / "receipts.json"
            existing.parent.mkdir(parents=True)
            existing.write_text(json.dumps([{"case_id": "failed-before", "failure_class": "transport"}]), encoding="utf-8")
            report = runner.execute_campaign([suite_path], registry, root / "run", target_factory=lambda case: PerApplicationHttpTarget(JsonOkHandler), official_ready=True, resume=True)
            self.assertEqual(report["suiteReports"][0]["attempted_case_count"], 1)
            self.assertEqual(report["suiteReports"][0]["checks"][0]["case_id"], "todo")

    def test_measurement_uses_case_track_not_url_suffix_and_real_helper_signature(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            audit = root / "audit.json"
            audit.write_text("{}", encoding="utf-8")
            calls = []
            fake = types.SimpleNamespace()
            def collect_fresh_coverage_evidence(p2b, audit_path, track):
                calls.append((str(p2b), str(audit_path), track))
                return {"measurementAdmissibility": "admissible_preparatory", "track": track}
            fake.collect_fresh_coverage_evidence = collect_fresh_coverage_evidence
            sys.modules["aws_campaign_unified_preflight_v3"] = fake
            try:
                sig = inspect.signature(fake.collect_fresh_coverage_evidence)
                self.assertEqual(list(sig.parameters), ["p2b", "audit_path", "track"])
                case = make_case("c1", "/transaction-posting-runs", "C1", "op", track="interest")
                measured = runner._collect_measurement({"path": "/transaction-posting-runs"}, {"workdir": str(root)}, {"cycle": str(root)}, case)
                self.assertEqual(measured["track"], "interest")
                self.assertEqual(calls[0][2], "interest")
            finally:
                sys.modules.pop("aws_campaign_unified_preflight_v3", None)


if __name__ == "__main__":
    unittest.main()

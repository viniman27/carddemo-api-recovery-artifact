from __future__ import annotations

import base64
import json
import sys
import tempfile
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
        if self.path == "/slow-stop":
            payload = {"ok": True, "path": self.path}
        else:
            payload = {"ok": True, "path": self.path}
        raw = json.dumps(payload, sort_keys=True).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *_args):
        pass


def make_case(case_id: str, path: str, contract_id: str = "C1", operation_id: str = "op") -> Case:
    return Case(
        case_id=case_id,
        suite_id="T1",
        origin="unit",
        request=HttpRequestSpec("POST", path, (("content-type", "application/json"),), "json", base64.b64encode(b"{}").decode()),
        resource_package_id="none",
        expectation=Expectation("status", {"status": [200]}),
        timeout_seconds=2.0,
        parameters={"contractId": contract_id, "operationId": operation_id, "track": "posting"},
        provenance=(f"T1:{case_id}",),
    )


class RunnerTests(unittest.TestCase):
    def write_contract(self, root: Path) -> tuple[Path, dict]:
        ok_schema = {
            "type": "object",
            "required": ["ok"],
            "properties": {"ok": {"type": "boolean"}, "path": {"type": "string"}},
        }
        spec = {
            "openapi": "3.1.0",
            "info": {"title": "synthetic", "version": "1"},
            "paths": {
                "/ok": {
                    "post": {
                        "operationId": "op",
                        "responses": {"200": {"description": "ok", "content": {"application/json": {"schema": ok_schema}}}},
                    }
                },
                "/bad-status": {
                    "post": {
                        "operationId": "opBad",
                        "responses": {"201": {"description": "created", "content": {"application/json": {"schema": {"type": "object"}}}}},
                    }
                },
            },
        }
        contract = root / "contract.json"
        contract.write_text(json.dumps(spec), encoding="utf-8")
        pin = runner.file_pin(contract)
        registry = {"C1": runner.ContractPin(contract_id="C1", arm="synthetic", path=contract, sha256=pin["sha256"], bytes=pin["bytes"], openapi=spec)}
        return contract, registry

    def test_plan_loads_frozen_suites_and_never_executes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _contract, registry = self.write_contract(root)
            suite_path = root / "T1.json"
            freeze_suite(Suite("T1", [make_case("c1", "/ok")]), suite_path)
            plan = runner.build_execution_plan([suite_path], registry, official_ready=False)
            self.assertEqual(plan["totals"], {"suites": 1, "cases": 1})
            self.assertFalse(plan["officialReady"])
            self.assertFalse((root / "run" / "receipts.json").exists())
            self.assertIn("caseRequestPins", plan["suites"][0]["cases"][0])

    def test_execute_requires_explicit_official_readiness_even_with_valid_suite(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _contract, registry = self.write_contract(root)
            suite_path = root / "T1.json"
            freeze_suite(Suite("T1", [make_case("c1", "/ok")]), suite_path)
            with self.assertRaisesRegex(runner.CampaignBlocked, "official_readiness_not_asserted"):
                runner.execute_campaign([suite_path], registry, root / "run", target_factory=lambda: PerApplicationHttpTarget(JsonOkHandler), official_ready=False)

    def test_execute_records_raw_response_body_structural_check_and_lifecycle(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _contract, registry = self.write_contract(root)
            suite_path = root / "T1.json"
            freeze_suite(Suite("T1", [make_case("c1", "/ok")]), suite_path)
            report = runner.execute_campaign([suite_path], registry, root / "run", target_factory=lambda: PerApplicationHttpTarget(JsonOkHandler), official_ready=True)
            self.assertEqual(report["totals"]["attempted"], 1)
            self.assertEqual(report["totals"]["completed"], 1)
            check = report["suiteReports"][0]["checks"][0]
            self.assertTrue(check["structuralCheck"]["ok"])
            self.assertEqual(check["structuralCheck"]["classification"], "schema_valid")
            self.assertEqual(base64.b64decode(check["receipt"]["response_body_b64"]), b'{"ok": true, "path": "/ok"}')
            self.assertTrue(report["suiteReports"][0]["applications_inline"][0]["target_quiet"])

    def test_structural_status_violation_stops_remaining_suites(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _contract, registry = self.write_contract(root)
            first = root / "T1.json"
            second = root / "T2.json"
            freeze_suite(Suite("T1", [make_case("bad", "/bad-status", operation_id="opBad")]), first)
            freeze_suite(Suite("T2", [make_case("later", "/ok")]), second)
            report = runner.execute_campaign([first, second], registry, root / "run", target_factory=lambda: PerApplicationHttpTarget(JsonOkHandler), official_ready=True)
            self.assertEqual(report["stopPolicy"]["stopped"], True)
            self.assertEqual(report["suiteReports"][0]["checks"][0]["structuralCheck"]["classification"], "status_violation")
            self.assertEqual(report["suiteReports"][1]["skippedReason"], "previous_suite_failed_stop_policy")

    def test_resume_runs_only_unattempted_cases_from_existing_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _contract, registry = self.write_contract(root)
            suite_path = root / "T1.json"
            freeze_suite(Suite("T1", [make_case("done", "/ok"), make_case("todo", "/ok")]), suite_path)
            existing = root / "run" / "T1" / "replay" / "receipts.json"
            existing.parent.mkdir(parents=True)
            existing.write_text(json.dumps([{"case_id": "done", "failure_class": None}]), encoding="utf-8")
            report = runner.execute_campaign([suite_path], registry, root / "run", target_factory=lambda: PerApplicationHttpTarget(JsonOkHandler), official_ready=True, resume=True)
            self.assertEqual(report["suiteReports"][0]["loaded_case_count"], 2)
            self.assertEqual(report["suiteReports"][0]["attempted_case_count"], 1)
            self.assertEqual(report["suiteReports"][0]["checks"][0]["receipt"]["case_id"], "todo")


if __name__ == "__main__":
    unittest.main()

import json
import os
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from campaign_harness import (  # noqa: E402
    Case,
    Expectation,
    HttpRequestSpec,
    LocalResourcePackage,
    PerApplicationHttpTarget,
    Suite,
    UnionBuilder,
    VerificationError,
    freeze_suite,
    load_frozen_suite,
    replay_suite,
)


class RecordingHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    seen = []

    def do_POST(self):
        length_header = self.headers.get("Content-Length")
        body = self.rfile.read(int(length_header or "0")) if length_header is not None else None
        type(self).seen.append({"path": self.path, "length_header": length_header, "body": body, "x_dup_all": self.headers.get_all("X-Dup")})
        if self.path == "/slow":
            time.sleep(0.35)
            self.send_response(200)
            payload = b'{"late":true}'
        elif self.path == "/fail":
            self.send_response(500)
            payload = b'{"documented":true}'
        else:
            self.send_response(200)
            payload = json.dumps({"path": self.path, "bodyState": "absent" if body is None else body.decode()}).encode()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        try:
            self.wfile.write(payload)
        except BrokenPipeError:
            pass

    def log_message(self, format, *args):  # noqa: A002
        pass


class WorkdirHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    seen = []
    workdir = None

    def do_POST(self):
        state = Path(type(self).workdir) / "state.txt"
        before = state.read_text(encoding="utf-8")
        state.write_text(before.strip() + "+mutated\n", encoding="utf-8")
        after = state.read_text(encoding="utf-8")
        type(self).seen.append({"workdir": str(type(self).workdir), "before": before, "after": after})
        payload = json.dumps({"before": before, "after": after}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):  # noqa: A002
        pass


def serve(handler_cls):
    server = HTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, f"http://127.0.0.1:{server.server_port}"


def stop(server, thread):
    server.shutdown()
    thread.join(timeout=2)
    server.server_close()


class CampaignHarnessTests(unittest.TestCase):
    def setUp(self):
        RecordingHandler.seen = []
        self.server = HTTPServer(("127.0.0.1", 0), RecordingHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=2)
        self.server.server_close()

    def mk_case(self, case_id, suite_id="T1", body_kind="absent", body_b64=None, path="/ok", expectation=None, timeout=1.0, headers=(("X-Synthetic", "qualification"),)):
        return Case(
            case_id=case_id,
            suite_id=suite_id,
            origin=suite_id,
            request=HttpRequestSpec("POST", path, headers, body_kind, body_b64),
            resource_package_id="pkg-a",
            expectation=expectation or Expectation("ok", {"status": [200, 500]}),
            timeout_seconds=timeout,
        )

    def test_freeze_hashes_detect_suite_tampering(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            suite = Suite("T1", [self.mk_case("c1")])
            path = freeze_suite(suite, tmp_path / "suite.json")
            loaded = load_frozen_suite(path)
            self.assertEqual(loaded.suite_id, "T1")
            data = json.loads(path.read_text())
            data["cases"][0]["request"]["path"] = "/tampered"
            path.write_text(json.dumps(data, indent=2, sort_keys=True))
            with self.assertRaisesRegex(VerificationError, "suite freeze hash mismatch"):
                load_frozen_suite(path)

    def test_body_absent_empty_and_empty_json_are_distinct_in_identity_and_wire(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cases = [self.mk_case("absent"), self.mk_case("empty", body_kind="bytes", body_b64=""), self.mk_case("object", body_kind="json", body_b64="e30=")]
            result = replay_suite(Suite("T1", cases), base_url=self.base_url, output_dir=tmp_path / "run")
            self.assertEqual(result.totals["completed"], 3)
            self.assertEqual([row["body_kind"] for row in result.receipts], ["absent", "bytes", "json"])
            self.assertIsNone(RecordingHandler.seen[0]["length_header"])
            self.assertEqual(RecordingHandler.seen[1]["length_header"], "0")
            self.assertEqual(RecordingHandler.seen[2]["length_header"], "2")
            self.assertEqual(len({case.identity_key() for case in cases}), 3)

    def test_http_preserves_duplicate_header_order_on_wire(self):
        with TemporaryDirectory() as tmp:
            case = self.mk_case("dup", headers=(("X-Dup", "one"), ("X-Dup", "two"), ("X-Other", "v")))
            result = replay_suite(Suite("T1", [case]), base_url=self.base_url, output_dir=Path(tmp) / "run")
            self.assertEqual(result.totals["completed"], 1)
            self.assertEqual(RecordingHandler.seen[0]["x_dup_all"], ["one", "two"])
            self.assertEqual(result.receipts[0]["request_headers"], [["X-Dup", "one"], ["X-Dup", "two"], ["X-Other", "v"]])

    def test_per_application_lifecycle_binds_server_to_fresh_workdir_and_resets_state(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "resources"
            source.mkdir()
            (source / "state.txt").write_text("original\n", encoding="utf-8")
            package = LocalResourcePackage.from_directory("pkg-a", source)
            WorkdirHandler.seen = []
            target = PerApplicationHttpTarget(WorkdirHandler)
            suite = Suite("T4", [self.mk_case("first", "T4"), self.mk_case("second", "T4")], resources={"pkg-a": package})
            result = replay_suite(suite, target=target, output_dir=tmp_path / "run")
            self.assertEqual(result.totals["completed"], 2)
            state_values = [Path(app["workdir"], "state.txt").read_text(encoding="utf-8") for app in result.applications]
            self.assertEqual(state_values, ["original+mutated\n", "original+mutated\n"])
            self.assertNotEqual(result.applications[0]["workdir"], result.applications[1]["workdir"])
            self.assertEqual(result.applications[0]["target_quiet"], True)
            self.assertEqual(result.applications[1]["pins_before"]["state.txt"], package.pins["state.txt"].to_dict())

    def test_timeout_on_uncontrolled_target_aborts_remaining_not_executed(self):
        with TemporaryDirectory() as tmp:
            slow = self.mk_case("slow", "T2", path="/slow", timeout=0.05)
            fast = self.mk_case("fast-after-slow", "T2", path="/ok", timeout=0.20)
            result = replay_suite(Suite("T2", [slow, fast]), base_url=self.base_url, output_dir=Path(tmp) / "run")
            self.assertEqual(result.totals["attempted"], 1)
            self.assertEqual(result.totals["not_executed"], 1)
            self.assertEqual(result.totals["deadline_failures"], 1)
            self.assertEqual(result.receipts[1]["failure_class"], "not_executed")
            self.assertIn("cannot prove target quiet", result.receipts[1]["not_executed_reason"])

    def test_expectations_are_structural_and_do_not_confuse_transport_completed_with_pass(self):
        with TemporaryDirectory() as tmp:
            cases = [
                self.mk_case("unexpected-500", "T2", path="/fail", expectation=Expectation("only-200", {"status": [200]})),
                self.mk_case("documented-500", "T2", path="/fail", expectation=Expectation("allows-500", {"status": [500]})),
                self.mk_case("unsupported", "T2", expectation=Expectation("unsupported", {"jsonSchema": {}})),
            ]
            result = replay_suite(Suite("T2", cases), base_url=self.base_url, output_dir=Path(tmp) / "run")
            self.assertEqual(result.totals["completed"], 3)
            self.assertEqual(result.totals["expectation_passes"], 1)
            self.assertEqual(result.totals["expectation_violations"], 1)
            self.assertEqual(result.totals["expectation_inconclusive"], 1)
            self.assertEqual(result.totals["http_failures"], 0)
            self.assertEqual([r["expectation_result"] for r in result.receipts], ["violation", "pass", "inconclusive"])

    def test_case_ids_preserved_but_workdir_paths_are_opaque_contained_and_symlink_safe(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            result = replay_suite(Suite("T1", [self.mk_case("x/../../escaped-case")]), base_url=self.base_url, output_dir=tmp_path / "run")
            self.assertEqual(result.receipts[0]["case_id"], "x/../../escaped-case")
            self.assertEqual(result.applications[0]["case_id"], "x/../../escaped-case")
            workdir = Path(result.applications[0]["workdir"]).resolve()
            apps = (tmp_path / "run" / "applications").resolve()
            self.assertIn(apps, workdir.parents)
            self.assertNotIn("escaped-case", workdir.name)

            src = tmp_path / "src"
            src.mkdir()
            os.symlink(tmp_path / "outside", src / "link")
            with self.assertRaisesRegex(VerificationError, "symlink"):
                LocalResourcePackage.from_directory("pkg-a", src)

    def test_union_stable_order_provenance_and_distinct_expectations(self):
        t1 = Suite("T1", [self.mk_case("a", "T1", expectation=Expectation("same", {"status": [200]}))])
        t2 = Suite("T2", [self.mk_case("b", "T2", expectation=Expectation("same", {"status": [200]})), self.mk_case("c", "T2", expectation=Expectation("distinct", {"status": [500]}))])
        t3 = Suite("T3", [self.mk_case("d", "T3", path="/other", expectation=Expectation("same", {"status": [200]}))])
        union, ledger = UnionBuilder().build([t1, t2, t3])
        self.assertEqual([case.case_id for case in union.cases], ["T4-0001", "T4-0002", "T4-0003"])
        self.assertEqual(union.cases[0].provenance, ("T1:a", "T2:b"))
        self.assertEqual(union.cases[1].provenance, ("T2:c",))
        self.assertEqual(union.cases[2].provenance, ("T3:d",))
        self.assertEqual(ledger[1]["action"], "duplicate_merged")
        self.assertEqual(ledger[2]["action"], "kept_distinct_expectation")

    def test_cli_accepts_only_synthetic_qualification_and_fails_closed_for_official_label(self):
        with TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "label.json"
            cfg.write_text(json.dumps({"approval": {"freezeStatus": "approved_frozen"}, "execution": {"mode": "approved_campaign_execution"}}))
            import subprocess
            good = subprocess.run([sys.executable, str(ROOT / "campaign_harness_cli.py"), "--mode", "synthetic-qualification", "--help"], text=True, capture_output=True)
            bad = subprocess.run([sys.executable, str(ROOT / "campaign_harness_cli.py"), "--mode", "official-aws", "--config", str(cfg)], text=True, capture_output=True)
            self.assertEqual(good.returncode, 0)
            self.assertEqual(bad.returncode, 2)
            self.assertIn("official AWS campaign execution is not implemented", bad.stderr)


if __name__ == "__main__":
    unittest.main()

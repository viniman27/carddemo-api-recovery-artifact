import json
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
        type(self).seen.append({"path": self.path, "length_header": length_header, "body": body})
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

    def mk_case(self, case_id, suite_id, body_kind="absent", body_b64=None, path="/ok", expectation_id="ok"):
        return Case(
            case_id=case_id,
            suite_id=suite_id,
            origin=suite_id,
            request=HttpRequestSpec("POST", path, (("X-Synthetic", "qualification"),), body_kind, body_b64),
            resource_package_id="pkg-a",
            expectation=Expectation(expectation_id, {"status": [200, 500]}),
            timeout_seconds=1.0,
        )

    def test_freeze_hashes_detect_suite_tampering(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            suite = Suite("T1", [self.mk_case("c1", "T1")])
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
            cases = [
                self.mk_case("absent", "T1", "absent", None),
                self.mk_case("empty", "T1", "bytes", ""),
                self.mk_case("object", "T1", "json", "e30="),
            ]
            suite = Suite("T1", cases)
            frozen = freeze_suite(suite, tmp_path / "suite.json")
            result = replay_suite(load_frozen_suite(frozen), base_url=self.base_url, output_dir=tmp_path / "run")

            self.assertEqual(result.totals["attempted"], 3)
            self.assertEqual(result.totals["completed"], 3)
            self.assertEqual([row["body_kind"] for row in result.receipts], ["absent", "bytes", "json"])
            self.assertIsNone(RecordingHandler.seen[0]["length_header"])
            self.assertIsNone(RecordingHandler.seen[0]["body"])
            self.assertEqual(RecordingHandler.seen[1]["length_header"], "0")
            self.assertEqual(RecordingHandler.seen[1]["body"], b"")
            self.assertEqual(RecordingHandler.seen[2]["length_header"], "2")
            self.assertEqual(RecordingHandler.seen[2]["body"], b"{}")
            self.assertEqual(len({case.identity_key() for case in cases}), 3)

    def test_union_stable_order_provenance_and_distinct_expectations(self):
        t1 = Suite("T1", [self.mk_case("a", "T1", expectation_id="same")])
        t2 = Suite("T2", [self.mk_case("b", "T2", expectation_id="same"), self.mk_case("c", "T2", expectation_id="distinct")])
        t3 = Suite("T3", [self.mk_case("d", "T3", path="/other", expectation_id="same")])

        union, ledger = UnionBuilder().build([t1, t2, t3])

        self.assertEqual([case.case_id for case in union.cases], ["T4-0001", "T4-0002", "T4-0003"])
        self.assertEqual(union.cases[0].provenance, ("T1:a", "T2:b"))
        self.assertEqual(union.cases[1].provenance, ("T2:c",))
        self.assertEqual(union.cases[2].provenance, ("T3:d",))
        self.assertEqual(ledger[1]["action"], "duplicate_merged")
        self.assertEqual(ledger[2]["action"], "kept_distinct_expectation")
        self.assertEqual(union.cases[0].expectation.expectation_id, "same")
        self.assertEqual(union.cases[1].expectation.expectation_id, "distinct")

    def test_fresh_resource_reset_detects_tamper_and_copies_original(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "resources"
            source.mkdir()
            (source / "state.txt").write_text("original")
            package = LocalResourcePackage.from_directory("pkg-a", source)
            suite = Suite("T4", [self.mk_case("one", "T4"), self.mk_case("two", "T4")], resources={"pkg-a": package})

            first = replay_suite(suite, base_url=self.base_url, output_dir=tmp_path / "run1", mutate_resource={"state.txt": "changed"})
            self.assertEqual(first.applications[0]["pins_before"]["state.txt"]["sha256"], package.pins["state.txt"].sha256)
            self.assertNotEqual(first.applications[0]["pins_after"]["state.txt"]["sha256"], package.pins["state.txt"].sha256)

            second = replay_suite(suite, base_url=self.base_url, output_dir=tmp_path / "run2")
            work_file = Path(second.applications[0]["workdir"]) / "state.txt"
            self.assertEqual(work_file.read_text(), "original")
            self.assertEqual(second.applications[0]["pins_before"]["state.txt"]["sha256"], package.pins["state.txt"].sha256)

    def test_deadline_failure_is_separate_from_documented_http_500(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fail = self.mk_case("fail", "T2", path="/fail")
            slow = self.mk_case("slow", "T2", path="/slow")
            slow.timeout_seconds = 0.05
            suite = Suite("T2", [fail, slow])

            result = replay_suite(suite, base_url=self.base_url, output_dir=tmp_path / "run")

            self.assertEqual(result.totals["attempted"], 2)
            self.assertEqual(result.totals["completed"], 1)
            self.assertEqual(result.totals["deadline_failures"], 1)
            self.assertEqual(result.totals["http_failures"], 0)
            self.assertEqual(result.receipts[0]["status"], 500)
            self.assertIsNone(result.receipts[0]["failure_class"])
            self.assertEqual(result.receipts[1]["failure_class"], "deadline")
            self.assertEqual(len(RecordingHandler.seen), 2)

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

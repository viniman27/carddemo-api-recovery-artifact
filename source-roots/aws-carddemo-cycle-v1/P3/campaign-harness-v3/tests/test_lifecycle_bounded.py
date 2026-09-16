import json
import multiprocessing
import os
import signal
import subprocess
import sys
import textwrap
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from campaign_harness import Case, Expectation, HttpRequestSpec, PerApplicationHttpTarget, Suite, replay_suite  # noqa: E402


def mk_case(case_id, path="/ok", timeout=0.05):
    return Case(
        case_id=case_id,
        suite_id="PX",
        origin="lifecycle-probe",
        request=HttpRequestSpec("POST", path),
        resource_package_id="none",
        expectation=Expectation("ok", {"status": [200]}),
        timeout_seconds=timeout,
    )


class InfiniteHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    workdir = None

    def do_POST(self):
        while True:
            time.sleep(1)

    def log_message(self, *args):
        pass


class SlowHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    workdir = None

    def do_POST(self):
        Path(type(self).workdir, "seen.txt").write_text(self.path, encoding="utf-8")
        if self.path == "/slow":
            time.sleep(0.35)
        payload = b"{}"
        self.send_response(200)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        try:
            self.wfile.write(payload)
        except BrokenPipeError:
            pass

    def log_message(self, *args):
        pass


class FastHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    workdir = None

    def do_POST(self):
        payload = b"{}"
        self.send_response(200)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


class StartupFailHandler(BaseHTTPRequestHandler):
    campaign_harness_startup_fail = True


class StopFailHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    workdir = None

    def do_POST(self):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        Path(type(self).workdir, "pid.txt").write_text(str(os.getpid()), encoding="utf-8")
        while True:
            time.sleep(1)

    def log_message(self, *args):
        pass


class LifecycleBoundedTests(unittest.TestCase):
    def test_external_watchdog_does_not_kill_harness_for_infinite_handler(self):
        with TemporaryDirectory() as tmp:
            script = Path(tmp) / "child.py"
            out = Path(tmp) / "run"
            script.write_text(textwrap.dedent(f'''
                import json, sys, time
                from http.server import BaseHTTPRequestHandler
                from pathlib import Path
                sys.path.insert(0, {str(ROOT / "src")!r})
                from campaign_harness import Case, Expectation, HttpRequestSpec, PerApplicationHttpTarget, Suite, replay_suite
                class HangHandler(BaseHTTPRequestHandler):
                    protocol_version = "HTTP/1.1"
                    workdir = None
                    def do_POST(self):
                        Path(type(self).workdir, "attempts.txt").write_text("hit\\n", encoding="utf-8")
                        while True: time.sleep(1)
                    def log_message(self, *args): pass
                c = Case("hang", "PX", "probe", HttpRequestSpec("POST", "/hang"), "none", Expectation("ok", {{"status": [200]}}), timeout_seconds=0.05)
                started = time.monotonic()
                r = replay_suite(Suite("PX", [c]), target=PerApplicationHttpTarget(HangHandler), output_dir=Path({str(out)!r}))
                print(json.dumps({{"duration": time.monotonic() - started, "totals": r.totals, "apps": r.applications, "receipts": r.receipts}}))
            '''), encoding="utf-8")
            p = subprocess.run([sys.executable, str(script)], text=True, capture_output=True, timeout=3)
            self.assertEqual(p.returncode, 0, p.stderr)
            data = json.loads(p.stdout)
            self.assertLess(data["duration"], 2.5)
            self.assertEqual(data["totals"]["deadline_failures"], 1)
            self.assertEqual(data["apps"][0]["target_quiet"], True)
            self.assertTrue(data["apps"][0]["lifecycle"]["reaped"])
            self.assertFalse(data["apps"][0]["lifecycle"]["pid_alive_after_reap"])

    def test_infinite_handler_is_not_retried_and_next_case_is_not_started_when_quiet_unproved(self):
        # Static target remains deliberately unprovable after a deadline; this must abort rather than start the fast case.
        from http.server import HTTPServer
        server = HTTPServer(("127.0.0.1", 0), InfiniteHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with TemporaryDirectory() as tmp:
                base = f"http://127.0.0.1:{server.server_port}"
                r = replay_suite(Suite("PX", [mk_case("hang", "/hang"), mk_case("fast", "/fast", 0.5)]), base_url=base, output_dir=Path(tmp) / "run")
                self.assertEqual(r.totals["attempted"], 1)
                self.assertEqual(r.totals["not_executed"], 1)
                self.assertEqual(r.receipts[1]["failure_class"], "not_executed")
        finally:
            server.server_close()

    def test_slow_controlled_handler_is_reaped_before_fast_next_case(self):
        with TemporaryDirectory() as tmp:
            suite = Suite("PX", [mk_case("slow", "/slow", 0.05), mk_case("fast", "/fast", 0.5)])
            r = replay_suite(suite, target=PerApplicationHttpTarget(SlowHandler), output_dir=Path(tmp) / "run")
            self.assertEqual(r.totals["attempted"], 2)
            self.assertEqual(r.totals["deadline_failures"], 1)
            self.assertEqual(r.totals["completed"], 1)
            self.assertEqual(r.receipts[1]["status"], 200)
            self.assertTrue(all(a["target_quiet"] for a in r.applications))
            self.assertTrue(all(a["lifecycle"]["reaped"] for a in r.applications))
            self.assertTrue(all(not a["lifecycle"]["pid_alive_after_reap"] for a in r.applications))

    def test_startup_failure_aborts_remaining_not_executed(self):
        with TemporaryDirectory() as tmp:
            r = replay_suite(Suite("PX", [mk_case("boom", "/boom"), mk_case("fast", "/fast", 0.5)]), target=PerApplicationHttpTarget(StartupFailHandler), output_dir=Path(tmp) / "run")
            self.assertEqual(r.totals["attempted"], 1)
            self.assertEqual(r.totals["transport_failures"], 1)
            self.assertEqual(r.totals["not_executed"], 1)
            self.assertEqual(r.receipts[0]["failure_class"], "startup")
            self.assertIn("startup", r.receipts[1]["not_executed_reason"])

    def test_stop_failure_escalates_to_kill_reaps_and_leaves_no_target_process(self):
        with TemporaryDirectory() as tmp:
            before_children = {p.pid for p in multiprocessing.active_children()}
            r = replay_suite(Suite("PX", [mk_case("stop-fail", "/hang")]), target=PerApplicationHttpTarget(StopFailHandler, stop_timeout_seconds=0.05, terminate_timeout_seconds=0.05, kill_timeout_seconds=0.5), output_dir=Path(tmp) / "run")
            after_children = {p.pid for p in multiprocessing.active_children()}
            app = r.applications[0]
            self.assertEqual(r.totals["deadline_failures"], 1)
            self.assertEqual(app["target_quiet"], True)
            self.assertEqual(app["lifecycle"]["stop_method"], "kill")
            self.assertTrue(app["lifecycle"]["reaped"])
            self.assertFalse(app["lifecycle"]["pid_alive_after_reap"])
            self.assertEqual(after_children - before_children, set())


if __name__ == "__main__":
    unittest.main()

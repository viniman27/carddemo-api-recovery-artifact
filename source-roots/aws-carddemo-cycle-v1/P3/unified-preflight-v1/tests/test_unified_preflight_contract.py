
import ast
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

class UnifiedPreflightContractTests(unittest.TestCase):
    def test_imports_assert_exact_harness_v3_not_v2(self):
        cli = ROOT / "unified_preflight_cli.py"
        self.assertTrue(cli.is_file(), "unified CLI missing")
        text = cli.read_text()
        self.assertNotIn("campaign-harness-v2", text)
        self.assertIn("campaign-harness-v3", text)
        self.assertIn("assert_module_file_and_hash", text)

    def test_cli_routes_execution_through_replay_suite(self):
        cli = ROOT / "unified_preflight_cli.py"
        self.assertTrue(cli.is_file(), "unified CLI missing")
        tree = ast.parse(cli.read_text())
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        called = {getattr(c.func, 'id', None) or getattr(c.func, 'attr', None) for c in calls}
        self.assertIn("replay_suite", called, "CLI must call harness-v3 replay_suite directly")
        forbidden = {"send_json"}
        self.assertFalse(forbidden & called, f"bypass HTTP helpers present: {forbidden & called}")

    def test_subprocess_target_protocol_is_harness_compatible_and_quiet(self):
        sys.path.insert(0, str(SRC))
        from api_target import PosixSpawnServer
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            server_py = tmp_path / "srv.py"
            server_py.write_text(
                "import http.server, pathlib, sys\n"
                "p=pathlib.Path(sys.argv[1])\n"
                "class H(http.server.BaseHTTPRequestHandler):\n"
                "  def do_POST(self):\n"
                "    self.send_response(200); self.send_header('content-type','application/json'); self.end_headers(); self.wfile.write(b'{\\\"ok\\\":true}')\n"
                "  def log_message(self,*a): pass\n"
                "s=http.server.HTTPServer(('127.0.0.1',0), H); p.write_text(str(s.server_port)); s.serve_forever()\n"
            )
            target = PosixSpawnServer([sys.executable, str(server_py), "{port_file}"], cwd=tmp_path, env={})
            base = target.start(tmp_path / "app")
            self.assertTrue(base.startswith("http://127.0.0.1:"))
            self.assertTrue(target.stop())
            self.assertTrue(target.quiet())
            self.assertTrue(target.last_lifecycle.get("quiet_proven"))

if __name__ == "__main__":
    unittest.main()

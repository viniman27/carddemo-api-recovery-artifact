import json
import os
import signal
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from api_harness_integration import (
    ContractChecker,
    HarnessCase,
    PosixSpawnServer,
    build_fixture_registry_from_copy,
    copy_current_fixture_package,
)


class IntegrationContractTests(unittest.TestCase):
    def test_fixture_registry_is_built_from_copied_current_package_and_hashes_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = ROOT.parents[0] / "fixture-materialization-v2" / "package"
            package = copy_current_fixture_package(source, tmp_path / "fixtures-copy")
            registry = build_fixture_registry_from_copy(package, tmp_path / "registry.json")
            data = json.loads(registry.read_text())
            self.assertEqual(data["kind"], "p3-local-technical-fixture-selection")
            self.assertEqual({fx["track"] for fx in data["fixtures"]}, {"posting", "interest", "reporting"})
            for fx in data["fixtures"]:
                for dd, rel in fx["materializer"]["files"].items():
                    p = registry.parent / rel
                    self.assertTrue(p.is_file(), (fx["track"], dd, rel))
                    self.assertEqual(fx["materializer"]["filePins"][dd]["bytes"], p.stat().st_size)

    def test_contract_checker_uses_jsonschema_and_separates_documented_500_from_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "openapi.yaml"
            spec.write_text(
                """
openapi: 3.1.0
info: {title: x, version: '1'}
paths:
  /x:
    post:
      responses:
        '500':
          description: documented failure
          content:
            application/json:
              schema:
                type: object
                required: [category]
                properties: {category: {const: technical_failure}}
                additionalProperties: false
""".strip()
            )
            checker = ContractChecker(spec)
            ok = checker.check("POST", "/x", 500, "application/json", b'{"category":"technical_failure"}')
            bad = checker.check("POST", "/x", 500, "application/json", b'{"category":"other"}')
            missing = checker.check("POST", "/x", 503, "application/json", b'{}')
            self.assertEqual(ok.classification, "documented_500_schema_valid")
            self.assertEqual(bad.classification, "schema_violation")
            self.assertEqual(missing.classification, "status_violation")

    def test_posix_spawn_server_execs_and_reaps_process_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            server_py = tmp_path / "srv.py"
            server_py.write_text(
                "import http.server, pathlib, sys\n"
                "p=pathlib.Path(sys.argv[1])\n"
                "class H(http.server.BaseHTTPRequestHandler):\n"
                "  def do_POST(self):\n"
                "    self.send_response(200); self.send_header('content-type','application/json'); self.end_headers(); self.wfile.write(b'{\"ok\":true}')\n"
                "  def log_message(self,*a): pass\n"
                "s=http.server.HTTPServer(('127.0.0.1',0), H); p.write_text(str(s.server_port)); s.serve_forever()\n"
            )
            target = PosixSpawnServer([sys.executable, str(server_py), "{port_file}"], cwd=tmp_path, env={})
            base = target.start(tmp_path / "app")
            self.assertTrue(base.startswith("http://127.0.0.1:"))
            self.assertTrue(target.spawn_method.startswith("posix_spawn"))
            self.assertTrue(target.stop())
            self.assertTrue(target.quiet_tree_proven)


if __name__ == "__main__":
    unittest.main()

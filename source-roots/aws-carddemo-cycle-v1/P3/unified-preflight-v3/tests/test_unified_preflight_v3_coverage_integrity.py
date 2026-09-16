import json
import py_compile
import tempfile
import time
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import unified_preflight_cli as cli


class UnifiedPreflightV3CoverageIntegrityTests(unittest.TestCase):
    def test_red_v2_artifacts_contain_stamp_mismatch_and_are_not_admissible(self):
        report = json.loads((P3 / "unified-preflight-v2" / "evidence-20260915T141606Z" / "unified-preflight-report.json").read_text())
        checks = report["runs"]["unionFirst"]["checks"] + report["runs"]["unionResetQualificationNotT4"]["checks"]
        mismatches = [c for c in checks if "stamp mismatch" in c.get("coverage", {}).get("gcov11", {}).get("stderr", "")]
        self.assertEqual(len(mismatches), 8)
        for check in mismatches:
            validation = cli.validate_gcov_record(check["coverage"]["gcov11"])
            self.assertFalse(validation["valid"])
            self.assertIn("gcov_stderr_not_empty", validation["reasons"])
            self.assertIn("stamp_mismatch", validation["reasons"])

    def test_gcov_error_is_rejected_not_zero_coverage(self):
        record = {"exit_code": 0, "stdout": "Lines executed:0.00% of 1120\nCreating 'CBTRN02C.c.gcov'\n", "stderr": "CBTRN02C.gcda:stamp mismatch with notes file\n", "summaryParsed": {"linesTotal": 1120, "linesPercent": 0.0}}
        validation = cli.validate_gcov_record(record)
        self.assertFalse(validation["valid"])
        self.assertNotEqual(validation.get("classification"), "valid_zero_coverage")

    def test_gcov_valid_zero_is_allowed_only_with_clean_exit_and_clean_stderr(self):
        record = {"exit_code": 0, "stdout": "Lines executed:0.00% of 1120\n", "stderr": "", "summaryParsed": {"linesTotal": 1120, "linesPercent": 0.0}}
        validation = cli.validate_gcov_record(record)
        self.assertTrue(validation["valid"])
        self.assertEqual(validation["classification"], "valid_zero_coverage")

    def test_collects_binary_gcno_gcda_hash_linkage_for_exact_invocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "posting-1"
            gcov = run / "gcov"
            build = Path(tmp) / "build"
            gcov.mkdir(parents=True)
            build.mkdir()
            binary = build / "CBTRN02C"
            gcno = build / "CBTRN02C-CBTRN02C.gcno"
            gcda = gcov / "CBTRN02C-CBTRN02C.gcda"
            binary.write_bytes(b"binary")
            gcno.write_bytes(b"gcno")
            gcda.write_bytes(b"gcda")
            links = cli.coverage_artifact_links(run, "CBTRN02C", build)
            self.assertEqual(len(links["pairs"]), 1)
            pair = links["pairs"][0]
            self.assertEqual(pair["binary"]["sha256"], cli.sha256_path(binary))
            self.assertEqual(pair["gcno"]["sha256"], cli.sha256_path(gcno))
            self.assertEqual(pair["gcda"]["sha256"], cli.sha256_path(gcda))

    def test_reset_comparison_surfaces_integral_pre_post_resource_hash_sets(self):
        first = {"checks": [{"case_id": "case", "coverage": {"track": "posting", "runDir": "/r1", "gcovPrefix": "/r1/gcov"}, "reach": {"audit": {"STATE": {"pre_cobol_materialization": {"files": [{"path": "A", "sha256": "1"}]}, "after": {"files": [{"path": "A", "sha256": "2"}, {"path": "B", "sha256": "3"}]}}}}}]}
        second = {"checks": [{"case_id": "case", "coverage": {"track": "posting", "runDir": "/r2", "gcovPrefix": "/r2/gcov"}, "reach": {"audit": {"STATE": {"pre_cobol_materialization": {"files": [{"path": "A", "sha256": "1"}]}, "after": {"files": [{"path": "A", "sha256": "2"}, {"path": "B", "sha256": "3"}]}}}}}]}
        row = cli.reset_comparison(first, second)[0]
        self.assertEqual(row["firstResourcePreHashes"], {"A": "1"})
        self.assertEqual(row["firstResourcePostHashes"], {"A": "2", "B": "3"})
        self.assertEqual(row["resourcePathSetComparison"], "integral_pre_and_post_sets")
        self.assertTrue(row["effectiveResourceHashesCompared"])
    def test_run_gcov_uses_actual_business_gcda_path_for_prefixed_counter_names(self):
        cov = cli.load_coverage_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p2b = root / "P2b"
            build = p2b / "build"
            run_dir = p2b / "runs" / "posting-1"
            gcov_dir = run_dir / "gcov"
            build.mkdir(parents=True)
            gcov_dir.mkdir(parents=True)
            (build / "CBTRN02C.c").write_text("int main(void){return 0;}\n")
            (build / "CBTRN02C-CBTRN02C.gcno").write_bytes(b"notes")
            gcda = gcov_dir / "CBTRN02C-CBTRN02C.gcda"
            gcda.write_bytes(b"data")
            calls = []
            original_run = cov.run
            try:
                def fake_run(cmd, cwd, *, expect=None):
                    calls.append([str(x) for x in cmd])
                    return {"exit_code": 0, "stdout": "Lines executed:1.00% of 1\n", "stderr": ""}
                cov.run = fake_run
                rec = cov.run_gcov_for_invocation(p2b, run_dir, "CBTRN02C", [gcda])
            finally:
                cov.run = original_run
            self.assertEqual(calls[0][4], str(gcda.resolve()))
            self.assertEqual(rec["gcdaObjectFile"]["path"], str(gcda.resolve()))

    def test_patch_isolated_fewshot_facade_routes_business_commands_to_same_invocation_gcov_and_p2b_log(self):
        cov = cli.load_coverage_runner()
        with tempfile.TemporaryDirectory() as tmp:
            cycle = Path(tmp) / "aws-carddemo-cycle-v1"
            p2c = cycle / "P2c-few-shot"
            p2c.mkdir(parents=True)
            facade = p2c / "p2c_facade.py"
            facade.write_text('''from pathlib import Path
P2B = Path('/iso/P2b')
ROOT = Path('/iso/P2c-few-shot')
RUNS = ROOT / 'runs'
OUTPUTS = ROOT / 'outputs'
def load_p2b():
    module.RUNS = RUNS / "p2b-redirected"
    module.COMMAND_LOG = OUTPUTS / "p2b-command-log.jsonl"
def _capture_and_write(audit, wd):
    audit["STATE"]["after"] = load_p2b().capture_state_snapshot(wd)
    (wd / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\\n")
def run_posting(p2b, wd):
    return p2b.run_cmd([p2b.BUILD / "CBTRN02C"], cwd=wd, env={"COB_LIBRARY_PATH": str(p2b.BUILD), "P2B_INVOCATION": wd.name, "P2B_WRITE_LOG": str(wd / "write-observations.log"), **{f"DD_{dd}": str(wd / dd) for dd in [*p2b.SIZES, "DALYTRAN", "DALYREJS"]}}, expect=None)
def run_interest(p2b, wd):
    return p2b.run_cmd([driver], cwd=wd, env={"COB_LIBRARY_PATH": f"{p2b.BUILD}{os.pathsep}{P2C_BUILD}", "P2C_PARM_LENGTH": str(parameter_length), **{f"DD_{dd}": str(wd / dd) for dd in (*p2b.RESOURCE_NAMES["interest"], "TRANSACT")}}, expect=None)
def run_reporting(p2b, wd):
    return p2b.run_cmd([p2b.BUILD / "CBTRN03C"], cwd=wd, env={"COB_LIBRARY_PATH": str(p2b.BUILD), **{f"DD_{dd}": str(wd / dd) for dd in (*p2b.RESOURCE_NAMES["reporting"], "TRANREPT")}}, expect=None)
''')
            info = cov.patch_isolated_p2c_fewshot(cycle)
            text = facade.read_text()
            self.assertEqual(info["patchScope"], "isolated P2c few-shot copy only")
            self.assertIn("module.COMMAND_LOG = P2B / \"command-log.jsonl\"", text)
            self.assertEqual(text.count('"GCOV_PREFIX": str(wd / "gcov")'), 3)
            self.assertEqual(text.count('"GCOV_PREFIX_STRIP": str(len(p2b.BUILD.resolve().parts))'), 3)
            self.assertIn('audit.setdefault("MEASUREMENT"', text)

    def test_command_log_env_maps_p2c_interest_driver_to_cbact04c_business_program(self):
        cov = cli.load_coverage_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p2b = root / "P2b"
            run_dir = root / "P2c-few-shot" / "runs" / "p2b-redirected" / "interest-1"
            run_dir.mkdir(parents=True)
            p2b.mkdir()
            expected = str(run_dir / "gcov")
            (p2b / "command-log.jsonl").write_text(json.dumps({
                "cmd": ["/iso/P2c-few-shot/build/P2C_INTEREST_DRIVER"],
                "cwd": str(run_dir),
                "exit_code": 0,
                "env_override": {"GCOV_PREFIX": expected, "COB_LIBRARY_PATH": "/iso/P2b/build:/iso/P2c-few-shot/build"},
            }) + "\n", encoding="utf-8")
            rows = cov.command_log_env_for_run(p2b, run_dir, "CBACT04C")
            self.assertEqual(rows[0]["env_subset"]["GCOV_PREFIX"], expected)

    def test_command_log_env_finds_zero_shot_facade_redirected_log_from_audit_run_dir(self):
        cov = cli.load_coverage_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p2b = root / "isolated-cycle" / "aws-carddemo-cycle-v1" / "P2b"
            run_dir = root / "case" / "replay" / "applications" / "0001" / "zero-shot-runs" / "p2b-runs" / "posting-1"
            run_dir.mkdir(parents=True)
            p2b.mkdir(parents=True)
            expected = str(run_dir / "gcov")
            facade_log = run_dir.parents[1] / "command-log.jsonl"
            facade_log.write_text(json.dumps({
                "cmd": [str(p2b / "build" / "CBTRN02C")],
                "cwd": str(run_dir),
                "exit_code": 0,
                "env_override": {"GCOV_PREFIX": expected, "COB_LIBRARY_PATH": str(p2b / "build")},
            }) + "\n", encoding="utf-8")
            rows = cov.command_log_env_for_run(p2b, run_dir, "CBTRN02C")
            self.assertEqual(rows[0]["env_subset"]["GCOV_PREFIX"], expected)

    def test_generated_isolated_bindings_compile_after_all_patches(self):
        with tempfile.TemporaryDirectory() as tmp:
            prep = cli.prepare_isolated_workspace(Path(tmp) / "out")
            for rel in ["P2b/p2b_binding.py", "P2c-few-shot/p2c_facade.py"]:
                py_compile.compile(str(Path(prep["cycle"]) / rel), doraise=True)
            self.assertIn("isolatedP2cFewshotCoveragePatch", prep)

    def test_server_start_compiles_python_entrypoint_before_waiting_for_port(self):
        sys.path.insert(0, str(ROOT / "src"))
        from api_target import PosixSpawnServer
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bad = tmp_path / "bad_server.py"
            bad.write_text("if True:\nprint('bad indent')\n")
            target = PosixSpawnServer([sys.executable, str(bad), "{port_file}"], cwd=tmp_path, env={})
            started = time.time()
            with self.assertRaises(RuntimeError) as cm:
                target.start(tmp_path / "app")
            elapsed = time.time() - started
            self.assertLess(elapsed, 2.0)
            self.assertIn("py_compile", str(cm.exception))
            self.assertIn("bad_server.py", str(cm.exception))


if __name__ == "__main__":
    unittest.main()

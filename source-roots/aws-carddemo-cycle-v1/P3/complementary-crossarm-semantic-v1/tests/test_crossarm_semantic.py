import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = ROOT / "P3" / "complementary-crossarm-semantic-v1"
RUN = ROOT / "P3" / "complementary-crossarm-v1" / "run-20260916T112642Z"

sys.path.insert(0, str(PKG))

class CrossarmSemanticTests(unittest.TestCase):
    def test_file_exists_wrong_same_length_posted_value_fails(self):
        from crossarm_semantic import semantic
        case = next(c for c in json.loads((RUN/"comparison.json").read_text())["cases"] if c["caseId"] == "CROSSARM-E1-1-posting")
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            work = td / "posting"
            shutil.copytree(Path(case["businessCheck"]["evidence"][0]["path"]).parent, work)
            raw = bytearray((work / "TRANFILE.after").read_bytes())
            # Same length, actual semantic value changed: transaction id no longer matches input-derived accepted source record.
            raw[0:16] = b"WRONG-ID-000000X"
            (work / "TRANFILE.after").write_bytes(raw)
            fake = json.loads(json.dumps(case))
            fake["businessCheck"]["evidence"][0]["path"] = str(work / "TRANFILE.after")
            fake["businessCheck"]["evidence"][0]["sha256"] = semantic.sha256_file(work / "TRANFILE.after")
            fake["businessCheck"]["evidence"][0]["bytes"] = (work / "TRANFILE.after").stat().st_size
            result = semantic.semantic_check_case(fake)
        statuses = {r["obligationId"]: r["status"] for r in result["checkerResults"]}
        self.assertEqual("failed", statuses["POSTTRAN-OBL-003"])
        self.assertIn("not copied", "; ".join(result["checkerResults"][0]["details"].get("failures", [])))

    def test_cli_binds_actual_preserved_21_without_api_reruns(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "results.json"
            completed = subprocess.run([sys.executable, "-m", "crossarm_semantic", "--run-root", str(RUN), "--cycle-root", str(ROOT), "--out", str(out)], cwd=PKG, text=True, capture_output=True, check=False)
            self.assertEqual(0, completed.returncode, completed.stderr)
            payload = json.loads(out.read_text())
        self.assertEqual(21, payload["summary"]["caseCount"])
        self.assertEqual({"posting": 7, "interest": 7, "reporting": 7}, payload["summary"]["caseCountsByTrack"])
        self.assertTrue(payload["summary"]["noApiReruns"])
        self.assertNotIn("businessvalidation", json.dumps(payload).lower())
        self.assertEqual(0, payload["summary"]["pinVerificationFailureCount"])
        self.assertEqual(21, len({c["caseId"] for c in payload["cases"]}))
        self.assertEqual(7, payload["summary"]["caseCountsByTrack"]["posting"])
        self.assertGreater(payload["summary"]["checkerStatusCounts"].get("pass", 0), 0)
        self.assertGreater(payload["summary"]["checkerStatusCounts"].get("inconclusive", 0), 0)
        posting = next(c for c in payload["cases"] if c["caseId"] == "CROSSARM-E1-1-posting")
        self.assertEqual("pass", {r["obligationId"]: r["status"] for r in posting["checkerResults"]}["POSTTRAN-OBL-003"])
        self.assertEqual("inconclusive", {r["obligationId"]: r["status"] for r in posting["checkerResults"]}["POSTTRAN-OBL-009"])
        self.assertIn("apiVisibleEvidence", posting)
        self.assertIn("rawCobolEffects", posting)

if __name__ == "__main__":
    unittest.main()

import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "final_coverage_ledger.py"
FIXTURES = ROOT / "tests" / "fixtures"


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def run_cli(tmp_path: Path, *extra):
    out = tmp_path / "out"
    cmd = [
        "python3", str(SCRIPT),
        "--catalog", str(FIXTURES / "catalog.json"),
        "--semantic-results", str(FIXTURES / "semantic.json"),
        "--model-registry", str(FIXTURES / "model-registry.json"),
        "--coverage-report", str(FIXTURES / "coverage.json"),
        "--campaign-coverage-csv", str(FIXTURES / "coverage.csv"),
        "--out-dir", str(out),
        *extra,
    ]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return completed, out


class FinalCoverageLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        FIXTURES.mkdir(parents=True, exist_ok=True)
        write_json(FIXTURES / "catalog.json", {
            "kind": "test-catalog",
            "denominators": {"obligationsTotal": 2, "contractsTotal": 2, "candidateApplicableObligationContractCells": 4, "obligationOperationCellsIllustrative": 12},
            "contracts": [
                {"contractId": "C1", "arm": "zero-shot", "operations": [{"operationId": "posting", "track": "posting"}, {"operationId": "interest", "track": "interest"}, {"operationId": "reporting", "track": "reporting"}]},
                {"contractId": "C2", "arm": "few-shot", "operations": [{"operationId": "posting", "track": "posting"}, {"operationId": "interest", "track": "interest"}, {"operationId": "reporting", "track": "reporting"}]},
            ],
            "scenarioRecords": [
                {"obligationId": "P-1", "track": "posting", "boundaryPartitions": [{"id": "ok"}, {"id": "neg"}]},
                {"obligationId": "I-1", "track": "interest", "boundaryPartitions": [{"id": "rate"}]},
            ],
            "obligationOperationMapping": [
                {"cellId": "P-1::C1::posting", "obligationId": "P-1", "contractId": "C1", "operationId": "posting", "operationTrack": "posting", "obligationTrack": "posting", "denominatorMembership": {"semanticDenominator": True}},
                {"cellId": "P-1::C2::posting", "obligationId": "P-1", "contractId": "C2", "operationId": "posting", "operationTrack": "posting", "obligationTrack": "posting", "denominatorMembership": {"semanticDenominator": True}},
                {"cellId": "I-1::C1::interest", "obligationId": "I-1", "contractId": "C1", "operationId": "interest", "operationTrack": "interest", "obligationTrack": "interest", "denominatorMembership": {"semanticDenominator": True}},
                {"cellId": "I-1::C2::interest", "obligationId": "I-1", "contractId": "C2", "operationId": "interest", "operationTrack": "interest", "obligationTrack": "interest", "denominatorMembership": {"semanticDenominator": True}},
                {"cellId": "P-1::C1::interest", "obligationId": "P-1", "contractId": "C1", "operationId": "interest", "operationTrack": "interest", "obligationTrack": "posting", "denominatorMembership": {"semanticDenominator": False}},
            ]
        })
        write_json(FIXTURES / "semantic.json", {
            "kind": "semantic-fixture",
            "scope": "actual saved evidence fixture",
            "cases": [
                {"caseId": "s1", "contractId": "C1", "operationId": "posting", "track": "posting", "semanticStatus": "pass", "checkerResults": [{"obligationId": "P-1", "status": "pass", "partitions": ["ok"]}]},
                {"caseId": "s2", "contractId": "C2", "operationId": "posting", "track": "posting", "semanticStatus": "failed", "checkerResults": [{"obligationId": "P-1", "status": "failed", "partitions": ["neg"]}]},
                {"caseId": "s3", "contractId": "C1", "operationId": "interest", "track": "interest", "semanticStatus": "pass", "checkerResults": [{"obligationId": "I-1", "status": "pass", "partitions": ["rate"]}]},
            ],
        })
        write_json(FIXTURES / "model-registry.json", {"cases": [{"caseId": "m1", "track": "posting", "classification": "eligible_t3_candidate", "modelTrace": [{"obligationRefs": ["P-1"], "guardResult": True, "qualified": True}]}]})
        write_json(FIXTURES / "coverage.json", {"invocations": [
            {"track": "posting", "businessProgram": "CBTRN02C", "measurementAdmissibility": "admissible_preparatory", "unitBreakdown": [{"classification": "main_generated_c", "sha256": "aaa", "source": "CBTRN02C.c", "lines": {"executed": 3, "total": 10}, "branches": {"executed": 5, "taken_at_least_once": 2, "total": 8}}]},
            {"track": "posting", "businessProgram": "CBTRN02C", "measurementAdmissibility": "admissible_preparatory", "unitBreakdown": [{"classification": "main_generated_c", "sha256": "bbb", "source": "CBTRN02C.c", "lines": {"executed": 4, "total": 10}, "branches": {"executed": 6, "taken_at_least_once": 3, "total": 8}}]},
            {"track": "interest", "businessProgram": "CBACT04C", "measurementAdmissibility": "admissible_preparatory", "unitBreakdown": [{"classification": "main_generated_c", "sha256": "ccc", "source": "CBACT04C.c", "lines": {"executed": 7, "total": 10}, "branches": {"executed": 1, "taken_at_least_once": 1, "total": 2}}]},
        ]})
        with (FIXTURES / "coverage.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["arm", "contract_id", "condition", "track", "business_program", "union_executed_lines", "union_total_lines"])
            writer.writeheader()
            writer.writerow({"arm": "zero-shot", "contract_id": "C1", "condition": "T3", "track": "posting", "business_program": "CBTRN02C", "union_executed_lines": "9", "union_total_lines": "10"})

    def test_cli_rejects_missing_scope_in_semantic_results(self):
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            bad = tmp_path / "bad-semantic.json"
            write_json(bad, {"cases": []})
            completed, _ = run_cli(tmp_path, "--semantic-results", str(bad))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("scope", completed.stderr)

    def test_ledger_uses_semantic_denominator_not_gross_and_keeps_na_separate(self):
        with tempfile.TemporaryDirectory() as td:
            completed, out = run_cli(Path(td))
            self.assertEqual(completed.returncode, 0, completed.stderr)
            ledger = json.loads((out / "acceptance-ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(ledger["denominators"]["semantic"], 4)
        self.assertEqual(ledger["denominators"]["grossIllustrative"], 12)
        self.assertEqual(ledger["summary"]["byStatus"]["covered_checked"], 2)
        self.assertEqual(ledger["summary"]["byStatus"]["failed"], 1)
        self.assertEqual(ledger["summary"]["byStatus"]["not_exercised"], 1)
        self.assertEqual(ledger["summary"]["notApplicableCells"], 1)
        self.assertFalse(any(c["status"] == "N/A" for c in ledger["cells"] if c["semanticDenominator"]))

    def test_gcov_separates_mismatched_main_c_fingerprints(self):
        with tempfile.TemporaryDirectory() as td:
            completed, out = run_cli(Path(td))
            self.assertEqual(completed.returncode, 0, completed.stderr)
            ledger = json.loads((out / "acceptance-ledger.json").read_text(encoding="utf-8"))
        posting = ledger["gcov"]["programs"]["CBTRN02C"]
        self.assertEqual(posting["comparability"], "separate_fingerprints_not_unionable")
        self.assertTrue(posting["comparabilityGaps"])
        self.assertEqual({s["sourceFingerprintSha256"] for s in posting["separateSeries"]}, {"aaa", "bbb"})
        self.assertNotIn("union", posting)

    def test_generates_ptbr_report_and_machine_ledger(self):
        with tempfile.TemporaryDirectory() as td:
            completed, out = run_cli(Path(td))
            self.assertEqual(completed.returncode, 0, completed.stderr)
            text = (out / "final-coverage-report.md").read_text(encoding="utf-8")
        self.assertIn("# Ledger final de cobertura defensável", text)
        self.assertIn("Denominador semântico", text)
        self.assertIn("Lacunas decisivas", text)


if __name__ == "__main__":
    unittest.main()

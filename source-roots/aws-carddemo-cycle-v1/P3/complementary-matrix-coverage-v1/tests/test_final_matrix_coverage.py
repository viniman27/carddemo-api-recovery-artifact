import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("final_matrix_coverage", ROOT / "final_matrix_coverage.py")
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class FinalMatrixCoverageTests(unittest.TestCase):
    def test_parse_gcov_distinguishes_branch_executed_from_taken(self):
        with tempfile.TemporaryDirectory() as td:
            gcov = Path(td) / "x.c.gcov"
            gcov.write_text(
                "        -:    0:Source:x.c\n"
                "        1:   10:if (a) {}\n"
                "branch  0 taken 0%\n"
                "branch  1 taken 100%\n"
                "    #####:   11:if (b) {}\n"
                "branch  0 never executed\n"
                "        -:   12:}\n",
                encoding="utf-8",
            )
            parsed = mod.parse_gcov_main(gcov, "sha")
        counts = mod.cov_counts(parsed)
        self.assertEqual(counts["lines"], {"executed": 1, "total": 2, "percent": 50.0})
        self.assertEqual(counts["branches_executed"], {"executed": 2, "total": 3, "percent": 66.67})
        self.assertEqual(counts["branches_taken_at_least_once"], {"taken": 1, "total": 3, "percent": 33.33})

    def test_union_counts_line_and_branch_ids_once(self):
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "a.gcov"
            b = Path(td) / "b.gcov"
            a.write_text("1: 1:x\nbranch 0 taken 100%\n#####: 2:y\nbranch 0 never executed\n", encoding="utf-8")
            b.write_text("1: 1:x\nbranch 0 taken 100%\n1: 2:y\nbranch 0 taken 0%\n", encoding="utf-8")
            union = mod.empty_sets()
            mod.union_into(union, mod.parse_gcov_main(a, "sha"))
            mod.union_into(union, mod.parse_gcov_main(b, "sha"))
        counts = mod.cov_counts(union)
        self.assertEqual(counts["lines"]["executed"], 2)
        self.assertEqual(counts["lines"]["total"], 2)
        self.assertEqual(counts["branches_executed"]["executed"], 2)
        self.assertEqual(counts["branches_taken_at_least_once"]["taken"], 1)


if __name__ == "__main__":
    unittest.main()

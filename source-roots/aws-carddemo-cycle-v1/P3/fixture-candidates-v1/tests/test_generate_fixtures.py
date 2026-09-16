import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_generator():
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_fixtures.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


class FixtureGeneratorTests(unittest.TestCase):
    def test_generator_materializes_required_manifest_and_binary_records(self):
        result = run_generator()
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "candidate_needs_review")
        tracks = {fixture["track"] for fixture in manifest["fixtures"]}
        self.assertEqual(tracks, {"posting", "interest", "reporting"})

        resources = {r["path"]: r for r in manifest["resources"]}
        for path, expected_record_len in {
            "data/sequential/posting/DALYTRAN.dat": 350,
            "data/sequential/interest/TCATBALF.dat": 50,
            "data/sequential/reporting/TRANFILE.dat": 350,
            "data/sequential/reporting/DATEPARM.dat": 80,
        }.items():
            payload = (ROOT / path).read_bytes()
            self.assertEqual(len(payload) % expected_record_len, 0)
            self.assertEqual(resources[path]["bytes"], len(payload))
            self.assertEqual(len(resources[path]["sha256"]), 64)
            self.assertEqual(resources[path]["encoding"], "ascii-fixed-width-no-newline")

    def test_indexed_resources_are_logical_not_claimed_bdb_ready(self):
        result = run_generator()
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        blockers = manifest["indexed_resource_materialization"]["blockers"]
        self.assertTrue(any("Berkeley DB/GnuCOBOL" in blocker for blocker in blockers))
        indexed = [r for r in manifest["resources"] if r["kind"] == "indexed-logical-jsonl"]
        self.assertTrue(indexed)
        self.assertTrue(all(r["materialization_status"] == "logical_bytes_only_candidate" for r in indexed))
        self.assertTrue(any("XREFFILE.1" in component for r in indexed for component in r.get("physical_components_required", [])))

    def test_required_families_are_declared_without_expected_outputs(self):
        result = run_generator()
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        family_ids = {family["id"] for family in manifest["selection_families"]}
        self.assertTrue({
            "posting.lookup.present",
            "posting.lookup.absent",
            "interest.rate.zero",
            "interest.rate.nonzero",
            "reporting.empty-input",
            "reporting.absent-input-blocked",
            "reporting.date-selection",
        }.issubset(family_ids))
        self.assertNotIn("expected_outputs", manifest)
        self.assertTrue(all("expected" not in json.dumps(fixture).lower() for fixture in manifest["fixtures"]))


if __name__ == "__main__":
    unittest.main()

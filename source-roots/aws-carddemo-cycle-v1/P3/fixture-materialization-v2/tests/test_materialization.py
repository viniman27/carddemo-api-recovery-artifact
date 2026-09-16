from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args):
    return subprocess.run([sys.executable, str(ROOT / 'tools' / 'materialize_candidates.py'), *args], cwd=ROOT, text=True, capture_output=True)


class MaterializationTests(unittest.TestCase):
    def test_cli_materializes_all_three_tracks_with_physical_sidecars_and_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'package'
            result = run_cli('--output', str(out))
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((out / 'manifest.json').read_text())
            self.assertEqual(manifest['status'], 'candidate_needs_review')
            self.assertEqual({fx['track'] for fx in manifest['fixtures']}, {'posting', 'interest', 'reporting'})
            self.assertFalse(manifest['claims']['business_cobol_executed'])
            self.assertFalse(manifest['claims']['expected_outputs_created'])
            for track in ['posting', 'interest', 'reporting']:
                pkg = out / track
                self.assertTrue(pkg.is_dir())
                inv = manifest['packages'][track]['inventory']
                for rel, pin in inv['files'].items():
                    p = pkg / rel
                    self.assertTrue(p.exists(), rel)
                    self.assertEqual(p.stat().st_size, pin['bytes'])
                if track == 'interest':
                    self.assertTrue((pkg / 'XREFFILE.1').exists())
            self.assertTrue(manifest['reset_verification']['resetVerified'])

    def test_cli_reader_verifies_logical_images_keys_and_alternates(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'package'
            self.assertEqual(run_cli('--output', str(out)).returncode, 0)
            result = run_cli('--verify-only', str(out))
            self.assertEqual(result.returncode, 0, result.stderr)
            verification = json.loads((out / 'verification.json').read_text())
            self.assertEqual(verification['status'], 'pass')
            self.assertEqual(verification['datasets']['interest']['XREFFILE']['alternateKeyName'], 'FD-XREF-ACCT-ID')
            self.assertEqual(verification['datasets']['interest']['XREFFILE']['alternateKeys'], ['10000000001', '10000000002'])
            self.assertEqual(verification['datasets']['posting']['DALYTRAN']['recordCount'], 2)
            self.assertEqual(verification['datasets']['reporting']['TRANFILE.empty']['recordCount'], 0)

    def test_s9_display_runtime_probe_is_recorded_and_no_negative_s9_candidates(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'package'
            self.assertEqual(run_cli('--output', str(out)).returncode, 0)
            byte_review = json.loads((out / 'byte-layout-review.json').read_text())
            self.assertTrue(byte_review['native_display_probe']['negative_s9_9v99_minus_123_hex'].endswith('73'))
            self.assertEqual(byte_review['candidate_s9_values']['negative_values_found'], [])
            self.assertEqual(byte_review['candidate_s9_values']['sign_policy'], 'unsigned candidate magnitudes only; no negative S9 DISPLAY emitted in v1/v2')

if __name__ == '__main__':
    unittest.main()

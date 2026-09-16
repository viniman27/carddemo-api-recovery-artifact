"""Synthetic framework checks; never AWS extraction or research results."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / 'pipeline/tools/check_anchors.py'


class SourceAnchorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.corpus = self.root / 'corpus'
        self.corpus.mkdir()
        self.source = self.corpus / 'cbl/main.cbl'
        self.source.parent.mkdir()
        self.source.write_bytes(b'       IDENTIFICATION DIVISION.\n       PROGRAM-ID. SAMPLE.\n')
        self.manifest = {'files': [{'path': 'cbl/main.cbl',
                                   'sha256': hashlib.sha256(self.source.read_bytes()).hexdigest()}]}
        self.register = {'items': [{'id': 'E-1', 'spec_section': 'Section 2.1',
                                   'anchors': [{'path': 'cbl/main.cbl', 'start': 1, 'end': 2}]}]}

    def run_check(self):
        manifest = self.root / 'manifest.json'
        register = self.root / 'anchors.json'
        manifest.write_text(json.dumps(self.manifest))
        register.write_text(json.dumps(self.register))
        return subprocess.run([sys.executable, str(TOOL), str(self.corpus), str(manifest), str(register)],
                              text=True, capture_output=True)

    def test_valid_source_anchor_reports_only_mechanical_success(self):
        proc = self.run_check()
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        data = json.loads(proc.stdout)
        self.assertTrue(data['ok'])
        self.assertEqual(data['evidence_checked'], 1)
        self.assertIs(data['human_approval'], False)

    def test_incomplete_or_malformed_register_never_passes(self):
        import copy
        valid = copy.deepcopy(self.register)
        invalid = [
            {}, {'items': []}, {'items': [None]},
            {'items': [dict(valid['items'][0], anchors=[])]},
            {'items': [dict(valid['items'][0], id='E-0')]},
            {'items': [dict(valid['items'][0], spec_section='')]},
            {'items': valid['items'] * 2},
            {'items': [dict(valid['items'][0], anchors=[{'path': 'cbl/main.cbl', 'start': True, 'end': 2}])]},
        ]
        for register in invalid:
            with self.subTest(register=register):
                self.register = register
                proc = self.run_check()
                self.assertEqual(proc.returncode, 1, proc.stderr or proc.stdout)
                data = json.loads(proc.stdout)
                self.assertFalse(data['ok'])
                self.assertTrue(data['errors'])
                self.assertFalse(data['human_approval'])

    def test_manifest_membership_is_exact_and_never_follows_aliases(self):
        import copy
        original = copy.deepcopy(self.manifest)
        source_hash = original['files'][0]['sha256']
        outside = self.root / 'outside.cbl'
        outside.write_bytes(self.source.read_bytes())
        alias = self.corpus / 'alias.cbl'
        alias.symlink_to(outside)
        bad_paths = ['../outside.cbl', str(outside), 'alias.cbl', './cbl/main.cbl',
                     'cbl/../cbl/main.cbl', 'cbl//main.cbl']
        for path in bad_paths:
            with self.subTest(path=path):
                self.manifest = {'files': [{'path': path, 'sha256': source_hash}]}
                self.register['items'][0]['anchors'][0]['path'] = path
                proc = self.run_check()
                self.assertEqual(proc.returncode, 1, proc.stdout)
                self.assertFalse(json.loads(proc.stdout)['ok'])
        self.register['items'][0]['anchors'][0]['path'] = 'cbl/main.cbl'
        for manifest in [{}, {'files': []}, {'files': original['files'] * 2},
                         {'files': [{'path': 'cbl/main.cbl', 'sha256': source_hash.upper()}]}]:
            with self.subTest(manifest=manifest):
                self.manifest = manifest
                proc = self.run_check()
                self.assertEqual(proc.returncode, 1, proc.stdout)
                self.assertFalse(json.loads(proc.stdout)['ok'])

    def test_homonymous_sources_remain_distinct(self):
        other = self.corpus / 'copy/main.cbl'
        other.parent.mkdir()
        other.write_bytes(b'one line\n')
        self.manifest['files'].append({'path': 'copy/main.cbl', 'sha256': hashlib.sha256(other.read_bytes()).hexdigest()})
        self.assertEqual(self.run_check().returncode, 0)
        self.register['items'][0]['anchors'][0]['path'] = 'copy/main.cbl'
        proc = self.run_check()
        self.assertEqual(proc.returncode, 1)
        self.assertIn('range', proc.stdout)

    def test_tampered_source_is_rejected(self):
        self.source.write_bytes(b'changed\n')
        proc = self.run_check()
        self.assertEqual(proc.returncode, 1)
        self.assertIn('hash mismatch', proc.stdout)

    def test_unlisted_source_is_rejected_even_when_present(self):
        other = self.corpus / 'support.cbl'
        other.write_bytes(self.source.read_bytes())
        self.register['items'][0]['anchors'][0]['path'] = 'support.cbl'
        proc = self.run_check()
        self.assertEqual(proc.returncode, 1)
        self.assertIn('outside manifest', proc.stdout)

    def test_invalid_ranges_and_trailing_newline_are_rejected(self):
        for start, end in [(0, 1), (2, 1), (1, 3)]:
            with self.subTest(start=start, end=end):
                anchor = self.register['items'][0]['anchors'][0]
                anchor.update(start=start, end=end)
                proc = self.run_check()
                self.assertEqual(proc.returncode, 1)
                self.assertIn('range', proc.stdout)


if __name__ == '__main__':
    unittest.main()

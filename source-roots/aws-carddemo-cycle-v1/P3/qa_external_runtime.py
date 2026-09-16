#!/usr/bin/env python3
"""Explicit technical integration QA. Not collected by campaign/config tests.
Run from P3: ../P2a/.venv/bin/python qa_external_runtime.py
Build must already exist. Never generates official cases or runs a campaign.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('binding', ROOT.parent / 'P2b/p2b_binding.py')
assert spec is not None and spec.loader is not None
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class ExternalRuntimeQA(unittest.TestCase):
    def test_external_bytes_used_by_all_tracks(self):
        evidence = Path(tempfile.mkdtemp(prefix='external-runtime-qa-', dir=ROOT))
        package = evidence / 'package'
        shutil.copytree(ROOT / 'technical-packages-v3-argument', package)
        reg = package / 'registry.json'
        data = json.loads(reg.read_text())
        marker = b'EXTREG0000000001'
        marker = marker.ljust(16, b' ')
        tr = package / 'reporting/TRANFILE'
        tr.write_bytes(marker + tr.read_bytes()[16:])
        for fx in data['fixtures']:
            for dd, rel in fx['materializer']['files'].items():
                src = package / rel
                fx['materializer']['filePins'][dd] = {'sha256': b.sha256(src), 'bytes': src.stat().st_size}
            fx['contentSha256'] = b.fixture_descriptor_sha256(fx)
        reg.write_text(json.dumps(data, indent=2) + '\n')
        prior = os.environ.get(b.FIXTURE_ENV)
        dd_prior = {key: os.environ.get(key) for key in ('DD_TRANFILE', 'DD_TRANSACT')}
        for key in dd_prior:
            os.environ[key] = str(evidence / ('outside-' + key))
        os.environ[b.FIXTURE_ENV] = str(reg)
        records = []
        try:
            for track in ('posting', 'interest', 'reporting'):
                with self.subTest(track=track):
                    status, body, audit = getattr(b, track)('explicit-technical-fixture-qa')
                    records.append({'track': track, 'status': status, 'body': body, 'auditPath': str(Path(audit['INV']['workdir']) / 'audit.json')})
                    (evidence / 'results.json').write_text(json.dumps(records, indent=2) + '\n')
                    self.assertEqual(status, 200)
                    snap = audit['STATE'].get('pre_cobol_materialization')
                    self.assertIsNotNone(snap, 'Missing after-setup/before-COBOL snapshot')
                    self.assertEqual({f['path'] for f in snap['files']}, b.RESOURCE_NAMES[track],
                                     'Configured packages must not fall back to builtin setup or stale outputs')
                    materialized = audit['CAP']['fixture_materialization']['files']
                    self.assertEqual(set(materialized), b.RESOURCE_NAMES[track])
                    for item in materialized.values():
                        self.assertEqual(item['sourceSha256'], item['materializedSha256'])
                    if track == 'reporting':
                        self.assertIn(marker, (Path(audit['INV']['workdir']) / 'TRANREPT').read_bytes(),
                                      'Actual report must reflect external transaction identifier, not builtin input')
        finally:
            for key, value in dd_prior.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            if prior is None:
                os.environ.pop(b.FIXTURE_ENV, None)
            else:
                os.environ[b.FIXTURE_ENV] = prior
            print('QA evidence:', evidence)


if __name__ == '__main__':
    unittest.main(verbosity=2)

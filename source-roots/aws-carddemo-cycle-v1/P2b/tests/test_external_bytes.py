import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('binding_fixture_test', ROOT / 'p2b_binding.py')
assert spec is not None and spec.loader is not None
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def fixture_for(base, files):
    for name, data in files.items():
        (base / name).write_bytes(data)
    fx = {'fixtureId': 'technical-test', 'track': 'posting',
          'materializer': {'kind': 'local_file_package', 'files': {n: n for n in files},
                          'filePins': {n: {'sha256': hashlib.sha256(v).hexdigest(), 'bytes': len(v)} for n, v in files.items()}},
          'provenance': {'class': 'local_synthetic_support'},
          'exposure': {'label': 'technical-only', 'notOracle': True},
          'reset': {'default': 'fresh_dir_per_run'}}
    fx['contentSha256'] = b.fixture_descriptor_sha256(fx)
    reg = base / 'registry.json'
    reg.write_text(json.dumps({'kind': 'p3-local-technical-fixture-selection', 'fixtures': [fx]}))
    return fx, reg


class ExternalBytesTests(unittest.TestCase):
    def test_reset_proof_cannot_ignore_a_missing_resource(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            _, reg = fixture_for(base, {dd: b'initial' for dd in b.RESOURCE_NAMES['posting']})
            fx = b.select_external_fixture('posting', reg)
            first = base / 'first'; first.mkdir()
            second = base / 'second'; second.mkdir()
            a = b.materialize_fixture(fx, first)
            z = b.materialize_fixture(fx, second)
            del z['files']['ACCTFILE']
            self.assertFalse(b.prove_fresh_materialization_reset(a, z)['resetVerified'])

    def test_incomplete_package_rejected_without_builtin_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            _, reg = fixture_for(base, {'DALYTRAN': b'input'})
            with self.assertRaises(b.FixtureConfigError):
                b.select_external_fixture('posting', reg)

    def test_resource_destination_cannot_escape_workdir(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            fx, reg = fixture_for(base, {'DALYTRAN': b'input'})
            fx['materializer']['files'] = {'../escaped': 'DALYTRAN'}
            fx['contentSha256'] = b.fixture_descriptor_sha256(fx)
            reg.write_text(json.dumps({'kind': 'p3-local-technical-fixture-selection', 'fixtures': [fx]}))
            with self.assertRaises(b.FixtureConfigError):
                b.select_external_fixture('posting', reg)

    def test_changed_bytes_rejected_even_with_unchanged_descriptor(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            _, reg = fixture_for(base, {dd: b'original' for dd in b.RESOURCE_NAMES['posting']})
            selected = b.select_external_fixture('posting', reg)
            (base / 'DALYTRAN').write_bytes(b'adulterated')
            wd = base / 'work'; wd.mkdir()
            with self.assertRaises(b.FixtureConfigError):
                b.materialize_fixture(selected, wd)
            self.assertEqual(list(wd.iterdir()), [])


if __name__ == '__main__':
    unittest.main()

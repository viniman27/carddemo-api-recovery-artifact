"""The response QA must fail closed without the real schema engine."""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class SchemaDependencyTests(unittest.TestCase):
    def test_missing_jsonschema_cannot_produce_subset_pass(self):
        # Simulate only the absent optional package in a clean interpreter;
        # the actual validator module and dependency import path are exercised.
        code = '''
import importlib.abc, runpy, sys
class MissingSchema(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "jsonschema" or fullname.startswith("jsonschema."):
            raise ModuleNotFoundError("jsonschema unavailable in dependency-negative QA")
sys.meta_path.insert(0, MissingSchema())
runpy.run_path(sys.argv[1], run_name="dependency_probe")
'''
        result = subprocess.run(
            [sys.executable, '-c', code, str(ROOT / 'validate_p2b.py')],
            capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0,
                            'Missing jsonschema must not enable a substitute validator')
        self.assertIn('jsonschema', result.stderr)


if __name__ == '__main__':
    unittest.main()

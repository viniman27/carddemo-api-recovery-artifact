import subprocess
import sys
import unittest

class IntegrityGuardTests(unittest.TestCase):
    def test_failure_is_not_disabled_by_optimized_python(self):
        p = subprocess.run([sys.executable, '-O', '-c',
            "import prepare; prepare.require(False, 'INTEGRITY_SENTINEL')"],
            capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('RuntimeError: INTEGRITY_SENTINEL', p.stderr)

import tempfile
from pathlib import Path

class ScopeGuardTests(unittest.TestCase):
    def test_loader_rejects_external_path(self):
        import prepare
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, 'outside run directory'):
                prepare.check_load_target(Path(tmp), Path(tmp).parent/'outside')

    def test_loader_refuses_existing_file(self):
        import prepare
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'index'
            target.write_bytes(b'preserve')
            with self.assertRaisesRegex(RuntimeError, 'already exists'):
                prepare.check_load_target(Path(tmp), target)
            self.assertEqual(target.read_bytes(), b'preserve')

if __name__ == '__main__': unittest.main()

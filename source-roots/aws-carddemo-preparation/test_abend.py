import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent

class AbendTests(unittest.TestCase):
    def test_missing_input_terminates_with_explicit_local_abend(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = subprocess.run([str(ROOT/'build/CBTRN02C')], cwd=tmp,
                env=dict(os.environ, DD_DALYTRAN=str(Path(tmp)/'missing'),
                         COB_LIBRARY_PATH=str(ROOT/'build')),
                capture_output=True, text=True, timeout=10)
            self.assertEqual(p.returncode, 12, p.stdout+p.stderr)
            self.assertRegex(p.stderr, r'LOCAL-CEE3ABD CODE=\+0*999 TIMING=\+0+\s')
            self.assertNotIn('END OF EXECUTION', p.stdout)

if __name__ == '__main__':
    unittest.main()

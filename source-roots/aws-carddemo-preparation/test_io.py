import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent

class IndexedIOTests(unittest.TestCase):
    def test_raw_record_roundtrip(self):
        exe = ROOT / 'build/io_XREFFILE'
        self.assertTrue(exe.is_file(), 'Missing external indexed-file loader/dumper')
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            original = b'0000000000000001' + b'A' * 34
            (p / 'raw').write_bytes(original)
            env = dict(os.environ, DD_RAW=str(p/'raw'), DD_IDX=str(p/'index'))
            for mode in ['LOAD', 'DUMP']:
                r = subprocess.run([str(exe)], env=dict(env, IO_MODE=mode), capture_output=True)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                if mode == 'LOAD':
                    (p / 'raw').unlink()
            self.assertEqual((p/'raw').read_bytes(), original)

if __name__ == '__main__':
    unittest.main()

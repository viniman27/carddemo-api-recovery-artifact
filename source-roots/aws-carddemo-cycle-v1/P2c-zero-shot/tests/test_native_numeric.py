import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import p2c_facade as facade
class NativeNumericTests(unittest.TestCase):
    def test_negative_transport_matches_measured_runtime_bytes(self):
        expected=(Path(__file__).resolve().parents[2]/'P3/native-display-probe-v1/native.bin').read_bytes()
        self.assertEqual(facade._amount('-1.23'),expected)

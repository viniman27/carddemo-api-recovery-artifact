import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import p2c_facade as facade
class NativeNumericTests(unittest.TestCase):
    def test_negative_runtime_amount_is_decoded_not_returned_as_raw_string(self):
        native=(Path(__file__).resolve().parents[2]/'P3/native-display-probe-v1/native.bin').read_text()
        self.assertEqual(facade._signed_display_to_decimal(native),-1.23)
    def test_numeric_identifiers_are_zero_filled_not_space_padded(self):
        tx=facade.sample_request('E2-2','posting')['transactions'][0]
        raw=facade.transaction_record(tx,'E2-2')
        self.assertEqual(raw[18:22],b'0001')
        self.assertEqual(raw[143:152],b'000000001')
    def test_negative_transport_matches_measured_runtime_bytes(self):
        expected=(Path(__file__).resolve().parents[2]/'P3/native-display-probe-v1/native.bin').read_bytes()
        self.assertEqual(facade._amount_to_display('-1.23'),expected)

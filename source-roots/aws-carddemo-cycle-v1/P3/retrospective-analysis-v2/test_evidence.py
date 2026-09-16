import unittest
import importlib.util
from pathlib import Path

class EvidenceTest(unittest.TestCase):
    def test_exact_records_preserve_missing_empty_order_and_multiplicity(self):
        p=Path(__file__).with_name('evidence.py')
        self.assertTrue(p.exists(), 'evidence comparator not implemented')
        s=importlib.util.spec_from_file_location('evidence',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
        for observed, expected, verdict in [(b'',b'','pass'),(None,b'','inconclusive'),(b'123',b'123','pass'),(b'124',b'123','failed'),(b'123123',b'123','failed'),(b'456123',b'123456','failed'),(b'123x',b'123','failed')]:
            self.assertEqual(m.compare_records(observed,expected,3)['verdict'],verdict)

if __name__=='__main__': unittest.main()

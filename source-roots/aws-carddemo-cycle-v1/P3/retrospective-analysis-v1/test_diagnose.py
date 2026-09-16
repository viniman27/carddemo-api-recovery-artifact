import unittest,importlib.util
from pathlib import Path
class DiagnosisTest(unittest.TestCase):
    def test_six_saved_rejections_match_pid_and_exact_decimal_countercheck(self):
        p=Path(__file__).with_name('diagnose.py'); self.assertTrue(p.exists(),'diagnosis absent')
        s=importlib.util.spec_from_file_location('diagnose',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
        rows=m.diagnose()
        self.assertEqual(len(rows),6)
        self.assertTrue(all(r['pidLinked'] and r['floatErrors'] and not r['decimalErrors'] and r['rawResponse']=='{}' for r in rows))
if __name__=='__main__': unittest.main()

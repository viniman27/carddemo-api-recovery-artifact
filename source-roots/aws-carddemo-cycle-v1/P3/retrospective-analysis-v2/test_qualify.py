import unittest,importlib.util
from pathlib import Path
class QualificationTest(unittest.TestCase):
    def test_known_wrong_values_and_blind_spots_are_reported(self):
        p=Path(__file__).with_name('qualify.py'); self.assertTrue(p.exists(),'qualification absent')
        s=importlib.util.spec_from_file_location('qualify',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
        rows=m.qualify()
        self.assertLessEqual(len(rows),60)
        self.assertTrue(any(r['errorClass']=='same_length_wrong_amount' for r in rows))
        self.assertTrue(any(r['errorClass']=='omission' for r in rows))
        self.assertTrue(any(r['errorClass']=='duplication' for r in rows))
        self.assertTrue(any(r['errorClass']=='reordering' for r in rows))
        self.assertTrue(any(r['errorClass']=='balance_not_updated' for r in rows))
        self.assertTrue(any(r['errorClass']=='wrong_grand_total' for r in rows))
        self.assertTrue(all(r['baselineVerdict']=='pass' for r in rows))
        self.assertTrue(all(r['verdict']=='failed' for r in rows if r['targetedFault']))
        self.assertTrue(any(r['verdict']=='inconclusive' for r in rows))
        self.assertTrue(any(r['verdict']=='pass' and not r['targetedFault'] for r in rows))
if __name__=='__main__': unittest.main()

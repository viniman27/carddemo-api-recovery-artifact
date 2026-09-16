import unittest, importlib.util
from pathlib import Path
class SummaryTest(unittest.TestCase):
    def test_contribution_excludes_T4_and_unknown_and_counts_real_overlap(self):
        p=Path(__file__).with_name('analysis.py'); self.assertTrue(p.exists(),'summary not implemented')
        s=importlib.util.spec_from_file_location('analysis',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
        rows=[{'lane':'official','contract':'C','track':'posting','strategy':s,'semanticInputKey':k,'businessObserved':True} for s,k in [('T1','a'),('T1','a'),('T2','a'),('T2','b'),('T3','c'),('T4','d'),('T3',None)]]
        r=m.contributions(rows)[0]
        self.assertEqual(r['unionT123'],3); self.assertEqual(r['exclusiveT1'],0); self.assertEqual(r['exclusiveT2'],1); self.assertEqual(r['incrementalT3_afterT12'],1); self.assertEqual(r['overlapT1T2'],1); self.assertEqual(r['T4_not_in_union'],1)
    def test_condition_from_enclosing_frozen_suite_not_case_name(self):
        import analysis as m
        self.assertTrue(hasattr(m,'condition'),'condition resolver absent')
        self.assertEqual(m.condition('E1-1-T3','E1-1'),'T3')
        self.assertEqual(m.condition('E1-1-T4','E1-1'),'T4')
        with self.assertRaises(ValueError): m.condition('E2-1-T3','E1-1')
        with self.assertRaises(ValueError): m.condition('looks-like-T3','E1-1')
    def test_missing_strategies_stay_in_obligation_denominator(self):
        import analysis as m
        cat={'obligations':[], 'obligationOperationMapping':[{'applicability':'candidate_applicable_obligation_contract','contractId':'C','arm':'SDD','obligationTrack':'posting','obligationId':'O'}]}
        _,obls,_=m.summarize([],cat)
        self.assertEqual(len(obls),5)
        self.assertTrue(all(o['claim']=='not_executed' for o in obls))
if __name__=='__main__': unittest.main()

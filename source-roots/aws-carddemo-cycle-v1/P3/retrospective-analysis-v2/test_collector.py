import unittest, tempfile, json, importlib.util
from pathlib import Path

class CollectorTest(unittest.TestCase):
    def test_snapshot_recovery_requires_historical_hash_and_distinguishes_mutation(self):
        path=Path(__file__).with_name('collector.py')
        self.assertTrue(path.exists(),'collector absent')
        spec=importlib.util.spec_from_file_location('collector',path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); rd=root/'run'; rd.mkdir(); src=root/'source'; src.write_bytes(b'before'); (rd/'ACCTFILE').write_bytes(b'after')
            store=mod.Store(root/'out')
            old={'path':'ACCTFILE','bytes':6,'sha256':mod.digest(b'before')}
            audit={'STATE':{'pre_cobol_materialization':{'files':[old]}},'CAP':{'fixture_materialization':{'files':{'ACCTFILE':{'sourcePath':str(src)}}}}}
            self.assertEqual(store.before(rd,audit,'ACCTFILE'),src)
            src.write_bytes(b'wrong!')
            with self.assertRaises(ValueError): store.before(rd,audit,'ACCTFILE')
            self.assertEqual(mod.request_key({'body_kind':'absent'}),mod.request_key({'body_kind':'absent'}))
            self.assertNotEqual(mod.request_key({'body_kind':'absent'}),mod.request_key({'body_kind':'json','body_b64':'e30='}))

    def test_semantic_key_excludes_filler_not_business_values(self):
        import collector as m
        self.assertTrue(hasattr(m,'semantic_inputs'))
        a={'ACCTFILE':[b'1'*122+b' '*178]}; b={'ACCTFILE':[b'1'*122+b'\x00'*178]}
        self.assertEqual(m.semantic_inputs(a),m.semantic_inputs(b))
        b={'ACCTFILE':[b'2'*122+b' '*178]}
        self.assertNotEqual(m.semantic_inputs(a),m.semantic_inputs(b))

    def test_absent_body_null_base64_is_not_json_empty(self):
        import collector as m
        self.assertEqual(m.request_key({'body_kind':'absent','body_b64':None}),m.request_key({'body_kind':'absent'}))
        self.assertNotEqual(m.request_key({'body_kind':'absent','body_b64':None}),m.request_key({'body_kind':'json','body_b64':'e30='}))

    def test_preserved_vertical_slice_has_linked_observations_not_http_only(self):
        path=Path(__file__).with_name('collector.py'); self.assertTrue(path.exists(),'collector absent')
        spec=importlib.util.spec_from_file_location('collector',path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        cycle=path.parents[2]
        report=json.loads((cycle/'P3/complementary-matrix-v2/parent-full84-v1/campaign/campaign-report.json').read_text())
        freeze=json.loads((cycle/'P3/complementary-matrix-v2/parent-plan-absolute-v1/suite.freeze.json').read_text()); frozen={x['case_id']:x for x in freeze['cases']}
        with tempfile.TemporaryDirectory() as td:
            store=mod.Store(Path(td),cycle)
            for track in ['posting','interest','reporting']:
              for cid in ['E1-1','E2-1','E3-SDD-stage6r3']:
                ch=next(x for x in report['suiteReports'][0]['checks'] if x['track']==track and x['contractId']==cid)
                row=mod.analyze(ch,frozen[ch['case_id']],'complementary','source-guided',store)
                self.assertTrue(row['businessObserved']); self.assertTrue(row['semanticInputKey']); self.assertTrue(row['checks'],row)
                self.assertFalse(row['provenanceErrors'],row)
                self.assertNotIn('collector_error',row['limit'],row)
            self.assertEqual(store.verify(),[])

    def test_saved_abnormal_case_gets_narrow_precondition_check(self):
        import collector as mod
        cycle=Path(__file__).resolve().parents[2]
        report=json.loads((cycle/'P3/official-campaign-large12k-run-v2/campaign-report.json').read_text())
        suite=next(s for s in report['suiteReports'] if s['suite_id']=='E2-1-T1')
        ch=next(c for c in suite['checks'] if c['case_id']=='T1-REAL-E2-1-E2-1-T1-REPORT-001')
        frozen={c['case_id']:c for c in json.loads(Path(suite['path']).read_text())['cases']}
        with tempfile.TemporaryDirectory() as td:
            row=mod.analyze(ch,frozen[ch['case_id']],'official','T1',mod.Store(Path(td),cycle))
            self.assertTrue(row['checks'],row)
            self.assertEqual(row['checks'][0]['name'],'missing_first_xref_abort')
            self.assertEqual(row['checks'][0]['verdict'],'pass')
            self.assertTrue(any('not general I/O' in x for x in row['limit']))

if __name__=='__main__': unittest.main()

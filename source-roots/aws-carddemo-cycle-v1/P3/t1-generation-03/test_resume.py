import unittest, importlib.util, tempfile
from pathlib import Path
class ResumeTests(unittest.TestCase):
 def test_only_four_calls_no_probe_and_no_repeated_e1(self):
  p=Path(__file__).with_name('resume_t1.py')
  self.assertTrue(p.exists(), 'versioned resume runner missing')
  spec=importlib.util.spec_from_file_location('resume',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
  calls=[]
  with tempfile.TemporaryDirectory() as td:
   def send(cid):
    calls.append(cid); return {'contractId':cid,'classification':'complete'}
   m.execute_remaining(send,Path(td))
  self.assertEqual(calls,['E2-1','E2-2','E2-3','E3-SDD-stage6r3'])
 def test_transport_failure_stops_without_retry(self):
  p=Path(__file__).with_name('resume_t1.py')
  self.assertTrue(p.exists(), 'versioned resume runner missing')
  spec=importlib.util.spec_from_file_location('resume',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
  calls=[]
  with tempfile.TemporaryDirectory() as td:
   def send(cid):
    calls.append(cid); return {'contractId':cid,'classification':'interrupted'}
   report=m.execute_remaining(send,Path(td))
  self.assertEqual(calls,['E2-1']); self.assertEqual(report['status'],'stopped')

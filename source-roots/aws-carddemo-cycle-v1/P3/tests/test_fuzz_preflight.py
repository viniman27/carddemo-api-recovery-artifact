"""Synthetic tool qualification only. Never loads an AWS contract."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class FuzzerPreflightTests(unittest.TestCase):
    def test_frozen_synthetic_requests_are_sent_exactly_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'evidence'
            run=subprocess.run([str(ROOT/'.venv-fuzz-preflight/bin/python'),str(ROOT/'fuzz_preflight.py'),'--output',str(target)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            report=json.loads((target/'report.json').read_text())
            self.assertTrue(report['passed'])
            self.assertEqual(report['httpCalls'],report['frozenCases'])
            self.assertEqual(report['unexpectedHttpCalls'],0)
            self.assertTrue(report['documented500Accepted'])
            self.assertTrue(report['malformedResponseDetected'])
            self.assertFalse(report['awsLoaded'])
            self.assertTrue(all(row['generated']<=12 for row in report['generation']))
            self.assertEqual(report['positiveBodyVariants'],['{}'])

if __name__=='__main__': unittest.main()

#!/usr/bin/env python3
"""Known local technical abort regression; not business/campaign verdicts."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'P2b'))
import p2b_binding as b

class FailureRuntimeQA(unittest.TestCase):
    def test_local_abort_keeps_500_precedence_and_audit_all_tracks(self):
        out=Path(tempfile.mkdtemp(prefix='failure-boundary-qa-',dir=ROOT))
        package=out/'package'; shutil.copytree(ROOT/'technical-packages-v3-argument',package)
        reg=package/'registry.json'; data=json.loads(reg.read_text())
        for fx in data['fixtures']:
            dd='CARDXREF' if fx['track']=='reporting' else 'XREFFILE'
            path=package/fx['materializer']['files'][dd]
            path.write_bytes(b'INVALID NATIVE INDEX FOR TECHNICAL QA')
            fx['materializer']['filePins'][dd]={'sha256':b.sha256(path),'bytes':path.stat().st_size}
            fx['contentSha256']=b.fixture_descriptor_sha256(fx)
        reg.write_text(json.dumps(data,indent=2)+'\n')
        old=os.environ.get(b.FIXTURE_ENV); os.environ[b.FIXTURE_ENV]=str(reg)
        rows=[]
        try:
            for track in ('posting','interest','reporting'):
                with self.subTest(track=track):
                    status,body,audit=getattr(b,track)('local-abort-qa')
                    rows.append({'track':track,'status':status,'body':body,'audit':str(Path(audit['INV']['workdir'])/'audit.json')})
                    (out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
                    self.assertEqual(status,500)
                    self.assertEqual(body['category'],'technical_failure')
                    self.assertTrue(audit['FAIL']['events'])
        finally:
            if old is None: os.environ.pop(b.FIXTURE_ENV,None)
            else: os.environ[b.FIXTURE_ENV]=old
            print('Evidence:',out)

if __name__=='__main__': unittest.main(verbosity=2)

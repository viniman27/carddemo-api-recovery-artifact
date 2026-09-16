#!/usr/bin/env python3
"""Bounded actual posting regression, not an experimental campaign."""
import importlib.util
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

class PostingRuntimeQA(unittest.TestCase):
    def test_write_order_reject_context_and_actual_counters(self):
        out=Path(tempfile.mkdtemp(prefix='posting-observation-qa-',dir=ROOT))
        package=out/'package'; shutil.copytree(ROOT/'technical-packages-v2-complete',package)
        raw=package/'posting/DALYTRAN'
        rows=[b.transaction().replace(b'TEST000000000001',ident) for ident in (b'ZZZZ000000000001',b'AAAA000000000001')]
        rows.append(b.transaction(card=b'9999999999999999').replace(b'TEST000000000001',b'REJT000000000001'))
        rows.append(rows[-1])  # actual sequential rejection multiplicity
        raw.write_bytes(b''.join(rows))
        reg=package/'registry.json'; data=json.loads(reg.read_text())
        fx=next(f for f in data['fixtures'] if f['track']=='posting')
        fx['materializer']['filePins']['DALYTRAN']={'sha256':b.sha256(raw),'bytes':raw.stat().st_size}
        fx['contentSha256']=b.fixture_descriptor_sha256(fx); reg.write_text(json.dumps(data,indent=2)+'\n')
        prior=os.environ.get(b.FIXTURE_ENV); os.environ[b.FIXTURE_ENV]=str(reg)
        try:
            status,body,audit=b.posting('posting-order-qa')
            (out/'result.json').write_text(json.dumps({'status':status,'body':body,'auditPath':str(Path(audit['INV']['workdir'])/'audit.json')},indent=2)+'\n')
            self.assertEqual(status,200)
            self.assertEqual([i['transactionId'] for i in body['outputs']['items']],['ZZZZ000000000001','AAAA000000000001'])
            self.assertEqual(body['progress']['value']['processedRecordCount'],4)
            self.assertEqual(body['progress']['value']['preliminaryRejectCount'],2)
            self.assertEqual(len(body['rejections']['items']),2)
            self.assertEqual(body['rejections']['items'][0],body['rejections']['items'][1])
            self.assertEqual(body['rejections']['items'][0]['candidate']['transactionId'],'REJT000000000001')
        finally:
            if prior is None: os.environ.pop(b.FIXTURE_ENV,None)
            else: os.environ[b.FIXTURE_ENV]=prior
            print('Evidence:',out)

if __name__=='__main__': unittest.main(verbosity=2)

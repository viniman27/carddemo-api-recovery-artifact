#!/usr/bin/env python3
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_t1_generation as r


def sse_completed(model='gpt-6-astra', text='T1_PROBE_OK'):
    events = [
        {'type': 'response.output_text.done', 'output_index': 0, 'content_index': 0, 'text': text},
        {'type': 'response.completed', 'response': {'id': 'resp_test', 'status': 'completed', 'model': model, 'tools': [], 'previous_response_id': None, 'store': False, 'usage': {'input_tokens': 1, 'output_tokens': 1}}},
    ]
    return ''.join('data: '+json.dumps(e, separators=(',', ':'))+'\n\n' for e in events) + 'data: [DONE]\n\n'


class ChunkedResponse:
    status = 200
    def __init__(self, chunks):
        self.chunks = list(chunks)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, n=-1):
        if not self.chunks:
            return b''
        return self.chunks.pop(0)


class RecordingOpener:
    def __init__(self, response):
        self.response = response
        self.requests = []
    def open(self, req, timeout=None):
        self.requests.append((req, timeout))
        return self.response


class TransportFixTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.old_out = r.OUT
        r.OUT = self.tmp
    def tearDown(self):
        r.OUT = self.old_out
        shutil.rmtree(self.tmp)

    def test_probe_and_effective_payload_omit_previous_response_id_only(self):
        probe = r.build_probe_payload()
        self.assertNotIn('previous_response_id', probe)
        self.assertEqual(probe['model'], r.MODEL)
        self.assertFalse(probe['store'])
        self.assertTrue(probe['stream'])
        self.assertEqual(probe['tools'], [])
        body = r.build_effective_payload('E1-1')
        self.assertNotIn('previous_response_id', body)
        self.assertEqual(set(body), {'model', 'store', 'stream', 'tools', 'input'})
        text = body['input'][0]['content'][0]['text']
        self.assertIn('[CONTRACT]', text)
        self.assertIn('[AUTHORIZED_PACKAGE_METADATA]', text)
        self.assertNotIn('/Users/', text)
        self.assertNotIn('previous_response_id', json.dumps(body, ensure_ascii=False))

    def test_call_provider_streams_incrementally_and_disables_redirects(self):
        raw = sse_completed(text='T1_PROBE_OK')
        chunks = [raw[:40].encode(), raw[40:90].encode(), raw[90:].encode()]
        opener = RecordingOpener(ChunkedResponse(chunks))
        row = r.call_provider({'api_key': 'secret'}, 'probe', r.build_probe_payload(), opener=opener, timeout_s=5)
        self.assertEqual(row['classification'], 'complete')
        self.assertTrue(row['redirectsDisabled'])
        self.assertEqual(row['followRedirects'], False)
        req, timeout = opener.requests[0]
        self.assertNotIn(b'previous_response_id', req.data)
        raw_path = self.tmp / row['rawSsePath']
        self.assertEqual(raw_path.read_text(), raw)
        receipt = json.loads((self.tmp / 'receipts/probe.receipt.json').read_text())
        self.assertEqual(receipt['rawSseSha256'], row['rawSseSha256'])

    def test_redirect_is_classified_as_transport_not_followed(self):
        class RedirectOpener:
            def open(self, req, timeout=None):
                raise r.RedirectBlockedError('redirect blocked: 307 https://example.invalid')
        row = r.call_provider({'api_key': 'secret'}, 'redirect', r.build_probe_payload(), opener=RedirectOpener(), timeout_s=5)
        self.assertEqual(row['classification'], 'interrupted_redirect_blocked')
        self.assertIn('redirect blocked', row['transportError'])


if __name__ == '__main__':
    unittest.main()

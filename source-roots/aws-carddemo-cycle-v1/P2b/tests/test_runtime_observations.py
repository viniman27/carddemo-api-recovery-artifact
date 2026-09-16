import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class RuntimeObservationTests(unittest.TestCase):
    def test_posting_order_duplicates_progress_and_rejections_are_observed(self):
        from runtime_observations import posting_observations
        import p2b_binding as b
        z = b.transaction().replace(b'TEST000000000001', b'ZZZZ000000000001')
        a = b.transaction().replace(b'TEST000000000001', b'AAAA000000000001')
        reject = a + b'0100' + b'External capture'.ljust(76)
        log = 'BEGIN|i1\n' + ''.join(f'WRITE|{i}|{name}|00|{data.hex()}\n' for i, (name, data) in enumerate([
            ('TRANSACT-FILE', z), ('TRANSACT-FILE', a), ('TRANSACT-FILE', a), ('DALYREJS-FILE', reject)], 1)) + 'END|i1|4\n'
        body, ev = posting_observations(log, 'i1', 'TRANSACTIONS PROCESSED :000000007\nTRANSACTIONS REJECTED  :000000001\n')
        self.assertFalse(ev['knownFailure'])
        self.assertEqual([x['transactionId'] for x in body['outputs']['items']], ['ZZZZ000000000001','AAAA000000000001','AAAA000000000001'])
        self.assertEqual(body['progress']['value']['processedRecordCount'], 7)
        self.assertEqual(body['rejections']['items'][0]['reason'], '100')
        self.assertEqual(body['rejections']['items'][0]['description'], 'External capture'.ljust(76))
        self.assertIn('suppliedProcessingTimestamp', body['rejections']['items'][0]['candidate'])

    def test_parameter_wrapper_failure_is_not_unavailable_content(self):
        from runtime_observations import apply_failure_boundary
        status, body, events = apply_failure_boundary('interest',503,{'track':'interest','category':'content_unavailable'}, {'exit_code':12,'stderr':'P2B-PARAMETER-FAIL: read\n'})
        self.assertEqual(status,500)
        self.assertTrue(events)

    def test_absent_capture_is_not_empty_or_invented_progress(self):
        from runtime_observations import posting_observations
        body, ev = posting_observations(None, 'i1', '')
        self.assertEqual(body['outputs'], {'availability': 'unavailable'})
        self.assertEqual(body['progress'], {'availability': 'unavailable'})
        self.assertFalse(ev['knownFailure'])

    def test_known_local_abort_precedes_missing_capture_but_exit_alone_does_not(self):
        from runtime_observations import apply_failure_boundary
        absent={'track':'interest','category':'content_unavailable','completeness':'not_attested','durability':'unknown'}
        status, _, ev = apply_failure_boundary('interest', 503, absent, {'exit_code':12,'stdout':'','stderr':'LOCAL-CEE3ABD/2 CODE=+0000000999 TIMING=+0000000000\n'})
        self.assertEqual(status, 500)
        self.assertTrue(ev)
        status, _, ev = apply_failure_boundary('interest', 503, absent, {'exit_code':12,'stdout':'','stderr':''})
        self.assertEqual(status, 503)
        self.assertFalse(ev)


if __name__ == '__main__': unittest.main()

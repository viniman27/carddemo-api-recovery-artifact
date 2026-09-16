import unittest
import evidence as e
from test_models import acct,tx
class GapTests(unittest.TestCase):
    def test_ascii_overpunch_roundtrip_and_negative_posting(self):
        for digit in range(10):
            raw=b'0000000012'+bytes([ord('p')+digit])
            self.assertEqual(e.number(raw),-(120+digit))
            self.assertEqual(e.put_number(b'0'*11,0,11,-(120+digit)),raw)
        with self.assertRaises(ValueError): e.number(b'0000000000?')
        with self.assertRaises(ValueError): e.put_number(b'0'*11,0,11,-100000000000)
        a=acct(credit=0,debit=0); x=b'4111111111111111'+b'000000001'+a[:11]+b' '*14
        t=e.put_number(tx(),132,143,-123)
        r=e.posting_expected([t],[a],[],[x])
        self.assertEqual(r['reasons'],[0]); self.assertEqual(e.number(r['accounts'][0][12:24]),9877)
        self.assertEqual(e.number(r['accounts'][0][78:90]),0); self.assertEqual(e.number(r['accounts'][0][90:102]),-123)
        self.assertEqual(e.number(r['categories'][0][17:28]),-123)
    def test_empty_dateparm_is_eof_not_missing_or_partial(self):
        result=e.report_expected([tx()],b'',[],[],[])
        self.assertEqual(result['legacy'],[]); self.assertEqual(result['selectedCount'],0)
        for raw in [None,b'2022',b'2022-07-01 2022-07-31']:
            with self.assertRaises(ValueError): e.report_expected([tx()],raw,[],[],[])
    def test_first_missing_xref_can_be_qualified_but_not_later_failure(self):
        self.assertTrue(hasattr(e,'first_missing_xref'))
        d=b'2022-07-01 2022-07-31'.ljust(80)
        self.assertEqual(e.first_missing_xref([tx()],d,[]),'4111111111111111')
        self.assertIsNone(e.first_missing_xref([tx()],b'',[]))
        x=b'4111111111111111'+b'000000001'+b'10000000001'+b' '*14
        self.assertIsNone(e.first_missing_xref([tx(),tx(card=b'4999999999999999')],d,[x]))
if __name__=='__main__': unittest.main()

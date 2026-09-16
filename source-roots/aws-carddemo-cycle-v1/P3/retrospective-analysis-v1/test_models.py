import unittest
from decimal import Decimal
import evidence as e

def acct(key=b'10000000001',balance=10000,credit=500,debit=200,limit=100000):
    b=bytearray(b' '*300); b[:11]=key; b[11:12]=b'Y'
    for a,z,v in [(12,24,balance),(24,36,limit),(36,48,0),(78,90,credit),(90,102,debit)]: b[a:z]=f'{v:0{z-a}d}'.encode()
    b[58:68]=b'2025-12-31'; b[112:122]=b'STANDARD  '; return bytes(b)

def tx(key=b'TEST000000000001',amount=100,card=b'4111111111111111',date=b'2022-07-01'):
    b=bytearray(b' '*350); b[:16]=key; b[16:22]=b'010005'; b[22:32]=b'System    '; b[132:143]=f'{amount:011d}'.encode(); b[262:278]=card; b[278:288]=date; b[304:314]=date; return bytes(b)

class InterestTest(unittest.TestCase):
    def test_account_break_and_final_account_are_separate_expectations(self):
        self.assertTrue(hasattr(e,'interest_expected'),'interest model absent')
        a1=acct(); a2=acct(b'10000000002'); a3=acct(b'10000000003')
        cats=[a[:11]+b'010005'+b'00000100000'+b' '*22 for a in (a1,a2,a3)]
        xrefs=[card+b'000000001'+a[:11]+b' '*14 for card,a in [(b'4111111111111111',a1),(b'4222222222222222',a2),(b'4333333333333333',a3)]]
        rates=[b'STANDARD  010005001200'+b' '*28]
        result=e.interest_expected([a1,a2,a3],cats,rates,xrefs,b'2022-07-31')
        self.assertEqual([r[132:143] for r in result['transactions']], [b'00000001000']*3)
        self.assertEqual(result['legacyAccounts'][0][12:24],b'000000011000')
        self.assertEqual(result['legacyAccounts'][0][78:102],b'0'*24)
        self.assertEqual(result['legacyAccounts'][-1],a3)
        self.assertEqual(result['financialAccounts'][-1][12:24],b'000000011000')
        self.assertEqual(e.interest_cents(101,1200),1)
        self.assertEqual(e.interest_cents(99,1200),0)
        with self.assertRaises(ValueError): e.interest_expected([a1],cats[:1],[],xrefs[:1],b'2022-07-31')

class PostingTest(unittest.TestCase):
    def test_exact_limit_expiry_rejection_and_state(self):
        self.assertTrue(hasattr(e,'posting_expected'),'posting model absent')
        a=acct(credit=0,debit=0,limit=100)
        x=b'4111111111111111'+b'000000001'+a[:11]+b' '*14
        r=e.posting_expected([tx(amount=100,date=b'2025-12-31')],[a],[],[x])
        self.assertEqual(r['reasons'],[0]); self.assertEqual(r['accounts'][0][12:24],b'000000010100')
        self.assertEqual(r['categories'][0][17:28],b'00000000100')
        for amount,date,reason in [(101,b'2025-12-31',102),(100,b'2026-01-01',103),(101,b'2026-01-01',103)]:
            r=e.posting_expected([tx(amount=amount,date=date)],[a],[],[x])
            self.assertEqual(r['reasons'],[reason]); self.assertEqual(r['accounts'],[a]); self.assertEqual(r['categories'],[])
        self.assertEqual(e.posting_expected([tx()],[a],[],[])['reasons'],[100])
        self.assertEqual(e.posting_expected([tx()],[],[],[x])['reasons'],[101])

class ReportingTest(unittest.TestCase):
    def test_all_subtotals_and_grand_total_and_eof_filter(self):
        self.assertTrue(hasattr(e,'report_expected'),'report model absent')
        records=[tx(key=f'{i:016d}'.encode()) for i in range(20)]
        x=b'4111111111111111'+b'000000001'+b'10000000001'+b' '*14
        args=(records,b'2022-07-01 2022-07-31',[x],[b'01Purchase'.ljust(60)],[b'010005Category'.ljust(60)])
        r=e.report_expected(*args)
        self.assertEqual([v[1] for v in r['legacy'] if v[0]=='page_total'],[1600,500])
        self.assertEqual([v[1] for v in r['financial'] if v[0]=='page_total'],[1600,400])
        self.assertEqual(r['legacy'][-1],('grand_total',2100))
        self.assertEqual(r['financial'][-1],('grand_total',2000))
        bad=list(r['financial']); bad[-1]=('grand_total',2001)
        self.assertEqual(e.compare_events(bad,r['financial'])['verdict'],'failed')
        self.assertEqual(e.compare_events(None,[])['verdict'],'inconclusive')
        self.assertEqual(e.compare_events([],[])['verdict'],'pass')
        outside=tx(key=b'9999999999999999',date=b'2022-08-01')
        r=e.report_expected(records[:1]+[outside],*args[1:])
        self.assertFalse(any(v[0]=='grand_total' for v in r['legacy']))
        # Inclusive boundaries: one before, exact start/end, one after.
        rr=[tx(key=f'{i:016d}'.encode(),date=d) for i,d in enumerate([b'2022-06-30',b'2022-07-01',b'2022-07-31',b'2022-08-01'])]
        r=e.report_expected(rr,*args[1:]); self.assertEqual(len([v for v in r['legacy'] if v[0]=='detail']),2)

    def test_parser_preserves_every_total_and_checks_money_strictly(self):
        self.assertTrue(hasattr(e,'parse_report'),'parser absent')
        lines=[]
        for name,amount in [('Page Total','+1.00'),('Page Total','+2.00'),('Grand Total','+3.00')]:
            lines.append(name.encode().ljust(97,b'.')+amount.encode().rjust(15)+b' '*21)
        self.assertEqual(e.parse_report(b''.join(lines)),[('page_total',100),('page_total',200),('grand_total',300)])
        self.assertEqual(e.parse_report(b''),[])
        self.assertIsNone(e.parse_report(None))
        with self.assertRaises(ValueError): e.parse_report(b'x')
        with self.assertRaises(ValueError): e.parse_report(b'Page Total'.ljust(133))

class SourceUnassignedBytesTest(unittest.TestCase):
    def test_unassigned_description_tail_and_tcat_filler_not_financial(self):
        a=bytearray(tx()); b=bytearray(a); a[56:132]=b' '*76; b[56:132]=b'\x00'*76
        self.assertEqual(e.stable_interest_transactions(bytes(a)),e.stable_interest_transactions(bytes(b)))
        self.assertTrue(hasattr(e,'stable_categories'))
        self.assertEqual(e.stable_categories(b'1'*28+b' '*22),e.stable_categories(b'1'*28+b'\x00'*22))
        self.assertNotEqual(e.stable_categories(b'1'*28+b' '*22),e.stable_categories(b'2'*28+b' '*22))

if __name__=='__main__': unittest.main()

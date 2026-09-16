"""Synthetic oracle qualification, never program mutation or empirical API cases."""
import json,copy
from pathlib import Path
from collections import Counter
import evidence as e
from test_models import acct,tx

def qualify():
    out=[]
    def record(domain,kind,baseline,observed,checker,targeted=True):
        b=checker(baseline); result=checker(observed)
        out.append({'domain':domain,'errorClass':kind,'baselineVerdict':b['verdict'],'verdict':result['verdict'],'targetedFault':targeted,'detected':result['verdict']=='failed','failures':result['failures'],'scope':'synthetic_output_or_state_checker_qualification_not_program_mutation'})
    # Two different records make reordering observable, not a degenerate swap.
    for domain,size,baseline,span in [('posting',350,tx()+tx(key=b'TEST000000000002',amount=200),142),('interest',350,tx()+tx(key=b'TEST000000000002',amount=200),142),('accounts',300,acct()+acct(b'10000000002',balance=20000),23)]:
        checker=lambda observed,b=baseline,s=size:e.compare_records(observed,b,s)
        wrong=baseline[:span]+(b'9' if baseline[span:span+1]!=b'9' else b'8')+baseline[span+1:]
        for kind,bad in [('same_length_wrong_amount',wrong),('omission',baseline[size:]),('duplication',baseline+baseline[:size]),('reordering',baseline[size:]+baseline[:size]),('partial_record',baseline+b'x'),('unexpected_empty',b'')]: record(domain,kind,baseline,bad,checker)
        record(domain,'missing_observation',baseline,None,checker,False)
    # Changed current balance + cycle reset are distinct from output transaction amount.
    before=acct(); after=e.put_number(e.put_number(e.put_number(before,12,24,11000),78,90,0),90,102,0)
    record('interest','balance_not_updated',after,before,lambda b:e.compare_records(b,after,300))
    record('interest','cycle_not_reset',after,e.put_number(after,78,90,500),lambda b:e.compare_records(b,after,300))
    # Full sequence of subtotals rather than dictionary of the last total per type.
    events=[('detail','a',100),('page_total',100),('detail','b',200),('account_total',300),('page_total',200),('grand_total',300)]
    checker=lambda obs:e.compare_events(obs,events)
    for index,kind in [(1,'wrong_first_subtotal'),(4,'wrong_last_subtotal'),(5,'wrong_grand_total')]:
        bad=list(events); bad[index]=(bad[index][0],bad[index][1]+1); record('reporting',kind,events,bad,checker)
    for kind,bad in [('omission',events[:1]+events[2:]),('duplication',events[:2]+[events[1]]+events[2:]),('reordering',events[2:]+events[:2])]: record('reporting',kind,events,bad,checker)
    record('reporting','missing_observation',events,None,checker,False)
    # Document an intentional blind spot rather than imply universal sensitivity.
    base=tx(); bad=base[:304]+b'1999-01-01'+base[314:]
    record('posting','excluded_processing_timestamp',base,bad,lambda b:e.compare_records(e.stable_posting_transactions(b),e.stable_posting_transactions(base),350),False)
    # Shift the model guard by one cent/day in a counterfactual result, not the COBOL.
    a=acct(credit=0,debit=0,limit=100); x=b'4111111111111111'+b'000000001'+a[:11]+b' '*14
    for amount,date,wrong in [(100,b'2025-12-31',102),(101,b'2025-12-31',0),(100,b'2025-12-31',103),(100,b'2026-01-01',0)]:
        expected=e.posting_expected([tx(amount=amount,date=date)],[a],[],[x])['reasons']
        record('posting','shifted_money_or_date_boundary',expected,[wrong],lambda obs,ex=expected:e.compare_events(obs,ex))
    return out

if __name__=='__main__':
    from analysis import write_csv
    rows=qualify(); root=Path(__file__).parent
    targeted=[r for r in rows if r['targetedFault']]
    by=[]
    for domain,kind in sorted({(r['domain'],r['errorClass']) for r in rows}):
        rr=[r for r in rows if (r['domain'],r['errorClass'])==(domain,kind)]
        by.append({'domain':domain,'errorClass':kind,'trials':len(rr),'targeted':sum(r['targetedFault'] for r in rr),'detected':sum(r['detected'] for r in rr),'verdicts':dict(Counter(r['verdict'] for r in rr))})
    result={'trials':len(rows),'targetedFaults':len(targeted),'detectedTargeted':sum(r['detected'] for r in targeted),'unavailable':sum(r['verdict']=='inconclusive' for r in rows),'intentionalBlindSpots':sum(r['verdict']=='pass' for r in rows),'limits':['small purposive output/state counterexample sample','not program mutation score','shared implementation/source; no independent reviewer','negative DISPLAY and overflow not qualified','timestamps deliberately excluded; internal ordering not observable'],'byClass':by,'rows':rows}
    (root/'oracle-qualification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n'); write_csv(root/'oracle-sensitivity.csv',by)
    print(json.dumps({k:v for k,v in result.items() if k not in ['rows','byClass']}))

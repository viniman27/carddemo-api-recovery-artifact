"""Strict byte comparisons: missing is not empty; no trailing partial records."""
from collections import Counter


def number(raw):
    if not raw.isdigit():
        raise ValueError('unqualified_signed_or_nonnumeric_DISPLAY:'+raw.hex())
    return int(raw)


def put_number(raw, start, end, value):
    if value < 0 or value >= 10**(end-start):
        raise ValueError('unqualified_sign_or_overflow')
    return raw[:start]+f'{value:0{end-start}d}'.encode()+raw[end:]


def interest_cents(balance_cents, annual_rate_hundredths):
    # integer cents, annual percentage has two decimal digits; truncate toward zero
    n=balance_cents*annual_rate_hundredths
    return (1 if n>=0 else -1)*(abs(n)//120000)


def interest_expected(accounts, categories, rates, xrefs, parameter):
    if len(parameter)!=10: raise ValueError('parameter_length')
    amap={a[:11]:a for a in accounts}; xmap={x[25:36]:x[:16] for x in xrefs}
    if len(amap)!=len(accounts) or len(xmap)!=len(xrefs): raise ValueError('duplicate_keys')
    rmap={r[:16]:number(r[16:22]) for r in rates}
    total=Counter(); transactions=[]; groups=[]; branches=[]
    for cat in categories:
        key=cat[:11]; a=amap[key]; group=a[112:122]; ratekey=group+cat[11:17]
        branch='specific'
        if ratekey not in rmap: ratekey=b'DEFAULT   '+cat[11:17]; branch='default'
        if ratekey not in rmap: raise ValueError('missing_default_rate_abend_not_zero')
        rate=rmap[ratekey]; branches.append(branch+('_zero' if rate==0 else '_nonzero'))
        if not groups or groups[-1]!=key: groups.append(key)
        if rate==0: continue
        amount=interest_cents(number(cat[17:28]),rate); total[key]+=amount
        # Stable fields only; timestamp/filler are explicitly excluded below.
        b=bytearray(b' '*350); b[:16]=parameter+f'{len(transactions)+1:06d}'.encode()
        b[16:22]=b'010005'; b[22:32]=b'System    '; b[32:56]=b'Int. for a/c '+key
        b[132:143]=f'{amount:011d}'.encode(); b[143:152]=b'000000000'; b[262:278]=xmap[key]
        transactions.append(bytes(b))
    legacy=[]; financial=[]
    for a in accounts:
        k=a[:11]; updated=put_number(a,12,24,number(a[12:24])+total[k])
        updated=put_number(put_number(updated,78,90,0),90,102,0)
        legacy.append(updated if k in groups[:-1] else a)
        financial.append(updated if k in groups else a)
    return {'transactions':transactions,'legacyAccounts':legacy,'financialAccounts':financial,'branches':branches,'groups':[g.decode() for g in groups],'totalInterestCents':dict((k.decode(),v) for k,v in total.items()),'limits':['nonnegative DISPLAY only; overflow unqualified','financial expectation requires final group update; source legacy does not','timestamps and filler excluded from transaction comparison']}


def stable_interest_transactions(data):
    if data is None: return None
    if len(data)%350: return data  # caller rejects framing first
    return b''.join(r[:56]+b' '*76+r[132:278]+b' '*72 for r in (data[i:i+350] for i in range(0,len(data),350)))

def stable_categories(data):
    if data is None: return None
    if len(data)%50: return data
    return b''.join(data[i:i+28]+b' '*22 for i in range(0,len(data),50))

def posting_expected(transactions, accounts, categories, xrefs):
    amap={a[:11]:a for a in accounts}; cmap={c[:17]:c for c in categories}; xmap={x[:16]:x[25:36] for x in xrefs}
    if len(amap)!=len(accounts) or len(cmap)!=len(categories) or len(xmap)!=len(xrefs): raise ValueError('duplicate_key')
    accepted=[]; rejected=[]; reasons=[]; partitions=[]
    descriptions={100:b'INVALID CARD NUMBER FOUND',101:b'ACCOUNT RECORD NOT FOUND',102:b'OVERLIMIT TRANSACTION',103:b'TRANSACTION RECEIVED AFTER ACCT EXPIRATION'}
    for t in transactions:
        amount=number(t[132:143]); card=t[262:278]; reason=0
        if card not in xmap: reason=100
        elif xmap[card] not in amap: reason=101
        else:
            k=xmap[card]; a=amap[k]
            limit=number(a[24:36]); temp=number(a[78:90])-number(a[90:102])+amount
            partitions.append('limit_'+('equal' if temp==limit else 'above' if temp>limit else 'below'))
            partitions.append('expiry_'+('equal' if a[58:68]==t[278:288] else 'after' if a[58:68]<t[278:288] else 'before'))
            if limit<temp: reason=102
            if a[58:68]<t[278:288]: reason=103
        reasons.append(reason)
        if reason:
            rejected.append(t+f'{reason:04d}'.encode()+descriptions[reason].ljust(76,b' '))
            partitions.append('reject_'+str(reason)); continue
        accepted.append(t[:304]+b' '*46)
        k=xmap[card]; a=amap[k]; ck=k+t[16:22]; exists=ck in cmap
        old=cmap.get(ck,ck+b'0'*11+b' '*22)
        cmap[ck]=put_number(old,17,28,number(old[17:28])+amount)
        amap[k]=put_number(put_number(a,12,24,number(a[12:24])+amount),78,90,number(a[78:90])+amount)
        partitions.append('tcat_update' if exists else 'tcat_create')
    return {'accepted':sorted(accepted,key=lambda t:t[:16]),'rejected':rejected,'accounts':[amap[k] for k in sorted(amap)],'categories':[cmap[k] for k in sorted(cmap)],'reasons':reasons,'partitions':sorted(set(partitions))}


def stable_posting_transactions(data):
    if data is None: return None
    if len(data)%350: return data
    return b''.join(r[:304]+b' '*46 for r in (data[i:i+350] for i in range(0,len(data),350)))


def parse_report(data):
    import re
    from decimal import Decimal
    if data is None: return None
    if len(data)%133: raise ValueError('partial_report_record')
    def money(raw):
        t=raw.decode('ascii').strip().replace(',','').replace(' ','')
        if not re.fullmatch(r'[+-]?\d+\.\d{2}',t): raise ValueError('invalid_money:'+repr(raw))
        return int(Decimal(t)*100)
    events=[]
    for i in range(0,len(data),133):
        r=data[i:i+133]
        if r.startswith(b'DALYREPT'):
            events.append(('header',r[91:101].decode(),r[105:115].decode()))
        elif not r.strip(): events.append(('blank',))
        elif r.startswith(b'Transaction ID'): events.append(('columns',))
        elif r==b'-'*133: events.append(('rule',))
        elif r.startswith((b'Page Total',b'Account Total',b'Grand Total')):
            kind='page_total' if r.startswith(b'Page') else 'account_total' if r.startswith(b'Account') else 'grand_total'
            events.append((kind,money(r[97:112])))
        else:
            fields=[r[a:b].decode('ascii').rstrip() for a,b in [(0,16),(17,28),(29,31),(32,47),(48,52),(53,82),(83,93)]]
            events.append(('detail',*fields,money(r[97:112])))
    return events


def compare_events(observed, expected):
    if observed is None: return {'verdict':'inconclusive','failures':['missing_report']}
    differences=[{'index':i,'expected':expected[i] if i<len(expected) else None,'observed':observed[i] if i<len(observed) else None} for i in range(max(len(expected),len(observed))) if (expected[i] if i<len(expected) else None)!=(observed[i] if i<len(observed) else None)]
    return {'verdict':'failed' if differences else 'pass','failures':differences,'expectedRecords':len(expected),'observedRecords':len(observed)}


def report_expected(transactions, dateparm, xrefs, types, categories):
    if len(dateparm)<21: raise ValueError('short_dateparm')
    start,end=dateparm[:10],dateparm[11:21]
    xm={x[:16]:x[25:36] for x in xrefs}; tm={t[:2]:t[2:17] for t in types}; cm={c[:6]:c[6:35] for c in categories}
    selected=[t for t in transactions if start<=t[304:314]<=end]
    events=[]; financial=[]; lines=0; page=0; account=0; grand=0; previous=None
    def add(event): events.append(event); financial.append(event)
    def headers():
        for event in [('header',start.decode(),end.decode()),('blank',),('columns',),('rule',)]: add(event)
    for t in selected:
        card=t[262:278]
        if previous is not None and card!=previous:
            add(('account_total',account)); add(('rule',)); lines+=2; account=0
        previous=card
        if not events: headers(); lines+=4
        if lines%20==0:
            add(('page_total',page)); add(('rule',)); grand+=page; page=0; lines+=2
            headers(); lines+=4
        amount=number(t[132:143]); page+=amount; account+=amount
        add(('detail',t[:16].decode().rstrip(),xm[card].decode(),t[16:18].decode(),tm[t[16:18]].decode().rstrip(),t[18:22].decode(),cm[t[16:22]].decode().rstrip(),t[22:32].decode().rstrip(),amount)); lines+=1
    eof_selected=bool(transactions and start<=transactions[-1][304:314]<=end)
    if eof_selected:
        stale=number(transactions[-1][132:143]); events.extend([('page_total',page+stale),('rule',),('grand_total',grand+page+stale)])
        financial.extend([('page_total',page),('rule',),('grand_total',grand+page)])
    return {'legacy':events,'financial':financial,'selectedCount':len(selected),'sourceCount':len(transactions),'eofSelected':eof_selected,'limits':['financial totals checked only where source emits totals; no invented final account subtotal','no JCL sort execution claimed; actual input order retained']}


def compare_records(observed, expected, size):
    if observed is None or expected is None:
        return {'verdict':'inconclusive','failures':['missing_evidence']}
    errors=[]
    if len(observed)%size: errors.append('partial_record')
    if len(expected)%size: raise ValueError('invalid expected framing')
    obs=[observed[i:i+size] for i in range(0,len(observed),size)]
    exp=[expected[i:i+size] for i in range(0,len(expected),size)]
    if Counter(obs)!=Counter(exp): errors.append('value_or_multiplicity')
    if obs!=exp: errors.append('ordered_records_differ')
    return {'verdict':'failed' if errors else 'pass','failures':errors,'expectedRecords':len(exp),'observedRecords':len(obs)}

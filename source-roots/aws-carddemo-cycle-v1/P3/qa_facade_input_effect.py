#!/usr/bin/env python3
"""Outside-in technical regression: requested bytes must reach COBOL resources."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

CYCLE=Path(__file__).resolve().parent.parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module

def main():
    out=Path(tempfile.mkdtemp(prefix='facade-input-review-',dir=Path(__file__).resolve().parent))
    rows=[]
    for arm,folder in [('E1','P2c-zero-shot'),('E2','P2c-few-shot')]:
        module=load(arm+'_input_review',CYCLE/folder/'p2c_facade.py')
        for n in range(1,4):
            cid=f'{arm}-{n}'
            for track in ['posting','interest']:
                row={'contract':cid,'track':track}
                try:
                    request=module.sample_request_for(cid,track) if arm=='E1' else module.sample_request(cid,track)
                    if track=='posting':
                        field='dailyTransactions' if 'dailyTransactions' in request else 'transactions'
                        request[field]=[];resource='DALYTRAN';expected=b''
                    else:
                        field=next(k for k in ['parameterDate','idPrefix','transactionIdPrefix'] if k in request)
                        request[field]='INPUTCHECK';resource='PARMFILE';expected=b'INPUTCHECK'
                    result=module.ContractFacade(cid).execute(track,request) if arm=='E1' else module.execute(cid,track,request)
                    ap=Path(result['p2b_audit_path'] if arm=='E1' else result['p2bAuditPath'])
                    audit=json.loads(ap.read_text());rp=Path(audit['INV']['workdir'])/resource
                    actual=rp.read_bytes()
                    row.update({'passed':actual==expected,'resource':str(rp),'actualBytes':len(actual),'expectedBytes':len(expected),'audit':str(ap),'request':request})
                except Exception as exc:row.update({'passed':False,'error':repr(exc)})
                rows.append(row)
                (out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({'evidence':str(out/'results.json'),'checks':len(rows),'passed':sum(x['passed'] for x in rows)},indent=2))
    return 0 if all(x['passed'] for x in rows) else 1
if __name__=='__main__':raise SystemExit(main())

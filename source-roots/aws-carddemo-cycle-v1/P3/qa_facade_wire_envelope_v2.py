#!/usr/bin/env python3
"""Validate actual HTTP entity bodies, never a nested projection."""
import importlib.util,sys,json,threading,tempfile,urllib.request,urllib.error,http.server
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator,RefResolver
ROOT=Path(__file__).resolve().parent; C=ROOT.parent

def load(name,folder):
    s=importlib.util.spec_from_file_location(name,C/folder/'p2c_facade.py');m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def main():
    out=Path(tempfile.mkdtemp(prefix='wire-envelope-review-',dir=ROOT));rows=[]
    for arm,folder in [('E1','P2c-zero-shot'),('E2','P2c-few-shot')]:
        m=load(arm+'wire',folder)
        for n in range(1,4):
            cid=f'{arm}-{n}';spec=yaml.safe_load((C/'collection-01'/cid/'response-original.txt').read_text())
            server=m.FacadeServer(output_root=out/cid,contract_id=cid) if arm=='E1' else http.server.HTTPServer(('127.0.0.1',0),m.Handler)
            if arm=='E2':server.contract_id=cid
            port=server.port if arm=='E1' else server.server_port
            t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
            try:
                for path,pitem in spec['paths'].items():
                    op=pitem['post'];track={'postDailyTransactions':'posting','generateInterestTransactions':'interest','generateTransactionReport':'reporting'}[op['operationId']]
                    body=m.sample_request_for(cid,track) if arm=='E1' else m.sample_request(cid,track)
                    req=urllib.request.Request(f'http://127.0.0.1:{port}{path}',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
                    try:
                        with urllib.request.urlopen(req,timeout=90) as r:raw=r.read();status=r.status
                    except urllib.error.HTTPError as r:raw=r.read();status=r.code
                    (out/f'{cid}-{track}-wire.json').write_bytes(raw)
                    response=spec['paths'][path]['post']['responses'].get(str(status))
                    if response and '$ref' in response:
                        cur=spec
                        for piece in response['$ref'][2:].split('/'):cur=cur[piece]
                        response=cur
                    errors=['undocumented status'] if response is None else [e.message for e in Draft202012Validator(response['content']['application/json']['schema'],resolver=RefResolver.from_schema(spec)).iter_errors(json.loads(raw))]
                    rows.append({'contract':cid,'track':track,'status':status,'wireValid':not errors,'errors':errors,'raw':str(out/f'{cid}-{track}-wire.json')})
                    (out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
            finally:
                server.shutdown()
                if arm=='E2':server.server_close()
                t.join()
    print(json.dumps({'evidence':str(out/'results.json'),'checks':len(rows),'passed':sum(r['wireValid'] for r in rows)},indent=2))
    return 0 if all(r['wireValid'] for r in rows) else 1
if __name__=='__main__':raise SystemExit(main())

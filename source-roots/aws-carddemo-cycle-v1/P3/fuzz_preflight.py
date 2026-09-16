#!/usr/bin/env python3
"""Schemathesis qualification against an isolated synthetic HTTP service only.

No arguments permit loading AWS, arbitrary schemas, or remote targets. Hypothesis
collects without HTTP; the fixed suite is written before serial one-shot replay.
"""
import argparse
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from importlib.metadata import version
import json
from pathlib import Path
import threading
import time

import requests
import schemathesis
from schemathesis import checks
from schemathesis.core.failures import FailureGroup
from schemathesis.generation import GenerationMode
from hypothesis import given, settings, seed, Phase

SPEC = {'openapi':'3.1.0','info':{'title':'Synthetic qualification; NOT CardDemo','version':'1'},'paths':{'/probe':{'post':{'operationId':'syntheticProbe','requestBody':{'required':True,'content':{'application/json':{'schema':{'type':'object','additionalProperties':False}}}},'responses':{'500':{'description':'documented synthetic error','content':{'application/json':{'schema':{'type':'object','required':['marker'],'additionalProperties':False,'properties':{'marker':{'const':'synthetic'}}}}}}}}}}}
SEEDS = (104729,130363,155921)


def qualify(output):
    output.mkdir(parents=True,exist_ok=False)
    schema=schemathesis.openapi.from_dict(SPEC)
    operation=schema['/probe']['POST']
    cases=[]; generation=[]
    for number in SEEDS:
        for mode in (GenerationMode.POSITIVE,GenerationMode.NEGATIVE):
            batch=[]
            @seed(number)
            @settings(max_examples=12,phases=(Phase.generate,),database=None,deadline=None)
            @given(operation.as_strategy(generation_mode=mode))
            def collect(case):
                batch.append(case)
            started=time.monotonic(); collect()
            generation.append({'seed':number,'mode':mode.value,'generated':len(batch),'maxExamples':12,'seconds':time.monotonic()-started})
            cases.extend((number,mode.value,case) for case in batch)
    received=[]
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body=self.rfile.read(int(self.headers.get('Content-Length','0')))
            received.append({'path':self.path,'bodyBase64':base64.b64encode(body).decode()})
            marker='bad' if len(received)==len(cases) else 'synthetic'
            content=json.dumps({'marker':marker}).encode()
            self.send_response(500);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
        def log_message(self,format,*args): pass
    server=HTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    prepared=[]; frozen=[]
    try:
        for number,mode,case in cases:
            req=requests.Request(**case.as_transport_kwargs(base_url=base)).prepare()
            body=req.body.encode() if isinstance(req.body,str) else req.body
            prepared.append(req)
            frozen.append({'seed':number,'mode':mode,'method':req.method,'url':req.url,'headers':list(req.headers.items()),'bodyPresent':body is not None,'bodyBase64':None if body is None else base64.b64encode(body).decode()})
        suite=json.dumps(frozen,indent=2).encode()
        (output/'frozen-synthetic-suite.json').write_bytes(suite)
        (output/'synthetic-openapi.json').write_text(json.dumps(SPEC,indent=2))
        if received: raise RuntimeError('HTTP happened before freezing')
        checks.load_all_checks()
        names={'status_code_conformance','content_type_conformance','response_schema_conformance'}
        selected=[check for check in checks.CHECKS.get_all() if check.__name__ in names]
        if {check.__name__ for check in selected} != names: raise RuntimeError('checker API mismatch')
        results=[]
        # No raise_for_status, no Case.call, no redirect, no session retry adapter.
        with requests.Session() as session:
            session.trust_env=False
            for i,((_,_,case),request) in enumerate(zip(cases,prepared)):
                response=session.send(request,timeout=5,allow_redirects=False)
                failures=[]
                try: case.validate_response(response,checks=selected)
                except FailureGroup as exc: failures.append(str(exc))
                results.append({'index':i,'status':response.status_code,'body':response.text,'failures':failures})
        positive=sorted({base64.b64decode(row['bodyBase64']).decode() for row in frozen if row['mode']=='positive'})
        matching=all(wire['bodyBase64']==saved['bodyBase64'] for wire,saved in zip(received,frozen))
        documented=bool(results) and all(row['status']==500 and not row['failures'] for row in results[:-1])
        detected=bool(results[-1]['failures']) if results else False
        report={'kind':'synthetic-tool-qualification-not-experiment','passed':matching and documented and detected and len(received)==len(frozen),'awsLoaded':False,'versions':{name:version(name) for name in ['schemathesis','hypothesis','requests']},'generation':generation,'phases':['generate'],'database':None,'httpCalls':len(received),'frozenCases':len(frozen),'unexpectedHttpCalls':len(received)-len(frozen),'documented500Accepted':documented,'malformedResponseDetected':detected,'positiveBodyVariants':positive,'suiteSha256':hashlib.sha256(suite).hexdigest(),'checkers':sorted(names),'limits':['12-example synthetic rehearsal, not official budget','no AWS schema, fixture or oracle','campaign reset and deadline orchestration not implemented here']}
        (output/'http-results.json').write_text(json.dumps(results,indent=2))
        (output/'wire-receipts.json').write_text(json.dumps(received,indent=2))
        (output/'report.json').write_text(json.dumps(report,indent=2))
        print(json.dumps(report,indent=2))
        return report['passed']
    finally:
        server.shutdown();server.server_close();thread.join()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();raise SystemExit(0 if qualify(args.output) else 1)

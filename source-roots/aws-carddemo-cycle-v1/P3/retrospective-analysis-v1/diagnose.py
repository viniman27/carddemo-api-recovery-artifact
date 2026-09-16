"""Saved request/log linkage and local-only schema numeric countercheck."""
import json,base64,hashlib,warnings
from decimal import Decimal
from pathlib import Path
import yaml
with warnings.catch_warnings():
    warnings.simplefilter('ignore',DeprecationWarning)
    from jsonschema import Draft202012Validator, RefResolver
ROOT=Path(__file__).resolve().parents[2]
def pin(p): return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def diagnose():
    p=ROOT/'P3'; reportpath=p/'complementary-matrix-v2/parent-full84-v1/campaign/campaign-report.json'; freezepath=p/'complementary-matrix-v2/parent-plan-absolute-v1/suite.freeze.json'
    logs=p/'complementary-matrix-v2/parent-full84-v1/p2b-preparation/isolated-cycle/aws-carddemo-cycle-v1/P2c-few-shot/outputs/http-rejections.jsonl'
    report=json.loads(reportpath.read_text()); freeze={c['case_id']:c for c in json.loads(freezepath.read_text())['cases']}; logrows=[json.loads(s) for s in logs.read_text().splitlines() if s]
    out=[]
    for ch in report['suiteReports'][0]['checks']:
        if ch['receipt']['status']!=400: continue
        fc=freeze[ch['case_id']]; raw=base64.b64decode(fc['request']['body_b64']); body=json.loads(raw)
        sp=ROOT/'collection-01'/ch['contractId']/'response-original.txt'; spec=yaml.safe_load(sp.read_text()); path=ch['receipt']['path']
        schema=spec['paths'][path]['post']['requestBody']['content']['application/json']['schema']
        def errors(spec,schema,body):
            v=Draft202012Validator(schema,resolver=RefResolver.from_schema(spec))
            return [{'path':list(e.path),'validator':e.validator,'message':e.message} for e in v.iter_errors(body)]
        floats=errors(spec,schema,body)
        ds=json.loads(json.dumps(spec),parse_float=Decimal); db=json.loads(raw,parse_float=Decimal)
        decimals=errors(ds,ds['paths'][path]['post']['requestBody']['content']['application/json']['schema'],db)
        pid=ch['application']['lifecycle']['pid']; matches=[r for r in logrows if r['pid']==pid and r['contractId']==ch['contractId'] and r['path']==path]
        response=base64.b64decode(ch['receipt']['response_body_b64'])
        assert hashlib.sha256(response).hexdigest()==ch['receipt']['response_sha256']
        out.append({'caseId':ch['case_id'],'pid':pid,'pidLinked':len(matches)==1,'historicalLog':matches,'requestSha256':hashlib.sha256(raw).hexdigest(),'rawResponse':response.decode(),'floatErrors':floats,'decimalErrors':decimals,'classification':'pre_COBOL_binary_float_multipleOf_rejection','pins':[pin(x) for x in [reportpath,freezepath,logs,sp]],'limits':'Local validator countercheck only; no API rerun or fix; Decimal mode is diagnostic, not replacement campaign result.'})
    return out
if __name__=='__main__':
    rows=diagnose(); Path(__file__).with_name('fewshot-diagnosis.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n'); print(json.dumps({'cases':len(rows),'pidLinked':sum(r['pidLinked'] for r in rows),'floatRejected':sum(bool(r['floatErrors']) for r in rows),'decimalAccepted':sum(not r['decimalErrors'] for r in rows)}))

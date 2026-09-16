"""Main-process, specifically authorized T1 continuation. No probe/retry."""
import json, hashlib, importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PREV=ROOT.parent/'t1-generation-02'
ORDER=['E2-1','E2-2','E2-3','E3-SDD-stage6r3']
def save(path,obj):
 path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def execute_remaining(send,out):
 report={'status':'running','order':ORDER,'items':[],'officialCampaign':False}
 save(out/'summary.json',report)
 for cid in ORDER:
  report['activeContract']=cid; save(out/'summary.json',report)
  item=send(cid); report['items'].append(item)
  report['activeContract']=None
  save(out/'summary.json',report)
  if item['classification'] not in ('complete','invalid_output_contract'):
   report['status']='stopped'; break
 else:
  report['status']='complete' if all(x['classification']=='complete' for x in report['items']) else 'completed_with_invalid_outputs'
 save(out/'summary.json',report)
 return report

def main():
 # Exclusive marker prevents accidental repeat of this authorized batch.
 with (ROOT/'STARTED.lock').open('x') as lock: lock.write('one authorized batch; never rerun\n')
 spec=importlib.util.spec_from_file_location('qualified_transport',PREV/'run_t1_generation.py')
 assert spec and spec.loader
 old=importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
 old.OUT=ROOT
 previous=json.loads((PREV/'summary.json').read_text())
 assert [i['contractId'] for i in previous['items'] if i['classification']=='complete']==['E1-1','E1-2','E1-3']
 for item in previous['items']:
  raw=(PREV/item['rawSsePath']).read_bytes()
  assert hashlib.sha256(raw).hexdigest()==item['rawSseSha256']
  assert old.parse_completed(raw.decode())['returnedModel']=='gpt-6-astra'
 old.verify_pins()
 bodies={cid:old.build_effective_payload(cid) for cid in ORDER}
 transformations=json.loads((PREV/'transformations.json').read_text())
 pins={x['contractId']:x['effectiveOutboundSha256Preview'] for x in transformations}
 checks=[]
 for cid,body in bodies.items():
  encoded=json.dumps(body,ensure_ascii=False,separators=(',',':')).encode()
  assert hashlib.sha256(encoded).hexdigest()==pins[cid], cid
  assert 'previous_response_id' not in body
  checks.append({'contractId':cid,'sha256':pins[cid],'bytes':len(encoded),'identicalToGeneration02Preview':True})
 save(ROOT/'consent.json',{'source':'User replied autorizo to replacement E2-1 plus first E2-2 E2-3 SDD, no new probe; main-process runner','authorized':True,'order':ORDER,'replacementOnly':'E2-1','retry':False,'fallback':False,'officialCampaignAuthorized':False})
 save(ROOT/'transformations.json',{'payloadChangesFromGeneration02':[],'checks':checks,'transportReuse':str(PREV/'run_t1_generation.py'),'transportSha256':hashlib.sha256((PREV/'run_t1_generation.py').read_bytes()).hexdigest(),'preservedCompleteE1':True})
 credentials=old.resolve_runtime_credentials()
 assert credentials.get('provider')==old.PROVIDER and credentials.get('base_url','').rstrip('/')==old.BASE_URL
 def send(cid):
  row={'contractId':cid,**old.call_provider(credentials,cid,bodies[cid],timeout_s=300.0)}
  rawpath=ROOT/'raw-sse'/f'{cid}.sse.txt'
  if rawpath.exists():
   raw=rawpath.read_bytes(); row['rawSseSha256']=hashlib.sha256(raw).hexdigest(); row['rawSseBytes']=len(raw)
  if row['classification']=='invalid_provider_error': row['classification']='provider_failure'
  if row['classification']=='invalid_parse_or_incomplete':
   events=[]
   for line in rawpath.read_bytes().splitlines():
    if line.startswith(b'data: '):
     try: events.append(json.loads(line[6:]).get('type'))
     except (ValueError,AttributeError): pass
   if any(e in events for e in ['response.failed','response.incomplete','error']): row['classification']='provider_failure'
   elif 'response.completed' not in events: row['classification']='interrupted_missing_completion'
   else: row['classification']='invalid_completed_response'
  if row['classification']=='complete':
   row['outputValidation']=old.validate_json_output(cid,ROOT/row['parsedPath'])
   if not row['outputValidation']['validJson'] or not row['outputValidation']['strictTopScenarios']: row['classification']='invalid_output_contract'
  save(ROOT/'receipts'/f'{cid}.reconciled.json',row)
  return row
 report=execute_remaining(send,ROOT)
 print(json.dumps({'status':report['status'],'items':[{k:x.get(k) for k in ['contractId','classification','returnedModel']} for x in report['items']]},ensure_ascii=False),flush=True)
 return 0 if report['status']=='complete' else 2
if __name__=='__main__': raise SystemExit(main())

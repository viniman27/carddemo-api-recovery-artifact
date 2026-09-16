"""One-time mechanical assembly; no generation or execution."""
import sys,json,hashlib,copy
from pathlib import Path
from urllib.parse import urlsplit
C=Path(__file__).resolve().parents[2]
P3=C/'P3'
sys.path.insert(0,str(P3/'campaign-harness-v3/src'))
from campaign_harness import Suite,UnionBuilder,freeze_suite,load_frozen_suite
OUT=P3/'campaign-freeze-package-v1'
assert not OUT.exists(), 'never overwrite package'
OUT.mkdir()
cfg=json.loads((P3/'campaign-configuration-v2/campaign-config-v2.json').read_text())
material=P3/'aws-suite-materialization-v1/final-20260915T155901'
rows=[]; sources=[]; union_ledgers={}
for contract in cfg['contracts']['contracts']:
 cid=contract['contractId']; normalized=[]
 opmap={(o['method'].upper(),o['path']):o for o in contract['operations']}
 for condition,src in [('T1',P3/'t1-import-qualification-v2/CANDIDATES'/f'T1-REAL-{cid}.json'),('T2',material/'T2/contracts'/cid/'T2-suite.json'),('T3',material/'T3/contracts'/cid/'T3-suite.json')]:
  suite=load_frozen_suite(src)
  sources.append({'path':str(src.relative_to(C)),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
  cases=copy.deepcopy(suite.cases)
  for case in cases:
   before=case.request.to_dict()
   op=opmap[(case.request.method.upper(),urlsplit(case.request.path).path)]
   fixture_track=case.resource_package_id.split('.')[0]
   assert fixture_track in ['posting','interest','reporting']
   case.parameters.update(contractId=cid,operationId=op['operationId'],track=fixture_track)
   case.suite_id=condition
   assert case.request.to_dict()==before
  logical=Suite(condition,cases);normalized.append(logical)
  artifact=Suite(f'{cid}-{condition}',copy.deepcopy(cases))
  dest=OUT/cid/f'{condition}.json';freeze_suite(artifact,dest)
  reread=load_frozen_suite(dest);assert len(reread.cases)==len(cases)
  rows.append({'contractId':cid,'condition':condition,'cases':len(cases),'path':str(dest.relative_to(C)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
 union,ledger=UnionBuilder().build(normalized)
 union_ledgers[cid]=ledger
 for case in union.cases:
  case.case_id=cid+'-'+case.case_id
 dest=OUT/cid/'T4.json';freeze_suite(Suite(f'{cid}-T4',union.cases),dest)
 reread=load_frozen_suite(dest);assert len(reread.cases)==len(union.cases)
 rows.append({'contractId':cid,'condition':'T4','cases':len(union.cases),'path':str(dest.relative_to(C)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
assert len(rows)==28
manifest={'kind':'campaign-freeze-package-v1','state':'frozen_bytes_pending_runtime_readiness','sourcePins':sources,'suites':rows,'counts':{t:sum(r['cases'] for r in rows if r['condition']==t) for t in ['T1','T2','T3','T4']},'campaignAuthorizedByUser':True,'officialRuntimeStarted':False,'humanInspectionClaimed':False,'transformations':['Explicit routing metadata from per-contract source suite and exact original registry method/path; request bytes/headers/body-kind unchanged.','Suite naming for unique runtime directories; T4 IDs prefixed by contract.','Union by existing harness identity policy T1->T2->T3; provenance and duplication ledger preserved.'],'limits':['Fixtures remain identified by original candidate IDs; readiness must establish exact byte promotion, isolation and measurement before runtime.','T3 expectation may be inconclusive independently of contractual structural check.','T1 source assertions not independent oracle; no new LLM calls.','T2 underfill retained; no regeneration.']}
(OUT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
(OUT/'UNION-LEDGER.json').write_text(json.dumps(union_ledgers,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'counts':manifest['counts'],'suiteCount':len(rows),'output':str(OUT)}))

"""Separate arithmetic, preservation and case-delta checks; no business execution."""
import json,hashlib,csv
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parent; V1=R.parent/'retrospective-analysis-v1'; run=R/'run-01'
load=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rows(path): return [json.loads(l) for l in path.read_text().splitlines()]
def key(r): return r['strategy'],r['contract'],r['caseId']
new={l:rows(run/(l+'-cases.jsonl')) for l in ['official','complementary']}
old={l:rows(V1/'run-04'/(l+'-cases.jsonl')) for l in new}
summary=load(run/'summary.json')
assert {k:len(v) for k,v in new.items()}==summary['applications']=={'official':12700,'complementary':84}
for lane in new:
 assert len({key(r) for r in new[lane]})==len(new[lane])
 assert {key(r) for r in new[lane]}=={key(r) for r in old[lane]}
 assert not any(r['provenanceErrors'] for r in new[lane])
 assert not any('collector_error' in reason for r in new[lane] for reason in r['limit'])
oldmap={key(r):r for r in old['official']}
delta=[r for r in new['official'] if r['checks'] and not oldmap[key(r)]['checks']]
assert len(delta)==68
assert Counter(r['track'] for r in delta)=={'posting':8,'reporting':60}
assert all(r['partitions']==['reject_100'] for r in delta if r['track']=='posting')
assert sum('dateparm_eof_before_transaction_loop' in r['partitions'] for r in delta)==58
assert sum(any(c['name']=='missing_first_xref_abort' for c in r['checks']) for r in delta)==2
assert all(c['verdict'] in ['pass','not_exercised'] for r in delta for c in r['checks'])
counts={l:dict(Counter(c['verdict'] for r in new[l] for c in r['checks'])) for l in new}
assert counts['official']=={'pass':3574,'not_exercised':486}
assert counts['complementary']=={'pass':324,'failed':22,'not_exercised':14}
assert sum(bool(r['checks']) for r in new['official'])==sum(r['businessObserved'] for r in new['official'])==1070
assert sum(bool(r['checks']) for r in new['complementary'])==78
assert {key(r):r['checks'] for r in new['complementary']}=={key(r):r['checks'] for r in old['complementary']}
for r in new['official']:
 if oldmap[key(r)]['checks']: assert r['checks']==oldmap[key(r)]['checks']
checked=0
for path in [run/'source-pins.json',V1/'run-04/source-pins.json']:
 for p in load(path):
  f=Path(p['path']); assert sha(f)==p['sha256'] and f.stat().st_size==p['bytes'],str(f); checked+=1
assert sha(R.parent/'official-campaign-large12k-run-v2/campaign-report.json')=='bdef12959aebfcf38f06e9e0720d7e211cdd66d9d7084043d1cfe496188e68aa'
methods=load(R/'METHOD-EVIDENCE.json')
for p in methods['pins']: assert sha(Path(p['path']))==p['sha256']
assert methods['actualCampaignStrategyCounts']==dict(Counter(r['strategy'] for r in new['official']))
sets={s:{(r['contract'],r['track'],r['semanticInputKey']) for r in new['official'] if r['strategy']==s and r['semanticInputKey'] and r['businessObserved']} for s in ['T1','T2','T3','T4']}
a,b,c,u=[sets[s] for s in ['T1','T2','T3','T4']]; assert a|b|c==u
contribution={'T1':len(a),'T2':len(b),'T3':len(c),'union':len(a|b|c),'exclusiveT1':len(a-b-c),'exclusiveT2':len(b-a-c),'exclusiveT3':len(c-a-b),'incrementalT2afterT1':len(b-a),'incrementalT3afterT12':len(c-a-b),'overlapT1T2':len(a&b),'overlapAll':len(a&b&c)}
assert contribution==load(V1/'FINAL-VERIFICATION.json')['contributionWithinContractTrack']
q=load(R/'oracle-qualification.json'); assert (q['trials'],q['detectedTargeted'],q['unavailable'],q['intentionalBlindSpots'])==(35,30,4,1)
signed=load(R/'signed-probe/qualification.json'); raw=(R/'signed-probe/output.raw').read_bytes()
assert sha(R/'signed-probe/probe.cbl')==signed['sourceSha256'] and sha(R/'signed-probe/output.raw')==signed['rawSha256']
assert signed['trials']==len(signed['rows'])==13
for i,r in enumerate(signed['rows']):
 expected=r['expectedCents']; digits=f'{abs(expected):011d}'.encode()
 if expected<0: digits=digits[:-1]+bytes([112+expected.__abs__()%10])
 assert raw[i*11:(i+1)*11]==digits==bytes.fromhex(r['rawHex']) and r['decodePass'] and r['encodePass']
diag=load(V1/'fewshot-diagnosis.json'); assert len(diag)==6
assert all(r['pidLinked'] and r['floatErrors'] and not r['decimalErrors'] for r in diag)
for r in diag:
 for p in r['pins']: assert sha(Path(p['path']))==p['sha256']
result={'status':'verified','applications':summary['applications'],'newlyCheckedOfficialApplications':len(delta),'resolvedGroups':{'emptyDateparmEOF':58,'signedPostingInputs':8,'firstMissingCardxrefAbort':2},'officialApplicationsWithChecks':1070,'officialApplicationsWithoutLinkedAudit':11630,'checkVerdicts':counts,'v2SourcePins':len(load(run/'source-pins.json')),'v1AndV2PinEntriesVerified':checked,'methodPins':len(methods['pins']),'priorCheckResultsUnchanged':True,'contributionWithinContractTrack':contribution,'checkerOutputProbes':35,'signedRepresentationTrials':13,'newBusinessApplications':0,'limits':['Only partial assertions per invocation, never whole-obligation certification','Signed representation qualified on local GnuCOBOL; eight actual negative cases reject missing cards, not accepted signed financial arithmetic','Overflow, general I/O failures, internal effect order and timestamps remain unqualified','No independent expert oracle adjudication; all extension findings are retrospective','Historical external audit hash-pinning limitations remain']}
(R/'FINAL-VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n'); (R/'resolved-cases.json').write_text(json.dumps([{'strategy':r['strategy'],'contract':r['contract'],'caseId':r['caseId'],'track':r['track'],'partitions':r['partitions'],'checkNames':[c['name'] for c in r['checks']]} for r in delta],indent=2)+'\n'); print(json.dumps(result))

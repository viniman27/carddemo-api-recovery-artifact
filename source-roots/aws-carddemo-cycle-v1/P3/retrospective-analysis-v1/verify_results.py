"""Independent final arithmetic/integrity checks over completed saved outputs."""
import json,csv,hashlib
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parent
run=ROOT/'run-04'
load=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
summary=load(run/'summary.json')
rows={lane:[json.loads(l) for l in (run/f'{lane}-cases.jsonl').read_text().splitlines()] for lane in ['official','complementary']}
assert {k:len(v) for k,v in rows.items()}==summary['applications']=={'official':12700,'complementary':84}
assert len({(r['strategy'],r['contract'],r['caseId']) for r in rows['official']})==12700
assert len({r['caseId'] for r in rows['complementary']})==84
assert all(not r['provenanceErrors'] for rr in rows.values() for r in rr)
pins=load(run/'source-pins.json'); changed=[p['path'] for p in pins if sha(Path(p['path']))!=p['sha256'] or Path(p['path']).stat().st_size!=p['bytes']]
assert not changed,changed
# Old reports were never rewritten; compare pins from the earlier completed analysis too.
prior=load(ROOT/'run-03/source-pins.json'); old={p['path']:p['sha256'] for p in prior if not Path(p['path']).is_relative_to(ROOT)}
assert all(sha(Path(path))==h for path,h in old.items())
official=ROOT.parent/'official-campaign-large12k-run-v2/campaign-report.json'
assert sha(official)=='bdef12959aebfcf38f06e9e0720d7e211cdd66d9d7084043d1cfe496188e68aa'
cat=load(ROOT.parent/'complementary-validation-v2/scenario-catalog.json'); source=Path(cat['sourceBase']); anchors={a['path']:a['sha256'] for o in cat['obligations'] for a in o['source_anchors']}
assert all(sha(source/path)==h for path,h in anchors.items())
with (run/'obligation-coverage.csv').open() as f: coverage=list(csv.DictReader(f))
assert len(coverage)==7*25*5
comp=rows['complementary']; checks=[(r,c) for r in comp for c in r['checks']]
assert Counter(c['verdict'] for r,c in checks)=={'pass':324,'failed':22,'not_exercised':14}
assert sum(c['name']=='accounts_financial_all_groups' and c['verdict']=='failed' for r,c in checks)==14
assert sum(c['name']=='report_all_subtotals_grand_financial' and c['verdict']=='failed' for r,c in checks)==8
assert sum(c['verdict']=='failed' and r['track']=='posting' for r,c in checks)==0
assert sum(r['businessObserved'] for r in comp)==78
assert not any(any('collector_error' in x for x in r['limit']) for r in comp)
# Exact set arithmetic independent of the analysis summary's contribution function.
sets={s:{(r['contract'],r['track'],r['semanticInputKey']) for r in rows['official'] if r['strategy']==s and r['semanticInputKey'] and r['businessObserved']} for s in ['T1','T2','T3','T4']}
a,b,c,u=[sets[s] for s in ['T1','T2','T3','T4']]
assert a|b|c==u
contribution={'T1':len(a),'T2':len(b),'T3':len(c),'union':len(a|b|c),'exclusiveT1':len(a-b-c),'exclusiveT2':len(b-a-c),'exclusiveT3':len(c-a-b),'incrementalT2afterT1':len(b-a),'incrementalT3afterT12':len(c-a-b),'overlapT1T2':len(a&b),'overlapAll':len(a&b&c)}
qualification=load(ROOT/'oracle-qualification.json'); assert qualification['trials']<=60
assert qualification['detectedTargeted']==sum(r['targetedFault'] and r['verdict']=='failed' for r in qualification['rows'])
diagnosis=load(ROOT/'fewshot-diagnosis.json'); assert len(diagnosis)==6 and all(r['pidLinked'] and r['floatErrors'] and not r['decimalErrors'] for r in diagnosis)
for row in diagnosis:
    for p in row['pins']: assert sha(Path(p['path']))==p['sha256']
result={'status':'verified','applications':{k:len(v) for k,v in rows.items()},'verifiedInputPins':len(pins),'earlierExternalPinsUnchanged':len(old),'sourceAnchorsVerified':len(anchors),'obligationCells':len(coverage),'contributionWithinContractTrack':contribution,'complementaryCheckVerdicts':dict(Counter(c['verdict'] for r,c in checks)),'qualification':{k:qualification[k] for k in ['trials','targetedFaults','detectedTargeted','unavailable','intentionalBlindSpots']},'sourcePreservationFailures':changed,'limitations':['No whole-obligation completeness claim','Official 58 short/empty DATEPARM and 8 signed DISPLAY applications have no qualified success-path oracle','External few-shot/SDD audit hashes not in historical application trees; linkage uses frozen report path/invocation/cwd and audit snapshots','Logical input diversity is not behavioral diversity or statistical independence','No new business executions; output mutations are checker qualification only']}
(ROOT/'FINAL-VERIFICATION.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(result,ensure_ascii=False))

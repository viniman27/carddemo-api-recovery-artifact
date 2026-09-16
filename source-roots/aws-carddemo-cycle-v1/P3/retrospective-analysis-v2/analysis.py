"""Reproducible local reanalysis. No API/business program invocation."""
import argparse,csv,json,sys
from collections import Counter,defaultdict
from pathlib import Path
from collector import Store,analyze,canonical,digest

def condition(suite_id, contract):
    matches=[s for s in ['T1','T2','T3','T4'] if suite_id==contract+'-'+s]
    if len(matches)!=1: raise ValueError('unqualified enclosing suite provenance:'+suite_id)
    return matches[0]

def contributions(rows):
    groups=defaultdict(lambda:defaultdict(set))
    for r in rows:
        if r['lane']!='official': continue
        g=groups[(r['contract'],r['track'])]
        if r['businessObserved'] and r['semanticInputKey']: g[r['strategy']].add(r['semanticInputKey'])
    out=[]
    for (c,t),g in sorted(groups.items()):
        a,b,d,u=[g[s] for s in ['T1','T2','T3','T4']]; union=a|b|d
        out.append({'contract':c,'track':t,'T1':len(a),'T2':len(b),'T3':len(d),'unionT123':len(union),'exclusiveT1':len(a-b-d),'exclusiveT2':len(b-a-d),'exclusiveT3':len(d-a-b),'incrementalT2_afterT1':len(b-a),'incrementalT3_afterT12':len(d-a-b),'overlapT1T2':len(a&b),'overlapT1T3':len(a&d),'overlapT2T3':len(b&d),'overlapAll':len(a&b&d),'T4_states':len(u),'T4_not_in_union':len(u-union),'union_not_in_T4':len(union-u)})
    return out

def write_csv(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader()
        for r in rows: w.writerow({k:json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in r.items()})

def summarize(rows,catalog):
    by=defaultdict(list)
    for r in rows: by[(r['lane'],r['strategy'],r['contract'],r['track'])].append(r)
    counts=[]; obligations=[]; partition_checks=[]
    for key,cases in sorted(by.items()):
        lane,strategy,contract,track=key
        checks=[ch for r in cases for ch in r['checks']]
        counts.append({'lane':lane,'strategy':strategy,'contract':contract,'arm':cases[0]['arm'],'track':track,'applications':len(cases),'http':dict(Counter(r['status'] for r in cases)),'businessObserved':sum(r['businessObserved'] for r in cases),'semanticStates':len({r['semanticInputKey'] for r in cases if r['semanticInputKey']}),'semanticStateUnknown':sum(r['semanticInputKey'] is None for r in cases),'requestBodies':len({r['requestKey'] for r in cases}),'checkedApplications':sum(bool(r['checks']) for r in cases),'checkVerdicts':dict(Counter(ch['verdict'] for ch in checks)),'provenanceErrors':sum(bool(r['provenanceErrors']) for r in cases),'collectorErrors':sum(any('collector_error' in s for s in r['limit']) for r in cases)})
        for obl in catalog['obligations']:
            prefix={'posting':'POSTTRAN','interest':'INTCALC','reporting':'TRANREPT'}[track]
            if not obl['id'].startswith(prefix): continue
            linked=[(r,ch) for r in cases for ch in r['checks'] if obl['id'] in ch['obligations']]
            obligations.append({'lane':lane,'strategy':strategy,'contract':contract,'arm':cases[0]['arm'],'track':track,'obligation':obl['id'],'title':obl['title'],'applicationsInTrack':len(cases),'businessObservedInTrack':sum(r['businessObserved'] for r in cases),'applicationsWithPartialCheck':len({r['caseId'] for r,ch in linked}),'partialChecks':len(linked),'verdicts':dict(Counter(ch['verdict'] for r,ch in linked)),'claim':'partial_assertions_only' if linked else 'unchecked','wholeObligationValidated':False,'limits':obl.get('limits_and_review_notes')})
        for r in cases:
            for ch in r['checks']:
                for oid in ch['obligations']:
                    partition_checks.append({'lane':lane,'strategy':strategy,'contract':contract,'arm':r['arm'],'track':track,'caseId':r['caseId'],'obligation':oid,'partitionContext':r['partitions'],'semanticInputKey':r['semanticInputKey'],'inputAccepted':r['inputAccepted'],'businessObserved':r['businessObserved'],'effect':ch['name'],'authority':ch['authority'],'verdict':ch['verdict'],'failure':ch['failures'],'auditPath':r['auditPath'],'limit':r['limit']})
    present={(r['lane'],r['strategy'],r['contract'],r['obligation']) for r in obligations}
    for cell in catalog.get('obligationOperationMapping',[]):
        if cell['applicability']!='candidate_applicable_obligation_contract': continue
        for lane,strategy in [('official',s) for s in ['T1','T2','T3','T4']]+[('complementary','source-guided')]:
            if (lane,strategy,cell['contractId'],cell['obligationId']) not in present:
                obligations.append({'lane':lane,'strategy':strategy,'contract':cell['contractId'],'arm':cell['arm'],'track':cell['obligationTrack'],'obligation':cell['obligationId'],'applicationsInTrack':0,'businessObservedInTrack':0,'applicationsWithPartialCheck':0,'partialChecks':0,'verdicts':{},'claim':'not_executed','wholeObligationValidated':False,'limits':'No application for this track in the frozen suite; retained in denominator.'})
    return counts,obligations,partition_checks

def run(out,cycle):
    out.mkdir(parents=True,exist_ok=False); store=Store(out,cycle); rows=[]
    # Pin analysis code and plan too; old evidence and new implementation are separate.
    for file in Path(__file__).parent.glob('*.py'): store.read(file)
    store.read(Path(__file__).with_name('QUALITY.md'))
    catalog=json.loads(store.read(cycle/'P3/complementary-validation-v2/scenario-catalog.json'))
    for label,path in [('official','P3/official-campaign-large12k-run-v2/campaign-report.json'),('complementary','P3/complementary-matrix-v2/parent-full84-v1/campaign/campaign-report.json')]:
        report=json.loads(store.read(cycle/path)); n=0
        with (out/f'{label}-cases.jsonl').open('w') as progress:
            for suite in report['suiteReports']:
                freeze=json.loads(store.read(Path(suite['path']))); frozen={c['case_id']:c for c in freeze['cases']}
                if len(frozen)!=len(freeze['cases']): raise ValueError('duplicate_frozen_case')
                for ch in suite['checks']:
                    fc=frozen[ch['case_id']]
                    strategy=condition(suite['suite_id'],ch['contractId']) if label=='official' else 'source-guided'
                    if label=='official' and strategy not in ['T1','T2','T3','T4']: raise ValueError('unknown frozen provenance:'+strategy)
                    r=analyze(ch,fc,label,strategy,store); rows.append(r); progress.write(json.dumps(r,ensure_ascii=False)+'\n'); n+=1
                progress.flush(); print(label,suite['suite_id'],n,flush=True)
        assert n==report['totals']['attempted']
    counts,obls,partitions=summarize(rows,catalog); contrib=contributions(rows)
    write_csv(out/'applications.csv',rows); write_csv(out/'observability.csv',counts); write_csv(out/'obligation-coverage.csv',obls); write_csv(out/'obligation-partition-checks.csv',partitions); write_csv(out/'strategy-contribution.csv',contrib)
    changed=store.verify(); (out/'source-pins.json').write_bytes(canonical(list(store.pins.values())))
    summary={'applications':dict(Counter(r['lane'] for r in rows)),'byLane':{},'sourcePins':len(store.pins),'preservationFailures':changed,'counts':counts,'strategyContribution':contrib,'obligationCells':len(obls),'partialObligationCheckRows':len(partitions),'newBusinessApplications':0,'newBusinessScenarios':0,'retrospective':True,'independentOracle':False}
    for lane in ['official','complementary']:
        rr=[r for r in rows if r['lane']==lane]; cc=[c for r in rr for c in r['checks']]
        summary['byLane'][lane]={'businessObserved':sum(r['businessObserved'] for r in rr),'withChecks':sum(bool(r['checks']) for r in rr),'semanticStatesAcrossContracts':len({(r['track'],r['semanticInputKey']) for r in rr if r['semanticInputKey']}),'checkVerdicts':dict(Counter(c['verdict'] for c in cc)),'provenanceErrors':sum(bool(r['provenanceErrors']) for r in rr),'collectorErrors':dict(Counter(s for r in rr for s in r['limit'] if s.startswith('collector_error')))}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['counts','strategyContribution']},ensure_ascii=False),flush=True)
    return summary

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); args=ap.parse_args()
    run(args.out.resolve(),Path(__file__).resolve().parents[2])

#!/usr/bin/env python3
import json, sys, hashlib
from pathlib import Path
OPS={"and","or","not","eq","ne","gte","lte","status_is","exists","changed","first_record","unknown"}
TYPES={"bool","status","enum","amount","string","date_text","count","nat"}
def load(p):
    with open(p, encoding='utf-8') as f: return json.load(f)
def err(errors,msg): errors.append(msg)
def check_guard(g, variables, errors, where):
    if not isinstance(g, dict): return err(errors, f'{where}: guard not object')
    op=g.get('op')
    if op not in OPS: err(errors, f'{where}: invalid op {op}')
    if 'var' in g and g['var'] not in variables: err(errors, f'{where}: unknown var {g["var"]}')
    if op in {'and','or'}:
        args=g.get('args')
        if not isinstance(args,list) or not args: err(errors, f'{where}: {op} requires nonempty args')
        for i,a in enumerate(args or []): check_guard(a, variables, errors, f'{where}.{op}[{i}]')
    elif op=='not':
        args=g.get('args')
        if not isinstance(args,list) or len(args)!=1: err(errors, f'{where}: not requires one arg')
        elif isinstance(args[0],dict) and 'op' in args[0]: check_guard(args[0], variables, errors, f'{where}.not')
    elif op in {'eq','ne','gte','lte'}:
        args=g.get('args')
        if not isinstance(args,list) or len(args)!=2: err(errors, f'{where}: {op} requires two args')
        else:
            for a in args:
                if isinstance(a,dict) and 'var' in a and a['var'] not in variables: err(errors, f'{where}: unknown var {a["var"]}')
                if isinstance(a,dict) and 'op' in a: check_guard(a, variables, errors, where+'.nested')
    elif op=='status_is':
        v=g.get('var')
        if v not in variables: err(errors, f'{where}: unknown status var {v}')
        elif variables[v].get('type')!='status': err(errors, f'{where}: {v} not status')
        elif g.get('value') not in variables[v].get('domain',[]): err(errors, f'{where}: value {g.get("value")} not in domain for {v}')
    elif op=='unknown':
        if not g.get('reason'): err(errors, f'{where}: unknown guard requires reason')
def main(root):
    root=Path(root).resolve()
    errors=[]
    model=load(root/'model.json'); obligations=load(root/'obligations.json'); matrix=load(root/'resolution-matrix.json')
    obl_ids={o['id'] for o in obligations.get('obligations',[])}
    if len(obl_ids)!=len(obligations.get('obligations',[])): err(errors,'duplicate obligation ids')
    if obligations.get('status')!='draft_needs_independent_review': err(errors,'obligations status must remain draft_needs_independent_review')
    if model.get('status')!='draft_needs_independent_review': err(errors,'model status must remain draft_needs_independent_review')
    caps=model.get('capabilities',[])
    if len(caps)!=3: err(errors,'expected 3 capabilities')
    state_count=trans_count=0
    for cap in caps:
        cid=cap.get('id','?')
        states={s['id'] for s in cap.get('states',[])}
        state_count += len(states); trans_count += len(cap.get('transitions',[]))
        if cap.get('initialState') not in states: err(errors,f'{cid}: missing initial state')
        terms=set(sum([v for v in cap.get('terminalStates',{}).values()], []))
        if not terms <= states: err(errors,f'{cid}: terminal state not declared')
        variables=cap.get('variables',{})
        for vn,vd in variables.items():
            if vd.get('type') not in TYPES: err(errors,f'{cid}: bad variable type {vn}')
            if 'domain' not in vd: err(errors,f'{cid}: variable without domain {vn}')
        tids=[]
        for t in cap.get('transitions',[]):
            tids.append(t.get('id'))
            if t.get('from') not in states or t.get('to') not in states: err(errors,f'{cid}/{t.get("id")}: bad from/to')
            check_guard(t.get('guard'), variables, errors, f'{cid}/{t.get("id")}')
            if not t.get('effects'): err(errors,f'{cid}/{t.get("id")}: missing effects')
            if not t.get('observables'): err(errors,f'{cid}/{t.get("id")}: missing observables')
            if not t.get('sourceAnchors'): err(errors,f'{cid}/{t.get("id")}: missing anchors')
            for ref in t.get('obligationRefs',[]):
                if ref not in obl_ids: err(errors,f'{cid}/{t.get("id")}: unknown obligation {ref}')
        if len(tids)!=len(set(tids)): err(errors,f'{cid}: duplicate transition ids')
        # reachability
        reachable={cap.get('initialState')}; changed=True
        while changed:
            changed=False
            for t in cap.get('transitions',[]):
                if t.get('from') in reachable and t.get('to') not in reachable:
                    reachable.add(t.get('to')); changed=True
        if states - reachable: err(errors,f'{cid}: unreachable states {sorted(states-reachable)}')
        if not any(t.get('terminal')=='unknown' or t.get('to') in cap.get('terminalStates',{}).get('unknown',[]) for t in cap.get('transitions',[])) and cid=='CBTRN03C_TRANREPT': err(errors,'TRANREPT must preserve unknown EOF receiver branch')
    # matrix
    ids=[f.get('id') for f in matrix.get('findings',[])]
    if ids != [f'FAIL-{i:02d}' for i in range(1,7)]: err(errors,'resolution matrix must cover FAIL-01..06 in order')
    if not all(f.get('decision')=='resolved_in_v2_draft' for f in matrix.get('findings',[])): err(errors,'all findings must be resolved in v2 draft')
    # source anchor hash/line validation against manifest
    inp=root.parent/'reference-authoring-input-v1'; manifest=load(inp/'input-manifest.json')
    sha_by={f['path']:f['sha256'] for f in manifest['files']}
    def validate_anchor(a, where):
        p=a.get('path')
        if p=='model.json': return
        if p not in sha_by: return err(errors,f'{where}: anchor file not in manifest {p}')
        data=(inp/'corpus'/p).read_bytes()
        if hashlib.sha256(data).hexdigest()!=a.get('sha256'): err(errors,f'{where}: bad sha {p}')
        total=len(data.decode('utf-8',errors='replace').splitlines())
        lines=a.get('lines')
        if not (isinstance(lines,list) and len(lines)==2 and 1<=lines[0]<=lines[1]<=total): err(errors,f'{where}: bad line range {p}:{lines}')
    for o in obligations.get('obligations',[]):
        for a in o.get('source_anchors',[]): validate_anchor(a, o['id'])
    for cap in caps:
        for t in cap.get('transitions',[]):
            for a in t.get('sourceAnchors',[]): validate_anchor(a, t['id'])
    for f in matrix.get('findings',[]):
        for a in f.get('sourceAnchors',[]): validate_anchor(a, f['id'])
    report={'status':'FAIL' if errors else 'PASS','errors':errors,'counts':{'capabilities':len(caps),'states':state_count,'transitions':trans_count,'obligations':len(obl_ids),'blocking_findings_resolved':sum(1 for f in matrix.get('findings',[]) if f.get('decision')=='resolved_in_v2_draft')}}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if errors else 0
if __name__=='__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv)>1 else '.'))

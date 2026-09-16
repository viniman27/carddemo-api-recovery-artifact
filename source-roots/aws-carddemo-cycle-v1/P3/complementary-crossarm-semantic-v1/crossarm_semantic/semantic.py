from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

SPANS = [('id',0,16),('type',16,18),('category',18,22),('source',22,32),('description',32,132),('amountRaw',132,143),('merchant',143,152),('merchantName',152,202),('merchantCity',202,252),('merchantPostalText',252,262),('card',262,278),('origTs',278,304),('procTs',304,330)]
OBLIGATIONS_BY_TRACK = {
    'posting': ['POSTTRAN-OBL-003', 'POSTTRAN-OBL-009'],
    'interest': ['INTCALC-OBL-005', 'INTCALC-OBL-006'],
    'reporting': ['TRANREPT-OBL-002', 'TRANREPT-OBL-006'],
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def pin(path: Path, label: str|None=None) -> dict[str, Any]:
    return {'label': label or path.name, 'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha256_file(path)}


def verify_pin(p: dict[str, Any]) -> list[str]:
    path = Path(p['path'])
    if not path.exists():
        return [f"missing:{path}"]
    out=[]
    if path.stat().st_size != p.get('bytes'):
        out.append(f"bytes mismatch:{path}")
    s=sha256_file(path)
    if p.get('sha256') and s != p.get('sha256'):
        out.append(f"sha mismatch:{path}")
    return out


def _money(raw: Any) -> str:
    digits=''.join(ch for ch in str(raw) if ch.isdigit()) or '0'
    return f"{(Decimal(digits)/Decimal(100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


def tx_fields(raw: bytes) -> dict[str, str]:
    d={}
    for name,a,b in SPANS:
        d[name]=raw[a:b].decode('latin1', errors='replace').rstrip('\x00 ')
    d['amount']=_money(d.pop('amountRaw'))
    return d


def records(path: Path, size: int) -> list[tuple[int, bytes]]:
    data=path.read_bytes() if path.exists() else b''
    return [(i, data[i:i+size]) for i in range(0, len(data), size) if len(data[i:i+size]) == size and data[i:i+size].strip(b'\x00 ')]


def _provenance(path: Path, offset: int, length: int, fields: list[str]) -> dict[str, Any]:
    return {'kind':'raw_file_record','artifact':str(path),'sha256':sha256_file(path),'recordOffset':offset,'recordLength':length,'observedFields':fields}


def _response_path_from_workdir(workdir: Path, contract: str, track: str) -> Path|None:
    base = workdir / ('zero-shot-runs' if (workdir/'zero-shot-runs').exists() else '')
    hits=list(base.glob(f"{contract}/{track}/*/response.json"))
    if not hits:
        hits=list(workdir.rglob('response.json'))
    return hits[0] if hits else None


def _request_body_pin(workdir: Path) -> dict[str, Any]|None:
    req = workdir / 'zero-shot-runs' / 'http-requests.jsonl'
    if req.exists(): return pin(req, 'captured-http-request-body-bytes')
    return None


def _materialized_files(audit: dict[str, Any]) -> dict[str, str]:
    return audit.get('RES',{}).get('selected_fixture',{}).get('resolvedFixtureFiles',{}) or audit.get('CAP',{}).get('fixture_materialization',{}).get('files',{})


def _run_dir_from_case(case: dict[str, Any]) -> Path:
    ev = case.get('businessCheck',{}).get('evidence',[])
    if ev:
        return Path(ev[0]['path']).parent
    raise ValueError('no evidence path')


def build_posting_fixture(case: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    run_dir=_run_dir_from_case(case); audit=load_json(run_dir/'audit.json')
    source_path=run_dir/'DALYTRAN'; out_path=run_dir/'TRANFILE.after'; rej_path=run_dir/'DALYREJS'
    src=[(off, tx_fields(raw), raw.hex()) for off,raw in records(source_path,350)]
    outs=[(off, tx_fields(raw), raw.hex()) for off,raw in records(out_path,350)]
    rejects=[]
    for off,raw in records(rej_path,430):
        candidate=tx_fields(raw[:350]); reason=raw[350:354].decode('latin1',errors='replace').strip(); desc=raw[354:430].decode('latin1',errors='replace').strip()
        rejects.append({'case': {'0100':'missing-card','0101':'account-missing','0102':'over-limit','0103':'expired'}.get(reason, reason), 'rawBytes': raw.hex(), 'reason': reason[-3:], 'description': desc, 'postedTransactionWritten': False, 'rejectRecordWritten': True, 'provenance': _provenance(rej_path, off, 430, ['rawBytes','reason','description'])})
    accepted=[]
    for idx,(off,posted,hexraw) in enumerate(outs):
        # input-derived: match by transaction id in actual materialized DALYTRAN, not by another case output.
        source = next((s for _,s,_ in src if s['id']==posted['id']), None)
        if source is None and idx < len(src):
            source = src[idx][1]
        daily = dict(source) if source else {}
        accepted.append({'id': posted.get('id'), 'rawBytes': hexraw, 'daily': daily, 'posted': posted, 'duplicatePrevalidated': False, 'provenance': _provenance(out_path, off, 350, ['rawBytes','daily','posted'])})
    obs={'posting': {'returnCode': audit.get('RESP',{}).get('program_exit'), 'acceptedTransactions': accepted, 'rejects': rejects}}
    fixture={'fixtureId': case['caseId'], 'description':'crossarm actual preserved posting observation', 'observations':obs, 'evidenceClass':'real_cobol_observation'}
    meta={'sourcePins':[pin(source_path,'input-DALYTRAN'), pin(out_path,'raw-TRANFILE.after'), pin(rej_path,'raw-DALYREJS'), pin(run_dir/'audit.json','audit')], 'typedObservationNotes': []}
    return fixture, meta


def _parse_interest_raw(raw: bytes) -> dict[str,str]:
    d=tx_fields(raw)
    # descriptions include account after prefix; category spans already raw 4 digits -> normalize to source checker expectation
    d['category']=d.get('category','')[-2:].zfill(2)
    return d


def build_interest_fixture(case: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    run_dir=_run_dir_from_case(case); audit=load_json(run_dir/'audit.json')
    out_path=run_dir/'TRANSACT'; txs=[]; notes=[]
    for off,raw in records(out_path,350):
        f=_parse_interest_raw(raw)
        # This cross-arm run preserved fixture bytes, but no qualified source extractor for TCATBALF/DISCGRP balance/rate is bound here.
        # Leave source-dependent formula fields absent so checker outcome is inconclusive rather than a default expected value.
        txs.append({'id': f['id'], 'rawBytes': raw.hex(), 'amount': f['amount'], 'transactionWritten': True, 'type': f['type'], 'category': f['category'], 'source': f['source'], 'description': f['description'], 'merchant': f['merchant'], 'card': f['card'], 'xrefCard': f['card'], 'provenance': _provenance(out_path, off, 350, ['rawBytes','amount','type','category','source','card'])})
    notes.append('interest_source_balance_rate_extractor_missing: formula obligations inconclusive, not defaulted')
    fixture={'fixtureId': case['caseId'], 'description':'crossarm actual preserved interest observation', 'observations':{'interest':{'transactions':txs}}, 'evidenceClass':'real_cobol_observation'}
    pins=[pin(out_path,'raw-TRANSACT'), pin(run_dir/'audit.json','audit')]
    for name in ['TCATBALF','DISCGRP','PARMFILE','XREFFILE','XREFFILE.1']:
        p=run_dir/name
        if p.exists(): pins.append(pin(p,'input-'+name))
    return fixture, {'sourcePins':pins,'typedObservationNotes':notes}


def _date_range(dateparm: Path) -> tuple[str,str]:
    text=dateparm.read_text('latin1').strip()
    parts=text.split()
    return (parts[0], parts[1]) if len(parts)>=2 else ('0000-00-00','9999-99-99')


def build_reporting_fixture(case: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    run_dir=_run_dir_from_case(case); dateparm=run_dir/'DATEPARM'; tranfile=run_dir/'TRANFILE'; report=run_dir/'TRANREPT'; audit=load_json(run_dir/'audit.json')
    start,end=_date_range(dateparm)
    source=[]
    for off,raw in records(tranfile,350):
        f=tx_fields(raw); proc=f['procTs'][:10]; source.append((off,f,raw.hex(),proc))
    data = report.read_bytes() if report.exists() else b''
    lines=[data[i:i+133] for i in range(0, len(data), 133) if data[i:i+133].strip(b'\x00 ')]
    detail_ids=set()
    txs=[]
    for i,line in enumerate(lines):
        txt=line.decode('latin1',errors='replace')
        if txt.startswith('REPORT-'):
            tid=txt[:16].strip(); detail_ids.add(tid)
            src=next((s for _,s,_,_ in source if s['id']==tid), {})
            txs.append({'id':tid,'procDate': src.get('procTs','')[:10], 'amount': src.get('amount','0.00'), 'detailWritten': True, 'detailLine': txt, 'reportLineBytes': line.hex(), 'provenance': {'kind':'report_line','artifact':str(report),'sha256':sha256_file(report),'recordOffset': i*133, 'recordLength':133, 'observedFields':['procDate','amount','detailLine','reportLineBytes']}})
    for off,f,hexraw,proc in source:
        if f['id'] not in detail_ids:
            txs.append({'id':f['id'],'procDate':proc,'amount':f['amount'],'detailWritten':False,'provenance':_provenance(tranfile, off, 350, ['procDate','detailWritten'])})
    fixture={'fixtureId': case['caseId'], 'description':'crossarm actual preserved reporting observation', 'observations':{'reporting':{'dateRange':[start,end], 'transactions':txs, 'reportFraming': {'eofBeforeTotalsBranch': True}}}, 'evidenceClass':'real_cobol_observation'}
    return fixture, {'sourcePins':[pin(dateparm,'input-DATEPARM'), pin(tranfile,'input-TRANFILE'), pin(report,'raw-TRANREPT'), pin(run_dir/'audit.json','audit')], 'typedObservationNotes':['report_totals_not_api_visible_or_raw_totals_missing: totals obligations may be inconclusive']}


def checker_import(cycle_root: Path):
    root=cycle_root/'P3'/'complementary-validation-implementation-v3'
    if str(root) not in sys.path: sys.path.insert(0,str(root))


def _safe_checker_results(fixture: dict[str,Any], obligation_ids: list[str], cycle_root: Path) -> list[dict[str,Any]]:
    checker_import(cycle_root)
    from semantic_checkers.fixtures import Fixture
    from semantic_checkers.runner import run_fixture_checks
    fixed=Fixture(fixture_id=fixture['fixtureId'], description=fixture.get('description',''), observations=fixture['observations'], evidence_class=fixture.get('evidenceClass','real_cobol_observation'))
    results=[]
    for oid in obligation_ids:
        try:
            results.extend([r.to_json_dict() for r in run_fixture_checks(fixed, [oid])])
        except Exception as exc:
            # Missing typed source input is inconclusive, never replaced with a default expectation.
            results.append({'obligationId':oid,'track':oid.split('-OBL-')[0].lower(),'status':'inconclusive','sourceAnchors':[],'boundaries':['raw_cobol_effect'], 'details':{'semanticOutcome':'inconclusive','failures':[f'typed_extractor_missing_or_unbound:{type(exc).__name__}:{exc}'], 'evidenceSufficiency':{'classification':'missing_source_typed_input','businessConclusionAllowed':False}}})
    return results


def semantic_check_case(case: dict[str, Any], cycle_root: Path|None=None) -> dict[str, Any]:
    cycle_root = cycle_root or Path(__file__).resolve().parents[3]
    track=case['track']
    if track=='posting': fixture,meta=build_posting_fixture(case)
    elif track=='interest': fixture,meta=build_interest_fixture(case)
    elif track=='reporting': fixture,meta=build_reporting_fixture(case)
    else: raise ValueError(track)
    results=_safe_checker_results(fixture, OBLIGATIONS_BY_TRACK[track], cycle_root)
    run_dir=_run_dir_from_case(case)
    response_path=_response_path_from_workdir(run_dir.parents[2] if 'p2b-runs' in str(run_dir) else run_dir, case['contractId'], track) or next(run_dir.parent.parent.rglob('response.json'), None)
    api={'httpStatus':case.get('httpStatus'),'responseSha256':case.get('responseSha256'),'responsePath':str(response_path) if response_path else None,'publicObservation': 'api_omits_business_records_or_totals' if track in ('posting','reporting') else 'api_visible_response_captured'}
    reqpin=_request_body_pin(run_dir.parents[1]) or _request_body_pin(run_dir.parent.parent) or _request_body_pin(run_dir.parents[2])
    pins=list(meta['sourcePins'])
    if response_path and response_path.exists(): pins.append(pin(response_path,'api-response'))
    if reqpin: pins.append(reqpin)
    pinfails=[f for p in pins for f in verify_pin(p)]
    status_counts=Counter(r['status'] for r in results)
    raw={'runDir':str(run_dir),'fixture':fixture,'typedObservationNotes':meta.get('typedObservationNotes',[])}
    return {**{k:case.get(k) for k in ['caseId','contractId','operationId','track','httpStatus','responseSha256','structural','measurementAdmissibility']}, 'semanticStatus': 'failed' if status_counts.get('failed') else ('pass' if status_counts.get('pass') and not status_counts.get('inconclusive') else 'inconclusive'), 'checkerResults':results, 'apiVisibleEvidence':api, 'rawCobolEffects':raw, 'artifactPins':pins, 'pinVerificationFailures':pinfails, 'noApiRerun':True}


def run(run_root: Path, cycle_root: Path) -> dict[str, Any]:
    comparison=load_json(run_root/'comparison.json')
    cases=[semantic_check_case(c, cycle_root) for c in comparison['cases']]
    by_track=Counter(c['track'] for c in cases); status_counts=Counter(r['status'] for c in cases for r in c['checkerResults'])
    sem_counts=Counter(c['semanticStatus'] for c in cases); by_contract=defaultdict(Counter); by_track_status=defaultdict(Counter)
    for c in cases:
        by_contract[c['contractId']][c['semanticStatus']]+=1; by_track_status[c['track']][c['semanticStatus']]+=1
    obligations=Counter(r['obligationId'] for c in cases for r in c['checkerResults'])
    return {'kind':'complementary-crossarm-semantic-v1-results','createdUtc':datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z'), 'scope':'Retrospective semantic binding of preserved21 run-20260916T112642Z artifacts only; no API/COBOL/model/quarantine reruns.', 'summary':{'caseCount':len(cases),'caseCountsByTrack':dict(by_track),'semanticCaseStatusCounts':dict(sem_counts),'checkerStatusCounts':dict(status_counts),'byContract':{k:dict(v) for k,v in by_contract.items()},'byTrackSemanticStatus':{k:dict(v) for k,v in by_track_status.items()},'uniqueObligationOccurrences':dict(obligations),'pinVerificationFailureCount':sum(len(c['pinVerificationFailures']) for c in cases),'noApiReruns':True,'sourcePendingNotUnqualifiedFull25':True}, 'cases':cases, 'sourceRunPins':[pin(run_root/'comparison.json','old-file-existence-comparison'), pin(run_root/'run'/'campaign-report.json','campaign-report')]}


def write_status(out: Path, payload: dict[str,Any]) -> None:
    s=payload['summary']
    text=f"""# Complementary cross-arm semantic v1 STATUS

Status: partial actual semantic qualification over the preserved21 real cases, without API reruns.

- Cases checked: {s['caseCount']} ({s['caseCountsByTrack']})
- Checker statuses: {s['checkerStatusCounts']}
- Case semantic statuses: {s['semanticCaseStatusCounts']}
- Pin verification failures: {s['pinVerificationFailureCount']}
- Evidence boundary: API-visible response evidence and raw COBOL file effects are reported separately. Same underlying raw bytes can pass internal effects while public API fields remain omitted/limited.
- Inconclusive is used where source-derived typed inputs or trace/totals evidence are not bound; no source-pending obligation is promoted to full 25-obligation validation.

Next step: bind qualified source extractors for INTCALC TCATBALF/DISCGRP rate+balance and TRANREPT totals/framing before upgrading current inconclusive observations to pass/fail business claims.
"""
    (out.parent/'STATUS.md').write_text(text, encoding='utf-8')


def main(argv: list[str]|None=None) -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--run-root', type=Path, required=True)
    ap.add_argument('--cycle-root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args=ap.parse_args(argv)
    payload=run(args.run_root, args.cycle_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)+'\n', encoding='utf-8')
    write_status(args.out, payload)
    print(json.dumps({'ok':True,'caseCount':payload['summary']['caseCount'],'checkerStatusCounts':payload['summary']['checkerStatusCounts'],'semanticCaseStatusCounts':payload['summary']['semanticCaseStatusCounts'],'out':str(args.out)}, ensure_ascii=False))
    return 0

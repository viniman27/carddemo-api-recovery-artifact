"""Read-only saved-evidence collector. Only indexed readers execute, on copies."""
import base64, hashlib, json, os, shutil, subprocess, importlib.util
from pathlib import Path
import evidence as e

LAYOUTS={'ACCTFILE':(300,11),'TCATBALF':(50,17),'XREFFILE':(50,16),'CARDXREF':(50,16),'DISCGRP':(50,16),'TRANTYPE':(60,2),'TRANCATG':(60,6),'TRANFILE':(350,16)}
INPUTS={'posting':['DALYTRAN','ACCTFILE','TCATBALF','XREFFILE'], 'interest':['TCATBALF','ACCTFILE','DISCGRP','XREFFILE','PARMFILE'], 'reporting':['TRANFILE','DATEPARM','CARDXREF','TRANTYPE','TRANCATG']}

def digest(data): return hashlib.sha256(data).hexdigest()
def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def request_key(req):
    raw=base64.b64decode(req.get('body_b64') or '',validate=True)
    try: body=json.loads(raw)
    except (ValueError,UnicodeError): body={'rawHex':raw.hex()}
    return digest(canonical({'body_kind':req.get('body_kind'),'body':body,'method':req.get('method'),'path':req.get('path')}))

def semantic_inputs(inp):
    spans={'ACCTFILE':122,'TCATBALF':28,'XREFFILE':36,'CARDXREF':36,'DISCGRP':22,'TRANTYPE':52,'TRANCATG':56}
    out={}
    for dd,value in inp.items():
        if isinstance(value,list): out[dd]=[r[:spans.get(dd,len(r))].hex() for r in value]
        elif dd in ['DALYTRAN','TRANFILE']: out[dd]=[r[:330].hex() for r in records(value,350)]
        elif dd=='DATEPARM': out[dd]=value[:21].hex()
        else: out[dd]=value.hex()
    return out

def records(raw,size):
    if len(raw)%size: raise ValueError('partial_input_record')
    return [raw[i:i+size] for i in range(0,len(raw),size)]

class Store:
    def __init__(self,out,cycle=None):
        self.out=Path(out); self.out.mkdir(parents=True,exist_ok=True); self.cycle=cycle
        self.pins={}; self.dumps={}; self.template=None
    def read(self,path):
        path=Path(path); data=path.read_bytes(); pin={'path':str(path),'bytes':len(data),'sha256':digest(data)}
        old=self.pins.get(str(path))
        if old and old!=pin: raise ValueError('input_changed_during_analysis:'+str(path))
        self.pins[str(path)]=pin
        return data
    def before(self,rd,audit,dd):
        state=audit['STATE']; snap=state.get('pre_cobol_request_materialized') or state.get('pre_cobol_materialization') or {}
        pin=next((x for x in snap.get('files',[]) if x['path']==dd),None)
        if pin is None: raise ValueError('missing_pre_cobol_pin:'+dd)
        material=audit.get('CAP',{}).get('fixture_materialization',{}).get('files',{}).get(dd,{})
        resolved=audit.get('RES',{}).get('selected_fixture',{}).get('resolvedFixtureFiles',{})
        candidates=[rd/dd]
        for value in [material.get('sourcePath'),resolved.get(dd)]:
            if value: candidates.append(Path(value))
        for p in candidates:
            if p.is_file():
                raw=p.read_bytes()
                if len(raw)==pin['bytes'] and digest(raw)==pin['sha256']:
                    self.read(p); return p
        raise ValueError('pre_state_unrecoverable:'+dd)
    def dump(self,path,size,key):
        raw=self.read(path); cachekey=(digest(raw),size,key)
        if cachekey in self.dumps: return self.dumps[cachekey]
        work=self.out/'indexed-copies'/f'{cachekey[0]}-{size}-{key}'; work.mkdir(parents=True,exist_ok=True)
        if self.template is None:
            src=self.cycle/'P3/complementary-interest-source-extractor-v1/interest_source_extractor/extractor.py'
            self.read(src); spec=importlib.util.spec_from_file_location('qualified_reader',src); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); self.template=mod.RAWIO_TEMPLATE
        tools=self.out/'readers'; tools.mkdir(exist_ok=True)
        exe=tools/f'rawio-{size}-{key}'
        if not exe.exists():
            src=exe.with_suffix('.cbl'); src.write_text(self.template.format(size=size,key=key,rest=size-key))
            p=subprocess.run(['cobc','-x','-free','-o',str(exe),str(src)],capture_output=True,timeout=120)
            (exe.with_suffix('.compile.log')).write_bytes(p.stdout+p.stderr)
            if p.returncode: raise ValueError('reader_compile_failure')
        idx=work/'IDX'; idx.write_bytes(raw); output=work/'dump.raw'
        env=dict(os.environ); env.update(IO_MODE='DUMP',DD_RAW=str(output),DD_IDX=str(idx))
        result=subprocess.run([str(exe)],cwd=work,env=env,capture_output=True,timeout=30)
        (work/'reader.log').write_bytes(result.stdout+result.stderr)
        if result.returncode: raise ValueError('reader_failed:'+result.stderr.decode(errors='replace'))
        data=output.read_bytes(); recs=records(data,size)
        keys=[r[:key] for r in recs]
        if keys!=sorted(set(keys)): raise ValueError('indexed_reader_keys_not_unique_sorted')
        self.dumps[cachekey]=recs
        return recs
    def verify(self):
        return [p for p in self.pins.values() if not Path(p['path']).is_file() or digest(Path(p['path']).read_bytes())!=p['sha256']]


def analyze(ch,fc,lane,strategy,store):
    contract=ch['contractId']; track=ch['track']; receipt=ch['receipt']; params=fc.get('parameters',{})
    row={'caseId':ch['case_id'],'contract':contract,'arm':params.get('contractArm') or ('zero-shot' if contract.startswith('E1-') else 'few-shot' if contract.startswith('E2-') else 'SDD'),'track':track,'lane':lane,'strategy':strategy,'originalOrigin':fc.get('origin'),'originalProvenance':fc.get('provenance',[]),'scenario':params.get('essentialScenarioId'),'status':receipt['status'],'requestKey':request_key(fc['request']),'businessObserved':False,'inputAccepted':'unknown','semanticInputKey':None,'partitions':[],'checks':[],'provenanceErrors':[],'limit':[],'auditPath':None,'responseSha256':receipt['response_sha256']}
    try:
        body=base64.b64decode(receipt.get('response_body_b64',''),validate=True)
        if digest(body)!=receipt['response_sha256'] or len(body)!=receipt['response_bytes']: row['provenanceErrors'].append('response_pin_mismatch')
        try: row['responseSummary']=json.loads(body)
        except (ValueError,UnicodeError): row['responseSummary']={'rawHex':body.hex()}
        # Do not export full potentially large bodies to main table; response pin remains.
        if len(canonical(row['responseSummary']))>1000: row['responseSummary']={'keys':list(row['responseSummary']) if isinstance(row['responseSummary'],dict) else 'array','bytes':len(body)}
        rd=Path(ch['measurement']['runDir']); ap=rd/'audit.json'
        if not ap.exists():
            row['limit'].append('no_invocation_linked_audit; not proof of zero COBOL execution')
            row['inputAccepted']='rejected_at_boundary' if receipt['status'] in [400,503] else 'unknown'
            return row
        app=Path(ch['application']['workdir'])
        try: historical=ch['application'].get('pins_after',{}).get(str(ap.relative_to(app)))
        except ValueError: historical=None
        audit=json.loads(store.read(ap)); row['auditPath']=str(ap)
        if historical:
            if historical['sha256']!=digest(ap.read_bytes()): row['provenanceErrors'].append('audit_not_matching_application_pin')
        else:
            m=ch['measurement']; linked=(m.get('auditSelection',{}).get('auditPath')==str(ap) and m.get('requestInvocation')==rd.name and audit['INV'].get('workdir')==str(rd) and audit['INV'].get('track')==track and any(x.get('cwd')==str(rd) for x in m.get('businessCommandEnvEvidence',[])))
            if not linked: row['provenanceErrors'].append('external_audit_not_invocation_linked')
            row['limit'].append('external audit linked by frozen report path/invocation/cwd; audit hash not historically pinned in application tree')
        row['businessObserved']=bool(audit.get('RESP',{}).get('reached_cobol'))
        row['inputAccepted']='accepted_to_invocation' if row['businessObserved'] else 'unknown'
        row['programExit']=audit.get('RESP',{}).get('program_exit')
        if not row['businessObserved'] or row['provenanceErrors']: return row
        inp={}; paths={}
        for dd in INPUTS[track]:
            p=store.before(rd,audit,dd); paths[dd]=str(p)
            inp[dd]=store.dump(p,*LAYOUTS[dd]) if dd in LAYOUTS and not (dd=='TRANFILE' and track=='reporting') else store.read(p)
        semantic=semantic_inputs(inp)
        row['semanticInputKey']=digest(canonical({'track':track,'inputs':semantic})); row['inputPaths']=paths
        row['inputRecordCounts']={dd:len(value) for dd,value in inp.items() if isinstance(value,list)}
        # Every output used must have a historical per-application pin.
        def output(dd,indexed=False):
            p=rd/dd
            if not p.exists(): return None
            data=store.read(p)
            try: hp=ch['application']['pins_after'].get(str(p.relative_to(app)))
            except ValueError: hp=None
            if hp is None:
                hp=next((x for x in audit.get('STATE',{}).get('after',{}).get('files',[]) if x['path']==dd),None)
            if not hp or hp['sha256']!=digest(data) or hp.get('size',hp.get('bytes'))!=len(data): raise ValueError('output_pin_mismatch:'+dd)
            return b''.join(store.dump(p,*LAYOUTS[dd])) if indexed else data
        def check(name,obligations,result,authority='source-derived'):
            row['checks'].append({'name':name,'obligations':obligations,'authority':authority,**result})
        if row['programExit'] not in [0,4]:
            key=e.first_missing_xref(records(inp['TRANFILE'],350),inp['DATEPARM'],inp['CARDXREF']) if track=='reporting' else None
            if key:
                stdout=audit.get('CAP',{}).get('program_stdout',''); stderr=audit.get('CAP',{}).get('program_stderr','')
                observed=[row['programExit']==12,'INVALID CARD NUMBER : '+key in stdout,'NNNN0023' in stdout,'ABENDING PROGRAM' in stdout,'LOCAL-CEE3ABD/2' in stderr]
                row['partitions']=['first_selected_card_missing']
                check('missing_first_xref_abort',['TRANREPT-OBL-004','TRANREPT-OBL-008'],e.compare_events(observed,[True]*5),'source_precondition_and_local_abort_bridge')
                check('no_report_before_first_lookup_abort',['TRANREPT-OBL-006'],e.compare_records(output('TRANREPT'),b'',133))
                row['limit'].append('First selected CARDXREF absence only; not general I/O failure qualification; exit 12 is local compatibility behavior')
            else: row['limit'].append('abnormal_exit_no_success_path_oracle')
            return row
        if track=='posting':
            model=e.posting_expected(records(inp['DALYTRAN'],350),inp['ACCTFILE'],inp['TCATBALF'],inp['XREFFILE'])
            row['partitions']=model['partitions']; row['sourceOutcomes']=model['reasons']
            check('posted_fields_multiplicity',['POSTTRAN-OBL-003','POSTTRAN-OBL-009'],e.compare_records(e.stable_posting_transactions(output('TRANFILE.after')),b''.join(model['accepted']),350))
            check('reject_bytes_reason_multiplicity',['POSTTRAN-OBL-004','POSTTRAN-OBL-005','POSTTRAN-OBL-006'],e.compare_records(output('DALYREJS'),b''.join(model['rejected']),430))
            check('account_all_fields_after',['POSTTRAN-OBL-008'],e.compare_records(output('ACCTFILE.after'),b''.join(model['accounts']),300))
            check('category_all_fields_after',['POSTTRAN-OBL-007'],e.compare_records(e.stable_categories(output('TCATBALF.after')),e.stable_categories(b''.join(model['categories'])),50))
            check('xref_unchanged',['POSTTRAN-OBL-004'],e.compare_records(output('XREFFILE.after'),b''.join(inp['XREFFILE']),50))
            check('return_code',['POSTTRAN-OBL-006'],e.compare_events([row['programExit']],[4 if any(model['reasons']) else 0]))
            row['limit']+=['No internal effect-order or I/O-failure assertion','ASCII signed DISPLAY qualified; overflow unqualified; processing timestamp/filler excluded; TCATBAL filler 28:50 excluded','TRANFILE OPEN OUTPUT: preexisting contents are not expected to survive']
        elif track=='interest':
            model=e.interest_expected(inp['ACCTFILE'],inp['TCATBALF'],inp['DISCGRP'],inp['XREFFILE'],inp['PARMFILE'])
            row['partitions']=sorted(set(model['branches']+['single_account' if len(model['groups'])==1 else 'multiple_accounts','final_account_eof']))
            check('interest_stable_fields_order',['INTCALC-OBL-003','INTCALC-OBL-004','INTCALC-OBL-005','INTCALC-OBL-006'],e.compare_records(e.stable_interest_transactions(output('TRANSACT')),e.stable_interest_transactions(b''.join(model['transactions'])),350))
            observed=output('ACCTFILE',indexed=True)
            check('accounts_legacy_all_fields',['INTCALC-OBL-007','INTCALC-OBL-008'],e.compare_records(observed,b''.join(model['legacyAccounts']),300))
            check('accounts_financial_all_groups',['INTCALC-OBL-007','INTCALC-OBL-008'],e.compare_records(observed,b''.join(model['financialAccounts']),300),'explicit_financial_expectation_not_legacy_equivalence')
            row['interestCentsByAccount']=model['totalInterestCents']; row['limit']+=model['limits']+['Unassigned description tail 56:132 excluded: source STRING assigns prefix only']
        else:
            model=e.report_expected(records(inp['TRANFILE'],350),inp['DATEPARM'],inp['CARDXREF'],inp['TRANTYPE'],inp['TRANCATG'])
            obs=e.parse_report(output('TRANREPT')); start,end=inp['DATEPARM'][:10],inp['DATEPARM'][11:21]
            dates=[t[304:314] for t in records(inp['TRANFILE'],350)] if inp['DATEPARM'] else []
            row['partitions']=sorted({('start' if d==start else 'end' if d==end else 'before' if d<start else 'after' if d>end else 'inside') for d in dates})
            if not inp['DATEPARM']: row['partitions'].append('dateparm_eof_before_transaction_loop')
            row['partitions']+=['selected_empty' if not model['selectedCount'] else 'selected_nonempty','eof_selected' if model['eofSelected'] else 'eof_not_selected']
            if sum(v[0]=='header' for v in model['legacy'])>1: row['partitions'].append('pagination')
            if any(v[0]=='account_total' for v in model['legacy']): row['partitions'].append('card_break')
            check('report_full_event_sequence_legacy',['TRANREPT-OBL-002','TRANREPT-OBL-003','TRANREPT-OBL-004','TRANREPT-OBL-005','TRANREPT-OBL-006','TRANREPT-OBL-007'],e.compare_events(obs,model['legacy']))
            check('report_details_all_fields',['TRANREPT-OBL-002','TRANREPT-OBL-004','TRANREPT-OBL-006'],e.compare_events(None if obs is None else [x for x in obs if x[0]=='detail'],[x for x in model['legacy'] if x[0]=='detail']))
            totals=lambda seq:[x for x in seq if x[0].endswith('_total')]
            financial=e.compare_events(None if obs is None else totals(obs),totals(model['financial']))
            if not totals(model['financial']) and obs is not None and not totals(obs): financial={'verdict':'not_exercised','failures':[]}
            check('report_all_subtotals_grand_financial',['TRANREPT-OBL-004','TRANREPT-OBL-007'],financial,'sum_of_selected_input_details_no_stale_EOF_addition')
            row['reportSelected']=model['selectedCount']; row['reportTotalsObserved']=None if obs is None else totals(obs)
            row['reportTotalsExpectedFinancial']=totals(model['financial']); row['limit']+=model['limits']
    except (ValueError,KeyError,FileNotFoundError,UnicodeError,subprocess.SubprocessError) as exc:
        row['limit'].append('collector_error:'+type(exc).__name__+':'+str(exc))
    return row

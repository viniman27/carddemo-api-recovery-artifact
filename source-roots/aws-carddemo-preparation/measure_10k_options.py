"""Measure candidate scopes only; no builds or legacy edits."""
import hashlib
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SRC=Path('<UPSTREAM_CHECKOUT>/aws-samples__aws-mainframe-modernization-carddemo/full-source/app')
BASE=['CBTRN02C','CBACT04C','CBTRN03C','CBSTM03A','CBSTM03B']
OPTIONS={'account-maintenance-batch':BASE+['COACTUPC'],
         'account-cycle':BASE+['COACTUPC','COACTVWC'],
         'account-cycle-payment':BASE+['COACTUPC','COACTVWC','COBIL00C'],
         'account-cycle-payment-transactions':BASE+['COACTUPC','COACTVWC','COBIL00C','COTRN00C','COTRN01C','COTRN02C']}

def body(p):
    return '\n'.join(line[7:72] for line in p.read_text().splitlines() if len(line)>6 and line[6] not in '*/')

def main():
    index={}
    for folder in ['cbl','cpy','cpy-bms']:
        for p in (SRC/folder).iterdir():
            if p.is_file():
                index.setdefault(p.stem.upper(),[]).append(p)
    output={}
    for option, names in OPTIONS.items():
        pending=[index[n][0] for n in names]
        seen=set(); missing=set(); calls=set(); transfers=set()
        while pending:
            p=pending.pop()
            if p in seen: continue
            seen.add(p); text=body(p)
            for cp in re.findall(r'\bCOPY\s+[\'\"]?([\w-]+)',text,re.I):
                matches=index.get(cp.upper(),[])
                if len(matches)==1: pending.extend(matches)
                else: missing.add(cp)
            for call in re.findall(r'\bCALL\s+[\'\"]([^\'\"]+)',text,re.I):
                matches=index.get(call.upper(),[])
                if len(matches)==1: pending.extend(matches)
                else: calls.add(call)
            transfers.update(re.findall(r'\b(?:XCTL|LINK)\s+PROGRAM\s*\(([^)]+)\)',text,re.I))
        files=[{'path':str(p.relative_to(SRC)), 'lines':len(p.read_bytes().splitlines()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(seen)]
        subtotal={folder:sum(x['lines'] for x in files if x['path'].startswith(folder+'/')) for folder in ['cbl','cpy','cpy-bms']}
        output[option]={'entry_programs':names,'files':files,'subtotals':subtotal,'total':sum(subtotal.values()),'missing_copybooks':sorted(missing),'external_literal_calls':sorted(calls),'cics_program_transfers':sorted(transfers),'runtime_closure_complete':False}
    dest=ROOT/'evidence/10k-scope-options.json'
    dest.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:{f:v[f] for f in ['entry_programs','subtotals','total','missing_copybooks','external_literal_calls','cics_program_transfers']} for k,v in output.items()},indent=2))

if __name__=='__main__': main()

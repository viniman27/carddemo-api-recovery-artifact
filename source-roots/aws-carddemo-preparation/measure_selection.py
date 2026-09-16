"""Read-only source inventory; writes only a selection manifest here."""
import hashlib
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parent
CASES = ROOT.parent
AWS = Path('<UPSTREAM_CHECKOUT>/aws-samples__aws-mainframe-modernization-carddemo/full-source')
EXTENSIONS = {'.cbl', '.cob', '.cobol', '.cpy'}
PROGRAMS = ['CBTRN02C.cbl','CBACT04C.cbl','CBTRN03C.cbl','CBSTM03A.CBL','CBSTM03B.CBL']

def item(path, base):
    data = path.read_bytes()
    return {'path':str(path.relative_to(base)), 'physical_lines':len(data.splitlines()),
            'sha256':hashlib.sha256(data).hexdigest()}

def main():
    baseline = {}
    for name in ['account-balance','payroll','bams']:
        base = CASES/name/'legacy-cobol'
        files = [item(p,base) for p in sorted(base.rglob('*')) if p.is_file() and p.suffix.lower() in EXTENSIONS and '.git' not in p.parts]
        baseline[name] = {'files':files,'physical_lines':sum(f['physical_lines'] for f in files)}
    pending = [AWS/'app/cbl'/n for n in PROGRAMS]
    seen = set()
    dependencies = {}
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        text = '\n'.join(line[7:72] for line in path.read_text().splitlines() if len(line)>6 and line[6] not in '*/')
        names = re.findall(r'\bCOPY\s+([\w-]+)',text,re.I)
        dependencies[str(path.relative_to(AWS))] = names
        for name in names:
            matches = [p for p in (AWS/'app/cpy').iterdir() if p.stem.upper()==name.upper()]
            if len(matches)!=1:
                raise RuntimeError(f'COPY {name}: {matches}')
            pending.extend(matches)
    files = [item(p,AWS) for p in sorted(seen)]
    programs = [f for f in files if f['path'].startswith('app/cbl/')]
    copybooks = [f for f in files if f not in programs]
    base_total = sum(v['physical_lines'] for v in baseline.values())
    total = sum(f['physical_lines'] for f in files)
    code_total = sum(f['physical_lines'] for f in programs)
    result = {'commit':'59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e',
        'metric':'physical lines including comments and blanks; unique paths; COPY expansion not counted repeatedly',
        'baseline_policy':'All COBOL/copybooks in the three legacy-cobol trees, including auxiliary programs and BAMS test; excludes generated wrappers and repeated contract copies',
        'baseline':baseline, 'baseline_total':base_total,
        'selection':{'programs':programs,'copybooks':copybooks,'copy_dependencies':dependencies,
                     'program_lines':code_total,'copybook_lines':total-code_total,'total':total,
                     'ratio_to_baseline':total/base_total,
                     'jcl_not_in_loc':['POSTTRAN.jcl','INTCALC.jcl','TRANBKP.jcl','COMBTRAN.jcl','TRANREPT.jcl','CREASTMT.JCL']}}
    if not (len(programs)==5 and total>base_total and code_total>base_total and total>=3000):
        raise RuntimeError('Selection size criterion failed')
    (ROOT/'evidence/large-scope-selection.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'baseline':{n:v['physical_lines'] for n,v in baseline.items()},'baseline_total':base_total,'programs':programs,'copybook_count':len(copybooks),'copybook_lines':total-code_total,'total':total,'ratio':total/base_total},indent=2))

if __name__=='__main__':
    main()

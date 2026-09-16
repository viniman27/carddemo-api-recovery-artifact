#!/usr/bin/env python3
"""Verified local batch preflight. Synthetic fixtures; no business reimplementation.
Uses source-format flags only; source bytes remain unchanged.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from prepare import require, check_load_target
from build_helpers import TEMPLATE

ROOT=Path(__file__).resolve().parent
PARENT=ROOT.parent
SOURCE=Path('<UPSTREAM_CHECKOUT>/aws-samples__aws-mainframe-modernization-carddemo/full-source')

def main():
    stage=Path(tempfile.mkdtemp(prefix='verified-',dir=ROOT/'runs'))
    build=stage/'build'; build.mkdir()
    logs=[]
    instrument='--coverage' in sys.argv
    def run(cmd, wd=build, extra=None, expect=0):
        env=dict(os.environ,**(extra or {}))
        if instrument and str(cmd[0])=='cobc':
            env.update(COB_CC='gcc-11',COB_CFLAGS='-I/opt/homebrew/include -fsigned-char')
        p=subprocess.run([str(x) for x in cmd],cwd=wd,env=env,capture_output=True,text=True,timeout=45)
        logs.append({'command':[str(x) for x in cmd],'cwd':str(wd),'env_override':extra or {},'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        (stage/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
        require(p.returncode==expect,p.stdout+p.stderr)
        return p
    manifest=json.loads((ROOT/'evidence/upstream-hashes.json').read_text())
    for f in manifest['files']:
        for base in [SOURCE,ROOT/'corpus']:
            require(hashlib.sha256((base/f['path']).read_bytes()).hexdigest()==f['sha256'],'Hash mismatch '+f['path'])
    cp=ROOT/'corpus/app/cpy'
    common=['cobc','-std=ibm','-fsign=ascii','-I',str(cp)]
    if instrument:
        common+=['-O0','--coverage','--save-temps']
    for name,exe,mode,flags in [('CBACT04C.cbl','CBACT04C.dylib','-m',[]),('CBTRN03C.cbl','CBTRN03C','-x',[])]:
        run(common+[mode,*flags,'-o',str(build/exe),str(ROOT/'corpus/app/cbl'/name)])
    run(common+['-x','-o',str(build/'CBTRN02C'),str(PARENT/'corpus/app/cbl/CBTRN02C.cbl')])
    for name in ['intcalc_fixture','report_fixture','CBACT04C_driver']:
        run(common+['-x','-free','-o',str(build/name),str(ROOT/'support'/f'{name}.cbl')])
    for variant in ['2']:
        lib=build/('le'+variant);lib.mkdir()
        run(common+['-m','-free','-o',str(lib/'CEE3ABD.dylib'),str(ROOT/'support'/f'CEE3ABD{variant}.cbl')])
    sizes={'TRANFILE':(350,16),'ACCTFILE':(300,11)}
    for name,(size,key) in sizes.items():
        helper=build/f'io_{name}.cbl'
        helper.write_text(TEMPLATE.format(size=size,key=key,rest=size-key))
        run(common+['-x','-free','-o',str(build/f'io_{name}'),str(helper)])
    def io_file(wd,name,mode,raw):
        if mode=='LOAD': check_load_target(wd,wd/name)
        run([build/f'io_{name}'],wd,{'IO_MODE':mode,'DD_RAW':str(raw),'DD_IDX':str(wd/name)})
    def nominal(label):
        wd=stage/label;wd.mkdir()
        run([build/'intcalc_fixture'],wd)
        from test_posttran import transaction
        posted=bytearray(transaction(card=b'4111111111111111'))
        posted[18:22]=b'0005'
        (wd/'DALYTRAN').write_bytes(posted)
        (wd/'TRANFILE.seed').write_bytes(b'')
        io_file(wd,'TRANFILE','LOAD',wd/'TRANFILE.seed')
        run([build/'CBTRN02C'],wd,{'COB_LIBRARY_PATH':str(build/'le2')})
        io_file(wd,'TRANFILE','DUMP',wd/'POSTED.raw')
        require(len((wd/'POSTED.raw').read_bytes())==350,'POSTTRAN did not persist one record')
        io_file(wd,'ACCTFILE','DUMP',wd/'ACCT.before')
        require((wd/'ACCT.before').read_bytes()[12:24]==b'000000052500','Post balance must be 525.00')
        p=run([build/'CBACT04C_driver'],wd,{'COB_LIBRARY_PATH':str(build)+os.pathsep+str(build/'le2')})
        require('END OF EXECUTION OF PROGRAM CBACT04C' in p.stdout,'Interest did not reach normal end')
        tr=(wd/'TRANSACT').read_bytes()
        require(len(tr)==350,'Interest must produce one 350-byte record')
        require(tr[132:143]==b'00000010025','Interest fixture: expected 100.25 from posted category balance')
        io_file(wd,'ACCTFILE','DUMP',wd/'ACCT.after')
        rd=wd/'report';rd.mkdir()
        # One actual generated record, already ordered; no sorting implementation needed.
        (rd/'TRANFILE').write_bytes(tr)
        run([build/'report_fixture'],rd)
        date=tr[304:314]
        (rd/'DATEPARM').write_bytes((date+b' '+date).ljust(80,b' '))
        run([build/'CBTRN03C'],rd,{'COB_LIBRARY_PATH':str(build/'le2')})
        report=(rd/'TRANREPT').read_bytes()
        require(len(report)>0 and len(report)%133==0,'Report framing invalid')
        require(b'100.25' in report,'Generated interest amount absent from report')
        observed={'case':label,'interest_bytes':len(tr),'interest_amount_ascii':tr[132:143].decode(),
            'account_before_hex':(wd/'ACCT.before').read_bytes()[12:24].hex(),
            'account_after_hex':(wd/'ACCT.after').read_bytes()[12:24].hex(),
            'report_bytes':len(report), 'report_sha256':hashlib.sha256(report).hexdigest()}
        (wd/'observations.json').write_text(json.dumps(observed,indent=2)+'\n')
        return tr,observed
    first,a=nominal('nominal-a');second,b=nominal('nominal-b')
    # CBACT04C sets both orig/proc timestamps. Retain originals, exclude only
    # timestamp area in the explicit repeatability comparison.
    require(first[:278]+first[330:]==second[:278]+second[330:],'Interest reset mismatch outside timestamp fields')
    require((stage/'nominal-a/ACCT.after').read_bytes()==(stage/'nominal-b/ACCT.after').read_bytes(),'Account record reset mismatch')
    # Isolated missing-file paths must terminate nonzero, not synthesize success.
    error=stage/'interest-missing-rate-file';error.mkdir()
    run([build/'intcalc_fixture'],error)
    (error/'DISCGRP').rename(error/'DISCGRP.absent')
    bad=run([build/'CBACT04C_driver'],error,{'COB_LIBRARY_PATH':str(build)+os.pathsep+str(build/'le2')},expect=12)
    require('LOCAL-CEE3ABD/2' in bad.stderr,'Interest error did not reach explicit abend')
    error=stage/'report-missing-date';error.mkdir()
    run([build/'report_fixture'],error)
    (error/'TRANFILE').write_bytes(first)
    bad=run([build/'CBTRN03C'],error,{'COB_LIBRARY_PATH':str(build/'le2')},expect=12)
    require('LOCAL-CEE3ABD/2' in bad.stderr,'Report error did not reach explicit abend')
    coverage=[]
    if instrument:
        for name in ['CBTRN02C','CBACT04C','CBTRN03C']:
            candidates=[build/(name+'.gcda'),build/(name+'.dylib-'+name+'.gcda')]
            available=[p for p in candidates if p.is_file()]
            require(len(available)==1,'Missing or ambiguous gcda for '+name)
            run(['gcov-11','-b','-c',str(available[0])])
            report=build/(name+'.cbl.gcov')
            require(report.is_file(),'No COBOL source report for '+name)
            counts=[]
            for line in report.read_text().splitlines():
                parts=line.split(':',2)
                if len(parts)==3 and parts[0].strip().rstrip('*').isdigit() and int(parts[0].strip().rstrip('*'))>0:
                    counts.append(int(parts[1]))
            require(bool(counts),'No positive source counters for '+name)
            coverage.append({'program':name,'report':str(report),'positive_source_line_counters':len(set(counts))})
    for f in manifest['files']:
        require(hashlib.sha256((SOURCE/f['path']).read_bytes()).hexdigest()==f['sha256'],'Upstream changed after run')
    summary={'stage':str(stage),'programs_exercised':['CBTRN02C','CBACT04C','CBTRN03C'],
             'blocked_programs':{'CBSTM03A':'z/OS PSA/TCB/TIOT dereference, actual SIGSEGV before business processing; see verified-deehe0as','CBSTM03B':'Compiled but excluded with blocked statement capability'},
             'nominal_runs':[a,b],'negative_paths':['missing DISCGRP -> rc12','missing DATEPARM -> rc12'],'coverage':coverage,
             'instrumentation':{'enabled':instrument,'COB_CC':'gcc-11' if instrument else 'default','COB_CFLAGS':'-I/opt/homebrew/include -fsigned-char' if instrument else 'default'},'repeatability':'Interest bytes except 278:330 timestamps; account balance',
             'all_commands_expected_rc':True,'source_unchanged':True,
             'limitations':['Local BDB/LE support, not mainframe equivalence','Synthetic datasets','Statement excluded: requires z/OS memory structures','No formal pipeline gate executed']}
    (stage/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (ROOT/'evidence/verified-latest.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()

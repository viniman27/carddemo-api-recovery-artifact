#!/usr/bin/env python3
"""Isolated measurement preflight. No frozen V4 artifact or denominator changed."""
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import test_posttran
from prepare import require
ROOT=Path(__file__).resolve().parent

def main():
    parent=ROOT/'coverage-preflight'
    parent.mkdir(exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='probe-',dir=parent))
    build=stage/'build'
    build.mkdir()
    logs=[]
    def command(args, env=None):
        p=subprocess.run(args,cwd=build,env=env,text=True,capture_output=True,timeout=120)
        logs.append({'command':args,'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        (stage/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
        require(p.returncode==0,p.stdout+p.stderr)
        return p
    env=dict(os.environ,COB_CC='gcc-11',COB_CFLAGS='-I/opt/homebrew/include -fsigned-char')
    cmd=['cobc','-x','-std=ibm','-fsign=ascii','-O0','--coverage','--save-temps',
         '-I',str(ROOT/'corpus/app/cpy'),'-o',str(build/'CBTRN02C'),str(ROOT/'corpus/app/cbl/CBTRN02C.cbl')]
    (stage/'environment.json').write_text(json.dumps({'COB_CC':env['COB_CC'],'COB_CFLAGS':env['COB_CFLAGS']},indent=2)+'\n')
    command(cmd,env)
    for name in ['io_TRANFILE','io_XREFFILE','io_ACCTFILE','io_TCATBALF','CEE3ABD.dylib']:
        (build/name).symlink_to(ROOT/'build'/name)
    test_posttran.ROOT=stage
    stream=io.StringIO()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(test_posttran.PosttranTests)
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (stage/'tests.txt').write_text(stream.getvalue())
    print(stream.getvalue())
    require(result.wasSuccessful(),'Instrumented behavioral test failure')
    gcda=list(build.glob('*.gcda'))
    require(bool(gcda),'No gcda was flushed by real execution')
    for p in gcda:
        command(['gcov-11','-b','-c',str(p)])
    reports=list(build.glob('*.gcov'))
    source_reports=[p for p in reports if 'CBTRN02C' in p.name and '.cbl.' in p.name]
    require(bool(source_reports),'No gcov report mapped to original COBOL')
    observed=[]
    for p in source_reports:
        active=[]
        for row in p.read_text().splitlines():
            fields=row.split(':',2)
            if len(fields)==3 and fields[0].strip().rstrip('*').isdigit():
                if int(fields[0].strip().rstrip('*'))>0: active.append(int(fields[1]))
        require(bool(active),'No positive source counter')
        observed.append({'report':str(p),'positive_source_line_counters':len(set(active))})
    summary={'stage':str(stage),'tests_run':result.testsRun,'tests_success':result.wasSuccessful(),
             'gcda_files':[str(p) for p in gcda],'source_reports':observed,
             'claim':'Technical gcov/behavior preflight only; not official coverage or semantic validation'}
    (stage/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (ROOT/'evidence/coverage-latest.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()

#!/usr/bin/env python3
"""Single local acceptance command for the executable research candidate."""
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parent

def main():
    logs=[]
    for script,args in [('verify.py',[]),('expanded-batch/verify_batch.py',['--coverage']),('package_research.py',[])]:
        command=[sys.executable,str(ROOT/script),*args]
        p=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=240)
        logs.append({'command':command,'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        (ROOT/'evidence/research-acceptance.json').write_text(json.dumps(logs,indent=2)+'\n')
        print(p.stdout,end='');print(p.stderr,end='')
        if p.returncode:raise SystemExit(p.returncode)
    print('Verified local batch candidate: immutable sources, real executions, reset and gcov. No formal research gate executed.')

if __name__=='__main__':main()

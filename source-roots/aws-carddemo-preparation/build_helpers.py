#!/usr/bin/env python3
"""Build byte-preserving indexed I/O helpers, not business implementations."""
import json
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent
# CBTRN02C FD declarations, lines 71-97: record size and primary-key prefix.
FILES = {'TRANFILE': (350, 16), 'XREFFILE': (50, 16),
         'ACCTFILE': (300, 11), 'TCATBALF': (50, 17)}
TEMPLATE = '''>>source format free
identification division.
program-id. RAWIO.
environment division.
input-output section.
file-control.
 select raw-file assign to RAW
 organization sequential file status fs.
 select idx-file assign to IDX
 organization indexed access sequential
 record key idx-key file status ix.
data division.
file section.
fd raw-file.
01 raw-rec pic x({size}).
fd idx-file.
01 idx-rec.
 02 idx-key pic x({key}).
 02 idx-rest pic x({rest}).
working-storage section.
01 fs pic xx.
01 ix pic xx.
01 op pic x(8).
procedure division.
 accept op from environment 'IO_MODE'
 evaluate function trim(op)
 when 'LOAD'
   open input raw-file
   if fs not = '00' perform bad-raw end-if
   open output idx-file
   if ix not = '00' perform bad-index end-if
   perform until fs = '10'
     read raw-file
     evaluate fs
       when '00'
         move raw-rec to idx-rec
         write idx-rec
         if ix not = '00' perform bad-index end-if
       when '10' continue
       when other perform bad-raw
     end-evaluate
   end-perform
 when 'DUMP'
   open input idx-file
   if ix not = '00' perform bad-index end-if
   open output raw-file
   if fs not = '00' perform bad-raw end-if
   perform until ix = '10'
     read idx-file next record
     evaluate ix
       when '00'
         move idx-rec to raw-rec
         write raw-rec
         if fs not = '00' perform bad-raw end-if
       when '10' continue
       when other perform bad-index
     end-evaluate
   end-perform
 when other
   display 'INVALID IO_MODE' upon syserr
   stop run returning 12
 end-evaluate
 close raw-file
 if fs not = '00' perform bad-raw end-if
 close idx-file
 if ix not = '00' perform bad-index end-if
 stop run returning 0.
bad-raw.
 display 'RAW STATUS=' fs upon syserr
 stop run returning 12.
bad-index.
 display 'INDEX STATUS=' ix upon syserr
 stop run returning 12.
'''

def main():
    support = ROOT / 'support'
    support.mkdir(exist_ok=True)
    results = []
    for name, (size, key) in FILES.items():
        path = support / f'io_{name}.cbl'
        path.write_text(TEMPLATE.format(size=size, key=key, rest=size-key))
        cmd = ['cobc', '-x', '-free', '-std=ibm', '-fsign=ascii', '-o',
               str(ROOT/'build'/f'io_{name}'), str(path)]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        results.append({'command': cmd, 'rc': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
        if p.returncode:
            print(p.stderr)
            raise SystemExit(p.returncode)
    (ROOT/'evidence/helper-build.json').write_text(json.dumps(results, indent=2)+'\n')
    print('Built external raw indexed-file loaders/dumpers:', ', '.join(FILES))

if __name__ == '__main__':
    main()

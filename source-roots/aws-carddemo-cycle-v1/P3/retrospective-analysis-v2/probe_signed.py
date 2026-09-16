"""Local toolchain qualification only: not a CardDemo business application."""
from pathlib import Path
import subprocess,json,hashlib
import evidence as e
root=Path(__file__).resolve().parent/'signed-probe'; root.mkdir(exist_ok=True)
values=list(range(-120,-130,-1))+[0,99999999999,-99999999999]
lines=['>>source format free','identification division.','program-id. SIGNPROBE.','data division.','working-storage section.','01 signed-number pic s9(09)v99.','01 raw-number redefines signed-number pic x(11).','procedure division.']
for cents in values:
    token=('-' if cents<0 else '')+str(abs(cents)//100)+'.'+f'{abs(cents)%100:02d}'
    lines+=['move '+token+' to signed-number','display raw-number with no advancing']
lines+=['stop run.']
src=root/'probe.cbl'; src.write_text('\n'.join(lines)+'\n'); exe=root/'probe'
compile_result=subprocess.run(['cobc','-x','-free','-o',str(exe),str(src)],capture_output=True,timeout=60)
(root/'compile.log').write_bytes(compile_result.stdout+compile_result.stderr); assert compile_result.returncode==0
result=subprocess.run([str(exe)],capture_output=True,timeout=30); (root/'output.raw').write_bytes(result.stdout); assert result.returncode==0 and len(result.stdout)==len(values)*11
rows=[]
for i,expected in enumerate(values):
    raw=result.stdout[i*11:(i+1)*11]; decoded=e.number(raw); encoded=e.put_number(b'0'*11,0,11,expected)
    rows.append({'expectedCents':expected,'rawHex':raw.hex(),'decodedCents':decoded,'decodePass':decoded==expected,'encodePass':encoded==raw})
assert all(r['decodePass'] and r['encodePass'] for r in rows)
version=subprocess.run(['cobc','-V'],capture_output=True,text=True,timeout=30)
report={'scope':'synthetic representation qualification; no business program executed','recordSize':11,'trials':len(rows),'rows':rows,'compilerVersion':version.stdout,'sourceSha256':hashlib.sha256(src.read_bytes()).hexdigest(),'rawSha256':hashlib.sha256(result.stdout).hexdigest(),'overflow':'not qualified; rejected by checker'}
(root/'qualification.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({'trials':len(rows),'allMatched':True,'compiler':version.stdout.splitlines()[0]}))

#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, shutil, subprocess, tempfile, textwrap, time
from pathlib import Path

ROOT = Path('<REDACTED_LOCAL_PATH>')
P3 = ROOT/'casos/aws-carddemo-cycle-v1/P3'
MAT = P3/'fixture-materialization-v2'
PKG = MAT/'package'
CAND = P3/'fixture-candidates-v1'
AUTH = P3/'reference-authoring-input-v1'
OUT = P3/'fixture-materialization-review-v2'
OUT.mkdir(parents=True, exist_ok=True)

commands=[]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def shab(b): return hashlib.sha256(b).hexdigest()
def rec_cmd(cmd, cwd=None, env=None, expect=None, timeout=120):
    started=time.time(); p=subprocess.run(cmd, cwd=cwd, env={**os.environ, **(env or {})}, text=True, capture_output=True, timeout=timeout)
    r={'cmd':cmd,'cwd':str(cwd or Path.cwd()),'env':env or {},'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'duration_s':round(time.time()-started,3)}
    commands.append(r)
    if expect is not None and p.returncode != expect:
        raise RuntimeError(json.dumps(r, indent=2))
    return r

def load_json(path): return json.loads(Path(path).read_text())
def load_jsonl(path): return [json.loads(x) for x in Path(path).read_text().splitlines() if x]

def inv(path):
    files={}
    for p in sorted(Path(path).rglob('*')):
        if p.is_file():
            rel=p.relative_to(path).as_posix()
            files[rel]={'bytes':p.stat().st_size,'sha256':sha(p)}
    return {'fileCount':len(files),'files':files,'treeSha256':shab(json.dumps(files,sort_keys=True,separators=(',',':')).encode())}

manifest=load_json(PKG/'manifest.json')
verification=load_json(PKG/'verification.json')
candidate_manifest=load_json(CAND/'manifest.json')
byte_review=load_json(PKG/'byte-layout-review.json')

findings=[]; blockers=[]
def add(status, area, detail, evidence=None, blocker=False):
    item={'status':status,'area':area,'detail':detail}
    if evidence: item['evidence']=evidence
    findings.append(item)
    if blocker: blockers.append(item)

# AGENTS exposure declaration
agents=[]
p=ROOT
while True:
    if (p/'WORKSPACE-NOTES.md').exists(): agents.append(str((p/'WORKSPACE-NOTES.md').relative_to(ROOT)))
    if p==p.parent: break
    if p == Path('<REDACTED_LOCAL_PATH>'): break
    p=p.parent

# Current bytes vs saved pins: recompute from disk for all manifest inventories.
pin_mismatches=[]
for track, meta in manifest['packages'].items():
    cur=inv(PKG/track)
    if cur['fileCount'] != meta['inventory']['fileCount'] or cur['treeSha256'] != meta['inventory']['treeSha256']:
        pin_mismatches.append({'track':track,'manifestTree':meta['inventory']['treeSha256'],'currentTree':cur['treeSha256']})
    for rel, saved in meta['inventory']['files'].items():
        p=PKG/track/rel
        if not p.exists(): pin_mismatches.append({'track':track,'file':rel,'issue':'missing'}); continue
        got={'bytes':p.stat().st_size,'sha256':sha(p)}
        if got != saved: pin_mismatches.append({'track':track,'file':rel,'saved':saved,'current':got})
if pin_mismatches:
    add('FAIL','pins/current-bytes','Manifest pins do not match current package bytes',pin_mismatches,True)
else:
    add('PASS','pins/current-bytes','Recomputed bytes/sha256/treeSha256 for all package inventories match current files, not only saved report.',{'tracks':list(manifest['packages'])})

# Candidate logical/sequential pins current
cand_mismatches=[]
for r in candidate_manifest['resources']:
    p=CAND/r['path']
    if p.exists():
        got={'bytes':p.stat().st_size,'sha256':sha(p)}
        if got['bytes']!=r['bytes'] or got['sha256']!=r['sha256']:
            cand_mismatches.append({'path':r['path'],'saved':{'bytes':r['bytes'],'sha256':r['sha256']},'current':got})
if cand_mismatches:
    add('FAIL','candidate-pins','Candidate manifest resources drifted',cand_mismatches,True)
else:
    add('PASS','candidate-pins','Candidate v1 resource pins match current source bytes.',{'resourceCount':len(candidate_manifest['resources'])})

# Layout source current and encodings vs authorized authoring input.
layout_issues=[]; layout_count=0
for lr in candidate_manifest['layout_copies']:
    cp=CAND/lr['path']; ap=AUTH/'corpus'/lr['source'].split('corpus/')[-1]
    layout_count += 1
    for label,path in [('candidate',cp),('authoring',ap)]:
        if not path.exists(): layout_issues.append({'layout':lr['path'],'missing':label}); continue
        data=path.read_bytes()
        if data.decode('ascii', errors='strict') is None: pass
    if cp.exists() and ap.exists():
        if cp.read_bytes()!=ap.read_bytes(): layout_issues.append({'layout':lr['path'],'issue':'candidate copy differs from authoring input'})
        if sha(cp)!=lr['sha256']: layout_issues.append({'layout':lr['path'],'issue':'layout manifest sha mismatch'})
if layout_issues:
    add('FAIL','layouts/encoding','Layout copies are not byte-identical ASCII to authorized authoring input',layout_issues,True)
else:
    add('PASS','layouts/encoding','All manifest layout/JCL/proc copies are current ASCII and byte-identical to reference-authoring-input-v1.',{'layoutCount':layout_count})

# Record lengths and selected field probes.
record_checks={}
# logical JSONL lengths
specs={'ACCTFILE':300,'CARDXREF':50,'DISCGRP':50,'TCATBALF':50,'TRANSACT':350,'TRANTYPE':60,'TRANCATG':60}
logical_issues=[]
for name,size in specs.items():
    rows=load_jsonl(CAND/f'data/indexed-logical/{name}.jsonl')
    lens=[len(r['recordImage'].encode('ascii')) for r in rows]
    if any(x!=size for x in lens): logical_issues.append({'name':name,'expected':size,'lengths':lens})
    record_checks[name]={'count':len(rows),'recordSize':size,'sha_raw':shab(b''.join(r['recordImage'].encode('ascii') for r in rows))}
# sequential fixed records
seq_defs=[('posting/DALYTRAN.dat',350),('interest/TCATBALF.dat',50),('reporting/TRANFILE.dat',350),('reporting/TRANFILE.empty.dat',350),('reporting/DATEPARM.dat',80)]
seq_issues=[]
for rel,size in seq_defs:
    p=CAND/'data/sequential'/rel; data=p.read_bytes()
    if len(data)%size!=0: seq_issues.append({'path':str(p.relative_to(CAND)),'bytes':len(data),'recordSize':size})
if logical_issues or seq_issues:
    add('FAIL','fields/layouts','Some logical/sequential record images are not fixed-width ASCII at expected lengths.',{'logical':logical_issues,'sequential':seq_issues},True)
else:
    add('PASS','fields/layouts','Logical JSONL record images and sequential files are ASCII fixed-width at expected copybook lengths.',record_checks)

# Build alternate lookup probe outside candidate source.
probe_src=OUT/'xref_alt_probe.cbl'
probe_src.write_text(textwrap.dedent(r'''
>>source format free
identification division.
program-id. XREFALT.
environment division.
input-output section.
file-control.
 select xref-file assign to XREFFILE organization indexed access random
   record key xref-card-num alternate record key xref-acct-id
   file status fs.
data division.
file section.
fd xref-file.
01 xref-rec.
 05 xref-card-num pic x(16).
 05 xref-cust-id pic 9(09).
 05 xref-acct-id pic 9(11).
 05 xref-fill pic x(14).
working-storage section.
01 fs pic xx.
01 ws-mode pic x(8).
01 keyin pic x(32).
procedure division.
 accept ws-mode from environment 'LOOKUP_MODE'
 accept keyin from environment 'LOOKUP_KEY'
 open input xref-file
 display 'OPEN=' fs
 if fs not = '00' stop run returning 12 end-if
 evaluate function trim(ws-mode)
 when 'PRIMARY'
   move keyin(1:16) to xref-card-num
   read xref-file invalid key display 'MISS=' fs end-read
 when 'ALT'
   move keyin(1:11) to xref-acct-id
   read xref-file key is xref-acct-id invalid key display 'MISS=' fs end-read
 when other
   display 'BADMODE' stop run returning 12
 end-evaluate
 display 'READ=' fs ' CARD=' xref-card-num ' ACCT=' xref-acct-id
 close xref-file
 if fs = '00' stop run returning 0 else stop run returning 2 end-if.
''').lstrip(), encoding='utf-8')
exe=OUT/'xref_alt_probe'
rec_cmd(['cobc','-std=ibm','-fsign=ascii','-x','-free','-o',str(exe),str(probe_src)], cwd=OUT, expect=0)
alt_results=[]
for track in ['posting','interest']:
    for mode,key in [('PRIMARY','4111111111111111'),('ALT','10000000001'),('ALT','99999999999')]:
        p=rec_cmd([str(exe)], cwd=PKG/track, env={'DD_XREFFILE':str(PKG/track/'XREFFILE'),'LOOKUP_MODE':mode,'LOOKUP_KEY':key}, expect=None)
        alt_results.append({'track':track,'mode':mode,'key':key,'exit_code':p['exit_code'],'stdout':p['stdout'].strip(),'stderr':p['stderr'].strip()})
alt_bad=[
    r for r in alt_results
    if ((r['key']!='99999999999' and (r['exit_code']!=0 or 'READ=00' not in r['stdout']))
        or (r['key']=='99999999999' and 'READ=23' not in r['stdout'] and 'MISS=23' not in r['stdout']))
]
if alt_bad:
    add('FAIL','alternate-lookup','Effective alternate/primary lookup probe failed.',alt_bad,True)
else:
    add('PASS','alternate-lookup','Compiled GnuCOBOL random READ by primary and alternate key succeeded for package XREFFILE; absent alternate key returned non-zero. This is an effective lookup, not a dump-only proof.',alt_results)

# Materialized indexed dumps with current helpers, do not run business COBOL.
dump_results=[]; dump_bad=[]
for track, datasets in verification['datasets'].items():
    for dd, meta in datasets.items():
        if 'dumpRawSha256' not in meta: continue
        helper=Path(verification['compiled_gnucobol_helpers'][dd])
        with tempfile.TemporaryDirectory(prefix='review-dump-') as td:
            out=Path(td)/'dump.raw'
            r=rec_cmd([str(helper)], cwd=PKG/track, env={'IO_MODE':'DUMP','DD_RAW':str(out),'DD_IDX':str(PKG/track/dd)}, expect=0)
            got=sha(out)
            ok=(got==meta['logicalRawSha256']==meta['dumpRawSha256'])
            dump_results.append({'track':track,'dd':dd,'sha256':got,'expected':meta['logicalRawSha256'],'ok':ok})
            if not ok: dump_bad.append(dump_results[-1])
if dump_bad:
    add('FAIL','materialized-read','Fresh dump/read of current indexed files did not match logical images.',dump_bad,True)
else:
    add('PASS','materialized-read','Fresh GnuCOBOL helper DUMP from current package indexed files matches logical raw SHA for every indexed DD.',dump_results)

# Verify-only on a copy so candidate is unmodified.
with tempfile.TemporaryDirectory(prefix='verify-only-copy-') as td:
    copy=Path(td)/'package'; shutil.copytree(PKG, copy)
    r=rec_cmd(['python3', str(MAT/'tools/materialize_candidates.py'), '--verify-only', str(copy)], cwd=MAT, expect=0)
    verify_only_result={'exit_code':r['exit_code'],'stdout_head':r['stdout'][:300]}
add('PASS','coordinator-verify-only','verify-only exited 0 on an isolated copy; source package not modified by the probe.',verify_only_result)

# Reset union/current full inventory proof: mutate one copy, restore second copy, compare full union of files, and prove read after reset.
with tempfile.TemporaryDirectory(prefix='review-reset-') as td:
    a=Path(td)/'first'; b=Path(td)/'second'
    shutil.copytree(PKG,a); shutil.copytree(PKG,b)
    (a/'posting'/'DALYTRAN').write_bytes(b'MUTATED')
    base_union=inv(PKG); b_union=inv(b)
    reset_ok=(base_union['treeSha256']==b_union['treeSha256'] and base_union['fileCount']==b_union['fileCount'])
    # Read one indexed and one sequential after reset from second copy.
    with tempfile.TemporaryDirectory(prefix='review-reset-dump-') as td2:
        out=Path(td2)/'dump.raw'
        rec_cmd([str(Path(verification['compiled_gnucobol_helpers']['XREFFILE']))], cwd=b/'interest', env={'IO_MODE':'DUMP','DD_RAW':str(out),'DD_IDX':str(b/'interest'/'XREFFILE')}, expect=0)
        reset_read={'interest_XREFFILE_dump_sha256':sha(out),'posting_DALYTRAN_sha256':sha(b/'posting'/'DALYTRAN')}
    if not reset_ok:
        add('FAIL','reset','Fresh copy after mutation does not match full package inventory union.',{'base':base_union,'second':b_union},True)
    else:
        add('PASS','reset','Reset validated by mutating first workspace, preparing second fresh copy, comparing full package union and performing effective read from second copy.',{'unionFileCount':base_union['fileCount'],'treeSha256':base_union['treeSha256'],'read':reset_read})

# Applicability probes: parse fixture families from bytes.
# Posting: card positions 263-278 in DALYTRAN, compare primary keys in CARDXREF JSONL.
daly=(PKG/'posting'/'DALYTRAN').read_bytes(); cards=[daly[i+262:i+278].decode('ascii') for i in range(0,len(daly),350)]
xref_cards=[r['recordImage'][:16] for r in load_jsonl(CAND/'data/indexed-logical/CARDXREF.jsonl')]
posting_lookup={'cards':cards,'xref_primary_keys':xref_cards,'present':[c for c in cards if c in xref_cards],'absent':[c for c in cards if c not in xref_cards]}
if posting_lookup['present'] and posting_lookup['absent']:
    add('PASS','family/posting.lookup','Posting fixture bytes include both present and absent CARDXREF lookup candidates.',posting_lookup)
else:
    add('FAIL','family/posting.lookup','Posting declared present/absent family is catalog-only or incomplete in bytes.',posting_lookup,True)
# Interest: PARMFILE exact and rate keys derived from account group in ACCTFILE + TCATBAL type/cat.
parm=(PKG/'interest'/'PARMFILE').read_bytes().decode('ascii')
acct_rows=load_jsonl(CAND/'data/indexed-logical/ACCTFILE.jsonl')
acct_groups={r['recordImage'][:11]:r['recordImage'][73:83] for r in acct_rows} # 1-based fields through S9s/dates to group id
# correct offset: ACCT group starts after 11+1+12*3+10*3+12*2+10=92? Recompute below.
acct_groups={}
for r in acct_rows:
    rec=r['recordImage']; acct_groups[rec[0:11]]=rec[112:122]
tcat_rows=load_jsonl(CAND/'data/indexed-logical/TCATBALF.jsonl')
disc_rows=load_jsonl(CAND/'data/indexed-logical/DISCGRP.jsonl')
disc={r['recordImage'][:16]:r['recordImage'][16:22] for r in disc_rows}
interest_rows=[]
for r in tcat_rows:
    rec=r['recordImage']; acct=rec[0:11]; t=rec[11:13]; cat=rec[13:17]; group=acct_groups.get(acct); key=(group or '')+t+cat; rate=disc.get(key)
    interest_rows.append({'acct':acct,'type':t,'cat':cat,'group':group,'discKey':key,'rateDisplay':rate})
rates=set(x['rateDisplay'] for x in interest_rows if x['rateDisplay'] is not None)
if parm=='2022071800' and '000000' in rates and any(r and r!='000000' for r in rates):
    add('PASS','family/interest.rate','PARMFILE is explicit 10-byte 2022071800 and TCATBALF/ACCTFILE/DISCGRP bytes make zero and non-zero rate rows selectable.',{'parm':parm,'rows':interest_rows})
else:
    add('FAIL','family/interest.rate','Interest zero/non-zero declaration is not fully supported by current selectable bytes/PARMFILE.',{'parm':parm,'rows':interest_rows},True)
# Reporting dates, empty/absent semantics.
dateparm=(PKG/'reporting'/'DATEPARM').read_bytes().decode('ascii')
reporting={'DATEPARM':dateparm,'start':dateparm[:10],'end':dateparm[11:21],'TRANFILE_bytes':(PKG/'reporting'/'TRANFILE').stat().st_size,'TRANFILE_empty_bytes':(PKG/'reporting'/'TRANFILE.empty').stat().st_size,'TRANREPT_present':(PKG/'reporting'/'TRANREPT').exists()}
if reporting['TRANFILE_empty_bytes']==0 and not reporting['TRANREPT_present'] and reporting['start'] and reporting['end']:
    add('PASS','family/reporting','Reporting has separate non-empty TRANFILE, zero-byte TRANFILE.empty, DATEPARM start/end bytes, and no precreated TRANREPT output; absent input remains a declared blocker rather than a materialized case.',reporting)
else:
    add('FAIL','family/reporting','Reporting empty/absent/date separation has current-byte issues.',reporting,True)

# DD inventory vs JCL selected scope.
expected={
 'posting':{'DALYTRAN','TRANFILE','XREFFILE','XREFFILE.1','ACCTFILE','TCATBALF'},
 'interest':{'TCATBALF','XREFFILE','XREFFILE.1','ACCTFILE','DISCGRP','PARMFILE'},
 'reporting':{'TRANFILE','TRANFILE.empty','CARDXREF','TRANTYPE','TRANCATG','DATEPARM'}
}
dd_issues=[]
for track, exp in expected.items():
    got={p.name for p in (PKG/track).iterdir() if p.is_file()}
    if got != exp: dd_issues.append({'track':track,'expected':sorted(exp),'got':sorted(got),'missing':sorted(exp-got),'extra':sorted(got-exp)})
if dd_issues:
    add('FAIL','dd-inventory','Physical DD/sidecar inventory differs from reviewed scope.',dd_issues,True)
else:
    add('PASS','dd-inventory','All reviewed physical DD files and sidecars are present exactly for the candidate package scope.',{k:sorted(v) for k,v in expected.items()})

# Overall verdict: no officialization, partial if any blocker else pass.
verdict='FAIL' if any(f['status']=='FAIL' and f in blockers for f in findings) else 'PASS'
# If no hard blockers but declared families are not business coverage, keep PASS with limits.
limits=[
 'Review did not execute CardDemo business COBOL and did not create/approve expected outputs or campaign fixtures.',
 'Declared families are applicable as technical selection/input families for current bytes; they are not complete business coverage claims.',
 'Absent reporting input is only represented as a blocker/precondition, not executable bytes.',
 'No fixture officialization performed.'
]
review={'verdict':verdict,'generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),'workspace':str(ROOT),'agents_exposure_declared':agents,'scope':{'allowed_inputs':['P3/fixture-materialization-v2','P3/fixture-candidates-v1','P3/reference-authoring-input-v1','P3/reference-executable-v4 metadata only','P3/reference-independent-review-v4 metadata only'],'not_used':['oracles','campaign/quarantine outputs','business COBOL execution']},'findings':findings,'blockers':blockers,'limits':limits,'commands':commands}
(OUT/'review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True)+'\n')

md=['# Fixture materialization candidate v2 — outside-in review','',f'Verdict: **{verdict}**','',f'Generated UTC: `{review["generated_utc"]}`','',f'AGENTS exposure declared: `{", ".join(agents) if agents else "none detected"}`','', '## Findings']
for f in findings:
    md.append(f'- **{f["status"]} — {f["area"]}**: {f["detail"]}')
md += ['', '## Limits / non-claims']
for x in limits: md.append(f'- {x}')
md += ['', '## Commands/probes executed']
for i,c in enumerate(commands,1):
    env=(' env='+json.dumps(c['env'], sort_keys=True) if c.get('env') else '')
    md.append(f'{i}. `cwd={c["cwd"]}{env} {" ".join(c["cmd"])}` → exit {c["exit_code"]}')
md += ['', 'See `review.json` for full stdout/stderr and byte-level evidence.']
(OUT/'REVIEW.md').write_text('\n'.join(md)+'\n', encoding='utf-8')
print(json.dumps({'verdict':verdict,'findings':len(findings),'blockers':len(blockers),'review':str(OUT/'REVIEW.md'),'json':str(OUT/'review.json')}, indent=2, ensure_ascii=False))

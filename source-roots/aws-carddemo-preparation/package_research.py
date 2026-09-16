#!/usr/bin/env python3
"""Freeze only the executable research candidate; never rewrites legacy."""
import json
import re
import shutil
import tarfile
from pathlib import Path
from prepare import SOURCE, UPSTREAM, COMMIT, require, digest
ROOT=Path(__file__).resolve().parent

def main():
    pending=[SOURCE/'app/cbl'/n for n in ['CBTRN02C.cbl','CBACT04C.cbl','CBTRN03C.cbl']]
    seen=set()
    while pending:
        p=pending.pop()
        if p in seen:continue
        seen.add(p)
        text='\n'.join(line[7:72] for line in p.read_text().splitlines() if len(line)>6 and line[6] not in '*/')
        for cp in re.findall(r'\bCOPY\s+([\w-]+)',text,re.I):
            item=SOURCE/'app/cpy'/(cp+'.cpy')
            require(item.is_file(),'Missing COPY '+cp)
            pending.append(item)
    code=set(seen)
    for n in ['POSTTRAN.jcl','INTCALC.jcl','TRANREPT.jcl','COMBTRAN.jcl','TRANBKP.jcl']:
        seen.add(SOURCE/'app/jcl'/n)
    seen.add(SOURCE/'LICENSE')
    # TRANREPT references the REPROC orchestration procedure.
    for p in (SOURCE/'app/proc').iterdir():
        if p.stem.upper()=='REPROC': seen.add(p)
    files=[]
    with tarfile.open(UPSTREAM/'source.tar.gz','r:gz') as archive:
        idx={m.name.split('/',1)[1]:m for m in archive.getmembers() if m.isfile() and '/' in m.name}
        import hashlib
        for p in sorted(seen):
            rel=str(p.relative_to(SOURCE))
            require(rel in idx,'Missing archive member '+rel)
            stream=archive.extractfile(idx[rel])
            if stream is None: raise RuntimeError('Archive member is not readable: '+rel)
            require(hashlib.sha256(stream.read()).hexdigest()==digest(p),'Archive mismatch '+rel)
            dest=ROOT/'research-corpus'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists(): require(digest(dest)==digest(p),'Frozen corpus mismatch '+rel)
            else: shutil.copy2(p,dest)
            files.append({'path':rel,'sha256':digest(p),'physical_lines':len(p.read_bytes().splitlines()),'in_code_count':p in code})
    total=sum(x['physical_lines'] for x in files if x['in_code_count'])
    baseline=json.loads((ROOT/'evidence/large-scope-selection.json').read_text())['baseline_total']
    require(total>baseline,'Executable candidate smaller than prior combined baseline')
    result={'commit':COMMIT,'scope':'Posting, interest transaction generation and transaction reporting',
            'programs':['CBTRN02C','CBACT04C','CBTRN03C'],'files':files,'physical_code_copybook_lines':total,
            'prior_combined_baseline':baseline,'scope_10k_ready':False,
            'pipeline_input':str(ROOT/'research-corpus'),
            'exclude_from_extraction':['support','runs','tests','reports','expected outputs','build','expanded-batch/corpus (broad exploratory include tree)'],
            'readiness':'Local operational prerequisites demonstrated; formal specs/validation not performed',
            'data_policy':'Original layouts/JCL are inputs; synthetic preflight fixtures and expected outcomes are quarantined. Freeze strategy-visible domain data during scope gate.'}
    (ROOT/'evidence/research-package.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'files':len(files),'programs':result['programs'],'physical_code_copybook_lines':total,'prior_baseline':baseline,'pipeline_input':result['pipeline_input']},indent=2))

if __name__=='__main__':main()

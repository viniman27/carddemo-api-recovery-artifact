#!/usr/bin/env python3
"""Local-only provenance, closure and compile probe. Never edits upstream."""
import hashlib
import json
import re
import shutil
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UPSTREAM = Path('<UPSTREAM_CHECKOUT>/aws-samples__aws-mainframe-modernization-carddemo')
SOURCE = UPSTREAM / 'full-source'
COMMIT = '59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e'

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def check_load_target(run_directory, target):
    root = Path(run_directory).resolve(strict=True)
    path = Path(target)
    resolved = path.resolve()
    require(resolved != root and resolved.is_relative_to(root), 'LOAD target outside run directory')
    require(not path.exists() and not path.is_symlink(), 'LOAD target already exists')
    return resolved

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    evidence = ROOT / 'evidence'
    evidence.mkdir(exist_ok=True)
    info = json.loads((UPSTREAM / 'inspection.json').read_text())
    require(info['commit'] == COMMIT, 'Commit mismatch')
    inventory = []
    for p in sorted(SOURCE.rglob('*')):
        if not p.is_file():
            continue
        rel = p.relative_to(SOURCE)
        item = {'path': str(rel), 'sha256': digest(p), 'bytes': p.stat().st_size}
        if p.suffix.lower() in ('.cbl', '.cob', '.cobol', '.cpy', '.jcl'):
            item['physical_lines'] = len(p.read_bytes().splitlines())
        inventory.append(item)
    manifest = {'commit': COMMIT, 'repository': info['url'],
                'archive_sha256': digest(UPSTREAM / 'source.tar.gz'), 'files': inventory}
    target = evidence / 'upstream-manifest.json'
    if target.exists():
        require(json.loads(target.read_text()) == manifest, 'Upstream changed; refusing overwrite')
    else:
        target.write_text(json.dumps(manifest, indent=2) + '\n')
    pending = ['app/cbl/CBTRN02C.cbl']
    closure = set()
    calls = set()
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        closure.add(name)
        text = '\n'.join(line[7:72] for line in (SOURCE / name).read_text().splitlines()
                         if len(line) > 6 and line[6] not in '*/')
        calls.update(re.findall(r"\bCALL\s+['\"]([^'\"]+)['\"]", text, re.I))
        for cp in re.findall(r'\bCOPY\s+([\w-]+)', text, re.I):
            path = 'app/cpy/' + cp + '.cpy'
            require((SOURCE / path).is_file(), f'Unresolved COPY: {cp}')
            pending.append(path)
    selected = closure | {'app/jcl/POSTTRAN.jcl', 'LICENSE'}
    with tarfile.open(UPSTREAM / 'source.tar.gz', 'r:gz') as archive:
        archived = {m.name.split('/', 1)[1]: m for m in archive.getmembers()
                    if m.isfile() and '/' in m.name}
        for name in selected:
            require(name in archived, f'Not in pinned archive: {name}')
            archived_hash = hashlib.sha256(archive.extractfile(archived[name]).read()).hexdigest()
            require(archived_hash == digest(SOURCE / name), f'Archive mismatch: {name}')
    for name in sorted(selected):
        src, dest = SOURCE / name, ROOT / 'corpus' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            require(digest(src) == digest(dest), f'Corpus changed: {name}')
        else:
            shutil.copy2(src, dest)
        require(digest(src) == digest(dest), f'Copy integrity failed: {name}')
    measured = [x for x in inventory if x['path'] in selected]
    (evidence / 'closure.json').write_text(json.dumps({
        'entrypoint': 'CBTRN02C', 'job': 'POSTTRAN', 'files': measured,
        'external_calls': sorted(calls), 'source_copybook_lines': sum(
            x.get('physical_lines', 0) for x in measured if x['path'] in closure),
        'status': 'static COPY closure only; CEE3ABD requires explicit runtime support'
    }, indent=2) + '\n')
    build = ROOT / 'build'
    build.mkdir(exist_ok=True)
    commands = [['cobc', '-info'], ['cobc', '-m', '-free', '-std=ibm', '-o', str(build / 'CEE3ABD.dylib'), str(ROOT / 'support/CEE3ABD.cbl')], ['cobc', '-x', '-std=ibm', '-fsign=ascii', '-I', str(ROOT / 'corpus/app/cpy'),
                '-o', str(build / 'CBTRN02C'), str(ROOT / 'corpus/app/cbl/CBTRN02C.cbl')]]
    results = []
    for command in commands:
        p = subprocess.run(command, cwd=build, capture_output=True, text=True, timeout=90)
        results.append({'command': command, 'rc': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
    (evidence / 'build.json').write_text(json.dumps(results, indent=2) + '\n')
    require(all(digest(SOURCE / x['path']) == x['sha256'] for x in inventory), 'Upstream integrity failed after build')
    print(json.dumps({'corpus_files': len(selected), 'external_calls': sorted(calls),
                      'compile_rc': results[-1]['rc'], 'diagnostics': results[-1]['stderr']}, indent=2))
    raise SystemExit(next((r['rc'] for r in results if r['rc']), 0))

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Rebuild, exercise and record the local preflight. Does not run formal gates."""
import collections
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import prepare

ROOT = Path(__file__).resolve().parent

def main():
    results = []
    for args in [['prepare.py'], ['build_helpers.py'],
                 ['-m', 'unittest', 'test_io', 'test_abend', 'test_posttran', 'test_safety', '-v']]:
        command = [sys.executable, *args]
        p = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=180)
        results.append({'command': command, 'rc': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
        print(p.stdout, end='')
        print(p.stderr, end='')
        (ROOT/'evidence/verification.json').write_text(json.dumps(results, indent=2)+'\n')
        if p.returncode:
            raise SystemExit(p.returncode)
    manifest = json.loads((ROOT/'evidence/upstream-manifest.json').read_text())
    for item in manifest['files']:
        prepare.require(prepare.digest(prepare.SOURCE/item['path']) == item['sha256'], 'Upstream hash mismatch: '+item['path'])
    closure = json.loads((ROOT/'evidence/closure.json').read_text())
    for item in closure['files']:
        prepare.require(prepare.digest(ROOT/'corpus'/item['path']) == item['sha256'], 'Corpus hash mismatch: '+item['path'])
    audit = {}
    for name in ['acctdata.txt','cardxref.txt','dailytran.txt','tcatbal.txt']:
        path = prepare.SOURCE/'app/data/ASCII'/name
        audit[name] = {'sha256': prepare.digest(path),
                       'physical_record_widths': dict(collections.Counter(map(len, path.read_bytes().splitlines())))}
    (ROOT/'evidence/upstream-data-widths.json').write_text(json.dumps(audit,indent=2)+'\n')
    checked = {'all_upstream_files_unchanged': len(manifest['files']),
               'selected_files_byte_identical_to_archive_and_source': len(closure['files']),
               'source_copybook_physical_lines': closure['source_copybook_lines'],
               'coverage_collected_by_this_command': False, 'formal_pipeline_started': False}
    (ROOT/'evidence/integrity.json').write_text(json.dumps(checked,indent=2)+'\n')
    print(json.dumps(checked, indent=2))

if __name__ == '__main__':
    main()

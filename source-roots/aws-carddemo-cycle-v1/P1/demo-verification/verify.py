"""Local nominal checks only; not an AWS experiment or human gate."""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import subprocess
import yaml
from openapi_spec_validator import validate

root = Path(__file__).resolve().parent.parent
cases = [
    ('temperature', 'demo-01-temperature', Decimal(0)*9/5+32, None),
    ('shipping', 'demo-02-shipping', Decimal(2)*Decimal('1.50'), 'Y'),
    ('membership', 'demo-03-membership', Decimal(100)*Decimal('0.10'), None),
]
results = []
for name, demo, expected, flag in cases:
    folder = root/'few-shot-candidate'/demo
    validate(yaml.safe_load((folder/'openapi.yaml').read_text()))
    exe = root/'demo-verification'/name
    cmd = ['cobc', '-x', '-free', '-o', str(exe), str(exe.with_suffix('.cbl')), str(folder/'legacy.cbl')]
    compiled = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    row = {'demo': demo, 'openapi_valid': True, 'compile_command': cmd,
           'compile_exit': compiled.returncode, 'compile_stderr': compiled.stderr, 'passed': False}
    if compiled.returncode == 0:
        run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=10)
        parts = run.stdout.strip().split('|')
        try:
            match = Decimal(parts[0]) == expected and (flag is None or parts[1:] == [flag])
        except (ArithmeticError, ValueError):
            match = False
        row.update(exit_code=run.returncode, stdout=run.stdout, stderr=run.stderr,
                   expected=str(expected), expected_flag=flag, passed=run.returncode == 0 and match)
    results.append(row)
manifest = json.loads((root/'few-shot-candidate/manifest.json').read_text())
originals = all(hashlib.sha256(Path(x['original_path']).read_bytes()).hexdigest() == x['original_sha256'] for x in manifest['files'])
candidates = all(hashlib.sha256((root/'few-shot-candidate'/x['path']).read_bytes()).hexdigest() == x['candidate_sha256'] for x in manifest['files'])
report = {'validator': 'openapi-spec-validator==0.7.2', 'originals_unchanged': originals,
          'candidate_hashes_match': candidates, 'results': results,
          'limits': 'One nominal case per demo. No boundary/overflow completeness or human approval.'}
(root/'demo-verification/results-final.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
raise SystemExit(0 if originals and candidates and all(x['passed'] for x in results) else 1)

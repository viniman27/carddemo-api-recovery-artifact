#!/usr/bin/env python3
"""Technical resource reset/adulteration QA only; does not invoke COBOL."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('binding', ROOT.parent / 'P2b/p2b_binding.py')
assert spec is not None and spec.loader is not None
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def main():
    out = Path(tempfile.mkdtemp(prefix='reset-bytes-qa-', dir=ROOT))
    package = out / 'package'
    shutil.copytree(ROOT / 'technical-packages-v3-argument', package)
    reg = package / 'registry.json'
    rows = []
    for track in ('posting', 'interest', 'reporting'):
        fx = b.select_external_fixture(track, reg)
        first = out / (track + '-first'); first.mkdir()
        second = out / (track + '-second'); second.mkdir()
        a = b.materialize_fixture(fx, first)
        for dd in b.RESOURCE_NAMES[track]:
            (first / dd).write_bytes(b'EXPLICIT TECHNICAL MUTATION')
        mutated = b.capture_state_snapshot(first)
        z = b.materialize_fixture(fx, second)
        proof = b.prove_fresh_materialization_reset(a, z)
        proof['allFirstResourcesActuallyChanged'] = all(b.sha256(first / dd) != item['sourceSha256'] for dd, item in a['files'].items())
        proof['sourcePackageUnchanged'] = all(b.sha256(Path(item['sourcePath'])) == item['sourceSha256'] for item in a['files'].values())
        assert proof['resetVerified'] and proof['allFirstResourcesActuallyChanged'] and proof['sourcePackageUnchanged']
        rows.append({'track': track, 'firstPreparation': a, 'firstAfterMutation': mutated, 'secondPreparation': z, 'proof': proof})
    fx = b.select_external_fixture('posting', reg)
    (package / 'posting/DALYTRAN').write_bytes(b'ADULTERATED AFTER SELECTION')
    rejected = out / 'rejected'; rejected.mkdir()
    try:
        b.materialize_fixture(fx, rejected)
    except b.FixtureConfigError as exc:
        negative = {'rejected': True, 'reason': str(exc), 'noResourcesWritten': not any(rejected.iterdir())}
    else:
        raise AssertionError('Tampered source accepted')
    assert negative['noResourcesWritten']
    report = {'kind': 'technical-resource-reset-and-negative-QA-not-campaign', 'tracks': rows, 'negative': negative}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'report': str(out / 'report.json'), 'resetVerifiedTracks': [r['track'] for r in rows], 'negative': negative}, indent=2))


if __name__ == '__main__':
    main()

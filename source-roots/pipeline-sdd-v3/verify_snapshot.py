"""Check archived base integrity and report candidate drift; no writes."""
import hashlib
import json
from pathlib import Path


def digest(path):
    if path.is_symlink() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(tree, expected):
    actual = {str(p.relative_to(tree)) for p in tree.rglob('*') if p.is_file() or p.is_symlink()}
    return {
        'missing': sorted(set(expected) - actual),
        'added': sorted(actual - set(expected)),
        'changed': sorted(name for name in actual & set(expected)
                          if digest(tree / name) != expected[name]),
    }


def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / 'provenance.json').read_text())
    expected = {item['path']: item['sha256'] for item in manifest['files']}
    if len(expected) != len(manifest['files']):
        raise ValueError('Duplicate manifest paths')
    if any(Path(name).is_absolute() or '..' in Path(name).parts for name in expected):
        raise ValueError('Unsafe manifest path')
    baseline = inspect(root / 'baseline', expected)
    candidate = inspect(root / 'pipeline', expected)
    source_mismatches = sorted(name for name, value in expected.items()
                               if digest(Path(manifest['source']) / name) != value)
    ok = not any(baseline.values()) and not source_mismatches
    print(json.dumps({'ok': ok, 'files_per_manifest': len(expected),
                      'baseline': baseline, 'candidate_diff': candidate,
                      'source_mismatches': source_mismatches,
                      'methodological_approval': False}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())

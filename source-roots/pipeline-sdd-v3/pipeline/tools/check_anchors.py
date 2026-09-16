"""Mechanical source anchoring only. Never grants human gate approval."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def validate_register(register):
    if not isinstance(register, dict) or not isinstance(register.get('items'), list) or not register['items']:
        raise ValueError('nonempty items list required')
    seen = set()
    for item in register['items']:
        if not isinstance(item, dict):
            raise ValueError('evidence entry must be an object')
        eid = item.get('id')
        if not isinstance(eid, str) or not re.fullmatch(r'E-[1-9][0-9]*', eid) or eid in seen:
            raise ValueError('invalid or duplicate evidence identifier')
        seen.add(eid)
        if not isinstance(item.get('spec_section'), str) or not item['spec_section'].strip():
            raise ValueError('spec_section required')
        if not isinstance(item.get('anchors'), list) or not item['anchors']:
            raise ValueError('nonempty anchors required')
        for anchor in item['anchors']:
            if (not isinstance(anchor, dict) or not isinstance(anchor.get('path'), str)
                    or type(anchor.get('start')) is not int or type(anchor.get('end')) is not int):
                raise ValueError('anchor requires path and integer start/end')


def relative_name(value):
    if (not isinstance(value, str) or not value or '\\' in value or ':' in value
            or '\x00' in value or any(part in ('', '.', '..') for part in value.split('/'))):
        raise ValueError('invalid corpus-relative path')
    return value


def load_sources(corpus, manifest):
    if not isinstance(manifest, dict) or not isinstance(manifest.get('files'), list) or not manifest['files']:
        raise ValueError('nonempty manifest files required')
    if corpus.is_symlink() or not corpus.is_dir():
        raise ValueError('corpus must be a real directory')
    root = corpus.resolve()
    approved = {}
    for entry in manifest['files']:
        if not isinstance(entry, dict):
            raise ValueError('manifest entry must be an object')
        name = relative_name(entry.get('path'))
        sha = entry.get('sha256')
        if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{64}', sha):
            raise ValueError('sha256 must be 64 lowercase hex characters')
        if name in approved:
            raise ValueError('duplicate manifest path: ' + name)
        path = root
        for part in name.split('/'):
            path = path / part
            if path.is_symlink():
                raise ValueError('symlink forbidden: ' + name)
        path.resolve().relative_to(root)
        if not path.is_file():
            raise ValueError('missing source file: ' + name)
        approved[name] = (path, sha, entry.get('encoding', 'utf-8'))
    sources, errors = {}, []
    for name, (path, sha, encoding) in approved.items():
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != sha:
            errors.append('source hash mismatch: ' + name)
        sources[name] = raw.decode(encoding).splitlines()
    return sources, errors


def check(corpus, manifest, register):
    validate_register(register)
    sources, errors = load_sources(corpus, manifest)
    for item in register['items']:
        for anchor in item['anchors']:
            relative_name(anchor['path'])
            lines = sources.get(anchor['path'])
            if lines is None:
                errors.append('anchor outside manifest: ' + anchor['path'])
            elif not 1 <= anchor['start'] <= anchor['end'] <= len(lines):
                errors.append('anchor range out of bounds: ' + item['id'])
    return {'ok': not errors, 'errors': errors,
            'evidence_checked': len(register['items']), 'human_approval': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('corpus', type=Path)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('register', type=Path)
    args = parser.parse_args()
    try:
        result = check(args.corpus, json.loads(args.manifest.read_text()),
                       json.loads(args.register.read_text()))
    except (ValueError, OSError, KeyError, TypeError, LookupError) as exc:
        result = {'ok': False, 'errors': [str(exc)], 'evidence_checked': 0, 'human_approval': False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

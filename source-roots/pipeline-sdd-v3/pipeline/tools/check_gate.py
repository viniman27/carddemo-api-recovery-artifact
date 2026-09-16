"""Check freshness of recorded reviews; never approve, sign or execute a gate."""
import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path


TYPES = ['pipeline-scope', 'capability-selection', 'legacy-evidence',
         'capability-semantics', 'canonical-data-boundary', 'api-contract',
         'adapter-behavior', 'semantic-validation',
         'implementation-executable-qualification']
CONTEXT = ('run_id', 'capability', 'pipeline_stage', 'artifact_type')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def local_file(root, name):
    require(isinstance(name, str) and bool(name) and not any(c in name for c in ('\\', ':', '\x00')), 'invalid relative path')
    require(all(p not in ('', '.', '..') for p in name.split('/')), 'invalid relative path')
    require(root.is_dir() and not root.is_symlink(), 'run root must be a real directory')
    root = root.resolve()
    path = root
    for part in name.split('/'):
        path = path / part
        require(not path.is_symlink(), 'symlink forbidden: ' + name)
    path.resolve().relative_to(root)
    require(path.is_file(), 'missing file: ' + name)
    return path


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key: ' + key)
        result[key] = value
    return result


def read_spec(root, name):
    return json.loads(local_file(root, name).read_text(encoding='utf-8'), object_pairs_hook=unique_object)


def inspect_gate(root, name, stack=()):
    if name in stack:
        return {'status': 'invalid', 'reasons': ['cyclic upstream dependency: ' + name]}
    spec = read_spec(root, name)
    require(isinstance(spec, dict), 'spec must be an object')
    stage = spec.get('pipeline_stage')
    require(type(stage) is int and 1 <= stage <= len(TYPES), f'pipeline_stage must be 1..{len(TYPES)}')
    require(spec.get('artifact_type') == TYPES[stage - 1], 'artifact_type does not match stage')
    for key in ('run_id', 'capability', 'artifact_path'):
        require(isinstance(spec.get(key), str) and bool(spec[key].strip()), key + ' required')
    upstream = spec.get('upstream_specs')
    require(isinstance(upstream, list) and all(isinstance(p, str) for p in upstream), 'upstream_specs must be paths')
    require(len(upstream) == len(set(upstream)), 'duplicate upstream path')
    require((stage == 1 and not upstream) or (stage > 1 and bool(upstream)), 'stage requires predecessor chain')
    gate = spec['gate']
    require(isinstance(gate, dict), 'gate must be an object')
    require(type(gate.get('completeness_gate_passed')) is bool, 'completeness flag must be boolean')
    require(isinstance(gate.get('blocking_gaps'), list), 'blocking_gaps must be a list')
    review = gate.get('review')
    if gate.get('completeness_gate_passed') is not True or not review:
        return {'status': 'unreviewed', 'reasons': ['no completed review record']}
    if gate.get('blocking_gaps'):
        return {'status': 'blocked', 'reasons': ['blocking gaps remain']}
    date.fromisoformat(gate['gate_review_date'])
    require(isinstance(review, dict), 'review must be an object')
    require(isinstance(review.get('reviewer'), str) and bool(review['reviewer'].strip()), 'reviewer required')
    require(isinstance(review.get('context'), dict), 'review context required')
    require(type(review['context'].get('pipeline_stage')) is int, 'review stage must be integer')
    if review['context'] != {key: spec[key] for key in CONTEXT} or review['artifact']['path'] != spec['artifact_path']:
        return {'status': 'stale', 'reasons': ['reviewed context or artifact identity changed']}
    require(isinstance(review.get('upstream_specs'), list), 'review upstream pins required')
    if [pin['path'] for pin in review['upstream_specs']] != upstream:
        return {'status': 'stale', 'reasons': ['declared upstream differs from reviewed inputs']}
    if review['decision'] != 'approve':
        return {'status': 'unreviewed', 'reasons': ['recorded decision is not approve']}
    for pin in [review['artifact'], review['authorization']] + review['upstream_specs']:
        require(isinstance(pin, dict), 'pin must be an object')
        require(isinstance(pin.get('sha256'), str) and re.fullmatch(r'[0-9a-f]{64}', pin['sha256']), 'invalid SHA-256 format')
        raw = local_file(root, pin['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != pin['sha256']:
            return {'status': 'stale', 'reasons': ['changed: ' + pin['path']]}
    predecessor_found = stage == 1
    for pin in review['upstream_specs']:
        parent = read_spec(root, pin['path'])
        require(isinstance(parent, dict), 'upstream spec must be an object')
        require(parent.get('run_id') == spec['run_id'] and parent.get('capability') == spec['capability'], 'upstream run/capability mismatch')
        previous_stage = parent.get('pipeline_stage')
        require(type(previous_stage) is int and 1 <= previous_stage < stage, 'upstream must be an earlier stage')
        predecessor_found = predecessor_found or previous_stage == stage - 1
        result = inspect_gate(root, pin['path'], stack + (name,))
        if result['status'] != 'current':
            result['reasons'].insert(0, 'upstream: ' + pin['path'])
            return result
    require(predecessor_found, 'immediate predecessor stage missing')
    return {'status': 'current', 'reasons': []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_root', type=Path)
    parser.add_argument('spec', help='Exact path relative to RUN_ROOT')
    args = parser.parse_args()
    try:
        result = inspect_gate(args.run_root, args.spec)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        result = {'status': 'invalid', 'reasons': [str(exc)]}
    result['human_approval_granted'] = False
    result['ok'] = result['status'] == 'current'
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

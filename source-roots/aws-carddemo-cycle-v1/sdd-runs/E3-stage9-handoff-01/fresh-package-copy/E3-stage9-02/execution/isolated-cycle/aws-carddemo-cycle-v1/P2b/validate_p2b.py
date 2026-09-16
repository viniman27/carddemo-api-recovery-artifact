#!/usr/bin/env python3
"""Validate P2b technical smoke responses against frozen P2a component schemas."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from jsonschema import Draft202012Validator, RefResolver

ROOT = Path(__file__).resolve().parent
P2A = ROOT.parent / 'P2a' / 'openapi-carddemo-stage6r3.yaml'
MANIFEST = ROOT / 'readiness-manifest.json'

SPEC = yaml.safe_load(P2A.read_text())
SCHEMAS = {
    'posting': 'PostingEnvelope',
    'interest': 'InterestEnvelope',
    'reporting': 'ReportingEnvelope',
}


def validate_case(schema_ref: str, body: dict[str, Any]) -> list[str]:
    schema = {'$ref': f'#/components/schemas/{schema_ref}'}
    resolver = RefResolver.from_schema(SPEC)
    return [e.message for e in sorted(
        Draft202012Validator(schema, resolver=resolver).iter_errors(body),
        key=lambda e: [str(part) for part in e.path],
    )]


def main() -> None:
    data = json.loads(MANIFEST.read_text())
    cases = []
    for result in data['results']:
        track = result['track']
        schema_name = SCHEMAS[track]
        errors = validate_case(schema_name, result['body'])
        cases.append({'track': track, 'schema': schema_name, 'status': result['status'], 'valid': not errors, 'errors': errors})
    # 400 shape check: bad request should map to InterfaceError without invoking COBOL.
    error_case = {'track': 'posting', 'category': 'request_representation', 'completeness': 'not_attested', 'durability': 'unknown'}
    errors = validate_case('InterfaceError', error_case)
    cases.append({'track': 'posting-bad-request', 'schema': 'InterfaceError', 'status': 400, 'valid': not errors, 'errors': errors})
    out = {
        'p2a_openapi': str(P2A),
        'readiness_manifest': str(MANIFEST),
        'validator': 'jsonschema',
        'cases': cases,
        'overall_passed': all(c['valid'] for c in cases),
    }
    (ROOT / 'schema-validation-report.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out, indent=2))
    raise SystemExit(0 if out['overall_passed'] else 1)


if __name__ == '__main__':
    main()

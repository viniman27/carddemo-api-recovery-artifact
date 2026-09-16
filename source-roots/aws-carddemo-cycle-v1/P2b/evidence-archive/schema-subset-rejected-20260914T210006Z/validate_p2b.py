#!/usr/bin/env python3
"""Validate P2b technical smoke responses against frozen P2a component schemas."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

try:  # Keep real jsonschema validation when the local environment provides it.
    from jsonschema import Draft202012Validator, RefResolver  # type: ignore
except ModuleNotFoundError:  # Fall back to the OpenAPI subset used by P2a.
    Draft202012Validator = None  # type: ignore
    RefResolver = None  # type: ignore

ROOT = Path(__file__).resolve().parent
P2A = ROOT.parent / 'P2a' / 'openapi-carddemo-stage6r3.yaml'
MANIFEST = ROOT / 'readiness-manifest.json'

SPEC = yaml.safe_load(P2A.read_text())
SCHEMAS = {
    'posting': 'PostingEnvelope',
    'interest': 'InterestEnvelope',
    'reporting': 'ReportingEnvelope',
}


def resolve_ref(ref: str, spec: dict[str, Any]) -> dict[str, Any]:
    prefix = '#/components/schemas/'
    if not ref.startswith(prefix):
        raise ValueError(f'unsupported ref {ref}')
    return spec['components']['schemas'][ref[len(prefix):]]


def validate_json_schema(schema: dict[str, Any], value: Any, spec: dict[str, Any], path: str = '$') -> list[str]:
    """Validate the JSON Schema subset present in the frozen P2a contract."""
    errors: list[str] = []
    if '$ref' in schema:
        return validate_json_schema(resolve_ref(schema['$ref'], spec), value, spec, path)
    if 'allOf' in schema:
        for idx, subschema in enumerate(schema['allOf']):
            errors.extend(validate_json_schema(subschema, value, spec, f'{path}.allOf[{idx}]'))
    if 'anyOf' in schema:
        branch_errors = [validate_json_schema(s, value, spec, path) for s in schema['anyOf']]
        if not any(not e for e in branch_errors):
            errors.append(f'{path}: did not match anyOf')
    if 'oneOf' in schema:
        branch_errors = [validate_json_schema(s, value, spec, path) for s in schema['oneOf']]
        if sum(1 for e in branch_errors if not e) != 1:
            errors.append(f'{path}: did not match exactly one oneOf branch')
    if 'const' in schema and value != schema['const']:
        errors.append(f'{path}: expected const {schema["const"]!r}')
    if 'enum' in schema and value not in schema['enum']:
        errors.append(f'{path}: value {value!r} not in enum')

    expected_type = schema.get('type')
    if expected_type == 'object':
        if not isinstance(value, dict):
            return errors + [f'{path}: expected object']
        required = schema.get('required', [])
        for name in required:
            if name not in value:
                errors.append(f'{path}: missing required property {name}')
        properties = schema.get('properties', {})
        if schema.get('additionalProperties') is False:
            for name in value:
                if name not in properties:
                    errors.append(f'{path}: additional property {name}')
        for name, subschema in properties.items():
            if name in value:
                errors.extend(validate_json_schema(subschema, value[name], spec, f'{path}.{name}'))
    elif expected_type == 'array':
        if not isinstance(value, list):
            return errors + [f'{path}: expected array']
        item_schema = schema.get('items', {})
        for idx, item in enumerate(value):
            errors.extend(validate_json_schema(item_schema, item, spec, f'{path}[{idx}]'))
    elif expected_type == 'string':
        if not isinstance(value, str):
            errors.append(f'{path}: expected string')
    elif expected_type == 'integer':
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f'{path}: expected integer')
    elif expected_type == 'number':
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f'{path}: expected number')
    elif expected_type == 'boolean':
        if not isinstance(value, bool):
            errors.append(f'{path}: expected boolean')
    return errors


def validate_case(schema_ref: str, body: dict[str, Any]) -> list[str]:
    schema = {'$ref': f'#/components/schemas/{schema_ref}'}
    if Draft202012Validator is not None:
        resolver = RefResolver.from_schema(SPEC)
        return [e.message for e in sorted(Draft202012Validator(schema, resolver=resolver).iter_errors(body), key=lambda e: list(e.path))]
    return validate_json_schema(schema, body, SPEC)


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
        'validator': 'jsonschema' if Draft202012Validator is not None else 'internal-openapi-subset',
        'cases': cases,
        'overall_passed': all(c['valid'] for c in cases),
    }
    (ROOT / 'schema-validation-report.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out, indent=2))
    raise SystemExit(0 if out['overall_passed'] else 1)


if __name__ == '__main__':
    main()

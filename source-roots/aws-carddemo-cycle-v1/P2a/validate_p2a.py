#!/usr/bin/env python3
import json, subprocess, hashlib, sys
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator, RefResolver, ValidationError
from openapi_spec_validator import validate

P2A = Path(__file__).resolve().parent
ROOT = Path('<REDACTED_LOCAL_PATH>')
CYCLE = ROOT/'casos/aws-carddemo-cycle-v1'
RUN = CYCLE/'sdd-runs/E3-01'
OAS_YAML = P2A/'openapi-carddemo-stage6r3.yaml'
OAS_JSON = P2A/'openapi-carddemo-stage6r3.json'
INPUTS = [
    RUN/'specs/api-contract-carddemo-r3/requirements.md',
    RUN/'specs/adapter-behavior-carddemo-r2/requirements.md',
    CYCLE/'POST-PIPELINE-READINESS.md',
    CYCLE/'PROTOCOLO.md',
    ROOT/'WORKSPACE-NOTES.md',
]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def run(cmd):
    p = subprocess.run(cmd, cwd=P2A, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {'cmd': ' '.join(map(str, cmd)), 'exit_code': p.returncode, 'output': p.stdout}

spec = yaml.safe_load(OAS_YAML.read_text(encoding='utf-8'))
report = {
    'p2a_root': str(P2A),
    'input_hashes_before_validation': {str(p): sha(p) for p in INPUTS},
    'commands': [],
    'openapi_validation': [],
    'json_schema_2020_12_cases': [],
    'counts': {},
    'blockers': [],
}

# Actual OpenAPI validators available locally in the P2a venv and npx cache/transport.
for cmd in [[str(P2A/'.venv/bin/python'), '-m', 'openapi_spec_validator', str(OAS_YAML)], [str(P2A/'.venv/bin/python'), '-m', 'openapi_spec_validator', str(OAS_JSON)]]:
    out = run(cmd)
    report['commands'].append(out)
    report['openapi_validation'].append({'validator': 'openapi-spec-validator', 'target': cmd[-1], 'passed': out['exit_code'] == 0, 'output': out['output']})

# In-process validation gives a second structural check and catches Python API exceptions.
try:
    validate(spec)
    report['openapi_validation'].append({'validator':'openapi_spec_validator.validate', 'target': str(OAS_YAML), 'passed': True, 'output': 'OK'})
except Exception as e:
    report['openapi_validation'].append({'validator':'openapi_spec_validator.validate', 'target': str(OAS_YAML), 'passed': False, 'output': repr(e)})

resolver = RefResolver.from_schema(spec)

def check(schema_name, instance, expect_valid, purpose):
    schema = spec['components']['schemas'][schema_name]
    validator = Draft202012Validator(schema, resolver=resolver)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    valid = not errors
    report['json_schema_2020_12_cases'].append({
        'case': purpose,
        'schema': schema_name,
        'expected_valid': expect_valid,
        'actual_valid': valid,
        'passed': valid == expect_valid,
        'errors': [e.message for e in errors[:5]],
        'instance': instance,
    })

# Required empty object request and body-absence policy.
for req in ['PostingRequest','InterestRequest','ReportingRequest']:
    check(req, {}, True, f'{req}: empty object accepted')
    check(req, None, False, f'{req}: null body rejected')
    check(req, [], False, f'{req}: array body rejected')
    check(req, {'selector':'x'}, False, f'{req}: properties/body business fields rejected')
body_required_all = all(spec['paths'][p]['post']['requestBody']['required'] for p in ['/posting','/interest','/reporting'])
report['json_schema_2020_12_cases'].append({
    'case': 'body absence policy: OpenAPI requestBody.required is true on all operations',
    'schema': 'paths.*.post.requestBody.required',
    'expected_valid': False,
    'actual_valid': False if body_required_all else True,
    'passed': body_required_all,
    'errors': [] if body_required_all else ['At least one operation does not require requestBody'],
    'instance': 'ABSENT_BODY_SENTINEL',
    'note': 'Absence is invalid because requestBody.required is true; this is an OpenAPI operation-level rule, not a JSON instance schema.'
})

unavail_tx = {'availability':'unavailable'}
avail_tx_empty = {'availability':'available','items':[]}
unavail_bad = {'availability':'unavailable','items':[]}
for schema in ['PostingTransactionAvailability','PostingRejectionAvailability','InterestOutputAvailability','ReportRecordAvailability']:
    check(schema, avail_tx_empty, True, f'{schema}: observed empty array accepted')
    check(schema, unavail_tx, True, f'{schema}: unavailable without items accepted')
    check(schema, unavail_bad, False, f'{schema}: unavailable items forbidden')

posting_progress_only = {'track':'posting','completeness':'not_attested','durability':'unknown','outputs':unavail_tx,'rejections':unavail_tx,'progress':{'availability':'available','value':{'processedRecordCount':0,'preliminaryRejectCount':0}}}
posting_all_unavail = {'track':'posting','completeness':'not_attested','durability':'unknown','outputs':unavail_tx,'rejections':unavail_tx,'progress':{'availability':'unavailable'}}
check('PostingEnvelope', posting_progress_only, True, 'posting progress-only 200 shape accepted; not output fulfillment')
check('PostingEnvelope', posting_all_unavail, False, 'posting all-unavailable envelope barred from 200/availableContent')

interest_empty = {'track':'interest','completeness':'not_attested','durability':'unknown','outputs':avail_tx_empty}
interest_unavail = {'track':'interest','completeness':'not_attested','durability':'unknown','outputs':unavail_tx}
check('InterestEnvelope', interest_empty, True, 'interest observed empty outputs accepted')
check('InterestEnvelope', interest_unavail, False, 'interest unavailable outputs forbidden for 200/availableContent')

reporting_empty = {'track':'reporting','completeness':'not_attested','durability':'unknown','records':avail_tx_empty}
reporting_unavail = {'track':'reporting','completeness':'not_attested','durability':'unknown','records':unavail_tx}
check('ReportingEnvelope', reporting_empty, True, 'reporting observed empty records accepted')
check('ReportingEnvelope', reporting_unavail, False, 'reporting unavailable records forbidden for 200/availableContent')

knownfailure_avail = {'track':'interest','category':'technical_failure','completeness':'not_attested','durability':'unknown','availableContent': interest_empty}
knownfailure_bad = {'track':'posting','category':'technical_failure','completeness':'not_attested','durability':'unknown','availableContent': posting_all_unavail}
check('InterfaceError', knownfailure_avail, True, 'knownfailure availableContent accepts available empty observation')
check('InterfaceError', knownfailure_bad, False, 'knownfailure availableContent rejects all-unavailable envelope')
check('InterfaceError', {'track':'reporting','category':'content_unavailable','completeness':'not_attested','durability':'unknown'}, True, '503 content_unavailable carries no substantive observation')
check('PostingRejection', {'candidate':{k:'x' for k in ['transactionId','typeCode','categoryCode','source','description','amount','merchantId','merchantName','merchantCity','merchantPostalText','cardReference','originalTimestamp','suppliedProcessingTimestamp']}, 'reason':'109','description':'x'}, False, 'reason 109 remains nonpublic/forbidden')
check('InterestEnvelope', {'track':'interest','completeness':'not_attested','durability':'unknown','outputs':avail_tx_empty,'extra':'x'}, False, 'closed objects reject unknown fields')

report['counts'] = {
    'paths': len(spec['paths']),
    'operations': sum(len(v) for v in spec['paths'].values()),
    'component_schemas': len(spec['components']['schemas']),
    'json_schema_cases': len(report['json_schema_2020_12_cases']),
    'json_schema_cases_passed': sum(1 for c in report['json_schema_2020_12_cases'] if c['passed']),
    'openapi_validator_checks': len(report['openapi_validation']),
    'openapi_validator_checks_passed': sum(1 for c in report['openapi_validation'] if c['passed']),
}
report['input_hashes_after_validation'] = {str(p): sha(p) for p in INPUTS}
report['input_hashes_unchanged'] = report['input_hashes_before_validation'] == report['input_hashes_after_validation']
report['overall_passed'] = report['input_hashes_unchanged'] and all(c['passed'] for c in report['openapi_validation']) and all(c['passed'] for c in report['json_schema_2020_12_cases'])
(P2A/'validation-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps({'overall_passed': report['overall_passed'], 'counts': report['counts'], 'report': str(P2A/'validation-report.json')}, indent=2))
sys.exit(0 if report['overall_passed'] else 1)

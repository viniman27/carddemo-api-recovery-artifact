#!/usr/bin/env python3
import json, hashlib, subprocess, sys, os, textwrap
from pathlib import Path
import yaml

ROOT = Path('<REDACTED_LOCAL_PATH>')
CYCLE = ROOT/'casos/aws-carddemo-cycle-v1'
RUN = CYCLE/'sdd-runs/E3-01'
P2A = CYCLE/'P2a'
P2A.mkdir(parents=True, exist_ok=True)
STAGE6 = RUN/'specs/api-contract-carddemo-r3/requirements.md'
STAGE7 = RUN/'specs/adapter-behavior-carddemo-r2/requirements.md'
POST = CYCLE/'POST-PIPELINE-READINESS.md'
PROTO = CYCLE/'PROTOCOLO.md'
AGENT_NOTES = ROOT/'WORKSPACE-NOTES.md'
inputs = [STAGE6, STAGE7, POST, PROTO, AGENT_NOTES]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
input_hashes_before = {str(p): sha(p) for p in inputs}

S6 = 'sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md'
S7 = 'sdd-runs/E3-01/specs/adapter-behavior-carddemo-r2/requirements.md'

def tr(clause, source, note):
    return {'source': source, 'clause': clause, 'note': note}

def obj(required, props, trace, extra=False):
    return {'type':'object','additionalProperties':extra,'required':required,'properties':props,'x-traceability':trace}

def sfield(name, clauses):
    return {'type':'string','x-traceability':tr(clauses,S6,f'{name}: string representation; no regex/length/coercion invented')}

def ifield(name, clauses):
    return {'type':'integer','x-traceability':tr(clauses,S6,f'{name}: integer progress count only')}

candidate_fields = ['transactionId','typeCode','categoryCode','source','description','amount','merchantId','merchantName','merchantCity','merchantPostalText','cardReference','originalTimestamp','suppliedProcessingTimestamp']
transaction_fields = ['transactionId','typeCode','categoryCode','source','description','amount','merchantId','merchantName','merchantCity','merchantPostalText','cardReference','originalTimestamp','processingTimestamp']
report_detail_fields = ['transactionId','accountReference','typeCode','typeDescription','categoryCode','categoryDescription','source','amountText']
header_fields = ['reportShortNameText','reportLongNameText','startText','endText']

def avail_schema(name, item_ref, clauses):
    return {
        'oneOf':[
            obj(['availability','items'],{
                'availability':{'const':'available','x-traceability':tr(clauses,S6,'Available means actual represented observation; items may be empty')},
                'items':{'type':'array','items':{'$ref':item_ref},'x-traceability':tr(clauses,S6,'Ordered array; duplicates retained; no minItems')}
            },tr(clauses,S6,f'{name} available variant')),
            obj(['availability'],{
                'availability':{'const':'unavailable','x-traceability':tr(clauses,S6,'Unavailable has no items property')}
            },tr(clauses,S6,f'{name} unavailable variant'))
        ],
        'x-traceability':tr(clauses,S6,f'{name} availability oneOf; unavailable items forbidden')
    }

progress_avail = {
    'oneOf':[
        obj(['availability','value'],{'availability':{'const':'available'},'value':{'$ref':'#/components/schemas/PostingProgress'}},tr('§3.4/C-5/D-16',S6,'Progress available, including zero counts')),
        obj(['availability'],{'availability':{'const':'unavailable'}},tr('§3.4/C-5/D-16',S6,'Progress unavailable omits value')),
    ],
    'x-traceability':tr('§3.4/C-5/D-16',S6,'Posting progress availability')
}

components = {}
for req in ['PostingRequest','InterestRequest','ReportingRequest']:
    components[req]=obj([],{},tr('§3.4 Requests/D-14/C-9',S6,'Required empty closed JSON object; missing body/null/array/properties invalid'))
components['PostingCandidate']=obj(candidate_fields,{f:sfield(f,'§3.2/C-5/D-11') for f in candidate_fields},tr('§3.2/C-5',S6,'Posting candidate/source daily fields'))
components['PostingTransaction']=obj(transaction_fields,{f:sfield(f,'§3.2/C-5/D-11') for f in transaction_fields},tr('§3.2/C-5',S6,'Prepared posted transaction fields'))
components['PostingRejection']=obj(['candidate','reason','description'],{
    'candidate':{'$ref':'#/components/schemas/PostingCandidate','x-traceability':tr('§3.2/C-5',S6,'Rejection retains original candidate context')},
    'reason':{'type':'string','enum':['100','101','102','103'],'x-traceability':tr('§3.2/C-5',S6,'Preliminary rejection reasons only; 109 remains internal')},
    'description':sfield('description','§3.2/C-5')
},tr('§3.2/C-5',S6,'Posting rejection content'))
components['PostingProgress']=obj(['processedRecordCount','preliminaryRejectCount'],{
    'processedRecordCount':ifield('processedRecordCount','§3.2/C-5/D-16'),
    'preliminaryRejectCount':ifield('preliminaryRejectCount','§3.2/C-5/D-16')
},tr('§3.2/C-5/D-16',S6,'Progress counts; not committed/durable output counts'))
components['InterestCategoryBasis']=obj(['accountReference','typeCode','categoryCode','categoryBalance'],{f:sfield(f,'§3.2/C-6') for f in ['accountReference','typeCode','categoryCode','categoryBalance']},tr('§3.2/C-6',S6,'External description only; not request'))
components['InterestIdentifierBasis']=obj(['parameterText'],{'parameterText':sfield('parameterText','§3.2/C-6')},tr('§3.2/C-6',S6,'External identifier basis only; not request'))
components['GeneratedInterestTransaction']=obj(transaction_fields,{f:sfield(f,'§3.2/C-6/D-11') for f in transaction_fields},tr('§3.2/C-6',S6,'Generated interest transaction fields; no fee/suffix public'))
components['ReportingTransactionBasis']=obj(['transactionId','cardReference','typeCode','categoryCode','source','amount','processingTimestamp'],{f:sfield(f,'§3.3') for f in ['transactionId','cardReference','typeCode','categoryCode','source','amount','processingTimestamp']},tr('§3.3',S6,'External description only; not request'))
components['ReportingDateBasis']=obj(['startText','endText'],{'startText':sfield('startText','§3.3'), 'endText':sfield('endText','§3.3')},tr('§3.3',S6,'External date basis only; not request'))
components['ReportDetail']=obj(report_detail_fields,{f:sfield(f,'§3.3/C-7') for f in report_detail_fields},tr('§3.3/C-7',S6,'Report receiver detail fields'))
components['ReportHeaderContext']=obj(header_fields,{f:sfield(f,'§3.3/C-7') for f in header_fields},tr('§3.3/C-7',S6,'Report header context'))
components['ReportTotal']=obj(['label','valueText'],{'label':{'type':'string','enum':['page','account','grand'],'x-traceability':tr('§3.3/C-8',S6,'Source-labelled totals only')},'valueText':sfield('valueText','§3.3/C-7/C-8')},tr('§3.3/C-7/C-8',S6,'Report total occurrence'))
components['ReportRecord']={'oneOf':[obj(['kind','value'],{'kind':{'const':'header'},'value':{'$ref':'#/components/schemas/ReportHeaderContext'}},tr('§3.4/C-7/C-8',S6,'Header record')),obj(['kind','value'],{'kind':{'const':'detail'},'value':{'$ref':'#/components/schemas/ReportDetail'}},tr('§3.4/C-7/C-8',S6,'Detail record')),obj(['kind','value'],{'kind':{'const':'total'},'value':{'$ref':'#/components/schemas/ReportTotal'}},tr('§3.4/C-7/C-8',S6,'Total record'))],'x-traceability':tr('§3.4/C-7/C-8/D-15',S6,'Mixed ordered reporting records union')}
components['PostingTransactionAvailability']=avail_schema('PostingTransactionAvailability','#/components/schemas/PostingTransaction','§3.4/D-15/D-16')
components['PostingRejectionAvailability']=avail_schema('PostingRejectionAvailability','#/components/schemas/PostingRejection','§3.4/C-5/D-16')
components['InterestOutputAvailability']=avail_schema('InterestOutputAvailability','#/components/schemas/GeneratedInterestTransaction','§3.4/C-6/D-16')
components['ReportRecordAvailability']=avail_schema('ReportRecordAvailability','#/components/schemas/ReportRecord','§3.4/C-8/D-16')
components['ProgressAvailability']=progress_avail
components['PostingEnvelope']=obj(['track','completeness','durability','outputs','rejections','progress'],{
    'track':{'const':'posting'}, 'completeness':{'const':'not_attested'}, 'durability':{'const':'unknown'},
    'outputs':{'$ref':'#/components/schemas/PostingTransactionAvailability'}, 'rejections':{'$ref':'#/components/schemas/PostingRejectionAvailability'}, 'progress':{'$ref':'#/components/schemas/ProgressAvailability'}
},tr('§3.4/D-16/C-10/C-12',S6,'Posting envelope; any available outputs/rejections/progress required for 200'), False)
components['PostingEnvelope']['anyOf']=[{'properties':{'outputs':{'properties':{'availability':{'const':'available'}}}}},{'properties':{'rejections':{'properties':{'availability':{'const':'available'}}}}},{'properties':{'progress':{'properties':{'availability':{'const':'available'}}}}}]
components['InterestEnvelope']=obj(['track','completeness','durability','outputs'],{'track':{'const':'interest'},'completeness':{'const':'not_attested'},'durability':{'const':'unknown'},'outputs':{'$ref':'#/components/schemas/InterestOutputAvailability'}},tr('§3.4/D-16/C-11/C-12',S6,'Interest envelope; outputs available required for 200'),False)
components['InterestEnvelope']['properties']['outputs']['allOf']=[{'$ref':'#/components/schemas/InterestOutputAvailability'},{'properties':{'availability':{'const':'available'}}}]
# avoid sibling ref issues by replacing ref-only with allOf above not ideal; use simpler schema construct
components['InterestEnvelope']['properties']['outputs']={'allOf':[{'$ref':'#/components/schemas/InterestOutputAvailability'},{'properties':{'availability':{'const':'available'}}}], 'x-traceability':tr('§3.4/D-16',S6,'Required available outputs; items may be []')}
components['ReportingEnvelope']=obj(['track','completeness','durability','records'],{'track':{'const':'reporting'},'completeness':{'const':'not_attested'},'durability':{'const':'unknown'},'records':{'allOf':[{'$ref':'#/components/schemas/ReportRecordAvailability'},{'properties':{'availability':{'const':'available'}}}], 'x-traceability':tr('§3.4/D-16',S6,'Required available records; items may be []')}},tr('§3.4/D-16/C-8/C-12',S6,'Reporting envelope; records available required for 200'),False)

def error_schema(track, env):
    return obj(['track','category','completeness','durability'],{
        'track':{'const':track},'category':{'type':'string','enum':['request_representation','technical_failure','content_unavailable']},'completeness':{'const':'not_attested'},'durability':{'const':'unknown'},'availableContent':{'$ref':f'#/components/schemas/{env}','x-traceability':tr('§3.4/C-12/D-16',S6,'Optional only when corresponding envelope has at least one actual available observation')}
    },tr('§3.4/§5/C-12/D-13/D-16',S6,f'{track} error envelope; known failure 500 precedence; no internal diagnostics'))
components['PostingInterfaceError']=error_schema('posting','PostingEnvelope')
components['InterestInterfaceError']=error_schema('interest','InterestEnvelope')
components['ReportingInterfaceError']=error_schema('reporting','ReportingEnvelope')
components['InterfaceError']={'oneOf':[{'$ref':'#/components/schemas/PostingInterfaceError'},{'$ref':'#/components/schemas/InterestInterfaceError'},{'$ref':'#/components/schemas/ReportingInterfaceError'}], 'x-traceability':tr('§3.4/§5/C-12',S6,'Track-specific interface errors')}

responses = lambda env: {'200':{'description':'Permitted observation available; no known technical failure','content':{'application/json':{'schema':{'$ref':f'#/components/schemas/{env}'}}},'x-traceability':tr('§5.2/C-12/D-16',S6,'200 observation boundary, no minItems')},'400':{'description':'Request representation mismatch','content':{'application/json':{'schema':{'$ref':'#/components/schemas/InterfaceError'}}},'x-traceability':tr('§5.2/C-9/C-12',S6,'400 request_representation only')},'500':{'description':'Known technical failure at response boundary','content':{'application/json':{'schema':{'$ref':'#/components/schemas/InterfaceError'}}},'x-traceability':tr('§5.2/C-12/D-13',S6,'Known failure precedence over 200/503; may include availableContent')},'503':{'description':'No representable observation and no known technical failure','content':{'application/json':{'schema':{'$ref':'#/components/schemas/InterfaceError'}}},'x-traceability':tr('§5.2/C-12/D-16',S6,'content_unavailable none; not observed empty')}}

paths={}
for route,op,req,env,clauses in [('/posting','posting','PostingRequest','PostingEnvelope','C-1/C-5/C-9/C-10/C-12-C-14'),('/interest','interest','InterestRequest','InterestEnvelope','C-2/C-6/C-9/C-11-C-14'),('/reporting','reporting','ReportingRequest','ReportingEnvelope','C-3/C-7-C-9/C-12-C-14')]:
    paths[route]={'post':{'operationId':op,'summary':op,'requestBody':{'required':True,'content':{'application/json':{'schema':{'$ref':f'#/components/schemas/{req}'}}},'x-traceability':tr('§3.4 Requests/D-14',S6,'Body required; empty closed JSON object only')},'responses':responses(env),'x-traceability':tr(clauses,S6,f'{op} operation; no selector/reset/polling/telemetry/default business fields'),'tags':[op]}}
openapi={'openapi':'3.1.0','info':{'title':'AWS CardDemo E3-01 SDD Stage6r3 Mechanical Contract','version':'p2a-2026-09-14','description':'Mechanical OpenAPI 3.1 materialization of approved Stage 6 r3 only; no runtime binding or semantic execution claim.','x-traceability':tr('Purpose/Contract Integrity Discipline',S6,'Materialized without source/spec semantic edits')},'jsonSchemaDialect':'https://json-schema.org/draft/2020-12/schema','paths':paths,'components':{'schemas':components},'x-traceability':{'approved_inputs':input_hashes_before,'stage6':str(STAGE6),'stage7':str(STAGE7),'scope':'P2a OpenAPI + binding plan only'}}
(P2A/'openapi-carddemo-stage6r3.yaml').write_text(yaml.safe_dump(openapi, sort_keys=False, allow_unicode=True), encoding='utf-8')
(P2A/'openapi-carddemo-stage6r3.json').write_text(json.dumps(openapi, indent=2, ensure_ascii=False), encoding='utf-8')

trace = {'input_hashes_before':input_hashes_before,'operation_count':3,'paths':['/posting','/interest','/reporting'],'schema_count':len(components),'mapping':[],'blocked_semantic_defaults':['authentication/authorization unspecified, not declared absent','no dataset selector/upload/reset/polling/status/readiness/idempotency/retry','no units/ranges/rounding/calendar/encoding/coercion/durability defaults','no public reason 109/file-status/internal telemetry','no runtime binding or COBOL execution claim']}
for name, schema in components.items():
    trace['mapping'].append({'component':name,'traceability':schema.get('x-traceability')})
for route, item in paths.items():
    trace['mapping'].append({'operation':item['post']['operationId'],'route':route,'traceability':item['post']['x-traceability']})
(P2A/'traceability.json').write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding='utf-8')

# Markdown mapping matrix
lines=['# P2a Traceability Mapping Matrix','',f'- Stage 6 r3: `{STAGE6}` SHA-256 `{input_hashes_before[str(STAGE6)]}`',f'- Stage 7 r2: `{STAGE7}` SHA-256 `{input_hashes_before[str(STAGE7)]}`','','| Artifact element | Source/clause | Mapping note |','|---|---|---|']
for m in trace['mapping']:
    key = m.get('component') or (m.get('operation')+' '+m.get('route'))
    t=m['traceability']; lines.append(f"| `{key}` | `{t['source']} {t['clause']}` | {t['note']} |")
(P2A/'mapping-matrix.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')

plan = f'''# P2a plan-binding — documentary binding plan only

Scope: derive binding duties from Stage 7 r2 for all three tracks without implementing, executing, compiling COBOL, reading support expected outputs, or asserting runtime behavior.

## Common duties

- INV: associate run `E3-01`, capability `unselected-stage-1-scope-only`, called operation, request-shape evidence, source/runtime binding reference, resource links, observation scope, capture channels, and response association. Internal invocation identity is not a receipt or idempotency key.
- RES: record actual resource instance identity or unresolved status, owner, origin/version, validity window, prerequisites, reuse/shared-state attribution, and missing dependencies. Never infer readiness from an empty request.
- CAP: record attributable observations, raw evidence/digest when available, capture scope/freshness/framing, represented positions, empty-observation basis, exclusions, uncertainty and destination. Zero-byte evidence is not automatically positive empty.
- CONV: for every represented field, record source span/path/pin/line, declaration, encoding/sign/framing basis, observed padding/width, mapped value, loss, and unresolved conflicts. No regex/range/rounding/calendar/coercion defaults.
- FAIL: record actual event/diagnostic, invocation attribution, meaning authority, known/unestablished boundary, retained observations, and selected existing category. Internal 109 is not public failure.
- STATE: distinguish local versus persistent resources, preparation/reuse evidence, attempted/observed/durable effects, reset/isolation evidence and repetition limits. No reset/durability/retry promise.
- RESP: bind contract version, INV, CAP/CONV/FAIL/STATE disposition, exact envelope/error fields, status rationale, occurrence-to-array index mapping, and unresolved gaps.

## Track duties

### posting
- INV/RES: bind daily candidate sequence and posting transaction/reject/xref/account/category resources; HTTP `{{}}` is only request representation.
- CAP: separate transaction, rejection, and progress observations; justify ordered arrays and duplicates per channel.
- CONV: map `PostingTransaction`, `PostingRejection.candidate`, `reason` enum 100-103 only, `description`, and progress counts from actual attributable sources.
- FAIL/RESP: 200 if outputs/rejections/progress available absent known failure; progress-only 200 remains progress only; all unavailable with no known failure is 503; known failure is 500 with optional availableContent.
- STATE: no account/category/output durability, rollback, or repetition guarantee; reason 109 remains internal.

### interest
- INV/RES: bind category sequence, identifier parameter, account/xref/disclosure/generated-output resources; do not use job literal as default.
- CAP: generated output only from actual generated transaction observations, including positive empty observation where justified.
- CONV: map generated transaction fields; preserve zero/negative quantities when observed; no fee/suffix/fallback public field.
- FAIL/RESP: available outputs including `items: []` supports 200 absent known failure; unavailable/no failure is 503; known failure is 500.
- STATE: no final flush insertion, no account-update receipt, no suffix uniqueness or repeat-safety claim.

### reporting
- INV/RES: bind transaction sequence, separate date resource, upstream selection provenance, lookup and report resources independently.
- CAP: acquire mixed report output; identify header/detail/total occurrences and excluded presentation mechanics without collapsing order/multiplicity.
- CONV: map receiver fields exactly as observed; do not restore descriptions, totals, dates, ranges, or arithmetic.
- FAIL/RESP: available records including empty observed sequence supports 200 absent known failure; unavailable/no failure is 503; known failure preserves available earlier content under 500.
- STATE: no complete empty report, full-range processing, reconciled totals, final account total, EOF storage, or executed job-flow claim.

## Still-pending deployment choices (not implemented here)

1. Adapter topology: per-call CLI wrapper, server facade, or offline harness.
2. Actual resource provisioning policy, legal data origin, encoding/framing/sign decoding, and file-instance identity.
3. Invocation isolation: new directories/resources per call versus controlled stateful sequence.
4. Capture channels and freshness/digest mechanisms for indexed, sequential, progress/display, and report outputs.
5. Failure-event taxonomy sufficient for known-failure boundary without exposing file status/internal telemetry.
6. Positive-empty evidence rule per channel, distinct from zero-byte/stale/truncated/failed capture.
7. Reset/isolation/durability evidence standard before any runtime claim.
8. Smoke fixtures allowed for development versus official T1/T2/T3/T4 oracle separation.
9. Minimum COBOL reach evidence per operation before operational claims.
10. Human gate for P2/P3 before implementation, COBOL execution, official cells, or E1/E2 comparison.
'''
(P2A/'plan-binding.md').write_text(plan, encoding='utf-8')

readme = f'''# P2a — OpenAPI materialization and binding plan

Status: working artifact created under Cycle/P2a only. It is a mechanical OpenAPI 3.1 materialization of approved Stage 6 r3 plus a documentary binding plan derived from Stage 7 r2. It is not an API server, adapter implementation, COBOL execution, official experiment, or runtime fidelity claim.

## Files

- `openapi-carddemo-stage6r3.yaml` / `.json` — OpenAPI 3.1 contract for `POST /posting`, `POST /interest`, `POST /reporting`.
- `traceability.json` — machine-readable source mapping and input hashes.
- `mapping-matrix.md` — separate traceability matrix.
- `plan-binding.md` — INV/RES/CAP/CONV/FAIL/STATE/RESP duties and pending choices.
- `validate_p2a.py` — structural/schema QA script.
- `validation-report.json` — validator commands, outputs, synthetic case results, before/after hashes.

## Limitations

- Required requests are closed empty JSON objects; body absence remains invalid by OpenAPI `requestBody.required`, not a business input policy.
- Ordered arrays are used throughout; no set/keymap representation or deduplication is introduced.
- `not_attested`, `unknown`, and `unavailable` are preserved as contract constants/variants only; they are not runtime facts.
- Authentication/authorization is unspecified, not declared absent.
- No selectors, upload/provisioning, reset, polling, retry, idempotency, telemetry, reason 109, file status, units, calendar, numeric coercion, durability, or complete reporting guarantee is added.
- No COBOL/support outputs were read or executed.
'''
(P2A/'README.md').write_text(readme, encoding='utf-8')
print(json.dumps({'created': [str(p) for p in [P2A/'openapi-carddemo-stage6r3.yaml',P2A/'openapi-carddemo-stage6r3.json',P2A/'traceability.json',P2A/'mapping-matrix.md',P2A/'plan-binding.md',P2A/'README.md']], 'input_hashes_before':input_hashes_before, 'schema_count':len(components)}, indent=2))

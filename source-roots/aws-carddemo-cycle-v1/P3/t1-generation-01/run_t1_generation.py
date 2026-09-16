#!/usr/bin/env python3
"""Authorized T1 direct provider runner for aws-carddemo-cycle-v1.

Scope: one fresh synthetic probe, then one generation per prepared T1 contract payload.
No retries, no fallback, no runtime COBOL/API calls. Persists exact outbound request
bodies, raw SSE receipts, timing, returned model and hashes.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import urllib.error
import urllib.request

REPO = Path('<REDACTED_LOCAL_PATH>')
ROOT = REPO / 'casos/aws-carddemo-cycle-v1'
P1 = ROOT / 'P1/direct-transport'
PKG = ROOT / 'P3/pre-campaign-acceptance-package-v1'
OUT = ROOT / 'P3/t1-generation-01'
MODEL = 'gpt-6-astra'
PROVIDER = 'openai-codex'
BASE_URL = 'https://chatgpt.com/backend-api/codex'
ENDPOINT = BASE_URL + '/responses'
ORDER = ['E1-1', 'E1-2', 'E1-3', 'E2-1', 'E2-2', 'E2-3', 'E3-SDD-stage6r3']

sys.path.insert(0, str(P1))
from stream_result import parse_result  # noqa: E402
sys.path.insert(0, '<REDACTED_LOCAL_PATH>/.run-cache/codex-transport')
from codex_transport.auth import resolve_codex_runtime_credentials  # noqa: E402


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def atomic_append_jsonl(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(data, ensure_ascii=False, sort_keys=True) + '\n')


def fail(message: str, extra: dict[str, Any] | None = None) -> None:
    summary = load_summary()
    summary['finishedUtc'] = now()
    summary['status'] = 'blocked'
    summary['blocker'] = message
    if extra:
        summary.setdefault('blockerDetail', {}).update(extra)
    write_json(OUT / 'summary.json', summary)
    print(json.dumps({'status': 'blocked', 'blocker': message, **(extra or {})}, ensure_ascii=False, indent=2))
    raise SystemExit(2)


def init_summary() -> dict[str, Any]:
    return {
        'kind': 't1-generation-01-summary',
        'startedUtc': now(),
        'workspace': str(ROOT),
        'outputRoot': str(OUT),
        'authorization': {
            'realConsentRecorded': True,
            'source': 'delegated task context: user replied “Pode prosseguir” to parent authorization question',
            'scope': 'one fresh synthetic probe and, if passed, exactly one T1 provider call per prepared contract via openai-codex gpt-6-astra; no temperature/max_output_tokens/seed; no retry/fallback/switch; send only contracts/instruction/metadata',
            'notClaimed': 'signature, campaign runtime authorization, T2/T3/T4 authorization, export of main study/personal/fixture/oracle material'
        },
        'provider': PROVIDER,
        'modelRequested': MODEL,
        'endpoint': ENDPOINT,
        'transport': {'stream': True, 'store': False, 'tools': [], 'previous_response_id': None, 'follow_redirects': False},
        'order': ORDER,
        'counts': {'expectedContracts': 7, 'probeCompleted': 0, 'complete': 0, 'invalid': 0, 'interrupted': 0, 'blocked': 0},
        'items': []
    }


def load_summary() -> dict[str, Any]:
    path = OUT / 'summary.json'
    if path.exists():
        return read_json(path)
    return init_summary()


def verify_pins() -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = read_json(PKG / 'MANIFEST.json')
    report = read_json(PKG / 'REPORT.json')
    if not report.get('verify_ok') or not report.get('self_test_ok'):
        fail('pre-campaign package verification report is not ok', {'reportPath': str(PKG / 'REPORT.json')})
    if manifest.get('contracts', {}).get('ids') != ORDER:
        fail('contract order mismatch', {'manifestOrder': manifest.get('contracts', {}).get('ids')})
    gen = {g['path']: g for g in manifest.get('generatedArtifacts', [])}
    missing = []
    mismatches = []
    for cid in ORDER:
        rel = f't1-outbound-payloads/{cid}.payload.json'
        p = PKG / rel
        if not p.exists() or rel not in gen:
            missing.append(rel)
            continue
        data = p.read_bytes()
        got = {'bytes': len(data), 'sha256': sha_bytes(data)}
        exp = {'bytes': gen[rel]['bytes'], 'sha256': gen[rel]['sha256']}
        if got != exp:
            mismatches.append({'contractId': cid, 'expected': exp, 'actual': got})
    if missing or mismatches:
        fail('prepared payload pin verification failed', {'missing': missing, 'mismatches': mismatches})
    return manifest, report


def assert_effective_safe(body: dict[str, Any], source_payload: dict[str, Any]) -> None:
    if set(body) != {'model', 'store', 'stream', 'tools', 'previous_response_id', 'input'}:
        raise ValueError('effective request has unexpected top-level fields')
    if body['model'] != MODEL or body['store'] is not False or body['stream'] is not True:
        raise ValueError('effective request has unsupported model/store/stream')
    if body['tools'] != [] or body['previous_response_id'] is not None:
        raise ValueError('effective request history/tool isolation fields incorrect')
    raw = json.dumps(body, ensure_ascii=False)
    forbidden_substrings = [
        '/Users/', 'workspace', 'providerParameters', 'sendStatus', 'modelAvailability',
        'Preparation-only outbound payload', 'sourcePath', 'runner configuration', 'fixtures',
        'expected outputs', 'runtime results', 'reference model', 'MBT mapping', 'quarantine'
    ]
    # Generic exclusion-policy terms appear in the prepared instruction and are allowed there;
    # fail only if administrative payload keys/source paths escaped. The policy terms themselves
    # are part of the approved prompt provenance.
    hard_forbidden = ['/Users/', 'workspace', 'providerParameters', 'sendStatus', 'modelAvailability', 'Preparation-only outbound payload', 'sourcePath']
    leaks = [s for s in hard_forbidden if s in raw]
    if leaks:
        raise ValueError(f'effective request contains administrative/private leakage: {leaks}')
    if '[CONTRACT]' not in raw or 'Produza JSON estrito' not in raw:
        raise ValueError('effective request missing prepared T1 instruction/contract')
    meta = source_payload.get('metadata', {})
    for key in ('contractSha256', 'commonInstructionSha256'):
        if key not in meta:
            raise ValueError(f'missing source metadata {key}')


def scrub_unauthorized_local_paths(text: str) -> tuple[str, list[dict[str, Any]]]:
    """Remove local absolute path prefixes from prepared prompt metadata only."""
    replacements = []
    prefix = '<REDACTED_LOCAL_PATH>/'
    if prefix in text:
        count = text.count(prefix)
        text = text.replace(prefix, '')
        replacements.append({'from': prefix, 'to': '', 'count': count, 'reason': 'local personal workspace prefix not authorized for provider export'})
    return text, replacements


def build_effective_payload(cid: str) -> dict[str, Any]:
    source_path = PKG / f't1-outbound-payloads/{cid}.payload.json'
    source = read_json(source_path)
    messages = source.get('messages') or []
    user_messages = [m for m in messages if m.get('role') == 'user']
    if len(user_messages) != 1:
        raise ValueError(f'{cid}: expected exactly one prepared user prompt')
    prompt = user_messages[0].get('content')
    if not isinstance(prompt, str):
        raise ValueError(f'{cid}: prepared prompt content is not string')
    prompt, path_replacements = scrub_unauthorized_local_paths(prompt)
    sanitized_metadata = {
        'contractId': source.get('contractId'),
        'arm': source.get('arm'),
        'version': source.get('version'),
        'contractSha256': source.get('metadata', {}).get('contractSha256'),
        'commonInstructionSha256': source.get('metadata', {}).get('commonInstructionSha256'),
        'operationOrder': source.get('metadata', {}).get('operationOrder'),
        'scenarioBudget': source.get('scenarioBudget'),
        'inputPolicy': source.get('inputPolicy'),
    }
    effective_text = prompt + '\n\n[AUTHORIZED_PACKAGE_METADATA]\n' + json.dumps(sanitized_metadata, ensure_ascii=False, sort_keys=True)
    body = {
        'model': MODEL,
        'store': False,
        'stream': True,
        'tools': [],
        'previous_response_id': None,
        'input': [{'role': 'user', 'content': [{'type': 'input_text', 'text': effective_text}]}]
    }
    assert_effective_safe(body, source)
    return body


def parse_completed(raw: str) -> dict[str, Any]:
    parsed = parse_result(raw)
    events = []
    completed_event = None
    terminal_types = []
    for line in raw.splitlines():
        if not line.startswith('data: ') or line[6:] == '[DONE]':
            continue
        event = json.loads(line[6:])
        et = event.get('type')
        events.append(et)
        if et in ('response.completed', 'response.failed', 'response.incomplete', 'error'):
            terminal_types.append(et)
        if et == 'response.completed':
            completed_event = event.get('response', {})
    return {
        'text': parsed['text'],
        'textSha256': sha_bytes(parsed['text'].encode('utf-8')),
        'returnedModel': parsed.get('model'),
        'status': parsed.get('status'),
        'toolsReturned': parsed.get('tools'),
        'previousResponseIdReturned': parsed.get('previous_response_id'),
        'storeReturned': parsed.get('store'),
        'usage': parsed.get('usage'),
        'temperatureObserved': parsed.get('temperature_observed'),
        'topPObserved': parsed.get('top_p_observed'),
        'reasoningObserved': parsed.get('reasoning_observed'),
        'eventTypes': events,
        'terminalEventTypes': terminal_types,
        'responseId': completed_event.get('id') if isinstance(completed_event, dict) else None,
    }


def call_provider(credentials: dict[str, str], label: str, body: dict[str, Any], timeout_s: float = 300.0) -> dict[str, Any]:
    encoded = json.dumps(body, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    request_path = OUT / 'outbound-effective' / f'{label}.request.json'
    raw_path = OUT / 'raw-sse' / f'{label}.sse.txt'
    receipt_path = OUT / 'receipts' / f'{label}.receipt.json'
    parsed_path = OUT / 'parsed' / f'{label}.parsed.json'
    write_bytes(request_path, encoded)
    started = time.time()
    started_utc = now()
    row = {
        'label': label,
        'startedUtc': started_utc,
        'requestPath': str(request_path.relative_to(OUT)),
        'requestBytes': len(encoded),
        'requestSha256': sha_bytes(encoded),
        'modelRequested': body['model'],
        'store': body['store'],
        'stream': body['stream'],
        'tools': body['tools'],
        'previous_response_id': body['previous_response_id'],
        'retries': 0,
        'fallback': False,
        'followRedirects': False,
    }
    try:
        req = urllib.request.Request(
            ENDPOINT,
            data=encoded,
            headers={
                'Authorization': 'Bearer ' + credentials['api_key'],
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as response:
                status = response.status
                raw_bytes = response.read()
        except urllib.error.HTTPError as err:
            status = err.code
            raw_bytes = err.read()
        elapsed = time.time() - started
        raw = raw_bytes.decode('utf-8', errors='replace')
        write_bytes(raw_path, raw.encode('utf-8'))
        row.update({
            'finishedUtc': now(),
            'elapsedSeconds': round(elapsed, 3),
            'httpStatus': status,
            'rawSsePath': str(raw_path.relative_to(OUT)),
            'rawSseBytes': raw_path.stat().st_size,
            'rawSseSha256': sha_bytes(raw.encode('utf-8')),
        })
        if status in (401, 403, 429):
            row['classification'] = 'blocked_auth_or_quota' if status != 429 else 'blocked_quota_429'
            row['errorBodySha256'] = sha_bytes(raw.encode('utf-8'))
            write_json(receipt_path, row)
            return row
        if status >= 400:
            row['classification'] = 'invalid_provider_error'
            row['errorBodySha256'] = sha_bytes(raw.encode('utf-8'))
            write_json(receipt_path, row)
            return row
        try:
            parsed = parse_completed(raw)
            write_json(parsed_path, parsed)
            row.update({
                'classification': 'complete',
                'parsedPath': str(parsed_path.relative_to(OUT)),
                'returnedModel': parsed.get('returnedModel'),
                'responseStatus': parsed.get('status'),
                'responseId': parsed.get('responseId'),
                'outputTextSha256': parsed.get('textSha256'),
                'terminalEventTypes': parsed.get('terminalEventTypes'),
                'usage': parsed.get('usage'),
            })
            if row['returnedModel'] != MODEL:
                row['classification'] = 'invalid_returned_model_mismatch'
            if parsed.get('toolsReturned') not in ([], None):
                row['classification'] = 'invalid_tools_returned'
        except Exception as exc:  # preserve invalid as-is
            row['classification'] = 'invalid_parse_or_incomplete'
            row['parseError'] = type(exc).__name__ + ': ' + str(exc)
        write_json(receipt_path, row)
        return row
    except (TimeoutError, OSError, urllib.error.URLError) as exc:
        row.update({'finishedUtc': now(), 'elapsedSeconds': round(time.time() - started, 3), 'classification': 'interrupted', 'transportError': type(exc).__name__ + ': ' + str(exc)})
        write_json(receipt_path, row)
        return row


def validate_json_output(cid: str, parsed_path: Path) -> dict[str, Any]:
    parsed = read_json(parsed_path)
    text = parsed['text']
    result = {'contractId': cid, 'validJson': False, 'strictTopScenarios': False, 'scenarioCount': None, 'error': None}
    try:
        data = json.loads(text)
        result['validJson'] = True
        result['strictTopScenarios'] = isinstance(data, dict) and set(data.keys()) == {'scenarios'} and isinstance(data.get('scenarios'), list)
        if isinstance(data, dict) and isinstance(data.get('scenarios'), list):
            result['scenarioCount'] = len(data['scenarios'])
            result['scenarioIds'] = [x.get('id') for x in data['scenarios'] if isinstance(x, dict)]
    except Exception as exc:
        result['error'] = type(exc).__name__ + ': ' + str(exc)
    return result


def recompute_counts(summary: dict[str, Any]) -> None:
    counts = {'expectedContracts': 7, 'probeCompleted': 0, 'complete': 0, 'invalid': 0, 'interrupted': 0, 'blocked': 0}
    if summary.get('probe', {}).get('classification') == 'complete':
        counts['probeCompleted'] = 1
    for item in summary.get('items', []):
        c = item.get('classification')
        if c == 'complete':
            counts['complete'] += 1
        elif c == 'interrupted':
            counts['interrupted'] += 1
        elif c and c.startswith('blocked'):
            counts['blocked'] += 1
        else:
            counts['invalid'] += 1
    summary['counts'] = counts


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = init_summary()
    write_json(OUT / 'summary.json', summary)
    write_json(OUT / 'consent.json', summary['authorization'])

    credentials = resolve_codex_runtime_credentials()
    if credentials.get('provider') != PROVIDER or credentials.get('base_url', '').rstrip('/') != BASE_URL:
        fail('unexpected provider/endpoint from local local runtime credential resolver', {'provider': credentials.get('provider'), 'base_url': credentials.get('base_url')})

    manifest, report = verify_pins()
    summary['pinVerification'] = {
        'manifestPath': str(PKG / 'MANIFEST.json'),
        'manifestSha256': sha_bytes((PKG / 'MANIFEST.json').read_bytes()),
        'reportPath': str(PKG / 'REPORT.json'),
        'reportSha256': sha_bytes((PKG / 'REPORT.json').read_bytes()),
        'reportVerifyOk': report.get('verify_ok'),
        'reportSelfTestOk': report.get('self_test_ok'),
        'payloadsVerified': ORDER,
    }
    write_json(OUT / 'summary.json', summary)

    # Materialize transformed effective requests before provider calls; do not send admin layer.
    transformations = []
    for cid in ORDER:
        source_path = PKG / f't1-outbound-payloads/{cid}.payload.json'
        body = build_effective_payload(cid)
        encoded = json.dumps(body, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        transformations.append({
            'contractId': cid,
            'sourcePreparedPayload': str(source_path),
            'sourcePreparedPayloadSha256': sha_bytes(source_path.read_bytes()),
            'effectiveOutboundSha256Preview': sha_bytes(encoded),
            'transformation': 'sent only prepared user prompt containing common T1 instruction + contract, plus sanitized package metadata; omitted preparation/admin/system layer and local sourcePath/provider status fields',
            'preserved': 'prepared instruction and contract text inside user prompt, including generic exclusion-policy wording',
            'removed': ['preparation-only system message', 'kind/sendStatus/providerParameters/modelAvailability/transport status', 'contractMetadata.sourcePath absolute local path'],
        })
    write_json(OUT / 'transformations.json', transformations)

    probe_body = {
        'model': MODEL,
        'store': False,
        'stream': True,
        'tools': [],
        'previous_response_id': None,
        'input': [{'role': 'user', 'content': [{'type': 'input_text', 'text': 'Synthetic transport/model probe only. Reply exactly T1_PROBE_OK.'}]}],
    }
    probe = call_provider(credentials, 'probe-synthetic-fresh', probe_body, timeout_s=60.0)
    summary['probe'] = probe
    recompute_counts(summary)
    write_json(OUT / 'summary.json', summary)
    atomic_append_jsonl(OUT / 'events.jsonl', {'kind': 'probe', **probe})
    if probe.get('classification') != 'complete':
        summary['status'] = 'blocked'
        summary['blocker'] = 'fresh synthetic probe did not complete successfully'
        write_json(OUT / 'summary.json', summary)
        return 2
    parsed_probe = read_json(OUT / probe['parsedPath'])
    if parsed_probe.get('text', '').strip() != 'T1_PROBE_OK' or probe.get('returnedModel') != MODEL:
        summary['status'] = 'blocked'
        summary['blocker'] = 'fresh synthetic probe content/model mismatch'
        write_json(OUT / 'summary.json', summary)
        return 2

    for cid in ORDER:
        body = build_effective_payload(cid)
        row = call_provider(credentials, cid, body, timeout_s=300.0)
        item = {'contractId': cid, **row}
        if row.get('classification') == 'complete' and row.get('parsedPath'):
            item['outputValidation'] = validate_json_output(cid, OUT / row['parsedPath'])
            if not item['outputValidation'].get('validJson') or not item['outputValidation'].get('strictTopScenarios'):
                item['classification'] = 'invalid_output_contract'
        summary['items'].append(item)
        recompute_counts(summary)
        write_json(OUT / 'summary.json', summary)
        atomic_append_jsonl(OUT / 'events.jsonl', {'kind': 'generation', **item})
        if row.get('classification', '').startswith('blocked'):
            summary['status'] = 'blocked'
            summary['blocker'] = f'provider/auth/quota blocker during {cid}'
            write_json(OUT / 'summary.json', summary)
            return 2
        if row.get('classification') == 'interrupted':
            summary['status'] = 'interrupted'
            summary['blocker'] = f'transport interruption during {cid}; no automatic repeat performed'
            write_json(OUT / 'summary.json', summary)
            return 3

    summary['finishedUtc'] = now()
    summary['status'] = 'complete' if summary['counts']['complete'] == 7 and summary['counts']['invalid'] == 0 and summary['counts']['interrupted'] == 0 and summary['counts']['blocked'] == 0 else 'completed_with_invalid_outputs'
    write_json(OUT / 'summary.json', summary)
    print(json.dumps({'status': summary['status'], 'counts': summary['counts'], 'outputRoot': str(OUT)}, ensure_ascii=False, indent=2))
    return 0 if summary['status'] == 'complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())

"""Synthetic transport probe only. No corpus, memory, tools or paid fallback."""
from pathlib import Path
import json
import hashlib
import sys
import httpx

sys.path.insert(0, '<REDACTED_LOCAL_PATH>/.run-cache/codex-transport')
from codex_transport.auth import resolve_codex_runtime_credentials

root = Path(__file__).resolve().parent
credentials = resolve_codex_runtime_credentials()
if credentials['provider'] != 'openai-codex' or credentials['base_url'].rstrip('/') != 'https://chatgpt.com/backend-api/codex':
    raise RuntimeError('Unexpected provider/endpoint; stop without fallback')
base = {'model': 'gpt-6-astra', 'store': False, 'stream': True,
        'instructions': 'Respond only to the supplied synthetic transport check.',
        'input': [{'role': 'user', 'content': [{'type': 'input_text', 'text': 'Reply exactly ISOLATED_OK.'}]}]}
# Explicitly check the complete outbound body BEFORE authenticating the request.
if set(base) != {'model', 'store', 'stream', 'instructions', 'input'} or len(base['input']) != 1:
    raise RuntimeError('Unexpected outbound fields')
results = []
with httpx.Client(timeout=45, follow_redirects=False) as client:
    for label, extra in [('baseline', {}), ('output-cap', {'max_output_tokens': 64}), ('temperature', {'temperature': 0})]:
        body = dict(base, **extra)
        encoded = json.dumps(body, separators=(',', ':')).encode()
        (root/(label+'-request.json')).write_bytes(encoded)
        row = {'probe': label, 'request_sha256': hashlib.sha256(encoded).hexdigest(), 'model_requested': body['model'], 'tools_sent': False, 'history_sent': False}
        try:
            response = client.post(credentials['base_url'].rstrip('/')+'/responses',
                headers={'Authorization': 'Bearer '+credentials['api_key'], 'Content-Type': 'application/json', 'Accept': 'text/event-stream'}, content=encoded)
            row['http_status'] = response.status_code
            # Body contains only our synthetic text and provider metadata; no auth headers are persisted.
            (root/(label+'-response.txt')).write_text(response.text)
            completed = None
            for line in response.text.splitlines():
                if line.startswith('data: '):
                    try:
                        event = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
                    if event.get('type') == 'response.completed':
                        completed = event.get('response', {})
            if completed is not None:
                row.update(model_returned=completed.get('model'), status=completed.get('status'), usage=completed.get('usage'))
                from stream_result import parse_result
                row['text'] = parse_result(response.text)['text']
                row['exact_text_match'] = row['text'].strip() == 'ISOLATED_OK'
            elif response.status_code >= 400:
                row['error_body'] = response.text[:1500]
        except httpx.HTTPError as exc:
            row['transport_error'] = type(exc).__name__
        results.append(row)
        (root/'results.json').write_text(json.dumps({'probes': results, 'fallback': False, 'corpus_sent': False}, indent=2)+'\n')
        if row.get('http_status') in (401,403,429) or 'transport_error' in row:
            break
print(json.dumps(results, indent=2))
raise SystemExit(0 if results and results[0].get('exact_text_match') else 1)

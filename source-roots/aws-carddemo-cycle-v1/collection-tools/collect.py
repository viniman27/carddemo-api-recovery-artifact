"""Authorized six-call collection. Never retries or repairs a response."""
from pathlib import Path
import sys
import json
import time
import hashlib
from datetime import datetime, timezone
import httpx
from guard import checked_body

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'P1/direct-transport'))
from stream_result import parse_result
sys.path.insert(0, '<REDACTED_LOCAL_PATH>/.run-cache/codex-transport')
from codex_transport.auth import resolve_codex_runtime_credentials

# All requests checked before the first call. Pinned values are the user-approved package.
PINS = {'E1':'b165ec4fc05055f11bc544ca8b63cb5362706aba0cba8aa6c4d47c8643ec595a',
        'E2':'ab8ed34287d5c5a2e89d252b3dc71c1535c10642c7e42b3f56f7b77c639d4ff4'}
ORDER = ['E1-1','E2-1','E1-2','E2-2','E1-3','E2-3']
auth_raw = (ROOT/'P1/AUTORIZACAO-COLETA.json').read_bytes()
auth = json.loads(auth_raw)
if auth['status'] != 'authorized_for_E1_E2_only' or auth['request_sha256'] != PINS or auth['order'] != ORDER or auth['repetitions'] != 3 or auth['automatic_retries'] != 0:
    raise RuntimeError('Authorization mismatch')
requests = {}
for strategy, pin in PINS.items():
    raw = (ROOT/'P1/prepared-requests'/(strategy+'.json')).read_bytes()
    checked_body(raw, pin)
    requests[strategy] = raw
out = ROOT/'collection-01'
out.mkdir(exist_ok=False)  # Never overwrite or resume automatically.
(out/'authorization.json').write_bytes(auth_raw)
(out/'runner.py').write_bytes(Path(__file__).read_bytes())
rows = []
summary = {'status':'running','order':ORDER,'attempts':rows,'automatic_retries':0,'model':'gpt-6-astra'}
(out/'status.json').write_text(json.dumps(summary,indent=2)+'\n')
for attempt in ORDER:
    strategy = attempt.split('-')[0]
    folder = out/attempt
    folder.mkdir()
    raw = requests[strategy]
    (folder/'request.json').write_bytes(raw)
    row = {'attempt':attempt,'strategy':strategy,'status':'starting','request_sha256':PINS[strategy],
           'started_utc':datetime.now(timezone.utc).isoformat()}
    rows.append(row)
    (folder/'receipt.json').write_text(json.dumps(row,indent=2)+'\n')
    (out/'status.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('START '+attempt, flush=True)
    start = time.monotonic()
    try:
        credentials = resolve_codex_runtime_credentials()
        if credentials['provider'] != 'openai-codex' or credentials['base_url'].rstrip('/') != 'https://chatgpt.com/backend-api/codex':
            raise RuntimeError('Unexpected endpoint; no fallback')
        # No SDK retries; response bytes saved as they arrive, even on interruption.
        with httpx.Client(timeout=httpx.Timeout(180,connect=30), follow_redirects=False) as client:
            with client.stream('POST', credentials['base_url'].rstrip('/')+'/responses',
                 headers={'Authorization':'Bearer '+credentials['api_key'],'Content-Type':'application/json','Accept':'text/event-stream'},content=raw) as response:
                row['http_status'] = response.status_code
                with (folder/'response.sse').open('xb') as sink:
                    for block in response.iter_bytes():
                        sink.write(block)
                        sink.flush()
                        if time.monotonic()-start > 900:
                            raise TimeoutError('Per-attempt wall budget exceeded; no retry')
        if row['http_status'] != 200:
            raise RuntimeError('HTTP '+str(row['http_status'])+'; collection paused')
        result = parse_result((folder/'response.sse').read_text())
        (folder/'parsed.json').write_text(json.dumps(result,indent=2)+'\n')
        if result['model'] != 'gpt-6-astra' or result['tools'] != [] or result['previous_response_id'] is not None or result['store'] is not False:
            raise RuntimeError('Returned model/isolation mismatch')
        # Raw model text, no fence stripping or YAML repair.
        (folder/'response-original.txt').write_text(result['text'])
        row.update(status='response_collected',model_returned=result['model'],usage=result['usage'],
                   response_sha256=hashlib.sha256(result['text'].encode()).hexdigest(),
                   contract_validation='pending')
    except Exception as exc:
        row.update(status='blocked',error_type=type(exc).__name__,error=str(exc)[:500])
        summary['status'] = 'blocked'
    row['elapsed_seconds'] = round(time.monotonic()-start,3)
    row['ended_utc'] = datetime.now(timezone.utc).isoformat()
    (folder/'receipt.json').write_text(json.dumps(row,indent=2)+'\n')
    (out/'status.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(attempt+' '+row['status'], flush=True)
    if row['status'] == 'blocked':
        break
if len(rows) == len(ORDER) and all(x['status']=='response_collected' for x in rows):
    summary['status']='collected_pending_validation'
summary['collected_count']=sum(x['status']=='response_collected' for x in rows)
summary['attempted_count']=len(rows)
(out/'status.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'status':summary['status'],'collected':summary['collected_count'],'attempted':len(rows)}),flush=True)
raise SystemExit(0 if summary['status']=='collected_pending_validation' else 1)

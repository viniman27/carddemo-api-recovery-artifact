"""Parse a completed Codex SSE response without trusting text alone."""
import json


def parse_result(raw):
    completed = None
    parts = {}
    for line in raw.splitlines():
        if not line.startswith('data: '):
            continue
        if line[6:] == '[DONE]':
            continue
        event = json.loads(line[6:])
        kind = event.get('type')
        if kind in ('response.failed', 'response.incomplete', 'error'):
            raise ValueError('Provider did not complete successfully')
        if kind == 'response.output_text.done':
            key = (event.get('output_index', 0), event.get('content_index', 0))
            if key in parts and parts[key] != event['text']:
                raise ValueError('Conflicting completed content')
            parts[key] = event['text']
        if kind == 'response.completed':
            completed = event['response']
    if completed is None or completed.get('status') != 'completed' or completed.get('error'):
        raise ValueError('Missing successful completion event')
    text = ''.join(parts[k] for k in sorted(parts))
    if not text:
        text = ''.join(c.get('text', '') for item in completed.get('output', [])
                       for c in item.get('content', []) if c.get('type') == 'output_text')
    if not text:
        raise ValueError('Completed without output text')
    return {'text': text, 'model': completed.get('model'), 'status': completed['status'],
            'tools': completed.get('tools'), 'previous_response_id': completed.get('previous_response_id'),
            'store': completed.get('store'), 'usage': completed.get('usage'),
            'temperature_observed': completed.get('temperature'), 'top_p_observed': completed.get('top_p'),
            'reasoning_observed': completed.get('reasoning')}

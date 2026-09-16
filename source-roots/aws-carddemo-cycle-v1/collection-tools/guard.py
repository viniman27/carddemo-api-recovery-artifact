"""Fail closed before sending a pinned experimental request."""
import json
import hashlib


def checked_body(raw, expected_hash):
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        raise ValueError('Request hash changed')
    body = json.loads(raw)
    if set(body) != {'model','store','stream','instructions','input'}:
        raise ValueError('Unexpected request fields')
    if body['model'] != 'gpt-6-astra' or body['store'] is not False or body['stream'] is not True:
        raise ValueError('Model or storage mode changed')
    if len(body['input']) != 1 or body['input'][0]['role'] != 'user':
        raise ValueError('Unexpected history')
    if set(body['input'][0]) != {'role','content'} or len(body['input'][0]['content']) != 1:
        raise ValueError('Unexpected input shape')
    part = body['input'][0]['content'][0]
    if set(part) != {'type','text'} or part['type'] != 'input_text' or not isinstance(part['text'],str):
        raise ValueError('Unexpected content')
    return body

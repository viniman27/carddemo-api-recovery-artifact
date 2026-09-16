import unittest
import hashlib
import json
from guard import checked_body

class GuardTests(unittest.TestCase):
    def test_pinned_body_and_isolation(self):
        body = {'model':'gpt-6-astra','store':False,'stream':True,'instructions':'synthetic','input':[{'role':'user','content':[{'type':'input_text','text':'synthetic'}]}]}
        raw = json.dumps(body).encode()
        self.assertEqual(checked_body(raw, hashlib.sha256(raw).hexdigest()), body)
        with self.assertRaises(ValueError):
            checked_body(raw+b' ', hashlib.sha256(raw).hexdigest())
        for key,value in [('model','other'),('store',True),('tools',[]),('previous_response_id','prior')]:
            changed = dict(body, **{key:value})
            data = json.dumps(changed).encode()
            with self.assertRaises(ValueError):
                checked_body(data,hashlib.sha256(data).hexdigest())

if __name__ == '__main__':
    unittest.main()

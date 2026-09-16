import sys, unittest, base64
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import requests, schemathesis
from t2_offline_bridge import transport_kwargs_to_frozen_request
class ActualTransport(unittest.TestCase):
    def test_real_schemathesis_kwargs_match_prepared_request(self):
        schema=schemathesis.openapi.from_dict({"openapi":"3.1.0","info":{"title":"synthetic","version":"1"},"paths":{"/x":{"post":{"parameters":[{"in":"query","name":"q","schema":{"type":"string"}}],"requestBody":{"content":{"application/json":{"schema":{"type":"object"}}}},"responses":{"200":{"description":"ok"}}}}}})
        case=schema["/x"]["POST"].Case(query={"q":"a b"},body={"x":1},media_type="application/json")
        kw=case.as_transport_kwargs(base_url="http://127.0.0.1")
        prepared=requests.Request(**kw).prepare()
        got=transport_kwargs_to_frozen_request("SYN",{"operationId":"x"},"one",kw,seed=1,direction="positive",expected_status=[200])
        self.assertEqual(got["path"],prepared.path_url)
        self.assertEqual(base64.b64decode(got["body_b64"]),prepared.body)
        self.assertEqual(got["headers"],[list(x) for x in prepared.headers.items()])

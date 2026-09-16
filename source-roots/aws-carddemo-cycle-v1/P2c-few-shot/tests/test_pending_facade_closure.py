import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import p2c_facade


def bindings_for(track):
    return {k: p2c_facade.LOCAL_BINDING_PREFIX + k for k in p2c_facade.BINDING_FIELDS[track]}


class PendingFacadeClosureTests(unittest.TestCase):
    def test_e2_2_parameter_length_is_sent_to_local_linkage_wrapper(self):
        body = {
            "bindings": bindings_for("interest"),
            "parameterDate": "LENPROBE42",
            "parameterLength": -7,
        }
        result = p2c_facade.execute("E2-2", "interest", body)
        audit = json.loads(Path(result["p2bAuditPath"]).read_text())
        external = audit["RES"]["externalParameter"]
        self.assertEqual(external["value"], "LENPROBE42")
        self.assertEqual(external["linkageParameterLength"], -7)
        self.assertEqual((Path(audit["INV"]["workdir"]) / "PARMFILE").read_bytes(), b"LENPROBE42")
        self.assertEqual(json.loads((Path(audit["INV"]["workdir"]) / "p2c-interest-linkage.json").read_text())["parameterLength"], -7)

    def test_contract_default_parameter_length_is_prefix_length_not_constant_ten(self):
        body = {
            "bindings": bindings_for("interest"),
            "parameterDate": "SHORT",
        }
        result = p2c_facade.execute("E2-2", "interest", body)
        audit = json.loads(Path(result["p2bAuditPath"]).read_text())
        external = audit["RES"]["externalParameter"]
        self.assertEqual(external["value"], "SHORT     ")
        self.assertEqual(external["linkageParameterLength"], 5)
        self.assertEqual((Path(audit["INV"]["workdir"]) / "PARMFILE").read_bytes(), b"SHORT     ")

    def test_bindings_are_resolved_to_real_dd_paths_and_unknown_token_fails(self):
        body = {"bindings": bindings_for("posting"), "transactions": []}
        result = p2c_facade.execute("E2-2", "posting", body)
        audit = json.loads(Path(result["p2bAuditPath"]).read_text())
        resolved = audit["RES"]["requestBindingsResolved"]
        self.assertEqual(resolved["accounts"]["ddName"], "ACCTFILE")
        self.assertTrue(Path(resolved["accounts"]["path"]).exists())
        body["bindings"]["accounts"] = p2c_facade.LOCAL_BINDING_PREFIX + "notAccounts"
        with self.assertRaises(p2c_facade.TransportRejection):
            p2c_facade.validate_request("E2-2", "posting", body)

    def test_pre_cobol_snapshot_is_after_request_materialization(self):
        tx = dict(p2c_facade.sample_request("E2-1", "posting")["dailyTransactions"][0], transactionId="SNAP000000000001")
        result = p2c_facade.execute("E2-1", "posting", {"dailyTransactions": [tx]})
        audit = json.loads(Path(result["p2bAuditPath"]).read_text())
        labels = {c["label"]: c for c in audit["CAP"]["captures"]}
        self.assertIn("DALYTRAN.pre_cobol", labels)
        pre = audit["STATE"]["pre_cobol_request_materialized"]
        self.assertTrue(any(f["path"] == "DALYTRAN" and f["bytes"] == 350 for f in pre["files"]))
        self.assertEqual(pre["afterRequestInputs"], ["DALYTRAN"])

    def test_http_server_is_single_contract_no_prefixed_alias(self):
        port_file = p2c_facade.OUTPUTS / f"single-contract-{time.time_ns()}.port"
        proc = subprocess.Popen([sys.executable, str(ROOT / "p2c_facade.py"), "serve", "--contract-id", "E2-3", "--port-file", str(port_file)], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            for _ in range(100):
                if port_file.exists():
                    break
                time.sleep(0.05)
            port = int(port_file.read_text())
            data = json.dumps({"transactionIdPrefix": "INPUTCHECK"}).encode()
            good = urllib.request.Request(f"http://127.0.0.1:{port}/interest-generation-runs", data=data, headers={"content-type":"application/json"}, method="POST")
            try:
                urllib.request.urlopen(good, timeout=120).read()
            except urllib.error.HTTPError as exc:
                self.assertIn(exc.code, {500, 503})
                exc.read()
            bad = urllib.request.Request(f"http://127.0.0.1:{port}/E2-3/interest-generation-runs", data=data, headers={"content-type":"application/json"}, method="POST")
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(bad, timeout=30)
            self.assertEqual(ctx.exception.code, 404)
        finally:
            proc.terminate()
            try:
                proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.communicate()


if __name__ == "__main__":
    unittest.main()

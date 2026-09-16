"""Technical characterization of ORIGINAL COBOL; not formal semantic validation.
Synthetic ASCII fixed records. No upstream sample padding/transcoding.
All money below is integer cents encoded as fixed-width DISPLAY bytes.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from prepare import check_load_target, require

ROOT = Path(__file__).resolve().parent
SIZES = {'TRANFILE': 350, 'XREFFILE': 50, 'ACCTFILE': 300, 'TCATBALF': 50}

def account(expiry=b'2099-12-31'):
    data = (b'00000000001' + b'Y' + b'000000000000' + b'000000100000' +
            b'000000100000' + b'2020-01-01' + expiry + b'2020-01-01' +
            b'000000000000' + b'000000000000' + b'0000000000' + b'TEST      ' + b' '*178)
    require(len(data) == 300, 'Invalid account fixture width')
    return data

def transaction(card=b'0000000000000001', amount=b'00000002500'):
    data = (b'TEST000000000001' + b'01' + b'0001' + b'TEST      ' +
            b'LOCAL SYNTHETIC FIXTURE'.ljust(100) + amount + b'000000001' +
            b'TEST MERCHANT'.ljust(50) + b'TEST CITY'.ljust(50) + b'0000000000' +
            card + b'2025-01-01-00.00.00.000000' + b' '*26 + b' '*20)
    require(len(data) == 350, 'Invalid transaction fixture width')
    return data

class PosttranTests(unittest.TestCase):
    def run_case(self, name, daily, acct=None):
        runs = ROOT/'runs'
        runs.mkdir(exist_ok=True)
        wd = Path(tempfile.mkdtemp(prefix=name+'-', dir=runs))
        seeds = {'TRANFILE': b'', 'TCATBALF': b'', 'ACCTFILE': account() if acct is None else acct,
                 'XREFFILE': b'0000000000000001' + b'000000001' + b'00000000001' + b' '*14}
        steps = []
        def execute(cmd, env):
            p = subprocess.run(cmd, cwd=wd, env=dict(os.environ, **env),
                               capture_output=True, text=True, timeout=15)
            steps.append({'command': cmd, 'env': env, 'rc': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
            return p
        for dd, data in seeds.items():
            self.assertEqual(len(data) % SIZES[dd], 0)
            raw = wd/(dd+'.seed')
            raw.write_bytes(data)
            check_load_target(wd, wd/dd)
            p = execute([str(ROOT/'build'/('io_'+dd))],
                {'IO_MODE':'LOAD', 'DD_RAW': str(raw), 'DD_IDX': str(wd/dd)})
            self.assertEqual(p.returncode, 0, p.stdout+p.stderr)
        (wd/'DALYTRAN').write_bytes(daily)
        env = {'DD_'+dd: str(wd/dd) for dd in [*SIZES, 'DALYTRAN', 'DALYREJS']}
        env['COB_LIBRARY_PATH'] = str(ROOT/'build')
        result = execute([str(ROOT/'build/CBTRN02C')], env)
        outputs = {}
        for dd in SIZES:
            raw = wd/(dd+'.after')
            p = execute([str(ROOT/'build'/('io_'+dd))],
                {'IO_MODE':'DUMP', 'DD_RAW': str(raw), 'DD_IDX': str(wd/dd)})
            self.assertEqual(p.returncode, 0, p.stdout+p.stderr)
            outputs[dd] = raw.read_bytes()
        outputs['DALYREJS'] = (wd/'DALYREJS').read_bytes()
        record = {'case': name, 'workdir': str(wd), 'steps': steps,
                  'input_sha256': {k: hashlib.sha256(v).hexdigest() for k,v in {**seeds,'DALYTRAN':daily}.items()},
                  'output_sha256': {k: hashlib.sha256(v).hexdigest() for k,v in outputs.items()},
                  'output_bytes': {k: len(v) for k,v in outputs.items()},
                  'observed_fields_hex': {
                      'ACCTFILE[12:24]': outputs['ACCTFILE'][12:24].hex(),
                      'TCATBALF[17:28]': outputs['TCATBALF'][17:28].hex(),
                      'TRANFILE[0:304]': outputs['TRANFILE'][:304].hex(),
                      'TRANFILE[330:]': outputs['TRANFILE'][330:].hex()},
                  'reset_exclusion': 'TRANFILE bytes 304:330 (processing timestamp)'}
        (wd/'execution.json').write_text(json.dumps(record, indent=2)+'\n')
        return result, outputs

    def test_nominal_posting(self):
        p, out = self.run_case('nominal', transaction())
        self.assertEqual(p.returncode, 0, p.stdout+p.stderr)
        self.assertIn('END OF EXECUTION', p.stdout)
        self.assertEqual(len(out['TRANFILE']), 350)
        self.assertEqual(out['TRANFILE'][:304], transaction()[:304])
        self.assertEqual(out['ACCTFILE'][12:24], b'000000002500')
        self.assertEqual(out['ACCTFILE'][78:90], b'000000002500')
        self.assertEqual(out['TCATBALF'][17:28], b'00000002500')
        self.assertEqual(out['DALYREJS'], b'')

    def test_invalid_card(self):
        data = transaction(card=b'9999999999999999')
        p, out = self.run_case('invalid-card', data)
        self.assertEqual(p.returncode, 4, p.stdout+p.stderr)
        self.assertEqual(out['DALYREJS'][:350], data)
        self.assertEqual(out['DALYREJS'][350:354], b'0100')
        self.assertEqual(len(out['DALYREJS']), 430)
        self.assertEqual(out['ACCTFILE'], account())
        self.assertEqual(out['TRANFILE'], b'')
        self.assertEqual(out['TCATBALF'], b'')

    def test_missing_account(self):
        p, out = self.run_case('missing-account', transaction(), acct=b'')
        self.assertEqual(p.returncode, 4, p.stdout+p.stderr)
        self.assertEqual(out['DALYREJS'][350:354], b'0101')
        self.assertEqual(out['TRANFILE'], b'')

    def test_credit_limit(self):
        p, out = self.run_case('overlimit', transaction(amount=b'00000100001'))
        self.assertEqual(p.returncode, 4, p.stdout+p.stderr)
        self.assertEqual(out['DALYREJS'][350:354], b'0102')
        self.assertEqual(out['ACCTFILE'], account())
        self.assertEqual(out['TRANFILE'], b'')

    def test_expired_account(self):
        seed = account(expiry=b'2024-12-31')
        p, out = self.run_case('expired', transaction(), acct=seed)
        self.assertEqual(p.returncode, 4, p.stdout+p.stderr)
        self.assertEqual(out['DALYREJS'][350:354], b'0103')
        self.assertEqual(out['ACCTFILE'], seed)
        self.assertEqual(out['TRANFILE'], b'')

    def test_empty_batch(self):
        p, out = self.run_case('empty', b'')
        self.assertEqual(p.returncode, 0, p.stdout+p.stderr)
        self.assertEqual(out['ACCTFILE'], account())
        self.assertEqual(out['TRANFILE'], b'')
        self.assertEqual(out['DALYREJS'], b'')

    def test_duplicate_preserves_observed_partial_updates(self):
        p, out = self.run_case('duplicate', transaction()*2)
        self.assertEqual(p.returncode, 12, p.stdout+p.stderr)
        self.assertIn('LOCAL-CEE3ABD', p.stderr)
        self.assertNotIn('END OF EXECUTION', p.stdout)
        self.assertEqual(len(out['TRANFILE']), 350)
        self.assertEqual(out['ACCTFILE'][12:24], b'000000005000')
        self.assertEqual(out['TCATBALF'][17:28], b'00000005000')

    def test_reset_repeats_state_except_processing_timestamp(self):
        a, first = self.run_case('reset-a', transaction())
        b, second = self.run_case('reset-b', transaction())
        self.assertEqual((a.returncode, b.returncode), (0,0))
        for dd in first:
            if dd == 'TRANFILE':
                # Explicitly exclude COBOL CURRENT-DATE, bytes 304:330 only.
                self.assertEqual(first[dd][:304]+first[dd][330:], second[dd][:304]+second[dd][330:])
            else:
                self.assertEqual(first[dd], second[dd])

if __name__ == '__main__':
    unittest.main()

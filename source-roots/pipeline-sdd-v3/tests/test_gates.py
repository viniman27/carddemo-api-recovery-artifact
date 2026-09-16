"""Synthetic review records only; no real human approval is created."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / 'pipeline/tools/check_gate.py'
TYPES = ['pipeline-scope', 'capability-selection', 'legacy-evidence',
         'capability-semantics', 'canonical-data-boundary', 'api-contract',
         'adapter-behavior', 'semantic-validation',
         'implementation-executable-qualification']


class GateTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def pin(self, name):
        return {'path': name, 'sha256': hashlib.sha256((self.root / name).read_bytes()).hexdigest()}

    def stage(self, number, upstream=()):
        artifact = f'stage{number}/artifact.md'
        auth = f'stage{number}/authorization.txt'
        spec_path = f'stage{number}/spec.json'
        self.write(artifact, 'Synthetic artifact; not a research output.\n')
        self.write(auth, 'SYNTHETIC TEST ONLY. No human authorization.\n')
        context = {'run_id': 'synthetic-run', 'capability': 'synthetic-capability',
                   'pipeline_stage': number, 'artifact_type': TYPES[number - 1]}
        spec = dict(context, artifact_path=artifact, upstream_specs=list(upstream), gate={
            'completeness_gate_passed': True, 'blocking_gaps': [], 'gate_review_date': '2026-01-01',
            'review': {'decision': 'approve', 'reviewer': 'SYNTHETIC TEST', 'context': context.copy(),
                       'artifact': self.pin(artifact), 'upstream_specs': [self.pin(n) for n in upstream],
                       'authorization': self.pin(auth)}})
        self.save(spec_path, spec)
        return spec_path

    def save(self, name, spec):
        self.write(name, json.dumps(spec, indent=2))

    def run_check(self, spec_path):
        proc = subprocess.run([sys.executable, str(TOOL), str(self.root), spec_path],
                              capture_output=True, text=True)
        self.assertTrue(proc.stdout.strip().startswith('{'), proc.stderr or proc.stdout)
        return proc, json.loads(proc.stdout)

    def test_current_record_reports_freshness_not_authorization(self):
        name = self.stage(1)
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        proc, data = self.run_check(name)
        self.assertEqual(proc.returncode, 0, data)
        self.assertEqual(data['status'], 'current')
        self.assertIs(data['human_approval_granted'], False)
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_transitive_change_invalidates_and_restoration_recovers(self):
        first = self.stage(1)
        second = self.stage(2, [first])
        third = self.stage(3, [second])
        self.assertEqual(self.run_check(third)[1]['status'], 'current')
        original = (self.root / 'stage1/artifact.md').read_text()
        self.write('stage1/artifact.md', 'Changed synthetic source of authority.\n')
        proc, data = self.run_check(third)
        self.assertEqual(proc.returncode, 1, data)
        self.assertEqual(data['status'], 'stale', data)
        self.write('stage1/artifact.md', original)
        self.assertEqual(self.run_check(third)[1]['status'], 'current')
        self.write(first, (self.root / first).read_text() + '\n')
        self.assertEqual(self.run_check(third)[1]['status'], 'stale')

    def test_metadata_changes_or_incomplete_review_cannot_look_current(self):
        import copy
        name = self.stage(1)
        original = json.loads((self.root / name).read_text())
        cases = []
        for field, value in [('run_id', 'other-run'), ('capability', 'other-capability'),
                             ('artifact_path', 'other.md')]:
            obj = copy.deepcopy(original)
            obj[field] = value
            cases.append((obj, 'stale'))
        for field in ['reviewer', 'context', 'authorization']:
            obj = copy.deepcopy(original)
            del obj['gate']['review'][field]
            cases.append((obj, 'invalid'))
        obj = copy.deepcopy(original)
        obj['gate']['review'] = None
        obj['gate']['completeness_gate_passed'] = False
        cases.append((obj, 'unreviewed'))
        obj = copy.deepcopy(original)
        obj['gate']['blocking_gaps'] = ['G-1']
        cases.append((obj, 'blocked'))
        obj = copy.deepcopy(original)
        obj['gate']['review']['reviewer'] = ' '
        cases.append((obj, 'invalid'))
        for obj, expected in cases:
            with self.subTest(expected=expected, obj=obj):
                self.save(name, obj)
                proc, data = self.run_check(name)
                self.assertEqual(proc.returncode, 1, data)
                self.assertEqual(data['status'], expected, data)

    def test_omitted_or_inconsistent_upstream_chain_is_rejected(self):
        first = self.stage(1)
        second = self.stage(2, [first])
        obj = json.loads((self.root / second).read_text())
        obj['gate']['review']['upstream_specs'] = []
        self.save(second, obj)
        self.assertNotEqual(self.run_check(second)[0].returncode, 0)
        obj['upstream_specs'] = []
        self.save(second, obj)
        self.assertNotEqual(self.run_check(second)[0].returncode, 0)
        other = json.loads((self.root / first).read_text())
        other['capability'] = 'different'
        other['gate']['review']['context']['capability'] = 'different'
        self.save(first, other)
        second = self.stage(2, [first])
        self.assertNotEqual(self.run_check(second)[0].returncode, 0)

    def test_paths_and_review_pins_fail_closed(self):
        import copy
        name = self.stage(1)
        original = json.loads((self.root / name).read_text())
        outside = self.root.parent / (self.root.name + '-outside.txt')
        outside.write_text('synthetic outside')
        self.addCleanup(outside.unlink)
        alias = self.root / 'alias.txt'
        alias.symlink_to(outside)
        bad_paths = [str(outside), '../' + outside.name, 'alias.txt', './stage1/authorization.txt']
        for bad in bad_paths:
            obj = copy.deepcopy(original)
            obj['gate']['review']['authorization'] = {
                'path': bad, 'sha256': hashlib.sha256((self.root / bad).read_bytes()).hexdigest()}
            self.save(name, obj)
            with self.subTest(path=bad):
                proc, data = self.run_check(name)
                self.assertEqual(proc.returncode, 1, data)
                self.assertEqual(data['status'], 'invalid', data)
        for sha in ['NOT-A-HASH', original['gate']['review']['artifact']['sha256'].upper()]:
            obj = copy.deepcopy(original)
            obj['gate']['review']['artifact']['sha256'] = sha
            self.save(name, obj)
            self.assertEqual(self.run_check(name)[1]['status'], 'invalid')

    def test_missing_or_modified_authorization_is_not_current(self):
        name = self.stage(1)
        self.write('stage1/authorization.txt', 'changed synthetic reference')
        self.assertEqual(self.run_check(name)[1]['status'], 'stale')
        (self.root / 'stage1/authorization.txt').unlink()
        self.assertNotEqual(self.run_check(name)[0].returncode, 0)

    def test_review_date_required_and_duplicate_json_keys_rejected(self):
        name = self.stage(1)
        obj = json.loads((self.root / name).read_text())
        obj['gate']['gate_review_date'] = None
        self.save(name, obj)
        self.assertEqual(self.run_check(name)[1]['status'], 'invalid')
        name = self.stage(1)
        text = (self.root / name).read_text()
        text = text.replace('"blocking_gaps": []', '"blocking_gaps": ["G-1"], "blocking_gaps": []')
        self.write(name, text)
        self.assertEqual(self.run_check(name)[1]['status'], 'invalid')

    def test_all_eight_stages_and_withdrawn_upstream_record(self):
        name = self.stage(1)
        for number in range(2, 10):
            name = self.stage(number, [name])
        self.assertEqual(self.run_check(name)[1]['status'], 'current')
        first = json.loads((self.root / 'stage1/spec.json').read_text())
        first['gate']['completeness_gate_passed'] = False
        self.save('stage1/spec.json', first)
        for number in range(2, 10):
            path = f'stage{number}/spec.json'
            obj = json.loads((self.root / path).read_text())
            obj['gate']['review']['upstream_specs'] = [self.pin(f'stage{number-1}/spec.json')]
            self.save(path, obj)
        self.assertEqual(self.run_check(name)[1]['status'], 'unreviewed')


if __name__ == '__main__':
    unittest.main()

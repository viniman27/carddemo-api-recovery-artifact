import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / 'pretest_config.py'

class PretestConfigTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location('pretest_config', MODULE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_fixture_registry_requires_hash_provenance_exposure_and_no_oracle_answer(self):
        mod = self.load_module()
        registry = json.loads((ROOT / 'fixture-registry.sample.json').read_text())
        result = mod.validate_fixture_registry(registry)
        self.assertEqual(result['ok'], True, result)
        first = registry['fixtures'][0]
        for key in ['track', 'fixtureId', 'contentSha256', 'provenance', 'exposure']:
            self.assertIn(key, first)
        self.assertEqual(first['exposure']['label'], 'technical-only')
        self.assertNotIn('expectedAnswer', first)
        self.assertNotIn('oracle', first)

    def test_campaign_config_is_non_executing_and_rejects_until_freeze(self):
        mod = self.load_module()
        cfg = json.loads((ROOT / 'campaign-config.sample.json').read_text())
        result = mod.validate_campaign_config(cfg)
        self.assertEqual(result['ok'], True, result)
        self.assertEqual(mod.execution_decision(cfg)['allowed'], False)
        self.assertIn('freeze approval missing', mod.execution_decision(cfg)['reasons'])
        self.assertEqual(cfg['execution']['mode'], 'schema_only_non_executing')
        self.assertEqual(cfg['reset']['default'], 'fresh_dir_per_run')
        self.assertEqual(cfg['statefulSequences']['status'], 'pending')
        for item in ['t1.model', 't1.budget', 't1.seed', 't2.budget', 't2.seed', 't3.modelOracle', 't4.unionPolicy']:
            self.assertIn(item, cfg['pendingFreezeChoices'])

    def test_campaign_config_rejects_missing_pending_choices(self):
        mod = self.load_module()
        cfg = json.loads((ROOT / 'campaign-config.sample.json').read_text())
        cfg['pendingFreezeChoices'] = []
        result = mod.validate_campaign_config(cfg)
        self.assertEqual(result['ok'], False)
        self.assertTrue(any('pendingFreezeChoices' in e for e in result['errors']))

    def test_execution_decision_does_not_treat_labels_as_authenticated_authorization(self):
        mod = self.load_module()
        cfg = json.loads((ROOT / 'campaign-config.sample.json').read_text())
        cfg['approval']['freezeStatus'] = 'approved_frozen'
        cfg['execution']['mode'] = 'approved_campaign_execution'
        decision = mod.execution_decision(cfg)
        self.assertEqual(decision['allowed'], False)
        self.assertIn('no official runner/authenticated execution gate is implemented', decision['reasons'])

    def test_fixture_registry_can_validate_explicit_three_track_technical_selection(self):
        mod = self.load_module()
        fixtures = []
        for track in ['posting', 'interest', 'reporting']:
            fx = {
                'fixtureId': f'{track}-local-tech',
                'track': track,
                'materializer': {'kind': 'builtin_technical_smoke'},
                'provenance': {'class': 'local_synthetic_support'},
                'exposure': {'label': 'technical-only', 'notExtractionInput': True, 'notOracle': True},
                'reset': {'default': 'fresh_dir_per_run'},
            }
            fx['contentSha256'] = mod.fixture_descriptor_sha256(fx)
            fixtures.append(fx)
        result = mod.validate_fixture_registry({'kind': 'p3-local-technical-fixture-selection', 'status': 'technical_local_only', 'fixtures': fixtures})
        self.assertEqual(result['ok'], True, result)

if __name__ == '__main__':
    unittest.main()

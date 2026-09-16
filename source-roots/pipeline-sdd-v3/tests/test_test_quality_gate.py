"""Synthetic test-quality gate fixtures only; no campaign approval is created."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / 'pipeline/tools/check_test_quality_gate.py'


class TestQualityGateTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def write_manifest(self, data):
        path = self.root / 'test-quality-gate.json'
        path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        return path

    def valid_manifest(self):
        return {
            'run_id': 'synthetic-run',
            'capability': 'synthetic-capability',
            'stage9_api_ready_for_testing': True,
            'stage9_handoff_evidence': {'path': 'stage9/HANDOFF.md', 'api_ready_for_testing': True, 'campaign_ready': False},
            'prospective_freeze': {'frozen_before_execution': True, 'freeze_id': 'synthetic-freeze-v1', 'frozen_at': '2026-01-01T00:00:00Z'},
            'descriptive_post_observation_supplementation': {'used': False, 'separate_from_freeze': True},
            'coverage': {
                'denominator': {'known': True, 'count': 4, 'source': 'synthetic-obligation-inventory'},
                'counts': {'executed': 2, 'not_executed': 1, 'inconclusive': 1, 'not_applicable': 0},
                'not_executed_items': [{'id': 'O-4', 'reason': 'no prepared valid stimulus'}],
                'inconclusive_items': [{'id': 'O-3', 'reason': 'runtime observation missing'}],
                'gap_items': [{'id': 'G-1', 'reason': 'no independent oracle yet'}],
                'target_policy': 'fixed inventory; no percent target chosen after seeing results'
            },
            'fixtures': {'per_case_reset': True, 'reset_evidence': 'synthetic reset transcript', 'resource_snapshot_compared': True},
            'oracles': [
                {
                    'id': 'O-contract', 'question': 'schema', 'kind': 'contract_schema',
                    'authority_source': {'type': 'approved_contract', 'path': 'contract/openapi.yaml'},
                    'independent_from_llm_outputs': True, 'wrong_output_counterexamples': ['malformed body']
                },
                {
                    'id': 'O-business', 'question': 'business obligation', 'kind': 'business_semantic',
                    'authority_source': {'type': 'source_evidence', 'path': 'legacy/evidence.md'},
                    'independent_from_llm_outputs': True, 'wrong_output_counterexamples': ['accepted amount with wrong balance']
                }
            ],
            'campaigns': [
                {'id': 'T1', 'role': 'generator', 'bad_outputs_preserved_in_results': True},
                {'id': 'T2', 'role': 'openapi_fuzz', 'mode': 'pure_openapi', 'domain_fuzz_separate': True},
                {'id': 'T3', 'role': 'model_based', 'guards_bound_to_checker': True, 'transitions_bound_to_checker': True},
                {'id': 'T4', 'role': 'union', 'no_new_cases': True, 'fresh_reset_per_case': True, 'not_counted_as_independent_replica': True}
            ],
            'mutations': {'used': True, 'scope': 'test_checker_only', 'source_artifacts_altered': False},
            'traceability': {'checks_to_obligations': {'O-business': ['R-1']}, 'gaps_separate': True},
            'human_review': {'required': True, 'approval_claimed_by_tool': False}
        }

    def run_check(self, data):
        path = self.write_manifest(data)
        proc = subprocess.run([sys.executable, str(TOOL), str(path)], capture_output=True, text=True)
        self.assertTrue(proc.stdout.strip().startswith('{'), proc.stderr or proc.stdout)
        return proc, json.loads(proc.stdout)

    def test_valid_manifest_reports_ready_without_approval(self):
        proc, data = self.run_check(self.valid_manifest())
        self.assertEqual(proc.returncode, 0, data)
        self.assertEqual(data['status'], 'ready_for_review')
        self.assertIs(data['human_approval_granted'], False)

    def test_schema_only_oracle_cannot_qualify_business_obligations(self):
        data = self.valid_manifest()
        data['oracles'] = [data['oracles'][0]]
        proc, result = self.run_check(data)
        self.assertEqual(proc.returncode, 1, result)
        self.assertEqual(result['status'], 'fail')
        self.assertIn('no independent business/semantic oracle', '\n'.join(result['errors']))

    def test_business_oracle_from_llm_output_is_rejected(self):
        data = self.valid_manifest()
        data['oracles'][1]['authority_source'] = {'type': 'llm_output', 'path': 'generated/answer.md'}
        data['oracles'][1]['independent_from_llm_outputs'] = False
        proc, result = self.run_check(data)
        self.assertEqual(proc.returncode, 1, result)
        self.assertIn('LLM output cannot be oracle authority', '\n'.join(result['errors']))

    def test_unknown_denominator_and_all_not_executed_are_not_ready(self):
        data = self.valid_manifest()
        data['coverage']['denominator']['known'] = False
        data['coverage']['counts'] = {'executed': 0, 'not_executed': 4, 'inconclusive': 0, 'not_applicable': 0}
        proc, result = self.run_check(data)
        self.assertEqual(proc.returncode, 1, result)
        text = '\n'.join(result['errors'])
        self.assertIn('coverage denominator must be known', text)
        self.assertIn('all obligations not executed', text)

    def test_campaign_specific_integrity_rules_fail_closed(self):
        data = self.valid_manifest()
        for campaign in data['campaigns']:
            if campaign['id'] == 'T4':
                campaign['no_new_cases'] = False
            if campaign['id'] == 'T3':
                campaign['guards_bound_to_checker'] = False
        proc, result = self.run_check(data)
        self.assertEqual(proc.returncode, 1, result)
        text = '\n'.join(result['errors'])
        self.assertIn('T3 model guards/transitions must be bound to executable checkers', text)
        self.assertIn('T4 union must not introduce new cases', text)


if __name__ == '__main__':
    unittest.main()

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    spec = importlib.util.spec_from_file_location('validate_catalog', ROOT / 'validate_catalog.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_catalog():
    return json.loads((ROOT / 'scenario-catalog.json').read_text(encoding='utf-8'))


class ComplementaryValidationV2Tests(unittest.TestCase):
    def test_catalog_has_one_source_backed_scenario_per_obligation_not_count_proxy(self):
        mod = load_validator()
        cat = load_catalog()
        result = mod.validate(cat, ROOT)
        self.assertEqual(result['status'], 'PASS', result)
        self.assertEqual(result['checked']['obligations'], 25)
        self.assertEqual(result['checked']['scenarioRecords'], 25)
        self.assertEqual(result['checked']['coveredObligations'], 25)
        self.assertIs(result['checked']['coverageIsByObligationIds'], True)

    def test_status_denominators_separate_not_executed_unchecked_inconclusive_nonexpressible_noobservation_failed_pass_and_na(self):
        mod = load_validator()
        cat = load_catalog()
        statuses = cat['statusVocabulary']
        for required in ['not_executed','unchecked','inconclusive','nonexpressible','no_observation','failed','pass','not_applicable']:
            self.assertIn(required, statuses)
        d = cat['denominators']
        self.assertIs(d['semanticDenominatorPolicy']['neverUseAll525AsSemanticDenominator'], True)
        self.assertEqual(d['preExecution']['allCandidateApplicableCells']['not_executed'], 175)
        self.assertEqual(d['preExecution']['allCandidateApplicableCells']['unchecked'], 175)
        self.assertEqual(d['preExecution']['allOperationCells']['not_applicable'], 350)
        self.assertNotIn('unobservable', d['preExecution']['allOperationCells'])
        self.assertEqual(mod.validate(cat, ROOT)['status'], 'PASS')

    def test_t3_mbt_is_separate_battery_with_shared_independent_checker_assessment(self):
        cat = load_catalog()
        t3 = cat['testConditionDesign']['T3']
        self.assertEqual(t3['role'], 'separate_mbt_battery')
        self.assertTrue(t3['modelSource']['transitionWitnessesPath'].endswith('reference-executable-v4/evidence/obligation-witnesses.json'))
        self.assertIs(t3['preserveMethod'], True)
        shared = cat['sharedOracleBattery']
        self.assertEqual(shared['reusedAcross'], ['T1','T2','T3','T4'])
        self.assertEqual(shared['independentCheckerAssessment'], 'pending_review_not_granted_by_this_design')

    def test_contract_mapping_is_7_contracts_21_operations_175_applicable_350_na(self):
        mod = load_validator()
        cat = load_catalog()
        result = mod.validate(cat, ROOT)
        self.assertEqual(result['checked']['contracts'], 7)
        self.assertEqual(result['checked']['operations'], 21)
        self.assertEqual(result['checked']['mappingCells'], 525)
        self.assertEqual(result['checked']['applicableCells'], 175)
        self.assertEqual(result['checked']['notApplicableCells'], 350)

    def test_source_pins_and_schema_reference_are_verified(self):
        mod = load_validator()
        cat = load_catalog()
        self.assertEqual(cat['schemaRef'], 'schema/complementary-validation-v2.schema.json')
        result = mod.validate(cat, ROOT)
        self.assertEqual(result['checked']['schemaRef'], 'schema/complementary-validation-v2.schema.json')
        self.assertIs(result['checked']['sourceHashesVerified'], True)

if __name__ == '__main__':
    unittest.main()

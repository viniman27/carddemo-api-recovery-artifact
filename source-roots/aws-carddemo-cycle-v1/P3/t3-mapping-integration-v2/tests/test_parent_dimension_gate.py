import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from mapping_integration import build_enriched_plan

class ParentDimensionGate(unittest.TestCase):
    def test_upstream_generation_denial_cannot_be_overridden_by_recipe(self):
        p3 = ROOT.parent
        matrix = json.loads((p3/'applicability-mapping-v3/applicability_matrix.json').read_text())
        recipes = json.loads((p3/'t3-mapping-recipes-v1/recipes.json').read_text())
        denied = {f"{o['obligationId']}::{c['contractId']}::{c['operation']['operationId']}" for o in matrix['obligations'] for c in o['contractMappings'] if not c['applicabilityDimensions']['generative_admissible']}
        result = build_enriched_plan(matrix, recipes)
        reopened = [c['cellId'] for c in result['cells'] if c['cellId'] in denied and c['executableEligible']]
        self.assertEqual(reopened, [])

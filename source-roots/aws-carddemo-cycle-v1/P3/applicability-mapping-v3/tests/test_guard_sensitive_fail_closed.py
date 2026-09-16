import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(os.environ.get("MATRIX_ROOT", Path(__file__).resolve().parents[1])).resolve()
CYCLE = ROOT.parents[1]
COORDINATOR_RECOVERY = CYCLE / "P3" / "applicability-review-v2-recovery" / "coordinator-recovery.json"
GUARD_SENSITIVE = {
    "POSTTRAN-OBL-004", "POSTTRAN-OBL-005", "POSTTRAN-OBL-006", "POSTTRAN-OBL-007",
    "INTCALC-OBL-004", "INTCALC-OBL-005", "INTCALC-OBL-007",
    "TRANREPT-OBL-003", "TRANREPT-OBL-004", "TRANREPT-OBL-005", "TRANREPT-OBL-007", "TRANREPT-OBL-008",
}
DIAGNOSTICS_ONLY = {"POSTTRAN-OBL-008", "POSTTRAN-OBL-009", "TRANREPT-OBL-003", "TRANREPT-OBL-007", "TRANREPT-OBL-008"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def all_mappings(matrix):
    for obligation in matrix["obligations"]:
        for mapping in obligation["contractMappings"]:
            yield obligation, mapping


def unblocked_guard_sensitive_without_variant(matrix):
    affected = []
    for obligation, mapping in all_mappings(matrix):
        oid = obligation["obligationId"]
        if oid not in GUARD_SENSITIVE or oid in DIAGNOSTICS_ONLY:
            continue
        plan = mapping["t3DeterministicMapping"]
        status = mapping["applicabilityStatus"]
        if status not in {"expressible_by_surface", "conditioned_on_external_fixture"}:
            continue
        if plan.get("fixtureVariant"):
            continue
        if plan.get("generativeUse") != "blocked":
            affected.append((oid, mapping["contractId"]))
    return affected


class GuardSensitiveFailClosedTests(unittest.TestCase):
    def test_v2_recovery_count_is_reproduced_when_pointed_at_v2(self):
        matrix = load_json(ROOT / "applicability_matrix.json")
        affected = unblocked_guard_sensitive_without_variant(matrix)
        if ROOT.name == "applicability-mapping-v2":
            recovery = load_json(COORDINATOR_RECOVERY)
            self.assertEqual(len(affected), recovery["confirmed_guard_sensitive_admissibility_without_variant_or_block"])
        else:
            self.assertEqual(affected, [])

    def test_guard_sensitive_cells_require_named_variant_or_are_blocked_even_when_surface_expressible(self):
        matrix = load_json(ROOT / "applicability_matrix.json")
        failures = unblocked_guard_sensitive_without_variant(matrix)
        self.assertEqual(failures, [])
        surface_blocked = []
        for obligation, mapping in all_mappings(matrix):
            if obligation["obligationId"] not in GUARD_SENSITIVE:
                continue
            if mapping["applicabilityStatus"] == "expressible_by_surface" and mapping["t3DeterministicMapping"].get("generativeUse") == "blocked":
                self.assertTrue(mapping["applicabilityDimensions"]["surface_expressible"])
                self.assertFalse(mapping["applicabilityDimensions"]["generative_admissible"])
                surface_blocked.append((obligation["obligationId"], mapping["contractId"]))
        self.assertTrue(surface_blocked)

    def test_rich_bindings_are_not_branch_variant_selection(self):
        matrix = load_json(ROOT / "applicability_matrix.json")
        binding_cells = []
        for obligation, mapping in all_mappings(matrix):
            if obligation["obligationId"] not in GUARD_SENSITIVE:
                continue
            selectors = mapping["t3DeterministicMapping"].get("fieldSelectors", [])
            if any(s.get("field") == "bindings" for s in selectors):
                binding_cells.append((obligation["obligationId"], mapping["contractId"], mapping["t3DeterministicMapping"]))
        for oid, cid, plan in binding_cells:
            self.assertIsNone(plan.get("fixtureVariant"), (oid, cid))
            self.assertEqual(plan.get("generativeUse"), "blocked", (oid, cid))

    def test_sdd_empty_body_is_immutable(self):
        matrix = load_json(ROOT / "applicability_matrix.json")
        sdd = [m for _, m in all_mappings(matrix) if m["contractId"] == "E3-01-SDD-stage6r3"]
        self.assertEqual(len(sdd), 25)
        for mapping in sdd:
            plan = mapping["t3DeterministicMapping"]
            schema = mapping["operation"]["requestSchema"]
            self.assertEqual(schema.get("properties"), [])
            self.assertIs(schema.get("additionalProperties"), False)
            self.assertEqual(plan.get("requestBody"), {})
            self.assertEqual(plan.get("fieldSelectors"), [])
            self.assertIs(plan.get("newSelectorsIntroduced"), False)

    def test_blocked_selectors_are_not_usable(self):
        matrix = load_json(ROOT / "applicability_matrix.json")
        failures = []
        for obligation, mapping in all_mappings(matrix):
            plan = mapping["t3DeterministicMapping"]
            if plan.get("generativeUse") == "blocked":
                if mapping["applicabilityDimensions"].get("generative_admissible") is not False:
                    failures.append((obligation["obligationId"], mapping["contractId"], "generative_admissible"))
                if plan.get("fieldSelectors"):
                    failures.append((obligation["obligationId"], mapping["contractId"], "fieldSelectors"))
                if plan.get("selectorUsableForGeneration") is not False:
                    failures.append((obligation["obligationId"], mapping["contractId"], "selectorUsableForGeneration"))
        self.assertEqual(failures, [])

    def test_validator_cli_passes_for_v3(self):
        if ROOT.name != "applicability-mapping-v3":
            self.skipTest("validator target is v3-only")
        result = subprocess.run([sys.executable, str(ROOT / "tools" / "validate_matrix.py")], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()

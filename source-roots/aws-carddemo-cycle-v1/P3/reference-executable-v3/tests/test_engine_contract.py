import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

import sys
sys.path.insert(0, str(ROOT))

from executable_reference import (
    ModelError,
    ValidationError,
    apply_effect,
    eval_guard,
    load_model,
    step,
    traverse,
    validate_model,
    validate_source_pins,
)


class ExecutableReferenceEngineTests(unittest.TestCase):
    def setUp(self):
        self.model = load_model(ROOT / "model.json")

    def test_validate_accepts_packaged_model_and_source_pins(self):
        report = validate_model(self.model, root=ROOT)
        self.assertEqual([], report["errors"])
        self.assertEqual("executable_draft_needs_review", report["status"])
        pin_report = validate_source_pins(self.model, ROOT)
        self.assertEqual([], pin_report["errors"])
        self.assertGreaterEqual(pin_report["checkedAnchors"], 30)

    def test_guard_type_and_domain_literals_are_rejected(self):
        bad = copy.deepcopy(self.model)
        bad["capabilities"][0]["transitions"][0]["guard"] = {
            "op": "eq", "left": {"var": "open_status"}, "right": {"value": True, "type": "bool"}
        }
        with self.assertRaises(ValidationError):
            validate_model(bad, root=ROOT, raise_on_error=True)
        bad = copy.deepcopy(self.model)
        bad["capabilities"][0]["transitions"][0]["guard"] = {
            "op": "eq", "left": {"var": "open_status"}, "right": {"value": "99", "type": "enum"}
        }
        with self.assertRaises(ValidationError):
            validate_model(bad, root=ROOT, raise_on_error=True)

    def test_broken_refs_and_unknown_effects_are_rejected(self):
        bad = copy.deepcopy(self.model)
        bad["capabilities"][0]["transitions"][0]["obligationRefs"] = ["NO-SUCH-OBL"]
        with self.assertRaises(ValidationError):
            validate_model(bad, root=ROOT, raise_on_error=True)
        bad = copy.deepcopy(self.model)
        bad["capabilities"][0]["transitions"][0]["effects"].append({"op": "not_a_known_effect"})
        with self.assertRaises(ValidationError):
            validate_model(bad, root=ROOT, raise_on_error=True)

    def test_eval_guard_is_manual_and_unknown_is_not_boolean_truthy_or_falsey(self):
        valuation = {"read_status": "UnknownEOF"}
        self.assertEqual("unknown", eval_guard({"op": "unknown", "var": "read_status"}, valuation, self.model["capabilities"][0]))
        self.assertFalse(eval_guard({"op": "eq", "left": {"var": "read_status"}, "right": {"value": "10", "type": "enum"}}, valuation, self.model["capabilities"][0]))
        self.assertFalse(eval_guard({"op": "eq", "left": {"var": "read_status"}, "right": {"value": "00", "type": "enum"}}, valuation, self.model["capabilities"][0]))

    def test_apply_effect_updates_structured_state_and_emits_observable_attempts(self):
        state = {"state": "P_ACCOUNT_REWRITE", "values": {"attempts": [], "events": [], "reject_reason": "none"}}
        nxt = apply_effect(state, {"op": "set", "var": "reject_reason", "value": "109"}, self.model["capabilities"][0])
        nxt = apply_effect(nxt, {"op": "emit", "event": "account_rewrite_invalid_key_continues"}, self.model["capabilities"][0])
        self.assertEqual("109", nxt["values"]["reject_reason"])
        self.assertEqual(["account_rewrite_invalid_key_continues"], nxt["values"]["events"])

    def test_step_posttran_109_continues_to_tranfile_not_abend(self):
        trace = step(self.model, "CBTRN02C_POSTTRAN", "P_ACCOUNT_REWRITE", {"rewrite_invalid_key": True})
        self.assertEqual(["POSTTRAN-T020"], [x["transitionId"] for x in trace])
        self.assertEqual("P_TRANFILE_WRITE", trace[0]["state"]["state"])
        self.assertIn("tranfile_write_attempt_pending", trace[0]["state"]["values"]["events"])
        self.assertNotEqual("P_ABEND", trace[0]["state"]["state"])

    def test_step_tranrept_out_of_range_skips_detail_and_accrual(self):
        trace = step(self.model, "CBTRN03C_TRANREPT", "R_LOOP", {"read_status": "00", "date_window": "out_of_range"})
        self.assertEqual(["TRANREPT-T009"], [x["transitionId"] for x in trace])
        events = trace[0]["state"]["values"]["events"]
        self.assertIn("tranrept_skip_detail_out_of_range", events)
        self.assertNotIn("report_detail_attempt", events)
        self.assertNotIn("account_accrual_attempt", events)

    def test_step_intcalc_eof_exits_without_final_account_update(self):
        trace = step(self.model, "CBACT04C_INTCALC", "I_OPENED", {"tcatbal_read_status": "10"})
        self.assertEqual(["INTCALC-T006"], [x["transitionId"] for x in trace])
        events = trace[0]["state"]["values"]["events"]
        self.assertIn("intcalc_eof_no_final_account_update", events)
        self.assertNotIn("account_update_attempt", events)

    def test_bfs_traversal_is_deterministic_and_reports_frontier_omitted_unknown(self):
        a = traverse(self.model, "CBTRN02C_POSTTRAN", max_depth=3, max_paths=2)
        b = traverse(self.model, "CBTRN02C_POSTTRAN", max_depth=3, max_paths=2)
        self.assertEqual(a, b)
        self.assertIn("frontier", a)
        self.assertIn("unknown", a)
        self.assertTrue(a["unknown"])

    def test_loop_bounds_are_enforced(self):
        report = traverse(self.model, "CBTRN02C_POSTTRAN", max_depth=20, max_paths=500)
        self.assertLessEqual(report["loopVisits"].get("P_OPENED", 0), self.model["capabilities"][0]["loopPolicy"]["bounds"]["daily_records"] + 1)

    def test_source_anchored_obligation_mutations_are_rejected(self):
        for transition_id, bad_event in [
            ("POSTTRAN-T020", "abend"),
            ("TRANREPT-T009", "report_detail_attempt"),
            ("INTCALC-T006", "account_update_attempt"),
        ]:
            bad = copy.deepcopy(self.model)
            for cap in bad["capabilities"]:
                for tr in cap["transitions"]:
                    if tr["id"] == transition_id:
                        tr["effects"].append({"op": "emit", "event": bad_event})
            with self.assertRaises(ValidationError, msg=transition_id):
                validate_model(bad, root=ROOT, raise_on_error=True)


if __name__ == "__main__":
    unittest.main()

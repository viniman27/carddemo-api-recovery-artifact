import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_stage4_adapter import PACKAGE, sha256_file, write_json
from test_stage7_adapter import Stage7AdapterTests
import adapter
import stage7_adapter

try:
    import stage8_adapter
    from stage8_adapter import main as stage8_main
except ModuleNotFoundError:  # RED before implementation
    stage8_adapter = None
    stage8_main = None


class Stage8AdapterTests(Stage7AdapterTests):
    def add_approved_stage7_r2(self, run_root: Path) -> dict[str, Path]:
        r3_paths = self.add_approved_stage6_r3(run_root)
        original = self.add_unapproved_stage7_original_and_r2_feedback(run_root)
        with self.stage7_hash_patches(r3_paths), self.stage7_r2_hash_patches(original), mock.patch.object(stage7_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])):
            self.assertEqual(stage7_adapter.main(self.args(run_root, run_root.parent, ["/sdd:spec-init", "adapter-behavior-carddemo-r2", "--stage", "7"])), 0)
        r2_dir = run_root / "specs/adapter-behavior-carddemo-r2"
        r2_artifact = r2_dir / "requirements.md"
        r2_artifact.write_text(
            "# Approved Stage 7 r2 Adapter Behavior\n\n"
            "Capability identity: unselected-stage-1-scope-only. Mandatory tracks: posting, interest, reporting.\n"
            "Internal protocols: INV invocation, RES resources, CAP capture, CONV conversion, FAIL failures, STATE state, RESP response.\n"
            "Capture rules distinguish stale, misattributed, truncated and empty captures from observed empty business outputs.\n"
            "Conversions preserve available items: [] versus unavailable/503 and known failure/500. Partial failures separate known from unknown.\n"
            "State isolation/reset is not promised as runtime proof. EOF and internal reason 109 rules remain documentary obligations.\n"
            "R-1..R-20 obligations remain mapped; positive, negative and counterexample scenarios must be specified later without execution.\n",
            encoding="utf-8",
        )
        spec = json.loads((r2_dir / "spec.json").read_text(encoding="utf-8"))
        spec["approvals"]["requirements"]["approved"] = True
        spec["gate"] = spec.get("gate", {})
        spec["gate"].update({"completeness_gate_passed": True, "gate_review_date": "2026-09-14", "blocking_gaps": []})
        review = run_root / "STAGE7-R2-COUNTEREXAMPLE-REVIEW.md"
        review.write_text("# Stage7 r2 counterexample review\n\nAccepted for Stage8 DOCUMENT scenarios only; no implementation, COBOL/runtime validation, approvals, E1/E2 or stage9.\n", encoding="utf-8")
        findings = r2_dir / "stage7-r2-verification.json"
        write_json(findings, {"stage": 7, "artifact_sha256": sha256_file(r2_artifact), "criteria_passed": 31, "total_criteria": 31})
        auth = run_root / "reviews/stage-7-r2-authorization.json"
        write_json(auth, {
            "reviewer": "unit-test",
            "user_message": "structured authorization; prose not parsed",
            "decision": "approve",
            "stage": 7,
            "run_id": "E3-01",
            "artifact": {"path": "specs/adapter-behavior-carddemo-r2/requirements.md", "sha256": sha256_file(r2_artifact)},
            "scope": "Approve Stage7 r2 documentary adapter behavior and authorize Stage8 Semantic Validation specification. No implementation, COBOL execution or experimental test execution authorized.",
            "review_reference": {"path": "STAGE7-R2-COUNTEREXAMPLE-REVIEW.md", "sha256": sha256_file(review)},
            "findings_reference": {"path": "specs/adapter-behavior-carddemo-r2/stage7-r2-verification.json", "sha256": sha256_file(findings)},
        })
        spec["gate"]["review"] = {
            "reviewer": "unit-test",
            "decision": "approve",
            "context": {"run_id": "E3-01", "capability": spec["capability"], "pipeline_stage": 7, "artifact_type": "adapter-behavior"},
            "artifact": {"path": "specs/adapter-behavior-carddemo-r2/requirements.md", "sha256": sha256_file(r2_artifact)},
            "authorization": {"path": "reviews/stage-7-r2-authorization.json", "sha256": sha256_file(auth)},
            "review_reference": {"path": "STAGE7-R2-COUNTEREXAMPLE-REVIEW.md", "sha256": sha256_file(review)},
            "findings_reference": {"path": "specs/adapter-behavior-carddemo-r2/stage7-r2-verification.json", "sha256": sha256_file(findings)},
            "upstream_specs": [{"path": "specs/api-contract-carddemo-r3/spec.json", "sha256": sha256_file(run_root / "specs/api-contract-carddemo-r3/spec.json")}],
        }
        write_json(r2_dir / "spec.json", spec)
        # Keep inherited stage7 recursive checks pointed at this temporary run.
        for name, path_key in {
            "EXPECTED_STAGE6_R3_ARTIFACT_SHA256": "r3_artifact",
            "EXPECTED_STAGE6_R3_AUTHORIZATION_SHA256": "r3_auth",
            "EXPECTED_STAGE6_R3_REVIEW_SHA256": "r3_review",
            "EXPECTED_STAGE6_R3_FINDINGS_SHA256": "r3_findings",
            "EXPECTED_R2_STAGE6_SPEC_SHA256": "r2_spec",
            "EXPECTED_R2_STAGE6_ARTIFACT_SHA256": "r2_artifact",
            "EXPECTED_R2_STAGE6_REQUEST_SHA256": "r2_request",
            "EXPECTED_R2_STAGE6_METADATA_SHA256": "r2_metadata",
            "EXPECTED_R2_STAGE6_AUTHORIZATION_SHA256": "r2_auth",
            "EXPECTED_R2_EMPTY_REVIEW_SHA256": "review",
            "EXPECTED_R2_DIRECTED_FEEDBACK_SHA256": "feedback",
            "EXPECTED_ORIGINAL_STAGE7_SPEC_SHA256": "stage7_spec",
            "EXPECTED_ORIGINAL_STAGE7_ARTIFACT_SHA256": "stage7_artifact",
            "EXPECTED_ORIGINAL_STAGE7_RAW_SHA256": "stage7_raw",
            "EXPECTED_ORIGINAL_STAGE7_REQUEST_SHA256": "stage7_request",
            "EXPECTED_ORIGINAL_STAGE7_METADATA_SHA256": "stage7_metadata",
            "EXPECTED_ORIGINAL_STAGE7_AUTHORIZATION_SHA256": "stage7_auth",
            "EXPECTED_STAGE7_R1_DIRECTED_FEEDBACK_SHA256": "stage7_feedback",
            "EXPECTED_STAGE7_DESIGN_EVIDENCE_REVIEW_SHA256": "stage7_review",
        }.items():
            setattr(stage7_adapter, name, sha256_file({**r3_paths, **original}[path_key]))
        out = {**r3_paths, **original, "stage7r2_spec": r2_dir / "spec.json", "stage7r2_artifact": r2_artifact, "stage7r2_auth": auth, "stage7r2_review": review, "stage7r2_findings": findings}
        return out

    def stage8_hash_patches(self, paths):
        return mock.patch.multiple(
            stage8_adapter,
            EXPECTED_STAGE7_R2_ARTIFACT_SHA256=sha256_file(paths["stage7r2_artifact"]),
            EXPECTED_STAGE7_R2_AUTHORIZATION_SHA256=sha256_file(paths["stage7r2_auth"]),
            EXPECTED_STAGE7_R2_REVIEW_SHA256=sha256_file(paths["stage7r2_review"]),
            EXPECTED_STAGE7_R2_FINDINGS_SHA256=sha256_file(paths["stage7r2_findings"]),
            EXPECTED_REAL_CORPUS_FILE_COUNT=len(json.loads(PACKAGE.read_text())["files"]),
        )

    def test_stage8_init_prepare_payload_documents_scenarios_obligations_and_preserves_chain(self):
        self.assertIsNotNone(stage8_main)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            paths = self.add_approved_stage7_r2(run_root)
            with self.stage8_hash_patches(paths):
                self.assertEqual(stage8_main(self.args(run_root, tmp, ["/sdd:spec-init", "semantic-validation-carddemo", "--stage", "8"])), 0)
                self.assertEqual(stage8_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "semantic-validation-carddemo", "--stage", "8", "--prepare-only"])), 0)
            spec = json.loads((run_root / "specs/semantic-validation-carddemo/spec.json").read_text(encoding="utf-8"))
            self.assertEqual(spec["pipeline_stage"], 8)
            self.assertEqual(spec["artifact_type"], "semantic-validation")
            self.assertEqual(spec["upstream_specs"], ["specs/adapter-behavior-carddemo-r2/spec.json"])
            self.assertFalse(spec["approvals"]["requirements"]["approved"])
            prepared = json.loads((run_root / "prepared/semantic-validation-carddemo/request.json").read_text(encoding="utf-8"))
            prompt = json.loads(prepared["input"][0]["content"])
            text = json.dumps(prompt, ensure_ascii=False)
            for token in [
                "Stage 8 Semantic Validation Specification", "DOCUMENT scenarios", "expected obligations", "evidence acceptance criteria",
                "Stage7 protocols", "Stage6 clauses", "R-1..R-20", "reverse completeness", "positive", "negative", "counterexample",
                "empirical uncertainties explicitly unresolved", "not fake test results", "stale", "misattributed", "truncated", "empty capture",
                "conversions", "partial failures", "known vs unknown", "state isolation/reset not promised", "EOF", "109", "no implementation",
                "no COBOL", "no runtime validation", "no approvals", "no stage9", "No E1/E2", "Do not call scenarios T1 experimental execution",
            ]:
                self.assertIn(token, text)
            pins = prompt["input_pins"]
            self.assertEqual([p["path"] for p in pins["upstream_specs"]][-1], "specs/adapter-behavior-carddemo-r2/spec.json")
            self.assertEqual([p["path"] for p in pins["authorizations"]][-1], "reviews/stage-7-r2-authorization.json")
            self.assertIn("stage7_r2_review_reference", pins)
            self.assertEqual(prompt["approved_upstream"]["stage7_r2_requirements_md"], paths["stage7r2_artifact"].read_text(encoding="utf-8"))
            self.assertEqual(prompt["input_pins"]["actual_corpus_file_count"], len(json.loads(PACKAGE.read_text())["files"]))
            self.assertIn("settings/templates/pipeline/semantic-validation-spec.md", [d["path"] for d in prompt["framework_context"]])

    def test_stage8_fails_closed_on_missing_mandatory_semantic_template(self):
        self.assertIsNotNone(stage8_main)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"; framework = tmp / "framework"
            import shutil
            shutil.copytree(Path(self.args(run_root, tmp, ["x", "y"])[self.args(run_root, tmp, ["x", "y"]).index("--framework-root") + 1]), framework)
            (framework / "settings/templates/pipeline/semantic-validation-spec.md").unlink()
            self.init_and_approve_stage5(run_root, tmp)
            paths = self.add_approved_stage7_r2(run_root)
            with self.stage8_hash_patches(paths):
                args = self.args(run_root, tmp, ["/sdd:spec-init", "semantic-validation-carddemo", "--stage", "8"])
                args[args.index("--framework-root") + 1] = str(framework)
                self.assertEqual(stage8_main(args), 2)

    def test_stage8_blocks_reduced_corpus_stale_unapproved_upstream_and_contradictory_auth(self):
        cases = ["reduced_corpus", "tampered_artifact", "unapproved_stage7r2", "auth_reject", "auth_stage", "artifact_hash", "review_hash", "findings_hash"]
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as d:
                tmp = Path(d); run_root = tmp / "run"
                self.init_and_approve_stage5(run_root, tmp)
                paths = self.add_approved_stage7_r2(run_root)
                if case == "tampered_artifact":
                    paths["stage7r2_artifact"].write_text("tampered\n", encoding="utf-8")
                elif case == "unapproved_stage7r2":
                    spec = json.loads(paths["stage7r2_spec"].read_text(encoding="utf-8")); spec["approvals"]["requirements"]["approved"] = False; write_json(paths["stage7r2_spec"], spec)
                elif case.startswith("auth") or case.endswith("hash"):
                    auth = json.loads(paths["stage7r2_auth"].read_text(encoding="utf-8"))
                    if case == "auth_reject": auth["decision"] = "reject"; auth["approved"] = True
                    if case == "auth_stage": auth["stage"] = 8
                    if case == "artifact_hash": auth["artifact"]["sha256"] = "0" * 64
                    if case == "review_hash": auth["review_reference"]["sha256"] = "0" * 64
                    if case == "findings_hash": auth["findings_reference"]["sha256"] = "0" * 64
                    write_json(paths["stage7r2_auth"], auth)
                    spec = json.loads(paths["stage7r2_spec"].read_text(encoding="utf-8")); spec["gate"]["review"]["authorization"]["sha256"] = sha256_file(paths["stage7r2_auth"]); write_json(paths["stage7r2_spec"], spec)
                patch_ctx = self.stage8_hash_patches(paths)
                if case == "reduced_corpus":
                    patch_ctx = mock.patch.multiple(stage8_adapter, EXPECTED_STAGE7_R2_ARTIFACT_SHA256=sha256_file(paths["stage7r2_artifact"]), EXPECTED_STAGE7_R2_AUTHORIZATION_SHA256=sha256_file(paths["stage7r2_auth"]), EXPECTED_STAGE7_R2_REVIEW_SHA256=sha256_file(paths["stage7r2_review"]), EXPECTED_STAGE7_R2_FINDINGS_SHA256=sha256_file(paths["stage7r2_findings"]))
                with patch_ctx:
                    self.assertEqual(stage8_main(self.args(run_root, tmp, ["/sdd:spec-init", "semantic-validation-carddemo", "--stage", "8"])), 2)

    def test_stage8_execute_rechecks_auth_request_tamper_and_refuses_stage9(self):
        self.assertIsNotNone(stage8_main)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            paths = self.add_approved_stage7_r2(run_root)
            with self.stage8_hash_patches(paths):
                self.assertEqual(stage8_main(self.args(run_root, tmp, ["/sdd:spec-init", "semantic-validation-carddemo", "--stage", "8"])), 0)
                self.assertEqual(stage8_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "semantic-validation-carddemo", "--stage", "8", "--prepare-only"])), 0)
                self.assertEqual(stage8_main(self.args(run_root, tmp, ["/sdd:spec-init", "semantic-validation-carddemo", "--stage", "9"])), 2)
            meta = json.loads((run_root / "prepared/semantic-validation-carddemo/metadata.json").read_text(encoding="utf-8"))
            wrong_stage = tmp / "wrong-stage.json"; write_json(wrong_stage, {"approved": True, "stage": 9, "run_id": "E3-01", "model": adapter.MODEL, "base_url": adapter.BASE_URL, "request_sha256": meta["request_sha256"]})
            wrong_hash = tmp / "wrong-hash.json"; write_json(wrong_hash, {"approved": True, "stage": 8, "run_id": "E3-01", "model": adapter.MODEL, "base_url": adapter.BASE_URL, "request_sha256": "0" * 64})
            request_path = run_root / "prepared/semantic-validation-carddemo/request.json"
            request = json.loads(request_path.read_text(encoding="utf-8")); request["store"] = True; write_json(request_path, request)
            good = tmp / "good.json"; write_json(good, {"approved": True, "stage": 8, "run_id": "E3-01", "model": adapter.MODEL, "base_url": adapter.BASE_URL, "request_sha256": meta["request_sha256"]})
            with self.stage8_hash_patches(paths):
                self.assertEqual(stage8_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "semantic-validation-carddemo", "--stage", "8", "--execute", "--authorization-file", str(wrong_stage)])), 2)
                self.assertEqual(stage8_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "semantic-validation-carddemo", "--stage", "8", "--execute", "--authorization-file", str(wrong_hash)])), 2)
                self.assertEqual(stage8_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "semantic-validation-carddemo", "--stage", "8", "--execute", "--authorization-file", str(good)])), 2)


if __name__ == "__main__":
    import unittest
    unittest.main()

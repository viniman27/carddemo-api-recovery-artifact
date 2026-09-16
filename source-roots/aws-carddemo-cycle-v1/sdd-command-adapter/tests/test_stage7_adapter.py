import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_stage4_adapter import FRAMEWORK, PACKAGE, sha256_file, write_json
from test_stage6_adapter import Stage6AdapterTests
import adapter
import stage6_adapter

try:
    import stage7_adapter
    from stage7_adapter import main as stage7_main
except ModuleNotFoundError:  # RED before implementation
    stage7_adapter = None
    stage7_main = None


class Stage7AdapterTests(Stage6AdapterTests):
    def add_approved_stage6_r3(self, run_root: Path) -> dict[str, Path]:
        paths = self.add_unapproved_stage6_r2_and_r3_inputs(run_root)
        r3_dir = run_root / "specs/api-contract-carddemo-r3"
        r3_dir.mkdir(parents=True, exist_ok=True)
        r3_artifact = r3_dir / "requirements.md"
        r3_artifact.write_text(
            "# Approved Stage 6 r3 API Contract\n\n"
            "Capability identity: unselected-stage-1-scope-only.\n"
            "Mandatory tracks: posting, interest, reporting.\n"
            "Operations: POST /posting, POST /interest, POST /reporting.\n"
            "External input design; ordered outputs; observed empty represented sequence available items: []; unavailable means no observation; "
            "known technical failure maps to 500; no observation maps to 503; successful observations may be 200.\n"
            "Preserve reason 109 internal, EOF limitations, unknown not false, no invented telemetry, readiness, durability, reset or retry guarantees.\n"
            + "\n".join(f"R-{i} contract disposition." for i in range(1, 21)) + "\n",
            encoding="utf-8",
        )
        write_json(r3_dir / "spec.json", {
            "feature_name": "api-contract-carddemo-r3",
            "artifact_path": "specs/api-contract-carddemo-r3/requirements.md",
            "pipeline_stage": 6,
            "artifact_type": "api-contract",
            "capability": "unselected-stage-1-scope-only",
            "run_id": "E3-01",
            "mandatory_tracks": ["posting", "interest", "reporting"],
            "upstream_specs": ["specs/canonical-data-boundary-carddemo/spec.json"],
            "approvals": {"requirements": {"generated": True, "approved": True}},
            "gate": {"completeness_gate_passed": True, "gate_review_date": "2026-09-13", "blocking_gaps": [], "review": {}},
            "ready_for_implementation": False,
            "revision_of": "api-contract-carddemo-r2",
        })
        review = run_root / "STAGE6-R3-COUNTEREXAMPLE-REVIEW.md"
        review.write_text("# Stage6 r3 review\n\nAccepted current Stage6r3 for Stage7 Adapter Behavior spec only. No Stage8 or implementation.\n", encoding="utf-8")
        findings = r3_dir / "stage6-r3-verification.json"
        write_json(findings, {"stage": 6, "artifact_sha256": sha256_file(r3_artifact), "criteria_passed": 10, "total_criteria": 10})
        auth = run_root / "reviews/stage-6-r3-authorization.json"
        write_json(auth, {
            "approved": True,
            "decision": "approve",
            "stage": 6,
            "run_id": "E3-01",
            "artifact": {"path": "specs/api-contract-carddemo-r3/requirements.md", "sha256": sha256_file(r3_artifact)},
            "scope": "Approve Stage6 r3 documentary contract. Authorize Stage7 Adapter Behavior specification for posting, interest and reporting. No Stage8, API implementation or COBOL execution authorization.",
            "review_reference": {"path": "STAGE6-R3-COUNTEREXAMPLE-REVIEW.md", "sha256": sha256_file(review)},
            "findings_reference": {"path": "specs/api-contract-carddemo-r3/stage6-r3-verification.json", "sha256": sha256_file(findings)},
        })
        spec = json.loads((r3_dir / "spec.json").read_text(encoding="utf-8"))
        spec["gate"]["review"] = {
            "reviewer": "unit-test",
            "decision": "approve",
            "context": {"run_id": "E3-01", "capability": "unselected-stage-1-scope-only", "pipeline_stage": 6, "artifact_type": "api-contract"},
            "artifact": {"path": "specs/api-contract-carddemo-r3/requirements.md", "sha256": sha256_file(r3_artifact)},
            "authorization": {"path": "reviews/stage-6-r3-authorization.json", "sha256": sha256_file(auth)},
            "review_reference": {"path": "STAGE6-R3-COUNTEREXAMPLE-REVIEW.md", "sha256": sha256_file(review)},
            "findings_reference": {"path": "specs/api-contract-carddemo-r3/stage6-r3-verification.json", "sha256": sha256_file(findings)},
            "upstream_specs": [{"path": "specs/canonical-data-boundary-carddemo/spec.json", "sha256": sha256_file(run_root / "specs/canonical-data-boundary-carddemo/spec.json")}],
        }
        write_json(r3_dir / "spec.json", spec)
        paths.update({"r3_spec": r3_dir / "spec.json", "r3_artifact": r3_artifact, "r3_auth": auth, "r3_review": review, "r3_findings": findings})
        return paths

    def stage7_hash_patches(self, paths):
        return mock.patch.multiple(
            stage7_adapter,
            EXPECTED_STAGE6_R3_ARTIFACT_SHA256=sha256_file(paths["r3_artifact"]),
            EXPECTED_STAGE6_R3_AUTHORIZATION_SHA256=sha256_file(paths["r3_auth"]),
            EXPECTED_STAGE6_R3_REVIEW_SHA256=sha256_file(paths["r3_review"]),
            EXPECTED_STAGE6_R3_FINDINGS_SHA256=sha256_file(paths["r3_findings"]),
            EXPECTED_R2_STAGE6_SPEC_SHA256=sha256_file(paths["r2_spec"]),
            EXPECTED_R2_STAGE6_ARTIFACT_SHA256=sha256_file(paths["r2_artifact"]),
            EXPECTED_R2_STAGE6_REQUEST_SHA256=sha256_file(paths["r2_request"]),
            EXPECTED_R2_STAGE6_METADATA_SHA256=sha256_file(paths["r2_metadata"]),
            EXPECTED_R2_STAGE6_AUTHORIZATION_SHA256=sha256_file(paths["r2_auth"]),
            EXPECTED_R2_EMPTY_REVIEW_SHA256=sha256_file(paths["review"]),
            EXPECTED_R2_DIRECTED_FEEDBACK_SHA256=sha256_file(paths["feedback"]),
        )

    def add_unapproved_stage7_original_and_r2_feedback(self, run_root: Path) -> dict[str, Path]:
        original_dir = run_root / "specs/adapter-behavior-carddemo"
        original_dir.mkdir(parents=True, exist_ok=True)
        original_artifact = original_dir / "requirements.md"
        original_artifact.write_text(
            "# Failed original Stage 7 Adapter Behavior\n\n"
            "Preserve 109/EOF/order/multiplicity, but G31 remains open and no human approval exists.\n"
            "The original must remain an exact unapproved artifact.\n",
            encoding="utf-8",
        )
        write_json(original_dir / "spec.json", {
            "feature_name": "adapter-behavior-carddemo",
            "pipeline_stage": 7,
            "artifact_type": "adapter-behavior",
            "capability": "unselected-stage-1-scope-only",
            "run_id": "E3-01",
            "mandatory_tracks": ["posting", "interest", "reporting"],
            "upstream_specs": ["specs/api-contract-carddemo-r3/spec.json"],
            "approvals": {"requirements": {"generated": True, "approved": False}},
            "gate": {"completeness_gate_passed": False, "blocking_gaps": ["G31"]},
            "ready_for_implementation": False,
        })
        prepared = run_root / "prepared/adapter-behavior-carddemo"
        execution = prepared / "execution"
        execution.mkdir(parents=True, exist_ok=True)
        request = {"model": adapter.MODEL, "store": False, "stream": True, "input": [{"role": "user", "content": "stage7 original request"}]}
        write_json(prepared / "request.json", request)
        write_json(execution / "request-body.json", request)
        request_sha = hashlib.sha256(json.dumps(request, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        metadata = {"stage": 7, "run_id": "E3-01", "feature": "adapter-behavior-carddemo", "request_sha256": request_sha, "execute_authorized": False}
        write_json(prepared / "metadata.json", metadata)
        (execution / "scope-original.md").write_text(original_artifact.read_text(encoding="utf-8"), encoding="utf-8")
        (execution / "response.sse").write_text("data: {\"type\": \"response.completed\"}\n\n", encoding="utf-8")
        exec_meta = dict(metadata)
        exec_meta["execute_authorized"] = True
        write_json(execution / "metadata.json", exec_meta)
        write_json(run_root / "stage7-generation-authorization.json", {
            "approved": True, "stage": 7, "run_id": "E3-01", "model": adapter.MODEL, "base_url": adapter.BASE_URL,
            "request_sha256": request_sha, "scope": "Authorize original Stage7 generation only; not human approval of the generated artifact.",
        })
        feedback = run_root / "reviews/stage-7-r1-directed-feedback.md"
        feedback.write_text(
            "# Stage 7 r1 Directed Feedback\n\n"
            "Revise documentary behavior only: add concrete internal invocation/resource/capture/conversion/failure/state records, field-by-field provenance, stale/truncated/zero-length vs observed empty, three-state documentary closure matrix, and preserve G31 as external human approval never authored here.\n",
            encoding="utf-8",
        )
        review = run_root / "STAGE7-DESIGN-EVIDENCE-REVIEW.md"
        review.write_text(
            "# Stage 7 Design Evidence Review\n\n"
            "Do not fabricate runtime proof. Preserve 109, EOF, order, multiplicity and no public route/status/request changes. Separate later empirical obligations from decisions now.\n",
            encoding="utf-8",
        )
        return {
            "stage7_spec": original_dir / "spec.json",
            "stage7_artifact": original_artifact,
            "stage7_output": execution / "scope-original.md",
            "stage7_raw": execution / "response.sse",
            "stage7_request": prepared / "request.json",
            "stage7_metadata": prepared / "metadata.json",
            "stage7_auth": run_root / "stage7-generation-authorization.json",
            "stage7_feedback": feedback,
            "stage7_review": review,
        }

    def stage7_r2_hash_patches(self, paths):
        patch_values = {
            "EXPECTED_ORIGINAL_STAGE7_SPEC_SHA256": sha256_file(paths["stage7_spec"]),
            "EXPECTED_ORIGINAL_STAGE7_ARTIFACT_SHA256": sha256_file(paths["stage7_artifact"]),
            "EXPECTED_ORIGINAL_STAGE7_RAW_SHA256": sha256_file(paths["stage7_raw"]),
            "EXPECTED_ORIGINAL_STAGE7_REQUEST_SHA256": sha256_file(paths["stage7_request"]),
            "EXPECTED_ORIGINAL_STAGE7_METADATA_SHA256": sha256_file(paths["stage7_metadata"]),
            "EXPECTED_ORIGINAL_STAGE7_AUTHORIZATION_SHA256": sha256_file(paths["stage7_auth"]),
            "EXPECTED_STAGE7_R1_DIRECTED_FEEDBACK_SHA256": sha256_file(paths["stage7_feedback"]),
            "EXPECTED_STAGE7_DESIGN_EVIDENCE_REVIEW_SHA256": sha256_file(paths["stage7_review"]),
        }
        return mock.patch.multiple(stage7_adapter, **patch_values)

    def test_stage7_r2_init_prepare_pins_original_feedback_review_and_documentary_revision_scope(self):
        self.assertIsNotNone(stage7_main)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            r3_paths = self.add_approved_stage6_r3(run_root)
            original = self.add_unapproved_stage7_original_and_r2_feedback(run_root)
            with self.stage7_hash_patches(r3_paths), self.stage7_r2_hash_patches(original), mock.patch.object(stage7_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])):
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-init", "adapter-behavior-carddemo-r2", "--stage", "7"])), 0)
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "adapter-behavior-carddemo-r2", "--stage", "7", "--prepare-only"])), 0)
            spec = json.loads((run_root / "specs/adapter-behavior-carddemo-r2/spec.json").read_text(encoding="utf-8"))
            self.assertEqual(spec["revision_of"], "adapter-behavior-carddemo")
            self.assertFalse(spec["approvals"]["requirements"]["approved"])
            prepared = json.loads((run_root / "prepared/adapter-behavior-carddemo-r2/request.json").read_text(encoding="utf-8"))
            prompt = json.loads(prepared["input"][0]["content"])
            self.assertEqual(prompt["failed_original_stage7"]["requirements_md"], original["stage7_artifact"].read_text(encoding="utf-8"))
            self.assertEqual(prompt["stage7_revision_feedback"]["directed_feedback_md"], original["stage7_feedback"].read_text(encoding="utf-8"))
            self.assertEqual(prompt["stage7_revision_feedback"]["design_evidence_review_md"], original["stage7_review"].read_text(encoding="utf-8"))
            pins = prompt["input_pins"]
            self.assertEqual([p["path"] for p in pins["failed_original_stage7"]], [
                "specs/adapter-behavior-carddemo/spec.json",
                "specs/adapter-behavior-carddemo/requirements.md",
                "prepared/adapter-behavior-carddemo/execution/scope-original.md",
                "prepared/adapter-behavior-carddemo/execution/response.sse",
                "prepared/adapter-behavior-carddemo/request.json",
                "prepared/adapter-behavior-carddemo/metadata.json",
                "stage7-generation-authorization.json",
            ])
            self.assertEqual([p["path"] for p in pins["stage7_r2_revision_feedback"]], ["reviews/stage-7-r1-directed-feedback.md", "STAGE7-DESIGN-EVIDENCE-REVIEW.md"])
            text = json.dumps(prompt, ensure_ascii=False)
            for token in [
                "versioned Stage 7 r2 revision", "concrete internal invocation/resource/capture/conversion/failure/state records",
                "field-by-field provenance", "stale/truncated/zero-length", "observed empty", "no new public fields/routes/status/request changes",
                "no fabricated runtime proof", "preserve109/EOF/order/multiplicity", "three-state documentary closure matrix",
                "G31 remains external human approval", "NEVER author its approval", "actual feedback verbatim", "later empirical obligations",
            ]:
                self.assertIn(token, text)

    def test_stage7_r2_blocks_stale_original_feedback_review_approved_original_and_upstream_stale(self):
        cases = ["stage7_artifact", "stage7_output", "stage7_raw", "stage7_request", "stage7_metadata", "stage7_auth", "stage7_auth_stage", "stage7_auth_request", "stage7_feedback", "stage7_review", "approved_original", "approved_upstream_stale"]
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as d:
                tmp = Path(d); run_root = tmp / "run"
                self.init_and_approve_stage5(run_root, tmp)
                r3_paths = self.add_approved_stage6_r3(run_root)
                original = self.add_unapproved_stage7_original_and_r2_feedback(run_root)
                ctx1 = self.stage7_hash_patches(r3_paths)
                ctx2 = self.stage7_r2_hash_patches(original)
                if case == "approved_original":
                    spec = json.loads(original["stage7_spec"].read_text(encoding="utf-8"))
                    spec["approvals"]["requirements"]["approved"] = True
                    spec["gate"]["completeness_gate_passed"] = True
                    write_json(original["stage7_spec"], spec)
                elif case == "approved_upstream_stale":
                    r3_paths["r3_review"].write_text("tampered upstream\n", encoding="utf-8")
                elif case == "stage7_auth_stage":
                    auth = json.loads(original["stage7_auth"].read_text(encoding="utf-8"))
                    auth["stage"] = 8
                    write_json(original["stage7_auth"], auth)
                elif case == "stage7_auth_request":
                    auth = json.loads(original["stage7_auth"].read_text(encoding="utf-8"))
                    auth["request_sha256"] = "0" * 64
                    write_json(original["stage7_auth"], auth)
                else:
                    original[case].write_text("tampered\n", encoding="utf-8")
                with ctx1, ctx2, mock.patch.object(stage7_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])):
                    self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-init", "adapter-behavior-carddemo-r2", "--stage", "7"])), 2)

    def test_stage7_r2_execute_rechecks_auth_stage_request_and_refuses_stage8(self):
        self.assertIsNotNone(stage7_main)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            r3_paths = self.add_approved_stage6_r3(run_root)
            original = self.add_unapproved_stage7_original_and_r2_feedback(run_root)
            with self.stage7_hash_patches(r3_paths), self.stage7_r2_hash_patches(original), mock.patch.object(stage7_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])):
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-init", "adapter-behavior-carddemo-r2", "--stage", "7"])), 0)
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "adapter-behavior-carddemo-r2", "--stage", "7", "--prepare-only"])), 0)
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-init", "adapter-behavior-carddemo-r2", "--stage", "8"])), 2)
            meta = json.loads((run_root / "prepared/adapter-behavior-carddemo-r2/metadata.json").read_text(encoding="utf-8"))
            wrong_stage = tmp / "wrong-stage.json"
            write_json(wrong_stage, {"approved": True, "stage": 8, "run_id": "E3-01", "model": adapter.MODEL, "base_url": adapter.BASE_URL, "request_sha256": meta["request_sha256"]})
            wrong_hash = tmp / "wrong-hash.json"
            write_json(wrong_hash, {"approved": True, "stage": 7, "run_id": "E3-01", "model": adapter.MODEL, "base_url": adapter.BASE_URL, "request_sha256": "0" * 64})
            with self.stage7_hash_patches(r3_paths), self.stage7_r2_hash_patches(original), mock.patch.object(stage7_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])):
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "adapter-behavior-carddemo-r2", "--stage", "7", "--execute", "--authorization-file", str(wrong_stage)])), 2)
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "adapter-behavior-carddemo-r2", "--stage", "7", "--execute", "--authorization-file", str(wrong_hash)])), 2)

    def test_init_prepare_payload_preserves_approved_stage6r3_and_stage7_document_scope(self):
        self.assertIsNotNone(stage7_main)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            paths = self.add_approved_stage6_r3(run_root)
            with self.stage7_hash_patches(paths), mock.patch.object(stage7_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])):
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-init", "adapter-behavior-carddemo", "--stage", "7"])), 0)
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "adapter-behavior-carddemo", "--stage", "7", "--prepare-only"])), 0)
            spec = json.loads((run_root / "specs/adapter-behavior-carddemo/spec.json").read_text(encoding="utf-8"))
            self.assertEqual(spec["pipeline_stage"], 7)
            self.assertEqual(spec["artifact_type"], "adapter-behavior")
            self.assertEqual(spec["upstream_specs"], ["specs/api-contract-carddemo-r3/spec.json"])
            self.assertEqual(spec["capability"], "unselected-stage-1-scope-only")
            self.assertEqual(spec["mandatory_tracks"], ["posting", "interest", "reporting"])
            prepared = json.loads((run_root / "prepared/adapter-behavior-carddemo/request.json").read_text(encoding="utf-8"))
            prompt = json.loads(prepared["input"][0]["content"])
            text = json.dumps(prompt, ensure_ascii=False)
            for token in [
                "Stage 7 Adapter Behavior Specification", "DOCUMENT behavior mapping only", "external input binding responsibilities",
                "observation acquisition and provenance vs fabrication", "observed-empty vs unavailable", "known failure", "500", "observations", "200", "observations503 none",
                "ordered outputs", "no invented telemetry", "readiness", "durability", "reset", "retry", "reason 109 internal", "EOF limitations",
                "Distinguish design proposals vs demonstrated runtime", "bounded gaps", "no implementation", "no code", "no COBOL", "No Stage8", "No E1/E2",
            ]:
                self.assertIn(token, text)
            self.assertEqual(prompt["approved_upstream"]["stage6_r3_requirements_md"], paths["r3_artifact"].read_text(encoding="utf-8"))
            self.assertEqual(prompt["approved_upstream"]["stage6_r3_authorization"], json.loads(paths["r3_auth"].read_text(encoding="utf-8")))
            self.assertEqual(prompt["approved_upstream"]["stage6_r3_counterexample_review_md"], paths["r3_review"].read_text(encoding="utf-8"))
            self.assertEqual(prompt["approved_upstream"]["stage6_r3_findings_json"], json.loads(paths["r3_findings"].read_text(encoding="utf-8")))
            self.assertEqual([p["path"] for p in prompt["input_pins"]["upstream_specs"]], [
                "specs/pipeline-scope-carddemo/spec.json", "specs/capability-selection-carddemo-r2/spec.json",
                "specs/legacy-evidence-carddemo-r2/spec.json", "specs/capability-semantics-carddemo/spec.json",
                "specs/canonical-data-boundary-carddemo/spec.json", "specs/api-contract-carddemo-r3/spec.json"])
            self.assertEqual(len(prompt["input_pins"]["authorizations"]), 6)
            self.assertEqual([doc["path"] for doc in prompt["framework_context"]][-1], "settings/templates/pipeline/adapter-behavior-spec.md")
            self.assertEqual(len(prompt["framework_context"]), 13)
            self.assertEqual(prompt["input_pins"]["actual_corpus_file_count"], len(json.loads(PACKAGE.read_text())["files"]))
            meta = json.loads((run_root / "prepared/adapter-behavior-carddemo/metadata.json").read_text())
            self.assertEqual(meta["stage"], 7)
            self.assertFalse(meta["execute_authorized"])

    def test_stage7_blocks_stale_unapproved_stage6r3_prepare_execute_and_stage8(self):
        self.assertIsNotNone(stage7_main)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            paths = self.add_approved_stage6_r3(run_root)
            with self.stage7_hash_patches(paths), mock.patch.object(stage7_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])):
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-init", "adapter-behavior-carddemo", "--stage", "7"])), 0)
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "adapter-behavior-carddemo", "--stage", "7", "--prepare-only"])), 0)
            meta = json.loads((run_root / "prepared/adapter-behavior-carddemo/metadata.json").read_text())
            good_auth = tmp / "stage7-auth.json"
            write_json(good_auth, {"approved": True, "stage": 7, "run_id": "E3-01", "model": adapter.MODEL, "base_url": adapter.BASE_URL, "request_sha256": meta["request_sha256"]})
            (run_root / "STAGE6-R3-COUNTEREXAMPLE-REVIEW.md").write_text("tampered\n", encoding="utf-8")
            with self.stage7_hash_patches(paths), mock.patch.object(stage7_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])):
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-init", "another-adapter", "--stage", "7"])), 2)
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "adapter-behavior-carddemo", "--stage", "7", "--prepare-only"])), 2)
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "adapter-behavior-carddemo", "--stage", "7", "--execute", "--authorization-file", str(good_auth)])), 2)
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-init", "adapter-behavior-carddemo", "--stage", "8"])), 2)

    def test_stage7_authorization_decision_hash_stage_mismatches_and_approved_r2_are_blocked(self):
        self.assertIsNotNone(stage7_main)
        cases = ["reject", "deny", "stage", "artifact_hash", "review_hash", "findings_hash", "approved_r2"]
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as d:
                tmp = Path(d); run_root = tmp / "run"
                self.init_and_approve_stage5(run_root, tmp)
                paths = self.add_approved_stage6_r3(run_root)
                if case == "approved_r2":
                    spec = json.loads(paths["r2_spec"].read_text(encoding="utf-8"))
                    spec["approvals"]["requirements"]["approved"] = True
                    spec["gate"]["completeness_gate_passed"] = True
                    write_json(paths["r2_spec"], spec)
                else:
                    auth = json.loads(paths["r3_auth"].read_text(encoding="utf-8"))
                    if case == "reject":
                        auth["decision"] = "reject"; auth["approved"] = True
                    elif case == "deny":
                        auth["decision"] = "deny"; auth["approved"] = True
                    elif case == "stage":
                        auth["stage"] = 7
                    elif case == "artifact_hash":
                        auth["artifact"]["sha256"] = "0" * 64
                    elif case == "review_hash":
                        auth["review_reference"]["sha256"] = "0" * 64
                    elif case == "findings_hash":
                        auth["findings_reference"]["sha256"] = "0" * 64
                    write_json(paths["r3_auth"], auth)
                    r3_spec = json.loads(paths["r3_spec"].read_text(encoding="utf-8"))
                    r3_spec["gate"]["review"]["authorization"]["sha256"] = sha256_file(paths["r3_auth"])
                    write_json(paths["r3_spec"], r3_spec)
                with self.stage7_hash_patches(paths), mock.patch.object(stage7_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])):
                    self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-init", "adapter-behavior-carddemo", "--stage", "7"])), 2)

    def test_stage7_authorization_is_structured_not_prose_token_based(self):
        self.assertIsNotNone(stage7_main)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            paths = self.add_approved_stage6_r3(run_root)
            auth = json.loads(paths["r3_auth"].read_text(encoding="utf-8"))
            auth["scope"] = "Structured approval recorded in fields; prose is not parsed as authorization."
            paths["r3_auth"].write_text(json.dumps(auth, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            r3_spec = json.loads(paths["r3_spec"].read_text(encoding="utf-8"))
            r3_spec["gate"]["review"]["authorization"]["sha256"] = sha256_file(paths["r3_auth"])
            write_json(paths["r3_spec"], r3_spec)
            with self.stage7_hash_patches(paths), mock.patch.object(stage7_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])):
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-init", "adapter-behavior-carddemo", "--stage", "7"])), 0)

    def test_stage7_missing_mandatory_framework_doc_fails_closed(self):
        self.assertIsNotNone(stage7_main)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"; framework = tmp / "framework"
            shutil.copytree(FRAMEWORK, framework)
            self.init_and_approve_stage5(run_root, tmp)
            paths = self.add_approved_stage6_r3(run_root)
            missing_doc = framework / "settings/rules/traceability.md"
            missing_doc.unlink()
            with self.stage7_hash_patches(paths), mock.patch.object(stage7_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])):
                args = self.args(run_root, tmp, ["/sdd:spec-init", "adapter-behavior-carddemo", "--stage", "7"])
                fw_idx = args.index("--framework-root") + 1
                args[fw_idx] = str(framework)
                self.assertEqual(stage7_main(args), 2)

    def test_production_stage7_refuses_reduced_corpus_without_cli_bypass(self):
        self.assertIsNotNone(stage7_main)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            paths = self.add_approved_stage6_r3(run_root)
            before = paths["r3_spec"].read_bytes()
            with self.stage7_hash_patches(paths):
                self.assertEqual(stage7_main(self.args(run_root, tmp, ["/sdd:spec-init", "adapter-behavior-carddemo", "--stage", "7"])), 2)
            self.assertEqual(paths["r3_spec"].read_bytes(), before)
            self.assertFalse((run_root / "specs/adapter-behavior-carddemo").exists())


if __name__ == "__main__":
    import unittest
    unittest.main()

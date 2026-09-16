import hashlib
import json
import sys
import tempfile
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stage5_adapter import main as stage5_main
from test_stage4_adapter import CORPUS, FRAMEWORK, PACKAGE, sha256_file, write_json
from test_stage5_adapter import Stage5AdapterTests

try:
    import stage6_adapter
    from stage6_adapter import main as stage6_main
except ModuleNotFoundError:  # RED before implementation
    stage6_main = None


class Stage6AdapterTests(Stage5AdapterTests):
    def stage6_fixture_main(self, argv):
        expected = len(json.loads(PACKAGE.read_text(encoding="utf-8"))["files"])
        with mock.patch.object(stage6_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", expected):
            return stage6_main(argv)

    def init_and_approve_stage5(self, run_root: Path, tmp_path: Path) -> None:
        self.init_and_approve_stage4(run_root, tmp_path)
        self.assertEqual(stage5_main(self.args(run_root, tmp_path, ["/sdd:spec-init", "canonical-data-boundary-carddemo", "--stage", "5"])), 0)
        spec_path = run_root / "specs/canonical-data-boundary-carddemo/spec.json"
        artifact = run_root / "specs/canonical-data-boundary-carddemo/requirements.md"
        stage5_review = run_root / "STAGE5-COUNTEREXAMPLE-REVIEW.md"
        stage5_findings = run_root / "stage5-counterexample-findings.json"
        stage5_review.parent.mkdir(parents=True, exist_ok=True)
        stage5_review.write_text("# Stage 5 Counterexample Review\n\nReview pins D-2..D-8, 17 types, mandatory tracks, and R-1..R-20 reverse completeness.\n", encoding="utf-8")
        write_json(stage5_findings, {"synthetic_test_fixture": True, "stage": 5, "findings": ["D/type/field/outcome traceability sampled"]})
        rules = "\n".join(f"| Operation {i} | E-{i} | R-{i} | D-{2 + ((i - 1) % 7)} / Type-{1 + ((i - 1) % 17)} / field-{i} / outcome-{i} | pending Stage 6 |" for i in range(1, 21))
        artifact.write_text(
            "# Synthetic approved stage-5 canonical data boundary\n\n"
            "Capability identity: unselected-stage-1-scope-only\n\n"
            "Mandatory tracks: posting, interest, reporting.\n\n"
            "Design decisions: D-2 D-3 D-4 D-5 D-6 D-7 D-8.\n\n"
            "Types: " + ", ".join(f"Type-{i}" for i in range(1, 18)) + ".\n\n"
            "Fields and outcomes preserve Stage5 D/type/field/outcome traceability.\n\n"
            "## Reverse Completeness\n| Operation / rule / effect | Evidence | Semantic representation | Boundary treatment | Contract destination / exclusion / gap |\n"
            "|---|---|---|---|---|\n" + rules + "\n",
            encoding="utf-8",
        )
        auth = run_root / "reviews/stage-5-authorization.json"
        write_json(auth, {
            "synthetic_test_fixture": True, "approved": True, "stage": 5, "run_id": "E3-01", "decision": "approve",
            "conditional_scope": "Stage 6 may prepare only API contract; no adapter implementation, COBOL execution or Stage 7.",
            "review_reference": {"path": "STAGE5-COUNTEREXAMPLE-REVIEW.md", "sha256": sha256_file(stage5_review)},
            "artifact": {"path": "specs/canonical-data-boundary-carddemo/requirements.md", "sha256": sha256_file(artifact)},
            "findings_reference": {"path": "stage5-counterexample-findings.json", "sha256": sha256_file(stage5_findings)},
        })
        spec = json.loads(spec_path.read_text())
        spec["approvals"]["requirements"]["generated"] = True
        spec["approvals"]["requirements"]["approved"] = True
        spec["gate"] = {"completeness_gate_passed": True, "gate_review_date": "2026-09-12", "blocking_gaps": [],
            "review": {"synthetic_test_fixture": True, "reviewer": "unit-test", "decision": "approve",
                "context": {"run_id": spec["run_id"], "capability": spec["capability"], "pipeline_stage": 5, "artifact_type": "canonical-data-boundary"},
                "artifact": {"path": "specs/canonical-data-boundary-carddemo/requirements.md", "sha256": sha256_file(artifact)},
                "authorization": {"path": "reviews/stage-5-authorization.json", "sha256": sha256_file(auth)},
                "attachments": [
                    {"path": "STAGE5-COUNTEREXAMPLE-REVIEW.md", "sha256": sha256_file(stage5_review)},
                    {"path": "stage5-counterexample-findings.json", "sha256": sha256_file(stage5_findings)},
                ],
                "upstream_specs": [{"path": "specs/capability-semantics-carddemo/spec.json", "sha256": sha256_file(run_root / "specs/capability-semantics-carddemo/spec.json")}]}}
        write_json(spec_path, spec)

    def test_init_prepare_payload_preserves_stage6_api_contract_scope_and_exact_inputs(self):
        self.assertIsNotNone(stage6_main)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-init", "api-contract-carddemo", "--stage", "6"])), 0)
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo", "--stage", "6", "--prepare-only"])), 0)
            spec = json.loads((run_root / "specs/api-contract-carddemo/spec.json").read_text())
            parent = json.loads((run_root / "specs/canonical-data-boundary-carddemo/spec.json").read_text())
            self.assertEqual(spec["capability"], parent["capability"])
            self.assertEqual(spec["pipeline_stage"], 6)
            self.assertEqual(spec["artifact_type"], "api-contract")
            self.assertEqual(spec["upstream_specs"], ["specs/canonical-data-boundary-carddemo/spec.json"])
            prepared = json.loads((run_root / "prepared/api-contract-carddemo/request.json").read_text())
            payload_text = json.dumps(prepared, ensure_ascii=False)
            for token in [
                "posting", "interest", "reporting", "API Contract Specification", "OpenAPI", "representable",
                "Stage5 D/type/field/outcome traceability", "reverse completeness", "R-1..R-20",
                "D-2", "D-8", "17 types", "unselected-stage-1-scope-only",
                "STAGE5-COUNTEREXAMPLE-REVIEW.md", "stage5-counterexample-findings.json",
                "blocking gaps", "unsupported", "no arbitrary closure",
            ]:
                self.assertIn(token, payload_text)
            for forbidden in [
                "must not invent units", "rounding", "date validity", "durability", "EOF", "retry safety",
                "must not expose internal state as guaranteed observability", "No adapter behavior", "No Stage7", "No COBOL execution",
            ]:
                self.assertIn(forbidden, payload_text)
            prompt = json.loads(prepared["input"][0]["content"])
            self.assertEqual(prompt["approved_upstream"]["stage5_requirements_md"], (run_root / "specs/canonical-data-boundary-carddemo/requirements.md").read_text())
            self.assertEqual(prompt["approved_upstream"]["stage5_counterexample_review_md"], (run_root / "STAGE5-COUNTEREXAMPLE-REVIEW.md").read_text())
            self.assertEqual(prompt["approved_upstream"]["stage5_counterexample_findings_json"], json.loads((run_root / "stage5-counterexample-findings.json").read_text()))
            self.assertEqual(len(prompt["source_bodies"]), len(json.loads(PACKAGE.read_text())["files"]))
            framework_by_path = {doc["path"]: doc["content"] for doc in prompt["framework_context"]}
            self.assertEqual(framework_by_path["settings/templates/pipeline/api-contract-spec.md"], (FRAMEWORK / "settings/templates/pipeline/api-contract-spec.md").read_text())
            pins = prompt["input_pins"]
            self.assertEqual([p["path"] for p in pins["upstream_specs"]], [
                "specs/pipeline-scope-carddemo/spec.json", "specs/capability-selection-carddemo-r2/spec.json",
                "specs/legacy-evidence-carddemo-r2/spec.json", "specs/capability-semantics-carddemo/spec.json",
                "specs/canonical-data-boundary-carddemo/spec.json"])
            self.assertEqual(len(pins["authorizations"]), 5)
            self.assertEqual([p["path"] for p in pins["review_attachments"]], ["reviews/STAGE4-COUNTEREXAMPLE-REVIEW.md", "STAGE5-COUNTEREXAMPLE-REVIEW.md", "stage5-counterexample-findings.json"])
            self.assertEqual(pins["actual_corpus_file_count"], len(json.loads(PACKAGE.read_text())["files"]))
            meta = json.loads((run_root / "prepared/api-contract-carddemo/metadata.json").read_text())
            self.assertEqual(meta["stage"], 6)
            self.assertFalse(meta["execute_authorized"])
            self.assertIn("input_pins_sha256", meta)

    def test_stale_unapproved_or_tampered_stage5_blocks_init_prepare_execute_and_stage7_refused(self):
        self.assertIsNotNone(stage6_main)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage4(run_root, tmp)
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-init", "api-contract-carddemo", "--stage", "6"])), 2)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-init", "api-contract-carddemo", "--stage", "6"])), 0)
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo", "--stage", "6", "--prepare-only"])), 0)
            meta = json.loads((run_root / "prepared/api-contract-carddemo/metadata.json").read_text())
            auth = tmp / "stage6-exec-auth.json"
            write_json(auth, {"approved": True, "stage": 6, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": meta["request_sha256"]})
            (run_root / "STAGE5-COUNTEREXAMPLE-REVIEW.md").write_text("tampered\n", encoding="utf-8")
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-init", "another-contract", "--stage", "6"])), 2)
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo", "--stage", "6", "--prepare-only"])), 2)
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo", "--stage", "6", "--execute", "--authorization-file", str(auth)])), 2)
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-init", "api-contract-carddemo", "--stage", "7"])), 2)

    def test_stage6_execution_authorization_requires_stage_and_request_hash(self):
        self.assertIsNotNone(stage6_main)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-init", "api-contract-carddemo", "--stage", "6"])), 0)
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo", "--stage", "6", "--prepare-only"])), 0)
            meta = json.loads((run_root / "prepared/api-contract-carddemo/metadata.json").read_text())
            wrong_stage = tmp / "wrong-stage.json"
            write_json(wrong_stage, {"approved": True, "stage": 5, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": meta["request_sha256"]})
            wrong_hash = tmp / "wrong-hash.json"
            write_json(wrong_hash, {"approved": True, "stage": 6, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": "0" * 64})
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo", "--stage", "6", "--execute", "--authorization-file", str(wrong_stage)])), 2)
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo", "--stage", "6", "--execute", "--authorization-file", str(wrong_hash)])), 2)


    def test_stage5_authorization_reject_wins_and_identity_artifact_references_are_enforced(self):
        self.assertIsNotNone(stage6_main)
        cases = [
            (lambda auth, run_root: auth.update({"decision": "reject", "approved": True}), "reject wins"),
            (lambda auth, run_root: auth.update({"stage": 4}), "stage identity"),
            (lambda auth, run_root: auth.update({"run_id": "WRONG"}), "run identity"),
            (lambda auth, run_root: auth.pop("artifact", None), "artifact required"),
            (lambda auth, run_root: auth["artifact"].update({"path": "specs/other/requirements.md"}), "artifact path"),
            (lambda auth, run_root: auth["review_reference"].update({"sha256": "0" * 64}), "review reference"),
            (lambda auth, run_root: auth["findings_reference"].update({"path": "reviews/stage5-counterexample-findings.json"}), "findings reference"),
        ]
        for mutate, label in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as d:
                tmp = Path(d); run_root = tmp / "run"
                self.init_and_approve_stage5(run_root, tmp)
                auth_path = run_root / "reviews/stage-5-authorization.json"
                auth = json.loads(auth_path.read_text(encoding="utf-8"))
                mutate(auth, run_root)
                write_json(auth_path, auth)
                spec_path = run_root / "specs/canonical-data-boundary-carddemo/spec.json"
                spec = json.loads(spec_path.read_text(encoding="utf-8"))
                spec["gate"]["review"]["authorization"]["sha256"] = sha256_file(auth_path)
                write_json(spec_path, spec)
                self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-init", "api-contract-carddemo", "--stage", "6"])), 2)

    def test_stage6_prompt_allows_traceable_representation_decisions_without_business_guarantees(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-init", "api-contract-carddemo", "--stage", "6"])), 0)
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo", "--stage", "6", "--prepare-only"])), 0)
            prepared = json.loads((run_root / "prepared/api-contract-carddemo/request.json").read_text(encoding="utf-8"))
            prompt = json.loads(prepared["input"][0]["content"])
            text = json.dumps(prompt, ensure_ascii=False)
            self.assertIn("D-n representation choices", text)
            for token in ["method", "route", "schema", "status"]:
                self.assertIn(token, text)
            self.assertIn("must not create new business guarantees", text)
            self.assertNotIn("blocking gaps for any concrete method, route, schema, validation, status, error or state/recovery decision unsupported by Stage5", text)

    def test_production_stage6_refuses_reduced_corpus_without_mutating_original_pins(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            before = (run_root / "specs/canonical-data-boundary-carddemo/input-pins.json").read_bytes()
            self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-init", "api-contract-carddemo", "--stage", "6"])), 2)
            self.assertEqual((run_root / "specs/canonical-data-boundary-carddemo/input-pins.json").read_bytes(), before)
            self.assertFalse((run_root / "specs/api-contract-carddemo").exists())

    def test_payload_preserves_exact_source_content_numbered_hashes_and_framework_doc_set(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-init", "api-contract-carddemo", "--stage", "6"])), 0)
            self.assertEqual(self.stage6_fixture_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo", "--stage", "6", "--prepare-only"])), 0)
            prepared = json.loads((run_root / "prepared/api-contract-carddemo/request.json").read_text(encoding="utf-8"))
            prompt = json.loads(prepared["input"][0]["content"])
            for body in prompt["source_bodies"]:
                source = (CORPUS / body["path"]).read_text(encoding="utf-8")
                numbered = "\n".join(f"{i}: {line}" for i, line in enumerate(source.splitlines(), 1))
                self.assertEqual(body["content"], source)
                self.assertEqual(body["numbered_lines"], numbered)
                self.assertEqual(body["sha256"], sha256_file(CORPUS / body["path"]))
                self.assertEqual(body["derived_representation_sha256"], hashlib.sha256(numbered.encode("utf-8")).hexdigest())
            expected_framework = [
                "steering/pipeline.md", "steering/product.md", "steering/tech.md", "steering/structure.md", "steering/glossary.md",
                "settings/rules/run-integrity.md", "settings/rules/ai-assistance.md", "settings/rules/traceability.md",
                "settings/rules/ambiguity-management.md", "settings/rules/legacy-code-policy.md", "settings/rules/validation-principles.md",
                "settings/rules/ears-format.md", "settings/templates/pipeline/api-contract-spec.md",
            ]
            self.assertEqual([doc["path"] for doc in prompt["framework_context"]], expected_framework)
            for doc in prompt["framework_context"]:
                self.assertEqual(doc["content"], (FRAMEWORK / doc["path"]).read_text(encoding="utf-8"))

    def add_unapproved_stage6_original_and_revision_inputs(self, run_root: Path, expected_sha=None):
        original_dir = run_root / "specs/api-contract-carddemo"
        original_dir.mkdir(parents=True, exist_ok=True)
        original_artifact = original_dir / "requirements.md"
        original_artifact.write_text(
            "# Failed original Stage 6 API Contract\n\n"
            "G-21 G-22 G-23 G-24 remain open. posting interest reporting.\n"
            "Do not treat this artifact as approved.\n",
            encoding="utf-8",
        )
        original_spec = original_dir / "spec.json"
        write_json(original_spec, {
            "feature_name": "api-contract-carddemo",
            "pipeline_stage": 6,
            "artifact_type": "api-contract",
            "capability": "unselected-stage-1-scope-only",
            "mandatory_tracks": ["posting", "interest", "reporting"],
            "upstream_specs": ["specs/canonical-data-boundary-carddemo/spec.json"],
            "approvals": {"requirements": {"generated": True, "approved": False}},
            "gate": {"completeness_gate_passed": False, "blocking_gaps": ["G-21", "G-22", "G-23", "G-24"]},
        })
        prepared_exec = run_root / "prepared/api-contract-carddemo/execution"
        prepared_exec.mkdir(parents=True, exist_ok=True)
        (prepared_exec / "scope-original.md").write_text(original_artifact.read_text(encoding="utf-8"), encoding="utf-8")
        feedback = run_root / "reviews/stage-6-r1-directed-feedback.md"
        feedback.write_text("# Feedback dirigido Stage 6 r1\n\nG-21 G-22 G-23 G-24: revise as versioned proposal, preserve unknown vs false and three tracks.\n", encoding="utf-8")
        plan = run_root / "STAGE6-REVISION-PLAN.md"
        plan.write_text("# Plano de Revisão Stage 6\n\nRevision bridge only; no Stage 7/API implementation; human gate remains external.\n", encoding="utf-8")
        if expected_sha is None:
            expected_sha = sha256_file(original_artifact)
        return original_artifact, feedback, plan

    def add_unapproved_stage6_r2_and_r3_inputs(self, run_root: Path):
        r2_dir = run_root / "specs/api-contract-carddemo-r2"
        r2_dir.mkdir(parents=True, exist_ok=True)
        r2_artifact = r2_dir / "requirements.md"
        r2_artifact.write_text(
            "# Stage 6 r2 API Contract\n\n"
            "External-input design remains: empty closed operation requests; posting interest reporting.\n"
            "Preserve ordering/multiplicity, reason 109 internal, unknown not false.\n"
            "r2 contradiction: available items: [] is allowed, but InterestEnvelope/ReportingEnvelope minItems: 1 and 503 content_unavailable conflict.\n",
            encoding="utf-8",
        )
        write_json(r2_dir / "spec.json", {
            "feature_name": "api-contract-carddemo-r2",
            "pipeline_stage": 6,
            "artifact_type": "api-contract",
            "capability": "unselected-stage-1-scope-only",
            "run_id": "E3-01",
            "mandatory_tracks": ["posting", "interest", "reporting"],
            "upstream_specs": ["specs/canonical-data-boundary-carddemo/spec.json"],
            "approvals": {"requirements": {"generated": True, "approved": False}},
            "gate": {"completeness_gate_passed": False, "blocking_gaps": []},
            "ready_for_implementation": False,
            "revision_of": "api-contract-carddemo",
        })
        prepared = run_root / "prepared/api-contract-carddemo-r2"
        execution = prepared / "execution"
        execution.mkdir(parents=True, exist_ok=True)
        request = {"model": "gpt-6-astra", "store": False, "stream": True, "input": [{"role": "user", "content": "r2 request"}]}
        write_json(prepared / "request.json", request)
        write_json(execution / "request-body.json", request)
        request_sha = hashlib.sha256(json.dumps(request, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        metadata = {"stage": 6, "run_id": "E3-01", "feature": "api-contract-carddemo-r2", "request_sha256": request_sha, "execute_authorized": False}
        write_json(prepared / "metadata.json", metadata)
        execution_metadata = dict(metadata)
        execution_metadata.update({"execute_authorized": True, "authorization_file": str(run_root / "stage6-r2-generation-authorization.json")})
        write_json(execution / "metadata.json", execution_metadata)
        (execution / "scope-original.md").write_text(r2_artifact.read_text(encoding="utf-8"), encoding="utf-8")
        write_json(run_root / "stage6-r2-generation-authorization.json", {
            "approved": True, "stage": 6, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex",
            "request_sha256": request_sha, "scope": "One versioned Stage6 revision with directed feedback; preserve original and all three tracks. No Stage7, implementation, automatic retry or paid fallback.",
            "reference": "reviews/stage-6-r1-directed-feedback.md",
        })
        review = run_root / "STAGE6-R2-INPUTS-EMPTY-REVIEW.md"
        review.write_text(
            "# Stage6 r2 Focused Review — External Inputs and Legitimately Empty Outputs\n\n"
            "r3 required before Stage 6 human acceptance. available with items: [] must be an observed empty represented sequence; unavailable is no represented observation; all-unavailable/no-observation must not be 200; zero-count progress is not output fulfillment.\n",
            encoding="utf-8",
        )
        feedback = run_root / "reviews/stage-6-r2-directed-feedback.md"
        feedback.write_text(
            "# Stage 6 r2 Directed Feedback — External Inputs and Empty Outputs\n\n"
            "r3 required before Stage 6 acceptance. Remove or narrow blanket minItems: 1 for InterestEnvelope and ReportingEnvelope; do not force observed empty sequences into 503; keep external-input design; no E1/E2 comparison; no Stage7.\n",
            encoding="utf-8",
        )
        return {
            "r2_spec": r2_dir / "spec.json",
            "r2_artifact": r2_artifact,
            "r2_output": execution / "scope-original.md",
            "r2_request": prepared / "request.json",
            "r2_metadata": prepared / "metadata.json",
            "r2_execution_request": execution / "request-body.json",
            "r2_execution_metadata": execution / "metadata.json",
            "r2_auth": run_root / "stage6-r2-generation-authorization.json",
            "review": review,
            "feedback": feedback,
        }

    def r3_hash_patches(self, paths):
        return mock.patch.multiple(
            stage6_adapter,
            EXPECTED_R2_STAGE6_SPEC_SHA256=sha256_file(paths["r2_spec"]),
            EXPECTED_R2_STAGE6_ARTIFACT_SHA256=sha256_file(paths["r2_artifact"]),
            EXPECTED_R2_STAGE6_REQUEST_SHA256=sha256_file(paths["r2_request"]),
            EXPECTED_R2_STAGE6_METADATA_SHA256=sha256_file(paths["r2_metadata"]),
            EXPECTED_R2_STAGE6_AUTHORIZATION_SHA256=sha256_file(paths["r2_auth"]),
            EXPECTED_R2_EMPTY_REVIEW_SHA256=sha256_file(paths["review"]),
            EXPECTED_R2_DIRECTED_FEEDBACK_SHA256=sha256_file(paths["feedback"]),
        )

    def test_stage6_r2_init_prepare_carries_failed_original_feedback_plan_and_revision_constraints(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            original_artifact, feedback, plan = self.add_unapproved_stage6_original_and_revision_inputs(run_root)
            expected_sha = sha256_file(original_artifact)
            expected_feedback_sha = sha256_file(feedback)
            expected_plan_sha = sha256_file(plan)
            with mock.patch.object(stage6_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])), \
                 mock.patch.object(stage6_adapter, "EXPECTED_ORIGINAL_STAGE6_ARTIFACT_SHA256", expected_sha), \
                 mock.patch.object(stage6_adapter, "EXPECTED_STAGE6_DIRECTED_FEEDBACK_SHA256", expected_feedback_sha), \
                 mock.patch.object(stage6_adapter, "EXPECTED_STAGE6_REVISION_PLAN_SHA256", expected_plan_sha):
                self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-init", "api-contract-carddemo-r2", "--stage", "6"])), 0)
                self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo-r2", "--stage", "6", "--prepare-only"])), 0)
            spec = json.loads((run_root / "specs/api-contract-carddemo-r2/spec.json").read_text(encoding="utf-8"))
            self.assertEqual(spec["feature_name"], "api-contract-carddemo-r2")
            self.assertEqual(spec["revision_of"], "api-contract-carddemo")
            self.assertFalse(spec["approvals"]["requirements"]["approved"])
            prepared = json.loads((run_root / "prepared/api-contract-carddemo-r2/request.json").read_text(encoding="utf-8"))
            prompt = json.loads(prepared["input"][0]["content"])
            self.assertEqual(prompt["failed_original_stage6"]["requirements_md"], original_artifact.read_text(encoding="utf-8"))
            self.assertEqual(prompt["revision_feedback"]["directed_feedback_md"], feedback.read_text(encoding="utf-8"))
            self.assertEqual(prompt["revision_feedback"]["revision_plan_md"], plan.read_text(encoding="utf-8"))
            text = json.dumps(prompt, ensure_ascii=False)
            for token in [
                "revision, not an independent replica", "Never approve the original Stage 6 artifact",
                "concrete proposed request/schema/status/envelope choices tied to D-n",
                "do not invent business rules", "unknown vs false", "not_attested is not confirmed incomplete",
                "batch granularity", "output order/multiplicity", "preliminary posting rejections 100..103",
                "reason 109", "optional observable outputs", "not guaranteed telemetry", "all-empty responses",
                "vacuously satisfy capability", "observable obligations must retain representation", "unknowns scoped",
                "posting", "interest", "reporting", "human gate remains external", "No Stage7", "No API implementation",
            ]:
                self.assertIn(token, text)
            pins = prompt["input_pins"]
            self.assertIn({"path": "specs/api-contract-carddemo/requirements.md", "sha256": expected_sha}, pins["failed_original_stage6"])
            self.assertIn("stage6_revision_feedback", pins)
            self.assertEqual([p["path"] for p in pins["upstream_specs"]][-1], "specs/canonical-data-boundary-carddemo/spec.json")
            self.assertEqual(pins["actual_corpus_file_count"], len(json.loads(PACKAGE.read_text())["files"]))

    def test_stage6_r2_blocks_tampered_original_feedback_plan_and_approved_original(self):
        cases = ["original", "feedback", "plan", "approved_original"]
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as d:
                tmp = Path(d); run_root = tmp / "run"
                self.init_and_approve_stage5(run_root, tmp)
                original_artifact, feedback, plan = self.add_unapproved_stage6_original_and_revision_inputs(run_root)
                expected_sha = sha256_file(original_artifact)
                expected_feedback_sha = sha256_file(feedback)
                expected_plan_sha = sha256_file(plan)
                if case == "original":
                    original_artifact.write_text("tampered\n", encoding="utf-8")
                elif case == "feedback":
                    feedback.write_text("tampered\n", encoding="utf-8")
                elif case == "plan":
                    plan.write_text("tampered\n", encoding="utf-8")
                else:
                    spec_path = run_root / "specs/api-contract-carddemo/spec.json"
                    spec = json.loads(spec_path.read_text(encoding="utf-8"))
                    spec["approvals"]["requirements"]["approved"] = True
                    spec["gate"]["completeness_gate_passed"] = True
                    write_json(spec_path, spec)
                with mock.patch.object(stage6_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])), \
                     mock.patch.object(stage6_adapter, "EXPECTED_ORIGINAL_STAGE6_ARTIFACT_SHA256", expected_sha), \
                     mock.patch.object(stage6_adapter, "EXPECTED_STAGE6_DIRECTED_FEEDBACK_SHA256", expected_feedback_sha), \
                     mock.patch.object(stage6_adapter, "EXPECTED_STAGE6_REVISION_PLAN_SHA256", expected_plan_sha):
                    self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-init", "api-contract-carddemo-r2", "--stage", "6"])), 2)

    def test_stage6_r2_execute_rechecks_request_hash_auth_stage_stage5_and_revision_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            original_artifact, feedback, plan = self.add_unapproved_stage6_original_and_revision_inputs(run_root)
            expected_sha = sha256_file(original_artifact)
            expected_feedback_sha = sha256_file(feedback)
            expected_plan_sha = sha256_file(plan)
            with mock.patch.object(stage6_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])), \
                 mock.patch.object(stage6_adapter, "EXPECTED_ORIGINAL_STAGE6_ARTIFACT_SHA256", expected_sha), \
                 mock.patch.object(stage6_adapter, "EXPECTED_STAGE6_DIRECTED_FEEDBACK_SHA256", expected_feedback_sha), \
                 mock.patch.object(stage6_adapter, "EXPECTED_STAGE6_REVISION_PLAN_SHA256", expected_plan_sha):
                self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-init", "api-contract-carddemo-r2", "--stage", "6"])), 0)
                self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo-r2", "--stage", "6", "--prepare-only"])), 0)
            meta = json.loads((run_root / "prepared/api-contract-carddemo-r2/metadata.json").read_text(encoding="utf-8"))
            bad_hash_auth = tmp / "bad-hash-auth.json"
            write_json(bad_hash_auth, {"approved": True, "stage": 6, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": "0" * 64})
            bad_stage_auth = tmp / "bad-stage-auth.json"
            write_json(bad_stage_auth, {"approved": True, "stage": 7, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": meta["request_sha256"]})
            with mock.patch.object(stage6_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])), \
                 mock.patch.object(stage6_adapter, "EXPECTED_ORIGINAL_STAGE6_ARTIFACT_SHA256", expected_sha), \
                 mock.patch.object(stage6_adapter, "EXPECTED_STAGE6_DIRECTED_FEEDBACK_SHA256", expected_feedback_sha), \
                 mock.patch.object(stage6_adapter, "EXPECTED_STAGE6_REVISION_PLAN_SHA256", expected_plan_sha):
                self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo-r2", "--stage", "6", "--execute", "--authorization-file", str(bad_hash_auth)])), 2)
                self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo-r2", "--stage", "6", "--execute", "--authorization-file", str(bad_stage_auth)])), 2)
                original_artifact.write_text("stale before execute\n", encoding="utf-8")
                good_auth = tmp / "good-auth.json"
                write_json(good_auth, {"approved": True, "stage": 6, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": meta["request_sha256"]})
                self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo-r2", "--stage", "6", "--execute", "--authorization-file", str(good_auth)])), 2)

    def test_stage6_r3_init_prepare_carries_exact_r2_provenance_review_feedback_and_narrow_empty_output_revision(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            paths = self.add_unapproved_stage6_r2_and_r3_inputs(run_root)
            with self.r3_hash_patches(paths), mock.patch.object(stage6_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])):
                self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-init", "api-contract-carddemo-r3", "--stage", "6"])), 0)
                self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo-r3", "--stage", "6", "--prepare-only"])), 0)
            spec = json.loads((run_root / "specs/api-contract-carddemo-r3/spec.json").read_text(encoding="utf-8"))
            self.assertEqual(spec["feature_name"], "api-contract-carddemo-r3")
            self.assertEqual(spec["revision_of"], "api-contract-carddemo-r2")
            self.assertFalse(spec["approvals"]["requirements"]["approved"])
            self.assertFalse(spec["ready_for_implementation"])
            prepared = json.loads((run_root / "prepared/api-contract-carddemo-r3/request.json").read_text(encoding="utf-8"))
            prompt = json.loads(prepared["input"][0]["content"])
            self.assertEqual(prompt["failed_original_stage6"]["requirements_md"], paths["r2_artifact"].read_text(encoding="utf-8"))
            self.assertEqual(prompt["revision_feedback"]["r2_empty_review_md"], paths["review"].read_text(encoding="utf-8"))
            self.assertEqual(prompt["revision_feedback"]["r2_directed_feedback_md"], paths["feedback"].read_text(encoding="utf-8"))
            pins = prompt["input_pins"]
            self.assertEqual(pins["revision_of"], "api-contract-carddemo-r2")
            self.assertEqual([p["path"] for p in pins["failed_original_stage6_r2"]], [
                "specs/api-contract-carddemo-r2/spec.json",
                "specs/api-contract-carddemo-r2/requirements.md",
                "prepared/api-contract-carddemo-r2/execution/scope-original.md",
                "prepared/api-contract-carddemo-r2/request.json",
                "prepared/api-contract-carddemo-r2/metadata.json",
                "stage6-r2-generation-authorization.json",
            ])
            self.assertEqual([p["path"] for p in pins["stage6_r3_revision_feedback"]], [
                "STAGE6-R2-INPUTS-EMPTY-REVIEW.md",
                "reviews/stage-6-r2-directed-feedback.md",
            ])
            text = json.dumps(prompt, ensure_ascii=False)
            for token in [
                "narrow revision only", "keep external-input design", "available with items: []",
                "observed empty represented sequence", "all-unavailable/no-observation envelope: not 200",
                "503 content_unavailable", "known technical failure: 500", "Remove or narrow blanket minItems: 1",
                "zero-rate bypass", "zero amount", "missing disclosure", "progress-only 200",
                "zero counts", "must not prove no effects", "no complete empty report", "zero-count progress is not output fulfillment",
                "preserve ordering/multiplicity", "reason 109 internal", "unknown not false", "No E1/E2", "No Stage7",
                "does not require substantive nonempty content for observed empty sequences",
            ]:
                self.assertIn(token, text)
            self.assertNotIn("must require substantive nonempty content for observed empty sequences", text)

    def test_stage6_r3_blocks_tampered_r2_inputs_review_feedback_and_approved_r2(self):
        cases = ["r2_spec", "r2_artifact", "r2_output", "r2_request", "r2_metadata", "r2_auth", "review", "feedback", "approved_r2"]
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as d:
                tmp = Path(d); run_root = tmp / "run"
                self.init_and_approve_stage5(run_root, tmp)
                paths = self.add_unapproved_stage6_r2_and_r3_inputs(run_root)
                ctx = self.r3_hash_patches(paths)
                if case == "approved_r2":
                    spec = json.loads(paths["r2_spec"].read_text(encoding="utf-8"))
                    spec["approvals"]["requirements"]["approved"] = True
                    spec["gate"]["completeness_gate_passed"] = True
                    write_json(paths["r2_spec"], spec)
                else:
                    paths[case].write_text("tampered\n", encoding="utf-8")
                with ctx, mock.patch.object(stage6_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])):
                    self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-init", "api-contract-carddemo-r3", "--stage", "6"])), 2)

    def test_stage6_r3_execute_rechecks_auth_request_hash_stage5_and_r2_revision_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage5(run_root, tmp)
            paths = self.add_unapproved_stage6_r2_and_r3_inputs(run_root)
            with self.r3_hash_patches(paths), mock.patch.object(stage6_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])):
                self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-init", "api-contract-carddemo-r3", "--stage", "6"])), 0)
                self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo-r3", "--stage", "6", "--prepare-only"])), 0)
            meta = json.loads((run_root / "prepared/api-contract-carddemo-r3/metadata.json").read_text(encoding="utf-8"))
            bad_hash_auth = tmp / "bad-r3-hash-auth.json"
            write_json(bad_hash_auth, {"approved": True, "stage": 6, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": "0" * 64})
            bad_stage_auth = tmp / "bad-r3-stage-auth.json"
            write_json(bad_stage_auth, {"approved": True, "stage": 7, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": meta["request_sha256"]})
            good_auth = tmp / "good-r3-auth.json"
            write_json(good_auth, {"approved": True, "stage": 6, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": meta["request_sha256"]})
            with self.r3_hash_patches(paths), mock.patch.object(stage6_adapter, "EXPECTED_REAL_CORPUS_FILE_COUNT", len(json.loads(PACKAGE.read_text())["files"])):
                self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo-r3", "--stage", "6", "--execute", "--authorization-file", str(bad_hash_auth)])), 2)
                self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo-r3", "--stage", "6", "--execute", "--authorization-file", str(bad_stage_auth)])), 2)
                paths["feedback"].write_text("stale before execute\n", encoding="utf-8")
                self.assertEqual(stage6_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "api-contract-carddemo-r3", "--stage", "6", "--execute", "--authorization-file", str(good_auth)])), 2)


if __name__ == "__main__":
    import unittest
    unittest.main()

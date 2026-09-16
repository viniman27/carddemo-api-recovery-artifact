import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stage4_adapter import main as stage4_main
from stage5_adapter import main as stage5_main
from test_stage4_adapter import Stage4AdapterTests, sha256_file, write_json, FRAMEWORK, CORPUS, PACKAGE


class Stage5AdapterTests(Stage4AdapterTests):
    def init_and_approve_stage4(self, run_root: Path, tmp_path: Path) -> None:
        self.approved_chain(run_root, tmp_path)
        self.assertEqual(stage4_main(self.args(run_root, tmp_path, ["/sdd:spec-init", "capability-semantics-carddemo", "--stage", "4"])), 0)
        spec_path = run_root / "specs/capability-semantics-carddemo/spec.json"
        artifact = run_root / "specs/capability-semantics-carddemo/requirements.md"
        rules = "\n".join(f"R-{i}: Synthetic semantic rule {i}." for i in range(1, 21))
        artifact.write_text(
            "# Synthetic approved stage-4 capability semantics\n\n"
            "Capability identity: unselected-stage-1-scope-only\n\n"
            "## Posting Track\nR-1 posting.\n## Interest Track\nR-2 interest.\n## Reporting Track\nR-3 reporting.\n\n"
            "## Semantic Rules\n" + rules + "\n\n"
            "## Unresolved Runtime and Configuration Limits\nMissing runtime/config limits remain unresolved.\n",
            encoding="utf-8",
        )
        review_attachment = run_root / "reviews/STAGE4-COUNTEREXAMPLE-REVIEW.md"
        review_attachment.parent.mkdir(parents=True, exist_ok=True)
        review_attachment.write_text("# Stage 4 Source-Grounded Counterexample Review\n\nAll categories reviewed from sources.\n", encoding="utf-8")
        auth = run_root / "reviews/stage-4-authorization.json"
        write_json(auth, {
            "synthetic_test_fixture": True, "approved": True, "stage": 4, "run_id": "E3-01", "decision": "approve",
            "conditional_scope": "Stage 5 may prepare only canonical data boundary; no API/transport execution decisions.",
            "attachments": [{"path": "reviews/STAGE4-COUNTEREXAMPLE-REVIEW.md", "sha256": sha256_file(review_attachment)}],
        })
        spec = json.loads(spec_path.read_text())
        spec["approvals"]["requirements"]["generated"] = True
        spec["approvals"]["requirements"]["approved"] = True
        spec["gate"] = {"completeness_gate_passed": True, "gate_review_date": "2026-09-12", "blocking_gaps": [],
            "review": {"synthetic_test_fixture": True, "reviewer": "unit-test", "decision": "approve",
                "context": {"run_id": spec["run_id"], "capability": spec["capability"], "pipeline_stage": 4, "artifact_type": "capability-semantics"},
                "artifact": {"path": "specs/capability-semantics-carddemo/requirements.md", "sha256": sha256_file(artifact)},
                "authorization": {"path": "reviews/stage-4-authorization.json", "sha256": sha256_file(auth)},
                "attachments": [{"path": "reviews/STAGE4-COUNTEREXAMPLE-REVIEW.md", "sha256": sha256_file(review_attachment)}],
                "upstream_specs": [{"path": "specs/legacy-evidence-carddemo-r2/spec.json", "sha256": sha256_file(run_root / "specs/legacy-evidence-carddemo-r2/spec.json")}]}}
        write_json(spec_path, spec)

    def test_init_prepare_payload_preserves_chain_identity_exact_inputs_and_stage5_boundaries(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage4(run_root, tmp)
            self.assertEqual(stage5_main(self.args(run_root, tmp, ["/sdd:spec-init", "canonical-data-boundary-carddemo", "--stage", "5"])), 0)
            self.assertEqual(stage5_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "canonical-data-boundary-carddemo", "--stage", "5", "--prepare-only"])), 0)
            spec = json.loads((run_root / "specs/canonical-data-boundary-carddemo/spec.json").read_text())
            parent = json.loads((run_root / "specs/capability-semantics-carddemo/spec.json").read_text())
            self.assertEqual(spec["capability"], parent["capability"])
            self.assertEqual(spec["pipeline_stage"], 5)
            self.assertEqual(spec["artifact_type"], "canonical-data-boundary")
            self.assertEqual(spec["upstream_specs"], ["specs/capability-semantics-carddemo/spec.json"])
            prepared = json.loads((run_root / "prepared/canonical-data-boundary-carddemo/request.json").read_text())
            payload_text = json.dumps(prepared, ensure_ascii=False)
            for token in [
                "posting", "interest", "reporting", "Canonical Data Boundary Specification",
                "conceptual data boundary", "source-to-canonical mapping/provenance", "explicit unresolved gaps",
                "trace each boundary decision to stage4 R-n", "R-1..R-20", "unselected-stage-1-scope-only",
                "STAGE4-COUNTEREXAMPLE-REVIEW.md",
            ]:
                self.assertIn(token, payload_text)
            for forbidden in ["No endpoint names", "HTTP methods", "OpenAPI", "stage6 decisions", "No model/network calls during prepare-only"]:
                self.assertIn(forbidden, payload_text)
            prompt = json.loads(prepared["input"][0]["content"])
            self.assertEqual(prompt["approved_upstream"]["stage4_requirements_md"], (run_root / "specs/capability-semantics-carddemo/requirements.md").read_text())
            self.assertEqual(prompt["approved_upstream"]["stage4_counterexample_review_md"], (run_root / "reviews/STAGE4-COUNTEREXAMPLE-REVIEW.md").read_text())
            self.assertEqual(len(prompt["source_bodies"]), len(json.loads(PACKAGE.read_text())["files"]))
            framework_by_path = {doc["path"]: doc["content"] for doc in prompt["framework_context"]}
            self.assertEqual(framework_by_path["settings/templates/pipeline/canonical-data-boundary-spec.md"], (FRAMEWORK / "settings/templates/pipeline/canonical-data-boundary-spec.md").read_text())
            pins = prompt["input_pins"]
            self.assertEqual([p["path"] for p in pins["upstream_specs"]], [
                "specs/pipeline-scope-carddemo/spec.json", "specs/capability-selection-carddemo-r2/spec.json",
                "specs/legacy-evidence-carddemo-r2/spec.json", "specs/capability-semantics-carddemo/spec.json"])
            self.assertEqual(len(pins["authorizations"]), 4)
            self.assertEqual(pins["review_attachments"][0]["path"], "reviews/STAGE4-COUNTEREXAMPLE-REVIEW.md")
            meta = json.loads((run_root / "prepared/canonical-data-boundary-carddemo/metadata.json").read_text())
            self.assertEqual(meta["stage"], 5)
            self.assertFalse(meta["execute_authorized"])
            self.assertIn("input_pins_sha256", meta)

    def test_stale_or_unapproved_stage4_blocks_init_prepare_execute_and_stage6_refused(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.approved_chain(run_root, tmp)
            self.assertEqual(stage5_main(self.args(run_root, tmp, ["/sdd:spec-init", "canonical-data-boundary-carddemo", "--stage", "5"])), 2)
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage4(run_root, tmp)
            self.assertEqual(stage5_main(self.args(run_root, tmp, ["/sdd:spec-init", "canonical-data-boundary-carddemo", "--stage", "5"])), 0)
            self.assertEqual(stage5_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "canonical-data-boundary-carddemo", "--stage", "5", "--prepare-only"])), 0)
            meta = json.loads((run_root / "prepared/canonical-data-boundary-carddemo/metadata.json").read_text())
            auth = tmp / "stage5-exec-auth.json"
            write_json(auth, {"approved": True, "stage": 5, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": meta["request_sha256"]})
            (run_root / "specs/capability-semantics-carddemo/requirements.md").write_text("changed after approval\n", encoding="utf-8")
            self.assertEqual(stage5_main(self.args(run_root, tmp, ["/sdd:spec-init", "another-boundary", "--stage", "5"])), 2)
            self.assertEqual(stage5_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "canonical-data-boundary-carddemo", "--stage", "5", "--prepare-only"])), 2)
            self.assertEqual(stage5_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "canonical-data-boundary-carddemo", "--stage", "5", "--execute", "--authorization-file", str(auth)])), 2)
            self.assertEqual(stage5_main(self.args(run_root, tmp, ["/sdd:spec-init", "canonical-data-boundary-carddemo", "--stage", "6"])), 2)

    def test_stage5_execution_authorization_requires_stage_and_request_hash(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_and_approve_stage4(run_root, tmp)
            self.assertEqual(stage5_main(self.args(run_root, tmp, ["/sdd:spec-init", "canonical-data-boundary-carddemo", "--stage", "5"])), 0)
            self.assertEqual(stage5_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "canonical-data-boundary-carddemo", "--stage", "5", "--prepare-only"])), 0)
            meta = json.loads((run_root / "prepared/canonical-data-boundary-carddemo/metadata.json").read_text())
            wrong_stage = tmp / "wrong-stage.json"
            write_json(wrong_stage, {"approved": True, "stage": 4, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": meta["request_sha256"]})
            wrong_hash = tmp / "wrong-hash.json"
            write_json(wrong_hash, {"approved": True, "stage": 5, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": "0" * 64})
            self.assertEqual(stage5_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "canonical-data-boundary-carddemo", "--stage", "5", "--execute", "--authorization-file", str(wrong_stage)])), 2)
            self.assertEqual(stage5_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "canonical-data-boundary-carddemo", "--stage", "5", "--execute", "--authorization-file", str(wrong_hash)])), 2)


if __name__ == "__main__":
    unittest.main()

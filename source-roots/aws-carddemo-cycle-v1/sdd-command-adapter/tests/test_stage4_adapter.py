import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from adapter import main as adapter_main
from stage3_adapter import main as stage3_main
from stage4_adapter import main as stage4_main

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
FRAMEWORK = FIXTURES / "framework"
CORPUS = FIXTURES / "corpus"
PACKAGE = FIXTURES / "research-package.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class Stage4AdapterTests(unittest.TestCase):
    def init_stage1(self, run_root: Path, tmp_path: Path) -> None:
        self.assertEqual(adapter_main([
            "/sdd:spec-init", "pipeline-scope-carddemo",
            "--run-root", str(run_root), "--allowed-run-parent", str(tmp_path),
            "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE),
            "--run-id", "E3-01", "--timestamp", "2026-09-11T12:00:00-03:00",
        ]), 0)
        spec_path = run_root / "specs/pipeline-scope-carddemo/spec.json"
        artifact = run_root / "specs/pipeline-scope-carddemo/requirements.md"
        artifact.write_text("# Synthetic approved stage-1 scope\n\nposting, interest, reporting\n", encoding="utf-8")
        auth = run_root / "reviews/stage-1-authorization.json"
        write_json(auth, {"synthetic_test_fixture": True, "approved": True, "stage": 1, "run_id": "E3-01"})
        spec = json.loads(spec_path.read_text())
        spec["approvals"]["requirements"]["generated"] = True
        spec["approvals"]["requirements"]["approved"] = True
        spec["gate"] = {"completeness_gate_passed": True, "gate_review_date": "2026-09-11", "blocking_gaps": [],
            "review": {"synthetic_test_fixture": True, "reviewer": "unit-test", "decision": "approve",
                "context": {"run_id": spec["run_id"], "capability": spec["capability"], "pipeline_stage": 1, "artifact_type": "pipeline-scope"},
                "artifact": {"path": "specs/pipeline-scope-carddemo/requirements.md", "sha256": sha256_file(artifact)},
                "authorization": {"path": "reviews/stage-1-authorization.json", "sha256": sha256_file(auth)},
                "upstream_specs": []}}
        write_json(spec_path, spec)

    def init_and_approve_stage2_r2(self, run_root: Path, tmp_path: Path) -> None:
        self.assertEqual(adapter_main([
            "/sdd:spec-init", "capability-selection-carddemo-r2", "--stage", "2",
            "--run-root", str(run_root), "--allowed-run-parent", str(tmp_path),
            "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE),
            "--run-id", "E3-01", "--timestamp", "2026-09-11T13:00:00-03:00",
        ]), 0)
        spec_path = run_root / "specs/capability-selection-carddemo-r2/spec.json"
        artifact = run_root / "specs/capability-selection-carddemo-r2/requirements.md"
        artifact.write_text("# Synthetic approved stage-2-r2 capability selection\n\nMandatory tracks: posting, interest, reporting.\n", encoding="utf-8")
        auth = run_root / "reviews/stage-2-r2-authorization.json"
        write_json(auth, {"synthetic_test_fixture": True, "approved": True, "stage": 2, "run_id": "E3-01", "decision": "approve"})
        spec = json.loads(spec_path.read_text())
        spec["approvals"]["requirements"]["generated"] = True
        spec["approvals"]["requirements"]["approved"] = True
        spec["gate"] = {"completeness_gate_passed": True, "gate_review_date": "2026-09-11", "blocking_gaps": [],
            "review": {"synthetic_test_fixture": True, "reviewer": "unit-test", "decision": "approve",
                "context": {"run_id": spec["run_id"], "capability": spec["capability"], "pipeline_stage": 2, "artifact_type": "capability-selection"},
                "artifact": {"path": "specs/capability-selection-carddemo-r2/requirements.md", "sha256": sha256_file(artifact)},
                "authorization": {"path": "reviews/stage-2-r2-authorization.json", "sha256": sha256_file(auth)},
                "upstream_specs": [{"path": "specs/pipeline-scope-carddemo/spec.json", "sha256": sha256_file(run_root / "specs/pipeline-scope-carddemo/spec.json")}]}}
        write_json(spec_path, spec)

    def init_and_approve_stage3_r2(self, run_root: Path, tmp_path: Path) -> None:
        self.assertEqual(stage3_main(self.args(run_root, tmp_path, ["/sdd:spec-init", "legacy-evidence-carddemo", "--stage", "3"])), 0)
        spec_dir = run_root / "specs/legacy-evidence-carddemo"
        r2_dir = run_root / "specs/legacy-evidence-carddemo-r2"
        r2_dir.mkdir(parents=True)
        for name in ["spec.json", "requirements.md", "input-pins.json"]:
            (r2_dir / name).write_text((spec_dir / name).read_text(encoding="utf-8"), encoding="utf-8")
        spec_path = r2_dir / "spec.json"
        artifact = r2_dir / "requirements.md"
        artifact.write_text("# Synthetic approved stage-3-r2 legacy evidence\n\nE-1 posting evidence.\nE-2 interest evidence.\nE-3 reporting evidence.\n", encoding="utf-8")
        auth = run_root / "reviews/stage-3-r2-authorization.json"
        write_json(auth, {"synthetic_test_fixture": True, "approved": True, "stage": 3, "run_id": "E3-01", "decision": "approve", "stage4_visibility": True})
        spec = json.loads(spec_path.read_text())
        spec["feature_name"] = "legacy-evidence-carddemo-r2"
        spec["artifact_path"] = "specs/legacy-evidence-carddemo-r2/requirements.md"
        spec["approvals"]["requirements"]["generated"] = True
        spec["approvals"]["requirements"]["approved"] = True
        spec["gate"] = {"completeness_gate_passed": True, "gate_review_date": "2026-09-12", "blocking_gaps": [],
            "review": {"synthetic_test_fixture": True, "reviewer": "unit-test", "decision": "approve",
                "context": {"run_id": spec["run_id"], "capability": spec["capability"], "pipeline_stage": 3, "artifact_type": "legacy-evidence"},
                "artifact": {"path": "specs/legacy-evidence-carddemo-r2/requirements.md", "sha256": sha256_file(artifact)},
                "authorization": {"path": "reviews/stage-3-r2-authorization.json", "sha256": sha256_file(auth)},
                "upstream_specs": [{"path": "specs/capability-selection-carddemo-r2/spec.json", "sha256": sha256_file(run_root / "specs/capability-selection-carddemo-r2/spec.json")}]}}
        write_json(spec_path, spec)

    def args(self, run_root: Path, tmp_path: Path, extra):
        return extra + [
            "--run-root", str(run_root), "--allowed-run-parent", str(tmp_path),
            "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE),
            "--run-id", "E3-01", "--timestamp", "2026-09-12T12:00:00-03:00",
        ]

    def approved_chain(self, run_root: Path, tmp_path: Path) -> None:
        self.init_stage1(run_root, tmp_path)
        self.init_and_approve_stage2_r2(run_root, tmp_path)
        self.init_and_approve_stage3_r2(run_root, tmp_path)

    def test_init_prepare_payload_preserves_chain_identity_exact_inputs_and_stage4_boundaries(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.approved_chain(run_root, tmp)
            self.assertEqual(stage4_main(self.args(run_root, tmp, ["/sdd:spec-init", "capability-semantics-carddemo", "--stage", "4"])), 0)
            self.assertEqual(stage4_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "capability-semantics-carddemo", "--stage", "4", "--prepare-only"])), 0)
            spec = json.loads((run_root / "specs/capability-semantics-carddemo/spec.json").read_text())
            parent = json.loads((run_root / "specs/legacy-evidence-carddemo-r2/spec.json").read_text())
            self.assertEqual(spec["capability"], parent["capability"])
            self.assertEqual(spec["pipeline_stage"], 4)
            self.assertEqual(spec["artifact_type"], "capability-semantics")
            self.assertEqual(spec["upstream_specs"], ["specs/legacy-evidence-carddemo-r2/spec.json"])
            prepared = json.loads((run_root / "prepared/capability-semantics-carddemo/request.json").read_text())
            payload_text = json.dumps(prepared, ensure_ascii=False)
            for token in ["posting", "interest", "reporting", "Capability Semantics Specification", "semantic rule IDs", "trace to stage3 E-n", "reverse completeness mapping", "unselected-stage-1-scope-only"]:
                self.assertIn(token, payload_text)
            for forbidden in ["canonical data boundary", "API contract", "stage5", "COBOL execution", "quarantine", "preparation outputs"]:
                self.assertIn(forbidden, payload_text)
            prompt = json.loads(prepared["input"][0]["content"])
            self.assertEqual(prompt["approved_upstream"]["stage3_r2_requirements_md"], (run_root / "specs/legacy-evidence-carddemo-r2/requirements.md").read_text())
            self.assertEqual(prompt["approved_upstream"]["stage3_r2_authorization"]["stage4_visibility"], True)
            self.assertEqual(len(prompt["source_bodies"]), len(json.loads(PACKAGE.read_text())["files"]))
            for body in prompt["source_bodies"]:
                self.assertIn("numbered_lines", body)
                self.assertIn("derived_representation_sha256", body)
            framework_by_path = {doc["path"]: doc["content"] for doc in prompt["framework_context"]}
            self.assertEqual(framework_by_path["settings/templates/pipeline/capability-semantics-spec.md"], (FRAMEWORK / "settings/templates/pipeline/capability-semantics-spec.md").read_text())
            pins = prompt["input_pins"]
            self.assertEqual([p["path"] for p in pins["upstream_specs"]], ["specs/pipeline-scope-carddemo/spec.json", "specs/capability-selection-carddemo-r2/spec.json", "specs/legacy-evidence-carddemo-r2/spec.json"])
            self.assertEqual(len(pins["authorizations"]), 3)
            meta = json.loads((run_root / "prepared/capability-semantics-carddemo/metadata.json").read_text())
            self.assertEqual(meta["stage"], 4)
            self.assertFalse(meta["execute_authorized"])
            self.assertIn("input_pins_sha256", meta)

    def test_missing_or_stale_stage3_r2_blocks_init_prepare_and_execute_and_stage5_refused(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_stage1(run_root, tmp); self.init_and_approve_stage2_r2(run_root, tmp)
            self.assertEqual(stage4_main(self.args(run_root, tmp, ["/sdd:spec-init", "capability-semantics-carddemo", "--stage", "4"])), 2)
            self.init_and_approve_stage3_r2(run_root, tmp)
            self.assertEqual(stage4_main(self.args(run_root, tmp, ["/sdd:spec-init", "capability-semantics-carddemo", "--stage", "4"])), 0)
            self.assertEqual(stage4_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "capability-semantics-carddemo", "--stage", "4", "--prepare-only"])), 0)
            meta = json.loads((run_root / "prepared/capability-semantics-carddemo/metadata.json").read_text())
            auth = tmp / "stage4-exec-auth.json"
            write_json(auth, {"approved": True, "stage": 4, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": meta["request_sha256"]})
            (run_root / "specs/legacy-evidence-carddemo-r2/requirements.md").write_text("changed after approval\n", encoding="utf-8")
            self.assertEqual(stage4_main(self.args(run_root, tmp, ["/sdd:spec-init", "another-semantics", "--stage", "4"])), 2)
            self.assertEqual(stage4_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "capability-semantics-carddemo", "--stage", "4", "--prepare-only"])), 2)
            self.assertEqual(stage4_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "capability-semantics-carddemo", "--stage", "4", "--execute", "--authorization-file", str(auth)])), 2)
            self.assertEqual(stage4_main(self.args(run_root, tmp, ["/sdd:spec-init", "capability-semantics-carddemo", "--stage", "5"])), 2)

    def test_stage4_execution_authorization_requires_stage_and_request_hash(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.approved_chain(run_root, tmp)
            self.assertEqual(stage4_main(self.args(run_root, tmp, ["/sdd:spec-init", "capability-semantics-carddemo", "--stage", "4"])), 0)
            self.assertEqual(stage4_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "capability-semantics-carddemo", "--stage", "4", "--prepare-only"])), 0)
            meta = json.loads((run_root / "prepared/capability-semantics-carddemo/metadata.json").read_text())
            wrong_stage = tmp / "wrong-stage.json"
            write_json(wrong_stage, {"approved": True, "stage": 3, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": meta["request_sha256"]})
            wrong_hash = tmp / "wrong-hash.json"
            write_json(wrong_hash, {"approved": True, "stage": 4, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": "0" * 64})
            self.assertEqual(stage4_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "capability-semantics-carddemo", "--stage", "4", "--execute", "--authorization-file", str(wrong_stage)])), 2)
            self.assertEqual(stage4_main(self.args(run_root, tmp, ["/sdd:spec-requirements", "capability-semantics-carddemo", "--stage", "4", "--execute", "--authorization-file", str(wrong_hash)])), 2)


if __name__ == "__main__":
    unittest.main()

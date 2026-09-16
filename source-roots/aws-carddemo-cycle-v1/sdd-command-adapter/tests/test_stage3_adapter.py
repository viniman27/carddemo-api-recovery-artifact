import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from adapter import main as adapter_main
from stage3_adapter import main as stage3_main

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


class Stage3AdapterTests(unittest.TestCase):
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
        spec["gate"] = {
            "completeness_gate_passed": True, "gate_review_date": "2026-09-11", "blocking_gaps": [],
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
        write_json(auth, {"synthetic_test_fixture": True, "approved": True, "stage": 2, "run_id": "E3-01", "decision": "approve", "scope": "authorize stage 3 documentary evidence only for posting, interest, reporting"})
        spec = json.loads(spec_path.read_text())
        spec["approvals"]["requirements"]["generated"] = True
        spec["approvals"]["requirements"]["approved"] = True
        spec["gate"] = {
            "completeness_gate_passed": True, "gate_review_date": "2026-09-11", "blocking_gaps": [],
            "review": {"synthetic_test_fixture": True, "reviewer": "unit-test", "decision": "approve",
                "context": {"run_id": spec["run_id"], "capability": spec["capability"], "pipeline_stage": 2, "artifact_type": "capability-selection"},
                "artifact": {"path": "specs/capability-selection-carddemo-r2/requirements.md", "sha256": sha256_file(artifact)},
                "authorization": {"path": "reviews/stage-2-r2-authorization.json", "sha256": sha256_file(auth)},
                "upstream_specs": [{"path": "specs/pipeline-scope-carddemo/spec.json", "sha256": sha256_file(run_root / "specs/pipeline-scope-carddemo/spec.json")}]}}
        write_json(spec_path, spec)

    def stage3_args(self, run_root: Path, tmp_path: Path, extra):
        return extra + [
            "--run-root", str(run_root), "--allowed-run-parent", str(tmp_path),
            "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE),
            "--run-id", "E3-01", "--timestamp", "2026-09-11T14:00:00-03:00",
        ]

    def test_init_prepare_payload_preserves_stage3_inputs_and_all_three_tracks(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_stage1(run_root, tmp); self.init_and_approve_stage2_r2(run_root, tmp)
            self.assertEqual(stage3_main(self.stage3_args(run_root, tmp, ["/sdd:spec-init", "legacy-evidence-carddemo", "--stage", "3"])), 0)
            self.assertEqual(stage3_main(self.stage3_args(run_root, tmp, ["/sdd:spec-requirements", "legacy-evidence-carddemo", "--stage", "3", "--prepare-only"])), 0)
            spec = json.loads((run_root / "specs/legacy-evidence-carddemo/spec.json").read_text())
            parent_spec = json.loads((run_root / "specs/capability-selection-carddemo-r2/spec.json").read_text())
            self.assertEqual(spec["capability"], parent_spec["capability"])
            self.assertEqual(spec["pipeline_stage"], 3)
            self.assertEqual(spec["artifact_type"], "legacy-evidence")
            self.assertEqual(spec["upstream_specs"], ["specs/capability-selection-carddemo-r2/spec.json"])
            prepared = json.loads((run_root / "prepared/legacy-evidence-carddemo/request.json").read_text())
            payload_text = json.dumps(prepared, ensure_ascii=False)
            for token in ["posting", "interest", "reporting", "Legacy Evidence Specification", "stable numbered source lines", "app/cbl/EXAMPLE.cbl", "app/jcl/EXAMPLE.jcl"]:
                self.assertIn(token, payload_text)
            prompt = json.loads(prepared["input"][0]["content"])
            framework_by_path = {doc["path"]: doc["content"] for doc in prompt["framework_context"]}
            self.assertEqual(framework_by_path["settings/templates/pipeline/legacy-evidence-spec.md"], (FRAMEWORK / "settings/templates/pipeline/legacy-evidence-spec.md").read_text())
            self.assertEqual(prompt["approved_upstream"]["stage2_r2_requirements_md"], (run_root / "specs/capability-selection-carddemo-r2/requirements.md").read_text())
            self.assertNotIn("stage-2 rejected", payload_text.lower())
            self.assertNotIn("stage4 semantic reconstruction", payload_text.lower())
            meta = json.loads((run_root / "prepared/legacy-evidence-carddemo/metadata.json").read_text())
            self.assertEqual(meta["stage"], 3)
            self.assertFalse(meta["execute_authorized"])
            self.assertIn("input_pins_sha256", meta)

    def test_stage3_refuses_missing_or_stale_stage2_r2_at_init_prepare_execute_and_stage4(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); run_root = tmp / "run"
            self.init_stage1(run_root, tmp)
            self.assertEqual(stage3_main(self.stage3_args(run_root, tmp, ["/sdd:spec-init", "legacy-evidence-carddemo", "--stage", "3"])), 2)
            self.init_and_approve_stage2_r2(run_root, tmp)
            self.assertEqual(stage3_main(self.stage3_args(run_root, tmp, ["/sdd:spec-init", "legacy-evidence-carddemo", "--stage", "3"])), 0)
            self.assertEqual(stage3_main(self.stage3_args(run_root, tmp, ["/sdd:spec-requirements", "legacy-evidence-carddemo", "--stage", "3", "--prepare-only"])), 0)
            meta = json.loads((run_root / "prepared/legacy-evidence-carddemo/metadata.json").read_text())
            auth = tmp / "stage3-exec-auth.json"
            write_json(auth, {"approved": True, "stage": 3, "run_id": "E3-01", "model": "gpt-6-astra", "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": meta["request_sha256"]})
            (run_root / "specs/capability-selection-carddemo-r2/requirements.md").write_text("changed after approval\n", encoding="utf-8")
            self.assertEqual(stage3_main(self.stage3_args(run_root, tmp, ["/sdd:spec-init", "another-legacy-evidence", "--stage", "3"])), 2)
            self.assertEqual(stage3_main(self.stage3_args(run_root, tmp, ["/sdd:spec-requirements", "legacy-evidence-carddemo", "--stage", "3", "--prepare-only"])), 2)
            self.assertEqual(stage3_main(self.stage3_args(run_root, tmp, ["/sdd:spec-requirements", "legacy-evidence-carddemo", "--stage", "3", "--execute", "--authorization-file", str(auth)])), 2)
            self.assertEqual(stage3_main(self.stage3_args(run_root, tmp, ["/sdd:spec-init", "legacy-evidence-carddemo", "--stage", "4"])), 2)


if __name__ == "__main__":
    unittest.main()

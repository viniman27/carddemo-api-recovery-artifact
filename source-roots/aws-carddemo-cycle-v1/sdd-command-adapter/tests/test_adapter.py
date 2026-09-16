import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from adapter import main, parse_sse_result


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
FRAMEWORK = FIXTURES / "framework"
CORPUS = FIXTURES / "corpus"
PACKAGE = FIXTURES / "research-package.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


class AdapterTests(unittest.TestCase):
    def run_cli(self, args):
        return main(args)

    def init_stage1(self, run_root: Path, tmp_path: Path) -> Path:
        rc = self.run_cli([
            "/sdd:spec-init", "pipeline-scope-carddemo",
            "--run-root", str(run_root),
            "--allowed-run-parent", str(tmp_path),
            "--framework-root", str(FRAMEWORK),
            "--corpus-root", str(CORPUS),
            "--research-package", str(PACKAGE),
            "--run-id", "E3-01",
            "--timestamp", "2026-09-11T12:00:00-03:00",
        ])
        self.assertEqual(rc, 0)
        return run_root / "specs" / "pipeline-scope-carddemo"

    def approve_stage1(self, run_root: Path) -> None:
        spec_path = run_root / "specs" / "pipeline-scope-carddemo" / "spec.json"
        requirements_path = run_root / "specs" / "pipeline-scope-carddemo" / "requirements.md"
        requirements_path.write_text("# Synthetic approved stage-1 scope\n\nClearly marked test fixture, not real output.\n", encoding="utf-8")
        reviews = run_root / "reviews"
        reviews.mkdir(parents=True, exist_ok=True)
        auth_path = reviews / "stage-1-authorization.json"
        auth_path.write_text(json.dumps({
            "synthetic_test_fixture": True,
            "approved": True,
            "stage": 1,
            "run_id": "E3-01",
            "decision": "approve",
        }, indent=2) + "\n", encoding="utf-8")
        spec = json.loads(spec_path.read_text())
        spec["approvals"]["requirements"]["generated"] = True
        spec["approvals"]["requirements"]["approved"] = True
        spec["gate"] = {
            "completeness_gate_passed": True,
            "gate_review_date": "2026-09-11",
            "blocking_gaps": [],
            "review": {
                "synthetic_test_fixture": True,
                "reviewer": "unit-test",
                "decision": "approve",
                "context": {
                    "run_id": spec["run_id"],
                    "capability": spec["capability"],
                    "pipeline_stage": spec["pipeline_stage"],
                    "artifact_type": spec["artifact_type"],
                },
                "artifact": {"path": "specs/pipeline-scope-carddemo/requirements.md", "sha256": sha256_file(requirements_path)},
                "authorization": {"path": "reviews/stage-1-authorization.json", "sha256": sha256_file(auth_path)},
                "upstream_specs": [],
            },
        }
        spec_path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")

    def test_spec_init_creates_stage1_structure_without_approval(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_path = Path(d)
            run_root = tmp_path / "run"
            spec_dir = self.init_stage1(run_root, tmp_path)
            spec = json.loads((spec_dir / "spec.json").read_text())
            self.assertEqual(spec["feature_name"], "pipeline-scope-carddemo")
            self.assertEqual(spec["artifact_type"], "pipeline-scope")
            self.assertEqual(spec["pipeline_stage"], 1)
            self.assertEqual(spec["run_id"], "E3-01")
            self.assertEqual(spec["phase"], "initialized")
            self.assertFalse(spec["approvals"]["requirements"]["generated"])
            self.assertFalse(spec["approvals"]["requirements"]["approved"])
            self.assertFalse(spec["gate"]["completeness_gate_passed"])
            self.assertIsNone(spec["gate"]["review"])
            self.assertTrue((spec_dir / "requirements.md").read_text().startswith("# Requirements Document"))
            manifest = json.loads((spec_dir / "input-manifest.json").read_text())
            self.assertEqual(manifest["visibility_policy"], "stage-1-inventory-only-no-source-bodies")
            self.assertEqual([f["path"] for f in manifest["visible_inputs"]], ["app/cbl/EXAMPLE.cbl", "app/jcl/EXAMPLE.jcl"])

    def test_stage2_spec_init_requires_current_approved_stage1_and_pins_it(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_path = Path(d)
            run_root = tmp_path / "run"
            self.init_stage1(run_root, tmp_path)
            self.approve_stage1(run_root)
            rc = self.run_cli([
                "/sdd:spec-init", "capability-selection-carddemo", "--stage", "2",
                "--run-root", str(run_root),
                "--allowed-run-parent", str(tmp_path),
                "--framework-root", str(FRAMEWORK),
                "--corpus-root", str(CORPUS),
                "--research-package", str(PACKAGE),
                "--run-id", "E3-01",
                "--timestamp", "2026-09-11T13:00:00-03:00",
            ])
            self.assertEqual(rc, 0)
            spec_dir = run_root / "specs" / "capability-selection-carddemo"
            spec = json.loads((spec_dir / "spec.json").read_text())
            self.assertEqual(spec["feature_name"], "capability-selection-carddemo")
            self.assertEqual(spec["artifact_type"], "capability-selection")
            self.assertEqual(spec["pipeline_stage"], 2)
            self.assertEqual(spec["capability"], "unselected-stage-1-scope-only")
            self.assertEqual(spec["upstream_specs"], ["specs/pipeline-scope-carddemo/spec.json"])
            pins = json.loads((spec_dir / "input-pins.json").read_text())
            self.assertEqual(pins["upstream_specs"][0]["path"], "specs/pipeline-scope-carddemo/spec.json")
            self.assertEqual(pins["upstream_artifacts"][0]["path"], "specs/pipeline-scope-carddemo/requirements.md")
            self.assertEqual(pins["gate_check"]["status"], "current")

    def test_stage2_prepare_only_payload_uses_allowed_bodies_framework_template_and_low_commitment(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_path = Path(d)
            run_root = tmp_path / "run"
            self.init_stage1(run_root, tmp_path)
            self.approve_stage1(run_root)
            self.assertEqual(self.run_cli([
                "/sdd:spec-init", "capability-selection-carddemo", "--stage", "2",
                "--run-root", str(run_root), "--allowed-run-parent", str(tmp_path),
                "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE),
                "--run-id", "E3-01", "--timestamp", "2026-09-11T13:00:00-03:00",
            ]), 0)
            self.assertEqual(self.run_cli([
                "/sdd:spec-requirements", "capability-selection-carddemo", "--stage", "2", "--prepare-only",
                "--run-root", str(run_root), "--allowed-run-parent", str(tmp_path),
                "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE),
                "--run-id", "E3-01", "--timestamp", "2026-09-11T13:01:00-03:00",
            ]), 0)
            prepared = json.loads((run_root / "prepared" / "capability-selection-carddemo" / "request.json").read_text())
            payload_text = json.dumps(prepared, ensure_ascii=False)
            self.assertIn("Stage 2 Capability Selection Spec", payload_text)
            self.assertIn("Low-Commitment Selection", payload_text)
            self.assertIn("IDENTIFICATION DIVISION", payload_text)
            self.assertIn("Synthetic approved stage-1 scope", payload_text)
            self.assertIn("source_bodies", payload_text)
            self.assertIn("Treat selection as low commitment", payload_text)
            self.assertNotIn("collection-01", payload_text)
            self.assertNotIn("evaluation-quarantine", payload_text)
            self.assertNotIn("preflight", payload_text.lower())
            self.assertNotIn("returned contract", payload_text.lower())
            prompt = json.loads(prepared["input"][0]["content"])
            for doc in prompt["framework_context"]:
                self.assertEqual(doc["content"], (FRAMEWORK / doc["path"]).read_text())
            meta = json.loads((run_root / "prepared" / "capability-selection-carddemo" / "metadata.json").read_text())
            self.assertEqual(meta["stage"], 2)
            self.assertFalse(meta["execute_authorized"])
            self.assertIn("input_pins_sha256", meta)

    def test_stage2_rejects_parent_changed_at_init_prepare_and_execute_existing_prepared(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_path = Path(d)
            run_root = tmp_path / "run"
            self.init_stage1(run_root, tmp_path)
            self.approve_stage1(run_root)
            self.assertEqual(self.run_cli([
                "/sdd:spec-init", "capability-selection-carddemo", "--stage", "2",
                "--run-root", str(run_root), "--allowed-run-parent", str(tmp_path),
                "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE),
                "--run-id", "E3-01",
            ]), 0)
            self.assertEqual(self.run_cli([
                "/sdd:spec-requirements", "capability-selection-carddemo", "--stage", "2", "--prepare-only",
                "--run-root", str(run_root), "--allowed-run-parent", str(tmp_path),
                "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE),
                "--run-id", "E3-01", "--timestamp", "2026-09-11T13:01:00-03:00",
            ]), 0)
            prepared_meta = json.loads((run_root / "prepared" / "capability-selection-carddemo" / "metadata.json").read_text())
            auth = tmp_path / "stage2-auth.json"
            auth.write_text(json.dumps({
                "approved": True, "stage": 2, "run_id": "E3-01", "model": "gpt-6-astra",
                "base_url": "https://chatgpt.com/backend-api/codex", "request_sha256": prepared_meta["request_sha256"],
            }) + "\n", encoding="utf-8")
            (run_root / "specs" / "pipeline-scope-carddemo" / "requirements.md").write_text("changed after approval\n", encoding="utf-8")
            self.assertEqual(self.run_cli([
                "/sdd:spec-init", "another-stage2", "--stage", "2",
                "--run-root", str(run_root), "--allowed-run-parent", str(tmp_path),
                "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE),
            ]), 2)
            self.assertEqual(self.run_cli([
                "/sdd:spec-requirements", "capability-selection-carddemo", "--stage", "2", "--prepare-only",
                "--run-root", str(run_root), "--allowed-run-parent", str(tmp_path),
                "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE),
                "--run-id", "E3-01",
            ]), 2)
            self.assertEqual(self.run_cli([
                "/sdd:spec-requirements", "capability-selection-carddemo", "--stage", "2", "--execute", "--authorization-file", str(auth),
                "--run-root", str(run_root), "--allowed-run-parent", str(tmp_path),
                "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE),
                "--run-id", "E3-01",
            ]), 2)

    def test_stage2_missing_approval_blocks_init_and_prepare(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_path = Path(d)
            run_root = tmp_path / "run"
            self.init_stage1(run_root, tmp_path)
            self.assertEqual(self.run_cli([
                "/sdd:spec-init", "capability-selection-carddemo", "--stage", "2",
                "--run-root", str(run_root), "--allowed-run-parent", str(tmp_path),
                "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE),
            ]), 2)
            (run_root / "specs" / "capability-selection-carddemo").mkdir(parents=True)
            spec = json.loads((run_root / "specs" / "pipeline-scope-carddemo" / "spec.json").read_text())
            spec["feature_name"] = "capability-selection-carddemo"
            spec["pipeline_stage"] = 2
            spec["artifact_type"] = "capability-selection"
            spec["artifact_path"] = "specs/capability-selection-carddemo/requirements.md"
            spec["upstream_specs"] = ["specs/pipeline-scope-carddemo/spec.json"]
            (run_root / "specs" / "capability-selection-carddemo" / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
            self.assertEqual(self.run_cli([
                "/sdd:spec-requirements", "capability-selection-carddemo", "--stage", "2", "--prepare-only",
                "--run-root", str(run_root), "--allowed-run-parent", str(tmp_path),
                "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE),
            ]), 2)

    def test_stage3_and_above_are_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_path = Path(d)
            run_root = tmp_path / "run"
            self.assertEqual(self.run_cli([
                "/sdd:spec-init", "legacy-evidence-carddemo", "--stage", "3",
                "--run-root", str(run_root), "--allowed-run-parent", str(tmp_path),
                "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE),
            ]), 2)
            self.assertEqual(self.run_cli([
                "/sdd:spec-requirements", "legacy-evidence-carddemo", "--stage", "3",
                "--run-root", str(run_root), "--allowed-run-parent", str(tmp_path),
                "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE),
            ]), 2)

    def test_rejects_unknown_command(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_path = Path(d)
            self.assertEqual(self.run_cli(["/sdd:spec-design", "x", "--run-root", str(tmp_path)]), 2)

    def test_rejects_roots_outside_scope_and_symlink_run_root(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_path = Path(d)
            outside = tmp_path / "outside"
            outside.mkdir()
            self.assertEqual(self.run_cli([
                "/sdd:spec-init", "valid-feature", "--run-root", str(outside),
                "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE)
            ]), 2)
            real = tmp_path / "real"
            real.mkdir()
            link = tmp_path / "link"
            link.symlink_to(real, target_is_directory=True)
            self.assertEqual(self.run_cli([
                "/sdd:spec-init", "valid-feature", "--run-root", str(link), "--allowed-run-parent", str(tmp_path),
                "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE)
            ]), 2)

    def test_spec_init_refuses_to_overwrite_existing_run(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_path = Path(d)
            run_root = tmp_path / "run"
            args = [
                "/sdd:spec-init", "pipeline-scope-carddemo", "--run-root", str(run_root),
                "--allowed-run-parent", str(tmp_path),
                "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE)
            ]
            self.assertEqual(self.run_cli(args), 0)
            self.assertEqual(self.run_cli(args), 2)

    def test_prepare_only_writes_stage1_payload_without_tools_history_or_preflight(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_path = Path(d)
            run_root = tmp_path / "run"
            self.init_stage1(run_root, tmp_path)
            self.assertEqual(self.run_cli([
                "/sdd:spec-requirements", "pipeline-scope-carddemo", "--prepare-only", "--run-root", str(run_root),
                "--allowed-run-parent", str(tmp_path),
                "--framework-root", str(FRAMEWORK), "--corpus-root", str(CORPUS), "--research-package", str(PACKAGE),
                "--run-id", "E3-01", "--timestamp", "2026-09-11T12:01:00-03:00",
            ]), 0)
            prepared = json.loads((run_root / "prepared" / "pipeline-scope-carddemo" / "request.json").read_text())
            self.assertEqual(prepared["model"], "gpt-6-astra")
            self.assertFalse(prepared["store"])
            self.assertNotIn("tools", prepared)
            self.assertNotIn("previous_response_id", prepared)
            self.assertNotIn("temperature", prepared)
            self.assertNotIn("max_output_tokens", prepared)
            payload_text = json.dumps(prepared)
            self.assertNotIn("collection-01", payload_text)
            self.assertNotIn("evaluation-quarantine", payload_text)
            self.assertNotIn("preflight", payload_text.lower())
            self.assertNotIn("IDENTIFICATION DIVISION", payload_text)
            meta = json.loads((run_root / "prepared" / "pipeline-scope-carddemo" / "metadata.json").read_text())
            self.assertEqual(meta["stage"], 1)
            self.assertFalse(meta["execute_authorized"])

    def test_parse_sse_result_uses_output_text_done_when_completed_output_empty(self):
        raw = '\n'.join([
            'data: {"type":"response.output_text.done","output_index":0,"content_index":0,"text":"hello"}',
            'data: {"type":"response.completed","response":{"status":"completed","model":"gpt-6-astra","output":[],"store":false,"tools":[],"previous_response_id":null}}',
            'data: [DONE]',
        ])
        parsed = parse_sse_result(raw)
        self.assertEqual(parsed["text"], "hello")
        self.assertEqual(parsed["model"], "gpt-6-astra")
        self.assertFalse(parsed["store"])


if __name__ == "__main__":
    unittest.main()

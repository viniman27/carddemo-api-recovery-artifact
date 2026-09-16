"""Stage 9 qualification tests use synthetic files; no AWS run is executed."""
import hashlib
import inspect
import json
from pathlib import Path
import tempfile
import unittest

from pipeline.tools import stage9_qualify


class Stage9QualificationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def sha_pin(self, path: Path, rel: str) -> dict:
        data = path.read_bytes()
        return {"path": rel, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}

    def test_stage9_run_metadata_records_adoption_not_generation_or_campaign(self):
        upstream = {"stages": {"8": {"spec": "s8/spec.json", "sha256": "a" * 64}}}
        implementation = self.write("impl/p2b_binding.py", "print('existing')\n")
        report = stage9_qualify.build_stage9_artifact(
            run_id="E3-stage9-01",
            upstream_run_id="E3-01",
            upstream_manifest=upstream,
            implementation_path=implementation,
            qualification={"overall_passed": True, "tracks": ["posting", "interest", "reporting"]},
            limits=["not T1-T4"],
        )
        self.assertEqual(report["artifact_type"], "implementation-executable-qualification")
        self.assertEqual(report["adoption"]["mode"], "source_adoption_and_build")
        self.assertEqual(report["adoption"]["generated_from_scratch"], False)
        self.assertEqual(report["campaign_boundary"], "not_T1_T2_T3_T4")
        self.assertEqual(report["implementation"]["sha256"], hashlib.sha256(implementation.read_bytes()).hexdigest())

    def test_hash_preservation_detects_stage1_to_stage8_mutation(self):
        before = {"stage1": "0" * 64, "stage8": "1" * 64}
        after = dict(before)
        self.assertEqual(stage9_qualify.compare_hashes(before, after)["preserved"], True)
        after["stage8"] = "2" * 64
        diff = stage9_qualify.compare_hashes(before, after)
        self.assertFalse(diff["preserved"])
        self.assertEqual(diff["changed"], ["stage8"])

    def test_stage9_tool_has_no_hardcoded_preflight_isolated_cycle_dependency(self):
        source = inspect.getsource(stage9_qualify)
        self.assertNotIn("unified-preflight", source)
        self.assertNotIn("evidence-20260915T-v3-fixed-current5x2-gcovclean", source)

    def test_manifest_requires_explicit_upstream_contract_toolchain_resources_and_commands(self):
        manifest = {"kind": "stage9-input-manifest", "version": 1}
        path = self.write("manifest.json", json.dumps(manifest))
        with self.assertRaises(stage9_qualify.ManifestError) as ctx:
            stage9_qualify.load_stage9_manifest(path)
        self.assertIn("upstream", str(ctx.exception))
        self.assertIn("implementation_sources", str(ctx.exception))
        self.assertIn("contract", str(ctx.exception))
        self.assertIn("toolchain", str(ctx.exception))
        self.assertIn("resources", str(ctx.exception))
        self.assertIn("commands", str(ctx.exception))

    def test_manifest_pin_tamper_blocks_source_adoption(self):
        src = self.write("src/p2b_binding.py", "print('v1')\n")
        manifest = {
            "kind": "stage9-input-manifest",
            "version": 1,
            "upstream": {"run_id": "E3-01", "stage_specs": []},
            "implementation_sources": {"root": "src", "files": [{"path": "p2b_binding.py", "sha256": "0" * 64, "bytes": src.stat().st_size}]},
            "contract": {"files": []},
            "toolchain": {"python": "python3", "commands": {"build": [], "start": [], "qualify": [], "package": []}},
            "resources": {"fixture_registry": {"path": "fixtures/registry.json", "sha256": "1" * 64, "bytes": 2}, "files": []},
            "commands": {"build": [], "start": [], "qualify": [], "package": []},
        }
        manifest_path = self.write("manifest.json", json.dumps(manifest))
        loaded = stage9_qualify.load_stage9_manifest(manifest_path)
        with self.assertRaises(stage9_qualify.ManifestError):
            stage9_qualify.verify_manifest_pins(loaded, manifest_path.parent)

    def test_prepare_workspace_copies_declared_sources_and_rejects_binary_outputs(self):
        src = self.write("src/p2b_binding.py", "print('source')\n")
        old_bin = self.root / "src" / "build" / "CBTRN02C"
        old_bin.parent.mkdir(parents=True)
        old_bin.write_bytes(b"old-binary")
        manifest = {
            "implementation_sources": {
                "root": "src",
                "files": [self.sha_pin(src, "p2b_binding.py")],
                "forbidden_existing_binary_dirs": ["build", "runs", "__pycache__"],
            },
            "contract": {"files": []},
            "resources": {"files": []},
        }
        target = self.root / "run" / "execution"
        result = stage9_qualify.prepare_source_workspace(manifest, self.root, target)
        self.assertTrue((target / "aws-carddemo-cycle-v1" / "P2b" / "p2b_binding.py").is_file())
        self.assertFalse((target / "aws-carddemo-cycle-v1" / "P2b" / "build" / "CBTRN02C").exists())
        self.assertEqual(result["adoption_mode"], "source_adoption_and_build")
        self.assertEqual(result["preexisting_binaries_copied"], [])

    def test_rerun_refuses_to_overwrite_existing_stage9_run(self):
        run_root = self.root / "sdd-runs" / "E3-stage9-02"
        run_root.mkdir(parents=True)
        (run_root / "sentinel.txt").write_text("preserve")
        with self.assertRaises(FileExistsError):
            stage9_qualify.reserve_new_run_root(self.root / "sdd-runs", "E3-stage9-02")
        self.assertEqual((run_root / "sentinel.txt").read_text(), "preserve")


if __name__ == "__main__":
    unittest.main()

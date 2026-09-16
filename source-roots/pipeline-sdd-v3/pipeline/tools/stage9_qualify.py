#!/usr/bin/env python3
"""Run Stage 9 executable implementation qualification for AWS CardDemo.

Stage 9 is manifest-driven. It adopts explicitly pinned source files and
resources, builds fresh binaries inside a new run directory, starts localhost,
qualifies the three AWS tracks, and packages the executable slice. It does not
call models and does not run T1-T4 campaigns.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

STAGE_SPECS = [
    (1, "specs/pipeline-scope-carddemo/spec.json"),
    (2, "specs/capability-selection-carddemo-r2/spec.json"),
    (3, "specs/legacy-evidence-carddemo-r2/spec.json"),
    (4, "specs/capability-semantics-carddemo/spec.json"),
    (5, "specs/canonical-data-boundary-carddemo/spec.json"),
    (6, "specs/api-contract-carddemo-r3/spec.json"),
    (7, "specs/adapter-behavior-carddemo-r2/spec.json"),
    (8, "specs/semantic-validation-carddemo/spec.json"),
]
TRACKS = ["posting", "interest", "reporting"]
REQUIRED_MANIFEST_KEYS = ["upstream", "implementation_sources", "contract", "toolchain", "resources", "commands"]
BINARY_SUFFIXES = {"", ".dylib", ".so", ".o", ".a", ".exe"}
TEXT_SOURCE_SUFFIXES = {".py", ".c", ".cbl", ".cpy", ".json", ".yaml", ".yml", ".md", ".txt", ".jcl", ".prc"}


class ManifestError(RuntimeError):
    """Invalid or tampered Stage 9 manifest."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_pin(path: Path, rel: str | None = None) -> dict[str, Any]:
    return {"path": rel if rel is not None else str(path), "sha256": sha256(path), "bytes": path.stat().st_size}


def safe_relpath(value: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ManifestError("paths must be non-empty relative strings")
    if value.startswith(("/", "~")) or ":" in value or "\\" in value or "\x00" in value:
        raise ManifestError(f"unsafe path: {value!r}")
    path = Path(value)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ManifestError(f"unsafe path: {value!r}")
    return path


def resolve_under(base: Path, rel: str) -> Path:
    rel_path = safe_relpath(rel)
    resolved_base = base.resolve()
    resolved = (resolved_base / rel_path).resolve()
    if resolved != resolved_base and resolved_base not in resolved.parents:
        raise ManifestError(f"path escapes base: {rel}")
    return resolved


def load_stage9_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"manifest is not valid JSON: {exc}") from exc
    if manifest.get("kind") != "stage9-input-manifest" or manifest.get("version") != 1:
        raise ManifestError("manifest kind/version must be stage9-input-manifest v1")
    missing = [key for key in REQUIRED_MANIFEST_KEYS if key not in manifest]
    if missing:
        raise ManifestError("manifest missing required sections: " + ", ".join(missing))
    toolchain = manifest.get("toolchain") or {}
    commands = manifest.get("commands") or {}
    for key in ["build", "start", "qualify", "package"]:
        if key not in commands:
            raise ManifestError(f"commands.{key} is required")
    if not toolchain.get("python"):
        raise ManifestError("toolchain.python is required")
    if not isinstance(manifest.get("implementation_sources", {}).get("files"), list):
        raise ManifestError("implementation_sources.files must be a list")
    return manifest


def verify_pin(path: Path, pin: dict[str, Any], label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ManifestError(f"missing pinned {label}: {path}")
    expected_hash = pin.get("sha256")
    expected_bytes = pin.get("bytes")
    actual_hash = sha256(path)
    actual_bytes = path.stat().st_size
    if expected_hash != actual_hash or expected_bytes != actual_bytes:
        raise ManifestError(
            f"pin mismatch for {label} {pin.get('path')}: "
            f"{actual_hash}/{actual_bytes} != {expected_hash}/{expected_bytes}"
        )
    return {"path": str(path), "sha256": actual_hash, "bytes": actual_bytes}


def iter_pin_groups(manifest: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    groups = [("implementation_sources", manifest.get("implementation_sources", {}))]
    for section in ["contract", "resources"]:
        item = manifest.get(section, {})
        if "groups" in item:
            groups.extend((f"{section}.{idx}", group) for idx, group in enumerate(item["groups"]))
        else:
            groups.append((section, item))
    return groups


def verify_manifest_pins(manifest: dict[str, Any], manifest_base: Path) -> dict[str, Any]:
    checked: list[dict[str, Any]] = []
    for label, group in iter_pin_groups(manifest):
        root_value = group.get("root", ".")
        root = resolve_under(manifest_base, root_value)
        for pin in group.get("files", []):
            rel = pin.get("path")
            source = resolve_under(root, rel)
            checked.append(verify_pin(source, pin, f"{label}"))
    fixture_registry = manifest.get("resources", {}).get("fixture_registry")
    if fixture_registry:
        source = resolve_under(manifest_base, fixture_registry["path"])
        checked.append(verify_pin(source, fixture_registry, "fixture_registry"))
    python_pin = manifest.get("toolchain", {}).get("python_pin")
    if python_pin:
        checked.append(verify_pin(Path(manifest["toolchain"]["python"]), python_pin, "toolchain.python"))
    return {"checked_count": len(checked), "checked": checked}


def is_probable_binary_path(path: Path) -> bool:
    if path.suffix in TEXT_SOURCE_SUFFIXES:
        return False
    if path.name in {"LICENSE", "NOTICE", "README"}:
        return False
    if path.suffix in BINARY_SUFFIXES:
        return True
    return False


def copy_pin_group(group: dict[str, Any], manifest_base: Path, target_root: Path, label: str) -> list[dict[str, Any]]:
    source_root = resolve_under(manifest_base, group.get("root", "."))
    default_target = "aws-carddemo-cycle-v1/P2b" if label == "implementation_sources" else "."
    dest_root = target_root / safe_relpath(group.get("target", default_target))
    copied = []
    for pin in group.get("files", []):
        rel = pin["path"]
        source = resolve_under(source_root, rel)
        verify_pin(source, pin, label)
        if label == "implementation_sources" and is_probable_binary_path(Path(rel)):
            raise ManifestError(f"implementation source list includes probable binary/build output: {rel}")
        dest = dest_root / safe_relpath(rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        copied.append({"label": label, "source": str(source), "target": str(dest), "sha256": sha256(dest), "bytes": dest.stat().st_size})
    return copied


def prepare_source_workspace(manifest: dict[str, Any], manifest_base: Path, isolated: Path) -> dict[str, Any]:
    if isolated.exists():
        raise FileExistsError(f"execution workspace already exists: {isolated}")
    copied: list[dict[str, Any]] = []
    copied.extend(copy_pin_group(manifest["implementation_sources"], manifest_base, isolated, "implementation_sources"))
    for label, group in iter_pin_groups(manifest):
        if label == "implementation_sources":
            continue
        copied.extend(copy_pin_group(group, manifest_base, isolated, label))
    fixture_registry = manifest.get("resources", {}).get("fixture_registry")
    registry_target = None
    if fixture_registry:
        source = resolve_under(manifest_base, fixture_registry["path"])
        verify_pin(source, fixture_registry, "fixture_registry")
        registry_target = isolated / "aws-carddemo-cycle-v1/P3/technical-packages-v3-argument/registry.json"
        registry_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, registry_target)
        copied.append({"label": "fixture_registry", "source": str(source), "target": str(registry_target), "sha256": sha256(registry_target), "bytes": registry_target.stat().st_size})
    old_binary_copied = []
    p2b = isolated / "aws-carddemo-cycle-v1/P2b"
    for forbidden in manifest["implementation_sources"].get("forbidden_existing_binary_dirs", ["build", "runs", "__pycache__"]):
        forbidden_path = p2b / safe_relpath(forbidden)
        if forbidden_path.exists():
            old_binary_copied.append(str(forbidden_path))
    if old_binary_copied:
        raise ManifestError("forbidden old binary/run directories copied: " + ", ".join(old_binary_copied))
    impl = p2b / "p2b_binding.py"
    return {
        "adoption_mode": "source_adoption_and_build",
        "generated_from_scratch": False,
        "implementation": str(impl),
        "implementation_sha256": sha256(impl) if impl.exists() else None,
        "target": str(isolated),
        "fixture_registry": str(registry_target) if registry_target else None,
        "copied_files": copied,
        "copied_file_count": len(copied),
        "preexisting_binaries_copied": old_binary_copied,
    }


def reserve_new_run_root(sdd_runs_root: Path, run_id: str) -> Path:
    run_root = sdd_runs_root / run_id
    try:
        run_root.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise FileExistsError(f"Stage 9 run already exists and will not be overwritten: {run_root}") from exc
    return run_root


def stage_hashes(upstream_root: Path, stage_specs: list[tuple[int, str]] | None = None) -> dict[str, str]:
    specs = stage_specs or STAGE_SPECS
    return {f"stage{n}": sha256(upstream_root / rel) for n, rel in specs}


def compare_hashes(before: dict[str, str], after: dict[str, str]) -> dict[str, Any]:
    changed = [key for key in sorted(before) if before.get(key) != after.get(key)]
    added_or_removed = sorted(set(before) ^ set(after))
    changed.extend(k for k in added_or_removed if k not in changed)
    return {"preserved": not changed, "changed": changed, "before": before, "after": after}


def build_stage9_artifact(
    *,
    run_id: str,
    upstream_run_id: str,
    upstream_manifest: dict[str, Any],
    implementation_path: Path,
    qualification: dict[str, Any],
    limits: list[str],
) -> dict[str, Any]:
    return {
        "kind": "stage9-implementation-executable-qualification-report",
        "artifact_type": "implementation-executable-qualification",
        "run_id": run_id,
        "upstream_run_id": upstream_run_id,
        "campaign_boundary": "not_T1_T2_T3_T4",
        "adoption": {
            "mode": "source_adoption_and_build",
            "generated_from_scratch": False,
            "claim": "Stage 9 adopts explicitly pinned existing source files and builds fresh executable artifacts in the run workspace.",
        },
        "upstream": upstream_manifest,
        "implementation": file_pin(implementation_path),
        "qualification": qualification,
        "limits": limits,
    }


def run_check_gate(framework_root: Path, upstream_root: Path, spec_rel: str) -> dict[str, Any]:
    cmd = [sys.executable, str(framework_root / "pipeline/tools/check_gate.py"), str(upstream_root), spec_rel]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {"status": "invalid", "reasons": [proc.stdout, proc.stderr]}
    data["command"] = cmd
    data["exit_code"] = proc.returncode
    return data


def manifest_stage_specs(manifest: dict[str, Any]) -> list[tuple[int, str]]:
    specs = manifest.get("upstream", {}).get("stage_specs") or []
    if not specs:
        return STAGE_SPECS
    out = []
    for item in specs:
        out.append((int(item["stage"]), item["path"]))
    return out


def verify_upstream(framework_root: Path, upstream_root: Path, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    specs_list = manifest_stage_specs(manifest or {})
    hashes = stage_hashes(upstream_root, specs_list)
    stage8_rel = [rel for n, rel in specs_list if n == 8][0]
    gate = run_check_gate(framework_root, upstream_root, stage8_rel)
    specs = {}
    for n, rel in specs_list:
        p = upstream_root / rel
        specs[str(n)] = {"spec": rel, "sha256": sha256(p), "bytes": p.stat().st_size}
    return {"run_root": str(upstream_root), "stages": specs, "stage8_gate": gate, "hashes": hashes, "approved_1_to_8_current": gate.get("status") == "current" and gate.get("exit_code") == 0}


def run_command(cmd: list[str], cwd: Path, env: dict[str, str] | None = None, timeout: int = 180, expect: int | None = 0) -> dict[str, Any]:
    merged = dict(os.environ)
    if env:
        merged.update(env)
    started = time.time()
    proc = subprocess.run(cmd, cwd=cwd, env=merged, capture_output=True, text=True, timeout=timeout)
    result = {"cmd": cmd, "cwd": str(cwd), "env_override": env or {}, "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "duration_s": round(time.time() - started, 3)}
    if expect is not None and proc.returncode != expect:
        raise RuntimeError(json.dumps(result, indent=2))
    return result


def http_post_json(url: str, timeout: int = 90) -> dict[str, Any]:
    req = urllib.request.Request(url, data=b"{}", headers={"content-type": "application/json"}, method="POST")
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
    return {"url": url, "status": status, "raw_sha256": hashlib.sha256(raw).hexdigest(), "raw_bytes": len(raw), "body": json.loads(raw), "duration_s": round(time.time() - started, 3)}


def build_fresh(adopted: dict[str, Any], python: Path) -> dict[str, Any]:
    p2b = Path(adopted["implementation"]).parent
    before = {p.name for p in (p2b / "build").glob("*")} if (p2b / "build").exists() else set()
    result = run_command([str(python), str(p2b / "p2b_binding.py"), "build"], cwd=p2b, timeout=300)
    after_files = sorted(p for p in (p2b / "build").glob("*") if p.is_file())
    built = [file_pin(p) | {"fresh_in_this_workspace": p.name not in before} for p in after_files]
    return {"command": result, "built_files": built, "built_file_count": len(built)}


def execute_http_qualification(adopted: dict[str, Any], run_root: Path, python: Path) -> dict[str, Any]:
    p2b = Path(adopted["implementation"]).parent
    port_file = run_root / "execution/server.port"
    if port_file.exists():
        port_file.unlink()
    before_dirs = {p.resolve() for p in (p2b / "runs").glob("*")} if (p2b / "runs").exists() else set()
    env = dict(os.environ)
    if adopted.get("fixture_registry"):
        env["P2B_FIXTURE_REGISTRY"] = adopted["fixture_registry"]
    proc = subprocess.Popen([str(python), str(p2b / "p2b_binding.py"), "serve", "--port-file", str(port_file)], cwd=p2b, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    lifecycle: dict[str, Any] = {"pid": proc.pid, "cmd": [str(python), str(p2b / "p2b_binding.py"), "serve", "--port-file", str(port_file)]}
    try:
        for _ in range(300):
            if port_file.exists():
                break
            if proc.poll() is not None:
                break
            time.sleep(0.1)
        if not port_file.exists():
            out, err = proc.communicate(timeout=1) if proc.poll() is not None else ("", "")
            raise RuntimeError(f"server did not publish port; return={proc.returncode}; stdout={out}; stderr={err}")
        port = int(port_file.read_text().strip())
        results = [http_post_json(f"http://127.0.0.1:{port}/{track}") | {"track": track} for track in TRACKS]
    finally:
        proc.terminate()
        try:
            out, err = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = proc.communicate(timeout=10)
        lifecycle.update({"returncode": proc.returncode, "stdout": out, "stderr": err})
    after_dirs = {p.resolve() for p in (p2b / "runs").glob("*")} if (p2b / "runs").exists() else set()
    new_dirs = sorted(after_dirs - before_dirs)
    audits = []
    for directory in new_dirs:
        audit_path = directory / "audit.json"
        if audit_path.exists():
            audit = json.loads(audit_path.read_text())
            audits.append({
                "track": audit.get("INV", {}).get("track"),
                "audit_path": str(audit_path),
                "audit_sha256": sha256(audit_path),
                "reached_cobol": audit.get("RESP", {}).get("reached_cobol"),
                "program_exit": audit.get("RESP", {}).get("program_exit"),
                "response_status": audit.get("RESP", {}).get("status"),
                "fixture_registry": audit.get("RES", {}).get("selected_fixture", {}).get("registryPath"),
                "captures_count": len(audit.get("CAP", {}).get("captures", [])),
                "state_after_entry_count": audit.get("STATE", {}).get("after", {}).get("entryCount"),
            })
    manifest = {
        "kind": "Stage9 fresh HTTP executable qualification; not official T1/T2/T3/T4",
        "localhost": f"127.0.0.1:{port}",
        "results": results,
        "current_run_dirs": [str(p) for p in new_dirs],
        "audits": audits,
        "server_lifecycle": lifecycle,
    }
    (p2b / "readiness-manifest.json").write_text(json.dumps({"kind": manifest["kind"], "results": results}, indent=2) + "\n")
    schema_proc = subprocess.run([str(python), str(p2b / "validate_p2b.py")], cwd=p2b, capture_output=True, text=True, timeout=120)
    manifest["schema_validation"] = {"exit_code": schema_proc.returncode, "stdout": schema_proc.stdout, "stderr": schema_proc.stderr}
    manifest["overall_passed"] = (
        all(r["status"] == 200 for r in results)
        and all(a.get("reached_cobol") for a in audits)
        and len({a.get("track") for a in audits}) == 3
        and schema_proc.returncode == 0
    )
    return manifest


def write_launch_script(run_root: Path, python: Path, fixture_registry: str | None) -> Path:
    script = run_root / "launch_stage9.py"
    text = f'''#!/usr/bin/env python3
"""Reproduce Stage 9 package build/start smoke from this run directory."""
from pathlib import Path
import os, subprocess, sys
root = Path(__file__).resolve().parent
p2b = root / "execution/isolated-cycle/aws-carddemo-cycle-v1/P2b"
python = Path(os.environ.get("STAGE9_PYTHON", {str(python)!r}))
env = dict(os.environ)
registry = root / "execution/isolated-cycle/aws-carddemo-cycle-v1/P3/technical-packages-v3-argument/registry.json"
if registry.exists():
    env["P2B_FIXTURE_REGISTRY"] = str(registry)
cmd = [str(python), str(p2b / "p2b_binding.py"), "smoke"]
raise SystemExit(subprocess.call(cmd, cwd=p2b, env=env))
'''
    script.write_text(text, encoding="utf-8")
    script.chmod(0o755)
    return script


def package_run(run_root: Path, python: Path, fixture_registry: str | None) -> dict[str, Any]:
    launch = write_launch_script(run_root, python, fixture_registry)
    package_path = run_root / f"{run_root.name}-stage9-executable-package.tar.gz"
    if package_path.exists():
        raise FileExistsError(f"package already exists: {package_path}")
    with tarfile.open(package_path, "w:gz") as tf:
        for rel in ["execution", "stage9-input-manifest.json", launch.name, "stage9-pending-review.md"]:
            path = run_root / rel
            if path.exists():
                tf.add(path, arcname=f"{run_root.name}/{rel}")
    return {"package": str(package_path), "sha256": sha256(package_path), "bytes": package_path.stat().st_size, "launch_script": str(launch)}


def write_stage9_spec(run_root: Path, artifact_rel: str, upstream_manifest: dict[str, Any], upstream_run_id: str) -> None:
    spec_dir = run_root / "specs/implementation-executable-qualification-carddemo"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec = {
        "feature_name": "carddemo-implementation-executable-qualification",
        "artifact_type": "implementation-executable-qualification",
        "pipeline_stage": 9,
        "capability": "carddemo-full3track-stage9-only",
        "run_id": run_root.name,
        "artifact_path": artifact_rel,
        "upstream_specs": [],
        "external_upstream_approved_run": {"run_id": upstream_run_id, "stage8_spec": STAGE_SPECS[-1][1], "stage_hashes": upstream_manifest["hashes"]},
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "language": "pt-BR",
        "phase": "stage9-executed" if (run_root / artifact_rel).exists() else "initialized",
        "gate": {"completeness_gate_passed": False, "gate_review_date": None, "blocking_gaps": ["pending human Stage 9 review"], "review": None},
        "ready_for_implementation": False,
    }
    (spec_dir / "spec.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")


def write_markdown_report(path: Path, artifact: dict[str, Any]) -> None:
    q = artifact["qualification"]
    lines = [
        "# Stage 9 — Implementation and Executable Qualification",
        "",
        "Status: " + ("PASS técnico" if q.get("overall_passed") else "FAIL técnico"),
        "",
        "Este estágio adotou fontes existentes explicitamente pinadas e construiu binários novos no diretório do run.",
        "Não declara geração do zero, não executa campanhas T1–T4 e não concede aprovação humana.",
        "",
        "## Trilhas HTTP executadas",
    ]
    for r in q.get("results", []):
        lines.append(f"- {r['track']}: HTTP {r['status']}, bytes={r['raw_bytes']}, sha256={r['raw_sha256']}")
    lines += ["", "## Audits alcançados"]
    for a in q.get("audits", []):
        lines.append(f"- {a.get('track')}: reached_cobol={a.get('reached_cobol')}, program_exit={a.get('program_exit')}, audit={a.get('audit_path')}")
    lines += ["", "## Limites"] + [f"- {item}" for item in artifact.get("limits", [])]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_pending_review(run_root: Path) -> None:
    (run_root / "stage9-pending-review.md").write_text(
        "# Revisão pendente — Stage 9\n\n"
        "Status: unreviewed. O run registra qualificação técnica executada, mas não aprovação humana.\n\n"
        "Pendências: revisão de escopo, suficiência da adoção por fonte, limites de fixtures técnicas, e decisão explícita antes de qualquer campanha T1–T4.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--cycle-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    args.cycle_root = args.cycle_root.resolve()
    args.manifest = args.manifest.resolve()
    manifest = load_stage9_manifest(args.manifest)
    upstream_run_id = manifest["upstream"].get("run_id")
    if not upstream_run_id:
        raise ManifestError("upstream.run_id is required")
    upstream_root = args.cycle_root / "sdd-runs" / upstream_run_id
    run_root = reserve_new_run_root(args.cycle_root / "sdd-runs", args.run_id)
    try:
        shutil.copy2(args.manifest, run_root / "stage9-input-manifest.json")
        manifest_base = args.manifest.resolve().parent
        pin_report = verify_manifest_pins(manifest, manifest_base)
        upstream_before = verify_upstream(args.framework_root, upstream_root, manifest)
        if not upstream_before["approved_1_to_8_current"]:
            diag = {"status": "blocked", "reason": "upstream stage8 gate is not current", "upstream": upstream_before}
            (run_root / "stage9-diagnostic.json").write_text(json.dumps(diag, indent=2, ensure_ascii=False) + "\n")
            print(json.dumps(diag, indent=2, ensure_ascii=False))
            return 1
        write_pending_review(run_root)
        adopted = prepare_source_workspace(manifest, manifest_base, run_root / "execution/isolated-cycle")
        python = Path(manifest["toolchain"]["python"])
        build_report = build_fresh(adopted, python)
        qualification: dict[str, Any] = {"overall_passed": False, "skipped": not args.execute, "reason": "--execute not provided"}
        if args.execute:
            qualification = execute_http_qualification(adopted, run_root, python)
        package_report = package_run(run_root, python, adopted.get("fixture_registry"))
        upstream_after = verify_upstream(args.framework_root, upstream_root, manifest)
        preservation = compare_hashes(upstream_before["hashes"], upstream_after["hashes"])
        artifact = build_stage9_artifact(
            run_id=args.run_id,
            upstream_run_id=upstream_run_id,
            upstream_manifest=upstream_before,
            implementation_path=Path(adopted["implementation"]),
            qualification=qualification,
            limits=[
                "qualificação técnica estreita por localhost e três POST {}",
                "não é campanha T1/T2/T3/T4 nem avaliação independente",
                "não afirma fidelidade semântica plena; reutiliza Stage6r3/7r2/8 aprovados",
                "falhas COBOL não-zero são preservadas nos audits, não reescritas como sucesso de programa",
            ],
        )
        artifact["input_manifest"] = file_pin(run_root / "stage9-input-manifest.json", "stage9-input-manifest.json")
        artifact["manifest_pin_verification"] = pin_report
        artifact["source_workspace"] = adopted
        artifact["build"] = build_report
        artifact["package"] = package_report
        artifact["stage1_to_8_hash_preservation"] = preservation
        artifact["gate_metadata"] = {"human_approval_granted": False, "stage9_review_status": "pending", "false_approved": False}
        artifact_rel = "stage9-implementation-executable-qualification.json"
        (run_root / artifact_rel).write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n")
        write_markdown_report(run_root / "stage9-implementation-executable-qualification.md", artifact)
        write_stage9_spec(run_root, artifact_rel, upstream_before, upstream_run_id)
        print(json.dumps({"run_root": str(run_root), "artifact": str(run_root / artifact_rel), "overall_passed": qualification.get("overall_passed"), "hashes_preserved": preservation["preserved"], "package": package_report}, indent=2, ensure_ascii=False))
        return 0 if qualification.get("overall_passed") and preservation["preserved"] else 1
    except Exception:
        # Preserve partial evidence in the newly reserved run, but never retry over it.
        raise


if __name__ == "__main__":
    raise SystemExit(main())

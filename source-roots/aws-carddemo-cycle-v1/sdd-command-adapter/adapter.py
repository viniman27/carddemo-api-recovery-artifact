#!/usr/bin/env python3
"""Local explicit bridge for adapted SDD stage-1 commands.

This is not a native local runtime slash-command handler. It accepts the literal
command tokens only so the AWS CardDemo v3 candidate run can prepare a bounded
stage-1 Pipeline Scope Spec request without reading historical/evaluation data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BRIDGE_NAME = "local-explicit-adapter-not-native-slash-command"
DEFAULT_BASE = Path("<REDACTED_LOCAL_PATH>")
DEFAULT_RUN_PARENT = DEFAULT_BASE / "casos/aws-carddemo-cycle-v1/sdd-runs"
DEFAULT_RUN_ROOT = DEFAULT_RUN_PARENT / "E3-01"
DEFAULT_FRAMEWORK_ROOT = DEFAULT_BASE / "pipeline-sdd-v3/pipeline"
DEFAULT_CORPUS_ROOT = DEFAULT_BASE / "casos/aws-carddemo-preparation/research-corpus"
DEFAULT_RESEARCH_PACKAGE = DEFAULT_BASE / "casos/aws-carddemo-preparation/evidence/research-package.json"
MODEL = "gpt-6-astra"
BASE_URL = "https://chatgpt.com/backend-api/codex"
STAGE1_FEATURE = "pipeline-scope-carddemo"
STAGE2_FEATURE = "capability-selection-carddemo"
STAGE1_SPEC = f"specs/{STAGE1_FEATURE}/spec.json"
STAGE1_ARTIFACT = f"specs/{STAGE1_FEATURE}/requirements.md"
BLOCKED_STAGE2_TERMS = ("collection-01", "preflight", "evaluation-quarantine", "expected outcomes")


def parse_stage(value: Any) -> int:
    try:
        stage = int(str(value))
    except ValueError as exc:
        raise AdapterError("stage must be 1 or 2") from exc
    if stage not in (1, 2):
        raise AdapterError("only stages 1 and 2 are authorized by this adapter")
    return stage


class AdapterError(Exception):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def rel_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def fail(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 2


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_new(path: Path, data: Any) -> None:
    if path.exists() or path.is_symlink():
        raise AdapterError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text_new(path: Path, text: str) -> None:
    if path.exists() or path.is_symlink():
        raise AdapterError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def scrub_blocked_stage2_terms(text: str) -> str:
    scrubbed = text
    for term in BLOCKED_STAGE2_TERMS:
        scrubbed = re.sub(re.escape(term), "[withheld-stage2-input]", scrubbed, flags=re.IGNORECASE)
    return scrubbed


def rel_run_file(run_root: Path, rel: str) -> Path:
    if rel.startswith("/") or ".." in Path(rel).parts:
        raise AdapterError(f"invalid run-relative path: {rel}")
    path = run_root / rel
    if path.is_symlink() or not path.exists() or not path.is_file():
        raise AdapterError(f"required run file missing or invalid: {rel}")
    path.resolve(strict=True).relative_to(run_root.resolve(strict=False))
    return path


def run_gate_checker(run_root: Path, framework_root: Path, spec_rel: str) -> dict[str, Any]:
    checker = framework_root / "tools/check_gate.py"
    if checker.is_symlink() or not checker.exists() or not checker.is_file():
        raise AdapterError(f"gate checker missing or invalid: {checker}")
    result = subprocess.run(
        [sys.executable, str(checker), str(run_root), spec_rel],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        gate = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AdapterError(f"gate checker returned invalid JSON: {result.stderr.strip()}") from exc
    if result.returncode != 0 or gate.get("status") != "current" or gate.get("ok") is not True:
        raise AdapterError(f"upstream gate is not current: {gate.get('status')} {gate.get('reasons')}")
    return gate


def pin_run_file(run_root: Path, rel: str) -> dict[str, str]:
    path = rel_run_file(run_root, rel)
    return {"path": rel, "sha256": sha256_file(path)}


def safe_existing_root(path: Path, label: str) -> Path:
    if path.is_symlink():
        raise AdapterError(f"{label} must not be a symlink: {path}")
    if not path.exists() or not path.is_dir():
        raise AdapterError(f"{label} does not exist or is not a directory: {path}")
    return path.resolve(strict=True)


def validate_run_root(run_root: Path, allowed_parent: Path) -> Path:
    if run_root.is_symlink():
        raise AdapterError(f"RUN_ROOT must not be a symlink: {run_root}")
    allowed = allowed_parent.resolve(strict=False)
    resolved = run_root.resolve(strict=False)
    if not rel_to(resolved, allowed):
        raise AdapterError(f"RUN_ROOT must be inside allowed parent {allowed}: {run_root}")
    # Refuse symlinks only inside the explicitly authorized run subtree.
    probe = run_root
    while True:
        if probe.exists() and probe.is_symlink():
            raise AdapterError(f"RUN_ROOT path contains symlink: {probe}")
        if probe.resolve(strict=False) == allowed:
            break
        if probe.parent == probe:
            break
        probe = probe.parent
    return resolved


def validate_feature(feature: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,80}", feature):
        raise AdapterError("feature must be lowercase kebab-case")
    return feature


def validate_common(args: argparse.Namespace) -> tuple[Path, Path, Path, Path]:
    run_root = validate_run_root(Path(args.run_root), Path(args.allowed_run_parent))
    framework_root = safe_existing_root(Path(args.framework_root), "FRAMEWORK_ROOT")
    corpus_root = safe_existing_root(Path(args.corpus_root), "CORPUS_ROOT") if Path(args.corpus_root).exists() else Path(args.corpus_root).resolve(strict=False)
    package = Path(args.research_package)
    if package.is_symlink() or not package.exists() or not package.is_file():
        raise AdapterError(f"research package missing or invalid: {package}")
    package = package.resolve(strict=True)
    # Read-only roots may be outside the adapter tree, but must be the explicit supplied roots.
    return run_root, framework_root, corpus_root, package


def load_manifest(package_path: Path) -> dict[str, Any]:
    package = load_json(package_path)
    files = []
    for item in package.get("files", []):
        rel = item.get("path")
        digest = item.get("sha256")
        if not rel or rel.startswith("/") or ".." in Path(rel).parts:
            raise AdapterError(f"invalid corpus-relative path in research package: {rel!r}")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise AdapterError(f"invalid sha256 for {rel}")
        role = "source" if item.get("in_code_count") else "operational doc"
        files.append({
            "path": rel,
            "sha256": digest,
            "role": role,
            "allowed_stages": [1],
            "reason": "stage-1 inventory/hash visibility only; source bodies withheld until explicitly escalated",
            "prior_exposure": "name and hash from approved research-package inventory only",
            "physical_lines": item.get("physical_lines"),
        })
    return {
        "source_package_path": str(package_path),
        "source_package_sha256": sha256_file(package_path),
        "scope_summary": package.get("scope", "Posting, interest transaction generation and transaction reporting"),
        "visibility_policy": "stage-1-inventory-only-no-source-bodies",
        "excluded_from_extraction": package.get("exclude_from_extraction", []),
        "data_policy": package.get("data_policy"),
        "visible_inputs": files,
    }


def collect_source_bodies(corpus_root: Path, manifest: dict[str, Any]) -> list[dict[str, str]]:
    bodies = []
    for item in manifest.get("visible_inputs", []):
        rel = item["path"]
        path = corpus_root / rel
        if path.is_symlink() or not path.exists() or not path.is_file():
            raise AdapterError(f"allowlisted source body missing or invalid: {rel}")
        resolved = path.resolve(strict=True)
        resolved.relative_to(corpus_root.resolve(strict=False))
        digest = sha256_file(resolved)
        if digest != item["sha256"]:
            raise AdapterError(f"allowlisted source body hash mismatch: {rel}")
        text = resolved.read_text(encoding="utf-8")
        bodies.append({"path": rel, "sha256": digest, "role": item.get("role", "source"), "content": text})
    return bodies


def read_required(path: Path) -> str:
    if not path.exists():
        raise AdapterError(f"required framework file missing: {path}")
    return path.read_text(encoding="utf-8")


def command_spec_init(args: argparse.Namespace) -> int:
    stage = parse_stage(args.stage)
    feature = validate_feature(args.feature)
    run_root, framework_root, corpus_root, package_path = validate_common(args)
    if stage == 2:
        return command_spec_init_stage2(args, feature, run_root, framework_root, corpus_root, package_path)
    manifest = load_manifest(package_path)
    timestamp = args.timestamp or now_iso()
    spec_dir = run_root / "specs" / feature
    if spec_dir.exists() or spec_dir.is_symlink():
        raise AdapterError(f"refusing to overwrite existing spec directory: {spec_dir}")
    template_json = read_required(framework_root / "settings/templates/specs/init.json")
    req_template = read_required(framework_root / "settings/templates/specs/requirements-init.md")
    scope_template = read_required(framework_root / "settings/templates/pipeline/pipeline-scope-spec.md")
    replacements = {
        "{{FEATURE_NAME}}": feature,
        "{{ARTIFACT_TYPE}}": "pipeline-scope",
        "{{CAPABILITY}}": "unselected-stage-1-scope-only",
        "{{RUN_ID}}": args.run_id,
        "{{ARTIFACT_PATH}}": f"specs/{feature}/requirements.md",
        "{{TIMESTAMP}}": timestamp,
        "{{PROJECT_DESCRIPTION}}": args.project_description,
    }
    for old, new in replacements.items():
        template_json = template_json.replace(old, new)
        req_template = req_template.replace(old, new)
    spec = json.loads(template_json)
    spec["pipeline_stage"] = 1
    spec["artifact_type"] = "pipeline-scope"
    spec["capability"] = "unselected-stage-1-scope-only"
    spec["bridge"] = BRIDGE_NAME
    spec["roots"] = {"RUN_ROOT": str(run_root), "FRAMEWORK_ROOT": str(framework_root), "CORPUS_ROOT": str(corpus_root)}
    spec["adapted_from"] = ["/sdd:spec-init", "pipeline-sdd-v3 stage 1 Pipeline Scope Spec"]
    init_meta = {
        "bridge": BRIDGE_NAME,
        "native_slash_command": False,
        "command": "/sdd:spec-init",
        "stage": 1,
        "timestamp": timestamp,
        "run_id": args.run_id,
        "model_calls_made": False,
        "scope_template_sha256": hashlib.sha256(scope_template.encode("utf-8")).hexdigest(),
    }
    manifest.update({
        "RUN_ROOT": str(run_root),
        "FRAMEWORK_ROOT": str(framework_root),
        "CORPUS_ROOT": str(corpus_root),
        "run_id": args.run_id,
        "stage": 1,
    })
    spec_dir.mkdir(parents=True, exist_ok=False)
    write_json_new(spec_dir / "spec.json", spec)
    write_text_new(spec_dir / "requirements.md", req_template)
    write_json_new(spec_dir / "input-manifest.json", manifest)
    write_json_new(spec_dir / "init-metadata.json", init_meta)
    print(json.dumps({"created": str(spec_dir), "next": f"/sdd:spec-requirements {feature}", "bridge": BRIDGE_NAME}, ensure_ascii=False))
    return 0


def stage1_pins(run_root: Path, framework_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    gate = run_gate_checker(run_root, framework_root, STAGE1_SPEC)
    stage1_spec_path = rel_run_file(run_root, STAGE1_SPEC)
    stage1_spec = load_json(stage1_spec_path)
    review = stage1_spec.get("gate", {}).get("review", {})
    auth_pin = review.get("authorization")
    if not isinstance(auth_pin, dict) or not auth_pin.get("path"):
        raise AdapterError("approved stage 1 authorization pin missing")
    pins = {
        "upstream_specs": [pin_run_file(run_root, STAGE1_SPEC)],
        "upstream_artifacts": [pin_run_file(run_root, STAGE1_ARTIFACT)],
        "authorizations": [pin_run_file(run_root, auth_pin["path"])],
        "gate_check": gate,
    }
    return stage1_spec, pins


def stage2_current_input_pins(run_root: Path, framework_root: Path, corpus_root: Path, package_path: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]], list[dict[str, str]]]:
    stage1_spec, pins = stage1_pins(run_root, framework_root)
    manifest = load_manifest(package_path)
    source_bodies = collect_source_bodies(corpus_root, manifest)
    framework_docs = collect_framework_context(framework_root, 2)
    pins.update({
        "source_bodies": [{"path": b["path"], "sha256": b["sha256"], "role": b["role"]} for b in source_bodies],
        "framework_context": [{"path": d["path"], "sha256": d["sha256"]} for d in framework_docs],
        "source_package": {"path": str(package_path), "sha256": sha256_file(package_path)},
    })
    return stage1_spec, pins, source_bodies, framework_docs


def input_pins_digest(pins: dict[str, Any]) -> str:
    return sha256_text(json.dumps(pins, sort_keys=True, ensure_ascii=False))


def command_spec_init_stage2(args: argparse.Namespace, feature: str, run_root: Path, framework_root: Path, corpus_root: Path, package_path: Path) -> int:
    stage1_spec, pins = stage1_pins(run_root, framework_root)
    timestamp = args.timestamp or now_iso()
    spec_dir = run_root / "specs" / feature
    if spec_dir.exists() or spec_dir.is_symlink():
        raise AdapterError(f"refusing to overwrite existing spec directory: {spec_dir}")
    template_json = read_required(framework_root / "settings/templates/specs/init.json")
    req_template = read_required(framework_root / "settings/templates/specs/requirements-init.md")
    selection_template = read_required(framework_root / "settings/templates/pipeline/capability-selection-spec.md")
    replacements = {
        "{{FEATURE_NAME}}": feature,
        "{{ARTIFACT_TYPE}}": "capability-selection",
        "{{CAPABILITY}}": stage1_spec["capability"],
        "{{RUN_ID}}": args.run_id,
        "{{ARTIFACT_PATH}}": f"specs/{feature}/requirements.md",
        "{{TIMESTAMP}}": timestamp,
        "{{PROJECT_DESCRIPTION}}": "AWS CardDemo stage-2 Capability Selection Spec placeholder; generation requires /sdd:spec-requirements --stage 2",
    }
    for old, new in replacements.items():
        template_json = template_json.replace(old, new)
        req_template = req_template.replace(old, new)
    spec = json.loads(template_json)
    spec["pipeline_stage"] = 2
    spec["artifact_type"] = "capability-selection"
    spec["capability"] = stage1_spec["capability"]
    spec["operational_chain_identity_note"] = "capability is an immutable operational chain id from stage 1, not a selected business capability name"
    spec["selected_business_capability"] = None
    spec["upstream_specs"] = [STAGE1_SPEC]
    spec["bridge"] = BRIDGE_NAME
    spec["roots"] = {"RUN_ROOT": str(run_root), "FRAMEWORK_ROOT": str(framework_root), "CORPUS_ROOT": str(corpus_root)}
    spec["adapted_from"] = ["/sdd:spec-init --stage 2", "pipeline-sdd-v3 stage 2 Capability Selection Spec"]
    pins.update({
        "stage": 2,
        "run_id": args.run_id,
        "feature": feature,
        "source_package": {"path": str(package_path), "sha256": sha256_file(package_path)},
        "framework_templates": [{"path": "settings/templates/pipeline/capability-selection-spec.md", "sha256": sha256_text(selection_template)}],
    })
    init_meta = {
        "bridge": BRIDGE_NAME,
        "native_slash_command": False,
        "command": "/sdd:spec-init",
        "stage": 2,
        "timestamp": timestamp,
        "run_id": args.run_id,
        "model_calls_made": False,
        "capability_selection_template_sha256": sha256_text(selection_template),
        "upstream_specs": [STAGE1_SPEC],
    }
    spec_dir.mkdir(parents=True, exist_ok=False)
    write_json_new(spec_dir / "spec.json", spec)
    write_text_new(spec_dir / "requirements.md", req_template)
    write_json_new(spec_dir / "input-pins.json", pins)
    write_json_new(spec_dir / "init-metadata.json", init_meta)
    print(json.dumps({"created": str(spec_dir), "next": f"/sdd:spec-requirements {feature} --stage 2", "bridge": BRIDGE_NAME}, ensure_ascii=False))
    return 0


def collect_framework_context(framework_root: Path, stage: int) -> list[dict[str, str]]:
    template = "settings/templates/pipeline/pipeline-scope-spec.md" if stage == 1 else "settings/templates/pipeline/capability-selection-spec.md"
    rels = [
        "steering/pipeline.md",
        "steering/product.md",
        "steering/tech.md",
        "steering/structure.md",
        "steering/glossary.md",
        "settings/rules/run-integrity.md",
        "settings/rules/ai-assistance.md",
        "settings/rules/traceability.md",
        template,
    ]
    docs = []
    for rel in rels:
        path = framework_root / rel
        if path.exists():
            text = path.read_text(encoding="utf-8")
            docs.append({"path": rel, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "content": text})
    return docs


def build_payload(args: argparse.Namespace, run_root: Path, framework_root: Path, corpus_root: Path, package_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    stage = parse_stage(args.stage)
    feature = validate_feature(args.feature)
    spec_dir = run_root / "specs" / feature
    if not spec_dir.exists():
        raise AdapterError(f"spec-init output not found for feature: {feature}")
    spec = load_json(spec_dir / "spec.json")
    if spec.get("pipeline_stage") != stage:
        raise AdapterError("requested stage does not match spec")
    if stage == 1:
        if spec.get("artifact_type") != "pipeline-scope":
            raise AdapterError("stage 1 requires pipeline-scope artifact")
        if spec.get("gate", {}).get("completeness_gate_passed"):
            raise AdapterError("requirements bridge must not start from an already approved gate")
        manifest = load_json(spec_dir / "input-manifest.json")
        manifest_for_prompt = {
            "visibility_policy": manifest.get("visibility_policy"),
            "scope_summary": manifest.get("scope_summary"),
            "RUN_ROOT": manifest.get("RUN_ROOT"),
            "FRAMEWORK_ROOT": manifest.get("FRAMEWORK_ROOT"),
            "CORPUS_ROOT": manifest.get("CORPUS_ROOT"),
            "run_id": manifest.get("run_id"),
            "stage": manifest.get("stage"),
            "visible_inputs": manifest.get("visible_inputs", []),
        }
        framework_docs = collect_framework_context(framework_root, 1)
        prompt = {
            "bridge_notice": "This is an explicit local bridge for adapted /sdd:spec-requirements, not a native slash command.",
            "task": "Draft ONLY the Stage 1 Pipeline Scope Spec for the AWS CardDemo public cycle. Do not select a capability, do not infer capability semantics, do not design an API, and do not generate adapter behavior or validation claims.",
            "study_scope_generic": "Target area: posting, interest transaction generation, and transaction reporting under public-study restrictions.",
            "visibility_rule": "Use only visible inventory metadata: corpus-relative paths, hashes, roles, line counts, roots, and v3 framework instructions. Do not assume COBOL source bodies are provided.",
            "required_output": "Return the Pipeline Scope Spec markdown only. Human gate approval remains false and external to this response.",
            "run": {"run_id": args.run_id, "stage": 1, "feature": feature},
            "roots": {"RUN_ROOT": str(run_root), "FRAMEWORK_ROOT": str(framework_root), "CORPUS_ROOT": str(corpus_root)},
            "spec_json": spec,
            "input_manifest": manifest_for_prompt,
            "framework_context": framework_docs,
            "negative_constraints": [
                "Use only the supplied inputs; no prior answers, external context or expected outcomes.",
                "No tools, no previous_response_id, store=false, no fallback/retry, no temperature/max_output_tokens fields.",
                "Do not claim three SDD replicas; this authorization is E3-01 stage 1 only.",
            ],
        }
        instructions = "Execute only the adapted stage-1 command supplied in the user input. Return English Markdown without code fences. Do not approve the human gate."
        extra_meta: dict[str, Any] = {}
    else:
        if spec.get("artifact_type") != "capability-selection" or spec.get("upstream_specs") != [STAGE1_SPEC]:
            raise AdapterError("stage 2 requires capability-selection pinned to stage 1")
        stage1_spec, pins, source_bodies, framework_docs = stage2_current_input_pins(run_root, framework_root, corpus_root, package_path)
        input_pins_path = spec_dir / "input-pins.json"
        if input_pins_path.exists():
            recorded = load_json(input_pins_path)
            if recorded.get("upstream_specs") != pins["upstream_specs"] or recorded.get("upstream_artifacts") != pins["upstream_artifacts"]:
                raise AdapterError("stage 2 recorded input pins are stale")
        # Preserve approved inputs verbatim; exclusion policies are not leaked evaluation data.
        stage1_requirements = rel_run_file(run_root, STAGE1_ARTIFACT).read_text(encoding="utf-8")
        prompt = {
            "bridge_notice": "This is an explicit local bridge for adapted /sdd:spec-requirements --stage 2, not a native slash command.",
            "task": "Draft ONLY the Stage 2 Capability Selection Spec for the AWS CardDemo public cycle. Treat selection as low commitment and stop before evidence semantics stage 3.",
            "required_output": "Return the Capability Selection Spec markdown only. Do not approve the human gate.",
            "selection_commitment": "low-commitment candidate selection only; preserve upstream operational chain identity separately from any business capability label",
            "stage_boundary": "No legacy evidence semantics, canonical data boundary, API contract, adapter behavior, downstream interface materials, or validation/evidence-semantic claims.",
            "visibility_rule": "Use only approved stage-1 scope/metadata, generic framework/rules/template, and the allowlisted source bodies checked against research-package hashes.",
            "run": {"run_id": args.run_id, "stage": 2, "feature": feature},
            "roots": {"RUN_ROOT": str(run_root), "FRAMEWORK_ROOT": str(framework_root), "CORPUS_ROOT": str(corpus_root)},
            "spec_json": spec,
            "approved_upstream": {"spec_json": stage1_spec, "requirements_md": stage1_requirements},
            "input_pins": pins,
            "source_bodies": source_bodies,
            "framework_context": framework_docs,
            "negative_constraints": [
                "Use only the supplied inputs; no historical results, withheld operational/evaluation materials, downstream interface materials, or quarantined test data.",
                "No tools, no previous_response_id, store=false, no fallback/retry, no temperature/max_output_tokens fields.",
                "Do not infer stable capability semantics; that begins at stage 3 and is not authorized here.",
            ],
        }
        instructions = "Execute only the adapted stage-2 Capability Selection command supplied in the user input. Return English Markdown without code fences. Do not approve the human gate."
        extra_meta = {"input_pins_sha256": input_pins_digest(pins), "upstream_specs": [STAGE1_SPEC]}
    payload = {"model": MODEL, "store": False, "stream": True, "instructions": instructions, "input": [{"role": "user", "content": json.dumps(prompt, ensure_ascii=False, indent=2)}]}
    metadata = {
        "bridge": BRIDGE_NAME,
        "native_slash_command": False,
        "command": "/sdd:spec-requirements",
        "stage": stage,
        "run_id": args.run_id,
        "feature": feature,
        "model": MODEL,
        "base_url": BASE_URL,
        "execute_authorized": False,
        "prepared_at": args.timestamp or now_iso(),
        "request_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
        "framework_root": str(framework_root),
        "corpus_root": str(corpus_root),
        "research_package": str(package_path),
    }
    metadata.update(extra_meta)
    return payload, metadata


def command_spec_requirements(args: argparse.Namespace) -> int:
    stage = parse_stage(args.stage)
    run_root, framework_root, corpus_root, package_path = validate_common(args)
    feature = validate_feature(args.feature)
    prep_dir = run_root / "prepared" / feature
    if prep_dir.exists() or prep_dir.is_symlink():
        if args.execute and not prep_dir.is_symlink():
            saved = load_json(prep_dir / "request.json")
            saved_meta = load_json(prep_dir / "metadata.json")
            if saved_meta.get("stage") != stage:
                raise AdapterError("prepared stage mismatch")
            if saved_meta.get("stage") == 2:
                _, current_pins, _, _ = stage2_current_input_pins(run_root, framework_root, corpus_root, package_path)
                if saved_meta.get("input_pins_sha256") != input_pins_digest(current_pins):
                    raise AdapterError("prepared stage 2 input pins are stale")
            digest = hashlib.sha256(json.dumps(saved, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if digest != saved_meta["request_sha256"]:
                raise AdapterError("prepared hash mismatch")
            return execute_request(args, prep_dir, saved, saved_meta)
        if stage == 2:
            stage2_current_input_pins(run_root, framework_root, corpus_root, package_path)
        raise AdapterError(f"refusing to overwrite existing prepared request: {prep_dir}")
    payload, metadata = build_payload(args, run_root, framework_root, corpus_root, package_path)
    prep_dir.mkdir(parents=True, exist_ok=False)
    write_json_new(prep_dir / "request.json", payload)
    write_json_new(prep_dir / "metadata.json", metadata)
    if args.prepare_only and not args.execute:
        print(json.dumps({"prepared": str(prep_dir), "network_called": False, "bridge": BRIDGE_NAME}, ensure_ascii=False))
        return 0
    if not args.execute:
        raise AdapterError("use --prepare-only for offline payload preparation or --execute with an authorization file")
    return execute_request(args, prep_dir, payload, metadata)


def verify_execution_authorization(path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    if path is None:
        raise AdapterError("--execute requires --authorization-file")
    stage = metadata.get("stage")
    if stage not in (1, 2, 3, 4, 5, 6, 7):
        raise AdapterError("prepared stage is not executable by this adapter")
    auth = load_json(path)
    expected = {"approved": True, "stage": stage, "run_id": metadata["run_id"], "model": MODEL, "base_url": BASE_URL, "request_sha256": metadata["request_sha256"]}
    for key, value in expected.items():
        if auth.get(key) != value:
            raise AdapterError(f"authorization {key} mismatch")
    metadata["execute_authorized"] = True
    metadata["authorization_file"] = str(path)
    metadata["authorization_sha256"] = sha256_file(path)
    return auth


def execute_request(args: argparse.Namespace, prep_dir: Path, payload: dict[str, Any], metadata: dict[str, Any]) -> int:
    auth_path = Path(args.authorization_file) if args.authorization_file else None
    verify_execution_authorization(auth_path, metadata)
    sys.path.insert(0, "<REDACTED_LOCAL_PATH>/.run-cache/codex-transport")
    from codex_transport.auth import resolve_codex_runtime_credentials  # type: ignore
    import httpx  # type: ignore

    creds = resolve_codex_runtime_credentials()
    base_url = creds.get("base_url") if isinstance(creds, dict) else getattr(creds, "base_url", None)
    token = creds.get("api_key") if isinstance(creds, dict) else getattr(creds, "api_key", None)
    if base_url != BASE_URL:
        raise AdapterError(f"unexpected Codex base_url: {base_url}")
    if not token:
        raise AdapterError("missing Codex runtime token")
    result_dir = prep_dir / "execution"
    if result_dir.exists():
        raise AdapterError(f"refusing to overwrite execution directory: {result_dir}")
    result_dir.mkdir()
    write_json_new(result_dir / "request-body.json", payload)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    write_json_new(result_dir / "metadata.json", metadata)
    try:
        with httpx.stream("POST", f"{BASE_URL}/responses", headers=headers, json=payload, timeout=180, follow_redirects=False) as resp:
            metadata["http_status"] = resp.status_code
            with (result_dir / "response.sse").open("x", encoding="utf-8") as sink:
                for chunk in resp.iter_text():
                    sink.write(chunk)
                    sink.flush()
        if metadata["http_status"] != 200:
            raise AdapterError(f"HTTP {metadata['http_status']}; no retry")
        raw = (result_dir / "response.sse").read_text()
        parsed = parse_sse_result(raw)
        if parsed["model"] != MODEL or parsed["tools"] != [] or parsed["store"] is not False or parsed["previous_response_id"] is not None:
            raise AdapterError("returned model or isolation mismatch")
        write_json_new(result_dir / "parsed.json", parsed)
        write_text_new(result_dir / "scope-original.md", parsed["text"])
        metadata["status"] = "generated_pending_human_review"
    except Exception as exc:
        metadata["status"] = "blocked"
        metadata["error_type"] = type(exc).__name__
        raise
    finally:
        (result_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({"executed": str(result_dir), "status": parsed["status"], "model": parsed.get("model")}, ensure_ascii=False))
    return 0


def parse_sse_result(raw: str) -> dict[str, Any]:
    completed = None
    parts: dict[tuple[int, int], str] = {}
    for line in raw.splitlines():
        if not line.startswith("data: "):
            continue
        if line[6:] == "[DONE]":
            continue
        event = json.loads(line[6:])
        kind = event.get("type")
        if kind in ("response.failed", "response.incomplete", "error"):
            raise ValueError("Provider did not complete successfully")
        if kind == "response.output_text.done":
            key = (event.get("output_index", 0), event.get("content_index", 0))
            if key in parts and parts[key] != event["text"]:
                raise ValueError("Conflicting completed content")
            parts[key] = event["text"]
        if kind == "response.completed":
            completed = event["response"]
    if completed is None or completed.get("status") != "completed" or completed.get("error"):
        raise ValueError("Missing successful completion event")
    text = "".join(parts[k] for k in sorted(parts))
    if not text:
        text = "".join(c.get("text", "") for item in completed.get("output", []) for c in item.get("content", []) if c.get("type") == "output_text")
    if not text:
        raise ValueError("Completed without output text")
    return {
        "text": text,
        "model": completed.get("model"),
        "status": completed["status"],
        "tools": completed.get("tools"),
        "previous_response_id": completed.get("previous_response_id"),
        "store": completed.get("store"),
        "usage": completed.get("usage"),
        "temperature_observed": completed.get("temperature"),
        "top_p_observed": completed.get("top_p"),
        "reasoning_observed": completed.get("reasoning"),
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Explicit local adapter for v3 SDD stage-1 commands")
    p.add_argument("command")
    p.add_argument("feature")
    p.add_argument("--stage", default="1")
    p.add_argument("--project-description", default="AWS CardDemo public cycle stage-1 Pipeline Scope Spec")
    p.add_argument("--run-id", default="E3-01")
    p.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    p.add_argument("--allowed-run-parent", default=str(DEFAULT_RUN_PARENT))
    p.add_argument("--framework-root", default=str(DEFAULT_FRAMEWORK_ROOT))
    p.add_argument("--corpus-root", default=str(DEFAULT_CORPUS_ROOT))
    p.add_argument("--research-package", default=str(DEFAULT_RESEARCH_PACKAGE))
    p.add_argument("--timestamp")
    p.add_argument("--prepare-only", action="store_true")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--authorization-file")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if args.command == "/sdd:spec-init":
            return command_spec_init(args)
        if args.command == "/sdd:spec-requirements":
            return command_spec_requirements(args)
        raise AdapterError(f"unsupported command: {args.command}")
    except AdapterError as e:
        return fail(str(e))


if __name__ == "__main__":
    raise SystemExit(main())

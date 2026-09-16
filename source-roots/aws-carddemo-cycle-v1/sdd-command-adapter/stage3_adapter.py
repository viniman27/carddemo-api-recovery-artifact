#!/usr/bin/env python3
"""Stage-3-only local bridge for AWS CardDemo Legacy Evidence SDD commands."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import adapter
from adapter import AdapterError

STAGE3_FEATURE = "legacy-evidence-carddemo"
STAGE2_R2_FEATURE = "capability-selection-carddemo-r2"
STAGE2_R2_SPEC = f"specs/{STAGE2_R2_FEATURE}/spec.json"
STAGE2_R2_ARTIFACT = f"specs/{STAGE2_R2_FEATURE}/requirements.md"
STAGE3_TEMPLATE = "settings/templates/pipeline/legacy-evidence-spec.md"
MANDATORY_TRACKS = ["posting", "interest", "reporting"]


def parse_stage3(value: Any) -> int:
    try:
        stage = int(str(value))
    except ValueError as exc:
        raise AdapterError("stage3 adapter accepts only --stage 3") from exc
    if stage != 3:
        raise AdapterError("stage3 adapter accepts only --stage 3")
    return stage


def read_framework_doc(framework_root: Path, rel: str) -> dict[str, str]:
    path = framework_root / rel
    if path.is_symlink() or not path.exists() or not path.is_file():
        raise AdapterError(f"required framework file missing or invalid: {rel}")
    text = path.read_text(encoding="utf-8")
    return {"path": rel, "sha256": adapter.sha256_text(text), "content": text}


def collect_stage3_framework_context(framework_root: Path) -> list[dict[str, str]]:
    rels = [
        "steering/pipeline.md",
        "steering/product.md",
        "steering/tech.md",
        "steering/structure.md",
        "steering/glossary.md",
        "settings/rules/run-integrity.md",
        "settings/rules/ai-assistance.md",
        "settings/rules/traceability.md",
        STAGE3_TEMPLATE,
    ]
    return [read_framework_doc(framework_root, rel) for rel in rels if (framework_root / rel).exists()]


def numbered_lines(text: str) -> str:
    lines = text.splitlines()
    if text.endswith("\n"):
        # splitlines intentionally drops the terminal empty record; preserve only source lines.
        pass
    return "\n".join(f"{i}: {line}" for i, line in enumerate(lines, 1))


def collect_stage3_corpus(corpus_root: Path, package_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = adapter.load_manifest(package_path)
    bodies = adapter.collect_source_bodies(corpus_root, manifest)
    prepared = []
    for body in bodies:
        numbered = numbered_lines(body["content"])
        prepared.append({
            "path": body["path"],
            "sha256": body["sha256"],
            "role": body.get("role", "source"),
            "line_count": len(body["content"].splitlines()),
            "citation_anchor_format": f"{body['path']}:start-end",
            "content": body["content"],
            "numbered_lines": numbered,
            "derived_representation": "stable 1-based line numbering of exact UTF-8 source text; source content is otherwise unmodified",
            "derived_representation_sha256": adapter.sha256_text(numbered),
            "source_sha256": body["sha256"],
        })
    return manifest, prepared


def stage3_current_input_pins(run_root: Path, framework_root: Path, corpus_root: Path, package_path: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    gate = adapter.run_gate_checker(run_root, framework_root, STAGE2_R2_SPEC)
    stage2_spec_path = adapter.rel_run_file(run_root, STAGE2_R2_SPEC)
    stage2_spec = adapter.load_json(stage2_spec_path)
    if stage2_spec.get("pipeline_stage") != 2 or stage2_spec.get("artifact_type") != "capability-selection":
        raise AdapterError("stage3 requires approved stage2-r2 capability-selection upstream")
    review = stage2_spec.get("gate", {}).get("review", {})
    auth_pin = review.get("authorization")
    if not isinstance(auth_pin, dict) or not auth_pin.get("path"):
        raise AdapterError("approved stage2-r2 authorization pin missing")
    upstream_review_specs = review.get("upstream_specs", [])
    if upstream_review_specs != [{"path": adapter.STAGE1_SPEC, "sha256": adapter.sha256_file(adapter.rel_run_file(run_root, adapter.STAGE1_SPEC))}]:
        raise AdapterError("stage2-r2 upstream stage1 pin is missing or stale")
    stage1_spec, stage1_pins = adapter.stage1_pins(run_root, framework_root)
    manifest, source_bodies = collect_stage3_corpus(corpus_root, package_path)
    framework_docs = collect_stage3_framework_context(framework_root)
    pins = {
        "stage": 3,
        "upstream_specs": stage1_pins["upstream_specs"] + [adapter.pin_run_file(run_root, STAGE2_R2_SPEC)],
        "upstream_artifacts": stage1_pins["upstream_artifacts"] + [adapter.pin_run_file(run_root, STAGE2_R2_ARTIFACT)],
        "authorizations": stage1_pins["authorizations"] + [adapter.pin_run_file(run_root, auth_pin["path"])],
        "gate_check": gate,
        "source_package": {"path": str(package_path), "sha256": adapter.sha256_file(package_path)},
        "source_bodies": [{"path": b["path"], "sha256": b["sha256"], "role": b["role"], "derived_representation_sha256": b["derived_representation_sha256"]} for b in source_bodies],
        "framework_context": [{"path": d["path"], "sha256": d["sha256"]} for d in framework_docs],
        "mandatory_tracks": MANDATORY_TRACKS,
    }
    upstream = {
        "stage1_spec_json": stage1_spec,
        "stage1_requirements_md": adapter.rel_run_file(run_root, adapter.STAGE1_ARTIFACT).read_text(encoding="utf-8"),
        "stage2_r2_spec_json": stage2_spec,
        "stage2_r2_requirements_md": adapter.rel_run_file(run_root, STAGE2_R2_ARTIFACT).read_text(encoding="utf-8"),
        "stage2_r2_authorization": adapter.load_json(adapter.rel_run_file(run_root, auth_pin["path"])),
    }
    return upstream, pins, source_bodies, framework_docs


def command_spec_init(args: argparse.Namespace) -> int:
    parse_stage3(args.stage)
    feature = adapter.validate_feature(args.feature)
    if feature != STAGE3_FEATURE:
        raise AdapterError(f"stage3 adapter accepts only feature {STAGE3_FEATURE}")
    run_root, framework_root, corpus_root, package_path = adapter.validate_common(args)
    upstream, pins, _, _ = stage3_current_input_pins(run_root, framework_root, corpus_root, package_path)
    timestamp = args.timestamp or adapter.now_iso()
    spec_dir = run_root / "specs" / feature
    if spec_dir.exists() or spec_dir.is_symlink():
        raise AdapterError(f"refusing to overwrite existing spec directory: {spec_dir}")
    template_json = adapter.read_required(framework_root / "settings/templates/specs/init.json")
    req_template = adapter.read_required(framework_root / "settings/templates/specs/requirements-init.md")
    replacements = {
        "{{FEATURE_NAME}}": feature,
        "{{ARTIFACT_TYPE}}": "legacy-evidence",
        "{{CAPABILITY}}": upstream["stage2_r2_spec_json"]["capability"],
        "{{RUN_ID}}": args.run_id,
        "{{ARTIFACT_PATH}}": f"specs/{feature}/requirements.md",
        "{{TIMESTAMP}}": timestamp,
        "{{PROJECT_DESCRIPTION}}": "AWS CardDemo stage-3 Legacy Evidence Spec placeholder for posting, interest and reporting documentary evidence only",
    }
    for old, new in replacements.items():
        template_json = template_json.replace(old, new)
        req_template = req_template.replace(old, new)
    spec = json.loads(template_json)
    spec["pipeline_stage"] = 3
    spec["artifact_type"] = "legacy-evidence"
    spec["capability"] = upstream["stage2_r2_spec_json"]["capability"]
    spec["mandatory_tracks"] = MANDATORY_TRACKS
    spec["upstream_specs"] = [STAGE2_R2_SPEC]
    spec["bridge"] = adapter.BRIDGE_NAME + ":stage3"
    spec["roots"] = {"RUN_ROOT": str(run_root), "FRAMEWORK_ROOT": str(framework_root), "CORPUS_ROOT": str(corpus_root)}
    spec["adapted_from"] = ["/sdd:spec-init --stage 3", "pipeline-sdd-v3 stage 3 Legacy Evidence Spec"]
    init_meta = {"bridge": spec["bridge"], "native_slash_command": False, "command": "/sdd:spec-init", "stage": 3, "timestamp": timestamp, "run_id": args.run_id, "model_calls_made": False, "input_pins_sha256": adapter.input_pins_digest(pins)}
    spec_dir.mkdir(parents=True, exist_ok=False)
    adapter.write_json_new(spec_dir / "spec.json", spec)
    adapter.write_text_new(spec_dir / "requirements.md", req_template)
    adapter.write_json_new(spec_dir / "input-pins.json", pins)
    adapter.write_json_new(spec_dir / "init-metadata.json", init_meta)
    print(json.dumps({"created": str(spec_dir), "next": f"/sdd:spec-requirements {feature} --stage 3", "bridge": spec["bridge"]}, ensure_ascii=False))
    return 0


def build_payload(args: argparse.Namespace, run_root: Path, framework_root: Path, corpus_root: Path, package_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    parse_stage3(args.stage)
    feature = adapter.validate_feature(args.feature)
    spec_dir = run_root / "specs" / feature
    if not spec_dir.exists():
        raise AdapterError(f"spec-init output not found for feature: {feature}")
    spec = adapter.load_json(spec_dir / "spec.json")
    if spec.get("pipeline_stage") != 3 or spec.get("artifact_type") != "legacy-evidence" or spec.get("upstream_specs") != [STAGE2_R2_SPEC]:
        raise AdapterError("stage3 requires legacy-evidence spec pinned to stage2-r2")
    upstream, pins, source_bodies, framework_docs = stage3_current_input_pins(run_root, framework_root, corpus_root, package_path)
    recorded = adapter.load_json(spec_dir / "input-pins.json") if (spec_dir / "input-pins.json").exists() else None
    if recorded and adapter.input_pins_digest(recorded) != adapter.input_pins_digest(pins):
        raise AdapterError("stage3 recorded input pins are stale")
    prompt = {
        "bridge_notice": "This is an explicit local bridge for adapted /sdd:spec-requirements --stage 3, not a native slash command.",
        "task": "Draft ONLY the Stage 3 Legacy Evidence Specification as documentary evidence for the AWS CardDemo public cycle.",
        "required_scope": {"mandatory_tracks": MANDATORY_TRACKS, "coverage_rule": "All three tracks are mandatory and must remain separately traceable: posting, interest, reporting."},
        "required_output": "Return one requirements.md Legacy Evidence Specification only. Human approval remains false and external. Do not produce semantic reconstruction, API claims, adapter behavior, validation results, or later-stage artifacts.",
        "evidence_rules": [
            "Use globally unique E-n IDs carrying track(s), full corpus-relative path, file SHA-256 and stable numbered source lines with line range.",
            "Use only approved upstream docs, this authorization, generic v3 framework/template/rules and exact allowlisted corpus bodies.",
            "Preserve framework and upstream text verbatim; do not scrub words merely naming excluded material.",
            "No evaluation quarantine, preflight results, E1/E2 outputs, prior rejected stage2 response, COBOL execution, human approval, semantic reconstruction or API claims.",
        ],
        "run": {"run_id": args.run_id, "stage": 3, "feature": feature},
        "roots": {"RUN_ROOT": str(run_root), "FRAMEWORK_ROOT": str(framework_root), "CORPUS_ROOT": str(corpus_root)},
        "spec_json": spec,
        "approved_upstream": upstream,
        "input_pins": pins,
        "source_bodies": source_bodies,
        "framework_context": framework_docs,
    }
    instructions = "Execute only the adapted stage-3 Legacy Evidence command supplied in the user input. Return English Markdown without code fences. Do not approve any gate."
    payload = {"model": adapter.MODEL, "store": False, "stream": True, "instructions": instructions, "input": [{"role": "user", "content": json.dumps(prompt, ensure_ascii=False, indent=2)}]}
    metadata = {
        "bridge": adapter.BRIDGE_NAME + ":stage3",
        "native_slash_command": False,
        "command": "/sdd:spec-requirements",
        "stage": 3,
        "run_id": args.run_id,
        "feature": feature,
        "model": adapter.MODEL,
        "base_url": adapter.BASE_URL,
        "execute_authorized": False,
        "prepared_at": args.timestamp or adapter.now_iso(),
        "request_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
        "input_pins_sha256": adapter.input_pins_digest(pins),
        "upstream_specs": [STAGE2_R2_SPEC],
        "framework_root": str(framework_root),
        "corpus_root": str(corpus_root),
        "research_package": str(package_path),
    }
    return payload, metadata


def command_spec_requirements(args: argparse.Namespace) -> int:
    parse_stage3(args.stage)
    run_root, framework_root, corpus_root, package_path = adapter.validate_common(args)
    feature = adapter.validate_feature(args.feature)
    if feature != STAGE3_FEATURE:
        raise AdapterError(f"stage3 adapter accepts only feature {STAGE3_FEATURE}")
    prep_dir = run_root / "prepared" / feature
    if prep_dir.exists() or prep_dir.is_symlink():
        if args.execute and not prep_dir.is_symlink():
            saved = adapter.load_json(prep_dir / "request.json")
            saved_meta = adapter.load_json(prep_dir / "metadata.json")
            if saved_meta.get("stage") != 3:
                raise AdapterError("prepared stage mismatch")
            _, current_pins, _, _ = stage3_current_input_pins(run_root, framework_root, corpus_root, package_path)
            if saved_meta.get("input_pins_sha256") != adapter.input_pins_digest(current_pins):
                raise AdapterError("prepared stage3 input pins are stale")
            digest = hashlib.sha256(json.dumps(saved, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if digest != saved_meta["request_sha256"]:
                raise AdapterError("prepared hash mismatch")
            return adapter.execute_request(args, prep_dir, saved, saved_meta)
        stage3_current_input_pins(run_root, framework_root, corpus_root, package_path)
        raise AdapterError(f"refusing to overwrite existing prepared request: {prep_dir}")
    payload, metadata = build_payload(args, run_root, framework_root, corpus_root, package_path)
    prep_dir.mkdir(parents=True, exist_ok=False)
    adapter.write_json_new(prep_dir / "request.json", payload)
    adapter.write_json_new(prep_dir / "metadata.json", metadata)
    if args.prepare_only and not args.execute:
        print(json.dumps({"prepared": str(prep_dir), "network_called": False, "bridge": metadata["bridge"]}, ensure_ascii=False))
        return 0
    if not args.execute:
        raise AdapterError("use --prepare-only for offline payload preparation or --execute with an authorization file")
    return adapter.execute_request(args, prep_dir, payload, metadata)


def build_parser() -> argparse.ArgumentParser:
    p = adapter.build_parser()
    p.description = "Explicit local adapter for v3 SDD stage-3 commands only"
    p.set_defaults(stage="3")
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
        return adapter.fail(str(e))


if __name__ == "__main__":
    raise SystemExit(main())

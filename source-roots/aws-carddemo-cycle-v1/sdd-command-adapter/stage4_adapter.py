#!/usr/bin/env python3
"""Stage-4-only local bridge for AWS CardDemo Capability Semantics SDD commands."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import adapter
import stage3_adapter
from adapter import AdapterError

STAGE4_FEATURE = "capability-semantics-carddemo"
STAGE3_R2_FEATURE = "legacy-evidence-carddemo-r2"
STAGE3_R2_SPEC = f"specs/{STAGE3_R2_FEATURE}/spec.json"
STAGE3_R2_ARTIFACT = f"specs/{STAGE3_R2_FEATURE}/requirements.md"
STAGE4_TEMPLATE = "settings/templates/pipeline/capability-semantics-spec.md"
MANDATORY_TRACKS = ["posting", "interest", "reporting"]


def parse_stage4(value: Any) -> int:
    try:
        stage = int(str(value))
    except ValueError as exc:
        raise AdapterError("stage4 adapter accepts only --stage 4") from exc
    if stage != 4:
        raise AdapterError("stage4 adapter accepts only --stage 4")
    return stage


def read_framework_doc(framework_root: Path, rel: str) -> dict[str, str]:
    path = framework_root / rel
    if path.is_symlink() or not path.exists() or not path.is_file():
        raise AdapterError(f"required framework file missing or invalid: {rel}")
    text = path.read_text(encoding="utf-8")
    return {"path": rel, "sha256": adapter.sha256_text(text), "content": text}


def collect_stage4_framework_context(framework_root: Path) -> list[dict[str, str]]:
    rels = [
        "steering/pipeline.md",
        "steering/product.md",
        "steering/tech.md",
        "steering/structure.md",
        "steering/glossary.md",
        "settings/rules/run-integrity.md",
        "settings/rules/ai-assistance.md",
        "settings/rules/traceability.md",
        STAGE4_TEMPLATE,
    ]
    return [read_framework_doc(framework_root, rel) for rel in rels if (framework_root / rel).exists()]


def stage4_current_input_pins(run_root: Path, framework_root: Path, corpus_root: Path, package_path: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    gate = adapter.run_gate_checker(run_root, framework_root, STAGE3_R2_SPEC)
    stage3_spec_path = adapter.rel_run_file(run_root, STAGE3_R2_SPEC)
    stage3_spec = adapter.load_json(stage3_spec_path)
    if stage3_spec.get("pipeline_stage") != 3 or stage3_spec.get("artifact_type") != "legacy-evidence":
        raise AdapterError("stage4 requires approved stage3-r2 legacy-evidence upstream")
    if stage3_spec.get("mandatory_tracks") != MANDATORY_TRACKS:
        raise AdapterError("stage3-r2 must preserve posting, interest and reporting tracks")
    if stage3_spec.get("upstream_specs") != [stage3_adapter.STAGE2_R2_SPEC]:
        raise AdapterError("stage3-r2 upstream stage2-r2 pin is missing")
    review = stage3_spec.get("gate", {}).get("review", {})
    auth_pin = review.get("authorization")
    if not isinstance(auth_pin, dict) or not auth_pin.get("path"):
        raise AdapterError("approved stage3-r2 authorization pin missing")
    stage2_pin = {"path": stage3_adapter.STAGE2_R2_SPEC, "sha256": adapter.sha256_file(adapter.rel_run_file(run_root, stage3_adapter.STAGE2_R2_SPEC))}
    if review.get("upstream_specs", []) != [stage2_pin]:
        raise AdapterError("stage3-r2 upstream stage2-r2 pin is missing or stale")

    upstream12, pins12, source_bodies, _ = stage3_adapter.stage3_current_input_pins(run_root, framework_root, corpus_root, package_path)
    framework_docs = collect_stage4_framework_context(framework_root)
    stage3_auth_path = adapter.rel_run_file(run_root, auth_pin["path"])
    pins = {
        "stage": 4,
        "upstream_specs": pins12["upstream_specs"] + [adapter.pin_run_file(run_root, STAGE3_R2_SPEC)],
        "upstream_artifacts": pins12["upstream_artifacts"] + [adapter.pin_run_file(run_root, STAGE3_R2_ARTIFACT)],
        "authorizations": pins12["authorizations"] + [adapter.pin_run_file(run_root, auth_pin["path"])],
        "gate_check": gate,
        "source_package": {"path": str(package_path), "sha256": adapter.sha256_file(package_path)},
        "source_bodies": [{"path": b["path"], "sha256": b["sha256"], "role": b["role"], "derived_representation_sha256": b["derived_representation_sha256"]} for b in source_bodies],
        "framework_context": [{"path": d["path"], "sha256": d["sha256"]} for d in framework_docs],
        "mandatory_tracks": MANDATORY_TRACKS,
    }
    upstream = dict(upstream12)
    upstream.update({
        "stage3_r2_spec_json": stage3_spec,
        "stage3_r2_requirements_md": adapter.rel_run_file(run_root, STAGE3_R2_ARTIFACT).read_text(encoding="utf-8"),
        "stage3_r2_authorization": adapter.load_json(stage3_auth_path),
    })
    return upstream, pins, source_bodies, framework_docs


def command_spec_init(args: argparse.Namespace) -> int:
    parse_stage4(args.stage)
    feature = adapter.validate_feature(args.feature)
    if feature != STAGE4_FEATURE:
        raise AdapterError(f"stage4 adapter accepts only feature {STAGE4_FEATURE}")
    run_root, framework_root, corpus_root, package_path = adapter.validate_common(args)
    upstream, pins, _, _ = stage4_current_input_pins(run_root, framework_root, corpus_root, package_path)
    timestamp = args.timestamp or adapter.now_iso()
    spec_dir = run_root / "specs" / feature
    if spec_dir.exists() or spec_dir.is_symlink():
        raise AdapterError(f"refusing to overwrite existing spec directory: {spec_dir}")
    template_json = adapter.read_required(framework_root / "settings/templates/specs/init.json")
    req_template = adapter.read_required(framework_root / "settings/templates/specs/requirements-init.md")
    replacements = {
        "{{FEATURE_NAME}}": feature,
        "{{ARTIFACT_TYPE}}": "capability-semantics",
        "{{CAPABILITY}}": upstream["stage3_r2_spec_json"]["capability"],
        "{{RUN_ID}}": args.run_id,
        "{{ARTIFACT_PATH}}": f"specs/{feature}/requirements.md",
        "{{TIMESTAMP}}": timestamp,
        "{{PROJECT_DESCRIPTION}}": "AWS CardDemo stage-4 Capability Semantics Spec placeholder for posting, interest and reporting semantics only",
    }
    for old, new in replacements.items():
        template_json = template_json.replace(old, new)
        req_template = req_template.replace(old, new)
    spec = json.loads(template_json)
    spec["pipeline_stage"] = 4
    spec["artifact_type"] = "capability-semantics"
    spec["capability"] = upstream["stage3_r2_spec_json"]["capability"]
    spec["mandatory_tracks"] = MANDATORY_TRACKS
    spec["upstream_specs"] = [STAGE3_R2_SPEC]
    spec["bridge"] = adapter.BRIDGE_NAME + ":stage4"
    spec["roots"] = {"RUN_ROOT": str(run_root), "FRAMEWORK_ROOT": str(framework_root), "CORPUS_ROOT": str(corpus_root)}
    spec["adapted_from"] = ["/sdd:spec-init --stage 4", "pipeline-sdd-v3 stage 4 Capability Semantics Spec"]
    init_meta = {"bridge": spec["bridge"], "native_slash_command": False, "command": "/sdd:spec-init", "stage": 4, "timestamp": timestamp, "run_id": args.run_id, "model_calls_made": False, "input_pins_sha256": adapter.input_pins_digest(pins)}
    spec_dir.mkdir(parents=True, exist_ok=False)
    adapter.write_json_new(spec_dir / "spec.json", spec)
    adapter.write_text_new(spec_dir / "requirements.md", req_template)
    adapter.write_json_new(spec_dir / "input-pins.json", pins)
    adapter.write_json_new(spec_dir / "init-metadata.json", init_meta)
    print(json.dumps({"created": str(spec_dir), "next": f"/sdd:spec-requirements {feature} --stage 4", "bridge": spec["bridge"]}, ensure_ascii=False))
    return 0


def build_payload(args: argparse.Namespace, run_root: Path, framework_root: Path, corpus_root: Path, package_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    parse_stage4(args.stage)
    feature = adapter.validate_feature(args.feature)
    spec_dir = run_root / "specs" / feature
    if not spec_dir.exists():
        raise AdapterError(f"spec-init output not found for feature: {feature}")
    spec = adapter.load_json(spec_dir / "spec.json")
    if spec.get("pipeline_stage") != 4 or spec.get("artifact_type") != "capability-semantics" or spec.get("upstream_specs") != [STAGE3_R2_SPEC]:
        raise AdapterError("stage4 requires capability-semantics spec pinned to stage3-r2")
    upstream, pins, source_bodies, framework_docs = stage4_current_input_pins(run_root, framework_root, corpus_root, package_path)
    recorded = adapter.load_json(spec_dir / "input-pins.json") if (spec_dir / "input-pins.json").exists() else None
    if recorded and adapter.input_pins_digest(recorded) != adapter.input_pins_digest(pins):
        raise AdapterError("stage4 recorded input pins are stale")
    prompt = {
        "bridge_notice": "This is an explicit local bridge for adapted /sdd:spec-requirements --stage 4, not a native slash command.",
        "task": "Draft ONLY the Stage 4 Capability Semantics Specification for the AWS CardDemo public cycle from approved stage3-r2 evidence.",
        "required_scope": {"mandatory_tracks": MANDATORY_TRACKS, "coverage_rule": "Posting, interest, and reporting are all mandatory and must remain separately traceable tracks; do not replace the inherited upstream capability identity with a portfolio label."},
        "required_output": "Return one requirements.md Capability Semantics Specification only. It must use unique semantic rule IDs that trace to stage3 E-n evidence IDs and include a reverse completeness mapping from every used stage3 E-n evidence item to semantic coverage or justified unresolved status.",
        "semantic_rules": [
            "Keep semantic rule IDs globally unique within the artifact and trace every rule to one or more stage3 E-n entries.",
            "Maintain separate posting, interest, and reporting tracks; do not collapse them into one generic capability.",
            "Preserve unresolved runtime/configuration limits: no assumed durable partial effects, EOF buffer state, date configuration, external routines, or invented desired behavior.",
            "Use only approved stages 1, 2-r2, 3-r2, their authorization files, exact source text with numbered lines/derived hashes, the actual v3 capability-semantics template, relevant generic rules, the source package, and allowlisted corpus files.",
            "Preserve generic exclusion-policy text verbatim; do not word-scrub it merely because it names excluded materials.",
        ],
        "negative_constraints": [
            "No canonical data boundary, API contract, stage5 or later material, COBOL execution, code fixes, quarantine data, E1/E2 outputs, preparation outputs, or invented behavior.",
            "Do not claim APIs, durable effects, modern adapter behavior, validation results, or downstream implementation readiness.",
            "No tools, no previous_response_id, store=false, no fallback/retry, no temperature/max_output_tokens fields.",
        ],
        "run": {"run_id": args.run_id, "stage": 4, "feature": feature},
        "roots": {"RUN_ROOT": str(run_root), "FRAMEWORK_ROOT": str(framework_root), "CORPUS_ROOT": str(corpus_root)},
        "spec_json": spec,
        "approved_upstream": upstream,
        "input_pins": pins,
        "source_bodies": source_bodies,
        "framework_context": framework_docs,
    }
    instructions = "Execute only the adapted stage-4 Capability Semantics command supplied in the user input. Return English Markdown without code fences. Do not approve any gate."
    payload = {"model": adapter.MODEL, "store": False, "stream": True, "instructions": instructions, "input": [{"role": "user", "content": json.dumps(prompt, ensure_ascii=False, indent=2)}]}
    metadata = {
        "bridge": adapter.BRIDGE_NAME + ":stage4",
        "native_slash_command": False,
        "command": "/sdd:spec-requirements",
        "stage": 4,
        "run_id": args.run_id,
        "feature": feature,
        "model": adapter.MODEL,
        "base_url": adapter.BASE_URL,
        "execute_authorized": False,
        "prepared_at": args.timestamp or adapter.now_iso(),
        "request_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
        "input_pins_sha256": adapter.input_pins_digest(pins),
        "upstream_specs": [STAGE3_R2_SPEC],
        "framework_root": str(framework_root),
        "corpus_root": str(corpus_root),
        "research_package": str(package_path),
    }
    return payload, metadata


def command_spec_requirements(args: argparse.Namespace) -> int:
    parse_stage4(args.stage)
    run_root, framework_root, corpus_root, package_path = adapter.validate_common(args)
    feature = adapter.validate_feature(args.feature)
    if feature != STAGE4_FEATURE:
        raise AdapterError(f"stage4 adapter accepts only feature {STAGE4_FEATURE}")
    prep_dir = run_root / "prepared" / feature
    if prep_dir.exists() or prep_dir.is_symlink():
        if args.execute and not prep_dir.is_symlink():
            saved = adapter.load_json(prep_dir / "request.json")
            saved_meta = adapter.load_json(prep_dir / "metadata.json")
            if saved_meta.get("stage") != 4:
                raise AdapterError("prepared stage mismatch")
            _, current_pins, _, _ = stage4_current_input_pins(run_root, framework_root, corpus_root, package_path)
            if saved_meta.get("input_pins_sha256") != adapter.input_pins_digest(current_pins):
                raise AdapterError("prepared stage4 input pins are stale")
            digest = hashlib.sha256(json.dumps(saved, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if digest != saved_meta["request_sha256"]:
                raise AdapterError("prepared hash mismatch")
            return adapter.execute_request(args, prep_dir, saved, saved_meta)
        stage4_current_input_pins(run_root, framework_root, corpus_root, package_path)
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
    p.description = "Explicit local adapter for v3 SDD stage-4 commands only"
    p.set_defaults(stage="4")
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

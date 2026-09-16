#!/usr/bin/env python3
"""Stage-5-only local bridge for AWS CardDemo Canonical Data Boundary SDD commands."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import adapter
import stage4_adapter
from adapter import AdapterError

STAGE5_FEATURE = "canonical-data-boundary-carddemo"
STAGE4_FEATURE = stage4_adapter.STAGE4_FEATURE
STAGE4_SPEC = f"specs/{STAGE4_FEATURE}/spec.json"
STAGE4_ARTIFACT = f"specs/{STAGE4_FEATURE}/requirements.md"
STAGE5_TEMPLATE = "settings/templates/pipeline/canonical-data-boundary-spec.md"
STAGE4_COUNTEREXAMPLE_REVIEW = "reviews/STAGE4-COUNTEREXAMPLE-REVIEW.md"
MANDATORY_TRACKS = ["posting", "interest", "reporting"]
EXPECTED_STAGE4_RULE_IDS = [f"R-{i}" for i in range(1, 21)]


def parse_stage5(value: Any) -> int:
    try:
        stage = int(str(value))
    except ValueError as exc:
        raise AdapterError("stage5 adapter accepts only --stage 5") from exc
    if stage != 5:
        raise AdapterError("stage5 adapter accepts only --stage 5")
    return stage


def read_framework_doc(framework_root: Path, rel: str) -> dict[str, str]:
    return stage4_adapter.read_framework_doc(framework_root, rel)


def collect_stage5_framework_context(framework_root: Path) -> list[dict[str, str]]:
    rels = [
        "steering/pipeline.md",
        "steering/product.md",
        "steering/tech.md",
        "steering/structure.md",
        "steering/glossary.md",
        "settings/rules/run-integrity.md",
        "settings/rules/ai-assistance.md",
        "settings/rules/traceability.md",
        "settings/rules/ambiguity-management.md",
        "settings/rules/legacy-code-policy.md",
        "settings/rules/validation-principles.md",
        STAGE5_TEMPLATE,
    ]
    return [read_framework_doc(framework_root, rel) for rel in rels if (framework_root / rel).exists()]


def _attachment_pins_from(value: Any) -> list[dict[str, str]]:
    pins: list[dict[str, str]] = []
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
            pins.append({"path": value["path"], "sha256": value["sha256"]})
        for key in ("attachments", "review_attachments", "attachment_pins", "source_grounded_counterexample_review", "review_reference"):
            pins.extend(_attachment_pins_from(value.get(key)))
    elif isinstance(value, list):
        for item in value:
            pins.extend(_attachment_pins_from(item))
    return pins


def require_stage4_counterexample_review_pin(run_root: Path, stage4_spec: dict[str, Any], stage4_auth: dict[str, Any]) -> tuple[dict[str, str], str]:
    candidates = _attachment_pins_from(stage4_spec.get("gate", {}).get("review", {})) + _attachment_pins_from(stage4_auth)
    expected = [pin for pin in candidates if pin.get("path") in (STAGE4_COUNTEREXAMPLE_REVIEW, "STAGE4-COUNTEREXAMPLE-REVIEW.md") or pin.get("path", "").endswith("/STAGE4-COUNTEREXAMPLE-REVIEW.md")]
    if not expected:
        raise AdapterError("approved stage4 source-grounded counterexample review attachment pin missing")
    pin = expected[0]
    actual = adapter.pin_run_file(run_root, pin["path"])
    if actual["sha256"] != pin["sha256"]:
        raise AdapterError("stage4 counterexample review attachment pin is stale")
    text = adapter.rel_run_file(run_root, pin["path"]).read_text(encoding="utf-8")
    return actual, text


def stage5_current_input_pins(run_root: Path, framework_root: Path, corpus_root: Path, package_path: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    gate = adapter.run_gate_checker(run_root, framework_root, STAGE4_SPEC)
    stage4_spec_path = adapter.rel_run_file(run_root, STAGE4_SPEC)
    stage4_spec = adapter.load_json(stage4_spec_path)
    if stage4_spec.get("pipeline_stage") != 4 or stage4_spec.get("artifact_type") != "capability-semantics":
        raise AdapterError("stage5 requires approved stage4 capability-semantics upstream")
    if stage4_spec.get("mandatory_tracks") != MANDATORY_TRACKS:
        raise AdapterError("stage4 must preserve posting, interest and reporting tracks")
    if stage4_spec.get("upstream_specs") != [stage4_adapter.STAGE3_R2_SPEC]:
        raise AdapterError("stage4 upstream stage3-r2 pin is missing")
    review = stage4_spec.get("gate", {}).get("review", {})
    auth_pin = review.get("authorization")
    if not isinstance(auth_pin, dict) or not auth_pin.get("path"):
        raise AdapterError("approved stage4 authorization pin missing")
    expected_stage3_pin = {"path": stage4_adapter.STAGE3_R2_SPEC, "sha256": adapter.sha256_file(adapter.rel_run_file(run_root, stage4_adapter.STAGE3_R2_SPEC))}
    if review.get("upstream_specs", []) != [expected_stage3_pin]:
        raise AdapterError("stage4 upstream stage3-r2 pin is missing or stale")

    upstream14, pins14, source_bodies, _ = stage4_adapter.stage4_current_input_pins(run_root, framework_root, corpus_root, package_path)
    framework_docs = collect_stage5_framework_context(framework_root)
    stage4_auth_path = adapter.rel_run_file(run_root, auth_pin["path"])
    stage4_auth = adapter.load_json(stage4_auth_path)
    attachment_pin, attachment_text = require_stage4_counterexample_review_pin(run_root, stage4_spec, stage4_auth)
    stage4_requirements = adapter.rel_run_file(run_root, STAGE4_ARTIFACT).read_text(encoding="utf-8")
    missing_rules = [rid for rid in EXPECTED_STAGE4_RULE_IDS if not re.search(rf"(?<![A-Za-z0-9-]){re.escape(rid)}(?![0-9-])", stage4_requirements)]
    if missing_rules:
        raise AdapterError(f"stage4 requirements missing mandatory R-1..R-20 rule ids: {', '.join(missing_rules)}")

    pins = {
        "stage": 5,
        "upstream_specs": pins14["upstream_specs"] + [adapter.pin_run_file(run_root, STAGE4_SPEC)],
        "upstream_artifacts": pins14["upstream_artifacts"] + [adapter.pin_run_file(run_root, STAGE4_ARTIFACT)],
        "authorizations": pins14["authorizations"] + [adapter.pin_run_file(run_root, auth_pin["path"])],
        "review_attachments": [attachment_pin],
        "gate_check": gate,
        "source_package": {"path": str(package_path), "sha256": adapter.sha256_file(package_path)},
        "source_bodies": [{"path": b["path"], "sha256": b["sha256"], "role": b["role"], "derived_representation_sha256": b["derived_representation_sha256"]} for b in source_bodies],
        "framework_context": [{"path": d["path"], "sha256": d["sha256"]} for d in framework_docs],
        "mandatory_tracks": MANDATORY_TRACKS,
        "expected_real_corpus_file_count": 19,
        "actual_corpus_file_count": len(source_bodies),
        "stage4_rule_ids": EXPECTED_STAGE4_RULE_IDS,
    }
    upstream = dict(upstream14)
    upstream.update({
        "stage4_spec_json": stage4_spec,
        "stage4_requirements_md": stage4_requirements,
        "stage4_authorization": stage4_auth,
        "stage4_counterexample_review_md": attachment_text,
        "stage4_counterexample_review_pin": attachment_pin,
    })
    return upstream, pins, source_bodies, framework_docs


def command_spec_init(args: argparse.Namespace) -> int:
    parse_stage5(args.stage)
    feature = adapter.validate_feature(args.feature)
    if feature != STAGE5_FEATURE:
        raise AdapterError(f"stage5 adapter accepts only feature {STAGE5_FEATURE}")
    run_root, framework_root, corpus_root, package_path = adapter.validate_common(args)
    upstream, pins, _, _ = stage5_current_input_pins(run_root, framework_root, corpus_root, package_path)
    timestamp = args.timestamp or adapter.now_iso()
    spec_dir = run_root / "specs" / feature
    if spec_dir.exists() or spec_dir.is_symlink():
        raise AdapterError(f"refusing to overwrite existing spec directory: {spec_dir}")
    template_json = adapter.read_required(framework_root / "settings/templates/specs/init.json")
    req_template = adapter.read_required(framework_root / "settings/templates/specs/requirements-init.md")
    replacements = {
        "{{FEATURE_NAME}}": feature,
        "{{ARTIFACT_TYPE}}": "canonical-data-boundary",
        "{{CAPABILITY}}": upstream["stage4_spec_json"]["capability"],
        "{{RUN_ID}}": args.run_id,
        "{{ARTIFACT_PATH}}": f"specs/{feature}/requirements.md",
        "{{TIMESTAMP}}": timestamp,
        "{{PROJECT_DESCRIPTION}}": "AWS CardDemo stage-5 Canonical Data Boundary Spec placeholder for posting, interest and reporting boundaries only",
    }
    for old, new in replacements.items():
        template_json = template_json.replace(old, new)
        req_template = req_template.replace(old, new)
    spec = json.loads(template_json)
    spec["pipeline_stage"] = 5
    spec["artifact_type"] = "canonical-data-boundary"
    spec["capability"] = upstream["stage4_spec_json"]["capability"]
    spec["mandatory_tracks"] = MANDATORY_TRACKS
    spec["upstream_specs"] = [STAGE4_SPEC]
    spec["bridge"] = adapter.BRIDGE_NAME + ":stage5"
    spec["roots"] = {"RUN_ROOT": str(run_root), "FRAMEWORK_ROOT": str(framework_root), "CORPUS_ROOT": str(corpus_root)}
    spec["adapted_from"] = ["/sdd:spec-init --stage 5", "pipeline-sdd-v3 stage 5 Canonical Data Boundary Spec"]
    init_meta = {"bridge": spec["bridge"], "native_slash_command": False, "command": "/sdd:spec-init", "stage": 5, "timestamp": timestamp, "run_id": args.run_id, "model_calls_made": False, "input_pins_sha256": adapter.input_pins_digest(pins)}
    spec_dir.mkdir(parents=True, exist_ok=False)
    adapter.write_json_new(spec_dir / "spec.json", spec)
    adapter.write_text_new(spec_dir / "requirements.md", req_template)
    adapter.write_json_new(spec_dir / "input-pins.json", pins)
    adapter.write_json_new(spec_dir / "init-metadata.json", init_meta)
    print(json.dumps({"created": str(spec_dir), "next": f"/sdd:spec-requirements {feature} --stage 5", "bridge": spec["bridge"]}, ensure_ascii=False))
    return 0


def build_payload(args: argparse.Namespace, run_root: Path, framework_root: Path, corpus_root: Path, package_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    parse_stage5(args.stage)
    feature = adapter.validate_feature(args.feature)
    spec_dir = run_root / "specs" / feature
    if not spec_dir.exists():
        raise AdapterError(f"spec-init output not found for feature: {feature}")
    spec = adapter.load_json(spec_dir / "spec.json")
    if spec.get("pipeline_stage") != 5 or spec.get("artifact_type") != "canonical-data-boundary" or spec.get("upstream_specs") != [STAGE4_SPEC]:
        raise AdapterError("stage5 requires canonical-data-boundary spec pinned to stage4")
    upstream, pins, source_bodies, framework_docs = stage5_current_input_pins(run_root, framework_root, corpus_root, package_path)
    recorded = adapter.load_json(spec_dir / "input-pins.json") if (spec_dir / "input-pins.json").exists() else None
    if recorded and adapter.input_pins_digest(recorded) != adapter.input_pins_digest(pins):
        raise AdapterError("stage5 recorded input pins are stale")
    prompt = {
        "bridge_notice": "This is an explicit local bridge for adapted /sdd:spec-requirements --stage 5, not a native slash command.",
        "task": "Draft ONLY the Stage 5 Canonical Data Boundary Specification for the AWS CardDemo public cycle from approved stage4 capability semantics; do not execute anything and do not approve any gate.",
        "required_scope": {"mandatory_tracks": MANDATORY_TRACKS, "coverage_rule": "Posting, interest, and reporting are all mandatory and must remain separately traceable tracks; inherit the exact upstream capability identity without renaming it."},
        "required_tracks": [
            {"name": "conceptual data boundary", "requirement": "Identify technology-neutral canonical data meanings, state scope, outcome variants and boundary decisions only when licensed by stage4 R-n rules."},
            {"name": "source-to-canonical mapping/provenance", "requirement": "Map every canonical element or exclusion to stage4 R-n and source evidence provenance; retain exact corpus bodies and stable numbered representations."},
            {"name": "explicit unresolved gaps", "requirement": "Preserve every underdetermined runtime/configuration limit or semantic gap as unresolved; do not repair source behavior or invent missing policy."},
        ],
        "required_output": "Return one requirements.md Canonical Data Boundary Specification only, following the supplied generic canonical-data-boundary-spec template/rules. It must trace each boundary decision to stage4 R-n and keep reverse completeness from all R-1..R-20 to disposition.",
        "boundary_rules": [
            "Keep conceptual data boundary, source-to-canonical mapping/provenance, and explicit unresolved gaps as separate mandatory tracks; do not force identical entities across tracks.",
            "Trace each boundary decision, canonical element, state treatment, exclusion, ambiguity or gap to one or more stage4 R-n rules.",
            "Maintain reverse completeness for every R-1..R-20: canonicalized, internal-only, excluded, ambiguous, unresolved gap, or not applicable with justification.",
            "Use approved stages 1, 2-r2, 3-r2 and 4 current versions, all original byte pins, authorizations, the stage4 source-grounded counterexample review attachment, exact source text, stable numbered line representations, the source package, and the actual generic canonical-data-boundary-spec template/rules.",
            "Preserve missing runtime/configuration limits as unresolved where stage4 left them unresolved.",
        ],
        "negative_constraints": [
            "No model/network calls during prepare-only; no execution, no COBOL runs, no source repairs, no generated code and no gate approval.",
            "No invented currency units, rate units, cardinality rules, numeric precision/rounding policy, date policy, persistence policy, retry/idempotency policy, or validation policy not licensed by stage4.",
            "No endpoint names, HTTP methods, status codes, OpenAPI schemas, route shapes, serialization formats, authentication, pagination, or stage6 decisions.",
            "No API contract, adapter behavior, stage6 or later material; do not claim downstream implementation readiness.",
            "No tools, no previous_response_id, store=false, no fallback/retry, no temperature/max_output_tokens fields.",
        ],
        "run": {"run_id": args.run_id, "stage": 5, "feature": feature},
        "roots": {"RUN_ROOT": str(run_root), "FRAMEWORK_ROOT": str(framework_root), "CORPUS_ROOT": str(corpus_root)},
        "spec_json": spec,
        "approved_upstream": upstream,
        "input_pins": pins,
        "source_bodies": source_bodies,
        "framework_context": framework_docs,
    }
    instructions = "Execute only the adapted stage-5 Canonical Data Boundary command supplied in the user input. Return English Markdown without code fences. Do not approve any gate."
    payload = {"model": adapter.MODEL, "store": False, "stream": True, "instructions": instructions, "input": [{"role": "user", "content": json.dumps(prompt, ensure_ascii=False, indent=2)}]}
    metadata = {
        "bridge": adapter.BRIDGE_NAME + ":stage5",
        "native_slash_command": False,
        "command": "/sdd:spec-requirements",
        "stage": 5,
        "run_id": args.run_id,
        "feature": feature,
        "model": adapter.MODEL,
        "base_url": adapter.BASE_URL,
        "execute_authorized": False,
        "prepared_at": args.timestamp or adapter.now_iso(),
        "request_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
        "input_pins_sha256": adapter.input_pins_digest(pins),
        "upstream_specs": [STAGE4_SPEC],
        "framework_root": str(framework_root),
        "corpus_root": str(corpus_root),
        "research_package": str(package_path),
    }
    return payload, metadata


def command_spec_requirements(args: argparse.Namespace) -> int:
    parse_stage5(args.stage)
    run_root, framework_root, corpus_root, package_path = adapter.validate_common(args)
    feature = adapter.validate_feature(args.feature)
    if feature != STAGE5_FEATURE:
        raise AdapterError(f"stage5 adapter accepts only feature {STAGE5_FEATURE}")
    prep_dir = run_root / "prepared" / feature
    if prep_dir.exists() or prep_dir.is_symlink():
        if args.execute and not prep_dir.is_symlink():
            saved = adapter.load_json(prep_dir / "request.json")
            saved_meta = adapter.load_json(prep_dir / "metadata.json")
            if saved_meta.get("stage") != 5:
                raise AdapterError("prepared stage mismatch")
            _, current_pins, _, _ = stage5_current_input_pins(run_root, framework_root, corpus_root, package_path)
            if saved_meta.get("input_pins_sha256") != adapter.input_pins_digest(current_pins):
                raise AdapterError("prepared stage5 input pins are stale")
            digest = hashlib.sha256(json.dumps(saved, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if digest != saved_meta["request_sha256"]:
                raise AdapterError("prepared hash mismatch")
            return adapter.execute_request(args, prep_dir, saved, saved_meta)
        stage5_current_input_pins(run_root, framework_root, corpus_root, package_path)
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
    p.description = "Explicit local adapter for v3 SDD stage-5 commands only"
    p.set_defaults(stage="5")
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

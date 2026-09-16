#!/usr/bin/env python3
"""Stage-6-only local bridge for AWS CardDemo API Contract SDD commands."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import adapter
import stage5_adapter
from adapter import AdapterError

STAGE6_FEATURE = "api-contract-carddemo"
STAGE6_REVISION_FEATURE = "api-contract-carddemo-r2"
STAGE6_R3_FEATURE = "api-contract-carddemo-r3"
STAGE6_ACCEPTED_FEATURES = (STAGE6_FEATURE, STAGE6_REVISION_FEATURE, STAGE6_R3_FEATURE)
STAGE5_FEATURE = stage5_adapter.STAGE5_FEATURE
STAGE5_SPEC = f"specs/{STAGE5_FEATURE}/spec.json"
STAGE5_ARTIFACT = f"specs/{STAGE5_FEATURE}/requirements.md"
STAGE6_TEMPLATE = "settings/templates/pipeline/api-contract-spec.md"
MANDATORY_TRACKS = ["posting", "interest", "reporting"]
EXPECTED_STAGE5_RULE_IDS = [f"R-{i}" for i in range(1, 21)]
EXPECTED_STAGE5_DECISIONS = [f"D-{i}" for i in range(2, 9)]
EXPECTED_REAL_CORPUS_FILE_COUNT = 19
ORIGINAL_STAGE6_SPEC = f"specs/{STAGE6_FEATURE}/spec.json"
ORIGINAL_STAGE6_ARTIFACT = f"specs/{STAGE6_FEATURE}/requirements.md"
ORIGINAL_STAGE6_EXECUTION_OUTPUT = f"prepared/{STAGE6_FEATURE}/execution/scope-original.md"
STAGE6_DIRECTED_FEEDBACK = "reviews/stage-6-r1-directed-feedback.md"
STAGE6_REVISION_PLAN = "STAGE6-REVISION-PLAN.md"
EXPECTED_ORIGINAL_STAGE6_ARTIFACT_SHA256 = "753a60a5ee7b1fb6d94f6ab982afe415bc01adca040bb3d89e24ffc60342bba7"
EXPECTED_STAGE6_DIRECTED_FEEDBACK_SHA256 = "87a74e6570babd2e5e811ba1c0a6f0ee2d5cd0bdfbe4bdbb5504e3e9bfe4659c"
EXPECTED_STAGE6_REVISION_PLAN_SHA256 = "51ce5a1a13ab107b5c6f0df536c371e3337ad79275da0377021c273598a59c35"
R2_STAGE6_SPEC = f"specs/{STAGE6_REVISION_FEATURE}/spec.json"
R2_STAGE6_ARTIFACT = f"specs/{STAGE6_REVISION_FEATURE}/requirements.md"
R2_STAGE6_EXECUTION_OUTPUT = f"prepared/{STAGE6_REVISION_FEATURE}/execution/scope-original.md"
R2_STAGE6_REQUEST = f"prepared/{STAGE6_REVISION_FEATURE}/request.json"
R2_STAGE6_METADATA = f"prepared/{STAGE6_REVISION_FEATURE}/metadata.json"
R2_STAGE6_AUTHORIZATION = "stage6-r2-generation-authorization.json"
R2_EMPTY_REVIEW = "STAGE6-R2-INPUTS-EMPTY-REVIEW.md"
R2_DIRECTED_FEEDBACK = "reviews/stage-6-r2-directed-feedback.md"
EXPECTED_R2_STAGE6_SPEC_SHA256 = "3dd7c64774f75c3155b2e9941f139ca593401887555fd7d7917874c6bc591b54"
EXPECTED_R2_STAGE6_ARTIFACT_SHA256 = "163d1d0455f2524e8100e1722b78f255fbca7a4bda1a5caccb45e05fbe362567"
EXPECTED_R2_STAGE6_REQUEST_SHA256 = "a829f772cf621c352c7c45f250fc576241ed4388e8e758ecbb1d16e43201c66a"
EXPECTED_R2_STAGE6_METADATA_SHA256 = "83c3179bf2950e8767b9a31cb9ca15bb3256db487239abd11d97337d8403073b"
EXPECTED_R2_STAGE6_AUTHORIZATION_SHA256 = "990a9d325cc3dfb66e58eb767523de9c4c79361170d48c437724df50faba511f"
EXPECTED_R2_EMPTY_REVIEW_SHA256 = "f670185483e1310f5a9313a75db5d4866bc4cc6c0b9d742b48831bf53d0ac9ec"
EXPECTED_R2_DIRECTED_FEEDBACK_SHA256 = "17f274900d9efc7bf41fcbbc523130d3d3896a5195e81ee2e29fcc72491ccdd8"


def parse_stage6(value: Any) -> int:
    try:
        stage = int(str(value))
    except ValueError as exc:
        raise AdapterError("stage6 adapter accepts only --stage 6") from exc
    if stage != 6:
        raise AdapterError("stage6 adapter accepts only --stage 6")
    return stage


def read_framework_doc(framework_root: Path, rel: str) -> dict[str, str]:
    return stage5_adapter.read_framework_doc(framework_root, rel)


def collect_stage6_framework_context(framework_root: Path) -> list[dict[str, str]]:
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
        "settings/rules/ears-format.md",
        STAGE6_TEMPLATE,
    ]
    return [read_framework_doc(framework_root, rel) for rel in rels if (framework_root / rel).exists()]


def _attachment_pins_from(value: Any) -> list[dict[str, str]]:
    pins: list[dict[str, str]] = []
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
            pins.append({"path": value["path"], "sha256": value["sha256"]})
        for key in (
            "attachments", "review_attachments", "attachment_pins",
            "source_grounded_counterexample_review", "review_reference", "findings_reference",
        ):
            pins.extend(_attachment_pins_from(value.get(key)))
    elif isinstance(value, list):
        for item in value:
            pins.extend(_attachment_pins_from(item))
    return pins


def _select_attachment(candidates: list[dict[str, str]], names: tuple[str, ...], missing_msg: str, stale_msg: str, run_root: Path) -> tuple[dict[str, str], str]:
    matches = [pin for pin in candidates if any(pin.get("path") == name or pin.get("path", "").endswith("/" + name) for name in names)]
    if not matches:
        raise AdapterError(missing_msg)
    pin = matches[0]
    actual = adapter.pin_run_file(run_root, pin["path"])
    if actual["sha256"] != pin["sha256"]:
        raise AdapterError(stale_msg)
    text = adapter.rel_run_file(run_root, pin["path"]).read_text(encoding="utf-8")
    return actual, text


def require_stage5_review_attachment_pins(run_root: Path, stage5_spec: dict[str, Any], stage5_auth: dict[str, Any]) -> tuple[list[dict[str, str]], str, dict[str, Any]]:
    candidates = _attachment_pins_from(stage5_spec.get("gate", {}).get("review", {})) + _attachment_pins_from(stage5_auth)
    review_pin, review_text = _select_attachment(
        candidates,
        ("STAGE5-COUNTEREXAMPLE-REVIEW.md",),
        "approved stage5 counterexample review attachment pin missing",
        "stage5 counterexample review attachment pin is stale",
        run_root,
    )
    findings_pin, findings_text = _select_attachment(
        candidates,
        ("stage5-counterexample-findings.json",),
        "approved stage5 counterexample findings attachment pin missing",
        "stage5 counterexample findings attachment pin is stale",
        run_root,
    )
    try:
        findings = json.loads(findings_text)
    except json.JSONDecodeError as exc:
        raise AdapterError("stage5 counterexample findings attachment is not JSON") from exc
    return [review_pin, findings_pin], review_text, findings


def _require_tokens(text: str, tokens: list[str], message: str) -> None:
    missing = [token for token in tokens if not re.search(rf"(?<![A-Za-z0-9-]){re.escape(token)}(?![0-9-])", text)]
    if missing:
        raise AdapterError(f"{message}: {', '.join(missing)}")


def _require_stage5_coverage(stage5_requirements: str) -> None:
    lowered = stage5_requirements.lower()
    missing_tracks = [track for track in MANDATORY_TRACKS if track not in lowered]
    if missing_tracks:
        raise AdapterError(f"stage5 requirements missing mandatory tracks: {', '.join(missing_tracks)}")
    _require_tokens(stage5_requirements, EXPECTED_STAGE5_RULE_IDS, "stage5 requirements missing mandatory R-1..R-20 rule ids")
    _require_tokens(stage5_requirements, EXPECTED_STAGE5_DECISIONS, "stage5 requirements missing expected D-2..D-8 decision ids")
    for token in ("type", "field", "outcome"):
        if token not in lowered:
            raise AdapterError(f"stage5 requirements missing {token} traceability")


def _require_pin_exact(run_root: Path, pin: Any, expected_path: str, message: str) -> None:
    if not isinstance(pin, dict) or pin.get("path") != expected_path or not isinstance(pin.get("sha256"), str):
        raise AdapterError(message)
    actual = adapter.pin_run_file(run_root, expected_path)
    if pin["sha256"] != actual["sha256"]:
        raise AdapterError(message)


def validate_stage5_authorization(run_root: Path, stage5_auth: dict[str, Any], run_id: str | None = None) -> None:
    decision = stage5_auth.get("decision")
    if decision == "reject":
        raise AdapterError("stage5 authorization decision rejects stage6")
    if decision != "approve" and stage5_auth.get("approved") is not True:
        raise AdapterError("stage5 authorization is not approved")
    if "stage" in stage5_auth and stage5_auth.get("stage") != 5:
        raise AdapterError("stage5 authorization stage mismatch")
    if run_id is not None and "run_id" in stage5_auth and stage5_auth.get("run_id") != run_id:
        raise AdapterError("stage5 authorization run_id mismatch")
    _require_pin_exact(run_root, stage5_auth.get("artifact"), STAGE5_ARTIFACT, "stage5 authorization artifact pin missing or stale")
    _require_pin_exact(run_root, stage5_auth.get("review_reference"), "STAGE5-COUNTEREXAMPLE-REVIEW.md", "stage5 authorization review reference missing or stale")
    _require_pin_exact(run_root, stage5_auth.get("findings_reference"), "stage5-counterexample-findings.json", "stage5 authorization findings reference missing or stale")


def stage6_current_input_pins(run_root: Path, framework_root: Path, corpus_root: Path, package_path: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    gate = adapter.run_gate_checker(run_root, framework_root, STAGE5_SPEC)
    stage5_spec_path = adapter.rel_run_file(run_root, STAGE5_SPEC)
    stage5_spec = adapter.load_json(stage5_spec_path)
    if stage5_spec.get("pipeline_stage") != 5 or stage5_spec.get("artifact_type") != "canonical-data-boundary":
        raise AdapterError("stage6 requires approved stage5 canonical-data-boundary upstream")
    if stage5_spec.get("mandatory_tracks") != MANDATORY_TRACKS:
        raise AdapterError("stage5 must preserve posting, interest and reporting tracks")
    if stage5_spec.get("upstream_specs") != [stage5_adapter.STAGE4_SPEC]:
        raise AdapterError("stage5 upstream stage4 pin is missing")
    review = stage5_spec.get("gate", {}).get("review", {})
    auth_pin = review.get("authorization")
    if not isinstance(auth_pin, dict) or not auth_pin.get("path"):
        raise AdapterError("approved stage5 authorization pin missing")
    expected_stage4_pin = {"path": stage5_adapter.STAGE4_SPEC, "sha256": adapter.sha256_file(adapter.rel_run_file(run_root, stage5_adapter.STAGE4_SPEC))}
    if review.get("upstream_specs", []) != [expected_stage4_pin]:
        raise AdapterError("stage5 upstream stage4 pin is missing or stale")

    upstream15, pins15, source_bodies, _ = stage5_adapter.stage5_current_input_pins(run_root, framework_root, corpus_root, package_path)
    if len(source_bodies) != EXPECTED_REAL_CORPUS_FILE_COUNT:
        raise AdapterError(f"stage6 requires exact real corpus retention: expected {EXPECTED_REAL_CORPUS_FILE_COUNT}, got {len(source_bodies)}")
    framework_docs = collect_stage6_framework_context(framework_root)
    stage5_auth_path = adapter.rel_run_file(run_root, auth_pin["path"])
    stage5_auth = adapter.load_json(stage5_auth_path)
    validate_stage5_authorization(run_root, stage5_auth, stage5_spec.get("run_id"))
    attachment_pins, review_text, findings_json = require_stage5_review_attachment_pins(run_root, stage5_spec, stage5_auth)
    stage5_requirements = adapter.rel_run_file(run_root, STAGE5_ARTIFACT).read_text(encoding="utf-8")
    _require_stage5_coverage(stage5_requirements)

    pins = {
        "stage": 6,
        "upstream_specs": pins15["upstream_specs"] + [adapter.pin_run_file(run_root, STAGE5_SPEC)],
        "upstream_artifacts": pins15["upstream_artifacts"] + [adapter.pin_run_file(run_root, STAGE5_ARTIFACT)],
        "authorizations": pins15["authorizations"] + [adapter.pin_run_file(run_root, auth_pin["path"])],
        "review_attachments": pins15.get("review_attachments", []) + attachment_pins,
        "gate_check": gate,
        "source_package": {"path": str(package_path), "sha256": adapter.sha256_file(package_path)},
        "source_bodies": [{"path": b["path"], "sha256": b["sha256"], "role": b["role"], "derived_representation_sha256": b["derived_representation_sha256"]} for b in source_bodies],
        "framework_context": [{"path": d["path"], "sha256": d["sha256"]} for d in framework_docs],
        "mandatory_tracks": MANDATORY_TRACKS,
        "expected_real_corpus_file_count": 19,
        "actual_corpus_file_count": len(source_bodies),
        "stage5_rule_ids": EXPECTED_STAGE5_RULE_IDS,
        "stage5_decision_ids": EXPECTED_STAGE5_DECISIONS,
    }
    upstream = dict(upstream15)
    upstream.update({
        "stage5_spec_json": stage5_spec,
        "stage5_requirements_md": stage5_requirements,
        "stage5_authorization": stage5_auth,
        "stage5_counterexample_review_md": review_text,
        "stage5_counterexample_findings_json": findings_json,
        "stage5_review_attachment_pins": attachment_pins,
    })
    return upstream, pins, source_bodies, framework_docs


def require_stage6_revision_inputs(run_root: Path) -> tuple[dict[str, Any], dict[str, Any], str, str, str]:
    original_spec = adapter.load_json(adapter.rel_run_file(run_root, ORIGINAL_STAGE6_SPEC))
    if original_spec.get("pipeline_stage") != 6 or original_spec.get("artifact_type") != "api-contract":
        raise AdapterError("original stage6 artifact has wrong stage or artifact type")
    if original_spec.get("feature_name") not in (None, STAGE6_FEATURE):
        raise AdapterError("original stage6 feature identity mismatch")
    if original_spec.get("upstream_specs") != [STAGE5_SPEC]:
        raise AdapterError("original stage6 must remain pinned to approved stage5")
    approvals = original_spec.get("approvals", {}).get("requirements", {})
    if approvals.get("approved") is True or original_spec.get("gate", {}).get("completeness_gate_passed") is True:
        raise AdapterError("original stage6 must remain unapproved for revision")
    original_artifact_pin = adapter.pin_run_file(run_root, ORIGINAL_STAGE6_ARTIFACT)
    if original_artifact_pin["sha256"] != EXPECTED_ORIGINAL_STAGE6_ARTIFACT_SHA256:
        raise AdapterError("original stage6 requirements sha mismatch")
    original_output_pin = adapter.pin_run_file(run_root, ORIGINAL_STAGE6_EXECUTION_OUTPUT)
    if original_output_pin["sha256"] != EXPECTED_ORIGINAL_STAGE6_ARTIFACT_SHA256:
        raise AdapterError("original stage6 execution output sha mismatch")
    original_text = adapter.rel_run_file(run_root, ORIGINAL_STAGE6_ARTIFACT).read_text(encoding="utf-8")
    output_text = adapter.rel_run_file(run_root, ORIGINAL_STAGE6_EXECUTION_OUTPUT).read_text(encoding="utf-8")
    if output_text != original_text:
        raise AdapterError("original stage6 materialized artifact differs from execution output")
    feedback_pin = adapter.pin_run_file(run_root, STAGE6_DIRECTED_FEEDBACK)
    if feedback_pin["sha256"] != EXPECTED_STAGE6_DIRECTED_FEEDBACK_SHA256:
        raise AdapterError("stage6 directed feedback sha mismatch")
    plan_pin = adapter.pin_run_file(run_root, STAGE6_REVISION_PLAN)
    if plan_pin["sha256"] != EXPECTED_STAGE6_REVISION_PLAN_SHA256:
        raise AdapterError("stage6 revision plan sha mismatch")
    feedback_text = adapter.rel_run_file(run_root, STAGE6_DIRECTED_FEEDBACK).read_text(encoding="utf-8")
    plan_text = adapter.rel_run_file(run_root, STAGE6_REVISION_PLAN).read_text(encoding="utf-8")
    for token in ("G-21", "G-22", "G-23", "G-24"):
        if token not in original_text or token not in feedback_text:
            raise AdapterError(f"stage6 revision input missing required gap token: {token}")
    return original_spec, {
        "original_spec": adapter.pin_run_file(run_root, ORIGINAL_STAGE6_SPEC),
        "original_artifact": original_artifact_pin,
        "original_execution_output": original_output_pin,
        "directed_feedback": feedback_pin,
        "revision_plan": plan_pin,
    }, original_text, feedback_text, plan_text


def _pin_expected_run_file(run_root: Path, rel: str, expected_sha256: str, message: str) -> dict[str, str]:
    pin = adapter.pin_run_file(run_root, rel)
    if pin["sha256"] != expected_sha256:
        raise AdapterError(message)
    return pin


def require_stage6_r3_revision_inputs(run_root: Path) -> tuple[dict[str, Any], dict[str, dict[str, str]], str, str, str]:
    r2_spec_pin = _pin_expected_run_file(run_root, R2_STAGE6_SPEC, EXPECTED_R2_STAGE6_SPEC_SHA256, "stage6 r2 spec sha mismatch")
    r2_spec = adapter.load_json(adapter.rel_run_file(run_root, R2_STAGE6_SPEC))
    if r2_spec.get("pipeline_stage") != 6 or r2_spec.get("artifact_type") != "api-contract":
        raise AdapterError("stage6 r2 artifact has wrong stage or artifact type")
    if r2_spec.get("feature_name") not in (None, STAGE6_REVISION_FEATURE):
        raise AdapterError("stage6 r2 feature identity mismatch")
    if r2_spec.get("upstream_specs") != [STAGE5_SPEC]:
        raise AdapterError("stage6 r2 must remain pinned to approved stage5")
    approvals = r2_spec.get("approvals", {}).get("requirements", {})
    if approvals.get("approved") is True or r2_spec.get("gate", {}).get("completeness_gate_passed") is True or r2_spec.get("ready_for_implementation") is True:
        raise AdapterError("stage6 r2 must remain unapproved for r3 revision")
    r2_artifact_pin = _pin_expected_run_file(run_root, R2_STAGE6_ARTIFACT, EXPECTED_R2_STAGE6_ARTIFACT_SHA256, "stage6 r2 requirements sha mismatch")
    r2_output_pin = _pin_expected_run_file(run_root, R2_STAGE6_EXECUTION_OUTPUT, EXPECTED_R2_STAGE6_ARTIFACT_SHA256, "stage6 r2 execution output sha mismatch")
    r2_text = adapter.rel_run_file(run_root, R2_STAGE6_ARTIFACT).read_text(encoding="utf-8")
    r2_output_text = adapter.rel_run_file(run_root, R2_STAGE6_EXECUTION_OUTPUT).read_text(encoding="utf-8")
    if r2_output_text != r2_text:
        raise AdapterError("stage6 r2 materialized artifact differs from execution output")
    r2_request_pin = _pin_expected_run_file(run_root, R2_STAGE6_REQUEST, EXPECTED_R2_STAGE6_REQUEST_SHA256, "stage6 r2 prepared request sha mismatch")
    r2_metadata_pin = _pin_expected_run_file(run_root, R2_STAGE6_METADATA, EXPECTED_R2_STAGE6_METADATA_SHA256, "stage6 r2 prepared metadata sha mismatch")
    r2_auth_pin = _pin_expected_run_file(run_root, R2_STAGE6_AUTHORIZATION, EXPECTED_R2_STAGE6_AUTHORIZATION_SHA256, "stage6 r2 authorization sha mismatch")
    r2_meta = adapter.load_json(adapter.rel_run_file(run_root, R2_STAGE6_METADATA))
    r2_auth = adapter.load_json(adapter.rel_run_file(run_root, R2_STAGE6_AUTHORIZATION))
    if r2_meta.get("stage") != 6 or r2_meta.get("feature") != STAGE6_REVISION_FEATURE:
        raise AdapterError("stage6 r2 prepared metadata identity mismatch")
    if r2_auth.get("stage") != 6 or r2_auth.get("run_id") != r2_spec.get("run_id") or r2_auth.get("approved") is not True:
        raise AdapterError("stage6 r2 authorization identity mismatch")
    if r2_auth.get("request_sha256") != r2_meta.get("request_sha256"):
        raise AdapterError("stage6 r2 authorization request hash mismatch")
    review_pin = _pin_expected_run_file(run_root, R2_EMPTY_REVIEW, EXPECTED_R2_EMPTY_REVIEW_SHA256, "stage6 r2 empty review sha mismatch")
    feedback_pin = _pin_expected_run_file(run_root, R2_DIRECTED_FEEDBACK, EXPECTED_R2_DIRECTED_FEEDBACK_SHA256, "stage6 r2 directed feedback sha mismatch")
    review_text = adapter.rel_run_file(run_root, R2_EMPTY_REVIEW).read_text(encoding="utf-8")
    feedback_text = adapter.rel_run_file(run_root, R2_DIRECTED_FEEDBACK).read_text(encoding="utf-8")
    required_tokens = ["available", "items", "unavailable", "503", "r3", "Stage"]
    for token in required_tokens:
        if token not in review_text and token not in feedback_text:
            raise AdapterError(f"stage6 r3 revision input missing required token: {token}")
    return r2_spec, {
        "r2_spec": r2_spec_pin,
        "r2_artifact": r2_artifact_pin,
        "r2_execution_output": r2_output_pin,
        "r2_request": r2_request_pin,
        "r2_metadata": r2_metadata_pin,
        "r2_authorization": r2_auth_pin,
        "r2_empty_review": review_pin,
        "r2_directed_feedback": feedback_pin,
    }, r2_text, review_text, feedback_text


def command_spec_init(args: argparse.Namespace) -> int:
    parse_stage6(args.stage)
    feature = adapter.validate_feature(args.feature)
    if feature not in STAGE6_ACCEPTED_FEATURES:
        raise AdapterError(f"stage6 adapter accepts only features {', '.join(STAGE6_ACCEPTED_FEATURES)}")
    run_root, framework_root, corpus_root, package_path = adapter.validate_common(args)
    upstream, pins, _, _ = stage6_current_input_pins(run_root, framework_root, corpus_root, package_path)
    revision = None
    if feature == STAGE6_REVISION_FEATURE:
        revision = require_stage6_revision_inputs(run_root)
        original_spec, revision_pins, _, _, _ = revision
        if original_spec.get("capability") != upstream["stage5_spec_json"].get("capability"):
            raise AdapterError("stage6 revision capability mismatch with approved stage5")
    if feature == STAGE6_R3_FEATURE:
        revision = require_stage6_r3_revision_inputs(run_root)
        r2_spec, _, _, _, _ = revision
        if r2_spec.get("capability") != upstream["stage5_spec_json"].get("capability"):
            raise AdapterError("stage6 r3 revision capability mismatch with approved stage5")
    timestamp = args.timestamp or adapter.now_iso()
    spec_dir = run_root / "specs" / feature
    if spec_dir.exists() or spec_dir.is_symlink():
        raise AdapterError(f"refusing to overwrite existing spec directory: {spec_dir}")
    template_json = adapter.read_required(framework_root / "settings/templates/specs/init.json")
    req_template = adapter.read_required(framework_root / "settings/templates/specs/requirements-init.md")
    replacements = {
        "{{FEATURE_NAME}}": feature,
        "{{ARTIFACT_TYPE}}": "api-contract",
        "{{CAPABILITY}}": upstream["stage5_spec_json"]["capability"],
        "{{RUN_ID}}": args.run_id,
        "{{ARTIFACT_PATH}}": f"specs/{feature}/requirements.md",
        "{{TIMESTAMP}}": timestamp,
        "{{PROJECT_DESCRIPTION}}": "AWS CardDemo stage-6 API Contract Spec placeholder for posting, interest and reporting API contract only",
    }
    for old, new in replacements.items():
        template_json = template_json.replace(old, new)
        req_template = req_template.replace(old, new)
    spec = json.loads(template_json)
    spec["pipeline_stage"] = 6
    spec["artifact_type"] = "api-contract"
    spec["capability"] = upstream["stage5_spec_json"]["capability"]
    spec["mandatory_tracks"] = MANDATORY_TRACKS
    spec["upstream_specs"] = [STAGE5_SPEC]
    spec["bridge"] = adapter.BRIDGE_NAME + ":stage6"
    if feature == STAGE6_REVISION_FEATURE:
        spec["revision_of"] = STAGE6_FEATURE
        spec["revision_basis"] = "failed-original-stage6-plus-directed-feedback-and-plan"
        spec.setdefault("approvals", {}).setdefault("requirements", {})["approved"] = False
    if feature == STAGE6_R3_FEATURE:
        spec["revision_of"] = STAGE6_REVISION_FEATURE
        spec["revision_basis"] = "failed-stage6-r2-plus-empty-output-review-and-directed-feedback"
        spec["ready_for_implementation"] = False
        spec.setdefault("approvals", {}).setdefault("requirements", {})["approved"] = False
    spec["roots"] = {"RUN_ROOT": str(run_root), "FRAMEWORK_ROOT": str(framework_root), "CORPUS_ROOT": str(corpus_root)}
    spec["adapted_from"] = ["/sdd:spec-init --stage 6", "pipeline-sdd-v3 stage 6 API Contract Spec"]
    if revision is not None:
        _, revision_pins, _, _, _ = revision
        if feature == STAGE6_REVISION_FEATURE:
            pins["failed_original_stage6"] = [revision_pins["original_spec"], revision_pins["original_artifact"], revision_pins["original_execution_output"]]
            pins["stage6_revision_feedback"] = [revision_pins["directed_feedback"], revision_pins["revision_plan"]]
            pins["revision_of"] = STAGE6_FEATURE
        else:
            pins["failed_original_stage6_r2"] = [revision_pins["r2_spec"], revision_pins["r2_artifact"], revision_pins["r2_execution_output"], revision_pins["r2_request"], revision_pins["r2_metadata"], revision_pins["r2_authorization"]]
            pins["stage6_r3_revision_feedback"] = [revision_pins["r2_empty_review"], revision_pins["r2_directed_feedback"]]
            pins["revision_of"] = STAGE6_REVISION_FEATURE
    init_meta = {"bridge": spec["bridge"], "native_slash_command": False, "command": "/sdd:spec-init", "stage": 6, "timestamp": timestamp, "run_id": args.run_id, "model_calls_made": False, "input_pins_sha256": adapter.input_pins_digest(pins)}
    spec_dir.mkdir(parents=True, exist_ok=False)
    adapter.write_json_new(spec_dir / "spec.json", spec)
    adapter.write_text_new(spec_dir / "requirements.md", req_template)
    adapter.write_json_new(spec_dir / "input-pins.json", pins)
    adapter.write_json_new(spec_dir / "init-metadata.json", init_meta)
    print(json.dumps({"created": str(spec_dir), "next": f"/sdd:spec-requirements {feature} --stage 6", "bridge": spec["bridge"]}, ensure_ascii=False))
    return 0


def build_payload(args: argparse.Namespace, run_root: Path, framework_root: Path, corpus_root: Path, package_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    parse_stage6(args.stage)
    feature = adapter.validate_feature(args.feature)
    if feature not in STAGE6_ACCEPTED_FEATURES:
        raise AdapterError(f"stage6 adapter accepts only features {', '.join(STAGE6_ACCEPTED_FEATURES)}")
    spec_dir = run_root / "specs" / feature
    if not spec_dir.exists():
        raise AdapterError(f"spec-init output not found for feature: {feature}")
    spec = adapter.load_json(spec_dir / "spec.json")
    if spec.get("pipeline_stage") != 6 or spec.get("artifact_type") != "api-contract" or spec.get("upstream_specs") != [STAGE5_SPEC]:
        raise AdapterError("stage6 requires api-contract spec pinned to stage5")
    upstream, pins, source_bodies, framework_docs = stage6_current_input_pins(run_root, framework_root, corpus_root, package_path)
    revision_prompt: dict[str, Any] | None = None
    feedback_text = ""
    plan_text = ""
    review_text = ""
    if feature == STAGE6_REVISION_FEATURE:
        original_spec, revision_pins, original_text, feedback_text, plan_text = require_stage6_revision_inputs(run_root)
        if spec.get("revision_of") != STAGE6_FEATURE:
            raise AdapterError("stage6 r2 spec must be marked as revision of original stage6")
        pins["failed_original_stage6"] = [revision_pins["original_spec"], revision_pins["original_artifact"], revision_pins["original_execution_output"]]
        pins["stage6_revision_feedback"] = [revision_pins["directed_feedback"], revision_pins["revision_plan"]]
        pins["revision_of"] = STAGE6_FEATURE
        revision_prompt = {
            "revision_mode": "versioned Stage 6 revision, not an independent replica",
            "original_feature": STAGE6_FEATURE,
            "original_stage6_spec_json": original_spec,
            "requirements_md": original_text,
            "instruction": "Carry the failed original Stage 6 artifact and feedback explicitly as revision inputs. Never approve the original Stage 6 artifact and do not silently repair it.",
        }
    if feature == STAGE6_R3_FEATURE:
        r2_spec, revision_pins, r2_text, review_text, feedback_text = require_stage6_r3_revision_inputs(run_root)
        if spec.get("revision_of") != STAGE6_REVISION_FEATURE:
            raise AdapterError("stage6 r3 spec must be marked as revision of stage6 r2")
        pins["failed_original_stage6_r2"] = [revision_pins["r2_spec"], revision_pins["r2_artifact"], revision_pins["r2_execution_output"], revision_pins["r2_request"], revision_pins["r2_metadata"], revision_pins["r2_authorization"]]
        pins["stage6_r3_revision_feedback"] = [revision_pins["r2_empty_review"], revision_pins["r2_directed_feedback"]]
        pins["revision_of"] = STAGE6_REVISION_FEATURE
        revision_prompt = {
            "revision_mode": "versioned Stage 6 r3 revision of r2, not an independent replica",
            "original_feature": STAGE6_REVISION_FEATURE,
            "original_stage6_spec_json": r2_spec,
            "requirements_md": r2_text,
            "instruction": "Carry the unapproved r2 artifact and both new review/feedback records explicitly as revision inputs. Never approve r2 or r3 and do not silently repair prior artifacts.",
        }
    recorded = adapter.load_json(spec_dir / "input-pins.json") if (spec_dir / "input-pins.json").exists() else None
    if recorded and adapter.input_pins_digest(recorded) != adapter.input_pins_digest(pins):
        raise AdapterError("stage6 recorded input pins are stale")
    prompt = {
        "bridge_notice": "This is an explicit local bridge for adapted /sdd:spec-requirements --stage 6, not a native slash command.",
        "task": "Draft ONLY the Stage 6 API Contract Specification for the AWS CardDemo public cycle from approved stage5 canonical data boundary; do not implement anything, do not execute COBOL, and do not approve any gate.",
        "required_scope": {"mandatory_tracks": MANDATORY_TRACKS, "coverage_rule": "Posting, interest, and reporting are all mandatory and must remain separately traceable tracks; inherit the exact upstream capability identity without renaming it."},
        "required_tracks": [
            {"name": "API operation surface", "requirement": "Define API contract clauses only where licensed by Stage5 canonical elements or explicit D-n decisions; OpenAPI is preferred and the output must be representable in OpenAPI."},
            {"name": "Stage5 D/type/field/outcome traceability", "requirement": "Map every contract element, type schema, field, outcome variant, exclusion, unsupported item or gap back to Stage5 D-n/type/field/outcome treatment and upstream R-n rule."},
            {"name": "traceable representation choices", "requirement": "Stage 6 may make D-n representation choices for method, route, schema shape, status and error categories when they remain traceable and must not create new business guarantees."},
            {"name": "explicit blocking gaps", "requirement": "Record blocking gaps only where Stage5 obligations cannot be represented without invention, or where a proposed contract clause would create unsupported business or semantic guarantees."},
        ],
        "required_output": "Return one requirements.md API Contract Specification only, following the supplied generic api-contract-spec template/rules. It must preserve reverse completeness for all R-1..R-20 with contract clause, justified exclusion, external/unsupported status, or gap. For r2, return a revision that proposes concrete request/schema/status/envelope choices for human gate review without treating them as approved runtime guarantees.",
        "contract_rules": [
            "Preserve exact capability identity and mandatory posting, interest, and reporting tracks.",
            "Use approved stages 1, 2-r2, 3-r2, 4, and 5 current versions, all original byte pins, authorizations, both stage5 review attachments, exact source text, stable numbered line representations, the source package, and the actual generic api-contract-spec template/rules.",
            "Carry Stage5 D/type/field/outcome traceability forward into API contract clauses and maintain reverse completeness for every R-1..R-20.",
            "Stage 6 may choose method, route, schema, validation, status, error category, and representation shape as documented D-n representation choices when traceable to Stage5 and when they do not add business guarantees.",
            "For the r2 revision, demand concrete proposed request/schema/status/envelope choices tied to D-n; do not invent business rules to make them appear source-grounded.",
            "For the r2 revision, preserve batch granularity, output order/multiplicity, and all three tracks; model request participation as consumer-supplied, externally supplied, internal dependency, unknown/EOF, or not exposed as appropriate.",
            "For the r2 revision, preserve unknown vs false: not_attested is not confirmed incomplete; missing disclosure is not zero; absence of report records/totals is not empty success or total zero.",
            "For the r2 revision, distinguish preliminary posting rejections 100..103 from internal reason 109; do not expose 109 as preliminary business rejection.",
            "For the r2 revision, optional observable outputs are optional boundary representations, not guaranteed telemetry; do not expose branch traces, file statuses, retries, idempotency receipts, rollbacks or status resources.",
            "For the r2 revision, do not allow all-empty responses to vacuously satisfy capability obligations or label everything closed by uncertainty tags; observable obligations must retain representation, with unknowns scoped to the missing authority.",
            "For the r3 revision, make a narrow revision only: keep external-input design and no-provisioning/no-selector/no-EOF limits; fix only the observed empty available[] versus all-unavailable/no-observation and 200/503/500 boundary.",
            "For the r3 revision, available with items: [] means an observed empty represented sequence and does not require substantive nonempty content for observed empty sequences; unavailable means no item observation represented.",
            "For the r3 revision, all-unavailable/no-observation envelope: not 200; 503 content_unavailable is for lack of substantive observation when no known technical failure; known technical failure: 500, optionally with already available content.",
            "For the r3 revision, Remove or narrow blanket minItems: 1 for InterestEnvelope and ReportingEnvelope; do not force observed empty generated-transaction or records sequences into 503 or business failure.",
            "For the r3 revision, keep zero-rate bypass distinct from zero amount/zero computed quantity and missing disclosure; do not require substantive nonempty content in a way that conflicts with the directed feedback.",
            "For the r3 revision, if progress-only 200 remains possible for posting, zero counts are progress observation only and must not prove no effects, full exhaustion, durable state, or transaction/rejection output fulfillment; zero-count progress is not output fulfillment.",
            "For the r3 revision, preserve no complete empty report claim: empty records must not certify complete empty report, complete date-range processing, zero totals, reconciled totals, final account total, or skip-and-continue repair.",
            "For the r3 revision, preserve ordering/multiplicity, reason 109 internal, unknown not false, deployment/status choices as proposals, No E1/E2 content/comparison, no Stage7, no implementation/OpenAPI generation, and no gate approval.",
            "Unsupported business or semantic guarantees, and Stage5 obligations that cannot be represented without invention, must remain explicit blocking gaps, exclusions, or unsupported/external statuses.",
            "State and observability clauses must distinguish consumer-visible contract from internal state; do not expose internal state as guaranteed observability unless Stage5 licenses it explicitly.",
        ],
        "negative_constraints": [
            "No model/network calls during prepare-only; no implementation, no adapter behavior, No Stage7, No API implementation, no COBOL execution, no source repairs, no generated code and no gate approval.",
            "The contract must not invent units, rounding, date validity, durability, EOF handling, retry safety, idempotency, rollback, persistence, reset, isolation, pagination, authentication, or validation policy not licensed by Stage5.",
            "The contract must not expose internal state as guaranteed observability merely because Stage5 modeled it as canonical/internal state.",
            "Do not close ambiguity by convenience; require explicit blocking gaps for unsupported concrete API contract decisions and no arbitrary closure.",
            "No COBOL execution. No Stage7 or later material. No adapter behavior, runtime binding, storage design, ports, framework implementation, or semantic validation.",
            "No tools, no previous_response_id, store=false, no fallback/retry, no temperature/max_output_tokens fields.",
        ],
        "run": {"run_id": args.run_id, "stage": 6, "feature": feature},
        "roots": {"RUN_ROOT": str(run_root), "FRAMEWORK_ROOT": str(framework_root), "CORPUS_ROOT": str(corpus_root)},
        "spec_json": spec,
        "approved_upstream": upstream,
        "failed_original_stage6": revision_prompt,
        "revision_feedback": ({"directed_feedback_md": feedback_text, "revision_plan_md": plan_text} if feature == STAGE6_REVISION_FEATURE else ({"r2_empty_review_md": review_text, "r2_directed_feedback_md": feedback_text} if feature == STAGE6_R3_FEATURE else None)),
        "revision_gate_rule": "human gate remains external; this bridge prepares or executes a request only and does not approve Stage 6, Stage 7, or any API implementation",
        "input_pins": pins,
        "source_bodies": source_bodies,
        "framework_context": framework_docs,
    }
    instructions = "Execute only the adapted stage-6 API Contract command supplied in the user input. Return English Markdown without code fences. Do not approve any gate."
    payload = {"model": adapter.MODEL, "store": False, "stream": True, "instructions": instructions, "input": [{"role": "user", "content": json.dumps(prompt, ensure_ascii=False, indent=2)}]}
    metadata = {
        "bridge": adapter.BRIDGE_NAME + ":stage6",
        "native_slash_command": False,
        "command": "/sdd:spec-requirements",
        "stage": 6,
        "run_id": args.run_id,
        "feature": feature,
        "model": adapter.MODEL,
        "base_url": adapter.BASE_URL,
        "execute_authorized": False,
        "prepared_at": args.timestamp or adapter.now_iso(),
        "request_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
        "input_pins_sha256": adapter.input_pins_digest(pins),
        "upstream_specs": [STAGE5_SPEC],
        "framework_root": str(framework_root),
        "corpus_root": str(corpus_root),
        "research_package": str(package_path),
    }
    return payload, metadata


def command_spec_requirements(args: argparse.Namespace) -> int:
    parse_stage6(args.stage)
    run_root, framework_root, corpus_root, package_path = adapter.validate_common(args)
    feature = adapter.validate_feature(args.feature)
    if feature not in STAGE6_ACCEPTED_FEATURES:
        raise AdapterError(f"stage6 adapter accepts only features {', '.join(STAGE6_ACCEPTED_FEATURES)}")
    prep_dir = run_root / "prepared" / feature
    if prep_dir.exists() or prep_dir.is_symlink():
        if args.execute and not prep_dir.is_symlink():
            saved = adapter.load_json(prep_dir / "request.json")
            saved_meta = adapter.load_json(prep_dir / "metadata.json")
            if saved_meta.get("stage") != 6:
                raise AdapterError("prepared stage mismatch")
            _, current_pins, _, _ = stage6_current_input_pins(run_root, framework_root, corpus_root, package_path)
            if feature == STAGE6_REVISION_FEATURE:
                _, revision_pins, _, _, _ = require_stage6_revision_inputs(run_root)
                current_pins["failed_original_stage6"] = [revision_pins["original_spec"], revision_pins["original_artifact"], revision_pins["original_execution_output"]]
                current_pins["stage6_revision_feedback"] = [revision_pins["directed_feedback"], revision_pins["revision_plan"]]
                current_pins["revision_of"] = STAGE6_FEATURE
            if feature == STAGE6_R3_FEATURE:
                _, revision_pins, _, _, _ = require_stage6_r3_revision_inputs(run_root)
                current_pins["failed_original_stage6_r2"] = [revision_pins["r2_spec"], revision_pins["r2_artifact"], revision_pins["r2_execution_output"], revision_pins["r2_request"], revision_pins["r2_metadata"], revision_pins["r2_authorization"]]
                current_pins["stage6_r3_revision_feedback"] = [revision_pins["r2_empty_review"], revision_pins["r2_directed_feedback"]]
                current_pins["revision_of"] = STAGE6_REVISION_FEATURE
            if saved_meta.get("input_pins_sha256") != adapter.input_pins_digest(current_pins):
                raise AdapterError("prepared stage6 input pins are stale")
            digest = hashlib.sha256(json.dumps(saved, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if digest != saved_meta["request_sha256"]:
                raise AdapterError("prepared hash mismatch")
            return adapter.execute_request(args, prep_dir, saved, saved_meta)
        stage6_current_input_pins(run_root, framework_root, corpus_root, package_path)
        if feature == STAGE6_REVISION_FEATURE:
            require_stage6_revision_inputs(run_root)
        if feature == STAGE6_R3_FEATURE:
            require_stage6_r3_revision_inputs(run_root)
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
    p.description = "Explicit local adapter for v3 SDD stage-6 commands only"
    p.set_defaults(stage="6")
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

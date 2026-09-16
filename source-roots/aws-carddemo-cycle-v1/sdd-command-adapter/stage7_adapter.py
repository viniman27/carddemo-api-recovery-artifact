#!/usr/bin/env python3
"""Stage-7-only local bridge for AWS CardDemo Adapter Behavior SDD commands."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import adapter
import stage6_adapter
from adapter import AdapterError

STAGE7_FEATURE = "adapter-behavior-carddemo"
STAGE7_R2_FEATURE = "adapter-behavior-carddemo-r2"
STAGE7_ACCEPTED_FEATURES = (STAGE7_FEATURE, STAGE7_R2_FEATURE)
STAGE6_R3_FEATURE = stage6_adapter.STAGE6_R3_FEATURE
STAGE6_R3_SPEC = f"specs/{STAGE6_R3_FEATURE}/spec.json"
STAGE6_R3_ARTIFACT = f"specs/{STAGE6_R3_FEATURE}/requirements.md"
STAGE6_R3_AUTHORIZATION = "reviews/stage-6-r3-authorization.json"
STAGE6_R3_REVIEW = "STAGE6-R3-COUNTEREXAMPLE-REVIEW.md"
STAGE6_R3_FINDINGS = f"specs/{STAGE6_R3_FEATURE}/stage6-r3-verification.json"
STAGE7_TEMPLATE = "settings/templates/pipeline/adapter-behavior-spec.md"
MANDATORY_TRACKS = stage6_adapter.MANDATORY_TRACKS
EXPECTED_REAL_CORPUS_FILE_COUNT = stage6_adapter.EXPECTED_REAL_CORPUS_FILE_COUNT
EXPECTED_STAGE6_R3_ARTIFACT_SHA256 = "6cba102f8335843b46e75a77b1a71d4e56373a95d5ac63cf645491556c443b27"
EXPECTED_STAGE6_R3_AUTHORIZATION_SHA256 = "0c5228634cb0f3b3c779fafe2e7e9ae5109aebeb24b116268e73a9a00dd8213e"
EXPECTED_STAGE6_R3_REVIEW_SHA256 = "a8e41764b56018f530a2df96d75bff483086e84b2462fca156175b0f91be7159"
EXPECTED_STAGE6_R3_FINDINGS_SHA256 = "69a59af451a700f8de1d4711f64149ce5bd295ced79bcee1747caf2aefee0193"
ORIGINAL_STAGE7_SPEC = f"specs/{STAGE7_FEATURE}/spec.json"
ORIGINAL_STAGE7_ARTIFACT = f"specs/{STAGE7_FEATURE}/requirements.md"
ORIGINAL_STAGE7_EXECUTION_OUTPUT = f"prepared/{STAGE7_FEATURE}/execution/scope-original.md"
ORIGINAL_STAGE7_RAW = f"prepared/{STAGE7_FEATURE}/execution/response.sse"
ORIGINAL_STAGE7_REQUEST = f"prepared/{STAGE7_FEATURE}/request.json"
ORIGINAL_STAGE7_METADATA = f"prepared/{STAGE7_FEATURE}/metadata.json"
ORIGINAL_STAGE7_AUTHORIZATION = "stage7-generation-authorization.json"
STAGE7_R1_DIRECTED_FEEDBACK = "reviews/stage-7-r1-directed-feedback.md"
STAGE7_DESIGN_EVIDENCE_REVIEW = "STAGE7-DESIGN-EVIDENCE-REVIEW.md"
EXPECTED_ORIGINAL_STAGE7_SPEC_SHA256 = "f561dbeb8c7be74057b98c6e502b82331d684a35b847481f55c2db5cf4ed1e5e"
EXPECTED_ORIGINAL_STAGE7_ARTIFACT_SHA256 = "0125e68e65e38c703e89b0c1b843358da91a5281e20860fb7f59316d3286ecf4"
EXPECTED_ORIGINAL_STAGE7_RAW_SHA256 = "93eb1f0e2ccf447726768f0ce9dfe242a7965434afc01205b03ef3b2b9b9f262"
EXPECTED_ORIGINAL_STAGE7_REQUEST_SHA256 = "4aba5f791186c4f5cbbd59495b29dbecfc98b1510d46ec545fda168d80ff2b0a"
EXPECTED_ORIGINAL_STAGE7_METADATA_SHA256 = "a89793d73e1020854af4020f3b617e9528aa85021488f23edd9bd215cf541d12"
EXPECTED_ORIGINAL_STAGE7_AUTHORIZATION_SHA256 = "0f2e743439454a617121cd1c9adccbe3a11b179f9bca2c3194a537fc4cdc7a5d"
EXPECTED_STAGE7_R1_DIRECTED_FEEDBACK_SHA256 = "960aae5144215cc64dd6f47acb883dd41aecad7d94a45d9cd66f4477ed0a3cc5"
EXPECTED_STAGE7_DESIGN_EVIDENCE_REVIEW_SHA256 = "9eeb4f3e46506f1ac185331a42ee26c7f2cfccc424239073a42fbb6d9e17a505"

# Re-export r2/r3 revision constants so tests and one-off read-only checks can
# patch this stage without mutating stage6_adapter module state.
EXPECTED_R2_STAGE6_SPEC_SHA256 = stage6_adapter.EXPECTED_R2_STAGE6_SPEC_SHA256
EXPECTED_R2_STAGE6_ARTIFACT_SHA256 = stage6_adapter.EXPECTED_R2_STAGE6_ARTIFACT_SHA256
EXPECTED_R2_STAGE6_REQUEST_SHA256 = stage6_adapter.EXPECTED_R2_STAGE6_REQUEST_SHA256
EXPECTED_R2_STAGE6_METADATA_SHA256 = stage6_adapter.EXPECTED_R2_STAGE6_METADATA_SHA256
EXPECTED_R2_STAGE6_AUTHORIZATION_SHA256 = stage6_adapter.EXPECTED_R2_STAGE6_AUTHORIZATION_SHA256
EXPECTED_R2_EMPTY_REVIEW_SHA256 = stage6_adapter.EXPECTED_R2_EMPTY_REVIEW_SHA256
EXPECTED_R2_DIRECTED_FEEDBACK_SHA256 = stage6_adapter.EXPECTED_R2_DIRECTED_FEEDBACK_SHA256


def parse_stage7(value: Any) -> int:
    try:
        stage = int(str(value))
    except ValueError as exc:
        raise AdapterError("stage7 adapter accepts only --stage 7") from exc
    if stage != 7:
        raise AdapterError("stage7 adapter accepts only --stage 7")
    return stage


def _pin_expected_run_file(run_root: Path, rel: str, expected_sha256: str, message: str) -> dict[str, str]:
    pin = adapter.pin_run_file(run_root, rel)
    if pin["sha256"] != expected_sha256:
        raise AdapterError(message)
    return pin


def read_framework_doc(framework_root: Path, rel: str) -> dict[str, str]:
    return stage6_adapter.read_framework_doc(framework_root, rel)


def collect_stage7_framework_context(framework_root: Path) -> list[dict[str, str]]:
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
        STAGE7_TEMPLATE,
    ]
    # Fail closed: these documents are mandatory Stage7 framework inputs, not
    # opportunistic context. A missing rule/template must stop request building
    # before a prompt can silently omit framework constraints.
    return [read_framework_doc(framework_root, rel) for rel in rels]


def _with_stage6_patch(name: str, value: Any):
    class _Patch:
        def __enter__(self):
            self.old = getattr(stage6_adapter, name)
            setattr(stage6_adapter, name, value)
            return None
        def __exit__(self, exc_type, exc, tb):
            setattr(stage6_adapter, name, self.old)
            return False
    return _Patch()


def require_stage6_r3_revision_history(run_root: Path):
    names = [
        "EXPECTED_R2_STAGE6_SPEC_SHA256",
        "EXPECTED_R2_STAGE6_ARTIFACT_SHA256",
        "EXPECTED_R2_STAGE6_REQUEST_SHA256",
        "EXPECTED_R2_STAGE6_METADATA_SHA256",
        "EXPECTED_R2_STAGE6_AUTHORIZATION_SHA256",
        "EXPECTED_R2_EMPTY_REVIEW_SHA256",
        "EXPECTED_R2_DIRECTED_FEEDBACK_SHA256",
    ]
    stack = []
    try:
        for name in names:
            p = _with_stage6_patch(name, globals()[name])
            p.__enter__()
            stack.append(p)
        return stage6_adapter.require_stage6_r3_revision_inputs(run_root)
    finally:
        for p in reversed(stack):
            p.__exit__(None, None, None)


def validate_stage6_r3_authorization(run_root: Path, stage6_spec: dict[str, Any], auth: dict[str, Any]) -> None:
    decision = auth.get("decision")
    if decision is not None and decision != "approve":
        raise AdapterError("stage6 r3 authorization decision rejects stage7")
    if auth.get("approved") is not True and decision != "approve":
        raise AdapterError("stage6 r3 authorization is not approved")
    if auth.get("stage") != 6:
        raise AdapterError("stage6 r3 authorization stage mismatch")
    if auth.get("run_id") != stage6_spec.get("run_id"):
        raise AdapterError("stage6 r3 authorization run_id mismatch")
    stage6_adapter._require_pin_exact(run_root, auth.get("artifact"), STAGE6_R3_ARTIFACT, "stage6 r3 authorization artifact pin missing or stale")
    stage6_adapter._require_pin_exact(run_root, auth.get("review_reference"), STAGE6_R3_REVIEW, "stage6 r3 authorization review reference missing or stale")
    stage6_adapter._require_pin_exact(run_root, auth.get("findings_reference"), STAGE6_R3_FINDINGS, "stage6 r3 authorization findings reference missing or stale")


def require_stage7_r2_revision_inputs(run_root: Path) -> tuple[dict[str, Any], dict[str, dict[str, str]], str, str, str]:
    original_spec_pin = _pin_expected_run_file(run_root, ORIGINAL_STAGE7_SPEC, EXPECTED_ORIGINAL_STAGE7_SPEC_SHA256, "original stage7 spec sha mismatch")
    original_spec = adapter.load_json(adapter.rel_run_file(run_root, ORIGINAL_STAGE7_SPEC))
    if original_spec.get("pipeline_stage") != 7 or original_spec.get("artifact_type") != "adapter-behavior":
        raise AdapterError("original stage7 artifact has wrong stage or artifact type")
    if original_spec.get("feature_name") not in (None, STAGE7_FEATURE):
        raise AdapterError("original stage7 feature identity mismatch")
    if original_spec.get("upstream_specs") != [STAGE6_R3_SPEC]:
        raise AdapterError("original stage7 must remain pinned to approved stage6 r3")
    approvals = original_spec.get("approvals", {}).get("requirements", {})
    if approvals.get("approved") is True or original_spec.get("gate", {}).get("completeness_gate_passed") is True or original_spec.get("ready_for_implementation") is True:
        raise AdapterError("original stage7 must remain unapproved for r2 revision")
    artifact_pin = _pin_expected_run_file(run_root, ORIGINAL_STAGE7_ARTIFACT, EXPECTED_ORIGINAL_STAGE7_ARTIFACT_SHA256, "original stage7 requirements sha mismatch")
    output_pin = _pin_expected_run_file(run_root, ORIGINAL_STAGE7_EXECUTION_OUTPUT, EXPECTED_ORIGINAL_STAGE7_ARTIFACT_SHA256, "original stage7 execution output sha mismatch")
    original_text = adapter.rel_run_file(run_root, ORIGINAL_STAGE7_ARTIFACT).read_text(encoding="utf-8")
    output_text = adapter.rel_run_file(run_root, ORIGINAL_STAGE7_EXECUTION_OUTPUT).read_text(encoding="utf-8")
    if output_text != original_text:
        raise AdapterError("original stage7 materialized artifact differs from execution output")
    raw_pin = _pin_expected_run_file(run_root, ORIGINAL_STAGE7_RAW, EXPECTED_ORIGINAL_STAGE7_RAW_SHA256, "original stage7 raw response sha mismatch")
    request_pin = _pin_expected_run_file(run_root, ORIGINAL_STAGE7_REQUEST, EXPECTED_ORIGINAL_STAGE7_REQUEST_SHA256, "original stage7 prepared request sha mismatch")
    metadata_pin = _pin_expected_run_file(run_root, ORIGINAL_STAGE7_METADATA, EXPECTED_ORIGINAL_STAGE7_METADATA_SHA256, "original stage7 prepared metadata sha mismatch")
    auth_pin = _pin_expected_run_file(run_root, ORIGINAL_STAGE7_AUTHORIZATION, EXPECTED_ORIGINAL_STAGE7_AUTHORIZATION_SHA256, "original stage7 generation authorization sha mismatch")
    meta = adapter.load_json(adapter.rel_run_file(run_root, ORIGINAL_STAGE7_METADATA))
    auth = adapter.load_json(adapter.rel_run_file(run_root, ORIGINAL_STAGE7_AUTHORIZATION))
    if meta.get("stage") != 7 or meta.get("feature") != STAGE7_FEATURE:
        raise AdapterError("original stage7 prepared metadata identity mismatch")
    if auth.get("stage") != 7 or auth.get("run_id") != original_spec.get("run_id") or auth.get("approved") is not True:
        raise AdapterError("original stage7 generation authorization identity mismatch")
    if auth.get("request_sha256") != meta.get("request_sha256"):
        raise AdapterError("original stage7 generation authorization request hash mismatch")
    feedback_pin = _pin_expected_run_file(run_root, STAGE7_R1_DIRECTED_FEEDBACK, EXPECTED_STAGE7_R1_DIRECTED_FEEDBACK_SHA256, "stage7 r1 directed feedback sha mismatch")
    review_pin = _pin_expected_run_file(run_root, STAGE7_DESIGN_EVIDENCE_REVIEW, EXPECTED_STAGE7_DESIGN_EVIDENCE_REVIEW_SHA256, "stage7 design evidence review sha mismatch")
    feedback_text = adapter.rel_run_file(run_root, STAGE7_R1_DIRECTED_FEEDBACK).read_text(encoding="utf-8")
    review_text = adapter.rel_run_file(run_root, STAGE7_DESIGN_EVIDENCE_REVIEW).read_text(encoding="utf-8")
    return original_spec, {
        "original_spec": original_spec_pin,
        "original_artifact": artifact_pin,
        "original_execution_output": output_pin,
        "original_raw": raw_pin,
        "original_request": request_pin,
        "original_metadata": metadata_pin,
        "original_authorization": auth_pin,
        "directed_feedback": feedback_pin,
        "design_evidence_review": review_pin,
    }, original_text, feedback_text, review_text


def stage7_current_input_pins(run_root: Path, framework_root: Path, corpus_root: Path, package_path: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    gate = adapter.run_gate_checker(run_root, framework_root, STAGE6_R3_SPEC)
    stage6_spec = adapter.load_json(adapter.rel_run_file(run_root, STAGE6_R3_SPEC))
    if stage6_spec.get("pipeline_stage") != 6 or stage6_spec.get("artifact_type") != "api-contract":
        raise AdapterError("stage7 requires approved/current stage6 r3 api-contract upstream")
    if stage6_spec.get("feature_name") not in (None, STAGE6_R3_FEATURE) or stage6_spec.get("revision_of") != stage6_adapter.STAGE6_REVISION_FEATURE:
        raise AdapterError("stage6 r3 feature or revision identity mismatch")
    if stage6_spec.get("upstream_specs") != [stage6_adapter.STAGE5_SPEC]:
        raise AdapterError("stage6 r3 must remain pinned to approved stage5")
    if stage6_spec.get("mandatory_tracks") != MANDATORY_TRACKS:
        raise AdapterError("stage6 r3 must preserve posting, interest and reporting tracks")
    approvals = stage6_spec.get("approvals", {}).get("requirements", {})
    if approvals.get("approved") is not True or stage6_spec.get("gate", {}).get("completeness_gate_passed") is not True:
        raise AdapterError("stage6 r3 is not approved/current for stage7")
    review = stage6_spec.get("gate", {}).get("review", {})
    auth_pin = review.get("authorization")
    if not isinstance(auth_pin, dict) or auth_pin.get("path") != STAGE6_R3_AUTHORIZATION:
        raise AdapterError("approved stage6 r3 authorization pin missing")
    expected_stage5_pin = {"path": stage6_adapter.STAGE5_SPEC, "sha256": adapter.sha256_file(adapter.rel_run_file(run_root, stage6_adapter.STAGE5_SPEC))}
    if review.get("upstream_specs", []) != [expected_stage5_pin]:
        raise AdapterError("stage6 r3 upstream stage5 pin is missing or stale")

    with _with_stage6_patch("EXPECTED_REAL_CORPUS_FILE_COUNT", EXPECTED_REAL_CORPUS_FILE_COUNT):
        upstream16, pins16, source_bodies, _ = stage6_adapter.stage6_current_input_pins(run_root, framework_root, corpus_root, package_path)
    if len(source_bodies) != EXPECTED_REAL_CORPUS_FILE_COUNT:
        raise AdapterError(f"stage7 requires exact real corpus retention: expected {EXPECTED_REAL_CORPUS_FILE_COUNT}, got {len(source_bodies)}")
    r2_spec, revision_pins, r2_text, r2_review_text, r2_feedback_text = require_stage6_r3_revision_history(run_root)
    stage6_artifact_pin = _pin_expected_run_file(run_root, STAGE6_R3_ARTIFACT, EXPECTED_STAGE6_R3_ARTIFACT_SHA256, "stage6 r3 requirements sha mismatch")
    stage6_auth_pin = _pin_expected_run_file(run_root, STAGE6_R3_AUTHORIZATION, EXPECTED_STAGE6_R3_AUTHORIZATION_SHA256, "stage6 r3 authorization sha mismatch")
    review_pin = _pin_expected_run_file(run_root, STAGE6_R3_REVIEW, EXPECTED_STAGE6_R3_REVIEW_SHA256, "stage6 r3 review sha mismatch")
    findings_pin = _pin_expected_run_file(run_root, STAGE6_R3_FINDINGS, EXPECTED_STAGE6_R3_FINDINGS_SHA256, "stage6 r3 findings sha mismatch")
    if auth_pin.get("sha256") != stage6_auth_pin["sha256"]:
        raise AdapterError("stage6 r3 gate authorization pin is stale")
    stage6_auth = adapter.load_json(adapter.rel_run_file(run_root, STAGE6_R3_AUTHORIZATION))
    validate_stage6_r3_authorization(run_root, stage6_spec, stage6_auth)
    stage6_text = adapter.rel_run_file(run_root, STAGE6_R3_ARTIFACT).read_text(encoding="utf-8")
    review_text = adapter.rel_run_file(run_root, STAGE6_R3_REVIEW).read_text(encoding="utf-8")
    findings_json = adapter.load_json(adapter.rel_run_file(run_root, STAGE6_R3_FINDINGS))
    framework_docs = collect_stage7_framework_context(framework_root)

    pins = {
        "stage": 7,
        "upstream_specs": pins16["upstream_specs"] + [adapter.pin_run_file(run_root, STAGE6_R3_SPEC)],
        "upstream_artifacts": pins16["upstream_artifacts"] + [stage6_artifact_pin],
        "authorizations": pins16["authorizations"] + [stage6_auth_pin],
        "review_attachments": pins16.get("review_attachments", []) + [review_pin, findings_pin],
        "stage6_r3_review_reference": review_pin,
        "stage6_r3_findings_reference": findings_pin,
        "stage6_r3_revision_history": [
            revision_pins["r2_spec"], revision_pins["r2_artifact"], revision_pins["r2_execution_output"],
            revision_pins["r2_request"], revision_pins["r2_metadata"], revision_pins["r2_authorization"],
            revision_pins["r2_empty_review"], revision_pins["r2_directed_feedback"],
        ],
        "gate_check": gate,
        "source_package": {"path": str(package_path), "sha256": adapter.sha256_file(package_path)},
        "source_bodies": [{"path": b["path"], "sha256": b["sha256"], "role": b["role"], "derived_representation_sha256": b["derived_representation_sha256"]} for b in source_bodies],
        "framework_context": [{"path": d["path"], "sha256": d["sha256"]} for d in framework_docs],
        "mandatory_tracks": MANDATORY_TRACKS,
        "expected_real_corpus_file_count": 19,
        "actual_corpus_file_count": len(source_bodies),
    }
    upstream = dict(upstream16)
    upstream.update({
        "stage6_r3_spec_json": stage6_spec,
        "stage6_r3_requirements_md": stage6_text,
        "stage6_r3_authorization": stage6_auth,
        "stage6_r3_counterexample_review_md": review_text,
        "stage6_r3_findings_json": findings_json,
        "stage6_r2_revision_spec_json": r2_spec,
        "stage6_r2_revision_requirements_md": r2_text,
        "stage6_r2_empty_review_md": r2_review_text,
        "stage6_r2_directed_feedback_md": r2_feedback_text,
    })
    return upstream, pins, source_bodies, framework_docs


def command_spec_init(args: argparse.Namespace) -> int:
    parse_stage7(args.stage)
    feature = adapter.validate_feature(args.feature)
    if feature not in STAGE7_ACCEPTED_FEATURES:
        raise AdapterError(f"stage7 adapter accepts only features {', '.join(STAGE7_ACCEPTED_FEATURES)}")
    run_root, framework_root, corpus_root, package_path = adapter.validate_common(args)
    upstream, pins, _, _ = stage7_current_input_pins(run_root, framework_root, corpus_root, package_path)
    revision = None
    if feature == STAGE7_R2_FEATURE:
        revision = require_stage7_r2_revision_inputs(run_root)
        original_spec, _, _, _, _ = revision
        if original_spec.get("capability") != upstream["stage6_r3_spec_json"].get("capability"):
            raise AdapterError("stage7 r2 revision capability mismatch with approved stage6 r3")
    timestamp = args.timestamp or adapter.now_iso()
    spec_dir = run_root / "specs" / feature
    if spec_dir.exists() or spec_dir.is_symlink():
        raise AdapterError(f"refusing to overwrite existing spec directory: {spec_dir}")
    template_json = adapter.read_required(framework_root / "settings/templates/specs/init.json")
    req_template = adapter.read_required(framework_root / "settings/templates/specs/requirements-init.md")
    replacements = {
        "{{FEATURE_NAME}}": feature,
        "{{ARTIFACT_TYPE}}": "adapter-behavior",
        "{{CAPABILITY}}": upstream["stage6_r3_spec_json"]["capability"],
        "{{RUN_ID}}": args.run_id,
        "{{ARTIFACT_PATH}}": f"specs/{feature}/requirements.md",
        "{{TIMESTAMP}}": timestamp,
        "{{PROJECT_DESCRIPTION}}": "AWS CardDemo stage-7 Adapter Behavior Spec placeholder for documentary behavior mapping only",
    }
    for old, new in replacements.items():
        template_json = template_json.replace(old, new)
        req_template = req_template.replace(old, new)
    spec = json.loads(template_json)
    spec["pipeline_stage"] = 7
    spec["artifact_type"] = "adapter-behavior"
    spec["capability"] = upstream["stage6_r3_spec_json"]["capability"]
    spec["mandatory_tracks"] = MANDATORY_TRACKS
    spec["upstream_specs"] = [STAGE6_R3_SPEC]
    spec["bridge"] = adapter.BRIDGE_NAME + ":stage7"
    spec["ready_for_implementation"] = False
    if feature == STAGE7_R2_FEATURE:
        spec["revision_of"] = STAGE7_FEATURE
        spec["revision_basis"] = "failed-original-stage7-plus-directed-feedback-and-design-evidence-review"
        spec.setdefault("approvals", {}).setdefault("requirements", {})["approved"] = False
    spec["roots"] = {"RUN_ROOT": str(run_root), "FRAMEWORK_ROOT": str(framework_root), "CORPUS_ROOT": str(corpus_root)}
    spec["adapted_from"] = ["/sdd:spec-init --stage 7", "pipeline-sdd-v3 stage 7 Adapter Behavior Spec"]
    init_meta = {"bridge": spec["bridge"], "native_slash_command": False, "command": "/sdd:spec-init", "stage": 7, "timestamp": timestamp, "run_id": args.run_id, "model_calls_made": False, "input_pins_sha256": adapter.input_pins_digest(pins)}
    if revision is not None:
        _, revision_pins, _, _, _ = revision
        pins["failed_original_stage7"] = [
            revision_pins["original_spec"], revision_pins["original_artifact"], revision_pins["original_execution_output"],
            revision_pins["original_raw"], revision_pins["original_request"], revision_pins["original_metadata"], revision_pins["original_authorization"],
        ]
        pins["stage7_r2_revision_feedback"] = [revision_pins["directed_feedback"], revision_pins["design_evidence_review"]]
        pins["revision_of"] = STAGE7_FEATURE
        init_meta["input_pins_sha256"] = adapter.input_pins_digest(pins)
    spec_dir.mkdir(parents=True, exist_ok=False)
    adapter.write_json_new(spec_dir / "spec.json", spec)
    adapter.write_text_new(spec_dir / "requirements.md", req_template)
    adapter.write_json_new(spec_dir / "input-pins.json", pins)
    adapter.write_json_new(spec_dir / "init-metadata.json", init_meta)
    print(json.dumps({"created": str(spec_dir), "next": f"/sdd:spec-requirements {feature} --stage 7", "bridge": spec["bridge"]}, ensure_ascii=False))
    return 0


def build_payload(args: argparse.Namespace, run_root: Path, framework_root: Path, corpus_root: Path, package_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    parse_stage7(args.stage)
    feature = adapter.validate_feature(args.feature)
    if feature not in STAGE7_ACCEPTED_FEATURES:
        raise AdapterError(f"stage7 adapter accepts only features {', '.join(STAGE7_ACCEPTED_FEATURES)}")
    spec_dir = run_root / "specs" / feature
    if not spec_dir.exists():
        raise AdapterError(f"spec-init output not found for feature: {feature}")
    spec = adapter.load_json(spec_dir / "spec.json")
    if spec.get("pipeline_stage") != 7 or spec.get("artifact_type") != "adapter-behavior" or spec.get("upstream_specs") != [STAGE6_R3_SPEC]:
        raise AdapterError("stage7 requires adapter-behavior spec pinned to stage6 r3")
    upstream, pins, source_bodies, framework_docs = stage7_current_input_pins(run_root, framework_root, corpus_root, package_path)
    revision_prompt: dict[str, Any] | None = None
    feedback_text = ""
    review_text = ""
    if feature == STAGE7_R2_FEATURE:
        original_spec, revision_pins, original_text, feedback_text, review_text = require_stage7_r2_revision_inputs(run_root)
        if spec.get("revision_of") != STAGE7_FEATURE:
            raise AdapterError("stage7 r2 spec must be marked as revision of original stage7")
        pins["failed_original_stage7"] = [
            revision_pins["original_spec"], revision_pins["original_artifact"], revision_pins["original_execution_output"],
            revision_pins["original_raw"], revision_pins["original_request"], revision_pins["original_metadata"], revision_pins["original_authorization"],
        ]
        pins["stage7_r2_revision_feedback"] = [revision_pins["directed_feedback"], revision_pins["design_evidence_review"]]
        pins["revision_of"] = STAGE7_FEATURE
        revision_prompt = {
            "revision_mode": "versioned Stage 7 r2 revision, not an independent replica",
            "original_feature": STAGE7_FEATURE,
            "original_stage7_spec_json": original_spec,
            "requirements_md": original_text,
            "instruction": "Carry the unapproved original Stage7 artifact, original raw/request/metadata/generation authorization, and both review/feedback records explicitly as revision inputs. Never approve the original or r2 and do not silently repair prior artifacts.",
        }
    recorded = adapter.load_json(spec_dir / "input-pins.json") if (spec_dir / "input-pins.json").exists() else None
    if recorded and adapter.input_pins_digest(recorded) != adapter.input_pins_digest(pins):
        raise AdapterError("stage7 recorded input pins are stale")
    prompt = {
        "bridge_notice": "This is an explicit local bridge for adapted /sdd:spec-requirements --stage 7, not a native slash command.",
        "task": "Draft ONLY the Stage 7 Adapter Behavior Specification for the AWS CardDemo public cycle from approved/current Stage6 r3. DOCUMENT behavior mapping only; do not implement anything, do not execute COBOL, do not prepare Stage8, and do not approve any gate.",
        "required_scope": {"mandatory_tracks": MANDATORY_TRACKS, "coverage_rule": "Posting, interest, and reporting are all mandatory and must remain separately traceable tracks; inherit the exact upstream capability identity without renaming it."},
        "required_tracks": [
            {"name": "external input binding responsibilities", "requirement": "Map who supplies each contract input and legacy/reference dependency; distinguish consumer request fields, external setup, legacy-internal dependencies, unknown EOF/input limitations, unavailable observations, and bounded gaps."},
            {"name": "observation acquisition and provenance vs fabrication", "requirement": "For every observable output, state how the adapter would acquire it from legacy/reference behavior or mark it unavailable; never fabricate telemetry, counters, readiness, durable state, reset evidence, retry evidence, or completion evidence."},
            {"name": "operation behavior mapping", "requirement": "Map the three contract operations in order with ordered outputs, observed-empty vs unavailable, known failure500, successful observations200, observations503 none, internal reason 109, EOF limitations, and Stage6 r3 status boundaries."},
            {"name": "bounded gaps", "requirement": "Distinguish design proposals vs demonstrated runtime. Raise bounded gaps where a binding, observation source, reset/isolation claim, durability claim, or error mapping cannot be justified from approved upstream evidence."},
        ],
        "required_output": "Return one requirements.md Adapter Behavior Specification only, following the supplied generic adapter-behavior-spec template/rules. It must map Stage6 r3 contract clauses to documentary adapter behavior responsibilities; no code, no implementation tasks, no COBOL, no Stage8.",
        "adapter_behavior_rules": [
            "Use approved stages 1, 2-r2, 3-r2, 4, 5, and Stage6 r3 current versions, all original byte pins, authorizations, Stage6 review/findings, revision history pins, exact corpus19 source text with stable numbered representations, and the actual generic adapter-behavior-spec template/rules.",
            "Preserve exact capability identity and mandatory posting, interest, and reporting tracks.",
            "Inherit Stage6 r3 external-input contract design exactly; Stage7 may document binding responsibilities but must not invent provisioning, selectors, EOF handling, validation policy, readiness, durability, reset, retry, idempotency, rollback, telemetry or state lifecycle guarantees.",
            "For observations, distinguish observed-empty from unavailable: available items: [] is an observed empty represented sequence; unavailable is no represented observation; known technical failure is 500; successful available observations are 200; observations503 none means no substantive observation is represented and no known technical failure is established.",
            "Preserve ordered outputs, output multiplicity, internal reason 109, preliminary reasons 100..103 boundary, zero-count progress limits, no complete empty report claim, unknown not false, and EOF limitations from Stage6 r3.",
            "Distinguish design proposals from demonstrated runtime: until actual runtime evidence exists, describe proposed adapter responsibilities as proposed and raise bounded gaps for unjustified binding or observation acquisition.",
            "Document behavior mapping only: no generated code, route/controller/service structure, COBOL changes, build commands, implementation tasks, Stage8 validation scenarios, E1/E2 comparisons, or claims based on executing the legacy.",
            "For the r2 revision, make a narrow documentary behavior revision only: require concrete internal invocation/resource/capture/conversion/failure/state records and field-by-field provenance for every mapped Stage6 r3 clause.",
            "For the r2 revision, distinguish stale/truncated/zero-length capture records from observed empty business outputs; observed empty is a represented observation, while absent, truncated, stale, or zero-length evidence is an evidence-state problem, not proof of empty behavior.",
            "For the r2 revision, no new public fields/routes/status/request changes; map internals and provenance without changing the Stage6 r3 public contract surface.",
            "For the r2 revision, use a three-state documentary closure matrix that separates closed-by-documentary-design, open-bounded-gap, and deferred-empirical-obligation; G31 remains external human approval and the model must NEVER author its approval.",
            "For the r2 revision, preserve109/EOF/order/multiplicity exactly, no fabricated runtime proof, and separate later empirical obligations from decisions now.",
        ],
        "negative_constraints": [
            "No model/network calls during prepare-only; no implementation, no code, no COBOL execution, no source repairs, no generated adapter, no API implementation, no Stage8 and no gate approval.",
            "No invented telemetry/readiness/durability/reset/retry/idempotency/rollback/persistence/progress completion guarantees.",
            "No E1/E2 comparisons or contents; do not import zero-shot/few-shot outputs or evaluate Stage6 against them.",
            "No tools, no previous_response_id, store=false, no fallback/retry, no temperature/max_output_tokens fields.",
        ],
        "run": {"run_id": args.run_id, "stage": 7, "feature": feature},
        "roots": {"RUN_ROOT": str(run_root), "FRAMEWORK_ROOT": str(framework_root), "CORPUS_ROOT": str(corpus_root)},
        "spec_json": spec,
        "approved_upstream": upstream,
        "failed_original_stage7": revision_prompt,
        "stage7_revision_feedback": ({"directed_feedback_md": feedback_text, "design_evidence_review_md": review_text, "verbatim_rule": "actual feedback verbatim"} if feature == STAGE7_R2_FEATURE else None),
        "revision_gate_rule": "human gate remains external; this bridge prepares or executes a request only and does not approve Stage 7, Stage 8, API implementation or COBOL execution",
        "input_pins": pins,
        "source_bodies": source_bodies,
        "framework_context": framework_docs,
    }
    instructions = "Execute only the adapted stage-7 Adapter Behavior command supplied in the user input. Return English Markdown without code fences. Do not approve any gate, do not write code, and do not create Stage 8 material."
    payload = {"model": adapter.MODEL, "store": False, "stream": True, "instructions": instructions, "input": [{"role": "user", "content": json.dumps(prompt, ensure_ascii=False, indent=2)}]}
    metadata = {
        "bridge": adapter.BRIDGE_NAME + ":stage7",
        "native_slash_command": False,
        "command": "/sdd:spec-requirements",
        "stage": 7,
        "run_id": args.run_id,
        "feature": feature,
        "model": adapter.MODEL,
        "base_url": adapter.BASE_URL,
        "execute_authorized": False,
        "prepared_at": args.timestamp or adapter.now_iso(),
        "request_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
        "input_pins_sha256": adapter.input_pins_digest(pins),
        "upstream_specs": [STAGE6_R3_SPEC],
        "framework_root": str(framework_root),
        "corpus_root": str(corpus_root),
        "research_package": str(package_path),
    }
    return payload, metadata


def command_spec_requirements(args: argparse.Namespace) -> int:
    parse_stage7(args.stage)
    run_root, framework_root, corpus_root, package_path = adapter.validate_common(args)
    feature = adapter.validate_feature(args.feature)
    if feature not in STAGE7_ACCEPTED_FEATURES:
        raise AdapterError(f"stage7 adapter accepts only features {', '.join(STAGE7_ACCEPTED_FEATURES)}")
    prep_dir = run_root / "prepared" / feature
    if prep_dir.exists() or prep_dir.is_symlink():
        if args.execute and not prep_dir.is_symlink():
            saved = adapter.load_json(prep_dir / "request.json")
            saved_meta = adapter.load_json(prep_dir / "metadata.json")
            if saved_meta.get("stage") != 7:
                raise AdapterError("prepared stage mismatch")
            _, current_pins, _, _ = stage7_current_input_pins(run_root, framework_root, corpus_root, package_path)
            if feature == STAGE7_R2_FEATURE:
                _, revision_pins, _, _, _ = require_stage7_r2_revision_inputs(run_root)
                current_pins["failed_original_stage7"] = [
                    revision_pins["original_spec"], revision_pins["original_artifact"], revision_pins["original_execution_output"],
                    revision_pins["original_raw"], revision_pins["original_request"], revision_pins["original_metadata"], revision_pins["original_authorization"],
                ]
                current_pins["stage7_r2_revision_feedback"] = [revision_pins["directed_feedback"], revision_pins["design_evidence_review"]]
                current_pins["revision_of"] = STAGE7_FEATURE
            if saved_meta.get("input_pins_sha256") != adapter.input_pins_digest(current_pins):
                raise AdapterError("prepared stage7 input pins are stale")
            digest = hashlib.sha256(json.dumps(saved, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if digest != saved_meta["request_sha256"]:
                raise AdapterError("prepared hash mismatch")
            return adapter.execute_request(args, prep_dir, saved, saved_meta)
        stage7_current_input_pins(run_root, framework_root, corpus_root, package_path)
        if feature == STAGE7_R2_FEATURE:
            require_stage7_r2_revision_inputs(run_root)
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
    p.description = "Explicit local adapter for v3 SDD stage-7 commands only"
    p.set_defaults(stage="7")
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

#!/usr/bin/env python3
"""Stage-8-only local bridge for AWS CardDemo Semantic Validation SDD commands."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import adapter
import stage7_adapter
from adapter import AdapterError

STAGE8_FEATURE = "semantic-validation-carddemo"
STAGE7_R2_FEATURE = stage7_adapter.STAGE7_R2_FEATURE
STAGE7_R2_SPEC = f"specs/{STAGE7_R2_FEATURE}/spec.json"
STAGE7_R2_ARTIFACT = f"specs/{STAGE7_R2_FEATURE}/requirements.md"
STAGE7_R2_AUTHORIZATION = "reviews/stage-7-r2-authorization.json"
STAGE7_R2_REVIEW = "STAGE7-R2-COUNTEREXAMPLE-REVIEW.md"
STAGE7_R2_FINDINGS = f"specs/{STAGE7_R2_FEATURE}/stage7-r2-verification.json"
STAGE8_TEMPLATE = "settings/templates/pipeline/semantic-validation-spec.md"
MANDATORY_TRACKS = stage7_adapter.MANDATORY_TRACKS
EXPECTED_REAL_CORPUS_FILE_COUNT = stage7_adapter.EXPECTED_REAL_CORPUS_FILE_COUNT
EXPECTED_STAGE7_R2_ARTIFACT_SHA256 = "b53c471116dfa0c3831fc810964bddca3eb1fa0d3b8e7d459181ba71e54b3d8f"
EXPECTED_STAGE7_R2_AUTHORIZATION_SHA256 = "3e3315cfb4ae05e65f9627ae3147343259d93eabf31931c3177a105c1615cb60"
EXPECTED_STAGE7_R2_REVIEW_SHA256 = "74b60bb0be83f746ff46a10f1682e0a50a8e09100a36323724d7ff7c5abc476f"
EXPECTED_STAGE7_R2_FINDINGS_SHA256 = "0eed83701b579f719d5864b84ac54db5fa4571675146af63bea491e4f6418aad"


def parse_stage8(value: Any) -> int:
    try:
        stage = int(str(value))
    except ValueError as exc:
        raise AdapterError("stage8 adapter accepts only --stage 8") from exc
    if stage != 8:
        raise AdapterError("stage8 adapter accepts only --stage 8")
    return stage


def _pin_expected_run_file(run_root: Path, rel: str, expected_sha256: str, message: str) -> dict[str, str]:
    pin = adapter.pin_run_file(run_root, rel)
    if pin["sha256"] != expected_sha256:
        raise AdapterError(message)
    return pin


def read_framework_doc(framework_root: Path, rel: str) -> dict[str, str]:
    return stage7_adapter.read_framework_doc(framework_root, rel)


def collect_stage8_framework_context(framework_root: Path) -> list[dict[str, str]]:
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
        STAGE8_TEMPLATE,
    ]
    # Fail closed: semantic-validation template and generic rules are mandatory.
    return [read_framework_doc(framework_root, rel) for rel in rels]


def validate_stage7_r2_authorization(run_root: Path, stage7_spec: dict[str, Any], auth: dict[str, Any]) -> None:
    decision = auth.get("decision")
    if decision is not None and decision != "approve":
        raise AdapterError("stage7 r2 authorization decision rejects stage8")
    if auth.get("approved") is not True and decision != "approve":
        raise AdapterError("stage7 r2 authorization is not approved")
    if auth.get("stage") != 7:
        raise AdapterError("stage7 r2 authorization stage mismatch")
    if auth.get("run_id") != stage7_spec.get("run_id"):
        raise AdapterError("stage7 r2 authorization run_id mismatch")
    stage7_adapter.stage6_adapter._require_pin_exact(run_root, auth.get("artifact"), STAGE7_R2_ARTIFACT, "stage7 r2 authorization artifact pin missing or stale")
    stage7_adapter.stage6_adapter._require_pin_exact(run_root, auth.get("review_reference"), STAGE7_R2_REVIEW, "stage7 r2 authorization review reference missing or stale")
    stage7_adapter.stage6_adapter._require_pin_exact(run_root, auth.get("findings_reference"), STAGE7_R2_FINDINGS, "stage7 r2 authorization findings reference missing or stale")


def _with_stage7_patch(name: str, value: Any):
    class _Patch:
        def __enter__(self):
            self.old = getattr(stage7_adapter, name)
            setattr(stage7_adapter, name, value)
            return None
        def __exit__(self, exc_type, exc, tb):
            setattr(stage7_adapter, name, self.old)
            return False
    return _Patch()


def _stage7_current_input_pins(run_root: Path, framework_root: Path, corpus_root: Path, package_path: Path):
    with _with_stage7_patch("EXPECTED_REAL_CORPUS_FILE_COUNT", EXPECTED_REAL_CORPUS_FILE_COUNT):
        return stage7_adapter.stage7_current_input_pins(run_root, framework_root, corpus_root, package_path)


def stage8_current_input_pins(run_root: Path, framework_root: Path, corpus_root: Path, package_path: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    gate = adapter.run_gate_checker(run_root, framework_root, STAGE7_R2_SPEC)
    stage7_spec = adapter.load_json(adapter.rel_run_file(run_root, STAGE7_R2_SPEC))
    if stage7_spec.get("pipeline_stage") != 7 or stage7_spec.get("artifact_type") != "adapter-behavior":
        raise AdapterError("stage8 requires approved/current stage7 r2 adapter-behavior upstream")
    if stage7_spec.get("feature_name") not in (None, STAGE7_R2_FEATURE) or stage7_spec.get("revision_of") != stage7_adapter.STAGE7_FEATURE:
        raise AdapterError("stage7 r2 feature or revision identity mismatch")
    if stage7_spec.get("upstream_specs") != [stage7_adapter.STAGE6_R3_SPEC]:
        raise AdapterError("stage7 r2 must remain pinned to approved stage6 r3")
    if stage7_spec.get("mandatory_tracks") != MANDATORY_TRACKS:
        raise AdapterError("stage7 r2 must preserve posting, interest and reporting tracks")
    approvals = stage7_spec.get("approvals", {}).get("requirements", {})
    if approvals.get("approved") is not True or stage7_spec.get("gate", {}).get("completeness_gate_passed") is not True:
        raise AdapterError("stage7 r2 is not approved/current for stage8")
    review = stage7_spec.get("gate", {}).get("review", {})
    auth_pin = review.get("authorization")
    if not isinstance(auth_pin, dict) or auth_pin.get("path") != STAGE7_R2_AUTHORIZATION:
        raise AdapterError("approved stage7 r2 authorization pin missing")
    expected_stage6_pin = {"path": stage7_adapter.STAGE6_R3_SPEC, "sha256": adapter.sha256_file(adapter.rel_run_file(run_root, stage7_adapter.STAGE6_R3_SPEC))}
    if review.get("upstream_specs", []) != [expected_stage6_pin]:
        raise AdapterError("stage7 r2 upstream stage6 r3 pin is missing or stale")

    upstream17, pins17, source_bodies, _stage7_framework_docs = _stage7_current_input_pins(run_root, framework_root, corpus_root, package_path)
    if len(source_bodies) != EXPECTED_REAL_CORPUS_FILE_COUNT:
        raise AdapterError(f"stage8 requires exact real corpus retention: expected {EXPECTED_REAL_CORPUS_FILE_COUNT}, got {len(source_bodies)}")
    stage7_artifact_pin = _pin_expected_run_file(run_root, STAGE7_R2_ARTIFACT, EXPECTED_STAGE7_R2_ARTIFACT_SHA256, "stage7 r2 requirements sha mismatch")
    stage7_auth_pin = _pin_expected_run_file(run_root, STAGE7_R2_AUTHORIZATION, EXPECTED_STAGE7_R2_AUTHORIZATION_SHA256, "stage7 r2 authorization sha mismatch")
    stage7_review_pin = _pin_expected_run_file(run_root, STAGE7_R2_REVIEW, EXPECTED_STAGE7_R2_REVIEW_SHA256, "stage7 r2 review sha mismatch")
    stage7_findings_pin = _pin_expected_run_file(run_root, STAGE7_R2_FINDINGS, EXPECTED_STAGE7_R2_FINDINGS_SHA256, "stage7 r2 findings sha mismatch")
    if auth_pin.get("sha256") != stage7_auth_pin["sha256"]:
        raise AdapterError("stage7 r2 gate authorization pin is stale")
    stage7_auth = adapter.load_json(adapter.rel_run_file(run_root, STAGE7_R2_AUTHORIZATION))
    validate_stage7_r2_authorization(run_root, stage7_spec, stage7_auth)
    stage7_text = adapter.rel_run_file(run_root, STAGE7_R2_ARTIFACT).read_text(encoding="utf-8")
    review_text = adapter.rel_run_file(run_root, STAGE7_R2_REVIEW).read_text(encoding="utf-8")
    findings_json = adapter.load_json(adapter.rel_run_file(run_root, STAGE7_R2_FINDINGS))
    framework_docs = collect_stage8_framework_context(framework_root)

    pins = {
        "stage": 8,
        "upstream_specs": pins17["upstream_specs"] + [adapter.pin_run_file(run_root, STAGE7_R2_SPEC)],
        "upstream_artifacts": pins17["upstream_artifacts"] + [stage7_artifact_pin],
        "authorizations": pins17["authorizations"] + [stage7_auth_pin],
        "review_attachments": pins17.get("review_attachments", []) + [stage7_review_pin, stage7_findings_pin],
        "stage7_r2_review_reference": stage7_review_pin,
        "stage7_r2_findings_reference": stage7_findings_pin,
        "gate_check": gate,
        "source_package": {"path": str(package_path), "sha256": adapter.sha256_file(package_path)},
        "source_bodies": [{"path": b["path"], "sha256": b["sha256"], "role": b["role"], "derived_representation_sha256": b["derived_representation_sha256"]} for b in source_bodies],
        "framework_context": [{"path": d["path"], "sha256": d["sha256"]} for d in framework_docs],
        "mandatory_tracks": MANDATORY_TRACKS,
        "expected_real_corpus_file_count": 19,
        "actual_corpus_file_count": len(source_bodies),
    }
    upstream = dict(upstream17)
    upstream.update({
        "stage7_r2_spec_json": stage7_spec,
        "stage7_r2_requirements_md": stage7_text,
        "stage7_r2_authorization": stage7_auth,
        "stage7_r2_counterexample_review_md": review_text,
        "stage7_r2_findings_json": findings_json,
    })
    return upstream, pins, source_bodies, framework_docs


def command_spec_init(args: argparse.Namespace) -> int:
    parse_stage8(args.stage)
    feature = adapter.validate_feature(args.feature)
    if feature != STAGE8_FEATURE:
        raise AdapterError(f"stage8 adapter accepts only feature {STAGE8_FEATURE}")
    run_root, framework_root, corpus_root, package_path = adapter.validate_common(args)
    upstream, pins, _, _ = stage8_current_input_pins(run_root, framework_root, corpus_root, package_path)
    timestamp = args.timestamp or adapter.now_iso()
    spec_dir = run_root / "specs" / feature
    if spec_dir.exists() or spec_dir.is_symlink():
        raise AdapterError(f"refusing to overwrite existing spec directory: {spec_dir}")
    template_json = adapter.read_required(framework_root / "settings/templates/specs/init.json")
    req_template = adapter.read_required(framework_root / "settings/templates/specs/requirements-init.md")
    replacements = {
        "{{FEATURE_NAME}}": feature,
        "{{ARTIFACT_TYPE}}": "semantic-validation",
        "{{CAPABILITY}}": upstream["stage7_r2_spec_json"]["capability"],
        "{{RUN_ID}}": args.run_id,
        "{{ARTIFACT_PATH}}": f"specs/{feature}/requirements.md",
        "{{TIMESTAMP}}": timestamp,
        "{{PROJECT_DESCRIPTION}}": "AWS CardDemo stage-8 Semantic Validation Spec placeholder for documentary scenario design only",
    }
    for old, new in replacements.items():
        template_json = template_json.replace(old, new)
        req_template = req_template.replace(old, new)
    spec = json.loads(template_json)
    spec["pipeline_stage"] = 8
    spec["artifact_type"] = "semantic-validation"
    spec["capability"] = upstream["stage7_r2_spec_json"]["capability"]
    spec["mandatory_tracks"] = MANDATORY_TRACKS
    spec["upstream_specs"] = [STAGE7_R2_SPEC]
    spec["bridge"] = adapter.BRIDGE_NAME + ":stage8"
    spec["ready_for_implementation"] = False
    spec.setdefault("approvals", {}).setdefault("requirements", {})["approved"] = False
    spec["roots"] = {"RUN_ROOT": str(run_root), "FRAMEWORK_ROOT": str(framework_root), "CORPUS_ROOT": str(corpus_root)}
    spec["adapted_from"] = ["/sdd:spec-init --stage 8", "pipeline-sdd-v3 stage 8 Semantic Validation Spec"]
    init_meta = {"bridge": spec["bridge"], "native_slash_command": False, "command": "/sdd:spec-init", "stage": 8, "timestamp": timestamp, "run_id": args.run_id, "model_calls_made": False, "input_pins_sha256": adapter.input_pins_digest(pins)}
    spec_dir.mkdir(parents=True, exist_ok=False)
    adapter.write_json_new(spec_dir / "spec.json", spec)
    adapter.write_text_new(spec_dir / "requirements.md", req_template)
    adapter.write_json_new(spec_dir / "input-pins.json", pins)
    adapter.write_json_new(spec_dir / "init-metadata.json", init_meta)
    print(json.dumps({"created": str(spec_dir), "next": f"/sdd:spec-requirements {feature} --stage 8", "bridge": spec["bridge"]}, ensure_ascii=False))
    return 0


def build_payload(args: argparse.Namespace, run_root: Path, framework_root: Path, corpus_root: Path, package_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    parse_stage8(args.stage)
    feature = adapter.validate_feature(args.feature)
    if feature != STAGE8_FEATURE:
        raise AdapterError(f"stage8 adapter accepts only feature {STAGE8_FEATURE}")
    spec_dir = run_root / "specs" / feature
    if not spec_dir.exists():
        raise AdapterError(f"spec-init output not found for feature: {feature}")
    spec = adapter.load_json(spec_dir / "spec.json")
    if spec.get("pipeline_stage") != 8 or spec.get("artifact_type") != "semantic-validation" or spec.get("upstream_specs") != [STAGE7_R2_SPEC]:
        raise AdapterError("stage8 requires semantic-validation spec pinned to stage7 r2")
    upstream, pins, source_bodies, framework_docs = stage8_current_input_pins(run_root, framework_root, corpus_root, package_path)
    recorded = adapter.load_json(spec_dir / "input-pins.json") if (spec_dir / "input-pins.json").exists() else None
    if recorded and adapter.input_pins_digest(recorded) != adapter.input_pins_digest(pins):
        raise AdapterError("stage8 recorded input pins are stale")
    prompt = {
        "bridge_notice": "This is an explicit local bridge for adapted /sdd:spec-requirements --stage 8, not a native slash command.",
        "task": "Draft ONLY the Stage 8 Semantic Validation Specification for the AWS CardDemo public cycle from approved/current Stage7 r2. DOCUMENT scenarios, expected obligations and evidence acceptance criteria only; do not execute tests, do not implement anything, do not run COBOL or validate a runtime, do not approve any gate, and do not create stage9 material.",
        "required_scope": {"mandatory_tracks": MANDATORY_TRACKS, "coverage_rule": "Posting, interest, and reporting are all mandatory and must remain separately traceable tracks; inherit the exact upstream capability identity without renaming it."},
        "required_scenario_families": [
            {"name": "positive documentary scenarios", "requirement": "Specify expected obligations and acceptable evidence for valid Stage6/Stage7 mappings without representing them as executed tests or empirical results."},
            {"name": "negative documentary scenarios", "requirement": "Specify rejection/violation observations for stale, misattributed, truncated, absent, zero-length and empty capture states, conversions, partial failures and known vs unknown failures."},
            {"name": "counterexample documentary scenarios", "requirement": "Specify counterexamples that would falsify semantic-validation obligations, including observed-empty vs unavailable/503/500, state isolation/reset not promised, EOF limitations and internal reason 109 rules."},
            {"name": "reverse completeness", "requirement": "Map every Stage7 protocol, every Stage6 clause and R-1..R-20 to at least one validation obligation or explicitly unresolved empirical uncertainty; no silent omissions."},
        ],
        "required_output": "Return one requirements.md Semantic Validation Specification only, following the supplied generic semantic-validation template/rules. It must document scenarios, expected obligations, and evidence acceptance criteria derived from Stage7 protocols, Stage6 clauses, and R-1..R-20; no code, no implementation tasks, no COBOL/runtime validation, no approvals, no stage9.",
        "semantic_validation_rules": [
            "Use approved stages 1, 2-r2, 3-r2, 4, 5, Stage6 r3 and Stage7 r2 current versions, all original byte pins, authorizations, review/findings records, revision provenance, exact corpus19 original source text and numbered representations, and the actual generic semantic-validation-spec template/rules.",
            "Preserve exact capability identity and mandatory posting, interest, and reporting tracks.",
            "Prompt Stage8 DOCUMENT scenarios only: expected obligations and evidence acceptance criteria from Stage7 internal invocation/resource/capture/conversion/failure/state/response protocols, Stage6 clauses and R-1..R-20.",
            "Do not call scenarios T1 experimental execution, tests, empirical runs, runtime validation, or execution results. They are specification scenarios only.",
            "Distinguish positive, negative, and counterexample scenarios. Separate documentary acceptance criteria from later empirical uncertainty; empirical uncertainties explicitly unresolved, not fake test results. Stage7 protocols remain documentary sources, not runtime proof.",
            "Include stale, misattributed, truncated and empty capture evidence states; distinguish those evidence states from observed empty business outputs.",
            "Include conversions, partial failures known vs unknown, observed-empty available items: [] vs unavailable/503 and known technical failure/500, ordered outputs, output multiplicity, internal reason 109, EOF limitations and no complete empty report claim.",
            "State isolation/reset must not be promised as demonstrated proof; if validation would require runtime evidence, mark it as a deferred empirical obligation.",
            "No implementation, COBOL changes, no runtime validation, model/network execution evidence, generated tests, API implementation, approvals, E1/E2 comparisons, quarantine material, or stage9.",
        ],
        "negative_constraints": [
            "No model/network calls during prepare-only; no real-run writes beyond spec-init/prepare in the authorized RUN_ROOT; no implementation, no code, no COBOL execution, no test execution, no source repairs, no generated adapter, no API implementation, no Stage9 and no gate approval.",
            "No invented telemetry/readiness/durability/reset/retry/idempotency/rollback/persistence/progress completion guarantees.",
            "No E1/E2 comparisons or contents; do not import zero-shot/few-shot outputs, comparisons, or quarantine materials.",
            "No tools, no previous_response_id, store=false, no fallback/retry, no temperature/max_output_tokens fields.",
        ],
        "run": {"run_id": args.run_id, "stage": 8, "feature": feature},
        "roots": {"RUN_ROOT": str(run_root), "FRAMEWORK_ROOT": str(framework_root), "CORPUS_ROOT": str(corpus_root)},
        "spec_json": spec,
        "approved_upstream": upstream,
        "authorization_scope_rule": "Stage7 r2 structured approval authorizes Stage8 Semantic Validation DOCUMENT only; prose consent heuristics are never used and reject/contradictory structured fields win.",
        "input_pins": pins,
        "source_bodies": source_bodies,
        "framework_context": framework_docs,
    }
    instructions = "Execute only the adapted stage-8 Semantic Validation command supplied in the user input. Return English Markdown without code fences. Do not approve any gate, do not write code, do not execute tests, and do not create Stage 9 material."
    payload = {"model": adapter.MODEL, "store": False, "stream": True, "instructions": instructions, "input": [{"role": "user", "content": json.dumps(prompt, ensure_ascii=False, indent=2)}]}
    metadata = {
        "bridge": adapter.BRIDGE_NAME + ":stage8",
        "native_slash_command": False,
        "command": "/sdd:spec-requirements",
        "stage": 8,
        "run_id": args.run_id,
        "feature": feature,
        "model": adapter.MODEL,
        "base_url": adapter.BASE_URL,
        "execute_authorized": False,
        "prepared_at": args.timestamp or adapter.now_iso(),
        "request_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
        "input_pins_sha256": adapter.input_pins_digest(pins),
        "upstream_specs": [STAGE7_R2_SPEC],
        "framework_root": str(framework_root),
        "corpus_root": str(corpus_root),
        "research_package": str(package_path),
    }
    return payload, metadata


def verify_stage8_execution_authorization(path: Path | None, metadata: dict[str, Any]) -> dict[str, Any]:
    if path is None:
        raise AdapterError("--execute requires --authorization-file")
    auth = adapter.load_json(path)
    expected = {"approved": True, "stage": 8, "run_id": metadata["run_id"], "model": adapter.MODEL, "base_url": adapter.BASE_URL, "request_sha256": metadata["request_sha256"]}
    for key, value in expected.items():
        if auth.get(key) != value:
            raise AdapterError(f"authorization {key} mismatch")
    metadata["execute_authorized"] = True
    metadata["authorization_file"] = str(path)
    metadata["authorization_sha256"] = adapter.sha256_file(path)
    return auth


def execute_stage8_request(args: argparse.Namespace, prep_dir: Path, payload: dict[str, Any], metadata: dict[str, Any]) -> int:
    old = adapter.verify_execution_authorization
    try:
        adapter.verify_execution_authorization = verify_stage8_execution_authorization  # type: ignore[assignment]
        return adapter.execute_request(args, prep_dir, payload, metadata)
    finally:
        adapter.verify_execution_authorization = old  # type: ignore[assignment]


def command_spec_requirements(args: argparse.Namespace) -> int:
    parse_stage8(args.stage)
    run_root, framework_root, corpus_root, package_path = adapter.validate_common(args)
    feature = adapter.validate_feature(args.feature)
    if feature != STAGE8_FEATURE:
        raise AdapterError(f"stage8 adapter accepts only feature {STAGE8_FEATURE}")
    prep_dir = run_root / "prepared" / feature
    if prep_dir.exists() or prep_dir.is_symlink():
        if args.execute and not prep_dir.is_symlink():
            saved = adapter.load_json(prep_dir / "request.json")
            saved_meta = adapter.load_json(prep_dir / "metadata.json")
            if saved_meta.get("stage") != 8:
                raise AdapterError("prepared stage mismatch")
            _, current_pins, _, _ = stage8_current_input_pins(run_root, framework_root, corpus_root, package_path)
            if saved_meta.get("input_pins_sha256") != adapter.input_pins_digest(current_pins):
                raise AdapterError("prepared stage8 input pins are stale")
            digest = hashlib.sha256(json.dumps(saved, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if digest != saved_meta["request_sha256"]:
                raise AdapterError("prepared hash mismatch")
            return execute_stage8_request(args, prep_dir, saved, saved_meta)
        stage8_current_input_pins(run_root, framework_root, corpus_root, package_path)
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
    return execute_stage8_request(args, prep_dir, payload, metadata)


def build_parser() -> argparse.ArgumentParser:
    p = adapter.build_parser()
    p.description = "Explicit local adapter for v3 SDD stage-8 commands only"
    p.set_defaults(stage="8")
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

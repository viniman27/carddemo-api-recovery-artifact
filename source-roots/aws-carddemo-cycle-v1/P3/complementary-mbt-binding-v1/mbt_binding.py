#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CAP_BY_TRACK = {
    "posting": "CBTRN02C_POSTTRAN",
    "interest": "CBACT04C_INTCALC",
    "reporting": "CBTRN03C_TRANREPT",
}

# Pinned essential-fixture cases. Valuations are derived from prepared fixture intent,
# not from response success. The model interpreter below evaluates every guard.
CASE_SPECS: dict[str, dict[str, Any]] = {
    "valid-new-tcatbal": {
        "track": "posting",
        "evidence": "P3/complementary-posting-essential-v1/evidence/posting-essential-report.json",
        "candidateKind": "source_guided_transition_trace",
        "steps": [
            ("P_START", {"open_status": "00"}, "POSTTRAN-T001"),
            ("P_OPENED", {"read_status": "00"}, "POSTTRAN-T003"),
            ("P_VALIDATE_XREF", {"xref_exists": True}, "POSTTRAN-T008"),
            ("P_VALIDATE_ACCOUNT", {"account_exists": True, "within_limit": True, "not_expired_textual": True}, "POSTTRAN-T012"),
            ("P_TCATBAL", {"tcatbal_status": "23"}, "POSTTRAN-T013"),
            ("P_ACCOUNT_REWRITE", {"rewrite_invalid_key": False}, "POSTTRAN-T019"),
            ("P_TRANFILE_WRITE", {"tranfile_write_status": "00"}, "POSTTRAN-T021"),
        ],
    },
    "valid-existing-tcatbal": {
        "track": "posting",
        "evidence": "P3/complementary-posting-essential-v1/evidence/posting-essential-report.json",
        "candidateKind": "source_guided_transition_trace",
        "steps": [
            ("P_START", {"open_status": "00"}, "POSTTRAN-T001"),
            ("P_OPENED", {"read_status": "00"}, "POSTTRAN-T003"),
            ("P_VALIDATE_XREF", {"xref_exists": True}, "POSTTRAN-T008"),
            ("P_VALIDATE_ACCOUNT", {"account_exists": True, "within_limit": True, "not_expired_textual": True}, "POSTTRAN-T012"),
            ("P_TCATBAL", {"tcatbal_status": "00"}, "POSTTRAN-T013"),
            ("P_ACCOUNT_REWRITE", {"rewrite_invalid_key": False}, "POSTTRAN-T019"),
            ("P_TRANFILE_WRITE", {"tranfile_write_status": "00"}, "POSTTRAN-T021"),
        ],
    },
    "reject-card-missing": {
        "track": "posting",
        "evidence": "P3/complementary-posting-essential-v1/evidence/posting-essential-report.json",
        "candidateKind": "source_guided_transition_trace",
        "steps": [
            ("P_START", {"open_status": "00"}, "POSTTRAN-T001"),
            ("P_OPENED", {"read_status": "00"}, "POSTTRAN-T003"),
            ("P_VALIDATE_XREF", {"xref_exists": False}, "POSTTRAN-T007"),
        ],
    },
    "reject-account-missing": {
        "track": "posting",
        "evidence": "P3/complementary-posting-essential-v1/evidence/posting-essential-report.json",
        "candidateKind": "source_guided_transition_trace",
        "steps": [
            ("P_START", {"open_status": "00"}, "POSTTRAN-T001"),
            ("P_OPENED", {"read_status": "00"}, "POSTTRAN-T003"),
            ("P_VALIDATE_XREF", {"xref_exists": True}, "POSTTRAN-T008"),
            ("P_VALIDATE_ACCOUNT", {"account_exists": False}, "POSTTRAN-T009"),
        ],
    },
    "reject-limit": {
        "track": "posting",
        "evidence": "P3/complementary-posting-essential-v1/evidence/posting-essential-report.json",
        "candidateKind": "source_guided_transition_trace",
        "steps": [
            ("P_START", {"open_status": "00"}, "POSTTRAN-T001"),
            ("P_OPENED", {"read_status": "00"}, "POSTTRAN-T003"),
            ("P_VALIDATE_XREF", {"xref_exists": True}, "POSTTRAN-T008"),
            ("P_VALIDATE_ACCOUNT", {"account_exists": True, "within_limit": False, "not_expired_textual": True}, "POSTTRAN-T010"),
        ],
    },
    "reject-expiry": {
        "track": "posting",
        "evidence": "P3/complementary-posting-essential-v1/evidence/posting-essential-report.json",
        "candidateKind": "source_guided_transition_trace",
        "steps": [
            ("P_START", {"open_status": "00"}, "POSTTRAN-T001"),
            ("P_OPENED", {"read_status": "00"}, "POSTTRAN-T003"),
            ("P_VALIDATE_XREF", {"xref_exists": True}, "POSTTRAN-T008"),
            ("P_VALIDATE_ACCOUNT", {"account_exists": True, "not_expired_textual": False}, "POSTTRAN-T011"),
        ],
    },
    "rates-specific-default-zero": {
        "track": "interest",
        "evidence": "P3/complementary-interest-essential-v1/evidence/rates-specific-default-zero/result.json",
        "candidateKind": "source_guided_transition_trace",
        "steps": [
            ("I_START", {"open_status": "00"}, "INTCALC-T001"),
            ("I_OPENED", {"tcatbal_read_status": "00"}, "INTCALC-T003"),
            ("I_GROUP", {"disc_rate_path": "specific"}, "INTCALC-T007"),
            ("I_RATE", {}, "INTCALC-T009"),
            ("I_WRITE_INTEREST", {"interest_write_status": "00"}, "INTCALC-T010"),
            ("I_GROUP", {"disc_rate_path": "zero"}, "INTCALC-T009Z"),
        ],
    },
    "single-final-eof": {
        "track": "interest",
        "evidence": "P3/complementary-interest-essential-v1/evidence/single-final-eof/result.json",
        "candidateKind": "source_defect_observation_not_financial_correctness",
        "steps": [
            ("I_START", {"open_status": "00"}, "INTCALC-T001"),
            ("I_OPENED", {"tcatbal_read_status": "00"}, "INTCALC-T003"),
            ("I_GROUP", {"disc_rate_path": "specific"}, "INTCALC-T007"),
            ("I_RATE", {}, "INTCALC-T009"),
            ("I_WRITE_INTEREST", {"interest_write_status": "00"}, "INTCALC-T010"),
            ("I_OPENED", {"tcatbal_read_status": "10"}, "INTCALC-T006"),
        ],
    },
    "date-boundaries-in-out-v1": {
        "track": "reporting",
        "evidence": "P3/complementary-reporting-essential-v1/evidence/reporting-essential-results.json",
        "candidateKind": "source_guided_transition_trace",
        "steps": [
            ("R_START", {"open_status": "00"}, "TRANREPT-T001"),
            ("R_LOOP", {"read_status": "00", "date_window": "in_range"}, "TRANREPT-T003"),
            ("R_DETAIL", {"write_status": "00"}, "TRANREPT-T014"),
            ("R_LOOP", {"read_status": "00", "date_window": "out_of_range"}, "TRANREPT-T009"),
        ],
    },
    "empty-in-range-v1": {
        "track": "reporting",
        "evidence": "P3/complementary-reporting-essential-v1/evidence/reporting-essential-results.json",
        "candidateKind": "shared_only",
        "sharedOnlyReason": "unknown_guard_blocked",
        "steps": [("R_LOOP", {"read_status": "UnknownEOF"}, "TRANREPT-T013")],
    },
    "card-break-two-groups-v1": {
        "track": "reporting",
        "evidence": "P3/complementary-reporting-essential-v1/evidence/reporting-essential-results.json",
        "candidateKind": "shared_only",
        "sharedOnlyReason": "model_lacks_card_break_transition",
        "steps": [],
    },
    "pagination-threshold-20-v1": {
        "track": "reporting",
        "evidence": "P3/complementary-reporting-essential-v1/evidence/reporting-essential-results.json",
        "candidateKind": "shared_only",
        "sharedOnlyReason": "model_lacks_pagination_threshold_transition",
        "steps": [],
    },
}

CONTRACTS_7_OPS_21 = [
    {"contractId": cid, "operationCount": 3, "trackOps": ["posting", "interest", "reporting"]}
    for cid in ["E1-1", "E1-2", "E1-3", "E2-1", "E2-2", "E2-3", "E3-SDD-stage6r3"]
]

@dataclass(frozen=True)
class ReferenceEngine:
    module: Any
    model: dict[str, Any]
    root: Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pin(path: Path, cycle_root: Path, label: str | None = None) -> dict[str, Any]:
    p = path.resolve()
    return {
        "label": label or p.name,
        "path": str(p.relative_to(cycle_root.resolve())),
        "absolutePath": str(p),
        "bytes": p.stat().st_size,
        "sha256": sha256_file(p),
    }


def load_reference_engine(cycle_root: Path) -> ReferenceEngine:
    root = cycle_root.resolve() / "P3/reference-executable-v4"
    py = root / "executable_reference.py"
    spec = importlib.util.spec_from_file_location("carddemo_reference_executable_v4", py)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import reference engine {py}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.load_model(root / "model.json")
    return ReferenceEngine(module=module, model=model, root=root)


def _find_transition(engine: ReferenceEngine, cap_id: str, transition_id: str) -> dict[str, Any] | None:
    for cap in engine.model.get("capabilities", []):
        if cap.get("id") == cap_id:
            for tr in cap.get("transitions", []):
                if tr.get("id") == transition_id:
                    return tr
    return None


def evaluate_step(engine: ReferenceEngine, cap_id: str, state_id: str, valuation: dict[str, Any], transition_id: str) -> dict[str, Any]:
    transition = _find_transition(engine, cap_id, transition_id)
    if transition is None:
        return {"transitionId": transition_id, "state": state_id, "valuation": valuation, "guardResult": None, "qualified": False, "blockReason": "transition_missing"}
    enabled = engine.module.step(engine.model, cap_id, state_id, valuation)
    actual = next((x for x in enabled if x["transitionId"] == transition_id), None)
    if actual is None:
        cap = next(c for c in engine.model["capabilities"] if c["id"] == cap_id)
        current = engine.module._initial_state(cap, state_id, valuation)
        guard_result = engine.module.eval_guard(transition["guard"], current["values"], cap)
    else:
        guard_result = actual["guardResult"]
    qualified = guard_result is True
    if qualified:
        block = None
    elif guard_result == "unknown":
        block = "guard_unknown"
    elif guard_result is False:
        block = "guard_false"
    else:
        block = "transition_not_enabled"
    return {
        "transitionId": transition_id,
        "state": state_id,
        "valuation": valuation,
        "guard": transition.get("guard"),
        "guardResult": guard_result,
        "qualified": qualified,
        "blockReason": block,
        "obligationRefs": transition.get("obligationRefs", []),
        "sourceAnchors": transition.get("sourceAnchors", []),
        "events": [e.get("event") for e in transition.get("effects", []) if e.get("op") == "emit"],
    }


def _fixture_pin(cycle_root: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    path = cycle_root / spec["evidence"]
    pins = [pin(path, cycle_root, "essential-fixture-evidence")]
    if spec["track"] == "interest":
        freeze = path.parent / "input-freeze.json"
        if freeze.exists():
            pins.append(pin(freeze, cycle_root, "pinned-input-freeze"))
    return pins


def _source_authority(case_steps: list[dict[str, Any]]) -> bool:
    return all(step.get("sourceAnchors") for step in case_steps)


def evaluate_all(cycle_root: Path) -> dict[str, Any]:
    cycle_root = cycle_root.resolve()
    engine = load_reference_engine(cycle_root)
    model_validation = engine.module.validate_model(engine.model, root=engine.root)
    source_pins = engine.module.validate_source_pins(engine.model, engine.root)
    cases: list[dict[str, Any]] = []
    for case_id, spec in CASE_SPECS.items():
        cap_id = CAP_BY_TRACK[spec["track"]]
        steps = [evaluate_step(engine, cap_id, state, valuation, transition) for state, valuation, transition in spec["steps"]]
        all_true = bool(steps) and all(s["qualified"] for s in steps)
        if spec.get("candidateKind") == "shared_only":
            classification = "shared_only"
            reason = spec["sharedOnlyReason"]
        elif all_true:
            classification = "eligible_t3_candidate"
            reason = None
        else:
            classification = "shared_only"
            reasons = [s["blockReason"] for s in steps if s["blockReason"]]
            reason = reasons[0] if reasons else "no_qualified_transition_trace"
        cases.append({
            "caseId": case_id,
            "track": spec["track"],
            "classification": classification,
            "candidateKind": spec.get("candidateKind"),
            "sharedOnlyReason": reason,
            "capability": cap_id,
            "modelTrace": steps,
            "sourceAuthorityChecked": _source_authority(steps) if steps else True,
            "fixturePins": _fixture_pin(cycle_root, spec),
            "checkerCompatibility": "shared complementary checker may evaluate preserved artifacts without prompts/feedback; candidate registry is prospective only",
        })
    counts = Counter(c["track"] for c in cases)
    classes = Counter(c["classification"] for c in cases)
    artifact_pins = [
        pin(engine.root / "model.json", cycle_root, "reference-executable-v4/model.json"),
        pin(engine.root / "executable_reference.py", cycle_root, "reference-executable-v4/executable_reference.py"),
    ]
    artifact_pins.extend(p for c in cases for p in c["fixturePins"])
    return {
        "kind": "complementary-mbt-binding-v1-candidate-registry",
        "createdUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "scope": "Evaluate pinned essential-fixture inputs against real reference-executable-v4 model guards/traces only. No API reruns, no COBOL reruns, no model calls, no invented T1/T2 generation.",
        "summary": {
            "essentialCaseCount": len(cases),
            "caseCountsByTrack": dict(counts),
            "eligibleT3CandidateCount": classes.get("eligible_t3_candidate", 0),
            "sharedOnlyCount": classes.get("shared_only", 0),
            "apiReruns": False,
            "originalCampaignReruns": False,
            "modelCalls": False,
            "modelValidationErrors": model_validation.get("errors", []),
            "sourcePinErrors": source_pins.get("errors", []),
        },
        "candidateRegistryContract": {
            "prospectiveOnly": True,
            "officialT3": False,
            "notRetroactive": "previously observed complementary results are not converted into official T3; this registry is a recipe/input qualification for future authorized execution",
            "t1T2Fixed": "T1/T2 first-campaign material remains fixed; this tool does not generate or rewrite T1/T2",
        },
        "contracts21OpsMapping": {"contractCount": 7, "operationCount": 21, "contracts": CONTRACTS_7_OPS_21},
        "cases": cases,
        "artifactPins": sorted({(p["path"], p["sha256"]): p for p in artifact_pins}.values(), key=lambda p: p["path"]),
        "recommendedNextAction": "If an official T3/T4 campaign is still desired, freeze this registry prospectively as a new recipe and run the authorized runner only on eligible_t3_candidate cases; keep shared_only cases in the complementary shared-checker ledger.",
    }


def render_plan(cycle_root: Path) -> str:
    lines = [
        "# Complementary MBT binding v1 plan",
        "",
        "Mode: plan only; no API/COBOL/model reruns and no campaign execution.",
        "Reference: P3/reference-executable-v4/model.json + executable_reference.py.",
        "Cases:",
    ]
    for case_id, spec in CASE_SPECS.items():
        lines.append(f"- {case_id}: {spec['track']} -> {len(spec['steps'])} model step(s), kind={spec.get('candidateKind')}")
    lines.append("")
    lines.append("Output of validate is a prospective candidate registry, not official T3/T4 evidence.")
    return "\n".join(lines) + "\n"


def write_status(out: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    text = f"""# Complementary MBT binding v1 STATUS

Status: validated against real `reference-executable-v4` interpreter and pinned essential fixture evidence.

- Essential cases evaluated: {s['essentialCaseCount']} ({s['caseCountsByTrack']})
- Eligible prospective T3 candidates: {s['eligibleT3CandidateCount']}
- Shared-only preserved cases: {s['sharedOnlyCount']}
- API/COBOL/model/original-campaign reruns: none
- Model validation errors: {s['modelValidationErrors']}
- Source pin errors: {s['sourcePinErrors']}

Recommended next action: {payload['recommendedNextAction']}
"""
    (out.parent / "STATUS.md").write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate complementary essential fixtures against real MBT model guards/traces.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--cycle-root", type=Path, required=True)
    v = sub.add_parser("validate")
    v.add_argument("--cycle-root", type=Path, required=True)
    v.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.cmd == "plan":
        sys.stdout.write(render_plan(args.cycle_root))
        return 0
    if args.cmd == "validate":
        payload = evaluate_all(args.cycle_root)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        write_status(args.out, payload)
        print(json.dumps(payload["summary"], sort_keys=True))
        return 1 if payload["summary"]["modelValidationErrors"] or payload["summary"]["sourcePinErrors"] else 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

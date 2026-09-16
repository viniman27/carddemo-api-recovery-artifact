#!/usr/bin/env python3
"""P3 pretest fixture/campaign configuration checks.

Non-executing preparation only. This module validates local review artifacts and
must not launch official T1/T2/T3/T4 campaigns.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REQUIRED_PENDING = {
    "t1.model", "t1.budget", "t1.seed",
    "t2.budget", "t2.seed",
    "t3.modelOracle", "t4.unionPolicy",
}
TRACKS = {"posting", "interest", "reporting"}
HEX = set("0123456789abcdef")


def _sha256ish(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX


def fixture_descriptor_sha256(fixture: dict[str, Any]) -> str:
    """Hash local technical fixture selection metadata excluding its hash field."""
    canonical = {k: v for k, v in fixture.items() if k != "contentSha256"}
    data = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _validate_common_fixture(i: int, fx: dict[str, Any], errors: list[str]) -> None:
    if fx.get("track") not in TRACKS:
        errors.append(f"fixtures[{i}].track invalid")
    for key in ["fixtureId", "contentSha256", "provenance", "exposure", "reset"]:
        if key not in fx:
            errors.append(f"fixtures[{i}].{key} missing")
    if not _sha256ish(fx.get("contentSha256")):
        errors.append(f"fixtures[{i}].contentSha256 must be explicit sha256")
    elif "materializer" in fx and fixture_descriptor_sha256(fx) != fx.get("contentSha256"):
        errors.append(f"fixtures[{i}].contentSha256 mismatch for local technical descriptor")
    if fx.get("exposure", {}).get("label") != "technical-only":
        errors.append(f"fixtures[{i}].exposure.label must be technical-only")
    if fx.get("reset", {}).get("default") != "fresh_dir_per_run":
        errors.append(f"fixtures[{i}].reset.default must be fresh_dir_per_run")
    forbidden = {"expectedAnswer", "oracle", "officialOutcome"} & set(fx)
    if forbidden:
        errors.append(f"fixtures[{i}] contains oracle/answer fields: {sorted(forbidden)}")


def validate_fixture_registry(registry: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    kind = registry.get("kind")
    status = registry.get("status")
    if kind == "p3-local-fixture-registry-schema-only":
        if status != "draft_pending_freeze":
            errors.append("status must be draft_pending_freeze")
    elif kind == "p3-local-technical-fixture-selection":
        if status != "technical_local_only":
            errors.append("status must be technical_local_only")
    else:
        errors.append("kind must mark schema-only registry or local technical fixture selection")
    fixtures = registry.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        errors.append("fixtures must be a non-empty list")
        fixtures = []
    seen_tracks: set[str] = set()
    for i, fx in enumerate(fixtures):
        _validate_common_fixture(i, fx, errors)
        if kind == "p3-local-technical-fixture-selection":
            seen_tracks.add(fx.get("track"))
            if fx.get("materializer", {}).get("kind") != "builtin_technical_smoke":
                errors.append(f"fixtures[{i}].materializer.kind must be builtin_technical_smoke")
    if kind == "p3-local-technical-fixture-selection" and seen_tracks != TRACKS:
        errors.append(f"local technical selection must cover all tracks: {sorted(TRACKS)}")
    return {"ok": not errors, "errors": errors}


def validate_campaign_config(cfg: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if cfg.get("kind") != "p3-campaign-config-schema-only":
        errors.append("kind must mark schema-only campaign config")
    if cfg.get("execution", {}).get("mode") != "schema_only_non_executing":
        errors.append("execution.mode must be schema_only_non_executing")
    if cfg.get("approval", {}).get("freezeStatus") != "pending_human_freeze":
        errors.append("approval.freezeStatus must be pending_human_freeze")
    if cfg.get("reset", {}).get("default") != "fresh_dir_per_run":
        errors.append("reset.default must be fresh_dir_per_run")
    if cfg.get("statefulSequences", {}).get("status") != "pending":
        errors.append("statefulSequences.status must remain pending")
    pending = set(cfg.get("pendingFreezeChoices", []))
    missing = sorted(REQUIRED_PENDING - pending)
    if missing:
        errors.append(f"pendingFreezeChoices missing required unresolved choices: {missing}")
    for forbidden in ["oracleAnswers", "officialFixtures", "execute", "modelResponses"]:
        if forbidden in cfg:
            errors.append(f"forbidden executable/official field present: {forbidden}")
    return {"ok": not errors, "errors": errors}


def execution_decision(cfg: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if cfg.get("approval", {}).get("freezeStatus") != "approved_frozen":
        reasons.append("freeze approval missing")
    if cfg.get("execution", {}).get("mode") != "approved_campaign_execution":
        reasons.append("config is non-executing preparation only")
    # This module has no official campaign runner and no authenticated approval
    # mechanism. Label-only configs therefore remain fail-closed by design.
    reasons.append("no official runner/authenticated execution gate is implemented")
    return {"allowed": False, "reasons": reasons}


def main() -> None:
    root = Path(__file__).resolve().parent
    checks = {
        "fixture_registry": validate_fixture_registry(json.loads((root / "fixture-registry.sample.json").read_text())),
        "campaign_config": validate_campaign_config(json.loads((root / "campaign-config.sample.json").read_text())),
        "execution_decision": execution_decision(json.loads((root / "campaign-config.sample.json").read_text())),
    }
    print(json.dumps(checks, indent=2))
    if not all(v.get("ok", True) for v in checks.values() if isinstance(v, dict)):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

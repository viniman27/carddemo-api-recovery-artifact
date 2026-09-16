#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

FORBIDDEN_AUTH_LABELS = {"approved", "approve", "authorized", "autorizado", "aprovado", "liberado"}


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def verify(manifest_path: Path) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    root = manifest_path.parent
    m = load_json(manifest_path)
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if m.get("campaignAuthorization", {}).get("authorized") is not False:
        failures.append({"code": "campaign_authorization_not_false", "field": "campaignAuthorization.authorized"})

    signed = m.get("humanAuthority", {}).get("signedAuthorization")
    if signed not in (None, "not_supplied"):
        failures.append({"code": "signed_human_authorization_supplied_or_ambiguous", "value": signed})

    label = str(m.get("humanAuthority", {}).get("label", "")).strip().lower()
    if label in FORBIDDEN_AUTH_LABELS and m.get("humanAuthority", {}).get("signedAuthorization") != "supplied_verified_external_signature":
        failures.append({"code": "label_misused_as_authorization", "label": label})

    for field in ("externalProviderPackage", "modelParameters"):
        status = m.get(field, {}).get("status")
        if status not in {"pending_not_verified", "not_supplied", "not_called"}:
            failures.append({"code": "provider_or_parameter_status_not_pending", "field": field, "status": status})

    for section in ("canonicalInputs", "generatedArtifacts", "toolchain", "evidenceInputs"):
        for item in m.get(section, []):
            raw_path = item.get("path")
            if not raw_path:
                failures.append({"code": "missing_path", "section": section, "item": item.get("id")})
                continue
            path = Path(raw_path)
            if not path.is_absolute():
                path = (root / path).resolve()
            if not path.exists():
                failures.append({"code": "missing_dependency", "section": section, "id": item.get("id"), "path": str(path)})
                continue
            expected = item.get("sha256")
            actual = sha256_path(path)
            if expected and actual != expected:
                failures.append({"code": "stale_or_tampered_dependency", "section": section, "id": item.get("id"), "path": str(path), "expected": expected, "actual": actual})
            expected_bytes = item.get("bytes")
            actual_bytes = path.stat().st_size
            if expected_bytes is not None and expected_bytes != actual_bytes:
                failures.append({"code": "size_mismatch", "section": section, "id": item.get("id"), "path": str(path), "expected": expected_bytes, "actual": actual_bytes})

    t1 = m.get("t1OutboundPayloads", [])
    if len(t1) != 7:
        failures.append({"code": "wrong_t1_payload_count", "expected": 7, "actual": len(t1)})
    for item in t1:
        payload_path = (root / item["payloadPath"]).resolve() if not Path(item["payloadPath"]).is_absolute() else Path(item["payloadPath"])
        if not payload_path.exists():
            failures.append({"code": "missing_t1_payload", "id": item.get("contractId"), "path": str(payload_path)})
            continue
        actual = sha256_path(payload_path)
        if item.get("sha256") != actual:
            failures.append({"code": "t1_payload_tampered", "id": item.get("contractId"), "expected": item.get("sha256"), "actual": actual})
        try:
            p = load_json(payload_path)
        except Exception as exc:
            failures.append({"code": "t1_payload_unreadable_json", "id": item.get("contractId"), "path": str(payload_path), "error": str(exc)})
            continue
        if p.get("sendStatus") != "not_sent" or p.get("providerCalled") is not False:
            failures.append({"code": "t1_payload_not_preparation_only", "id": item.get("contractId")})
        if p.get("providerParameters", {}).get("status") != "pending_not_verified":
            failures.append({"code": "t1_provider_params_not_pending", "id": item.get("contractId")})
        if p.get("inputPolicy", {}).get("onlyContractCommonInstructionMetadata") is not True:
            failures.append({"code": "t1_input_policy_not_strict", "id": item.get("contractId")})
        ops = p.get("contractMetadata", {}).get("operations", [])
        if len(ops) != 3:
            failures.append({"code": "t1_contract_not_three_ops", "id": item.get("contractId"), "actual": len(ops)})
        if p.get("scenarioBudget", {}).get("maxScenariosPerOperation") != 12:
            failures.append({"code": "t1_budget_not_12_per_operation", "id": item.get("contractId")})

    readiness = m.get("readinessMatrix", {})
    if readiness.get("T3", {}).get("overall") != "blocked":
        failures.append({"code": "t3_not_blocked_despite_missing_authority_or_executable_mapping"})
    if m.get("overallStatus") != "blocked_pre_campaign_not_ready_to_execute":
        failures.append({"code": "overall_status_not_blocked"})

    return {"ok": not failures, "manifest": str(manifest_path), "failures": failures, "warnings": warnings}


def self_test(manifest_path: Path) -> dict[str, Any]:
    base = verify(manifest_path)
    tests: list[dict[str, Any]] = [{"name": "base_manifest", "ok": base["ok"], "result": base}]
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        shutil.copytree(manifest_path.parent, tmp / "pkg")
        mp = tmp / "pkg" / manifest_path.name
        m = load_json(mp)
        # missing dependency detection
        first_art = m["generatedArtifacts"][0]
        target = tmp / "pkg" / first_art["path"]
        target.unlink()
        mp.write_text(json.dumps(m, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        r = verify(mp)
        tests.append({"name": "detect_missing_dependency", "ok": any(f["code"] == "missing_dependency" for f in r["failures"]), "result": r})
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        shutil.copytree(manifest_path.parent, tmp / "pkg")
        mp = tmp / "pkg" / manifest_path.name
        m = load_json(mp)
        payload_rel = m["t1OutboundPayloads"][0]["payloadPath"]
        (tmp / "pkg" / payload_rel).write_text("tampered", encoding="utf-8")
        r = verify(mp)
        tests.append({"name": "detect_tamper", "ok": any(f["code"] == "t1_payload_tampered" for f in r["failures"]), "result": r})
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        shutil.copytree(manifest_path.parent, tmp / "pkg")
        mp = tmp / "pkg" / manifest_path.name
        m = load_json(mp)
        m["humanAuthority"]["label"] = "approved"
        mp.write_text(json.dumps(m, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        r = verify(mp)
        tests.append({"name": "reject_label_as_authorization", "ok": any(f["code"] == "label_misused_as_authorization" for f in r["failures"]), "result": r})
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        shutil.copytree(manifest_path.parent, tmp / "pkg")
        mp = tmp / "pkg" / manifest_path.name
        m = load_json(mp)
        first_art = m["generatedArtifacts"][0]
        target = tmp / "pkg" / first_art["path"]
        target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        r = verify(mp)
        tests.append({"name": "detect_stale_hash", "ok": any(f["code"] == "stale_or_tampered_dependency" for f in r["failures"]), "result": r})
    return {"ok": all(t["ok"] for t in tests), "tests": tests}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    result = self_test(ns.manifest) if ns.self_test else verify(ns.manifest)
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

EXPECTED_COUNTS = {"T1": 88, "T2": 5868, "T3": 394, "T4": 6350}
EXPECTED_AMENDED = {
    "id": "coverage-runner-v3",
    "old": {"sha256": "7af57b8245e3fba4684a435541e812edbfb8fbec889198aff52c8cf8c35e7fbf", "bytes": 31406},
    "new": {"sha256": "cd2f4dfad9efe7e5258a42a3e24d7b66f94c2bc06437b8047ec589b483cfeef8", "bytes": 36798},
}


def fail(msg: str) -> None:
    print(json.dumps({"ok": False, "error": msg}, indent=2, ensure_ascii=False))
    raise SystemExit(1)


def pin(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def _check_pin(label: str, expected: dict[str, object], failures: list[str]) -> None:
    p = Path(str(expected.get("path", "")))
    if not p.exists():
        failures.append(f"missing source {label}: {p}")
        return
    actual = pin(p)
    if actual["sha256"] != expected.get("sha256"):
        failures.append(f"sha256 mismatch {label}: {actual['sha256']} != {expected.get('sha256')}")
    if actual["bytes"] != expected.get("bytes"):
        failures.append(f"bytes mismatch {label}: {actual['bytes']} != {expected.get('bytes')}")


def verify(config_path: Path) -> dict[str, object]:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    if cfg.get("kind") != "aws-carddemo-p3-campaign-configuration-v3-executable-preparation":
        failures.append("kind must be v3 executable preparation")
    auth = cfg.get("authorization", {})
    if auth.get("campaignAuthorized") is not False:
        failures.append("campaignAuthorized must be boolean false; user authorization is separate from campaignReady")
    if cfg.get("campaignReady") is not False:
        failures.append("campaignReady must be boolean false in config; final handoff computes readiness")
    if auth.get("officialCampaignsStarted") is not False:
        failures.append("officialCampaignsStarted must be boolean false")
    if auth.get("externalT1SendAuthorized") is not False:
        failures.append("externalT1SendAuthorized must be boolean false for this handoff")
    if auth.get("userFullTestsAuthorizationText") != "Pode seguir com toda a fase de testes ate o fim":
        failures.append("explicit user full-tests authorization text missing or changed")

    amendments = cfg.get("versionNotes", {}).get("qualifiedStalePinsFound")
    if amendments != 1:
        failures.append("qualifiedStalePinsFound must be exactly 1")
    source_mismatches = 0
    for item in cfg.get("sources", []):
        before = len(failures)
        _check_pin(str(item.get("id")), item, failures)
        source_mismatches += max(0, len(failures) - before)
    coverage = [item for item in cfg.get("sources", []) if item.get("id") == EXPECTED_AMENDED["id"]]
    if len(coverage) != 1:
        failures.append("coverage-runner-v3 source pin must occur exactly once")
    else:
        row = coverage[0]
        if row.get("sha256") != EXPECTED_AMENDED["new"]["sha256"] or row.get("bytes") != EXPECTED_AMENDED["new"]["bytes"]:
            failures.append("coverage-runner-v3 amended pin does not match reviewed current code")

    contract_block = cfg.get("contracts", {})
    contracts = contract_block.get("contracts", [])
    if contract_block.get("count") != 7 or len(contracts) != 7:
        failures.append("contract count must be exactly 7")
    op_total = sum(c.get("operationCount", 0) for c in contracts)
    if contract_block.get("operationsTotal") != 21 or op_total != 21:
        failures.append("operation count must be exactly 21")
    for c in contracts:
        if c.get("operationCount") != len(c.get("operations", [])):
            failures.append(f"operationCount mismatch for {c.get('contractId')}")
        _check_pin(f"contract source {c.get('contractId')}", c.get("source", {}), failures)

    t1 = cfg.get("t1DecisionPackage", {}).get("localPackageAlreadyExists", {}).get("payloads", [])
    if len(t1) != 7:
        failures.append("T1 payload count must be exactly 7")
    for row in t1:
        if row.get("sendStatus") != "not_sent" or row.get("providerCalled") is not False:
            failures.append(f"T1 payload is not local-only: {row.get('contractId')}")
        _check_pin(f"T1 payload {row.get('contractId')}", row.get("payload", {}), failures)
    for fx in cfg.get("fixturesCandidates", {}).get("fixtures", []):
        if fx.get("status") == "official" or fx.get("notOfficial") is not True:
            failures.append(f"fixture promoted without review: {fx.get('fixtureId')}")

    freeze = cfg.get("freezePackage", {})
    freeze_path = Path(str(freeze.get("path", "")))
    if freeze_path.name != "campaign-freeze-package-v3":
        failures.append("freeze package must be v3")
    if freeze.get("counts") != EXPECTED_COUNTS:
        failures.append(f"freeze counts must be {EXPECTED_COUNTS}")
    if freeze.get("expectedTotalCases") != sum(EXPECTED_COUNTS.values()):
        failures.append("freeze total must be 12700")
    _check_pin("freeze-v3 manifest", freeze.get("manifest", {}), failures)
    _check_pin("freeze-v3 verification", freeze.get("verification", {}), failures)
    if freeze_path.exists():
        v = json.loads((freeze_path / "VERIFICATION.json").read_text(encoding="utf-8"))
        if v.get("counts") != EXPECTED_COUNTS or v.get("t3GuardNotTrueRemaining") != [] or v.get("t4GuardNotTrueRemaining") != []:
            failures.append("freeze-v3 verification does not prove guard-clean counts")

    amendment_path = config_path.parent / "CONFIG-AMENDMENT-v3.json"
    if not amendment_path.exists():
        failures.append("missing CONFIG-AMENDMENT-v3.json")
        amendment_count = 0
    else:
        amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
        rows = amendment.get("qualifiedStalePinsFound", [])
        amendment_count = len(rows)
        if amendment_count != 1 or rows[0].get("id") != EXPECTED_AMENDED["id"]:
            failures.append("amendment must document exactly coverage-runner-v3")
        if amendment_count == 1:
            row = rows[0]
            if row.get("old", {}).get("sha256") != EXPECTED_AMENDED["old"]["sha256"] or row.get("old", {}).get("bytes") != EXPECTED_AMENDED["old"]["bytes"]:
                failures.append("amendment old coverage pin mismatch")
            if row.get("new", {}).get("sha256") != EXPECTED_AMENDED["new"]["sha256"] or row.get("new", {}).get("bytes") != EXPECTED_AMENDED["new"]["bytes"]:
                failures.append("amendment new coverage pin mismatch")

    if failures:
        fail("; ".join(failures))
    return {
        "ok": True,
        "config": str(config_path.resolve()),
        "contracts": len(contracts),
        "operations": op_total,
        "official_campaigns_started": auth.get("officialCampaignsStarted"),
        "provider_calls_allowed_by_config": auth.get("externalT1SendAuthorized"),
        "t1_payloads": len(t1),
        "sources_checked": len(cfg.get("sources", [])),
        "source_mismatches": source_mismatches,
        "fixtures_candidate_not_official": len(cfg.get("fixturesCandidates", {}).get("fixtures", [])),
        "freeze_package": freeze_path.name,
        "freeze_counts": freeze.get("counts"),
        "amendments": amendment_count,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        fail("usage: verify_campaign_config_v3.py campaign-config-v3.json")
    print(json.dumps(verify(Path(sys.argv[1])), indent=2, ensure_ascii=False, sort_keys=True))

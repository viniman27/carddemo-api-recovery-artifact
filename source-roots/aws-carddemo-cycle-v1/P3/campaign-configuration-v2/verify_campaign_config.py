#!/usr/bin/env python3
import json, hashlib, sys
from pathlib import Path


def fail(msg):
    print(json.dumps({"ok": False, "error": msg}, indent=2))
    raise SystemExit(1)


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(config_path: Path):
    cfg=json.loads(config_path.read_text())
    auth=cfg.get("authorization", {})
    if auth.get("campaignAuthorized") is not False:
        fail("campaignAuthorized must be boolean false; labels are not authorization")
    if auth.get("officialCampaignsStarted") is not False:
        fail("officialCampaignsStarted must be boolean false")
    if auth.get("externalT1SendAuthorized") is not False:
        fail("externalT1SendAuthorized must be boolean false before user confirmation")
    failures=[]
    for item in cfg.get("sources", []):
        p=Path(item["path"])
        if not p.exists():
            failures.append(f"missing source {item['id']}: {p}")
            continue
        data=p.read_bytes()
        actual=hashlib.sha256(data).hexdigest()
        if actual != item.get("sha256"):
            failures.append(f"sha256 mismatch {item['id']}: {actual} != {item.get('sha256')}")
        if len(data) != item.get("bytes"):
            failures.append(f"bytes mismatch {item['id']}: {len(data)} != {item.get('bytes')}")
    contract_block=cfg.get("contracts", {})
    contracts=contract_block.get("contracts", [])
    if contract_block.get("count") != 7 or len(contracts) != 7:
        failures.append("contract count must be exactly 7")
    op_total=sum(c.get("operationCount", 0) for c in contracts)
    if contract_block.get("operationsTotal") != 21 or op_total != 21:
        failures.append("operation count must be exactly 21")
    for c in contracts:
        if c.get("operationCount") != len(c.get("operations", [])):
            failures.append(f"operationCount mismatch for {c.get('contractId')}")
        src=c.get("source", {})
        p=Path(src.get("path", ""))
        if not p.exists():
            failures.append(f"missing contract source {c.get('contractId')}")
        else:
            data=p.read_bytes()
            if hashlib.sha256(data).hexdigest()!=src.get("sha256") or len(data)!=src.get("bytes"):
                failures.append(f"contract source pin mismatch {c.get('contractId')}")
    t1=cfg.get("t1DecisionPackage", {}).get("localPackageAlreadyExists", {}).get("payloads", [])
    if len(t1) != 7:
        failures.append("T1 payload count must be exactly 7")
    for row in t1:
        if row.get("sendStatus") != "not_sent" or row.get("providerCalled") is not False:
            failures.append(f"T1 payload is not local-only: {row.get('contractId')}")
        payload=row.get("payload", {})
        p=Path(payload.get("path", ""))
        if not p.exists():
            failures.append(f"missing T1 payload {row.get('contractId')}")
        else:
            data=p.read_bytes()
            if hashlib.sha256(data).hexdigest()!=payload.get("sha256") or len(data)!=payload.get("bytes"):
                failures.append(f"T1 payload pin mismatch {row.get('contractId')}")
    for fx in cfg.get("fixturesCandidates", {}).get("fixtures", []):
        if fx.get("status") == "official" or fx.get("notOfficial") is not True:
            failures.append(f"fixture promoted without review: {fx.get('fixtureId')}")
    if failures:
        fail("; ".join(failures))
    report={"ok": True,"contracts": len(contracts),"operations": op_total,"official_campaigns_started": auth.get("officialCampaignsStarted"),"provider_calls_allowed_by_config": auth.get("externalT1SendAuthorized"),"t1_payloads": len(t1),"sources_checked": len(cfg.get("sources", [])),"fixtures_candidate_not_official": len(cfg.get("fixturesCandidates", {}).get("fixtures", []))}
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    if len(sys.argv)!=2:
        fail("usage: verify_campaign_config.py campaign-config-v2.json")
    verify(Path(sys.argv[1]))

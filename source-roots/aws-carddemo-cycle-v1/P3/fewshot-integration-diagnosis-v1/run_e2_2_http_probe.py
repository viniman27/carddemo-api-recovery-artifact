#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, RefResolver

ROOT = Path(__file__).resolve().parent
CYCLE = ROOT / "isolated-cycle" / "aws-carddemo-cycle-v1"
P2C = CYCLE / "P2c-few-shot"
REGISTRY = CYCLE / "P3" / "technical-packages-v3-argument" / "registry.json"
sys.path.insert(0, str(P2C))
os.environ["P2B_FIXTURE_REGISTRY"] = str(REGISTRY)
import p2c_facade  # noqa: E402


def validate_response(contract_id: str, track: str, status: int, body: dict) -> dict:
    spec = yaml.safe_load(p2c_facade.CONTRACTS[contract_id].original_path.read_text())
    path = p2c_facade.CONTRACTS[contract_id].paths[track]
    response = spec["paths"][path]["post"]["responses"][str(status)]
    if "$ref" in response:
        cur = spec
        for part in response["$ref"].removeprefix("#/").split("/"):
            cur = cur[part]
        response = cur
    schema = response["content"]["application/json"]["schema"]
    errors = [e.message for e in Draft202012Validator(schema, resolver=RefResolver.from_schema(spec)).iter_errors(body)]
    return {"ok": not errors, "errors": errors, "statusDocumented": str(status) in spec["paths"][path]["post"]["responses"]}


def file_meta(path: Path) -> dict:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main() -> None:
    rows = []
    for track in ["posting", "reporting"]:
        req = p2c_facade.sample_request("E2-2", track)
        status, body, ev = p2c_facade.http_roundtrip("E2-2", track, req)
        audit = json.loads(Path(ev["p2bAuditPath"]).read_text())
        rows.append({
            "track": track,
            "status": status,
            "requestSha256": hashlib.sha256(json.dumps(req, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "responseSha256": ev["responseRawSha256"],
            "schema": validate_response("E2-2", track, status, body),
            "body": body,
            "p2bAuditPath": ev["p2bAuditPath"],
            "reachedCobol": audit["RESP"].get("reached_cobol"),
            "programExit": audit["RESP"].get("program_exit"),
            "failureEvents": audit.get("FAIL", {}).get("events", []),
            "programStdout": audit.get("CAP", {}).get("program_stdout"),
            "programStderr": audit.get("CAP", {}).get("program_stderr"),
        })
    report = {
        "kind": "fewshot-e2-2-http-diagnosis-probe",
        "scope": "technical HTTP probe against isolated copy with copied-current fixture package; not campaign/oracle",
        "registry": file_meta(REGISTRY),
        "facade": file_meta(P2C / "p2c_facade.py"),
        "contract": file_meta(CYCLE / "collection-01" / "E2-2" / "response-original.txt"),
        "rows": rows,
    }
    out = ROOT / "e2_2_http_probe.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"out": str(out), "rows": [{"track": r["track"], "status": r["status"], "schemaOk": r["schema"]["ok"], "reachedCobol": r["reachedCobol"], "programExit": r["programExit"]} for r in rows]}, indent=2))


if __name__ == "__main__":
    main()

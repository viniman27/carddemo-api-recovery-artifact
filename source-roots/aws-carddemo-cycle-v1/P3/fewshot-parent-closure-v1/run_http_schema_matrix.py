#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, RefResolver

CYCLE = Path(__file__).resolve().parents[2]
P2C = CYCLE / "P2c-few-shot"
OUT = CYCLE / "P3" / "fewshot-parent-closure-v1" / "http-schema-matrix"
RUNS = OUT / "runs"
OUTPUTS = OUT / "outputs"
PY = CYCLE / "P2a" / ".venv" / "bin" / "python"
if not PY.exists():
    PY = Path(sys.executable)

sys.path.insert(0, str(P2C))
import p2c_facade  # noqa: E402


def _resolve_ref(spec: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    if "$ref" not in node:
        return node
    cur: Any = spec
    for part in node["$ref"].removeprefix("#/").split("/"):
        cur = cur[part]
    return cur


def validate_response(contract_id: str, track: str, status: int, body: dict[str, Any]) -> list[str]:
    spec = yaml.safe_load(p2c_facade.CONTRACTS[contract_id].original_path.read_text())
    operation = p2c_facade.CONTRACTS[contract_id].paths[track]
    response = _resolve_ref(spec, spec["paths"][operation]["post"]["responses"][str(status)])
    schema = response.get("content", {}).get("application/json", {}).get("schema", {}) or {"type": "object"}
    validator = Draft202012Validator(schema, resolver=RefResolver.from_schema(spec))
    return [e.message for e in sorted(validator.iter_errors(body), key=lambda e: [str(p) for p in e.path])]


def run_one(contract_id: str, track: str) -> dict[str, Any]:
    contract_out = OUTPUTS / contract_id / track
    contract_runs = RUNS / contract_id / track
    contract_out.mkdir(parents=True, exist_ok=True)
    contract_runs.mkdir(parents=True, exist_ok=True)
    port_file = contract_out / "server.port"
    code = (
        "from pathlib import Path; import sys; "
        f"sys.path.insert(0, {str(P2C)!r}); import p2c_facade; "
        f"p2c_facade.RUNS=Path({str(contract_runs)!r}); "
        f"p2c_facade.OUTPUTS=Path({str(contract_out)!r}); "
        f"p2c_facade.serve(Path({str(port_file)!r}), {contract_id!r})"
    )
    proc = subprocess.Popen([str(PY), "-c", code], cwd=P2C, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    lifecycle: dict[str, Any] = {"pid": proc.pid}
    try:
        for _ in range(200):
            if port_file.exists():
                break
            if proc.poll() is not None:
                raise RuntimeError(f"server exited early rc={proc.returncode}")
            time.sleep(0.05)
        if not port_file.exists():
            raise RuntimeError("server port file was not created")
        port = int(port_file.read_text())
        request_body = p2c_facade.sample_request(contract_id, track)
        request_raw = json.dumps(request_body, sort_keys=True, separators=(",", ":")).encode()
        url = f"http://127.0.0.1:{port}{p2c_facade.CONTRACTS[contract_id].paths[track]}"
        req = urllib.request.Request(url, data=json.dumps(request_body).encode(), headers={"content-type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                response_raw = resp.read(); status = resp.status
        except urllib.error.HTTPError as exc:
            status = exc.code; response_raw = exc.read()
        body = json.loads(response_raw)
        errors = validate_response(contract_id, track, status, body)
        invocations = contract_out / "http-invocations.jsonl"
        latest = None
        if invocations.exists():
            rows = [json.loads(line) for line in invocations.read_text().splitlines() if line.strip()]
            latest = rows[-1] if rows else None
        p2b_audit_path = latest.get("p2bAuditPath") if latest else None
        p2b_reached = None
        p2b_events = []
        program_exit = None
        if p2b_audit_path and Path(p2b_audit_path).exists():
            audit = json.loads(Path(p2b_audit_path).read_text())
            p2b_reached = audit.get("RESP", {}).get("reached_cobol")
            program_exit = audit.get("RESP", {}).get("program_exit")
            p2b_events = audit.get("FAIL", {}).get("events", [])
        preconditions = [e for e in p2b_events if e.get("kind") == "cobol_precondition_failure"]
        transport_failed = status in {400, 404, 503} or bool(errors)
        return {
            "contractId": contract_id,
            "track": track,
            "operation": p2c_facade.CONTRACTS[contract_id].paths[track],
            "status": status,
            "schemaValid": not errors,
            "schemaErrors": errors,
            "transportFailed": transport_failed,
            "fixturePrecondition": bool(preconditions),
            "preconditions": preconditions,
            "reachedCobol": p2b_reached,
            "programExit": program_exit,
            "requestSha256": hashlib.sha256(request_raw).hexdigest(),
            "responseSha256": hashlib.sha256(response_raw).hexdigest(),
            "auditPath": latest.get("auditPath") if latest else None,
            "p2bAuditPath": p2b_audit_path,
        }
    except Exception as exc:
        return {
            "contractId": contract_id,
            "track": track,
            "operation": p2c_facade.CONTRACTS[contract_id].paths[track],
            "blocked": True,
            "error": repr(exc),
            "schemaValid": False,
            "transportFailed": True,
        }
    finally:
        proc.terminate()
        try:
            out, err = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill(); out, err = proc.communicate()
        lifecycle.update({"returncode": proc.returncode, "stdout": out, "stderr": err})
        (contract_out / "server-lifecycle.json").write_text(json.dumps(lifecycle, indent=2) + "\n")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [run_one(cid, track) for cid in sorted(p2c_facade.CONTRACTS) for track in p2c_facade.TRACKS]
    counts = {
        "total": len(rows),
        "schemaValid": sum(1 for r in rows if r.get("schemaValid")),
        "schemaInvalid": sum(1 for r in rows if not r.get("schemaValid")),
        "transportFailed": sum(1 for r in rows if r.get("transportFailed")),
        "fixturePrecondition": sum(1 for r in rows if r.get("fixturePrecondition")),
        "blocked": sum(1 for r in rows if r.get("blocked")),
        "http500": sum(1 for r in rows if r.get("status") == 500),
        "http200": sum(1 for r in rows if r.get("status") == 200),
    }
    contract_hashes = {cid: p2c_facade.sha256(c.original_path) for cid, c in sorted(p2c_facade.CONTRACTS.items())}
    report = {
        "kind": "fewshot-parent-closure-http-schema-matrix",
        "runner": str(Path(__file__).relative_to(CYCLE)),
        "p2cFacadeSha256": p2c_facade.sha256(P2C / "p2c_facade.py"),
        "contractHashes": contract_hashes,
        "counts": counts,
        "overallPassed": counts["total"] == 9 and counts["schemaInvalid"] == 0 and counts["transportFailed"] == 0 and counts["blocked"] == 0,
        "note": "Documented 500 responses caused by fixture/precondition events are counted separately and not as transport failures when schema-valid.",
        "results": rows,
    }
    target = OUT / "http-schema-matrix-report.json"
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["overallPassed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

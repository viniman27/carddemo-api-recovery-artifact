#!/usr/bin/env python3
"""Validate P2c few-shot responses against each original contract schema."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, RefResolver

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "outputs" / "smoke-all-report.json"

TRACK_TO_METHOD = {"posting": "post", "interest": "post", "reporting": "post"}


def load_audit(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def schema_for(spec: dict[str, Any], operation: str, status: int) -> dict[str, Any]:
    responses = spec["paths"][operation]["post"]["responses"]
    content = responses[str(status)].get("content", {}).get("application/json", {})
    return content.get("schema", {}) or {"type": "object"}


def validate_response(contract_path: Path, operation: str, status: int, body: dict[str, Any]) -> list[str]:
    spec = yaml.safe_load(contract_path.read_text())
    schema = schema_for(spec, operation, status)
    resolver = RefResolver.from_schema(spec)
    validator = Draft202012Validator(schema, resolver=resolver)
    return [error.message for error in sorted(validator.iter_errors(body), key=lambda e: [str(p) for p in e.path])]


def main() -> int:
    report = json.loads(REPORT.read_text())
    cases = []
    for result in report["results"]:
        audit = load_audit(result["auditPath"])
        contract_path = Path(audit["contractOriginal"])
        errors = validate_response(contract_path, result["operation"], result["status"], audit["response"])
        cases.append({
            "contractId": result["contractId"],
            "track": result["track"],
            "operation": result["operation"],
            "status": result["status"],
            "contractOriginal": str(contract_path),
            "contractOriginalSha256": audit["contractOriginalSha256"],
            "auditPath": result["auditPath"],
            "p2bAuditPath": result["p2bAuditPath"],
            "valid": not errors,
            "errors": errors,
        })
    out = {
        "kind": "p2c-few-shot-jsonschema-validation",
        "validator": "jsonschema.Draft202012Validator via P2a virtualenv",
        "smokeReport": str(REPORT),
        "cases": cases,
        "overallPassed": all(c["valid"] for c in cases),
    }
    target = ROOT / "outputs" / "schema-validation-report.json"
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out["overallPassed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())

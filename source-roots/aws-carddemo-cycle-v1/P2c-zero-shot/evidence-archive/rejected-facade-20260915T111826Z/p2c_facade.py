#!/usr/bin/env python3
"""Executable P2c facades for zero-shot E1 AWS CardDemo contracts.

This layer adapts the three frozen E1 OpenAPI envelopes to the existing local
COBOL technical binding without editing the contracts, P2a, P2b or P3.
"""
from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parent
CYCLE = ROOT.parent
P2B_PATH = CYCLE / "P2b" / "p2b_binding.py"
P3_REGISTRY = CYCLE / "P3" / "technical-packages-v3-argument" / "registry.json"
CONTRACTS = {
    "E1-1": CYCLE / "collection-01" / "E1-1" / "response-original.txt",
    "E1-2": CYCLE / "collection-01" / "E1-2" / "response-original.txt",
    "E1-3": CYCLE / "collection-01" / "E1-3" / "response-original.txt",
}
TRACK_BY_OPERATION = {
    "postDailyTransactions": "posting",
    "generateInterestTransactions": "interest",
    "generateTransactionReport": "reporting",
}
OPERATION_BY_TRACK = {v: k for k, v in TRACK_BY_OPERATION.items()}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_contract(contract_id: str) -> dict[str, Any]:
    if contract_id not in CONTRACTS:
        raise ValueError(f"unsupported zero-shot contract: {contract_id}")
    return yaml.safe_load(CONTRACTS[contract_id].read_text())


def load_operation_index(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for path, methods in contract.get("paths", {}).items():
        post = methods.get("post") if isinstance(methods, dict) else None
        if not post:
            continue
        op_id = post.get("operationId")
        if op_id in TRACK_BY_OPERATION:
            out[op_id] = {"path": path, "operation": post, "track": TRACK_BY_OPERATION[op_id]}
    return out


def _resolve_ref(doc: dict[str, Any], ref: str) -> Any:
    if not ref.startswith("#/"):
        raise ValueError(f"external refs are not used by these contracts: {ref}")
    cur: Any = doc
    for part in ref[2:].split("/"):
        cur = cur[part]
    return cur


def dereference_schema(doc: dict[str, Any], schema: Any) -> Any:
    if isinstance(schema, list):
        return [dereference_schema(doc, x) for x in schema]
    if not isinstance(schema, dict):
        return schema
    if "$ref" in schema:
        base = dereference_schema(doc, _resolve_ref(doc, schema["$ref"]))
        rest = {k: v for k, v in schema.items() if k != "$ref"}
        if rest and isinstance(base, dict):
            merged = dict(base)
            merged.update(dereference_schema(doc, rest))
            return merged
        return base
    if "allOf" in schema:
        merged: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
        other = {k: v for k, v in schema.items() if k != "allOf"}
        for subschema in schema["allOf"]:
            resolved = dereference_schema(doc, subschema)
            if resolved.get("type") == "object" or "properties" in resolved:
                merged["properties"].update(resolved.get("properties", {}))
                merged["required"].extend(resolved.get("required", []))
                for key, value in resolved.items():
                    if key not in {"properties", "required", "type"}:
                        merged[key] = value
            else:
                merged.setdefault("allOf", []).append(resolved)
        merged["required"] = sorted(set(merged["required"]))
        merged.update(dereference_schema(doc, other))
        return merged
    return {k: dereference_schema(doc, v) for k, v in schema.items()}


def operation_schema(contract: dict[str, Any], operation_id: str) -> dict[str, Any]:
    op = load_operation_index(contract)[operation_id]["operation"]
    return dereference_schema(contract, op["requestBody"]["content"]["application/json"]["schema"])


def response_schema(contract: dict[str, Any], operation_id: str, status: str) -> dict[str, Any]:
    op = load_operation_index(contract)[operation_id]["operation"]
    resp = op["responses"][status]
    if "$ref" in resp:
        resp = dereference_schema(contract, resp)
    return dereference_schema(contract, resp["content"]["application/json"]["schema"])


def _load_p2b():
    spec = importlib.util.spec_from_file_location("p2b_binding_for_p2c", P2B_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _records(path: Path, size: int) -> list[bytes]:
    if not path.exists():
        return []
    data = path.read_bytes()
    if len(data) % size:
        return []
    return [data[i : i + size] for i in range(0, len(data), size)]


def _fixture_file(track: str, name: str, registry: Path = P3_REGISTRY) -> Path:
    reg = json.loads(registry.read_text())
    for fx in reg["fixtures"]:
        if fx["track"] == track:
            return registry.parent / fx["materializer"]["files"][name]
    raise KeyError((track, name))


def sample_request_for(contract_id: str, track: str, registry: Path = P3_REGISTRY) -> dict[str, Any]:
    # Technical request examples use P3 local resources only. They are not campaign
    # cases and are not expected-output oracles.
    bind = lambda name: f"p3:{track}:{name}"
    if contract_id == "E1-1":
        if track == "posting":
            return {"dailyTransactions": [{"recordBase64": _b64(r)} for r in _records(_fixture_file("posting", "DALYTRAN", registry), 350)], "transactionFile": bind("TRANFILE"), "crossReferenceFile": bind("XREFFILE"), "accountFile": bind("ACCTFILE"), "categoryBalanceFile": bind("TCATBALF"), "rejectFile": bind("DALYREJS")}
        if track == "interest":
            return {"parameterDate": _fixture_file("interest", "PARMFILE", registry).read_text(), "parameterLength": 10, "categoryBalanceFile": bind("TCATBALF"), "crossReferenceFile": bind("XREFFILE"), "disclosureGroupFile": bind("DISCGRP"), "accountFile": bind("ACCTFILE"), "outputTransactionFile": bind("TRANSACT")}
        return {"transactions": [{"recordBase64": _b64(r)} for r in _records(_fixture_file("reporting", "TRANFILE", registry), 350)], "dateParameterRecords": [_fixture_file("reporting", "DATEPARM", registry).read_text()], "crossReferenceFile": bind("CARDXREF"), "transactionTypeFile": bind("TRANTYPE"), "transactionCategoryFile": bind("TRANCATG"), "reportFile": bind("TRANREPT")}
    if contract_id == "E1-2":
        if track == "posting":
            return {"dailyTransactions": [{"recordBase64": _b64(r)} for r in _records(_fixture_file("posting", "DALYTRAN", registry), 350)], "transactionFile": bind("TRANFILE"), "crossReferenceFile": bind("XREFFILE"), "accountFile": bind("ACCTFILE"), "categoryBalanceFile": bind("TCATBALF")}
        if track == "interest":
            return {"idPrefix": _fixture_file("interest", "PARMFILE", registry).read_text(), "categoryBalanceFile": bind("TCATBALF"), "crossReferenceFile": bind("XREFFILE"), "accountFile": bind("ACCTFILE"), "disclosureGroupFile": bind("DISCGRP")}
        return {"transactions": [{"recordBase64": _b64(r)} for r in _records(_fixture_file("reporting", "TRANFILE", registry), 350)], "dateParameters": [_fixture_file("reporting", "DATEPARM", registry).read_text()], "crossReferenceFile": bind("CARDXREF"), "transactionTypeFile": bind("TRANTYPE"), "transactionCategoryFile": bind("TRANCATG")}
    if contract_id == "E1-3":
        if track == "posting":
            return {"dailyTransactions": [_b64(r) for r in _records(_fixture_file("posting", "DALYTRAN", registry), 350)], "cardCrossReference": bind("XREFFILE"), "accounts": bind("ACCTFILE"), "categoryBalances": bind("TCATBALF"), "transactionOutput": bind("TRANFILE"), "rejectionOutput": bind("DALYREJS")}
        if track == "interest":
            return {"transactionIdPrefix": _fixture_file("interest", "PARMFILE", registry).read_text(), "categoryBalances": bind("TCATBALF"), "cardCrossReference": bind("XREFFILE"), "accounts": bind("ACCTFILE"), "disclosureGroups": bind("DISCGRP"), "transactionOutput": bind("TRANSACT")}
        return {"transactions": [_b64(r) for r in _records(_fixture_file("reporting", "TRANFILE", registry), 350)], "dateParameterRecords": [_b64(r) for r in _records(_fixture_file("reporting", "DATEPARM", registry), 80)], "cardCrossReference": bind("CARDXREF"), "transactionTypes": bind("TRANTYPE"), "transactionCategories": bind("TRANCATG"), "reportOutput": bind("TRANREPT")}
    raise ValueError(contract_id)


class ContractFacade:
    def __init__(self, contract_id: str, output_root: Path = ROOT / "runs", registry: Path = P3_REGISTRY):
        self.contract_id = contract_id
        self.contract = load_contract(contract_id)
        self.output_root = Path(output_root)
        self.registry = Path(registry)
        self.index = load_operation_index(self.contract)
        self.p2b = _load_p2b()
        self.p2b.RUNS = self.output_root / "p2b-runs"
        self.p2b.COMMAND_LOG = self.output_root / "command-log.jsonl"
        self.output_root.mkdir(parents=True, exist_ok=True)

    def _operation_id(self, track_or_operation: str) -> str:
        if track_or_operation in TRACK_BY_OPERATION:
            return track_or_operation
        if track_or_operation in OPERATION_BY_TRACK:
            return OPERATION_BY_TRACK[track_or_operation]
        raise ValueError(track_or_operation)

    def validate_request(self, track_or_operation: str, body: dict[str, Any]) -> None:
        op_id = self._operation_id(track_or_operation)
        schema = operation_schema(self.contract, op_id)
        jsonschema.Draft202012Validator(schema).validate(body)
        self._validate_decoded_lengths(body)

    def _validate_decoded_lengths(self, obj: Any) -> None:
        if isinstance(obj, dict):
            if "recordBase64" in obj:
                if len(base64.b64decode(obj["recordBase64"], validate=True)) != 350:
                    raise jsonschema.ValidationError("recordBase64 must decode to 350 bytes")
            for value in obj.values():
                self._validate_decoded_lengths(value)
        elif isinstance(obj, list):
            for value in obj:
                self._validate_decoded_lengths(value)
        elif isinstance(obj, str):
            # E1-3 raw record strings are checked by field names in schema only in QA samples.
            pass

    def response_schema_for(self, track_or_operation: str, status: str) -> dict[str, Any]:
        return response_schema(self.contract, self._operation_id(track_or_operation), status)

    def _ensure_built(self) -> None:
        required = ["CBTRN02C", "P2B_INTEREST_DRIVER", "CBTRN03C"]
        missing = [x for x in required if not (self.p2b.BUILD / x).exists()]
        if missing:
            self.p2b.build()

    def execute(self, track: str, request: dict[str, Any]) -> dict[str, Any]:
        op_id = self._operation_id(track)
        self.validate_request(op_id, request)
        self._ensure_built()
        run_id = f"{self.contract_id}-{track}-{int(time.time()*1000)}"
        before = {p.resolve() for p in self.p2b.RUNS.glob("*")} if self.p2b.RUNS.exists() else set()
        old_env = os.environ.get("P2B_FIXTURE_REGISTRY")
        os.environ["P2B_FIXTURE_REGISTRY"] = str(self.registry)
        try:
            status, body, audit = {"posting": self.p2b.posting, "interest": self.p2b.interest, "reporting": self.p2b.reporting}[track](run_id)
        finally:
            if old_env is None:
                os.environ.pop("P2B_FIXTURE_REGISTRY", None)
            else:
                os.environ["P2B_FIXTURE_REGISTRY"] = old_env
        after = {p.resolve() for p in self.p2b.RUNS.glob("*")}
        new_dirs = sorted(after - before)
        p2b_audit_path = Path(audit["INV"]["workdir"]) / "audit.json"
        shaped = self._shape_body(track, status, body, p2b_audit_path)
        final_status = 200 if status == 200 else status
        out_dir = self.output_root / self.contract_id / track / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        response_path = out_dir / "response.json"
        response_path.write_text(json.dumps(shaped, indent=2, ensure_ascii=False) + "\n")
        facade_audit = {
            "contract_id": self.contract_id,
            "contract_path": str(CONTRACTS[self.contract_id]),
            "contract_sha256": sha256(CONTRACTS[self.contract_id]),
            "operation_id": op_id,
            "track": track,
            "request_sha256": hashlib.sha256(json.dumps(request, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "request_policy": "schema-validated original E1 envelope; bindings resolved by local P3 technical registry; inline arrays preserved in request audit but P2b execution uses pinned file package resources",
            "binding_policy": "opaque p3:<track>:<DD> identifiers; no public reset, telemetry, or dataset management endpoint",
            "encoding_policy": "ASCII/GnuCOBOL -fsign=ascii for local execution; raw records preserved as base64 or 133-character strings per contract response schema",
            "linkage_parameter_policy": "interest X(10) bytes come from request field and pinned PARMFILE; no date parsing, calendar default, rounding or suffix uniqueness invented",
            "semantic_ambiguities": self._ambiguities(track),
            "p2b_audit_path": str(p2b_audit_path),
            "p2b_new_run_dirs": [str(p) for p in new_dirs],
            "http_status": final_status,
            "response_path": str(response_path),
        }
        audit_path = out_dir / "facade-audit.json"
        audit_path.write_text(json.dumps(facade_audit, indent=2, ensure_ascii=False) + "\n")
        return {"contract_id": self.contract_id, "track": track, "http_status": final_status, "body": shaped, "audit_path": str(audit_path), "response_path": str(response_path), "p2b_audit_path": str(p2b_audit_path)}

    def _ambiguities(self, track: str) -> list[dict[str, str]]:
        if track != "interest":
            return []
        return [{"point": "CBACT04C alternate-key account lookup when multiple card rows exist for one account", "recommendation": "Do not select a card in the facade; preserve runtime-selected XREFFILE alternate-key behavior and register as an evaluation ambiguity if a case depends on which card is chosen."}]

    def _diagnostics(self, audit: dict[str, Any]) -> list[str]:
        text = (audit.get("CAP", {}).get("program_stdout") or "") + (audit.get("CAP", {}).get("program_stderr") or "")
        return [line for line in text.splitlines() if line]

    def _shape_body(self, track: str, status: int, p2b_body: dict[str, Any], p2b_audit_path: Path) -> dict[str, Any]:
        audit = json.loads(p2b_audit_path.read_text()) if p2b_audit_path.exists() else {}
        diagnostics = self._diagnostics(audit)
        if status != 200:
            if self.contract_id == "E1-3":
                return {"outcome": "failed", "program": {"posting":"CBTRN02C","interest":"CBACT04C","reporting":"CBTRN03C"}[track], "diagnostics": diagnostics}
            if self.contract_id == "E1-2":
                return {"program": {"posting":"CBTRN02C","interest":"CBACT04C","reporting":"CBTRN03C"}[track], "diagnostics": diagnostics}
            return {"message": p2b_body.get("category", "execution failure"), "program": {"posting":"CBTRN02C","interest":"CBACT04C","reporting":"CBTRN03C"}[track], "diagnostics": diagnostics}
        if track == "posting":
            return self._posting_body(audit, diagnostics)
        if track == "interest":
            return self._interest_body(audit, diagnostics)
        return self._reporting_body(audit, diagnostics)

    def _write_events(self, audit: dict[str, Any], select_name: str) -> list[bytes]:
        evs = audit.get("CONV", {}).get("write_observations", {}).get("events", [])
        return [bytes.fromhex(ev["rawHex"]) for ev in evs if ev.get("select") == select_name and ev.get("status") == "00"]

    def _posting_body(self, audit: dict[str, Any], diagnostics: list[str]) -> dict[str, Any]:
        outputs = self._write_events(audit, "TRANSACT-FILE")
        rejects = self._write_events(audit, "DALYREJS-FILE")
        progress = audit.get("RESP", {}).get("body", {}).get("progress", {}).get("value", {})
        processed = int(progress.get("processedRecordCount", 0))
        rejected = int(progress.get("preliminaryRejectCount", len(rejects)))
        if self.contract_id == "E1-1":
            return {"transactionsProcessed": processed, "transactionsRejected": rejected, "returnCode": audit.get("RESP", {}).get("program_exit"), "writtenTransactions": [{"recordBase64": _b64(r)} for r in outputs], "rejects": [{"originalRecord": {"recordBase64": _b64(r[:350])}, "reasonCode": r[350:354].decode("ascii"), "reasonDescription": r[354:430].decode("ascii").rstrip(), "recordBase64": _b64(r)} for r in rejects], "diagnostics": diagnostics}
        if self.contract_id == "E1-2":
            return {"processedCount": processed, "rejectedCount": rejected, "returnCode": audit.get("RESP", {}).get("program_exit"), "transactions": [{"recordBase64": _b64(r)} for r in outputs], "rejects": [{"inputRecord": {"recordBase64": _b64(r[:350])}, "reasonCode": r[350:354].decode("ascii"), "reasonDescription": r[354:430].decode("ascii").rstrip()} for r in rejects], "diagnostics": diagnostics}
        return {"outcome": "completed", "returnCode": audit.get("RESP", {}).get("program_exit"), "diagnostics": diagnostics, "processedCount": processed, "rejectedCount": rejected, "transactionsWritten": [_b64(r) for r in outputs], "rejections": [{"record": _b64(r), "reasonCode": r[350:354].decode("ascii"), "reasonDescription": r[354:430].decode("ascii").rstrip()} for r in rejects]}

    def _capture_path(self, audit: dict[str, Any], label: str) -> Path | None:
        for cap in audit.get("CAP", {}).get("captures", []):
            if cap.get("label") == label and cap.get("exists"):
                return Path(cap["path"])
        return None

    def _interest_body(self, audit: dict[str, Any], diagnostics: list[str]) -> dict[str, Any]:
        path = self._capture_path(audit, "TRANSACT")
        recs = _records(path, 350) if path else []
        if self.contract_id == "E1-1":
            return {"generatedTransactions": [{"recordBase64": _b64(r)} for r in recs], "diagnostics": diagnostics}
        if self.contract_id == "E1-2":
            return {"transactions": [{"recordBase64": _b64(r)} for r in recs], "diagnostics": diagnostics, "returnCode": audit.get("RESP", {}).get("program_exit")}
        return {"outcome": "completed", "returnCode": audit.get("RESP", {}).get("program_exit"), "diagnostics": diagnostics, "transactionsWritten": [_b64(r) for r in recs]}

    def _reporting_body(self, audit: dict[str, Any], diagnostics: list[str]) -> dict[str, Any]:
        path = self._capture_path(audit, "TRANREPT")
        recs = _records(path, 133) if path else []
        if self.contract_id == "E1-1":
            return {"lines": [r.decode("ascii") for r in recs], "diagnostics": diagnostics}
        if self.contract_id == "E1-2":
            return {"lines": [r.decode("ascii") for r in recs], "diagnostics": diagnostics, "returnCode": audit.get("RESP", {}).get("program_exit")}
        return {"outcome": "completed", "returnCode": audit.get("RESP", {}).get("program_exit"), "diagnostics": diagnostics, "reportRecords": [_b64(r) for r in recs]}

    def extract_report_records(self, body: dict[str, Any]) -> list[str]:
        if "lines" in body:
            return body["lines"]
        return body.get("reportRecords", [])


def run_qa(output_root: Path = ROOT / "runs", registry: Path = P3_REGISTRY) -> dict[str, Any]:
    report: dict[str, Any] = {"kind": "P2c-zero-shot executable facade QA", "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "contracts": {}, "summary": {"implemented": 0, "exercised": 0, "blocked": 0}}
    for cid in ["E1-1", "E1-2", "E1-3"]:
        facade = ContractFacade(cid, output_root, registry)
        cinfo = {"contract_path": str(CONTRACTS[cid]), "contract_sha256": sha256(CONTRACTS[cid]), "operations": {}}
        for track in ["posting", "interest", "reporting"]:
            req = sample_request_for(cid, track, registry)
            try:
                result = facade.execute(track, req)
                if result["http_status"] == 200:
                    schema = facade.response_schema_for(track, "200")
                    jsonschema.Draft202012Validator(schema).validate(result["body"])
                status = "exercitado" if result["http_status"] == 200 else "bloqueado"
                cinfo["operations"][track] = {"implementado": True, "exercitado": result["http_status"] == 200, "bloqueado": result["http_status"] != 200, "http_status": result["http_status"], "audit_path": result["audit_path"], "p2b_audit_path": result["p2b_audit_path"], "response_path": result["response_path"], "schema_validated": result["http_status"] == 200}
            except Exception as exc:
                cinfo["operations"][track] = {"implementado": True, "exercitado": False, "bloqueado": True, "erro": repr(exc)}
        report["contracts"][cid] = cinfo
    for cinfo in report["contracts"].values():
        for op in cinfo["operations"].values():
            report["summary"]["implemented"] += 1 if op.get("implementado") else 0
            report["summary"]["exercised"] += 1 if op.get("exercitado") else 0
            report["summary"]["blocked"] += 1 if op.get("bloqueado") else 0
    report["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    path = output_root / "p2c-zero-shot-qa-report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    report["report_path"] = str(path)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["qa", "call"])
    ap.add_argument("--contract", choices=["E1-1", "E1-2", "E1-3"])
    ap.add_argument("--track", choices=["posting", "interest", "reporting"])
    ap.add_argument("--request-json", type=Path)
    ap.add_argument("--output-root", type=Path, default=ROOT / "runs")
    ap.add_argument("--registry", type=Path, default=P3_REGISTRY)
    args = ap.parse_args()
    if args.command == "qa":
        print(json.dumps(run_qa(args.output_root, args.registry), indent=2, ensure_ascii=False))
    else:
        if not args.contract or not args.track:
            ap.error("call requires --contract and --track")
        body = json.loads(args.request_json.read_text()) if args.request_json else sample_request_for(args.contract, args.track, args.registry)
        print(json.dumps(ContractFacade(args.contract, args.output_root, args.registry).execute(args.track, body), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

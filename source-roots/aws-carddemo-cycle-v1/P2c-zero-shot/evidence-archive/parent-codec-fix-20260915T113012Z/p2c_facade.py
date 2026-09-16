#!/usr/bin/env python3
"""Executable P2c facades for zero-shot E1 AWS CardDemo contracts.

This adapter validates the frozen E1 OpenAPI envelopes, materializes the caller's
sequential records/linkage parameters into per-call local file packages, invokes
the existing read-only P2b COBOL binding, and exposes a real localhost HTTP
server on the contract paths.
"""
from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import http.server
import importlib.util
import json
import os
import shutil
import socketserver
import sys
import tempfile
import time
import urllib.error
import urllib.request
import warnings
from pathlib import Path
from typing import Any

import jsonschema
import yaml
from jsonschema.validators import validator_for

warnings.filterwarnings("ignore", category=DeprecationWarning, message="jsonschema.RefResolver is deprecated.*")

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
PROGRAMS = {"posting": "CBTRN02C", "interest": "CBACT04C", "reporting": "CBTRN03C"}
INPUT_DDS = {
    "posting": {"DALYTRAN"},
    "interest": {"PARMFILE"},
    "reporting": {"TRANFILE", "DATEPARM"},
}
P2B_REQUIRED = {
    "posting": {"ACCTFILE", "DALYTRAN", "TCATBALF", "TRANFILE", "XREFFILE"},
    "interest": {"ACCTFILE", "DISCGRP", "TCATBALF", "XREFFILE", "XREFFILE.1", "PARMFILE"},
    "reporting": {"CARDXREF", "DATEPARM", "TRANCATG", "TRANFILE", "TRANTYPE"},
}
OUTPUT_BINDING_FIELDS = {
    "E1-1": {"posting": {"rejectFile": "DALYREJS"}, "interest": {"outputTransactionFile": "TRANSACT"}, "reporting": {"reportFile": "TRANREPT"}},
    "E1-2": {"posting": {}, "interest": {}, "reporting": {}},
    "E1-3": {"posting": {"transactionOutput": "TRANFILE", "rejectionOutput": "DALYREJS"}, "interest": {"transactionOutput": "TRANSACT"}, "reporting": {"reportOutput": "TRANREPT"}},
}
BINDING_FIELDS = {
    "E1-1": {
        "posting": {"transactionFile": "TRANFILE", "crossReferenceFile": "XREFFILE", "accountFile": "ACCTFILE", "categoryBalanceFile": "TCATBALF", "rejectFile": "DALYREJS"},
        "interest": {"categoryBalanceFile": "TCATBALF", "crossReferenceFile": "XREFFILE", "disclosureGroupFile": "DISCGRP", "accountFile": "ACCTFILE", "outputTransactionFile": "TRANSACT"},
        "reporting": {"crossReferenceFile": "CARDXREF", "transactionTypeFile": "TRANTYPE", "transactionCategoryFile": "TRANCATG", "reportFile": "TRANREPT"},
    },
    "E1-2": {
        "posting": {"transactionFile": "TRANFILE", "crossReferenceFile": "XREFFILE", "accountFile": "ACCTFILE", "categoryBalanceFile": "TCATBALF"},
        "interest": {"categoryBalanceFile": "TCATBALF", "crossReferenceFile": "XREFFILE", "accountFile": "ACCTFILE", "disclosureGroupFile": "DISCGRP"},
        "reporting": {"crossReferenceFile": "CARDXREF", "transactionTypeFile": "TRANTYPE", "transactionCategoryFile": "TRANCATG"},
    },
    "E1-3": {
        "posting": {"cardCrossReference": "XREFFILE", "accounts": "ACCTFILE", "categoryBalances": "TCATBALF", "transactionOutput": "TRANFILE", "rejectionOutput": "DALYREJS"},
        "interest": {"categoryBalances": "TCATBALF", "cardCrossReference": "XREFFILE", "accounts": "ACCTFILE", "disclosureGroups": "DISCGRP", "transactionOutput": "TRANSACT"},
        "reporting": {"cardCrossReference": "CARDXREF", "transactionTypes": "TRANTYPE", "transactionCategories": "TRANCATG", "reportOutput": "TRANREPT"},
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bytes_sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
    cur: Any = doc
    for part in ref.removeprefix("#/").split("/"):
        cur = cur[part]
    return cur


def _resolve_response(contract: dict[str, Any], resp: dict[str, Any]) -> dict[str, Any]:
    if "$ref" in resp:
        return _resolve_ref(contract, resp["$ref"])
    return resp


def operation_schema(contract: dict[str, Any], operation_id: str) -> dict[str, Any]:
    op = load_operation_index(contract)[operation_id]["operation"]
    return op["requestBody"]["content"]["application/json"]["schema"]


def response_schema(contract: dict[str, Any], operation_id: str, status: str) -> dict[str, Any]:
    op = load_operation_index(contract)[operation_id]["operation"]
    resp = _resolve_response(contract, op["responses"][status])
    return resp["content"]["application/json"]["schema"]


def _validator(contract: dict[str, Any], schema: dict[str, Any]) -> Any:
    cls = validator_for(contract)
    cls.check_schema(contract)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        resolver = jsonschema.RefResolver.from_schema(contract)
    return cls(schema, resolver=resolver)


def _load_p2b():
    spec = importlib.util.spec_from_file_location("p2b_binding_for_p2c", P2B_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


class FixedRecordError(RuntimeError):
    pass


def _records(path: Path, size: int) -> list[bytes]:
    if not path.exists():
        raise FixedRecordError(f"missing fixed-record file: {path}")
    data = path.read_bytes()
    if len(data) % size:
        raise FixedRecordError(f"truncated fixed-record file: {path} has {len(data)} bytes, record size {size}")
    return [data[i : i + size] for i in range(0, len(data), size)]


def _ascii(s: str, width: int) -> bytes:
    data = s.encode("ascii")
    if len(data) > width:
        raise ValueError(f"field too long for PIC X({width}): {s!r}")
    return data.ljust(width, b" ")


def _num(s: str, width: int) -> bytes:
    data = str(s).encode("ascii")
    if len(data) > width:
        raise ValueError(f"numeric text too long for width {width}: {s!r}")
    return data.zfill(width)


def _amount(s: str, width: int = 11) -> bytes:
    text = str(s)
    neg = text.startswith("-")
    if neg:
        text = text[1:]
    digits = text.replace(".", "")
    if not digits.isdigit():
        raise ValueError(f"unsupported structured amount text: {s!r}")
    out = digits.zfill(width)
    if neg:
        out = "-" + out[1:]
    return out.encode("ascii")


def transaction_from_struct(obj: dict[str, Any]) -> bytes:
    txid = obj.get("transactionId", obj.get("id", ""))
    return b"".join([
        _ascii(txid, 16),
        _ascii(obj.get("typeCode", ""), 2),
        _num(obj.get("categoryCode", ""), 4),
        _ascii(obj.get("source", ""), 10),
        _ascii(obj.get("description", ""), 100),
        _amount(obj.get("amount", "0.00"), 11),
        _num(obj.get("merchantId", ""), 9),
        _ascii(obj.get("merchantName", ""), 50),
        _ascii(obj.get("merchantCity", ""), 50),
        _ascii(obj.get("merchantZip", obj.get("merchantPostalText", "")), 10),
        _ascii(obj.get("cardNumber", obj.get("cardReference", "")), 16),
        _ascii(obj.get("originalTimestamp", ""), 26),
        _ascii(obj.get("processingTimestamp", ""), 26),
        _ascii(obj.get("filler", ""), 20),
    ])


def tx_item_to_bytes(item: Any) -> bytes:
    if isinstance(item, str):
        data = base64.b64decode(item, validate=True)
    elif isinstance(item, dict) and "recordBase64" in item:
        data = base64.b64decode(item["recordBase64"], validate=True)
    elif isinstance(item, dict):
        data = transaction_from_struct(item)
    else:
        raise TypeError(f"unsupported transaction record item: {type(item).__name__}")
    if len(data) != 350:
        raise ValueError(f"transaction record must materialize to 350 bytes, got {len(data)}")
    return data


def date_item_to_bytes(item: Any, raw_b64: bool) -> bytes:
    data = base64.b64decode(item, validate=True) if raw_b64 else str(item).encode("ascii")
    if len(data) != 80:
        raise ValueError(f"DATEPARM record must materialize to 80 bytes, got {len(data)}")
    return data


def _load_registry_files(registry: Path) -> dict[tuple[str, str], Path]:
    data = json.loads(registry.read_text())
    mapping: dict[tuple[str, str], Path] = {}
    for fx in data["fixtures"]:
        track = fx["track"]
        for dd, rel in fx["materializer"]["files"].items():
            mapping[(track, dd)] = (registry.parent / rel).resolve()
    return mapping


def sample_request_for(contract_id: str, track: str, registry: Path = P3_REGISTRY) -> dict[str, Any]:
    mapping = _load_registry_files(registry)
    bind = lambda name: f"p3:{track}:{name}"
    def raw_records(dd: str, size: int) -> list[bytes]:
        return _records(mapping[(track, dd)], size)
    if contract_id == "E1-1":
        if track == "posting":
            return {"dailyTransactions": [{"recordBase64": _b64(r)} for r in raw_records("DALYTRAN", 350)], "transactionFile": bind("TRANFILE"), "crossReferenceFile": bind("XREFFILE"), "accountFile": bind("ACCTFILE"), "categoryBalanceFile": bind("TCATBALF"), "rejectFile": bind("DALYREJS")}
        if track == "interest":
            return {"parameterDate": mapping[(track, "PARMFILE")].read_text(), "parameterLength": 10, "categoryBalanceFile": bind("TCATBALF"), "crossReferenceFile": bind("XREFFILE"), "disclosureGroupFile": bind("DISCGRP"), "accountFile": bind("ACCTFILE"), "outputTransactionFile": bind("TRANSACT")}
        return {"transactions": [{"recordBase64": _b64(r)} for r in raw_records("TRANFILE", 350)], "dateParameterRecords": [mapping[(track, "DATEPARM")].read_text()], "crossReferenceFile": bind("CARDXREF"), "transactionTypeFile": bind("TRANTYPE"), "transactionCategoryFile": bind("TRANCATG"), "reportFile": bind("TRANREPT")}
    if contract_id == "E1-2":
        if track == "posting":
            return {"dailyTransactions": [{"recordBase64": _b64(r)} for r in raw_records("DALYTRAN", 350)], "transactionFile": bind("TRANFILE"), "crossReferenceFile": bind("XREFFILE"), "accountFile": bind("ACCTFILE"), "categoryBalanceFile": bind("TCATBALF")}
        if track == "interest":
            return {"idPrefix": mapping[(track, "PARMFILE")].read_text(), "categoryBalanceFile": bind("TCATBALF"), "crossReferenceFile": bind("XREFFILE"), "accountFile": bind("ACCTFILE"), "disclosureGroupFile": bind("DISCGRP")}
        return {"transactions": [{"recordBase64": _b64(r)} for r in raw_records("TRANFILE", 350)], "dateParameters": [mapping[(track, "DATEPARM")].read_text()], "crossReferenceFile": bind("CARDXREF"), "transactionTypeFile": bind("TRANTYPE"), "transactionCategoryFile": bind("TRANCATG")}
    if contract_id == "E1-3":
        if track == "posting":
            return {"dailyTransactions": [_b64(r) for r in raw_records("DALYTRAN", 350)], "cardCrossReference": bind("XREFFILE"), "accounts": bind("ACCTFILE"), "categoryBalances": bind("TCATBALF"), "transactionOutput": bind("TRANFILE"), "rejectionOutput": bind("DALYREJS")}
        if track == "interest":
            return {"transactionIdPrefix": mapping[(track, "PARMFILE")].read_text(), "categoryBalances": bind("TCATBALF"), "cardCrossReference": bind("XREFFILE"), "accounts": bind("ACCTFILE"), "disclosureGroups": bind("DISCGRP"), "transactionOutput": bind("TRANSACT")}
        return {"transactions": [_b64(r) for r in raw_records("TRANFILE", 350)], "dateParameterRecords": [_b64(r) for r in raw_records("DATEPARM", 80)], "cardCrossReference": bind("CARDXREF"), "transactionTypes": bind("TRANTYPE"), "transactionCategories": bind("TRANCATG"), "reportOutput": bind("TRANREPT")}
    raise ValueError(contract_id)


class ContractFacade:
    def __init__(self, contract_id: str, output_root: Path = ROOT / "runs", registry: Path = P3_REGISTRY):
        self.contract_id = contract_id
        self.contract = load_contract(contract_id)
        self.output_root = Path(output_root).resolve()
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
        _validator(self.contract, operation_schema(self.contract, op_id)).validate(body)
        self._validate_decoded_lengths(body)

    def _validate_decoded_lengths(self, obj: Any, key: str | None = None) -> None:
        if isinstance(obj, dict):
            if "recordBase64" in obj:
                if len(base64.b64decode(obj["recordBase64"], validate=True)) != 350:
                    raise jsonschema.ValidationError("recordBase64 must decode to 350 bytes")
            for k, value in obj.items():
                self._validate_decoded_lengths(value, k)
        elif isinstance(obj, list):
            for value in obj:
                self._validate_decoded_lengths(value, key)
        elif isinstance(obj, str):
            if key in {"dailyTransactions", "transactions"}:
                if len(base64.b64decode(obj, validate=True)) != 350:
                    raise jsonschema.ValidationError(f"{key} raw item must decode to 350 bytes")
            if key == "dateParameterRecords" and self.contract_id == "E1-3":
                if len(base64.b64decode(obj, validate=True)) != 80:
                    raise jsonschema.ValidationError("dateParameterRecords raw item must decode to 80 bytes")

    def response_schema_for(self, track_or_operation: str, status: str) -> dict[str, Any]:
        return response_schema(self.contract, self._operation_id(track_or_operation), status)

    def validate_response(self, track_or_operation: str, status: str, body: dict[str, Any]) -> None:
        _validator(self.contract, self.response_schema_for(track_or_operation, status)).validate(body)

    def _ensure_built(self) -> None:
        required = ["CBTRN02C", "P2B_INTEREST_DRIVER", "CBTRN03C", "io_TRANFILE", "io_ACCTFILE", "io_XREFFILE", "io_TCATBALF"]
        missing = [x for x in required if not (self.p2b.BUILD / x).exists()]
        if missing:
            raise RuntimeError(f"P2b build precondition missing: {missing}; P2c does not call P2b build")

    def _resolve_token(self, track: str, token: str) -> Path:
        if not isinstance(token, str):
            raise ValueError(f"binding token must be a string, got {type(token).__name__}")
        mapping = _load_registry_files(self.registry)
        allowed: dict[str, Path] = {f"p3:{t}:{dd}": path for (t, dd), path in mapping.items()}
        if token not in allowed:
            raise ValueError(f"unresolved local binding token: {token!r}")
        dd_track = token.split(":")[1]
        if dd_track != track:
            raise ValueError(f"binding token track mismatch: {token!r} for {track}")
        return allowed[token]

    def _materialize_request_package(self, track: str, request: dict[str, Any], run_id: str) -> tuple[Path, dict[str, Any]]:
        package = self.output_root / "request-packages" / run_id
        package.mkdir(parents=True, exist_ok=False)
        files: dict[str, dict[str, Any]] = {}
        sources: dict[str, Path] = {}
        bindings: dict[str, Any] = {}
        output_bindings: dict[str, Any] = {}

        # Resolve explicit request bindings into exact local files; do not accept prefixes or unknown tokens.
        for field, dd in BINDING_FIELDS[self.contract_id][track].items():
            if field not in request:
                continue
            token = request[field]
            if dd in OUTPUT_BINDING_FIELDS.get(self.contract_id, {}).get(track, {}).values() and dd not in P2B_REQUIRED[track]:
                output_bindings[dd] = {"field": field, "token": token, "policy": "output resource; P2b COBOL creates it in the invocation workdir"}
                continue
            source = self._resolve_token(track, token)
            sources[dd] = source
            bindings[dd] = {"field": field, "token": token, "sourcePath": str(source), "sourceSha256": sha256(source), "sourceBytes": source.stat().st_size}

        # Interest alternate-key sidecar is an implementation prerequisite tied to XREFFILE.
        if track == "interest" and "XREFFILE.1" not in sources:
            sources["XREFFILE.1"] = self._resolve_token(track, "p3:interest:XREFFILE.1")
            bindings["XREFFILE.1"] = {"field": "implicitAlternateIndexSidecar", "token": "p3:interest:XREFFILE.1", "sourcePath": str(sources["XREFFILE.1"]), "sourceSha256": sha256(sources["XREFFILE.1"]), "sourceBytes": sources["XREFFILE.1"].stat().st_size}

        # Request-owned sequential/linkage bytes override any pinned sample input.
        if track == "posting":
            data = b"".join(tx_item_to_bytes(item) for item in request.get("dailyTransactions", []))
            (package / "DALYTRAN").write_bytes(data)
            sources["DALYTRAN"] = package / "DALYTRAN"
        elif track == "interest":
            prefix = request.get({"E1-1": "parameterDate", "E1-2": "idPrefix", "E1-3": "transactionIdPrefix"}[self.contract_id])
            data = str(prefix).encode("ascii")
            if len(data) != 10:
                raise ValueError("interest linkage prefix must materialize to exactly 10 bytes")
            (package / "PARMFILE").write_bytes(data)
            sources["PARMFILE"] = package / "PARMFILE"
        elif track == "reporting":
            tx_field = "transactions"
            date_field = "dateParameterRecords" if self.contract_id in {"E1-1", "E1-3"} else "dateParameters"
            raw_dates = self.contract_id == "E1-3"
            tx_data = b"".join(tx_item_to_bytes(item) for item in request.get(tx_field, []))
            date_data = b"".join(date_item_to_bytes(item, raw_dates) for item in request.get(date_field, []))
            (package / "TRANFILE").write_bytes(tx_data)
            (package / "DATEPARM").write_bytes(date_data)
            sources["TRANFILE"] = package / "TRANFILE"
            sources["DATEPARM"] = package / "DATEPARM"
        else:
            raise ValueError(track)

        missing = sorted(P2B_REQUIRED[track] - set(sources))
        if missing:
            raise ValueError(f"request did not resolve required COBOL resources: {missing}")

        file_pins: dict[str, dict[str, Any]] = {}
        registry_files: dict[str, str] = {}
        for dd in sorted(P2B_REQUIRED[track]):
            src = sources[dd]
            dest = package / dd
            if src.resolve() != dest.resolve():
                shutil.copy2(src, dest)
            data = dest.read_bytes()
            file_pins[dd] = {"sha256": bytes_sha(data), "bytes": len(data)}
            registry_files[dd] = dd
            files[dd] = {"path": str(dest), "bytes": len(data), "sha256": bytes_sha(data), "requestOwned": dd in INPUT_DDS[track]}

        fixture = {
            "fixtureId": f"p2c-request-{run_id}",
            "track": track,
            "materializer": {"kind": "local_file_package", "files": registry_files, "filePins": file_pins},
            "provenance": {"class": "p2c-request-materialization", "officialFixture": False, "requestSha256": self._request_hash(request), "contractId": self.contract_id},
            "exposure": {"label": "technical-only", "notOracle": True, "notExtractionInput": True, "notPublicRequest": False},
            "reset": {"default": "fresh_dir_per_run", "statefulSequence": "not_used"},
        }
        fixture["contentSha256"] = self.p2b.fixture_descriptor_sha256(fixture)
        reg = {"kind": "p3-local-technical-fixture-selection", "status": "p2c_request_materialized_local_only", "fixtures": [fixture]}
        reg_path = package / "registry.json"
        reg_path.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n")
        evidence = {"package": str(package), "registry": str(reg_path), "files": files, "bindings": bindings, "output_bindings": output_bindings, "fixture_descriptor_sha256": fixture["contentSha256"]}
        (package / "materialization-audit.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
        return reg_path, evidence

    def _request_hash(self, request: dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(request, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def execute(self, track: str, request: dict[str, Any]) -> dict[str, Any]:
        op_id = self._operation_id(track)
        track = TRACK_BY_OPERATION[op_id]
        self.validate_request(op_id, request)
        self._ensure_built()
        run_id = f"{self.contract_id}-{track}-{int(time.time()*1000)}"
        reg_path, materialization = self._materialize_request_package(track, request, run_id)
        before = {p.resolve() for p in self.p2b.RUNS.glob("*")} if self.p2b.RUNS.exists() else set()
        old_env = os.environ.get("P2B_FIXTURE_REGISTRY")
        os.environ["P2B_FIXTURE_REGISTRY"] = str(reg_path)
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
        response_payload = {"contract_id": self.contract_id, "track": track, "body": shaped}
        response_path.write_text(json.dumps(response_payload, indent=2, ensure_ascii=False) + "\n")
        facade_audit = {
            "contract_id": self.contract_id,
            "contract_path": str(CONTRACTS[self.contract_id]),
            "contract_sha256": sha256(CONTRACTS[self.contract_id]),
            "operation_id": op_id,
            "track": track,
            "request_sha256": self._request_hash(request),
            "request_policy": "original E1 schema with refs validated by jsonschema; request arrays/linkage fields materialized into exact COBOL input bytes before invocation",
            "binding_policy": "opaque tokens resolved only by exact local preprovisioned map entries; unknown tokens fail; prefixes alone are never accepted",
            "encoding_policy": "request raw bytes are preserved; structured transaction records are fixed-width ASCII transport materializations with filler retained when supplied",
            "linkage_parameter_policy": "interest PARMFILE is exactly the ten request bytes; no date parsing, calendar normalization, rounding, suffix uniqueness or default substitution",
            "request_materialization": materialization,
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
        return [{"point": "CBACT04C alternate-key account lookup when multiple card rows exist for one account", "recommendation": "Do not select a card in the facade; preserve runtime-selected XREFFILE alternate-key behavior and record as ambiguity if a case depends on which card is chosen."}]

    def _diagnostics(self, audit: dict[str, Any]) -> list[str]:
        text = (audit.get("CAP", {}).get("program_stdout") or "") + (audit.get("CAP", {}).get("program_stderr") or "")
        return [line for line in text.splitlines() if line]

    def _shape_body(self, track: str, status: int, p2b_body: dict[str, Any], p2b_audit_path: Path) -> dict[str, Any]:
        audit = json.loads(p2b_audit_path.read_text()) if p2b_audit_path.exists() else {}
        diagnostics = self._diagnostics(audit)
        if status != 200:
            return self._failure_body(track, p2b_body, diagnostics)
        try:
            if track == "posting":
                return self._posting_body(audit, diagnostics)
            if track == "interest":
                return self._interest_body(audit, diagnostics)
            return self._reporting_body(audit, diagnostics)
        except FixedRecordError as exc:
            return self._failure_body(track, {"category": "technical_failure", "detail": str(exc)}, diagnostics)

    def _failure_body(self, track: str, p2b_body: dict[str, Any], diagnostics: list[str]) -> dict[str, Any]:
        if self.contract_id == "E1-3":
            return {"outcome": "failed", "program": PROGRAMS[track], "diagnostics": diagnostics}
        if self.contract_id == "E1-2":
            return {"program": PROGRAMS[track], "diagnostics": diagnostics}
        return {"message": p2b_body.get("category", "execution failure"), "program": PROGRAMS[track], "diagnostics": diagnostics}

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


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


class FacadeServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 0, output_root: Path = ROOT / "runs", registry: Path = P3_REGISTRY):
        self.output_root = Path(output_root).resolve()
        self.registry = Path(registry)
        routes = {}
        for cid in CONTRACTS:
            for op_id, meta in load_operation_index(load_contract(cid)).items():
                routes[f"/{cid}{meta['path']}"] = (cid, meta["track"])
        self.routes = routes
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            server_version = "P2cZeroShot/1"
            def do_POST(self) -> None:
                n = int(self.headers.get("content-length", "0"))
                raw = self.rfile.read(n)
                log = {"method": "POST", "path": self.path, "request_body_sha256": bytes_sha(raw), "bytes": len(raw), "time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
                try:
                    if self.path not in outer.routes:
                        self._reply(404, {"error": "unknown route"}); return
                    cid, track = outer.routes[self.path]
                    log.update({"contract_id": cid, "track": track})
                    body = json.loads(raw or b"{}")
                    result = ContractFacade(cid, outer.output_root, outer.registry).execute(track, body)
                    log.update({"http_status": result["http_status"], "audit_path": result["audit_path"]})
                    self._reply(result["http_status"], {"contract_id": cid, "track": track, "body": result["body"], "audit_path": result["audit_path"]})
                except Exception as exc:
                    log.update({"http_status": 500, "error": repr(exc)})
                    self._reply(500, {"error": "technical_failure", "detail": repr(exc)})
                finally:
                    outer._append_log(log)
            def _reply(self, status: int, body: dict[str, Any]) -> None:
                data = json.dumps(body, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(data)))
                self.end_headers(); self.wfile.write(data)
            def log_message(self, format: str, *args: Any) -> None:
                return

        self.httpd = ThreadingHTTPServer((host, port), Handler)
        self.port = int(self.httpd.server_address[1])

    def _append_log(self, rec: dict[str, Any]) -> None:
        path = self.output_root / "http-requests.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def serve_forever(self) -> None:
        self.httpd.serve_forever()

    def shutdown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


def run_qa(output_root: Path = ROOT / "runs", registry: Path = P3_REGISTRY) -> dict[str, Any]:
    server = FacadeServer(output_root=output_root, registry=registry)
    import threading
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    report: dict[str, Any] = {"kind": "P2c-zero-shot executable HTTP facade QA", "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "localhost": f"127.0.0.1:{server.port}", "contracts": {}, "summary": {"implemented_routes": 0, "exercised_http": 0, "schema_validated": 0, "blocked": 0}}
    try:
        for cid in ["E1-1", "E1-2", "E1-3"]:
            contract = load_contract(cid)
            cinfo = {"contract_path": str(CONTRACTS[cid]), "contract_sha256": sha256(CONTRACTS[cid]), "operations": {}}
            for op_id, meta in load_operation_index(contract).items():
                track = meta["track"]
                req_body = sample_request_for(cid, track, registry)
                raw = json.dumps(req_body).encode()
                url = f"http://127.0.0.1:{server.port}/{cid}{meta['path']}"
                entry = {"implemented": True, "url": url, "request_sha256": bytes_sha(raw)}
                try:
                    req = urllib.request.Request(url, data=raw, headers={"content-type": "application/json"}, method="POST")
                    with urllib.request.urlopen(req, timeout=180) as resp:
                        data = resp.read(); payload = json.loads(data); status = resp.status
                except urllib.error.HTTPError as exc:
                    data = exc.read(); payload = json.loads(data or b"{}"); status = exc.code
                entry.update({"http_status": status, "exercised_http": True, "response_sha256": bytes_sha(data), "audit_path": payload.get("audit_path")})
                if status == 200:
                    try:
                        ContractFacade(cid, output_root, registry).validate_response(track, "200", payload["body"])
                        entry["schema_validated"] = True
                    except Exception as exc:
                        entry["schema_validated"] = False; entry["schema_error"] = repr(exc)
                else:
                    entry["schema_validated"] = False; entry["blocked"] = True
                cinfo["operations"][track] = entry
            report["contracts"][cid] = cinfo
    finally:
        server.shutdown(); thread.join(timeout=5)
    for cinfo in report["contracts"].values():
        for op in cinfo["operations"].values():
            report["summary"]["implemented_routes"] += 1 if op.get("implemented") else 0
            report["summary"]["exercised_http"] += 1 if op.get("exercised_http") else 0
            report["summary"]["schema_validated"] += 1 if op.get("schema_validated") else 0
            report["summary"]["blocked"] += 1 if op.get("blocked") else 0
    report["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    path = output_root / "p2c-zero-shot-http-qa-report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    report["report_path"] = str(path)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["qa", "call", "serve"])
    ap.add_argument("--contract", choices=["E1-1", "E1-2", "E1-3"])
    ap.add_argument("--track", choices=["posting", "interest", "reporting"])
    ap.add_argument("--request-json", type=Path)
    ap.add_argument("--output-root", type=Path, default=ROOT / "runs")
    ap.add_argument("--registry", type=Path, default=P3_REGISTRY)
    ap.add_argument("--port-file", type=Path)
    args = ap.parse_args()
    if args.command == "qa":
        print(json.dumps(run_qa(args.output_root, args.registry), indent=2, ensure_ascii=False))
    elif args.command == "serve":
        server = FacadeServer(output_root=args.output_root, registry=args.registry)
        if args.port_file:
            args.port_file.write_text(str(server.port))
        try:
            server.serve_forever()
        finally:
            server.shutdown()
    else:
        if not args.contract or not args.track:
            ap.error("call requires --contract and --track")
        body = json.loads(args.request_json.read_text()) if args.request_json else sample_request_for(args.contract, args.track, args.registry)
        print(json.dumps(ContractFacade(args.contract, args.output_root, args.registry).execute(args.track, body), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

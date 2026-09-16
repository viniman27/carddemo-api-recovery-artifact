#!/usr/bin/env python3
"""Executable local facades for few-shot contracts E2-1/E2-2/E2-3.

P2c writes only P2c evidence. COBOL execution uses the existing P2b build and
helpers as read-only technical infrastructure, with per-request sequential input
resources materialized from the public request body before each invocation.
"""
from __future__ import annotations

import argparse, hashlib, http.server, importlib.util, json, os, signal, socket, subprocess, sys, tempfile, threading, time, urllib.error, urllib.request
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, InvalidOperation
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
CYCLE = ROOT.parent
# Prefer the existing P2a validator environment when this facade is imported by
# plain python3 tools such as P3/qa_facade_input_effect.py.
for _site in (CYCLE / "P2a" / ".venv" / "lib").glob("python*/site-packages"):
    if str(_site) not in sys.path:
        sys.path.insert(0, str(_site))
import yaml

P2B = CYCLE / "P2b"
REGISTRY = CYCLE / "P3" / "technical-packages-v3-argument" / "registry.json"
CONTRACT_ROOT = CYCLE / "collection-01"
RUNS = ROOT / "runs"
OUTPUTS = ROOT / "outputs"
P2C_BUILD = ROOT / "build"
LOCAL_BINDING_PREFIX = "p3-local-technical-fixture-selection:"
TRACKS = ("posting", "interest", "reporting")
PROGRAM = {"posting": "CBTRN02C", "interest": "CBACT04C", "reporting": "CBTRN03C"}

@dataclass(frozen=True)
class Contract:
    contract_id: str
    original_path: Path
    paths: dict[str, str]

CONTRACTS: dict[str, Contract] = {
    "E2-1": Contract("E2-1", CONTRACT_ROOT / "E2-1" / "response-original.txt", {"posting": "/transaction-postings", "interest": "/interest-transaction-generations", "reporting": "/transaction-reports"}),
    "E2-2": Contract("E2-2", CONTRACT_ROOT / "E2-2" / "response-original.txt", {"posting": "/transaction-posting-runs", "interest": "/interest-generation-runs", "reporting": "/transaction-report-runs"}),
    "E2-3": Contract("E2-3", CONTRACT_ROOT / "E2-3" / "response-original.txt", {"posting": "/transaction-posting-runs", "interest": "/interest-generation-runs", "reporting": "/transaction-report-runs"}),
}
BINDING_FIELDS = {
    "posting": {"crossReferences", "accounts", "categoryBalances", "transactionOutput", "rejectionOutput"},
    "interest": {"categoryBalances", "crossReferences", "accounts", "disclosureGroups", "transactionOutput"},
    "reporting": {"crossReferences", "transactionTypes", "transactionCategories", "reportOutput"},
}
BINDING_TO_DD = {
    "posting": {"crossReferences":"XREFFILE", "accounts":"ACCTFILE", "categoryBalances":"TCATBALF", "transactionOutput":"TRANFILE", "rejectionOutput":"DALYREJS"},
    "interest": {"categoryBalances":"TCATBALF", "crossReferences":"XREFFILE", "accounts":"ACCTFILE", "disclosureGroups":"DISCGRP", "transactionOutput":"TRANSACT"},
    "reporting": {"crossReferences":"CARDXREF", "transactionTypes":"TRANTYPE", "transactionCategories":"TRANCATG", "reportOutput":"TRANREPT"},
}

class TransportRejection(ValueError):
    pass

_P2B_CACHE: Any | None = None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_p2b() -> Any:
    global _P2B_CACHE
    if _P2B_CACHE is not None:
        return _P2B_CACHE
    spec = importlib.util.spec_from_file_location("p2b_binding_redirected", P2B / "p2b_binding.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load P2b binding")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    RUNS.mkdir(parents=True, exist_ok=True); OUTPUTS.mkdir(parents=True, exist_ok=True)
    module.RUNS = RUNS / "p2b-redirected"
    module.COMMAND_LOG = OUTPUTS / "p2b-command-log.jsonl"
    _P2B_CACHE = module
    return module


def _spec(contract_id: str) -> dict[str, Any]:
    return yaml.safe_load(CONTRACTS[contract_id].original_path.read_text())


def _request_schema(contract_id: str, track: str) -> dict[str, Any]:
    spec = _spec(contract_id)
    return spec["paths"][CONTRACTS[contract_id].paths[track]]["post"].get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})


def _jsonschema_errors(contract_id: str, track: str, body: Any) -> list[str]:
    """Validate with real jsonschema in the existing P2a venv, not a subset."""
    py = CYCLE / "P2a" / ".venv" / "bin" / "python"
    payload = {"contract": str(CONTRACTS[contract_id].original_path), "operation": CONTRACTS[contract_id].paths[track], "body": body}
    code = r'''
import json, sys, yaml
from jsonschema import Draft202012Validator, RefResolver
payload=json.loads(sys.stdin.read())
spec=yaml.safe_load(open(payload['contract']).read())
schema=spec['paths'][payload['operation']]['post'].get('requestBody',{}).get('content',{}).get('application/json',{}).get('schema',{})
validator=Draft202012Validator(schema, resolver=RefResolver.from_schema(spec))
print(json.dumps([e.message for e in sorted(validator.iter_errors(payload['body']), key=lambda e:[str(p) for p in e.path])]))
'''
    if py.exists():
        proc = subprocess.run([str(py), "-c", code], input=json.dumps(payload), text=True, capture_output=True, timeout=30)
        if proc.returncode != 0:
            raise TransportRejection(f"jsonschema validator failed: {proc.stderr.strip()}")
        return json.loads(proc.stdout)
    # Fallback only when the validator environment is absent; still uses jsonschema if available.
    from jsonschema import Draft202012Validator, RefResolver  # type: ignore
    spec = _spec(contract_id); schema = _request_schema(contract_id, track)
    validator = Draft202012Validator(schema, resolver=RefResolver.from_schema(spec))
    return [e.message for e in sorted(validator.iter_errors(body), key=lambda e: [str(p) for p in e.path])]


def validate_request(contract_id: str, track: str, body: Any) -> None:
    if contract_id not in CONTRACTS or track not in TRACKS:
        raise TransportRejection("unknown contract or track")
    errors = _jsonschema_errors(contract_id, track, body)
    if errors:
        raise TransportRejection("; ".join(errors))
    if isinstance(body, dict) and "bindings" in body:
        _validate_bindings(track, body["bindings"])


def _validate_bindings(track: str, value: Any) -> None:
    if not isinstance(value, dict):
        raise TransportRejection("bindings must be an object")
    required = BINDING_FIELDS[track]
    missing = sorted(required - set(value))
    if missing:
        raise TransportRejection(f"bindings missing field(s): {missing}")
    for key in required:
        token = value.get(key)
        if not isinstance(token, str) or not token.startswith(LOCAL_BINDING_PREFIX):
            raise TransportRejection(f"bindings.{key} must use the local P2c fixture token prefix")
        opaque = token[len(LOCAL_BINDING_PREFIX):]
        if opaque != key:
            raise TransportRejection(f"bindings.{key} token does not resolve to the requested local DD binding")


def _resolve_request_bindings(track: str, body: dict[str, Any], wd: Path, audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Resolve local binding tokens to concrete DD paths in this invocation.

    The contract exposes binding identifiers; P2c deliberately accepts only its
    local technical tokens and attributes each token to the actual DD file used
    by the COBOL process. Unknown or mismatched tokens fail before invocation.
    """
    bindings = body.get("bindings")
    if bindings is None:
        audit["RES"]["requestBindingsResolved"] = {}
        return {}
    _validate_bindings(track, bindings)
    resolved: dict[str, dict[str, Any]] = {}
    for field in sorted(BINDING_FIELDS[track]):
        dd = BINDING_TO_DD[track][field]
        path = wd / dd
        resolved[field] = {
            "token": bindings[field],
            "ddName": dd,
            "path": str(path),
            "existsAtResolution": path.exists(),
            "bytesAtResolution": path.stat().st_size if path.exists() else None,
            "sha256AtResolution": sha256(path) if path.exists() else None,
        }
    audit["RES"]["requestBindingsResolved"] = resolved
    return resolved


def _mark_pre_cobol_request_materialized(audit: dict[str, Any], wd: Path, input_labels: list[str]) -> None:
    snap = load_p2b().capture_state_snapshot(wd)
    snap["afterRequestInputs"] = input_labels
    snap["provenance"] = "after fixture materialization and request DALYTRAN/TRANFILE/DATEPARM/PARMFILE writes; before COBOL invocation"
    audit["STATE"]["pre_cobol_request_materialized"] = snap


def _text(value: Any, width: int, *, pad: bool = True) -> bytes:
    s = str(value)
    b = s.encode("ascii", "strict")
    if len(b) > width:
        raise TransportRejection(f"value longer than {width} bytes")
    return b.ljust(width, b" ") if pad else b


def _amount_to_display(value: Any) -> bytes:
    try:
        dec = Decimal(str(value))
    except InvalidOperation as exc:
        raise TransportRejection("amount must be decimal transport value") from exc
    cents_dec = dec * Decimal(100)
    if cents_dec != cents_dec.to_integral_value():
        raise TransportRejection("amount has more than two implied decimal places; no rounding performed")
    cents = int(cents_dec)
    if abs(cents) > 99999999999:
        raise TransportRejection("amount outside 11-digit S9(9)V99 storage range")
    digits = f"{abs(cents):011d}"
    if cents < 0:
        digits = digits[:-1] + "pqrstuvwxy"[int(digits[-1])]
    return digits.encode("ascii")


def transaction_record(tx: dict[str, Any], contract_id: str) -> bytes:
    filler = tx.get("filler", "")
    data = b"".join([
        _text(tx.get("transactionId", ""), 16), _text(tx.get("typeCode", ""), 2),
        str(tx["categoryCode"]).encode("ascii").zfill(4), _text(tx.get("source", ""), 10),
        _text(tx.get("description", ""), 100), _amount_to_display(tx.get("amount", 0)),
        str(tx["merchantId"]).encode("ascii").zfill(9), _text(tx.get("merchantName", ""), 50),
        _text(tx.get("merchantCity", ""), 50), _text(tx.get("merchantZip", ""), 10),
        _text(tx.get("cardNumber", ""), 16), _text(tx.get("originalTimestamp", ""), 26),
        _text(tx.get("processingTimestamp", ""), 26), _text(filler, 20),
    ])
    if len(data) != 350:
        raise AssertionError(len(data))
    return data


def _records_bytes(items: list[dict[str, Any]], contract_id: str) -> bytes:
    return b"".join(transaction_record(x, contract_id) for x in items)


def _dateparm_bytes(records: list[str], contract_id: str) -> bytes:
    out = []
    for rec in records:
        b = rec.encode("ascii", "strict")
        if len(b) > 80:
            raise TransportRejection("DATEPARM record exceeds 80 bytes")
        if contract_id == "E2-3" and len(b) != 80:
            raise TransportRejection("E2-3 DATEPARM record must be exactly 80 bytes")
        out.append(b.ljust(80, b" "))
    return b"".join(out)


P2C_INTEREST_DRIVER = r'''
>>source format free
identification division.
program-id. P2C_INTEREST_DRIVER.
environment division.
input-output section.
file-control.
    select parameter-file assign to PARMFILE organization sequential file status parameter-status.
data division.
file section.
fd parameter-file.
01 parameter-bytes pic x(10).
working-storage section.
01 parameter-status pic xx.
01 length-text pic x(16).
01 external-parms.
   05 parm-length pic s9(4) comp value 10.
   05 parm-value pic x(10).
procedure division.
    accept length-text from environment 'P2C_PARM_LENGTH'
    if function trim(length-text) not = ''
        compute parm-length = function numval(length-text)
    end-if
    open input parameter-file
    if parameter-status not = '00'
        display 'P2C-PARAMETER-FAIL: open' upon syserr
        stop run returning 12
    end-if
    read parameter-file
    if parameter-status not = '00'
        display 'P2C-PARAMETER-FAIL: read' upon syserr
        stop run returning 12
    end-if
    move parameter-bytes to parm-value
    close parameter-file
    display 'P2C-PARM-LENGTH=' parm-length
    display 'P2C-PARM-VALUE=' parm-value
    call 'CBACT04C' using external-parms
    stop run.
'''


def _ensure_p2c_interest_driver() -> Path:
    p2b = load_p2b()
    if not (p2b.BUILD / "CBACT04C.dylib").exists():
        raise RuntimeError("P2b CBACT04C module is missing; run the existing P2b build outside P2c before this facade")
    P2C_BUILD.mkdir(exist_ok=True)
    src = P2C_BUILD / "p2c_interest_driver.cbl"
    src.write_text(P2C_INTEREST_DRIVER)
    out = P2C_BUILD / "P2C_INTEREST_DRIVER"
    cp = p2b.CORPUS / "app" / "cpy"
    cmd = p2b.run_cmd(["cobc", "-std=ibm", "-fsign=ascii", "-I", cp, "-x", "-free", "-o", out, src], cwd=P2C_BUILD, expect=0)
    (P2C_BUILD / "p2c-interest-driver-build.json").write_text(json.dumps(cmd, indent=2) + "\n")
    return out


def _interest_parameter(contract_id: str, body: dict[str, Any]) -> tuple[str, bytes, int, str]:
    if contract_id == "E2-2":
        raw = str(body.get("parameterDate", ""))
        if "parameterLength" in body:
            length = int(body["parameterLength"])
            authority = "request parameterLength PIC S9(4) COMP"
        else:
            length = len(raw.encode("ascii", "strict"))
            authority = "contract default: supplied prefix byte length when parameterLength omitted"
    else:
        raw = str(body.get("transactionIdPrefix", body.get("parameterDate", "")))
        length = len(raw.encode("ascii", "strict"))
        authority = "local wrapper supplies prefix byte length; COBOL does not inspect length"
    return raw, _text(raw, 10), length, authority


def diagnostics_from_audit(audit: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for key in ("program_stdout", "program_stderr"):
        text = audit.get("CAP", {}).get(key, "") or ""
        lines.extend([line for line in text.splitlines() if line])
    return lines


def cobol_precondition_failures(cmd: dict[str, Any], track: str) -> list[dict[str, Any]]:
    """Extract source-level indexed lookup abort causes from COBOL DISPLAY text."""
    events: list[dict[str, Any]] = []
    lines = (cmd.get("stdout") or "").splitlines()
    lookup_labels = {
        "INVALID CARD NUMBER : ": ("CARDXREF", "CBTRN03C DISPLAY before 9999-ABEND-PROGRAM; CARDXREF indexed lookup precondition not met"),
        "INVALID TRAN TYPE KEY : ": ("TRANTYPE", "CBTRN03C DISPLAY before 9999-ABEND-PROGRAM; TRANTYPE indexed lookup precondition not met"),
        "INVALID TRAN CATG KEY : ": ("TRANCATG", "CBTRN03C DISPLAY before 9999-ABEND-PROGRAM; TRANCATG indexed lookup precondition not met"),
    }
    for idx, line in enumerate(lines):
        for prefix, (lookup, authority) in lookup_labels.items():
            if not line.startswith(prefix):
                continue
            status = None
            raw_status_text = lines[idx + 1].strip() if idx + 1 < len(lines) else None
            if raw_status_text and "FILE STATUS IS:" in raw_status_text:
                raw_status = raw_status_text.split("FILE STATUS IS:", 1)[1].strip()
                status = raw_status[-2:] if len(raw_status) >= 2 else raw_status
            events.append({
                "kind": "cobol_precondition_failure",
                "track": track,
                "lookup": lookup,
                "key": line.split(":", 1)[1].strip(),
                "fileStatus": status,
                "rawStatusText": raw_status_text,
                "authority": authority,
            })
    return events


def reached_cobol_program(cmd: dict[str, Any], program: str, output: bytes | None = None) -> bool:
    stdout = cmd.get("stdout") or ""
    return (
        output is not None and len(output) > 0
    ) or f"START OF EXECUTION OF PROGRAM {program}" in stdout or f"END OF EXECUTION OF PROGRAM {program}" in stdout


def _decode_ascii(raw: bytes, label: str, audit: dict[str, Any] | None = None) -> str:
    try:
        return raw.decode("ascii")
    except UnicodeDecodeError as exc:
        if audit is not None:
            audit.setdefault("FAIL", {}).setdefault("events", []).append({"kind":"raw_decode_failure", "label":label, "offset":exc.start, "rawHexPrefix":raw[:64].hex()})
        raise


def _signed_display_to_decimal(text: str) -> Any:
    s = text.strip()
    if not s:
        return text
    if s.isdigit():
        return int(s) / 100
    if s[-1] in "pqrstuvwxy" and s[:-1].isdigit():
        digits = s[:-1] + str("pqrstuvwxy".index(s[-1]))
        return -int(digits) / 100
    raise ValueError("unrepresentable signed DISPLAY capture; retain raw audit")


def _tx_for_public(item: dict[str, Any], contract_id: str) -> dict[str, Any]:
    out = dict(item)
    if "cardReference" in out and "cardNumber" not in out:
        out["cardNumber"] = out.pop("cardReference")
    if "merchantPostalText" in out and "merchantZip" not in out:
        out["merchantZip"] = out.pop("merchantPostalText")
    if "amount" in out:
        out["amount"] = _signed_display_to_decimal(str(out["amount"]))
    if contract_id == "E2-3" and "filler" not in out and "rawText" in out:
        out["filler"] = out["rawText"][330:350]
    if contract_id in {"E2-2", "E2-3"}:
        for k in ("categoryCode", "merchantId"):
            if isinstance(out.get(k), str) and out[k].strip().isdigit():
                out[k] = int(out[k])
    out.pop("rawText", None)
    return out


def _rejection_for_public(item: dict[str, Any], contract_id: str) -> dict[str, Any]:
    if "candidate" in item:
        tx = _tx_for_public(item["candidate"], contract_id)
        # P2b labels this field to stress that posting rejects preserve the
        # request-owned DALYTRAN bytes. E2-2's public Transaction schema still
        # requires processingTimestamp; expose the captured receiver span without
        # inventing a runtime timestamp or changing other contracts silently.
        if contract_id == "E2-2" and "processingTimestamp" not in tx and "suppliedProcessingTimestamp" in tx:
            tx["processingTimestamp"] = tx.pop("suppliedProcessingTimestamp")
        reason = item.get("reason", "")
        code = "0" + reason if len(reason) == 3 else reason
        return {"transaction": tx, "reasonCode": code, "reasonDescription": item.get("description", "")}
    if "transaction" in item:
        item = dict(item); item["transaction"] = _tx_for_public(item["transaction"], contract_id)
    return item


def _report_lines_from_audit(audit: dict[str, Any]) -> list[str]:
    for capture in audit.get("CAP", {}).get("captures", []):
        if capture.get("label") == "TRANREPT" and capture.get("exists"):
            data = Path(capture["path"]).read_bytes()
            if len(data) % 133:
                audit.setdefault("FAIL", {}).setdefault("events", []).append({"kind":"report_fragment_preserved", "bytes":len(data), "remainder":len(data)%133, "rawHexTail":data[-(len(data)%133):].hex()})
            lines = []
            for i in range(0, len(data) - (len(data) % 133), 133):
                lines.append(_decode_ascii(data[i:i+133], "TRANREPT", audit))
            return lines
    audit.setdefault("FAIL", {}).setdefault("events", []).append({"kind":"report_capture_missing", "classification":"content_unavailable_not_empty_positive"})
    return []


def _failure_body(contract_id: str, track: str, diagnostics: list[str]) -> dict[str, Any]:
    if contract_id == "E2-3":
        out: dict[str, Any] = {"program": PROGRAM[track]}
        if diagnostics: out["diagnostics"] = diagnostics
        return out
    out = {"diagnostics": diagnostics} if diagnostics else {}
    if contract_id == "E2-2": out["program"] = PROGRAM[track]
    return out


def _filler_by_transaction_id(audit: dict[str, Any] | None, label: str) -> dict[str, str]:
    if not audit:
        return {}
    for capture in audit.get("CAP", {}).get("captures", []):
        if capture.get("label") == label and capture.get("exists"):
            data = Path(capture["path"]).read_bytes()
            out: dict[str, str] = {}
            for i in range(0, len(data) - (len(data) % 350), 350):
                rec = data[i:i+350]
                tid = rec[0:16].decode("ascii", "replace").strip()
                out[tid] = rec[330:350].decode("ascii", "replace")
            return out
    return {}


def project_response(contract_id: str, track: str, status: int, p2b_body: dict[str, Any], diagnostics: list[str], audit: dict[str, Any] | None = None) -> dict[str, Any]:
    if status != 200:
        return _failure_body(contract_id, track, diagnostics)
    if track == "posting":
        progress = p2b_body.get("progress", {}).get("value", {})
        txs = [_tx_for_public(x, contract_id) for x in p2b_body.get("outputs", {}).get("items", [])]
        if contract_id == "E2-3":
            fillers = _filler_by_transaction_id(audit, "TRANFILE.after")
            for tx in txs:
                tid = str(tx.get("transactionId", "")).strip()
                if tid in fillers:
                    tx["filler"] = fillers[tid]
        rejs = [_rejection_for_public(x, contract_id) for x in p2b_body.get("rejections", {}).get("items", [])]
        rc = audit.get("RESP", {}).get("program_exit") if audit else None
        if contract_id == "E2-2":
            return {"transactionsProcessed": progress.get("processedRecordCount", 0), "transactionsRejected": progress.get("preliminaryRejectCount", 0), "returnCode": rc, "postedTransactions": txs, "rejections": rejs, "diagnostics": diagnostics}
        return {"processedCount": progress.get("processedRecordCount", 0), "rejectedCount": progress.get("preliminaryRejectCount", 0), "returnCode": rc, "transactions": txs, "rejects": rejs}
    if track == "interest":
        txs = [_tx_for_public(x, contract_id) for x in p2b_body.get("outputs", {}).get("items", [])]
        if contract_id == "E2-2": return {"generatedTransactions": txs, "diagnostics": diagnostics}
        return {"transactions": txs}
    if track == "reporting":
        lines = _report_lines_from_audit(audit or {})
        if contract_id == "E2-2": return {"lines": lines, "diagnostics": diagnostics}
        return {"lines": lines}
    raise ValueError(track)


def _fixture(track: str) -> dict[str, Any] | None:
    os.environ["P2B_FIXTURE_REGISTRY"] = str(REGISTRY)
    return load_p2b().select_external_fixture(track, REGISTRY)


def _new_audit(track: str, inv_id: str, fixture: dict[str, Any] | None):
    p2b = load_p2b(); wd = p2b.invocation_dir(track)
    audit = p2b.new_audit(track, wd, inv_id, fixture)
    if fixture and fixture.get("materializer", {}).get("kind") == "local_file_package":
        p2b.note_fixture_materialization(audit, p2b.materialize_fixture(fixture, wd))
    else:
        p2b.note_fixture_materialization(audit, p2b.materialize_fixture(fixture, wd))
    return p2b, wd, audit


def _capture_and_write(audit: dict[str, Any], wd: Path) -> None:
    audit["STATE"]["after"] = load_p2b().capture_state_snapshot(wd)
    (wd / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n")


def run_posting(contract_id: str, body: dict[str, Any], inv_id: str):
    p2b, wd, audit = _new_audit("posting", inv_id, _fixture("posting"))
    _resolve_request_bindings("posting", body, wd, audit)
    txs = body.get("dailyTransactions", body.get("transactions", []))
    (wd / "DALYTRAN").write_bytes(_records_bytes(txs, contract_id))
    p2b.record_file(audit, "DALYTRAN.pre_cobol", wd / "DALYTRAN")
    _mark_pre_cobol_request_materialized(audit, wd, ["DALYTRAN"])
    cmd = p2b.run_cmd([p2b.BUILD / "CBTRN02C"], cwd=wd, env={"COB_LIBRARY_PATH": str(p2b.BUILD), "P2B_INVOCATION": wd.name, "P2B_WRITE_LOG": str(wd / "write-observations.log"), **{f"DD_{dd}": str(wd / dd) for dd in [*p2b.SIZES, "DALYTRAN", "DALYREJS"]}}, expect=None)
    audit["CAP"]["program_stdout"] = cmd["stdout"]; audit["CAP"]["program_stderr"] = cmd["stderr"]
    for dd in p2b.SIZES:
        raw = wd / f"{dd}.after"
        try: p2b.io_file(wd, dd, "DUMP", raw)
        except Exception as exc: audit["FAIL"]["events"].append({"kind":"local_snapshot_acquisition_failure", "resource":dd, "raw":repr(exc)})
        p2b.record_file(audit, f"{dd}.after", raw)
    if (wd / "DALYREJS").exists(): p2b.record_file(audit, "DALYREJS", wd / "DALYREJS")
    log_path = wd / "write-observations.log"; p2b.record_file(audit, "write-observations", log_path)
    p2b.observations = getattr(p2b, 'observations')
    out_body, event_evidence = p2b.observations.posting_observations(log_path.read_text() if log_path.exists() else None, wd.name, cmd["stdout"])
    audit["CONV"]["write_observations"] = event_evidence
    available = any(v.get("availability")=="available" for v in out_body.values() if isinstance(v,dict))
    status = 200 if available and not event_evidence.get("knownFailure") and not audit["FAIL"]["events"] else 500
    status, out_body, failures = p2b.observations.apply_failure_boundary("posting", status, out_body if available else p2b.error_body("posting", "content_unavailable"), cmd)
    audit["FAIL"]["events"].extend(failures)
    audit["RESP"] = {"status": status, "body": out_body, "program_exit": cmd["exit_code"], "reached_cobol": "START OF EXECUTION OF PROGRAM CBTRN02C" in cmd["stdout"]}
    _capture_and_write(audit, wd)
    return status, out_body, audit


def run_interest(contract_id: str, body: dict[str, Any], inv_id: str):
    p2b, wd, audit = _new_audit("interest", inv_id, _fixture("interest"))
    _resolve_request_bindings("interest", body, wd, audit)
    raw_prefix, parameter_bytes, parameter_length, authority = _interest_parameter(contract_id, body)
    (wd / "PARMFILE").write_bytes(parameter_bytes)
    linkage_evidence = {"parameterValueRaw": raw_prefix, "parameterLength": parameter_length, "parameterBytesHex": parameter_bytes.hex()}
    (wd / "p2c-interest-linkage.json").write_text(json.dumps(linkage_evidence, indent=2) + "\n")
    p2b.record_file(audit, "PARMFILE.pre_cobol", wd / "PARMFILE")
    p2b.record_file(audit, "p2c-interest-linkage", wd / "p2c-interest-linkage.json")
    audit["RES"]["externalParameter"] = {"path": str(wd / "PARMFILE"), "sha256": sha256(wd / "PARMFILE"), "bytes": 10, "value": parameter_bytes.decode("ascii"), "linkageParameterLength": parameter_length, "authority": authority}
    _mark_pre_cobol_request_materialized(audit, wd, ["PARMFILE", "p2c-interest-linkage.json"])
    driver = _ensure_p2c_interest_driver()
    cmd = p2b.run_cmd([driver], cwd=wd, env={"COB_LIBRARY_PATH": f"{p2b.BUILD}{os.pathsep}{P2C_BUILD}", "P2C_PARM_LENGTH": str(parameter_length), **{f"DD_{dd}": str(wd / dd) for dd in (*p2b.RESOURCE_NAMES["interest"], "TRANSACT")}}, expect=None)
    if (wd / "TRANSACT").exists(): p2b.record_file(audit, "TRANSACT", wd / "TRANSACT")
    tr = (wd / "TRANSACT").read_bytes() if (wd / "TRANSACT").exists() else None
    items, evidence = p2b.parse_transaction_records(tr or b"", "interest") if tr is not None else ([], {"framing": p2b.fixed_capture_status("interest", None, 350)})
    # Preserve filler bytes absent from P2b's public parser.
    for item, idx in zip(items, range(0, len(tr or b""), 350)):
        rec = (tr or b"")[idx:idx+350]; item["rawText"] = rec.decode("ascii", "replace"); item["filler"] = rec[330:350].decode("ascii", "replace")
    body2 = {"track":"interest", "completeness":"not_attested", "durability":"unknown", "outputs":{"availability":"available", "items":items}}
    status, mapped = p2b.status_for_capture_observation("interest", evidence["framing"], body2)
    if status != 200: body2 = mapped
    status, body2, failures = p2b.observations.apply_failure_boundary("interest", status, body2, cmd)
    audit["FAIL"]["events"].extend(failures)
    audit["CAP"]["program_stdout"] = cmd["stdout"]; audit["CAP"]["program_stderr"] = cmd["stderr"]
    audit["CONV"]["field_mappings"].append({"field":"GeneratedInterestTransaction", "basis":"TRANSACT fixed 350-byte records; filler bytes 330:350 retained where exposed"})
    audit["RESP"] = {"status": status, "body": body2, "program_exit": cmd["exit_code"], "reached_cobol": bool(tr) or "END OF EXECUTION" in cmd["stdout"]}
    _capture_and_write(audit, wd)
    return status, body2, audit


def run_reporting(contract_id: str, body: dict[str, Any], inv_id: str):
    p2b, wd, audit = _new_audit("reporting", inv_id, _fixture("reporting"))
    _resolve_request_bindings("reporting", body, wd, audit)
    (wd / "TRANFILE").write_bytes(_records_bytes(body.get("transactions", []), contract_id))
    (wd / "DATEPARM").write_bytes(_dateparm_bytes(body.get("dateParameterRecords", []), contract_id))
    p2b.record_file(audit, "TRANFILE.pre_cobol", wd / "TRANFILE"); p2b.record_file(audit, "DATEPARM.pre_cobol", wd / "DATEPARM")
    _mark_pre_cobol_request_materialized(audit, wd, ["TRANFILE", "DATEPARM"])
    cmd = p2b.run_cmd([p2b.BUILD / "CBTRN03C"], cwd=wd, env={"COB_LIBRARY_PATH": str(p2b.BUILD), **{f"DD_{dd}": str(wd / dd) for dd in (*p2b.RESOURCE_NAMES["reporting"], "TRANREPT")}}, expect=None)
    if (wd / "TRANREPT").exists(): p2b.record_file(audit, "TRANREPT", wd / "TRANREPT")
    report = (wd / "TRANREPT").read_bytes() if (wd / "TRANREPT").exists() else None
    records, evidence = p2b.parse_report_records(report or b"") if report is not None else ([], {"framing": p2b.fixed_capture_status("reporting", None, 133)})
    body2 = {"track":"reporting", "completeness":"not_attested", "durability":"unknown", "records":{"availability":"available", "items":records}}
    audit["CAP"]["program_stdout"] = cmd["stdout"]; audit["CAP"]["program_stderr"] = cmd["stderr"]
    audit["CAP"]["report_record_classifications"] = evidence.get("records", [])
    status, mapped = p2b.status_for_capture_observation("reporting", evidence["framing"], body2)
    if status != 200: body2 = mapped
    status, body2, failures = p2b.observations.apply_failure_boundary("reporting", status, body2, cmd)
    audit["FAIL"]["events"].extend(cobol_precondition_failures(cmd, "reporting"))
    audit["FAIL"]["events"].extend(failures)
    audit["RESP"] = {"status": status, "body": body2, "program_exit": cmd["exit_code"], "reached_cobol": reached_cobol_program(cmd, "CBTRN03C", report)}
    _capture_and_write(audit, wd)
    return status, body2, audit


def _run_track(contract_id: str, track: str, body: dict[str, Any], inv_id: str):
    return {"posting": run_posting, "interest": run_interest, "reporting": run_reporting}[track](contract_id, body, inv_id)


def execute(contract_id: str, track: str, body: dict[str, Any]) -> dict[str, Any]:
    validate_request(contract_id, track, body)
    started = time.time(); inv_id = f"p2c-{contract_id}-{track}-{int(started*1000)}"
    status, p2b_body, p2b_audit = _run_track(contract_id, track, body, inv_id)
    diagnostics = diagnostics_from_audit(p2b_audit)
    projected = project_response(contract_id, track, status, p2b_body, diagnostics, p2b_audit)
    audit = {
        "kind":"p2c-few-shot-facade-invocation", "contractId":contract_id, "contractOriginal":str(CONTRACTS[contract_id].original_path),
        "contractOriginalSha256":sha256(CONTRACTS[contract_id].original_path), "track":track, "path":CONTRACTS[contract_id].paths[track],
        "status":status, "requestBody":body, "requestBodySha256":hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "requestMaterialization": {"arraysAreSequentialFiles": True, "p2bRunDirectory": p2b_audit.get("INV", {}).get("workdir"), "registry": str(REGISTRY), "registrySha256": sha256(REGISTRY)},
        "semanticLimits":["P2c uses P3 local technical resources as preprovisioned DD resources only; request arrays/arguments are materialized per invocation and are not fixture selectors.", "Binding prefix is resolved locally to DD resources and rejected if malformed; it is not accepted and ignored.", "Raw receiver bytes and decode/framing failures are preserved in audits."],
        "response": projected, "p2bAuditPath": str(Path(p2b_audit.get("INV", {}).get("workdir", ".")) / "audit.json"),
        "durationSeconds": round(time.time()-started,3),
    }
    out_dir = RUNS / contract_id / track; out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{int(started*1000)}-audit.json"; out_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False)+"\n")
    return {"status":status, "body":projected, "auditPath":str(out_path), "p2bAuditPath":audit["p2bAuditPath"]}


def sample_request(contract_id: str, track: str) -> dict[str, Any]:
    tx_str = {"transactionId":"TEST000000000001","typeCode":"01","categoryCode":"0001","source":"TEST","description":"LOCAL SYNTHETIC FIXTURE","amount":25.0,"merchantId":"000000001","merchantName":"TEST MERCHANT","merchantCity":"TEST CITY","merchantZip":"0000000000","cardNumber":"0000000000000001","originalTimestamp":"2025-01-01-00.00.00.000000","processingTimestamp":"2025-01-01-00.00.00.000000","filler":"ORIGINAL-FILLER-1234"}
    tx_num = dict(tx_str, categoryCode=1, merchantId=1)
    if contract_id == "E2-1":
        return {"posting":{"dailyTransactions":[tx_str]}, "interest":{"transactionIdPrefix":"2022071800"}, "reporting":{"transactions":[tx_str], "dateParameterRecords":["2025-01-01 2025-12-31"]}}[track]
    if contract_id == "E2-2":
        bindings = {k: LOCAL_BINDING_PREFIX+k for k in BINDING_FIELDS[track]}
        if track == "posting": return {"bindings":bindings, "transactions":[tx_num]}
        if track == "interest": return {"bindings":bindings, "parameterDate":"2022071800", "parameterLength":10}
        return {"bindings":bindings, "transactions":[tx_num], "dateParameterRecords":["2025-01-01 2025-12-31"]}
    if track == "posting": return {"transactions":[tx_num]}
    if track == "interest": return {"transactionIdPrefix":"2022071800"}
    return {"transactions":[tx_num], "dateParameterRecords":["2025-01-01 2025-12-31".ljust(80)]}

class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "P2cFewShot/1"
    def do_POST(self):
        route = None
        cid = getattr(self.server, "contract_id", None)
        contract_ids = [cid] if cid else []
        for contract_id in contract_ids:
            contract = CONTRACTS[contract_id]
            for track, path in contract.paths.items():
                if self.path == path:
                    route = (contract_id, track)
        if route is None:
            self.send_error(404); return
        n = int(self.headers.get("content-length", "0"))
        try:
            body = json.loads(self.rfile.read(n) or b"null")
            result = execute(route[0], route[1], body)
            with (OUTPUTS / "http-invocations.jsonl").open("a") as log:
                log.write(json.dumps({"pid":os.getpid(),"path":self.path,"auditPath":result["auditPath"],"p2bAuditPath":result["p2bAuditPath"]}) + "\n")
            self.reply(result["status"], result["body"])
        except TransportRejection as exc:
            with (OUTPUTS / "http-rejections.jsonl").open("a") as log:
                log.write(json.dumps({"pid":os.getpid(),"path":self.path,"contractId":route[0],"track":route[1],"error":str(exc)}) + "\n")
            self.reply(400, {})
        except Exception as exc:
            with (OUTPUTS / "http-errors.jsonl").open("a") as log:
                log.write(json.dumps({"pid":os.getpid(),"path":self.path,"contractId":route[0],"track":route[1],"error":repr(exc)}) + "\n")
            self.reply(500, _failure_body(route[0], route[1], [repr(exc)]))
    def reply(self, status:int, body:dict[str,Any]) -> None:
        data=json.dumps(body, ensure_ascii=False).encode(); self.send_response(status); self.send_header("content-type","application/json"); self.send_header("content-length",str(len(data))); self.end_headers(); self.wfile.write(data)
    def log_message(self, fmt:str, *args:Any)->None:
        (OUTPUTS/"http-access.log").parent.mkdir(exist_ok=True); (OUTPUTS/"http-access.log").open("a").write((fmt%args)+"\n")


def serve(port_file: Path, contract_id: str) -> None:
    httpd = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    httpd.contract_id = contract_id  # type: ignore[attr-defined]
    port_file.write_text(str(httpd.server_address[1]))
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    httpd.serve_forever()


def http_roundtrip(contract_id: str, track: str, body: dict[str, Any]) -> tuple[int, dict[str, Any], dict[str, Any]]:
    port_file = OUTPUTS / f"http-{os.getpid()}-{int(time.time()*1000)}.port"; OUTPUTS.mkdir(exist_ok=True)
    proc = subprocess.Popen([sys.executable, __file__, "serve", "--contract-id", contract_id, "--port-file", str(port_file)], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        for _ in range(100):
            if port_file.exists(): break
            time.sleep(0.05)
        port = int(port_file.read_text())
        data = json.dumps(body).encode()
        url = f"http://127.0.0.1:{port}{CONTRACTS[contract_id].paths[track]}"
        req = urllib.request.Request(url, data=data, headers={"content-type":"application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read(); status = r.status
        except urllib.error.HTTPError as e:
            status = e.code; raw = e.read()
        parsed = json.loads(raw)
        evidence = {"url":url, "status":status, "requestBody":body, "responseRawSha256":hashlib.sha256(raw).hexdigest(), "auditPath":parsed.get("auditPath"), "p2bAuditPath":parsed.get("p2bAuditPath")}
        local_log = OUTPUTS / "http-invocations.jsonl"
        if local_log.exists():
            matches = [json.loads(line) for line in local_log.read_text().splitlines() if line.strip()]
            matches = [entry for entry in matches if entry.get("pid") == proc.pid]
            if matches:
                evidence["auditPath"] = matches[-1]["auditPath"]
                evidence["p2bAuditPath"] = matches[-1]["p2bAuditPath"]
        return status, parsed, evidence
    finally:
        proc.terminate();
        try: out, err = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired: proc.kill(); out, err = proc.communicate()
        with (OUTPUTS/"http-lifecycle.jsonl").open("a") as f:
            f.write(json.dumps({"pid":proc.pid,"returncode":proc.returncode,"stdout":out,"stderr":err})+"\n")


def main() -> None:
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd", required=True)
    one=sub.add_parser("invoke"); one.add_argument("contract_id", choices=sorted(CONTRACTS)); one.add_argument("track", choices=TRACKS); one.add_argument("--request-json", type=Path)
    srv=sub.add_parser("serve"); srv.add_argument("--contract-id", choices=sorted(CONTRACTS), required=True); srv.add_argument("--port-file", type=Path, required=True)
    http=sub.add_parser("http-smoke")
    sub.add_parser("smoke-all")
    args=ap.parse_args()
    if args.cmd=="invoke":
        body=json.loads(args.request_json.read_text()) if args.request_json else sample_request(args.contract_id,args.track); print(json.dumps(execute(args.contract_id,args.track,body), indent=2, ensure_ascii=False))
    elif args.cmd=="serve": serve(args.port_file, args.contract_id)
    elif args.cmd=="http-smoke":
        rows=[]
        for cid in sorted(CONTRACTS):
            for track in TRACKS:
                try:
                    st, body, ev = http_roundtrip(cid, track, sample_request(cid, track)); rows.append({"contractId":cid,"track":track,"operation":CONTRACTS[cid].paths[track],"status":st,"body":body,**ev})
                except Exception as exc: rows.append({"contractId":cid,"track":track,"operation":CONTRACTS[cid].paths[track],"blocked":True,"error":repr(exc)})
        report={"kind":"p2c-few-shot-http-smoke","results":rows,"overallExercised":all(not r.get('blocked') for r in rows)}; (OUTPUTS/"http-smoke-report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n"); print(json.dumps(report,indent=2,ensure_ascii=False))
    elif args.cmd=="smoke-all":
        rows=[]
        for cid in sorted(CONTRACTS):
            for track in TRACKS:
                rec={"contractId":cid,"track":track,"operation":CONTRACTS[cid].paths[track]}
                try:
                    result=execute(cid,track,sample_request(cid,track)); rec.update({"implemented":True,"exercised":True,"blocked":False,"status":result["status"],"auditPath":result["auditPath"],"p2bAuditPath":result["p2bAuditPath"]})
                except Exception as exc: rec.update({"implemented":True,"exercised":False,"blocked":True,"blocker":repr(exc)})
                rows.append(rec)
        report={"kind":"p2c-few-shot-smoke-all","registry":str(REGISTRY),"results":rows,"overallExercised":all(r["exercised"] for r in rows)}; OUTPUTS.mkdir(exist_ok=True); (OUTPUTS/"smoke-all-report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n"); print(json.dumps(report,indent=2,ensure_ascii=False))

if __name__ == "__main__": main()

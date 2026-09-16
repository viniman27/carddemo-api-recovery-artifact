#!/usr/bin/env python3
"""Executable local facades for few-shot contracts E2-1/E2-2/E2-3.

Only P2c evidence is written here. COBOL execution is delegated to the existing
P2b technical harness with its mutable run/log destinations redirected into this
P2c directory. Contract files under collection-01 are read-only authority.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
CYCLE = ROOT.parent
P2B = CYCLE / "P2b"
REGISTRY = CYCLE / "P3" / "technical-packages-v3-argument" / "registry.json"
CONTRACT_ROOT = CYCLE / "collection-01"
RUNS = ROOT / "runs"
OUTPUTS = ROOT / "outputs"
LOCAL_BINDING_PREFIX = "p3-local-technical-fixture-selection:"

TRACKS = ("posting", "interest", "reporting")

@dataclass(frozen=True)
class Contract:
    contract_id: str
    original_path: Path
    paths: dict[str, str]
    request_fields: dict[str, set[str]]
    response_projection: str

CONTRACTS: dict[str, Contract] = {
    "E2-1": Contract(
        "E2-1", CONTRACT_ROOT / "E2-1" / "response-original.txt",
        {"posting": "/transaction-postings", "interest": "/interest-transaction-generations", "reporting": "/transaction-reports"},
        {"posting": {"dailyTransactions"}, "interest": {"transactionIdPrefix"}, "reporting": {"transactions", "dateParameterRecords"}},
        "e2_1",
    ),
    "E2-2": Contract(
        "E2-2", CONTRACT_ROOT / "E2-2" / "response-original.txt",
        {"posting": "/transaction-posting-runs", "interest": "/interest-generation-runs", "reporting": "/transaction-report-runs"},
        {"posting": {"bindings", "transactions"}, "interest": {"bindings", "parameterDate"}, "reporting": {"bindings", "transactions", "dateParameterRecords"}},
        "e2_2",
    ),
    "E2-3": Contract(
        "E2-3", CONTRACT_ROOT / "E2-3" / "response-original.txt",
        {"posting": "/transaction-posting-runs", "interest": "/interest-generation-runs", "reporting": "/transaction-report-runs"},
        {"posting": {"transactions"}, "interest": {"transactionIdPrefix"}, "reporting": {"transactions", "dateParameterRecords"}},
        "e2_3",
    ),
}

BINDING_FIELDS = {
    "posting": {"crossReferences", "accounts", "categoryBalances", "transactionOutput", "rejectionOutput"},
    "interest": {"categoryBalances", "crossReferences", "accounts", "disclosureGroups", "transactionOutput"},
    "reporting": {"crossReferences", "transactionTypes", "transactionCategories", "reportOutput"},
}

class TransportRejection(ValueError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_p2b() -> Any:
    spec = importlib.util.spec_from_file_location("p2b_binding_redirected", P2B / "p2b_binding.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load P2b binding")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Redirect mutable P2b evidence into P2c only. Existing P2b build binaries
    # and source files remain read-only inputs.
    (ROOT / "runs").mkdir(parents=True, exist_ok=True)
    (ROOT / "outputs").mkdir(parents=True, exist_ok=True)
    module.RUNS = ROOT / "runs" / "p2b-redirected"
    module.COMMAND_LOG = ROOT / "outputs" / "p2b-command-log.jsonl"
    return module


def _assert_object(obj: Any) -> dict[str, Any]:
    if not isinstance(obj, dict):
        raise TransportRejection("request body must be a JSON object")
    return obj


def _assert_fields(contract: Contract, track: str, obj: dict[str, Any]) -> None:
    required = contract.request_fields[track]
    missing = sorted(required - set(obj))
    extra = sorted(set(obj) - required)
    if missing:
        raise TransportRejection(f"missing required field(s): {missing}")
    if extra:
        raise TransportRejection(f"additional field(s) not accepted: {extra}")


def _assert_array(name: str, value: Any) -> None:
    if not isinstance(value, list):
        raise TransportRejection(f"{name} must be an array")


def _assert_string(name: str, value: Any, *, min_len: int | None = None, max_len: int | None = None) -> None:
    if not isinstance(value, str):
        raise TransportRejection(f"{name} must be a string")
    if min_len is not None and len(value) < min_len:
        raise TransportRejection(f"{name} shorter than {min_len}")
    if max_len is not None and len(value) > max_len:
        raise TransportRejection(f"{name} longer than {max_len}")


def _validate_transactions(value: Any, *, numeric_category: bool = False, numeric_merchant: bool = False) -> None:
    _assert_array("transactions", value)
    for index, tx in enumerate(value):
        if not isinstance(tx, dict):
            raise TransportRejection(f"transactions[{index}] must be an object")
        for field in ["transactionId", "typeCode", "source", "description", "merchantName", "merchantCity", "merchantZip", "cardNumber", "originalTimestamp", "processingTimestamp"]:
            if field not in tx:
                raise TransportRejection(f"transactions[{index}] missing {field}")
            limits = {"transactionId": 16, "typeCode": 2, "source": 10, "description": 100, "merchantName": 50, "merchantCity": 50, "merchantZip": 10, "cardNumber": 16, "originalTimestamp": 26, "processingTimestamp": 26}
            _assert_string(f"transactions[{index}].{field}", tx[field], max_len=limits[field])
        if "categoryCode" not in tx or "merchantId" not in tx or "amount" not in tx:
            raise TransportRejection(f"transactions[{index}] missing numeric/category fields")
        if numeric_category:
            if not isinstance(tx["categoryCode"], int) or not 0 <= tx["categoryCode"] <= 9999:
                raise TransportRejection(f"transactions[{index}].categoryCode must be integer 0..9999")
        else:
            _assert_string(f"transactions[{index}].categoryCode", tx["categoryCode"], max_len=4)
        if numeric_merchant:
            if not isinstance(tx["merchantId"], int) or not 0 <= tx["merchantId"] <= 999999999:
                raise TransportRejection(f"transactions[{index}].merchantId must be integer 0..999999999")
        else:
            _assert_string(f"transactions[{index}].merchantId", tx["merchantId"], max_len=9)
        if not isinstance(tx["amount"], (int, float)) or not -999999999.99 <= float(tx["amount"]) <= 999999999.99:
            raise TransportRejection(f"transactions[{index}].amount outside S9(9)V99 transport range")
        if "filler" in tx:
            _assert_string(f"transactions[{index}].filler", tx["filler"], max_len=20)


def _validate_bindings(track: str, value: Any) -> None:
    if not isinstance(value, dict):
        raise TransportRejection("bindings must be an object")
    required = BINDING_FIELDS[track]
    missing = sorted(required - set(value))
    extra = sorted(set(value) - required)
    if missing:
        raise TransportRejection(f"bindings missing field(s): {missing}")
    if extra:
        raise TransportRejection(f"bindings additional field(s) not accepted: {extra}")
    for key, token in value.items():
        _assert_string(f"bindings.{key}", token)
        if not token.startswith(LOCAL_BINDING_PREFIX):
            raise TransportRejection(f"bindings.{key} must use the local P2c fixture token prefix")


def validate_request(contract_id: str, track: str, body: Any) -> None:
    contract = CONTRACTS[contract_id]
    obj = _assert_object(body)
    _assert_fields(contract, track, obj)
    numeric = contract_id in {"E2-2", "E2-3"}
    if "bindings" in obj:
        _validate_bindings(track, obj["bindings"])
    if "dailyTransactions" in obj:
        _validate_transactions(obj["dailyTransactions"], numeric_category=False, numeric_merchant=False)
    if "transactions" in obj:
        _validate_transactions(obj["transactions"], numeric_category=numeric, numeric_merchant=numeric)
    if "transactionIdPrefix" in obj:
        if contract_id == "E2-3":
            _assert_string("transactionIdPrefix", obj["transactionIdPrefix"], min_len=10, max_len=10)
        else:
            _assert_string("transactionIdPrefix", obj["transactionIdPrefix"], max_len=10)
    if "parameterDate" in obj:
        _assert_string("parameterDate", obj["parameterDate"], max_len=10)
    if "dateParameterRecords" in obj:
        _assert_array("dateParameterRecords", obj["dateParameterRecords"])
        for i, value in enumerate(obj["dateParameterRecords"]):
            if contract_id == "E2-3":
                _assert_string(f"dateParameterRecords[{i}]", value, min_len=80, max_len=80)
            else:
                _assert_string(f"dateParameterRecords[{i}]", value, max_len=80)


def diagnostics_from_audit(audit: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for key in ("program_stdout", "program_stderr"):
        text = audit.get("CAP", {}).get(key, "") or ""
        lines.extend([line for line in text.splitlines() if line])
    return lines


def _implied_cents(value: Any) -> Any:
    if isinstance(value, str):
        text = value.strip()
        if text and (text.isdigit() or (text[0] in "+-" and text[1:].isdigit())):
            sign = -1 if text[0] == "-" else 1
            digits = text[1:] if text[0] in "+-" else text
            return sign * (int(digits) / 100)
    return value


def _tx_for_public(item: dict[str, Any], contract_id: str) -> dict[str, Any]:
    out = dict(item)
    # P2b uses cardReference/merchantPostalText names. Few-shot contracts use
    # cardNumber/merchantZip. Preserve original values; do not repair semantics.
    if "cardReference" in out and "cardNumber" not in out:
        out["cardNumber"] = out.pop("cardReference")
    if "merchantPostalText" in out and "merchantZip" not in out:
        out["merchantZip"] = out.pop("merchantPostalText")
    if "amount" in out:
        out["amount"] = _implied_cents(out["amount"])
    if contract_id == "E2-3" and "filler" not in out:
        out["filler"] = ""
    if contract_id in {"E2-2", "E2-3"}:
        if isinstance(out.get("categoryCode"), str) and out["categoryCode"].strip().isdigit():
            out["categoryCode"] = int(out["categoryCode"])
        if isinstance(out.get("merchantId"), str) and out["merchantId"].strip().isdigit():
            out["merchantId"] = int(out["merchantId"])
    return out


def _rejection_for_public(item: dict[str, Any], contract_id: str) -> dict[str, Any]:
    if "candidate" in item:
        tx = _tx_for_public(item["candidate"], contract_id)
        code = "0" + item.get("reason", "") if len(item.get("reason", "")) == 3 else item.get("reason", "")
        return {"transaction": tx, "reasonCode": code, "reasonDescription": item.get("description", "")}
    if "transaction" in item:
        item = dict(item); item["transaction"] = _tx_for_public(item["transaction"], contract_id)
    return item


def _report_lines_from_audit(audit: dict[str, Any]) -> list[str]:
    for capture in audit.get("CAP", {}).get("captures", []):
        if capture.get("label") == "TRANREPT" and capture.get("exists"):
            data = Path(capture["path"]).read_bytes()
            return [data[i:i+133].decode("ascii", "replace") for i in range(0, len(data), 133) if len(data[i:i+133]) == 133]
    return []


def _failure_body(contract_id: str, track: str, body: dict[str, Any], diagnostics: list[str]) -> dict[str, Any]:
    if contract_id == "E2-3":
        out: dict[str, Any] = {"program": {"posting": "CBTRN02C", "interest": "CBACT04C", "reporting": "CBTRN03C"}[track]}
        if diagnostics: out["diagnostics"] = diagnostics
        return out
    out = {"diagnostics": diagnostics} if diagnostics else {}
    if contract_id == "E2-2":
        out["program"] = {"posting": "CBTRN02C", "interest": "CBACT04C", "reporting": "CBTRN03C"}[track]
    return out


def project_response(contract_id: str, track: str, status: int, p2b_body: dict[str, Any], diagnostics: list[str], audit: dict[str, Any] | None = None) -> dict[str, Any]:
    if status != 200:
        return _failure_body(contract_id, track, p2b_body, diagnostics)
    if track == "posting":
        progress = p2b_body.get("progress", {}).get("value", {})
        txs = [_tx_for_public(x, contract_id) for x in p2b_body.get("outputs", {}).get("items", [])]
        rejs = [_rejection_for_public(x, contract_id) for x in p2b_body.get("rejections", {}).get("items", [])]
        if contract_id == "E2-2":
            return {"transactionsProcessed": progress.get("processedRecordCount", 0), "transactionsRejected": progress.get("preliminaryRejectCount", 0), "returnCode": audit.get("RESP", {}).get("program_exit") if audit else None, "postedTransactions": txs, "rejections": rejs, "diagnostics": diagnostics}
        return {"processedCount": progress.get("processedRecordCount", 0), "rejectedCount": progress.get("preliminaryRejectCount", 0), "returnCode": audit.get("RESP", {}).get("program_exit") if audit else None, "transactions": txs, "rejects": rejs}
    if track == "interest":
        txs = [_tx_for_public(x, contract_id) for x in p2b_body.get("outputs", {}).get("items", [])]
        if contract_id == "E2-2":
            return {"generatedTransactions": txs, "diagnostics": diagnostics}
        return {"transactions": txs}
    if track == "reporting":
        lines = _report_lines_from_audit(audit or {})
        if not lines and "records" in p2b_body:
            lines = [json.dumps(x, sort_keys=True) for x in p2b_body.get("records", {}).get("items", [])]
        if contract_id == "E2-2":
            return {"lines": lines, "diagnostics": diagnostics}
        return {"lines": lines}
    raise ValueError(track)


def execute(contract_id: str, track: str, body: dict[str, Any]) -> dict[str, Any]:
    validate_request(contract_id, track, body)
    OUTPUTS.mkdir(exist_ok=True)
    os.environ["P2B_FIXTURE_REGISTRY"] = str(REGISTRY)
    p2b = load_p2b()
    fn: Callable[[str], tuple[int, dict[str, Any], dict[str, Any]]] = getattr(p2b, track)
    started = time.time()
    status, p2b_body, p2b_audit = fn(f"p2c-{contract_id}-{track}-{int(started*1000)}")
    diagnostics = diagnostics_from_audit(p2b_audit)
    projected = project_response(contract_id, track, status, p2b_body, diagnostics, p2b_audit)
    audit = {
        "kind": "p2c-few-shot-facade-invocation",
        "contractId": contract_id,
        "contractOriginal": str(CONTRACTS[contract_id].original_path),
        "contractOriginalSha256": sha256(CONTRACTS[contract_id].original_path),
        "track": track,
        "path": CONTRACTS[contract_id].paths[track],
        "status": status,
        "requestShape": sorted(body.keys()),
        "localDatasetBindingResolution": {
            "scope": "infraestrutura técnica local P2c/P3 somente; não expõe endpoints setup/reset/telemetria; não altera contratos",
            "registry": str(REGISTRY),
            "registrySha256": sha256(REGISTRY),
            "p2bRunDirectory": p2b_audit.get("INV", {}).get("workdir"),
        },
        "semanticLimits": [
            "A fachada valida e preserva o envelope few-shot, mas a execução técnica usa pacotes locais P3 por trilha como recursos já provisionados; arrays JSON de entrada não são promovidos a oráculo de negócio.",
            "Ausência de captura é classificada como indisponibilidade técnica, não como vazio positivo.",
            "Motivo 0109 permanece interno: não é convertido em rejeição pública comum.",
            "TRANREPT é lido em registros físicos de 133 bytes, preservando ordem e duplicatas.",
        ],
        "response": projected,
        "p2bAuditPath": str(Path(p2b_audit.get("INV", {}).get("workdir", ".")) / "audit.json"),
        "durationSeconds": round(time.time() - started, 3),
    }
    out_dir = ROOT / "runs" / contract_id / track
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{int(started*1000)}-audit.json"
    out_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n")
    return {"status": status, "body": projected, "auditPath": str(out_path), "p2bAuditPath": audit["p2bAuditPath"]}


def sample_request(contract_id: str, track: str) -> dict[str, Any]:
    tx_str = {"transactionId":"TEST000000000001","typeCode":"01","categoryCode":"0001","source":"TEST","description":"LOCAL SYNTHETIC FIXTURE","amount":25.0,"merchantId":"000000001","merchantName":"TEST MERCHANT","merchantCity":"TEST CITY","merchantZip":"0000000000","cardNumber":"0000000000000001","originalTimestamp":"2025-01-01-00.00.00.000000","processingTimestamp":"2025-01-01-00.00.00.000000","filler":""}
    tx_num = dict(tx_str, categoryCode=1, merchantId=1)
    if contract_id == "E2-1":
        return {"posting": {"dailyTransactions": [tx_str]}, "interest": {"transactionIdPrefix": "2022071800"}, "reporting": {"transactions": [tx_str], "dateParameterRecords": ["2025-01-01 2025-12-31"]}}[track]
    if contract_id == "E2-2":
        bindings = {k: LOCAL_BINDING_PREFIX + k for k in BINDING_FIELDS[track]}
        if track == "posting": return {"bindings": bindings, "transactions": [tx_num]}
        if track == "interest": return {"bindings": bindings, "parameterDate": "2022071800"}
        return {"bindings": bindings, "transactions": [tx_num], "dateParameterRecords": ["2025-01-01 2025-12-31"]}
    if track == "posting": return {"transactions": [tx_num]}
    if track == "interest": return {"transactionIdPrefix": "2022071800"}
    return {"transactions": [tx_num], "dateParameterRecords": ["2025-01-01 2025-12-31".ljust(80)]}


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    one = sub.add_parser("invoke")
    one.add_argument("contract_id", choices=sorted(CONTRACTS))
    one.add_argument("track", choices=TRACKS)
    one.add_argument("--request-json", type=Path)
    sub.add_parser("smoke-all")
    args = ap.parse_args()
    if args.cmd == "invoke":
        body = json.loads(args.request_json.read_text()) if args.request_json else sample_request(args.contract_id, args.track)
        print(json.dumps(execute(args.contract_id, args.track, body), indent=2, ensure_ascii=False))
    elif args.cmd == "smoke-all":
        results = []
        for cid in sorted(CONTRACTS):
            for track in TRACKS:
                rec = {"contractId": cid, "track": track, "operation": CONTRACTS[cid].paths[track]}
                try:
                    result = execute(cid, track, sample_request(cid, track))
                    rec.update({"implemented": True, "exercised": True, "blocked": False, "status": result["status"], "auditPath": result["auditPath"], "p2bAuditPath": result["p2bAuditPath"]})
                except Exception as exc:
                    rec.update({"implemented": True, "exercised": False, "blocked": True, "blocker": repr(exc)})
                results.append(rec)
        report = {"kind": "p2c-few-shot-smoke-all", "registry": str(REGISTRY), "results": results, "overallExercised": all(r["exercised"] for r in results)}
        OUTPUTS.mkdir(exist_ok=True)
        path = OUTPUTS / "smoke-all-report.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

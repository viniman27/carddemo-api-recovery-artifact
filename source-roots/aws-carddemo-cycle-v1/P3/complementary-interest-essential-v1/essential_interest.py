from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CYCLE = HERE.parents[1]
P2B = CYCLE / "P2b"
sys.path.insert(0, str(P2B))
import p2b_binding as p2b  # type: ignore

EVIDENCE = HERE / "evidence"
COPYBOOKS = CYCLE.parent / "aws-carddemo-preparation" / "research-corpus" / "app" / "cpy"


@dataclass(frozen=True)
class InterestCase:
    case_id: str
    parm_date: str
    accounts: list[dict[str, str]]
    xrefs: list[dict[str, str]]
    disc: list[dict[str, str]]
    balances: list[dict[str, str]]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_monthly_interest(category_balance: str, annual_rate: str) -> Decimal:
    # COBOL target field is PIC S9(09)V99; assignment truncates to cents in this runtime.
    return (Decimal(category_balance) * Decimal(annual_rate) / Decimal("1200")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)


def money_cents_text(value: Decimal) -> str:
    cents = int((value * 100).to_integral_value(rounding=ROUND_DOWN))
    return f"{cents:011d}"


def _cob_amount(value: str) -> str:
    return str(Decimal(value))


def _q(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def _group(s: str) -> str:
    return s[:10].ljust(10)


def _ensure_runtime() -> None:
    required = [p2b.BUILD / "P2B_INTEREST_DRIVER", p2b.BUILD / "CBACT04C.dylib", p2b.BUILD / "io_ACCTFILE"]
    if all(x.exists() for x in required):
        return
    subprocess.run([sys.executable, "p2b_binding.py", "build"], cwd=P2B, check=True, text=True)


def _builder_source(case: InterestCase) -> str:
    lines = [
        "identification division. program-id. BUILDINTEREST.",
        "environment division. input-output section. file-control.",
        " select TCATBAL-FILE assign to TCATBALF organization indexed access sequential record key FD-TRAN-CAT-KEY file status FS-TCAT.",
        " select XREF-FILE assign to XREFFILE organization indexed access sequential record key FD-XREF-CARD-NUM alternate record key FD-XREF-ACCT-ID file status FS-XREF.",
        " select ACCOUNT-FILE assign to ACCTFILE organization indexed access random record key FD-ACCT-ID file status FS-ACCT.",
        " select DISCGRP-FILE assign to DISCGRP organization indexed access random record key FD-DISCGRP-KEY file status FS-DISC.",
        "data division. file section.",
        "fd TCATBAL-FILE. 01 FD-TRAN-CAT-BAL-RECORD. 05 FD-TRAN-CAT-KEY. 10 FD-TRANCAT-ACCT-ID pic 9(11). 10 FD-TRANCAT-TYPE-CD pic x(02). 10 FD-TRANCAT-CD pic 9(04). 05 FD-FD-TRAN-CAT-DATA pic x(33).",
        "fd XREF-FILE. 01 FD-XREFFILE-REC. 05 FD-XREF-CARD-NUM pic x(16). 05 FD-XREF-CUST-NUM pic 9(09). 05 FD-XREF-ACCT-ID pic 9(11). 05 FD-XREF-FILLER pic x(14).",
        "fd DISCGRP-FILE. 01 FD-DISCGRP-REC. 05 FD-DISCGRP-KEY. 10 FD-DIS-ACCT-GROUP-ID pic x(10). 10 FD-DIS-TRAN-TYPE-CD pic x(02). 10 FD-DIS-TRAN-CAT-CD pic 9(04). 05 FD-DISCGRP-DATA pic x(34).",
        "fd ACCOUNT-FILE. 01 FD-ACCTFILE-REC. 05 FD-ACCT-ID pic 9(11). 05 FD-ACCT-DATA pic x(289).",
        "working-storage section.",
        ">>source format fixed", "       COPY CVTRA01Y.", "       >>source format free",
        ">>source format fixed", "       COPY CVACT03Y.", "       >>source format free",
        ">>source format fixed", "       COPY CVTRA02Y.", "       >>source format free",
        ">>source format fixed", "       COPY CVACT01Y.", "       >>source format free",
        "01 FS-TCAT pic xx. 01 FS-XREF pic xx. 01 FS-ACCT pic xx. 01 FS-DISC pic xx.",
        "procedure division.",
        " open output TCATBAL-FILE XREF-FILE ACCOUNT-FILE DISCGRP-FILE",
    ]
    for a in case.accounts:
        lines += [
            f" move {a['acct']} to ACCT-ID",
            " move 'Y' to ACCT-ACTIVE-STATUS",
            " move 0 to ACCT-CURR-BAL",
            " move 10000.00 to ACCT-CREDIT-LIMIT",
            " move 5000.00 to ACCT-CASH-CREDIT-LIMIT",
            " move '2020-01-01' to ACCT-OPEN-DATE",
            " move '2030-01-01' to ACCT-EXPIRAION-DATE",
            " move '2025-01-01' to ACCT-REISSUE-DATE",
            " move 0 to ACCT-CURR-CYC-CREDIT ACCT-CURR-CYC-DEBIT",
            " move '99999' to ACCT-ADDR-ZIP",
            f" move {_q(_group(a['group']))} to ACCT-GROUP-ID",
            " move ACCOUNT-RECORD to FD-ACCTFILE-REC",
            " write FD-ACCTFILE-REC",
        ]
    for x in case.xrefs:
        lines += [
            f" move {_q(x['card'])} to FD-XREF-CARD-NUM",
            " move 000000001 to FD-XREF-CUST-NUM",
            f" move {x['acct']} to FD-XREF-ACCT-ID",
            " move spaces to FD-XREF-FILLER",
            " write FD-XREFFILE-REC",
        ]
    for d in case.disc:
        lines += [
            f" move {_q(_group(d['group']))} to DIS-ACCT-GROUP-ID",
            f" move {_q(d['type'])} to DIS-TRAN-TYPE-CD",
            f" move {d['cat']} to DIS-TRAN-CAT-CD",
            f" move {_cob_amount(d['rate'])} to DIS-INT-RATE",
            " move DIS-GROUP-RECORD to FD-DISCGRP-REC",
            " write FD-DISCGRP-REC",
        ]
    for b in sorted(case.balances, key=lambda r: (r["acct"], r["type"], r["cat"])):
        lines += [
            f" move {b['acct']} to TRANCAT-ACCT-ID",
            f" move {_q(b['type'])} to TRANCAT-TYPE-CD",
            f" move {b['cat']} to TRANCAT-CD",
            f" move {_cob_amount(b['balance'])} to TRAN-CAT-BAL",
            " move TRAN-CAT-BAL-RECORD to FD-TRAN-CAT-BAL-RECORD",
            " write FD-TRAN-CAT-BAL-RECORD",
        ]
    lines += [" close TCATBAL-FILE XREF-FILE ACCOUNT-FILE DISCGRP-FILE", " stop run."]
    return "\n".join(lines) + "\n"


def _run(cmd: list[str | Path], cwd: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    merged = dict(os.environ)
    if env:
        merged.update({k: str(v) for k, v in env.items()})
    p = subprocess.run([str(x) for x in cmd], cwd=cwd, env=merged, text=True, capture_output=True, timeout=60)
    rec = {"cmd": [str(x) for x in cmd], "cwd": str(cwd), "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    if p.returncode != 0:
        raise RuntimeError(json.dumps(rec, indent=2))
    return rec


def _dump_indexed(workdir: Path, dd: str, raw: Path) -> dict[str, Any]:
    p2b.io_file(workdir, dd, "DUMP", raw)
    data = raw.read_bytes()
    size = p2b.IO_SPECS[dd][0]
    return {"path": str(raw), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "classification": "available" if len(data) % size == 0 else "truncated", "recordCount": len(data) // size, "rawHexPrefix": data[:64].hex()}


def _parse_acct_dump(path: Path) -> dict[str, dict[str, str]]:
    data = path.read_bytes()
    out: dict[str, dict[str, str]] = {}
    for i in range(0, len(data), 300):
        rec = data[i:i+300]
        if len(rec) < 300:
            continue
        acct = rec[0:11].decode("ascii")
        out[acct] = {"currentBalanceCentsText": rec[12:24].decode("ascii"), "rawHex": rec.hex(), "recordOffset": i}
    return out


def _file_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False, "classification": "missing"}
    return {"path": str(path), "exists": True, "bytes": path.stat().st_size, "sha256": sha256(path), "classification": "available" if path.stat().st_size else "known_empty"}


def _descriptor_hash(fixture: dict[str, Any]) -> str:
    canonical = {k: v for k, v in fixture.items() if k != "contentSha256"}
    return hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _prepare_package(case: InterestCase, case_dir: Path) -> tuple[Path, Path, dict[str, Any]]:
    package = case_dir / "package"
    if package.exists():
        shutil.rmtree(package)
    package.mkdir(parents=True)
    src = case_dir / "build_interest.cbl"
    src.write_text(_builder_source(case), encoding="utf-8")
    exe = case_dir / "build_interest"
    _run(["cobc", "-std=ibm", "-fsign=ascii", "-I", COPYBOOKS, "-x", "-free", "-o", exe, src], cwd=case_dir)
    _run([exe], cwd=package)
    (package / "PARMFILE").write_bytes(case.parm_date.encode("ascii"))
    files = {name: f"package/{name}" for name in ["TCATBALF", "ACCTFILE", "XREFFILE", "XREFFILE.1", "DISCGRP", "PARMFILE"]}
    pins = {name: {"bytes": (package / name).stat().st_size, "sha256": sha256(package / name)} for name in files}
    fixture: dict[str, Any] = {
        "fixtureId": f"{case.case_id}-local-file-package-v1",
        "track": "interest",
        "capability": "CBACT04C/INTCALC",
        "suiteUse": "p3-complementary-interest-essential-local-only",
        "materializer": {"kind": "local_file_package", "files": files, "filePins": pins},
        "provenance": {"class": "local_synthetic_support", "source": "P3 complementary-interest-essential-v1 generated physical indexed files", "officialFixture": False},
        "exposure": {"label": "technical-only", "notExtractionInput": True, "notOracle": True, "notPublicRequest": True},
        "reset": {"default": "fresh_dir_per_run", "statefulSequence": "not_used"},
    }
    fixture["contentSha256"] = _descriptor_hash(fixture)
    registry = {"kind": "p3-local-technical-fixture-selection", "status": "technical_local_only", "fixtures": [fixture]}
    registry_path = case_dir / "registry.json"
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    manifest = {"case": case.__dict__, "package": str(package), "filePins": pins, "fixtureDescriptorSha256": fixture["contentSha256"]}
    (case_dir / "input-freeze.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return package, registry_path, manifest


def _expected_transactions(case: InterestCase) -> list[dict[str, str]]:
    accounts = {a["acct"]: a for a in case.accounts}
    disc = {( _group(d["group"]), d["type"], d["cat"]): d for d in case.disc}
    default_by_type_cat = {(d["type"], d["cat"]): d for d in case.disc if _group(d["group"]) == _group("DEFAULT")}
    expected = []
    for b in sorted(case.balances, key=lambda r: (r["acct"], r["type"], r["cat"])):
        acct = accounts[b["acct"]]
        d = disc.get((_group(acct["group"]), b["type"], b["cat"])) or default_by_type_cat.get((b["type"], b["cat"]))
        rate = Decimal(d["rate"]) if d else Decimal("0")
        if rate == 0:
            continue
        amount = source_monthly_interest(b["balance"], str(rate))
        expected.append({"acct": b["acct"], "amount": money_cents_text(amount), "rate": f"{rate:.2f}", "balance": f"{Decimal(b['balance']):.2f}"})
    return expected


def run_interest_case(case: InterestCase) -> dict[str, Any]:
    _ensure_runtime()
    case_dir = EVIDENCE / case.case_id
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)
    package, registry, manifest = _prepare_package(case, case_dir)
    before_acct_raw = case_dir / "ACCTFILE.before.raw"
    before_dump = _dump_indexed(package, "ACCTFILE", before_acct_raw)
    physical_inputs = {name: {"before": _file_info(package / name)} for name in ["TCATBALF", "ACCTFILE", "XREFFILE", "XREFFILE.1", "DISCGRP", "PARMFILE"]}
    physical_inputs["ACCTFILE"]["qualifiedDumpBefore"] = before_dump
    old_registry = os.environ.get(p2b.FIXTURE_ENV)
    old_runs, old_log = p2b.RUNS, p2b.COMMAND_LOG
    p2b.RUNS = case_dir / "p2b-runs"
    p2b.COMMAND_LOG = case_dir / "command-log.jsonl"
    os.environ[p2b.FIXTURE_ENV] = str(registry)
    try:
        status, body, audit = p2b.interest(f"p3-interest-essential-{case.case_id}")
    finally:
        p2b.RUNS, p2b.COMMAND_LOG = old_runs, old_log
        if old_registry is None:
            os.environ.pop(p2b.FIXTURE_ENV, None)
        else:
            os.environ[p2b.FIXTURE_ENV] = old_registry
    wd = Path(audit["INV"]["workdir"])
    after_acct_raw = case_dir / "ACCTFILE.after.raw"
    after_dump = _dump_indexed(wd, "ACCTFILE", after_acct_raw)
    for name in physical_inputs:
        physical_inputs[name]["after"] = _file_info(wd / name)
    physical_inputs["ACCTFILE"]["qualifiedDumpAfter"] = after_dump
    before_accounts = _parse_acct_dump(before_acct_raw)
    after_accounts = _parse_acct_dump(after_acct_raw)
    expected = _expected_transactions(case)
    observed = body.get("outputs", {}).get("items", []) if isinstance(body, dict) else []
    transact_path = wd / "TRANSACT"
    transact_bytes = transact_path.read_bytes() if transact_path.exists() else b""
    observed_with_provenance = []
    for idx, item in enumerate(observed):
        enriched = dict(item)
        raw = transact_bytes[idx * 350:(idx + 1) * 350]
        enriched["rawBytesHex"] = raw.hex()
        enriched["provenance"] = {"kind": "raw_file_record", "artifact": str(transact_path), "recordOffset": idx * 350, "recordLength": len(raw), "sha256": hashlib.sha256(raw).hexdigest() if raw else None}
        observed_with_provenance.append(enriched)
    failures: list[str] = []
    if [x.get("amount") for x in observed] != [x["amount"] for x in expected]:
        failures.append("observed interest amounts differ from independent source-derived expected cents text")
    expected_cards = [{x["acct"]: x["card"] for x in case.xrefs}[e["acct"]] for e in expected]
    if [x.get("cardReference") for x in observed] != expected_cards:
        failures.append("observed card references differ from XREFFILE account lookup")
    acct_deltas = {}
    for acct, before in before_accounts.items():
        after = after_accounts.get(acct, before)
        delta = int(after["currentBalanceCentsText"]) - int(before["currentBalanceCentsText"])
        is_final = acct == sorted([b["acct"] for b in case.balances])[-1]
        acct_deltas[acct] = {"beforeCentsText": before["currentBalanceCentsText"], "afterCentsText": after["currentBalanceCentsText"], "deltaCentsText": f"{delta:011d}", "partition": "source_eof_final_account_not_rewritten" if is_final else "account_transition_rewrite"}
    file_effects = {}
    for name in ["TRANSACT", "ACCTFILE", "XREFFILE", "XREFFILE.1", "DISCGRP", "TCATBALF"]:
        before = package / name
        after = wd / name
        file_effects[name] = {"before": _file_info(before), "after": _file_info(after), "changed": (sha256(before) if before.exists() else None) != (sha256(after) if after.exists() else None)}
    result = {
        "caseId": case.case_id,
        "status": status,
        "response": body,
        "observedTransactions": observed,
        "observedTransactionsWithProvenance": observed_with_provenance,
        "sourceExpected": {"transactions": expected, "formula": "COMPUTE WS-MONTHLY-INT = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200; PIC S9(09)V99 cents truncation observed", "sourceAnchors": ["app/cbl/CBACT04C.cbl:214-216", "app/cbl/CBACT04C.cbl:415-439", "app/cbl/CBACT04C.cbl:462-500", "app/cbl/CBACT04C.cbl:188-221"]},
        "physicalInputs": physical_inputs,
        "fileEffects": file_effects,
        "accountDeltas": acct_deltas,
        "auditPath": str(wd / "audit.json"),
        "p2bWorkdir": str(wd),
        "inputFreeze": manifest,
        "checks": {"failures": failures},
    }
    (case_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result

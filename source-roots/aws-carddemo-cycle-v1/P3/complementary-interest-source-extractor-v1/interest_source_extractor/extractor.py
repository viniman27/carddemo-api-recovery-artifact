from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from typing import Any

TRANSACTION_SPANS = {
    "id": (0, 16),
    "type": (16, 18),
    "category": (18, 22),
    "source": (22, 32),
    "description": (32, 132),
    "amountCentsText": (132, 143),
    "card": (262, 278),
}

RAWIO_TEMPLATE = r'''
>>source format free
identification division.
program-id. RAWIO.
environment division.
input-output section.
file-control.
 select raw-file assign to RAW organization sequential file status fs.
 select idx-file assign to IDX organization indexed access sequential record key idx-key file status ix.
data division.
file section.
fd raw-file.
01 raw-rec pic x({size}).
fd idx-file.
01 idx-rec.
 02 idx-key pic x({key}).
 02 idx-rest pic x({rest}).
working-storage section.
01 fs pic xx.
01 ix pic xx.
01 op pic x(8).
procedure division.
 accept op from environment 'IO_MODE'
 evaluate function trim(op)
 when 'DUMP'
   open input idx-file
   if ix not = '00' perform bad-index end-if
   open output raw-file
   if fs not = '00' perform bad-raw end-if
   perform until ix = '10'
     read idx-file next record
     evaluate ix
       when '00'
         move idx-rec to raw-rec
         write raw-rec
         if fs not = '00' perform bad-raw end-if
       when '10' continue
       when other perform bad-index
     end-evaluate
   end-perform
 when other
   display 'INVALID IO_MODE' upon syserr
   stop run returning 12
 end-evaluate
 close raw-file idx-file
 stop run returning 0.
bad-raw.
 display 'RAW STATUS=' fs upon syserr
 stop run returning 12.
bad-index.
 display 'INDEX STATUS=' ix upon syserr
 stop run returning 12.
'''


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pin(path: Path, label: str | None = None) -> dict[str, Any]:
    return {"label": label or path.name, "path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def verify_pin(p: dict[str, Any]) -> list[str]:
    path = Path(p["path"])
    if not path.exists():
        return [f"missing:{path}"]
    out: list[str] = []
    if path.stat().st_size != p.get("bytes"):
        out.append(f"bytes mismatch:{path}")
    if sha256_file(path) != p.get("sha256"):
        out.append(f"sha mismatch:{path}")
    return out


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def decode_display_decimal(raw: bytes, scale: int) -> Decimal:
    text = raw.decode("ascii", errors="strict")
    sign = -1 if text.startswith("-") else 1
    digits = "".join(ch for ch in text if ch.isdigit()) or "0"
    return Decimal(sign) * (Decimal(int(digits)) / (Decimal(10) ** scale))


def cents_text_to_decimal(cents_text: str) -> Decimal:
    digits = "".join(ch for ch in str(cents_text) if ch.isdigit()) or "0"
    return Decimal(int(digits)) / Decimal(100)


def decimal_to_cents_text(value: Decimal) -> str:
    cents = int((value * Decimal(100)).to_integral_value(rounding=ROUND_DOWN))
    sign = "-" if cents < 0 else ""
    return sign + f"{abs(cents):011d}"


def compute_monthly_interest_cents(balance: Decimal, annual_rate: Decimal) -> str:
    # Faithful to the current GnuCOBOL/CBACT04C branch: COMPUTE into PIC S9(09)V99 truncates fractional cents.
    value = (balance * annual_rate / Decimal("1200")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    return decimal_to_cents_text(value)


def _run(cmd: list[str | Path], cwd: Path, env: dict[str, str] | None = None) -> None:
    merged = dict(os.environ)
    if env:
        merged.update({k: str(v) for k, v in env.items()})
    p = subprocess.run([str(x) for x in cmd], cwd=cwd, env=merged, text=True, capture_output=True, timeout=120)
    if p.returncode != 0:
        raise RuntimeError(json.dumps({"cmd": [str(x) for x in cmd], "cwd": str(cwd), "exit": p.returncode, "stdout": p.stdout, "stderr": p.stderr}, indent=2))


def _compile_rawio(work: Path, dd: str, size: int, key_len: int) -> Path:
    src = work / f"rawio_{dd}.cbl"
    exe = work / f"rawio_{dd}"
    src.write_text(RAWIO_TEMPLATE.format(size=size, key=key_len, rest=size - key_len), encoding="utf-8")
    _run(["cobc", "-x", "-free", "-o", exe, src], cwd=work)
    return exe


def dump_indexed_from_copy(run_dir: Path, dd: str, size: int, key_len: int, scratch: Path) -> dict[str, Any]:
    src = run_dir / dd
    if not src.exists():
        return {"ddName": dd, "classification": "missing", "records": [], "sourcePin": None}
    work = scratch / dd
    work.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, work / dd)
    exe = _compile_rawio(work, dd, size, key_len)
    raw = work / f"{dd}.raw"
    _run([exe], cwd=work, env={"IO_MODE": "DUMP", "DD_RAW": raw, "DD_IDX": work / dd})
    data = raw.read_bytes()
    records = []
    for offset in range(0, len(data), size):
        rec = data[offset:offset + size]
        if len(rec) == size and rec.strip(b"\x00 "):
            records.append({"dumpRecordOffset": offset, "logicalBytes": rec})
    return {"ddName": dd, "classification": "available", "rawPath": str(raw), "rawSha256": sha256_file(raw), "rawBytes": len(data), "records": records, "sourcePin": pin(src, f"before-input-{dd}")}


def _prov(source: Path, dump: dict[str, Any], rec: dict[str, Any], span: tuple[int, int] | None = None) -> dict[str, Any]:
    logical = rec["logicalBytes"] if span is None else rec["logicalBytes"][span[0]:span[1]]
    return {
        "kind": "qualified_indexed_bdb_dump",
        "physicalFile": str(source),
        "physicalFileSha256": sha256_file(source),
        "dumpRawSha256": dump["rawSha256"],
        "dumpRecordOffset": rec["dumpRecordOffset"],
        "recordLength": len(rec["logicalBytes"]),
        "logicalBytesHex": logical.hex(),
        "fieldSpan": list(span) if span else [0, len(rec["logicalBytes"])],
        "readOnlyCopy": True,
    }


def _parse_tcat(run_dir: Path, dump: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    src = run_dir / "TCATBALF"
    for rec in dump["records"]:
        raw = rec["logicalBytes"]
        acct = raw[0:11].decode("ascii")
        typ = raw[11:13].decode("ascii")
        cat = raw[13:17].decode("ascii")
        bal = decode_display_decimal(raw[17:28], 2)
        out.append({"key": {"accountId": acct, "type": typ, "category": cat}, "balance": f"{bal:.2f}", "provenance": _prov(src, dump, rec, (17, 28))})
    return out


def _parse_disc(run_dir: Path, dump: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    src = run_dir / "DISCGRP"
    for rec in dump["records"]:
        raw = rec["logicalBytes"]
        group = raw[0:10].decode("ascii")
        typ = raw[10:12].decode("ascii")
        cat = raw[12:16].decode("ascii")
        rate = decode_display_decimal(raw[16:22], 2)
        out.append({"key": {"group": group, "type": typ, "category": cat}, "rate": f"{rate:.2f}", "provenance": _prov(src, dump, rec, (16, 22))})
    return out


def _parse_acct(run_dir: Path, dump: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    src = run_dir / "ACCTFILE"
    for rec in dump["records"]:
        raw = rec["logicalBytes"]
        acct = raw[0:11].decode("ascii")
        group = raw[112:122].decode("ascii")
        out[acct] = {"accountId": acct, "group": group, "provenance": _prov(src, dump, rec, (112, 122))}
    return out


def _parse_xref(run_dir: Path, dump: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    src = run_dir / "XREFFILE"
    for rec in dump["records"]:
        raw = rec["logicalBytes"]
        card = raw[0:16].decode("ascii")
        acct = raw[25:36].decode("ascii")
        out[acct] = {"accountId": acct, "card": card, "provenance": _prov(src, dump, rec, (0, 36))}
    return out


def extract_inputs_for_run_dir(run_dir: Path, case_id: str | None = None) -> dict[str, Any]:
    run_dir = Path(run_dir)
    with tempfile.TemporaryDirectory(prefix="interest-source-dump-") as td:
        scratch = Path(td)
        dumps = {
            "TCATBALF": dump_indexed_from_copy(run_dir, "TCATBALF", 50, 17, scratch),
            "DISCGRP": dump_indexed_from_copy(run_dir, "DISCGRP", 50, 16, scratch),
            "ACCTFILE": dump_indexed_from_copy(run_dir, "ACCTFILE", 300, 11, scratch),
            "XREFFILE": dump_indexed_from_copy(run_dir, "XREFFILE", 50, 16, scratch),
        }
    balances = _parse_tcat(run_dir, dumps["TCATBALF"])
    rates = _parse_disc(run_dir, dumps["DISCGRP"])
    accounts = _parse_acct(run_dir, dumps["ACCTFILE"])
    xrefs = _parse_xref(run_dir, dumps["XREFFILE"])
    pins = [d["sourcePin"] for d in dumps.values() if d.get("sourcePin")]
    for extra in ["XREFFILE.1", "PARMFILE"]:
        p = run_dir / extra
        if p.exists():
            pins.append(pin(p, f"before-input-{extra}"))
    return {
        "caseId": case_id,
        "method": "read_only_dump_on_copy",
        "semanticReader": "indexed_bdb_qualified_rawio_dump",
        "balances": balances,
        "rates": rates,
        "accountsById": accounts,
        "xrefsByAccountId": xrefs,
        "artifactPins": pins,
    }


def parse_transact_record(raw: bytes, offset: int, path: Path) -> dict[str, Any]:
    def text(name: str) -> str:
        a, b = TRANSACTION_SPANS[name]
        return raw[a:b].decode("latin1", errors="replace").rstrip("\x00 ")
    return {
        "id": text("id"),
        "type": text("type"),
        "category": text("category")[-4:].zfill(4),
        "source": text("source"),
        "description": text("description"),
        "observedAmountCentsText": text("amountCentsText"),
        "card": text("card"),
        "provenance": {"kind": "raw_sequential_record", "artifact": str(path), "artifactSha256": sha256_file(path), "recordOffset": offset, "recordLength": 350, "logicalBytesHex": raw.hex()},
    }


def parse_transactions(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "TRANSACT"
    data = path.read_bytes() if path.exists() else b""
    out = []
    for offset in range(0, len(data), 350):
        raw = data[offset:offset + 350]
        if len(raw) == 350 and raw.strip(b"\x00 "):
            out.append(parse_transact_record(raw, offset, path))
    return out


def _effective_rate(balance: dict[str, Any], accounts: dict[str, Any], rates: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
    acct = accounts.get(balance["key"]["accountId"], {})
    group = acct.get("group", "")
    typ = balance["key"]["type"]
    cat = balance["key"]["category"]
    for r in rates:
        if r["key"]["group"] == group and r["key"]["type"] == typ and r["key"]["category"] == cat:
            return r, "specific_group"
    for r in rates:
        if r["key"]["group"].rstrip() == "DEFAULT" and r["key"]["type"] == typ and r["key"]["category"] == cat:
            return r, "default_group"
    return None, "absent_group_zero_rate"


def _expected_transactions(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    expected = []
    accounts = inputs["accountsById"]
    xrefs = inputs["xrefsByAccountId"]
    for bal in inputs["balances"]:
        rate, source = _effective_rate(bal, accounts, inputs["rates"])
        rate_dec = Decimal(rate["rate"]) if rate else Decimal("0")
        if rate_dec == 0:
            continue
        balance_dec = Decimal(bal["balance"])
        expected.append({
            "accountId": bal["key"]["accountId"],
            "type": bal["key"]["type"],
            "category": bal["key"]["category"],
            "balance": f"{balance_dec:.2f}",
            "rate": f"{rate_dec:.2f}",
            "rateSource": source,
            "expectedAmountCentsText": compute_monthly_interest_cents(balance_dec, rate_dec),
            "card": xrefs.get(bal["key"]["accountId"], {}).get("card"),
            "inputProvenance": {"balance": bal["provenance"], "rate": rate["provenance"] if rate else None, "account": accounts.get(bal["key"]["accountId"], {}).get("provenance"), "xref": xrefs.get(bal["key"]["accountId"], {}).get("provenance")},
        })
    return expected


def _response_path_from_run_dir(run_dir: Path, case: dict[str, Any]) -> Path | None:
    # zero-shot run dirs sit under .../zero-shot-runs/p2b-runs/<run>; response is under sibling contract/track.
    parents = [run_dir] + list(run_dir.parents)[:5]
    for parent in parents:
        hits = list(parent.glob(f"{case['contractId']}/{case['track']}/*/response.json"))
        if hits:
            return hits[0]
    hits = list(run_dir.parent.rglob("response.json")) if run_dir.parent.exists() else []
    return hits[0] if hits else None


def check_case(case: dict[str, Any], cycle_root: Path) -> dict[str, Any]:
    run_dir = Path(case["businessCheck"]["evidence"][0]["path"]).parent
    inputs = extract_inputs_for_run_dir(run_dir, case_id=case["caseId"])
    expected = _expected_transactions(inputs)
    observed = parse_transactions(run_dir)
    txs = []
    failures: list[str] = []
    for idx, exp in enumerate(expected):
        obs = observed[idx] if idx < len(observed) else None
        if obs is None:
            failures.append(f"missing_observed_transaction:{idx}")
            continue
        ok_amount = obs["observedAmountCentsText"] == exp["expectedAmountCentsText"]
        ok_card = (not exp.get("card")) or obs.get("card") == exp.get("card")
        if not ok_amount:
            failures.append(f"amount_mismatch:{idx}:{obs['observedAmountCentsText']}!={exp['expectedAmountCentsText']}")
        if not ok_card:
            failures.append(f"card_mismatch:{idx}:{obs.get('card')}!={exp.get('card')}")
        txs.append({**exp, "observedAmountCentsText": obs["observedAmountCentsText"], "observedCard": obs.get("card"), "observedProvenance": obs["provenance"], "formulaMatched": ok_amount and ok_card})
    if len(observed) > len(expected):
        failures.append(f"unexpected_observed_transactions:{len(observed) - len(expected)}")
    pins = list(inputs["artifactPins"])
    for name in ["TRANSACT", "audit.json"]:
        p = run_dir / name
        if p.exists():
            pins.append(pin(p, name))
    response_path = _response_path_from_run_dir(run_dir, case)
    if response_path and response_path.exists():
        pins.append(pin(response_path, "api-response"))
    pin_failures = [f for p in pins for f in verify_pin(p)]
    verdict = "inconclusive" if not expected else ("fail" if failures else "pass")
    return {
        "caseId": case["caseId"],
        "contractId": case["contractId"],
        "operationId": case.get("operationId"),
        "track": "interest",
        "httpStatus": case.get("httpStatus"),
        "semanticVerdict": verdict,
        "failures": failures,
        "transactions": txs,
        "sourceInputs": inputs,
        "apiVisibleEvidence": {"httpStatus": case.get("httpStatus"), "responseSha256": case.get("responseSha256"), "responsePath": str(response_path) if response_path else None, "publicExposureSeparatedFromInternalRaw": True},
        "byteProvenance": {"pins": pins, "pinVerificationFailures": pin_failures},
        "noApiRerun": True,
        "sourceFormula": "COMPUTE WS-MONTHLY-INT = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200; PIC S9(09)V99 cents truncation in current source/runtime",
        "sourceAnchors": ["app/cbl/CBACT04C.cbl:210-216", "app/cbl/CBACT04C.cbl:415-439", "app/cbl/CBACT04C.cbl:462-500", "app/cpy/CVTRA01Y.cpy:4-10", "app/cpy/CVTRA02Y.cpy:4-10"],
    }


def run(run_root: Path, cycle_root: Path) -> dict[str, Any]:
    comparison = load_json(run_root / "comparison.json")
    cases = [check_case(c, cycle_root) for c in comparison["cases"] if c.get("track") == "interest"]
    counts = Counter(c["semanticVerdict"] for c in cases)
    return {
        "kind": "complementary-interest-source-extractor-v1-results",
        "createdUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "scope": "Read-only source-derived rate/balance extraction over preserved cross-arm interest artifacts only; no API, COBOL business, model, or quarantine reruns.",
        "summary": {"caseCount": len(cases), "semanticVerdictCounts": dict(counts), "pinVerificationFailureCount": sum(len(c["byteProvenance"]["pinVerificationFailures"]) for c in cases), "noApiReruns": True},
        "cases": cases,
        "sourceRunPins": [pin(run_root / "comparison.json", "comparison"), pin(run_root / "run" / "campaign-report.json", "campaign-report")],
    }


def write_status(out: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Complementary interest source extractor v1",
        "",
        "Status: completed read-only arithmetic qualification for preserved cross-arm interest cases.",
        "",
        f"- Cases: {summary['caseCount']}",
        f"- Semantic verdicts: {summary['semanticVerdictCounts']}",
        f"- Pin verification failures: {summary['pinVerificationFailureCount']}",
        "- Boundary: internal raw COBOL records, API-visible responses, and source input bytes are reported separately.",
        "- Execution: no business/API reruns; indexed inputs were dumped from per-run copies only.",
    ]
    (out.parent / "STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", type=Path, required=True)
    ap.add_argument("--cycle-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    payload = run(args.run_root, args.cycle_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    write_status(args.out, payload)
    print(json.dumps({"ok": True, **payload["summary"], "out": str(args.out)}, ensure_ascii=False))
    return 0

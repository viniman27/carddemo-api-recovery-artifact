from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any


TX_SPANS = {
    "id": (0, 16),
    "type": (16, 18),
    "category": (18, 22),
    "source": (22, 32),
    "description": (32, 132),
    "amountRaw": (132, 143),
    "merchant": (143, 152),
    "merchantName": (152, 202),
    "merchantCity": (202, 252),
    "merchantPostalText": (252, 262),
    "card": (262, 278),
    "origTs": (278, 304),
    "procTs": (304, 330),
}


def _text(data: bytes, start: int, end: int) -> str:
    return data[start:end].decode("ascii", "strict").strip()


def _money(raw: str) -> str:
    if not raw.strip():
        return "0.00"
    return f"{(Decimal(int(raw)) / Decimal(100)):.2f}"


def transaction_record_fields(raw: bytes) -> dict[str, str]:
    if len(raw) != 350:
        raise ValueError(f"transaction record must be 350 bytes, got {len(raw)}")
    fields = {name: _text(raw, start, end) for name, (start, end) in TX_SPANS.items()}
    fields["amount"] = _money(fields.pop("amountRaw"))
    return fields


def parse_report_capture(data: bytes) -> dict[str, Any]:
    framing: dict[str, Any] = {"bytes": len(data), "recordSize": 133, "classification": None}
    if len(data) == 0:
        framing["classification"] = "known_empty"
        return {"framing": framing, "details": [], "totals": [], "unknown": []}
    if len(data) % 133 != 0:
        framing.update({"classification": "truncated", "remainderBytes": len(data) % 133})
        return {"framing": framing, "details": [], "totals": [], "unknown": []}
    details: list[dict[str, Any]] = []
    totals: list[dict[str, Any]] = []
    unknown: list[dict[str, Any]] = []
    for idx in range(0, len(data), 133):
        rec = data[idx:idx + 133]
        raw = rec.decode("ascii", "replace")
        text = raw.rstrip()
        if not text.strip() or set(text.strip()) == {"-"} or text.startswith("Transaction ID") or raw.startswith("DALYREPT"):
            continue
        if raw.startswith("Page Total") or raw.startswith("Account Total") or raw.startswith("Grand Total"):
            label = raw[:20].strip()
            totals.append({"label": label, "amount": raw[97:112].strip(), "rawBytes": rec.hex(), "rawText": text})
            continue
        if len(raw) >= 112 and raw[16] == " " and raw[28] == " " and raw[31] == "-" and raw[47] == " " and raw[52] == "-":
            details.append({
                "id": raw[0:16].strip(),
                "accountReference": raw[17:28].strip(),
                "type": raw[29:31].strip(),
                "category": raw[48:52].strip(),
                "source": raw[83:93].strip(),
                "amount": raw[97:112].strip(),
                "detailLine": text,
                "reportLineBytes": rec.hex(),
            })
            continue
        unknown.append({"index": idx // 133, "rawBytes": rec.hex(), "rawText": text})
    framing["classification"] = "unmapped_meaningful" if unknown else "available"
    return {"framing": framing, "details": details, "totals": totals, "unknown": unknown}


def _read_audit(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _event_order(events: list[dict[str, Any]]) -> list[str]:
    order = []
    for ev in events:
        sel = ev.get("select")
        if sel == "TRANSACT-FILE":
            order.append("tranfile")
        elif sel == "DALYREJS-FILE":
            order.append("reject")
        elif sel:
            order.append(str(sel).lower())
    # p2b write observer only wraps writes. Account/TCATBAL updates are
    # evidenced by after snapshots, so keep trace caveat explicit elsewhere.
    return order


def _capture_sha(audit: dict[str, Any], label: str) -> dict[str, Any] | None:
    for cap in audit.get("CAP", {}).get("captures", []):
        if cap.get("label") == label:
            return cap
    return None


def _extract_posting(audit: dict[str, Any]) -> dict[str, Any]:
    wd = Path(audit["INV"]["workdir"])
    body = audit.get("RESP", {}).get("body", {})
    events = audit.get("CONV", {}).get("write_observations", {}).get("events", [])
    accepted = []
    rejects = []
    daily_records = []
    daly = wd / "DALYTRAN"
    if daly.exists():
        data = daly.read_bytes()
        for i in range(0, len(data), 350):
            chunk = data[i:i + 350]
            if len(chunk) == 350:
                daily_records.append(transaction_record_fields(chunk))
    daily_by_id = {r["id"]: r for r in daily_records}
    for ev in events:
        raw = bytes.fromhex(ev.get("rawHex", ""))
        if ev.get("select") == "TRANSACT-FILE" and len(raw) == 350:
            posted = transaction_record_fields(raw)
            accepted.append({
                "id": posted["id"],
                "rawBytes": raw.hex(),
                "daily": daily_by_id.get(posted["id"], {}),
                "posted": posted,
                "effectOrder": _event_order(events),
                "duplicatePrevalidated": False,
                "traceBoundary": "account/tcatbal effects inferred from after-capture presence only; write-order trace unavailable",
            })
        elif ev.get("select") == "DALYREJS-FILE" and len(raw) >= 430:
            candidate = transaction_record_fields(raw[:350])
            rejects.append({
                "case": "missing-card" if raw[350:354].decode("ascii", "replace") == "0100" else "other-reject",
                "rawBytes": raw.hex(),
                "reason": raw[351:354].decode("ascii", "replace"),
                "description": raw[354:430].decode("ascii", "replace").strip(),
                "candidate": candidate,
                "postedTransactionWritten": candidate.get("id") in {a.get("id") for a in accepted},
                "rejectRecordWritten": True,
            })
    return_code = audit.get("RESP", {}).get("program_exit")
    if body.get("progress", {}).get("value", {}).get("preliminaryRejectCount", 0) and return_code == 0:
        return_code = 4
    return {"returnCode": return_code, "acceptedTransactions": accepted, "rejects": rejects}


def _ascii_windows(data: bytes, width: int, key_len: int) -> list[bytes]:
    windows = []
    seen = set()
    for i in range(0, max(0, len(data) - width + 1)):
        chunk = data[i:i + width]
        if chunk in seen:
            continue
        if all((32 <= b <= 126) for b in chunk) and chunk[:key_len].strip():
            seen.add(chunk)
            windows.append(chunk)
    return windows


def _extract_interest_inputs(wd: Path) -> dict[str, dict[str, str]]:
    accounts: dict[str, str] = {}
    for rec in _ascii_windows((wd / "ACCTFILE").read_bytes(), 300, 11) if (wd / "ACCTFILE").exists() else []:
        acct = rec[0:11].decode("ascii")
        group = rec[112:122].decode("ascii").strip()
        if acct.isdigit() and group:
            accounts[acct] = group
    balances: dict[str, str] = {}
    for rec in _ascii_windows((wd / "TCATBALF").read_bytes(), 50, 17) if (wd / "TCATBALF").exists() else []:
        acct = rec[0:11].decode("ascii")
        bal = rec[17:28].decode("ascii")
        if acct.isdigit() and bal.isdigit():
            balances[acct] = _money(bal)
    rates: dict[str, str] = {}
    for rec in _ascii_windows((wd / "DISCGRP").read_bytes(), 50, 16) if (wd / "DISCGRP").exists() else []:
        group = rec[0:10].decode("ascii").strip()
        rate = rec[16:22].decode("ascii")
        if group and rate.isdigit():
            rates[group] = _money(rate)
    cards: dict[str, str] = {}
    for rec in _ascii_windows((wd / "XREFFILE").read_bytes(), 50, 16) if (wd / "XREFFILE").exists() else []:
        card = rec[0:16].decode("ascii")
        acct = rec[25:36].decode("ascii")
        if card.isdigit() and acct.isdigit():
            cards[acct] = card
    return {"accounts": accounts, "balances": balances, "rates": rates, "cards": cards}


def _extract_interest(audit: dict[str, Any]) -> dict[str, Any]:
    wd = Path(audit["INV"]["workdir"])
    tr = wd / "TRANSACT"
    observed_inputs = _extract_interest_inputs(wd)
    records = []
    written_accounts: set[str] = set()
    if tr.exists():
        data = tr.read_bytes()
        for i in range(0, len(data), 350):
            raw = data[i:i + 350]
            if len(raw) == 350:
                f = transaction_record_fields(raw)
                acct = ""
                marker = "Int. for a/c "
                if f["description"].startswith(marker):
                    acct = f["description"][len(marker):len(marker) + 11]
                    written_accounts.add(acct)
                group = observed_inputs["accounts"].get(acct, "")
                records.append({
                    "id": f["id"],
                    "rawBytes": raw.hex(),
                    "categoryBalance": observed_inputs["balances"].get(acct, "0.00"),
                    "annualRate": observed_inputs["rates"].get(group, "0.00"),
                    "amount": f["amount"],
                    "transactionWritten": True,
                    "type": f["type"],
                    "category": f["category"][-2:] if len(f["category"]) == 4 else f["category"],
                    "source": f["source"],
                    "description": f["description"],
                    "merchant": f["merchant"],
                    "card": f["card"],
                    "xrefCard": observed_inputs["cards"].get(acct, f["card"]),
                    "observedAccount": acct,
                    "observedRateGroup": group,
                })
    for acct, group in sorted(observed_inputs["accounts"].items()):
        rate = observed_inputs["rates"].get(group)
        if rate == "0.00" and acct not in written_accounts:
            records.append({
                "id": f"zero-rate-account-{acct}",
                "categoryBalance": observed_inputs["balances"].get(acct, "0.00"),
                "annualRate": rate,
                "transactionWritten": False,
                "observedAccount": acct,
                "observedRateGroup": group,
                "observationBasis": "account/TCATBALF/DISCGRP raw physical files plus absence from TRANSACT output",
            })
    if not records:
        records.append({"id": "no-written-interest-transaction", "transactionWritten": False, "categoryBalance": "0.00", "annualRate": "0.00"})
    return {"transactions": records, "observedInputPartitions": observed_inputs}


def _extract_reporting(audit: dict[str, Any]) -> dict[str, Any]:
    wd = Path(audit["INV"]["workdir"])
    dateparm = wd / "DATEPARM"
    date_range = [None, None]
    if dateparm.exists():
        raw_date = dateparm.read_bytes().decode("ascii", "replace")
        date_range = [raw_date[0:10].strip(), raw_date[11:21].strip()]
    parsed = parse_report_capture((wd / "TRANREPT").read_bytes() if (wd / "TRANREPT").exists() else b"")
    input_dates: dict[str, str] = {}
    tranfile = wd / "TRANFILE"
    if tranfile.exists():
        data = tranfile.read_bytes()
        for i in range(0, len(data), 350):
            raw_tx = data[i:i + 350]
            if len(raw_tx) == 350:
                f = transaction_record_fields(raw_tx)
                input_dates[f["id"]] = f.get("procTs", "")[:10]
    txs = []
    for d in parsed["details"]:
        txs.append({
            "id": d["id"],
            "procDate": input_dates.get(d["id"], "unknown"),
            "amount": d["amount"].replace(",", ""),
            "detailWritten": True,
            "detailLine": d["detailLine"],
            "reportLineBytes": d["reportLineBytes"],
        })
    totals = {t["label"]: t["amount"].replace(",", "") for t in parsed["totals"]}
    result = {"dateRange": date_range, "transactions": txs, "reportFraming": parsed["framing"]}
    if "Page Total" in totals:
        result["pageTotal"] = totals["Page Total"]
    if "Account Total" in totals:
        result["accountTotal"] = totals["Account Total"]
    result["observedTotalsPresent"] = sorted(totals)
    return result


def extract_fixture_from_audits(fixture_id: str, audit_paths: list[Path]) -> dict[str, Any]:
    observations: dict[str, Any] = {}
    raw_audits = []
    for p in audit_paths:
        audit = _read_audit(p)
        track = audit.get("INV", {}).get("track")
        raw_audits.append(str(p))
        if track == "posting":
            observations["posting"] = _extract_posting(audit)
        elif track == "interest":
            observations["interest"] = _extract_interest(audit)
        elif track == "reporting":
            observations["reporting"] = _extract_reporting(audit)
    return {"fixtureId": fixture_id, "description": "Actual API/COBOL observations extracted from raw audits and files; no expected fields injected.", "rawAuditPaths": raw_audits, "observations": observations}

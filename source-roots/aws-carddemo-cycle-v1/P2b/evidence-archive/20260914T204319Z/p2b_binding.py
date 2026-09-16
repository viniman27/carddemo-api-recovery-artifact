#!/usr/bin/env python3
"""P2b local technical binding vertical slice.

Localhost facade + per-invocation COBOL process harness for AWS CardDemo full3track.
Synthetic fixtures are technical smoke inputs only, not evaluation oracle data.
"""
from __future__ import annotations

import argparse
import hashlib
import http.server
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CYCLE = ROOT.parent
P2A = CYCLE / "P2a"
PREP = CYCLE.parent / "aws-carddemo-preparation"
CORPUS = PREP / "research-corpus"
if not CORPUS.exists():
    CORPUS = PREP / "corpus"
EXPANDED_SUPPORT = PREP / "expanded-batch" / "support"
MANIFEST = PREP / "evidence" / "research-package.json"
BUILD = ROOT / "build"
RUNS = ROOT / "runs"
COMMAND_LOG = ROOT / "command-log.jsonl"

SIZES = {"TRANFILE": (350, 16), "XREFFILE": (50, 16), "ACCTFILE": (300, 11), "TCATBALF": (50, 17)}
IO_TEMPLATE = r'''
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
 when 'LOAD'
   open input raw-file
   if fs not = '00' perform bad-raw end-if
   open output idx-file
   if ix not = '00' perform bad-index end-if
   perform until fs = '10'
     read raw-file
     evaluate fs
       when '00'
         move raw-rec to idx-rec
         write idx-rec
         if ix not = '00' perform bad-index end-if
       when '10' continue
       when other perform bad-raw
     end-evaluate
   end-perform
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
 close raw-file
 close idx-file
 stop run returning 0.
bad-raw.
 display 'RAW STATUS=' fs upon syserr
 stop run returning 12.
bad-index.
 display 'INDEX STATUS=' ix upon syserr
 stop run returning 12.
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_cmd(cmd: list[str | Path], cwd: Path | None = None, env: dict[str, str] | None = None, expect: int | None = 0, timeout: int = 60) -> dict[str, Any]:
    cwd = cwd or ROOT
    merged = dict(os.environ)
    if env:
        merged.update({k: str(v) for k, v in env.items()})
    started = time.time()
    p = subprocess.run([str(x) for x in cmd], cwd=cwd, env=merged, capture_output=True, text=True, timeout=timeout)
    rec = {"cmd": [str(x) for x in cmd], "cwd": str(cwd), "env_override": env or {}, "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr, "duration_s": round(time.time() - started, 3)}
    COMMAND_LOG.parent.mkdir(parents=True, exist_ok=True)
    with COMMAND_LOG.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    if expect is not None and p.returncode != expect:
        raise RuntimeError(json.dumps(rec, indent=2))
    return rec


def load_expected_source_pins() -> dict[str, Any]:
    data = json.loads(MANIFEST.read_text())
    return {"commit": data["commit"], "programs": data["programs"], "files_by_path": {f["path"]: f for f in data["files"]}}


def verify_source_pins() -> dict[str, Any]:
    pins = load_expected_source_pins()
    checked = []
    for rel, item in pins["files_by_path"].items():
        path = CORPUS / rel
        if path.exists():
            actual = sha256(path)
            if actual != item["sha256"]:
                raise RuntimeError(f"source pin mismatch {rel}: {actual} != {item['sha256']}")
            checked.append({"path": rel, "sha256": actual, "bytes": path.stat().st_size})
    return {"commit": pins["commit"], "programs": pins["programs"], "checked_files": checked, "source_root": str(CORPUS)}


def validate_request(obj: Any) -> str | None:
    if not isinstance(obj, dict) or obj:
        return "request_representation"
    return None


def new_audit(track: str, workdir: Path, inv_id: str) -> dict[str, Any]:
    return {
        "INV": {"id": inv_id, "run": "E3-01", "track": track, "request": {}, "workdir": str(workdir), "localhost_only": True, "time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
        "RES": {"source_pins": verify_source_pins(), "fixture_policy": "externally prepared synthetic technical smoke fixture; not evaluation oracle; not extraction input", "p2a_contract": str(P2A / "openapi-carddemo-stage6r3.yaml")},
        "CAP": {"captures": [], "freshness": "created in this invocation workspace"},
        "CONV": {"field_mappings": [], "limits": ["technical parse only", "no semantic repairs", "no coverage inference from build"]},
        "FAIL": {"events": []},
        "STATE": {"isolation": "new per-invocation directory", "durability": "unknown", "reset_claim": "not_attested"},
        "RESP": {"status": None, "body": None, "contract": "P2a Stage6r3 mechanical OpenAPI"},
    }


def record_file(audit: dict[str, Any], label: str, path: Path) -> None:
    audit["CAP"]["captures"].append({"label": label, "path": str(path), "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else None, "sha256": sha256(path) if path.exists() else None})


def account(expiry: bytes = b"2099-12-31") -> bytes:
    data = (b"00000000001" + b"Y" + b"000000000000" + b"000000100000" + b"000000100000" + b"2020-01-01" + expiry + b"2020-01-01" + b"000000000000" + b"000000000000" + b"0000000000" + b"TEST      " + b" " * 178)
    assert len(data) == 300
    return data


def transaction(card: bytes = b"0000000000000001", amount: bytes = b"00000002500") -> bytes:
    data = (b"TEST000000000001" + b"01" + b"0001" + b"TEST      " + b"LOCAL SYNTHETIC FIXTURE".ljust(100) + amount + b"000000001" + b"TEST MERCHANT".ljust(50) + b"TEST CITY".ljust(50) + b"0000000000" + card + b"2025-01-01-00.00.00.000000" + b" " * 26 + b" " * 20)
    assert len(data) == 350
    return data


def build() -> dict[str, Any]:
    ROOT.mkdir(exist_ok=True)
    BUILD.mkdir(exist_ok=True)
    COMMAND_LOG.write_text("")
    pins = verify_source_pins()
    (ROOT / "support-generated").mkdir(exist_ok=True)
    run_cmd(["cobc", "-info"], cwd=BUILD, expect=None)
    cp = CORPUS / "app" / "cpy"
    common = ["cobc", "-std=ibm", "-fsign=ascii", "-I", cp]
    run_cmd(common + ["-x", "-o", BUILD / "CBTRN02C", CORPUS / "app/cbl/CBTRN02C.cbl"], cwd=BUILD)
    run_cmd(common + ["-m", "-o", BUILD / "CBACT04C.dylib", CORPUS / "app/cbl/CBACT04C.cbl"], cwd=BUILD)
    run_cmd(common + ["-x", "-o", BUILD / "CBTRN03C", CORPUS / "app/cbl/CBTRN03C.cbl"], cwd=BUILD)
    for name in ["intcalc_fixture", "report_fixture", "CBACT04C_driver", "CEE3ABD2"]:
        src = EXPANDED_SUPPORT / f"{name}.cbl"
        run_cmd(common + ["-x" if name != "CEE3ABD2" else "-m", "-free", "-o", BUILD / ("CEE3ABD.dylib" if name == "CEE3ABD2" else name), src], cwd=BUILD)
    for dd, (size, key) in SIZES.items():
        helper = ROOT / "support-generated" / f"io_{dd}.cbl"
        helper.write_text(IO_TEMPLATE.format(size=size, key=key, rest=size - key))
        run_cmd(common + ["-x", "-free", "-o", BUILD / f"io_{dd}", helper], cwd=BUILD)
    out = {"built": True, "build_dir": str(BUILD), "source_pins": pins, "commands_jsonl": str(COMMAND_LOG)}
    (ROOT / "build-report.json").write_text(json.dumps(out, indent=2) + "\n")
    return out


def io_file(wd: Path, dd: str, mode: str, raw: Path) -> None:
    run_cmd([BUILD / f"io_{dd}"], cwd=wd, env={"IO_MODE": mode, "DD_RAW": str(raw), "DD_IDX": str(wd / dd)})


def invocation_dir(track: str) -> Path:
    RUNS.mkdir(exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f"{track}-", dir=RUNS))


def fixed_capture_status(track: str, data: bytes | None, record_size: int, *, provenance: str = "capture") -> dict[str, Any]:
    status = {"track": track, "provenance": provenance, "recordSize": record_size, "bytes": None, "classification": None}
    if data is None:
        status.update({"classification": "missing", "reason": "capture was not present/readable as bytes"})
        return status
    status["bytes"] = len(data)
    if len(data) == 0:
        status.update({"classification": "known_empty", "recordCount": 0})
        return status
    if len(data) % record_size != 0:
        status.update({"classification": "truncated", "recordCount": len(data) // record_size, "remainderBytes": len(data) % record_size, "rawPrefixHex": data[:64].hex()})
        return status
    try:
        data.decode("ascii")
    except UnicodeDecodeError as exc:
        status.update({"classification": "malformed", "reason": f"non-ascii byte at offset {exc.start}", "rawPrefixHex": data[:64].hex()})
        return status
    status.update({"classification": "available", "recordCount": len(data) // record_size})
    return status


def empty_available_body(track: str) -> dict[str, Any]:
    if track == "posting":
        return {"track": "posting", "completeness": "not_attested", "durability": "unknown", "outputs": {"availability": "available", "items": []}, "rejections": {"availability": "available", "items": []}, "progress": {"availability": "available", "value": {"processedRecordCount": 0, "preliminaryRejectCount": 0}}}
    if track == "interest":
        return {"track": "interest", "completeness": "not_attested", "durability": "unknown", "outputs": {"availability": "available", "items": []}}
    if track == "reporting":
        return {"track": "reporting", "completeness": "not_attested", "durability": "unknown", "records": {"availability": "available", "items": []}}
    raise ValueError(track)


def error_body(track: str, category: str, available_content: dict[str, Any] | None = None) -> dict[str, Any]:
    body = {"track": track, "category": category, "completeness": "not_attested", "durability": "unknown"}
    if available_content is not None:
        body["availableContent"] = available_content
    return body


def status_for_capture_observation(track: str, framing: dict[str, Any], available_content: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    cls = framing["classification"]
    if cls == "known_empty":
        return 200, empty_available_body(track)
    if cls == "missing":
        return 503, error_body(track, "content_unavailable")
    if cls in {"truncated", "malformed", "unreadable", "stale", "unmapped_meaningful"}:
        return 500, error_body(track, "technical_failure", available_content)
    if cls == "available" and available_content is not None:
        return 200, available_content
    return 503, error_body(track, "content_unavailable")


def transaction_item(rec: bytes) -> dict[str, str]:
    return {"transactionId": rec[0:16].decode('ascii','replace').strip(), "typeCode": rec[16:18].decode('ascii','replace'), "categoryCode": rec[18:22].decode('ascii','replace'), "source": rec[22:32].decode('ascii','replace').strip(), "description": rec[32:132].decode('ascii','replace').strip(), "amount": rec[132:143].decode('ascii','replace'), "merchantId": rec[143:152].decode('ascii','replace').strip(), "merchantName": rec[152:202].decode('ascii','replace').strip(), "merchantCity": rec[202:252].decode('ascii','replace').strip(), "merchantPostalText": rec[252:262].decode('ascii','replace').strip(), "cardReference": rec[262:278].decode('ascii','replace'), "originalTimestamp": rec[278:304].decode('ascii','replace').strip(), "processingTimestamp": rec[304:330].decode('ascii','replace').strip()}


def parse_transaction_records(data: bytes, track: str) -> tuple[list[dict[str, str]], dict[str, Any]]:
    framing = fixed_capture_status(track, data, 350, provenance="TRANFILE/TRANSACT fixed-width receiver")
    evidence = {"framing": framing, "records": []}
    if framing["classification"] != "available":
        return [], evidence
    items = []
    for idx in range(0, len(data), 350):
        rec = data[idx:idx+350]
        item = transaction_item(rec)
        items.append(item)
        evidence["records"].append({"index": idx // 350, "classification": "transaction", "sourceSpan": [idx, idx + 350], "rawText": rec.decode('ascii', 'replace')})
    return items, evidence


def classify_report_line(rec: bytes, index: int) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    raw = rec.decode('ascii', 'replace')
    text = raw.rstrip()
    ev = {"index": index, "sourceSpan": [index * 133, (index + 1) * 133], "rawText": text, "classification": "unknown_unmapped"}
    if not text.strip():
        ev["classification"] = "known_blank"
        return None, ev
    if set(text.strip()) == {"-"}:
        ev["classification"] = "known_unmapped_rule"
        return None, ev
    if text.startswith("Transaction ID"):
        ev["classification"] = "known_unmapped_header_row"
        return None, ev
    if raw.startswith("DALYREPT"):
        ev["classification"] = "header"
        return {"kind": "header", "value": {"reportShortNameText": raw[0:38].strip(), "reportLongNameText": raw[38:79].strip(), "startText": raw[91:101].strip(), "endText": raw[105:115].strip()}}, ev
    for label_text, label in [("Page Total", "page"), ("Account Total", "account"), ("Grand Total", "grand")]:
        if raw.startswith(label_text):
            ev["classification"] = "total"
            return {"kind": "total", "value": {"label": label, "valueText": raw[97:112].strip()}}, ev
    if len(raw) >= 112 and raw[16] == " " and raw[28] == " " and raw[31] == "-" and raw[47] == " " and raw[52] == "-":
        ev["classification"] = "detail"
        return {"kind": "detail", "value": {"transactionId": raw[0:16].strip(), "accountReference": raw[17:28].strip(), "typeCode": raw[29:31].strip(), "typeDescription": raw[32:47].strip(), "categoryCode": raw[48:52].strip(), "categoryDescription": raw[53:82].strip(), "source": raw[83:93].strip(), "amountText": raw[97:112].strip()}}, ev
    return None, ev


def parse_report_records(data: bytes) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    framing = fixed_capture_status("reporting", data, 133, provenance="TRANREPT fixed-width receiver")
    evidence = {"framing": framing, "records": []}
    if framing["classification"] != "available":
        return [], evidence
    records: list[dict[str, Any]] = []
    for idx in range(0, len(data), 133):
        record, ev = classify_report_line(data[idx:idx+133], idx // 133)
        evidence["records"].append(ev)
        if record is not None:
            records.append(record)
    if not records and any(ev.get("classification") == "unknown_unmapped" for ev in evidence["records"]):
        framing["classification"] = "unmapped_meaningful"
        framing["reason"] = "non-empty report record(s) did not match any frozen public report shape"
        framing["unknownRecordIndexes"] = [ev["index"] for ev in evidence["records"] if ev.get("classification") == "unknown_unmapped"]
    return records, evidence


def posting(inv_id: str) -> tuple[int, dict[str, Any], dict[str, Any]]:
    wd = invocation_dir("posting")
    audit = new_audit("posting", wd, inv_id)
    seeds = {"TRANFILE": b"", "TCATBALF": b"", "ACCTFILE": account(), "XREFFILE": b"0000000000000001" + b"000000001" + b"00000000001" + b" " * 14}
    for dd, data in seeds.items():
        raw = wd / f"{dd}.seed"; raw.write_bytes(data); io_file(wd, dd, "LOAD", raw); record_file(audit, f"{dd}.seed", raw)
    (wd / "DALYTRAN").write_bytes(transaction()); record_file(audit, "DALYTRAN", wd / "DALYTRAN")
    cmd = run_cmd([BUILD / "CBTRN02C"], cwd=wd, env={"COB_LIBRARY_PATH": str(BUILD), **{f"DD_{dd}": str(wd / dd) for dd in [*SIZES, "DALYTRAN", "DALYREJS"]}}, expect=None)
    audit["CAP"]["program_stdout"] = cmd["stdout"]; audit["CAP"]["program_stderr"] = cmd["stderr"]
    for dd in SIZES:
        raw = wd / f"{dd}.after"; io_file(wd, dd, "DUMP", raw); record_file(audit, f"{dd}.after", raw)
    if (wd / "DALYREJS").exists(): record_file(audit, "DALYREJS", wd / "DALYREJS")
    tran = (wd / "TRANFILE.after").read_bytes() if (wd / "TRANFILE.after").exists() else None
    rejs = (wd / "DALYREJS").read_bytes() if (wd / "DALYREJS").exists() else b""
    reached = "END OF EXECUTION" in cmd["stdout"] or bool(tran) or len(rejs) > 0
    audit["CONV"]["field_mappings"].append({"field": "PostingProgress", "basis": "CBTRN02C stdout + dumped output lengths"})
    items, output_evidence = parse_transaction_records(tran or b"", "posting") if tran is not None else ([], {"framing": fixed_capture_status("posting", None, 350)})
    audit["CONV"]["field_mappings"].append({"field": "PostingTransaction", "basis": "TRANFILE.after 350-byte fixed records", "sourceSpanEvidence": output_evidence})
    body = {"track": "posting", "completeness": "not_attested", "durability": "unknown", "outputs": {"availability": "available", "items": items}, "rejections": {"availability": "available", "items": []}, "progress": {"availability": "available", "value": {"processedRecordCount": len(items), "preliminaryRejectCount": 1 if rejs else 0}}}
    framing = output_evidence["framing"]
    status, mapped_body = status_for_capture_observation("posting", framing, body)
    if status != 200:
        body = mapped_body
    if status == 200 and not (reached and cmd["exit_code"] in (0, 4)):
        status, body = 500, error_body("posting", "technical_failure", body)
    audit["RESP"] = {"status": status, "body": body, "program_exit": cmd["exit_code"], "reached_cobol": reached}
    (wd / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    return status, body, audit


def interest(inv_id: str) -> tuple[int, dict[str, Any], dict[str, Any]]:
    wd = invocation_dir("interest")
    audit = new_audit("interest", wd, inv_id)
    run_cmd([BUILD / "intcalc_fixture"], cwd=wd)
    cmd = run_cmd([BUILD / "CBACT04C_driver"], cwd=wd, env={"COB_LIBRARY_PATH": str(BUILD)}, expect=None)
    if (wd / "TRANSACT").exists(): record_file(audit, "TRANSACT", wd / "TRANSACT")
    tr = (wd / "TRANSACT").read_bytes() if (wd / "TRANSACT").exists() else None
    reached = "END OF EXECUTION OF PROGRAM CBACT04C" in cmd["stdout"] or bool(tr)
    audit["CONV"]["field_mappings"].append({"field": "GeneratedInterestTransaction", "basis": "CBACT04C generated TRANSACT 350-byte records"})
    items, evidence = parse_transaction_records(tr or b"", "interest") if tr is not None else ([], {"framing": fixed_capture_status("interest", None, 350)})
    audit["CONV"]["field_mappings"].append({"field": "GeneratedInterestTransaction", "basis": "TRANSACT 350-byte fixed records", "sourceSpanEvidence": evidence})
    body = {"track": "interest", "completeness": "not_attested", "durability": "unknown", "outputs": {"availability": "available", "items": items}}
    status, mapped_body = status_for_capture_observation("interest", evidence["framing"], body)
    if status != 200:
        body = mapped_body
    if status == 200 and not (reached and cmd["exit_code"] == 0):
        status, body = 500, error_body("interest", "technical_failure", body)
    audit["CAP"]["program_stdout"] = cmd["stdout"]; audit["CAP"]["program_stderr"] = cmd["stderr"]
    audit["RESP"] = {"status": status, "body": body, "program_exit": cmd["exit_code"], "reached_cobol": reached}
    (wd / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    return status, body, audit


def reporting(inv_id: str) -> tuple[int, dict[str, Any], dict[str, Any]]:
    wd = invocation_dir("reporting")
    audit = new_audit("reporting", wd, inv_id)
    # Prepare a current technical transaction via actual CBACT04C first, then report it.
    src = invocation_dir("reporting-source")
    run_cmd([BUILD / "intcalc_fixture"], cwd=src)
    run_cmd([BUILD / "CBACT04C_driver"], cwd=src, env={"COB_LIBRARY_PATH": str(BUILD)})
    tr = (src / "TRANSACT").read_bytes()
    (wd / "TRANFILE").write_bytes(tr)
    run_cmd([BUILD / "report_fixture"], cwd=wd)
    date = tr[304:314]
    (wd / "DATEPARM").write_bytes((date + b" " + date).ljust(80, b" "))
    cmd = run_cmd([BUILD / "CBTRN03C"], cwd=wd, env={"COB_LIBRARY_PATH": str(BUILD)}, expect=None)
    if (wd / "TRANREPT").exists(): record_file(audit, "TRANREPT", wd / "TRANREPT")
    report = (wd / "TRANREPT").read_bytes() if (wd / "TRANREPT").exists() else None
    reached = bool(report) or "END OF EXECUTION" in cmd["stdout"]
    records, report_evidence = parse_report_records(report or b"") if report is not None else ([], {"framing": fixed_capture_status("reporting", None, 133)})
    audit["CONV"]["field_mappings"].append({"field": "ReportRecord", "basis": "CBTRN03C TRANREPT 133-byte records parsed directly; raw text retained", "sourceSpanEvidence": report_evidence})
    body = {"track": "reporting", "completeness": "not_attested", "durability": "unknown", "records": {"availability": "available", "items": records}}
    audit["CAP"]["report_text_preview"] = [r.get("rawText", "") for r in report_evidence.get("records", [])[:5]]
    audit["CAP"]["report_record_classifications"] = report_evidence.get("records", [])
    audit["CAP"]["program_stdout"] = cmd["stdout"]; audit["CAP"]["program_stderr"] = cmd["stderr"]
    status, mapped_body = status_for_capture_observation("reporting", report_evidence["framing"], body)
    if status != 200:
        body = mapped_body
    if status == 200 and not (reached and cmd["exit_code"] == 0):
        status, body = 500, error_body("reporting", "technical_failure", body)
    audit["RESP"] = {"status": status, "body": body, "program_exit": cmd["exit_code"], "reached_cobol": reached}
    (wd / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    return status, body, audit

TRACKS = {"/posting": posting, "/interest": interest, "/reporting": reporting}

class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "P2bLocal/0"
    def do_POST(self):
        if self.path not in TRACKS:
            self.send_error(404); return
        n = int(self.headers.get("content-length", "0"))
        try:
            obj = json.loads(self.rfile.read(n) or b"null")
        except Exception:
            obj = None
        err = validate_request(obj)
        if err:
            body = {"track": self.path.strip('/'), "category": err, "completeness": "not_attested", "durability": "unknown"}
            self.reply(400, body); return
        try:
            status, body, _audit = TRACKS[self.path](f"http-{int(time.time()*1000)}")
        except Exception:
            body = error_body(self.path.strip('/'), "technical_failure")
            status = 500
        self.reply(status, body)
    def reply(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers(); self.wfile.write(data)
    def log_message(self, fmt: str, *args: Any) -> None:
        with (ROOT / "server-access.log").open("a") as f:
            f.write((fmt % args) + "\n")


def serve(port_file: Path) -> None:
    build()
    httpd = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    port_file.write_text(str(httpd.server_address[1]))
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    httpd.serve_forever()


def smoke() -> dict[str, Any]:
    build_report = build()
    before_dirs = {p.resolve() for p in RUNS.glob("*")} if RUNS.exists() else set()
    port_file = ROOT / "server.port"
    if port_file.exists(): port_file.unlink()
    proc = subprocess.Popen([sys.executable, __file__, "serve", "--port-file", str(port_file)], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        for _ in range(100):
            if port_file.exists(): break
            time.sleep(0.05)
        port = int(port_file.read_text())
        results = []
        smoke_started_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        for track in ["posting", "interest", "reporting"]:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/{track}", data=b"{}", headers={"content-type": "application/json"}, method="POST")
            started = time.time()
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
                results.append({"track": track, "status": r.status, "body": json.loads(raw), "body_sha256": hashlib.sha256(raw).hexdigest(), "duration_s": round(time.time() - started, 3)})
        after_dirs = {p.resolve() for p in RUNS.glob("*")}
        current_dirs = sorted(str(p) for p in after_dirs - before_dirs)
        manifest = {"kind": "P2b technical smoke, not official T1/T2/T3/T4", "smoke_started_utc": smoke_started_utc, "localhost": f"127.0.0.1:{port}", "build": build_report, "results": results, "current_run_dirs": current_dirs, "stale_capture_guard": "current_run_dirs are set difference after this smoke invocation", "done": [r["track"] for r in results if r["status"] == 200], "blocked": [], "unverified": ["No official oracle/comparative analysis", "No coverage claim", "No P2/P3 human gate approval claimed"]}
        (ROOT / "readiness-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        return manifest
    finally:
        proc.terminate()
        try:
            out, err = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill(); out, err = proc.communicate()
        (ROOT / "server-lifecycle.json").write_text(json.dumps({"pid": proc.pid, "returncode": proc.returncode, "stdout": out, "stderr": err}, indent=2) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    sp = sub.add_parser("serve"); sp.add_argument("--port-file", type=Path, required=True)
    sub.add_parser("smoke")
    args = ap.parse_args()
    if args.cmd == "build": print(json.dumps(build(), indent=2))
    elif args.cmd == "serve": serve(args.port_file)
    elif args.cmd == "smoke": print(json.dumps(smoke(), indent=2))

if __name__ == "__main__":
    main()

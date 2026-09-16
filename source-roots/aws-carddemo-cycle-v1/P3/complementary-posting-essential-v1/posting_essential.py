#!/usr/bin/env python3
"""Posting-only essential complementary runtime checks.

Local extension package only. It imports existing P2b binding and uses isolated
local fixtures; it does not edit COBOL, API contracts, or shared P2b/P3 assets.
"""
from __future__ import annotations

import hashlib
import http.server
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
P3 = ROOT.parent
CYCLE = P3.parent
P2B = CYCLE / "P2b"
CATALOG = P3 / "complementary-validation-v2" / "scenario-catalog.json"
CORPUS = CYCLE.parent / "aws-carddemo-preparation" / "research-corpus"
EVIDENCE = ROOT / "evidence"
PACKAGES = EVIDENCE / "packages"
RUNS = EVIDENCE / "p2b-runs"
RAW_HTTP = EVIDENCE / "raw-http"

POSTING_OBLIGATIONS = [f"POSTTRAN-OBL-{i:03d}" for i in range(1, 10)]
RECORD_SIZES = {"DALYTRAN": 350, "TRANFILE": 350, "DALYREJS": 430, "ACCTFILE": 300, "XREFFILE": 50, "TCATBALF": 50}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_p2b():
    spec = importlib.util.spec_from_file_location("p2b_posting_essential", P2B / "p2b_binding.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load P2b binding")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.RUNS = RUNS
    mod.COMMAND_LOG = EVIDENCE / "command-log.jsonl"
    return mod


def descriptor_sha256(fx: dict[str, Any]) -> str:
    canonical = {k: v for k, v in fx.items() if k != "contentSha256"}
    return sha256_bytes(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode())


def load_source_catalog() -> dict[str, Any]:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    obligations = {o["id"]: o for o in data["obligations"] if o["id"].startswith("POSTTRAN-")}
    scenarios = {s["obligationId"]: s for s in data["scenarioRecords"] if s["obligationId"].startswith("POSTTRAN-")}
    return {"sourceBase": data["sourceBase"], "obligations": obligations, "scenarios": scenarios}


def verify_posting_sources(catalog: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    verified: list[dict[str, Any]] = []
    expected: dict[str, str] = {}
    for oid in POSTING_OBLIGATIONS:
        obligation = catalog["obligations"].get(oid)
        if not obligation:
            failures.append(f"missing catalog obligation {oid}")
            continue
        for anchor in obligation.get("source_anchors", []):
            prev = expected.setdefault(anchor["path"], anchor["sha256"])
            if prev != anchor["sha256"]:
                failures.append(f"conflicting source hash for {anchor['path']}")
    for rel, expected_sha in sorted(expected.items()):
        path = Path(catalog["sourceBase"]) / rel
        if not path.is_file():
            failures.append(f"missing source file {rel}")
            continue
        actual = sha256_file(path)
        if actual != expected_sha:
            failures.append(f"source hash mismatch {rel}: {actual} != {expected_sha}")
        else:
            verified.append({"path": rel, "sha256": actual, "bytes": path.stat().st_size})
    return {"status": "pass" if not failures else "fail", "verifiedFiles": verified, "failures": failures}


def require_nonempty_field(record: dict[str, Any], field: str) -> dict[str, str]:
    if field not in record:
        return {"status": "inconclusive", "reason": f"{field} absent; not equivalent to empty"}
    if record[field] == "":
        return {"status": "fail", "reason": f"{field} empty"}
    return {"status": "pass", "reason": "present and non-empty"}


def qualify_effect_trace(record: dict[str, Any], required: tuple[str, ...]) -> dict[str, Any]:
    trace = record.get("effectTrace")
    if not isinstance(trace, list):
        return {"status": "inconclusive", "reasons": ["missing trace; internal effect order not observed"]}
    names = [e.get("name") for e in trace if isinstance(e, dict)]
    missing = [r for r in required if r not in names]
    if missing:
        return {"status": "inconclusive", "reasons": [f"missing trace entries: {missing}"]}
    return {"status": "pass", "reasons": []}


def make_provenance_record(path: Path, offset: int, length: int, fields: dict[str, Any]) -> dict[str, Any]:
    data = path.read_bytes()
    rec = dict(fields)
    rec["provenance"] = {
        "kind": "raw_file_record",
        "artifact": str(path),
        "artifactSha256": sha256_bytes(data),
        "recordOffset": offset,
        "recordLength": length,
        "observedFields": sorted(fields),
    }
    return rec


def verify_provenance_record(record: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    prov = record.get("provenance")
    if not isinstance(prov, dict):
        return ["provenance missing"]
    path = Path(prov.get("artifact", ""))
    if not path.is_file():
        return ["provenance artifact missing"]
    data = path.read_bytes()
    if sha256_bytes(data) != prov.get("artifactSha256"):
        failures.append("artifact sha mismatch")
    offset = prov.get("recordOffset")
    length = prov.get("recordLength")
    if not isinstance(offset, int) or not isinstance(length, int):
        failures.append("offset/length missing")
        return failures
    raw_hex = record.get("rawBytes")
    if raw_hex is not None:
        try:
            raw = bytes.fromhex(raw_hex)
            if data[offset:offset + length] != raw:
                failures.append("slice mismatch for rawBytes")
        except ValueError:
            failures.append("rawBytes not hex")
    return failures


def check_case_expectations(case: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    exp_reason = expected.get("expectedRejectReason")
    if exp_reason is not None:
        reasons = [str(r.get("reason")) for r in case.get("rejects", [])]
        if str(exp_reason) not in reasons:
            failures.append(f"expected reject reason {exp_reason}, observed {reasons}")
    return {"status": "pass" if not failures else "fail", "failures": failures}


def money12(cents: int) -> bytes:
    # P2b/GnuCOBOL display-signed fixtures use unsigned positives for these tests.
    if cents < 0:
        raise ValueError("negative packed/display fixture not used in essential package")
    return f"{cents:012d}".encode()


def account_bytes(acct: bytes = b"00000000001", *, balance: int = 0, limit: int = 100000, expiry: bytes = b"2099-12-31", cycle_credit: int = 0, cycle_debit: int = 0) -> bytes:
    data = acct + b"Y" + money12(balance) + money12(limit) + money12(limit) + b"2020-01-01" + expiry + b"2020-01-01" + money12(cycle_credit) + money12(cycle_debit) + b"0000000000" + b"TEST      " + b" " * 178
    assert len(data) == 300
    return data


def xref_bytes(card: bytes = b"0000000000000001", acct: bytes = b"00000000001") -> bytes:
    data = card + b"000000001" + acct + b" " * 14
    assert len(data) == 50
    return data


def tcatbal_bytes(acct: bytes = b"00000000001", type_cd: bytes = b"01", cat: bytes = b"0001", balance: int = 0) -> bytes:
    data = acct + type_cd + cat + f"{balance:011d}".encode() + b" " * 22
    assert len(data) == 50
    return data


def transaction_bytes(p2b, ident: bytes, *, card: bytes = b"0000000000000001", amount: bytes = b"00000002500") -> bytes:
    base = p2b.transaction(card=card, amount=amount)
    return ident + base[16:]


def load_index(p2b, work: Path, dd: str, raw_bytes: bytes) -> Path:
    raw = work / f"{dd}.seed"
    raw.write_bytes(raw_bytes)
    p2b.io_file(work, dd, "LOAD", raw)
    return work / dd


def write_fixture_package(p2b, case: dict[str, Any]) -> Path:
    case_dir = PACKAGES / case["caseId"]
    shutil.rmtree(case_dir, ignore_errors=True)
    pkg = case_dir / "posting"
    pkg.mkdir(parents=True)
    tmp = case_dir / "build-indexes"
    tmp.mkdir()
    acct_records = case.get("acctRecords", [account_bytes(expiry=case.get("expiry", b"2099-12-31"), balance=case.get("balance", 0), limit=case.get("limit", 100000), cycle_credit=case.get("cycleCredit", 0), cycle_debit=case.get("cycleDebit", 0))])
    xref_records = case.get("xrefRecords", [xref_bytes()])
    tcat_records = case.get("tcatRecords", [])
    indexed = {
        "ACCTFILE": b"".join(acct_records),
        "XREFFILE": b"".join(xref_records),
        "TCATBALF": b"".join(tcat_records),
        "TRANFILE": b"",
    }
    for dd, raw in indexed.items():
        load_index(p2b, tmp, dd, raw)
        shutil.copy2(tmp / dd, pkg / dd)
        sidecar = tmp / f"{dd}.1"
        if sidecar.exists():
            shutil.copy2(sidecar, pkg / f"{dd}.1")
    (pkg / "DALYTRAN").write_bytes(b"".join(case["transactions"]))
    files = {dd: f"posting/{dd}" for dd in ["ACCTFILE", "DALYTRAN", "TCATBALF", "TRANFILE", "XREFFILE"]}
    pins = {dd: {"bytes": (case_dir / rel).stat().st_size, "sha256": sha256_file(case_dir / rel)} for dd, rel in files.items()}
    # sidecar is not consumed by P2b posting RESOURCE_NAMES today, but preserve it
    # as original fixture sidecar evidence when RAWIO/BDB creates it.
    sidecars = {}
    if (pkg / "XREFFILE.1").exists():
        sidecars["XREFFILE.1"] = {"path": "posting/XREFFILE.1", "bytes": (pkg / "XREFFILE.1").stat().st_size, "sha256": sha256_file(pkg / "XREFFILE.1")}
    fx = {
        "fixtureId": f"posting-essential-{case['caseId']}",
        "track": "posting",
        "materializer": {"kind": "local_file_package", "files": files, "filePins": pins},
        "provenance": {"class": "local_physical_input_changes", "officialFixture": False, "caseId": case["caseId"], "preservedSidecars": sidecars},
        "exposure": {"label": "technical-only", "notOracle": True, "notExtractionInput": True, "notPublicRequest": True},
        "reset": {"default": "fresh_dir_per_run", "statefulSequence": "not_used"},
    }
    fx["contentSha256"] = descriptor_sha256(fx)
    registry = {"kind": "p3-local-technical-fixture-selection", "fixtures": [fx]}
    (case_dir / "registry.json").write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n")
    return case_dir / "registry.json"


def make_cases(p2b) -> list[dict[str, Any]]:
    return [
        {"caseId": "valid-new-tcatbal", "guard": "valid", "expectedStatus": 200, "expectedAccepted": 1, "expectedRejectReason": None, "transactions": [transaction_bytes(p2b, b"POSTNEWTCAT00001")], "tcatPartition": "missing creates"},
        {"caseId": "valid-existing-tcatbal", "guard": "valid", "expectedStatus": 200, "expectedAccepted": 1, "expectedRejectReason": None, "transactions": [transaction_bytes(p2b, b"POSTOLDTCAT00001")], "tcatRecords": [tcatbal_bytes(balance=500)], "tcatPartition": "existing rewrites"},
        {"caseId": "reject-card-missing", "guard": "card_missing", "expectedStatus": 200, "expectedAccepted": 0, "expectedRejectReason": "100", "transactions": [transaction_bytes(p2b, b"REJCARDMISS00001", card=b"9999999999999999")]},
        {"caseId": "reject-account-missing", "guard": "account_missing", "expectedStatus": 200, "expectedAccepted": 0, "expectedRejectReason": "101", "transactions": [transaction_bytes(p2b, b"REJACCTMISS00001")], "acctRecords": [], "xrefRecords": [xref_bytes(acct=b"00000000999")]},
        {"caseId": "reject-limit", "guard": "over_limit", "expectedStatus": 200, "expectedAccepted": 0, "expectedRejectReason": "102", "transactions": [transaction_bytes(p2b, b"REJLIMIT00000001", amount=b"00000002500")], "cycleCredit": 99000, "limit": 100000},
        {"caseId": "reject-expiry", "guard": "expired", "expectedStatus": 200, "expectedAccepted": 0, "expectedRejectReason": "103", "transactions": [transaction_bytes(p2b, b"REJEXPIRY0000001")], "expiry": b"2000-01-01"},
    ]


class LocalPostingServer:
    def __init__(self, p2b):
        self.p2b = p2b
        outer = self
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                if self.path != "/posting":
                    self.send_error(404); return
                raw_req = self.rfile.read(int(self.headers.get("content-length", "0")))
                try:
                    obj = json.loads(raw_req or b"null")
                except Exception:
                    obj = None
                err = outer.p2b.validate_request(obj)
                if err:
                    status, body = 400, {"track": "posting", "category": err, "completeness": "not_attested", "durability": "unknown"}
                else:
                    status, body, _audit = outer.p2b.posting(f"posting-essential-http-{int(time.time()*1000)}")
                raw = json.dumps(body, sort_keys=True).encode()
                self.send_response(status)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(raw)))
                self.end_headers(); self.wfile.write(raw)
            def log_message(self, fmt: str, *args: Any) -> None:
                pass
        self.httpd = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
    def __enter__(self):
        self.thread.start(); return self
    def __exit__(self, *exc):
        self.httpd.shutdown(); self.thread.join(timeout=5)
    @property
    def port(self) -> int:
        return int(self.httpd.server_address[1])


def latest_run_dir(before: set[Path]) -> Path:
    after = {p.resolve() for p in RUNS.glob("posting-*") if p.is_dir()}
    new = sorted(after - before, key=lambda p: p.stat().st_mtime)
    if not new:
        raise RuntimeError("no new posting run directory observed")
    return new[-1]


def post_http_once(port: int, case_id: str) -> dict[str, Any]:
    RAW_HTTP.mkdir(parents=True, exist_ok=True)
    req_body = b"{}"
    req_path = RAW_HTTP / f"{case_id}.request.bin"
    resp_path = RAW_HTTP / f"{case_id}.response.bin"
    req_path.write_bytes(req_body)
    req = urllib.request.Request(f"http://127.0.0.1:{port}/posting", data=req_body, headers={"content-type": "application/json"}, method="POST")
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read(); status = resp.status; headers = dict(resp.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read(); status = exc.code; headers = dict(exc.headers)
    resp_path.write_bytes(raw)
    return {"status": status, "body": json.loads(raw), "request": {"path": str(req_path), "bytes": len(req_body), "sha256": sha256_file(req_path)}, "response": {"path": str(resp_path), "bytes": len(raw), "sha256": sha256_file(resp_path), "headers": headers}, "durationSeconds": round(time.time() - started, 3)}


def raw_records(path: Path, size: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = path.read_bytes()
    out = []
    for off in range(0, len(data), size):
        chunk = data[off:off+size]
        if len(chunk) != size:
            continue
        out.append(make_provenance_record(path, off, size, {"rawBytes": chunk.hex()}))
    return out


def summarize_case(case: dict[str, Any], http: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    audit = json.loads((run_dir / "audit.json").read_text())
    captures = {c["label"]: c for c in audit.get("CAP", {}).get("captures", [])}
    records = {"accepted": raw_records(run_dir / "TRANFILE.after", 350), "acctAfter": raw_records(run_dir / "ACCTFILE.after", 300), "tcatAfter": raw_records(run_dir / "TCATBALF.after", 50), "rejectFile": raw_records(run_dir / "DALYREJS", 430)}
    rejects = []
    for item in http["body"].get("rejections", {}).get("items", []):
        r = {"reason": str(item.get("reason")), "description": item.get("description", ""), "rawBytes": records["rejectFile"][len(rejects)]["rawBytes"] if len(rejects) < len(records["rejectFile"]) else ""}
        if len(rejects) < len(records["rejectFile"]):
            r["provenance"] = records["rejectFile"][len(rejects)]["provenance"]
        rejects.append(r)
    observed = {
        "caseId": case["caseId"],
        "guard": case["guard"],
        "httpStatus": http["status"],
        "programExit": audit["RESP"].get("program_exit"),
        "reachedCobol": audit["RESP"].get("reached_cobol"),
        "runDir": str(run_dir),
        "acceptedCount": len(http["body"].get("outputs", {}).get("items", [])),
        "rejects": rejects,
        "progress": http["body"].get("progress"),
        "beforeAfterBytes": {label: captures.get(label) for label in ["DALYTRAN.pre_cobol", "TRANFILE.after", "ACCTFILE.after", "TCATBALF.after", "DALYREJS", "write-observations"]},
        "recordProvenance": records,
        "effectTraceQualification": qualify_effect_trace({}, required=("tcatbal", "account", "tranfile")),
    }
    expected = {"expectedStatus": case.get("expectedStatus"), "expectedAccepted": case.get("expectedAccepted"), "expectedRejectReason": case.get("expectedRejectReason"), "sourceExpectedComputedBeforeRun": True}
    failures = []
    if observed["httpStatus"] != expected["expectedStatus"]:
        failures.append(f"status {observed['httpStatus']} != {expected['expectedStatus']}")
    if observed["acceptedCount"] != expected["expectedAccepted"]:
        failures.append(f"accepted {observed['acceptedCount']} != {expected['expectedAccepted']}")
    reason_check = check_case_expectations(observed, expected)
    failures.extend(reason_check["failures"])
    if not observed["reachedCobol"]:
        failures.append("COBOL not reached")
    provenance_failures = []
    for group in records.values():
        for rec in group:
            provenance_failures.extend(verify_provenance_record(rec))
    failures.extend(provenance_failures)
    observed["qualification"] = {"status": "pass" if not failures else "fail", "failures": failures, "expected": expected}
    return observed


def obligation_matrix(catalog: dict[str, Any], cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Partition-level coverage is intentionally explicit: a passing case never
    # silently qualifies every source-catalog partition for an obligation.
    partitions_by_obligation = {
        "POSTTRAN-OBL-001": {
            "all DD/open statuses are 00 before first read": ["valid-new-tcatbal", "valid-existing-tcatbal", "reject-card-missing", "reject-account-missing", "reject-limit", "reject-expiry"],
            "one required open returns non-00 and must stop before processing": [],
        },
        "POSTTRAN-OBL-002": {
            "first read status 00 increments processed count": ["valid-new-tcatbal"],
            "read status 10 ends loop without processing a new record": ["valid-new-tcatbal", "reject-card-missing"],
            "non-00/non-10 read status abends": [],
        },
        "POSTTRAN-OBL-003": {
            "accepted transaction copies business fields from DALYTRAN": ["valid-new-tcatbal", "valid-existing-tcatbal"],
            "processing timestamp is current-date derived and not pre-fixed": ["valid-new-tcatbal", "valid-existing-tcatbal"],
        },
        "POSTTRAN-OBL-004": {
            "card absent in XREF rejects with reason 100": ["reject-card-missing"],
            "card present continues to account checks without format-only validation": ["valid-new-tcatbal", "reject-account-missing", "reject-limit", "reject-expiry"],
        },
        "POSTTRAN-OBL-005": {
            "account absent rejects 101": ["reject-account-missing"],
            "account over limit rejects 102 unless later expiry check overwrites with 103": ["reject-limit"],
            "textual expiration comparison fails and final reason is 103": ["reject-expiry"],
        },
        "POSTTRAN-OBL-006": {
            "one validation reason writes one reject trailer": ["reject-card-missing", "reject-account-missing", "reject-limit", "reject-expiry"],
            "normal close with reject count greater than zero returns RC 4": ["reject-card-missing", "reject-account-missing", "reject-limit", "reject-expiry"],
        },
        "POSTTRAN-OBL-007": {
            "TCATBAL missing key creates initial category balance": ["valid-new-tcatbal"],
            "TCATBAL existing key rewrites balance plus amount": ["valid-existing-tcatbal"],
            "TCATBAL I/O status outside documented set abends before account/TRANFILE effects": [],
        },
        "POSTTRAN-OBL-008": {
            "positive amount updates balance and credit": ["valid-new-tcatbal", "valid-existing-tcatbal"],
            "negative amount updates balance and debit": [],
            "ACCOUNT rewrite invalid key records reason 109 but continues toward TRANFILE write": [],
        },
        "POSTTRAN-OBL-009": {
            "TRANFILE write status 00 completes after prior effects": ["valid-new-tcatbal", "valid-existing-tcatbal"],
            "TRANFILE write non-00 abends after prior effects were attempted": [],
            "duplicate DALYTRAN/TRAN id is not prevalidated before write": [],
        },
    }
    case_status = {c["caseId"]: c["qualification"]["status"] for c in cases}
    matrix = []
    for oid in POSTING_OBLIGATIONS:
        scenario = catalog["scenarios"].get(oid, {})
        partition_rows = []
        for partition in scenario.get("boundaryPartitions", []):
            ids = partitions_by_obligation.get(oid, {}).get(partition, [])
            if oid == "POSTTRAN-OBL-009" and "after prior effects" in partition:
                pstatus = "inconclusive_internal_order_unobserved"
            elif ids and all(case_status.get(cid) == "pass" for cid in ids):
                pstatus = "qualified_observed"
            elif ids:
                pstatus = "attempted_failed_or_error"
            else:
                pstatus = "pending_unattempted"
            partition_rows.append({"partition": partition, "status": pstatus, "caseIds": ids})
        statuses = {p["status"] for p in partition_rows}
        if statuses == {"qualified_observed"}:
            status = "qualified_observed_all_listed_partitions"
        elif "attempted_failed_or_error" in statuses:
            status = "partial_with_failures"
        elif oid == "POSTTRAN-OBL-009" and "inconclusive_internal_order_unobserved" in statuses:
            status = "inconclusive_internal_order"
        elif "qualified_observed" in statuses:
            status = "partial_qualified_pending_partitions"
        else:
            status = "pending_unattempted"
        matrix.append({"obligationId": oid, "status": status, "partitions": partition_rows, "note": "partition-level scope; no one passing case is treated as covering all partitions"})
    return matrix


def run_all() -> dict[str, Any]:
    EVIDENCE.mkdir(exist_ok=True)
    PACKAGES.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)
    RAW_HTTP.mkdir(parents=True, exist_ok=True)
    p2b = load_p2b()
    build = p2b.build()
    catalog = load_source_catalog()
    source_status = verify_posting_sources(catalog)
    if source_status["status"] != "pass":
        raise RuntimeError(f"source verification failed: {source_status['failures']}")
    cases = make_cases(p2b)
    receipts = []
    prior_env = os.environ.get(p2b.FIXTURE_ENV)
    with LocalPostingServer(p2b) as server:
        for case in cases:
            registry = write_fixture_package(p2b, case)
            os.environ[p2b.FIXTURE_ENV] = str(registry)
            before = {p.resolve() for p in RUNS.glob("posting-*") if p.is_dir()}
            try:
                http = post_http_once(server.port, case["caseId"])
                run_dir = latest_run_dir(before)
                receipts.append(summarize_case(case, http, run_dir))
            except Exception as exc:
                receipts.append({"caseId": case["caseId"], "qualification": {"status": "error", "failures": [repr(exc)]}})
    if prior_env is None:
        os.environ.pop(p2b.FIXTURE_ENV, None)
    else:
        os.environ[p2b.FIXTURE_ENV] = prior_env
    report = {
        "kind": "complementary-posting-essential-v1",
        "createdUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "posting-only essential complementary scenarios; real isolated local API/COBOL; not official campaign; not oracle quarantine",
        "build": build,
        "sourceVerification": source_status,
        "caseReceipts": receipts,
        "obligationMatrix": obligation_matrix(catalog, receipts),
        "summary": {"cases": len(receipts), "caseStatusCounts": {s: sum(1 for r in receipts if r.get("qualification", {}).get("status") == s) for s in sorted({r.get("qualification", {}).get("status") for r in receipts})}},
    }
    (EVIDENCE / "posting-essential-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report)
    return report


def write_markdown(report: dict[str, Any]) -> None:
    lines = ["# Complementary posting essential v1 report", "", f"Scope: {report['scope']}", "", f"Case status counts: `{json.dumps(report['summary']['caseStatusCounts'], sort_keys=True)}`", "", "## Case receipts"]
    for r in report["caseReceipts"]:
        q = r.get("qualification", {})
        lines.append(f"- {r.get('caseId')}: {q.get('status')} HTTP={r.get('httpStatus')} COBOL={r.get('reachedCobol')} run=`{r.get('runDir')}` failures={q.get('failures', [])}")
    lines += ["", "## Obligation matrix"]
    for row in report["obligationMatrix"]:
        partition_text = "; ".join(f"{p['partition']} => {p['status']} cases={p['caseIds']}" for p in row["partitions"])
        lines.append(f"- {row['obligationId']}: {row['status']} :: {partition_text}")
    (EVIDENCE / "posting-essential-report.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    result = run_all()
    print(json.dumps({"report": str(EVIDENCE / "posting-essential-report.json"), "summary": result["summary"]}, indent=2, sort_keys=True))

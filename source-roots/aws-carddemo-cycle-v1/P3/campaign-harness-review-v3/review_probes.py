#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import textwrap
import time
from pathlib import Path

P3 = Path(__file__).resolve().parents[1]
V3 = P3 / "campaign-harness-v3"
OUT = P3 / "campaign-harness-review-v3"
EVID = OUT / ("evidence-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))


def run(cmd, cwd=V3, timeout=30):
    started = time.time()
    p = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, timeout=timeout)
    return {"cmd": cmd, "cwd": str(cwd), "returncode": p.returncode, "duration_seconds": round(time.time() - started, 3), "stdout": p.stdout, "stderr": p.stderr}


def main():
    EVID.mkdir(parents=True, exist_ok=False)
    results = {"evidence_dir": str(EVID), "checks": {}, "summary": {}}

    unit = run([sys.executable, "-m", "unittest", "tests/test_campaign_harness.py", "tests/test_lifecycle_bounded.py", "-v"], timeout=60)
    (EVID / "unittest.stdout").write_text(unit["stdout"], encoding="utf-8")
    (EVID / "unittest.stderr").write_text(unit["stderr"], encoding="utf-8")
    results["checks"]["unittest_9_existing_plus_lifecycle"] = {k: v for k, v in unit.items() if k not in {"stdout", "stderr"}}

    probes_out = EVID / "outside-in-probes"
    outside = run([sys.executable, "outside_in_probes.py", "--output", str(probes_out)], timeout=60)
    (EVID / "outside_in.stdout").write_text(outside["stdout"], encoding="utf-8")
    (EVID / "outside_in.stderr").write_text(outside["stderr"], encoding="utf-8")
    outside_json = probes_out / "outside_in_probes.json"
    outside_data = json.loads(outside_json.read_text(encoding="utf-8")) if outside_json.exists() else None
    results["checks"]["outside_in_five_fixes"] = {k: v for k, v in outside.items() if k not in {"stdout", "stderr"}}
    if outside_data:
        results["checks"]["outside_in_five_fixes"].update(outside_data["counts"])
        results["checks"]["outside_in_five_fixes"]["probe_results"] = {k: v.get("fix_verified") for k, v in outside_data["probes"].items()}

    child = EVID / "shutdown_hang_green_child.py"
    child.write_text(textwrap.dedent(f'''
        import json, sys, time
        from http.server import BaseHTTPRequestHandler
        from pathlib import Path
        sys.path.insert(0, {str(V3 / "src")!r})
        from campaign_harness import Case, Expectation, HttpRequestSpec, PerApplicationHttpTarget, Suite, replay_suite
        class HangHandler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"
            workdir = None
            def do_POST(self):
                Path(type(self).workdir, "attempts.txt").write_text("hit\\n", encoding="utf-8")
                while True:
                    time.sleep(1)
            def log_message(self, *args): pass
        c = Case("hang", "PX", "probe", HttpRequestSpec("POST", "/hang"), "none", Expectation("ok", {{"status": [200]}}), timeout_seconds=0.05)
        started = time.monotonic()
        r = replay_suite(Suite("PX", [c]), target=PerApplicationHttpTarget(HangHandler), output_dir=Path({str(EVID / "shutdown-hang-run")!r}))
        print(json.dumps({{"duration_seconds": round(time.monotonic() - started, 3), "totals": r.totals, "applications": r.applications, "receipts": r.receipts}}, sort_keys=True))
    '''), encoding="utf-8")
    started = time.time()
    try:
        p = subprocess.run([sys.executable, str(child)], text=True, capture_output=True, timeout=3)
        hang = {"external_timeout_seconds": 3, "timed_out_externally": False, "returncode": p.returncode, "duration_seconds": round(time.time() - started, 3), "stdout": p.stdout, "stderr": p.stderr}
        hang["stdout_json"] = json.loads(p.stdout) if p.returncode == 0 and p.stdout.strip() else None
    except subprocess.TimeoutExpired as exc:
        hang = {"external_timeout_seconds": 3, "timed_out_externally": True, "duration_seconds": round(time.time() - started, 3), "stdout": exc.stdout or "", "stderr": exc.stderr or "", "stdout_json": None}
    (EVID / "shutdown_hang_green_probe.json").write_text(json.dumps(hang, indent=2, sort_keys=True), encoding="utf-8")
    results["checks"]["shutdown_hang_bounded_green"] = hang

    semantic_code = textwrap.dedent('''
        import json, sys, tempfile
        from pathlib import Path
        sys.path.insert(0, str(Path.cwd() / "src"))
        from campaign_harness import *
        from tests.test_campaign_harness import RecordingHandler, serve, stop
        out = {}
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            srv, th, base = serve(RecordingHandler)
            try:
                cases = [
                    Case("unsupported", "PX", "probe", HttpRequestSpec("POST", "/ok"), "pkg", Expectation("schema", {"jsonSchema": {}})),
                    Case("supported", "PX", "probe", HttpRequestSpec("POST", "/ok"), "pkg", Expectation("status", {"status": [200]})),
                ]
                r = replay_suite(Suite("PX", cases), base_url=base, output_dir=td / "unsupported-run")
                out["unsupported_checker"] = {"totals": r.totals, "receipt_results": [x["expectation_result"] for x in r.receipts], "details": [x["expectation_detail"] for x in r.receipts]}
            finally:
                stop(srv, th)
            src = td / "src"; src.mkdir(); (src / "a.txt").write_text("A", encoding="utf-8")
            pkg = LocalResourcePackage.from_directory("pkg", src)
            copied_pins = pkg.copy_fresh_to(td / "copy")
            (td / "copy" / "a.txt").write_text("B", encoding="utf-8")
            out["copy_integrity"] = {"pins_before_match_source": copied_pins == pkg.pin_dict(), "source_after_copy_mutation": (src / "a.txt").read_text(encoding="utf-8"), "copy_after_mutation": (td / "copy" / "a.txt").read_text(encoding="utf-8")}
            t1 = Suite("T1", [Case("a", "T1", "T1", HttpRequestSpec("POST", "/ok"), "pkg", Expectation("same", {"status": [200]}))])
            t2 = Suite("T2", [Case("b", "T2", "T2", HttpRequestSpec("POST", "/ok"), "pkg", Expectation("same", {"status": [200]})), Case("c", "T2", "T2", HttpRequestSpec("POST", "/ok"), "pkg", Expectation("other", {"status": [500]}))])
            union, ledger = UnionBuilder().build([t2, t1])
            out["union"] = {"case_ids": [c.case_id for c in union.cases], "provenance": [list(c.provenance) for c in union.cases], "ledger": ledger}
            path = freeze_suite(union, td / "union.json")
            loaded = load_frozen_suite(path)
            tampered = json.loads(path.read_text())
            tampered["cases"][0]["request"]["path"] = "/tampered"
            path.write_text(json.dumps(tampered))
            try:
                load_frozen_suite(path); freeze_rejected = False
            except VerificationError:
                freeze_rejected = True
            out["freeze"] = {"loaded_case_count": len(loaded.cases), "tamper_rejected": freeze_rejected}
        print(json.dumps(out, indent=2, sort_keys=True))
    ''')
    sem = subprocess.run([sys.executable, "-c", semantic_code], cwd=str(V3), text=True, capture_output=True, timeout=20)
    (EVID / "semantic_probes.stdout").write_text(sem.stdout, encoding="utf-8")
    (EVID / "semantic_probes.stderr").write_text(sem.stderr, encoding="utf-8")
    results["checks"]["semantic_probes"] = {"returncode": sem.returncode, "stdout_json": json.loads(sem.stdout) if sem.returncode == 0 and sem.stdout.strip() else None, "stderr": sem.stderr}

    hashes = {}
    for path in sorted(EVID.rglob("*")):
        if path.is_file():
            hashes[str(path.relative_to(EVID))] = hashlib.sha256(path.read_bytes()).hexdigest()
    results["artifact_hashes"] = hashes
    green = hang.get("stdout_json") or {}
    apps = green.get("applications") or []
    results["summary"] = {
        "unittest_ok": unit["returncode"] == 0,
        "outside_in_fixes_verified": bool(outside_data and outside_data["counts"]["fixes_verified"] == 5),
        "shutdown_hang_bounded_without_external_kill": bool(not hang["timed_out_externally"] and hang.get("returncode") == 0 and apps and apps[0].get("target_quiet") is True and apps[0].get("lifecycle", {}).get("reaped") is True and apps[0].get("lifecycle", {}).get("pid_alive_after_reap") is False),
        "semantic_probes_ok": sem.returncode == 0,
    }
    (EVID / "review_probes_result.json").write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"evidence_dir": str(EVID), **results["summary"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

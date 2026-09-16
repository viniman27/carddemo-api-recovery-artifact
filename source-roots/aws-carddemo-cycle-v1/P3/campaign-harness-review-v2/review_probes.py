#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

P3 = Path(__file__).resolve().parents[1]
V2 = P3 / "campaign-harness-v2"
OUT = P3 / "campaign-harness-review-v2"
EVID = OUT / ("evidence-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))


def run(cmd, cwd=V2, timeout=20):
    started = time.time()
    p = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, timeout=timeout)
    return {
        "cmd": cmd,
        "cwd": str(cwd),
        "returncode": p.returncode,
        "duration_seconds": round(time.time() - started, 3),
        "stdout": p.stdout,
        "stderr": p.stderr,
    }


def main():
    EVID.mkdir(parents=True, exist_ok=False)
    results = {"evidence_dir": str(EVID), "checks": {}, "summary": {}}

    unittest_result = run([sys.executable, "-m", "unittest", "tests/test_campaign_harness.py", "-v"], timeout=30)
    (EVID / "unittest.stdout").write_text(unittest_result["stdout"], encoding="utf-8")
    (EVID / "unittest.stderr").write_text(unittest_result["stderr"], encoding="utf-8")
    results["checks"]["unittest_existing"] = {k: v for k, v in unittest_result.items() if k not in {"stdout", "stderr"}}

    probes_out = EVID / "outside-in-probes"
    outside = run([sys.executable, "outside_in_probes.py", "--output", str(probes_out)], timeout=30)
    (EVID / "outside_in.stdout").write_text(outside["stdout"], encoding="utf-8")
    (EVID / "outside_in.stderr").write_text(outside["stderr"], encoding="utf-8")
    outside_json = probes_out / "outside_in_probes.json"
    outside_data = json.loads(outside_json.read_text(encoding="utf-8")) if outside_json.exists() else None
    results["checks"]["outside_in_five_fixes"] = {k: v for k, v in outside.items() if k not in {"stdout", "stderr"}}
    if outside_data:
        results["checks"]["outside_in_five_fixes"].update(outside_data["counts"])
        results["checks"]["outside_in_five_fixes"]["probe_results"] = {k: v.get("fix_verified") for k, v in outside_data["probes"].items()}

    # Bounded negative probe: handler blocks after client timeout. In v2 stop() calls
    # HTTPServer.shutdown() before a bounded join; shutdown() itself has no timeout.
    child = EVID / "shutdown_hang_child.py"
    child.write_text(textwrap.dedent(f'''
        import sys, time, json
        from http.server import BaseHTTPRequestHandler
        from pathlib import Path
        sys.path.insert(0, {str(V2 / "src")!r})
        from campaign_harness import Case, Expectation, HttpRequestSpec, PerApplicationHttpTarget, Suite, replay_suite
        class HangHandler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"
            workdir = None
            def do_POST(self):
                time.sleep(60)
                self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers(); self.wfile.write(b"{{}}")
            def log_message(self, *args): pass
        c = Case("hang", "PX", "probe", HttpRequestSpec("POST", "/hang"), "none", Expectation("ok", {{"status": [200]}}), timeout_seconds=0.05)
        replay_suite(Suite("PX", [c]), target=PerApplicationHttpTarget(HangHandler), output_dir=Path({str(EVID / "shutdown-hang-run")!r}))
        print("completed")
    '''), encoding="utf-8")
    started = time.time()
    try:
        p = subprocess.run([sys.executable, str(child)], text=True, capture_output=True, timeout=3)
        hang = {"bounded_external_timeout_seconds": 3, "timed_out_externally": False, "returncode": p.returncode, "duration_seconds": round(time.time() - started, 3), "stdout": p.stdout, "stderr": p.stderr}
    except subprocess.TimeoutExpired as exc:
        hang = {"bounded_external_timeout_seconds": 3, "timed_out_externally": True, "duration_seconds": round(time.time() - started, 3), "stdout": exc.stdout or "", "stderr": exc.stderr or ""}
    (EVID / "shutdown_hang_probe.json").write_text(json.dumps(hang, indent=2, sort_keys=True), encoding="utf-8")
    results["checks"]["shutdown_hang_bounded_negative"] = hang

    # Local semantic probes for unsupported checker and freeze/union/copy integrity.
    semantic_code = textwrap.dedent('''
        import json, sys, tempfile, os
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
    sem = subprocess.run([sys.executable, "-c", semantic_code], cwd=str(V2), text=True, capture_output=True, timeout=20)
    (EVID / "semantic_probes.stdout").write_text(sem.stdout, encoding="utf-8")
    (EVID / "semantic_probes.stderr").write_text(sem.stderr, encoding="utf-8")
    results["checks"]["semantic_probes"] = {"returncode": sem.returncode, "stdout_json": json.loads(sem.stdout) if sem.returncode == 0 and sem.stdout.strip() else None, "stderr": sem.stderr}

    # Hash key evidence files.
    import hashlib
    hashes = {}
    for path in sorted(EVID.rglob("*")):
        if path.is_file():
            hashes[str(path.relative_to(EVID))] = hashlib.sha256(path.read_bytes()).hexdigest()
    results["artifact_hashes"] = hashes
    results["summary"] = {
        "unittest_ok": unittest_result["returncode"] == 0,
        "outside_in_fixes_verified": bool(outside_data and outside_data["counts"]["fixes_verified"] == 5),
        "shutdown_hang_regression_reproduced": hang["timed_out_externally"],
        "semantic_probes_ok": sem.returncode == 0,
    }
    (EVID / "review_probes_result.json").write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"evidence_dir": str(EVID), **results["summary"]}, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()

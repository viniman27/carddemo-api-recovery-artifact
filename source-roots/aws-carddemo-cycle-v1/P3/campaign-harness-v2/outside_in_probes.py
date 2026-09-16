#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from campaign_harness import Case, Expectation, HttpRequestSpec, LocalResourcePackage, PerApplicationHttpTarget, Suite, replay_suite  # noqa: E402


def mk_case(case_id, path="/ok", headers=(), body_kind="absent", body_b64=None, timeout=0.5, expectation=None, pkg="pkg-a"):
    return Case(
        case_id=case_id,
        suite_id="PX",
        origin="probe",
        request=HttpRequestSpec("POST", path, tuple(headers), body_kind, body_b64),
        resource_package_id=pkg,
        expectation=expectation or Expectation("expect-200", {"status": [200]}),
        timeout_seconds=timeout,
    )


def serve(handler_cls):
    server = HTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, f"http://127.0.0.1:{server.server_port}"


def stop(server, thread):
    server.shutdown(); thread.join(timeout=2); server.server_close()


class HeaderHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    seen = []
    def do_POST(self):
        HeaderHandler.seen.append({"x_dup_all": self.headers.get_all("X-Dup"), "raw_items": list(self.headers.items()), "content_length": self.headers.get("Content-Length")})
        payload = b"{}"
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(payload))); self.end_headers(); self.wfile.write(payload)
    def log_message(self, *args): pass


class WorkdirStateHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    workdir = None
    seen = []
    def do_POST(self):
        state = Path(WorkdirStateHandler.workdir) / "state.txt"
        before = state.read_text(encoding="utf-8")
        state.write_text(before.strip() + "+mutated\n", encoding="utf-8")
        after = state.read_text(encoding="utf-8")
        WorkdirStateHandler.seen.append({"workdir": str(WorkdirStateHandler.workdir), "before": before, "after": after})
        payload = json.dumps({"before": before, "after": after}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(payload))); self.end_headers(); self.wfile.write(payload)
    def log_message(self, *args): pass


class SlowThenFastHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    seen = []
    workdir = None
    def do_POST(self):
        started = time.time()
        if self.path == "/slow":
            time.sleep(0.35)
        SlowThenFastHandler.seen.append({"path": self.path, "started": started, "finished": time.time(), "workdir": SlowThenFastHandler.workdir})
        payload = b"{}"
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(payload))); self.end_headers()
        try: self.wfile.write(payload)
        except BrokenPipeError: pass
    def log_message(self, *args): pass


class Status500Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def do_POST(self):
        payload = b'{"error":"undocumented"}'
        self.send_response(500); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(payload))); self.end_headers(); self.wfile.write(payload)
    def log_message(self, *args): pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    out = Path(args.output)
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.mkdir(parents=True)
    results = {"probes": {}, "counts": {"probes_total": 0, "fixes_verified": 0}}

    srv, th, base = serve(HeaderHandler)
    try:
        c = mk_case("dup-headers", headers=(("X-Dup", "one"), ("X-Dup", "two")))
        r = replay_suite(Suite("PX", [c]), base_url=base, output_dir=out / "dup_headers_run")
        ok = HeaderHandler.seen[0]["x_dup_all"] == ["one", "two"]
        results["probes"]["duplicate_headers_wire_preserved"] = {"fix_verified": ok, "requested_headers": list(c.request.headers), "server_get_all_X_Dup": HeaderHandler.seen[0]["x_dup_all"], "receipt_headers": r.receipts[0]["request_headers"], "totals": r.totals}
    finally:
        stop(srv, th)

    with TemporaryDirectory() as td:
        td = Path(td); source = td / "source"; source.mkdir(); (source / "state.txt").write_text("original\n", encoding="utf-8")
        WorkdirStateHandler.seen = []
        pkg = LocalResourcePackage.from_directory("pkg-a", source)
        suite = Suite("PX", [mk_case("first"), mk_case("second")], {"pkg-a": pkg})
        r = replay_suite(suite, target=PerApplicationHttpTarget(WorkdirStateHandler), output_dir=out / "reset_bound_run")
        ok = [x["before"] for x in WorkdirStateHandler.seen] == ["original\n", "original\n"] and WorkdirStateHandler.seen[0]["workdir"] != WorkdirStateHandler.seen[1]["workdir"]
        results["probes"]["reset_workdir_bound_to_service_state"] = {"fix_verified": ok, "service_seen": WorkdirStateHandler.seen, "target_quiet_all": all(a["target_quiet"] for a in r.applications), "totals": r.totals}

    SlowThenFastHandler.seen = []
    suite = Suite("PX", [mk_case("slow", path="/slow", timeout=0.05), mk_case("fast-after-slow", path="/fast", timeout=0.50)])
    r = replay_suite(suite, target=PerApplicationHttpTarget(SlowThenFastHandler), output_dir=out / "deadline_controlled_run")
    ok = r.totals["deadline_failures"] == 1 and r.totals["completed"] == 1 and [x["path"] for x in SlowThenFastHandler.seen] == ["/slow", "/fast"] and all(a["target_quiet"] for a in r.applications)
    results["probes"]["deadline_reaped_before_next_application"] = {"fix_verified": ok, "server_seen": SlowThenFastHandler.seen, "totals": r.totals, "receipts": r.receipts}

    srv, th, base = serve(Status500Handler)
    try:
        suite = Suite("PX", [mk_case("unexpected-500", expectation=Expectation("only-200", {"status": [200]})), mk_case("documented-500", expectation=Expectation("allows-500", {"status": [500]})), mk_case("unsupported", expectation=Expectation("unsupported", {"jsonSchema": {}}))])
        r = replay_suite(suite, base_url=base, output_dir=out / "expectations_run")
        ok = [x["expectation_result"] for x in r.receipts] == ["violation", "pass", "inconclusive"] and r.totals["completed"] == 3 and r.totals["http_failures"] == 0
        results["probes"]["expectations_separate_from_transport"] = {"fix_verified": ok, "totals": r.totals, "receipts": r.receipts}
    finally:
        stop(srv, th)

    srv, th, base = serve(HeaderHandler)
    try:
        c = mk_case("x/../../escaped-case")
        r = replay_suite(Suite("PX", [c]), base_url=base, output_dir=out / "path_traversal_run")
        workdir = Path(r.applications[0]["workdir"]).resolve(); apps_root = (out / "path_traversal_run" / "applications").resolve()
        ok = apps_root in workdir.parents and r.applications[0]["case_id"] == c.case_id and "escaped-case" not in workdir.name
        results["probes"]["case_id_preserved_workdir_opaque_contained"] = {"fix_verified": ok, "case_id": c.case_id, "recorded_workdir": r.applications[0]["workdir"], "resolved_workdir": str(workdir), "applications_root": str(apps_root), "totals": r.totals}
    finally:
        stop(srv, th)

    results["counts"]["probes_total"] = len(results["probes"])
    results["counts"]["fixes_verified"] = sum(1 for p in results["probes"].values() if p.get("fix_verified"))
    (out / "outside_in_probes.json").write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(results["counts"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

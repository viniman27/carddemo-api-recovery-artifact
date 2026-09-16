#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

P3 = Path(__file__).resolve().parents[1]
HARNESS = P3 / "campaign-harness-v1"
sys.path.insert(0, str(HARNESS / "src"))

from campaign_harness import Case, Expectation, HttpRequestSpec, LocalResourcePackage, Suite, VerificationError, replay_suite  # noqa: E402


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


class HeaderHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    seen = []
    def do_POST(self):
        HeaderHandler.seen.append({
            "x_dup_all": self.headers.get_all("X-Dup"),
            "raw_items": list(self.headers.items()),
            "content_length": self.headers.get("Content-Length"),
        })
        payload = b"{}"
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    def log_message(self, *args):
        pass


class FixedStateHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    state_file = None
    seen = []
    def do_POST(self):
        before = Path(FixedStateHandler.state_file).read_text(encoding="utf-8")
        Path(FixedStateHandler.state_file).write_text(before.strip() + "+mutated\n", encoding="utf-8")
        after = Path(FixedStateHandler.state_file).read_text(encoding="utf-8")
        FixedStateHandler.seen.append({"before": before, "after": after})
        payload = json.dumps({"before": before, "after": after}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    def log_message(self, *args):
        pass


class SlowThenFastHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    seen = []
    def do_POST(self):
        started = time.time()
        if self.path == "/slow":
            time.sleep(0.35)
        SlowThenFastHandler.seen.append({"path": self.path, "started": started, "finished": time.time()})
        payload = b"{}"
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        try:
            self.wfile.write(payload)
        except BrokenPipeError:
            pass
    def log_message(self, *args):
        pass


class Status500Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def do_POST(self):
        payload = b'{"error":"undocumented"}'
        self.send_response(500)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    def log_message(self, *args):
        pass


def stop(server, thread):
    server.shutdown(); thread.join(timeout=2); server.server_close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    out = Path(args.output)
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.mkdir(parents=True)
    results = {"probes": {}, "counts": {"probes_total": 0, "defects_reproduced": 0}}

    # 1. Duplicate headers are preserved in identity/freeze shape but collapsed on the wire.
    srv, th, base = serve(HeaderHandler)
    try:
        c = mk_case("dup-headers", headers=(("X-Dup", "one"), ("X-Dup", "two")))
        r = replay_suite(Suite("PX", [c]), base, out / "dup_headers_run")
        x_dup_all = HeaderHandler.seen[0]["x_dup_all"]
        defect = x_dup_all != ["one", "two"]
        results["probes"]["duplicate_headers_wire_collapse"] = {
            "defect_reproduced": defect,
            "requested_headers": list(c.request.headers),
            "server_get_all_X_Dup": x_dup_all,
            "totals": r.totals,
        }
    finally:
        stop(srv, th)

    # 2. Resource reset copies fresh files but the HTTP service receives no per-application workdir.
    with TemporaryDirectory() as td:
        td = Path(td)
        source = td / "source"; source.mkdir(); (source / "state.txt").write_text("original\n")
        fixed = td / "service-state.txt"; fixed.write_text("original\n")
        FixedStateHandler.state_file = fixed
        FixedStateHandler.seen = []
        srv, th, base = serve(FixedStateHandler)
        try:
            pkg = LocalResourcePackage.from_directory("pkg-a", source)
            suite = Suite("PX", [mk_case("first"), mk_case("second")], {"pkg-a": pkg})
            r = replay_suite(suite, base, out / "reset_no_effect_run")
            defect = FixedStateHandler.seen[1]["before"] != "original\n"
            results["probes"]["reset_copy_not_bound_to_service_state"] = {
                "defect_reproduced": defect,
                "service_seen": FixedStateHandler.seen,
                "application_pins_before_all_match_original": all(a["pins_before"]["state.txt"] == pkg.pins["state.txt"].to_dict() for a in r.applications),
                "totals": r.totals,
            }
        finally:
            stop(srv, th)

    # 3. A timed-out request can occupy a serial service and cascade into the next application.
    SlowThenFastHandler.seen = []
    srv, th, base = serve(SlowThenFastHandler)
    try:
        suite = Suite("PX", [mk_case("slow", path="/slow", timeout=0.05), mk_case("fast-after-slow", path="/fast", timeout=0.10)])
        r = replay_suite(suite, base, out / "deadline_cascade_run")
        defect = r.totals["deadline_failures"] == 2
        results["probes"]["deadline_cascade_on_serial_target"] = {
            "defect_reproduced": defect,
            "server_seen": SlowThenFastHandler.seen,
            "totals": r.totals,
            "receipts": r.receipts,
        }
    finally:
        stop(srv, th)

    # 4. Expectations are not evaluated; an undocumented 500 is completed and http_failures remains zero.
    srv, th, base = serve(Status500Handler)
    try:
        suite = Suite("PX", [mk_case("unexpected-500", expectation=Expectation("only-200", {"status": [200]}))])
        r = replay_suite(suite, base, out / "unexpected_500_run")
        defect = r.totals["completed"] == 1 and r.totals["http_failures"] == 0 and r.receipts[0]["status"] == 500
        results["probes"]["unexpected_500_not_classified_against_expectation"] = {
            "defect_reproduced": defect,
            "expectation": suite.cases[0].expectation.to_dict(),
            "totals": r.totals,
            "receipts": r.receipts,
        }
    finally:
        stop(srv, th)

    # 5. Case IDs can escape the applications directory via path separators and '..'.
    srv, th, base = serve(HeaderHandler)
    try:
        c = mk_case("x/../../escaped-case")
        r = replay_suite(Suite("PX", [c]), base, out / "path_traversal_run")
        workdir = Path(r.applications[0]["workdir"]).resolve()
        apps_root = (out / "path_traversal_run" / "applications").resolve()
        defect = apps_root not in [workdir, *workdir.parents]
        results["probes"]["case_id_path_traversal_workdir_escape"] = {
            "defect_reproduced": defect,
            "case_id": c.case_id,
            "recorded_workdir": r.applications[0]["workdir"],
            "resolved_workdir": str(workdir),
            "applications_root": str(apps_root),
            "totals": r.totals,
        }
    finally:
        stop(srv, th)

    results["counts"]["probes_total"] = len(results["probes"])
    results["counts"]["defects_reproduced"] = sum(1 for p in results["probes"].values() if p.get("defect_reproduced"))
    (out / "outside_in_probes.json").write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(results["counts"], indent=2, sort_keys=True))

if __name__ == "__main__":
    main()

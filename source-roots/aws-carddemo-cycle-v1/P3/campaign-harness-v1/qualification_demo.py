#!/usr/bin/env python3
"""Run a real loopback-only synthetic qualification demonstration.

No AWS contract, fixture, COBOL binary, public API, model call, or official campaign
cell is loaded here. The demo exercises the common pre-campaign kernel with local
HTTP and local resource copies only.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from campaign_harness import (  # noqa: E402
    Case,
    Expectation,
    HttpRequestSpec,
    LocalResourcePackage,
    Suite,
    UnionBuilder,
    VerificationError,
    freeze_suite,
    load_frozen_suite,
    replay_suite,
)


class SyntheticHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    seen = []

    def do_POST(self):
        length_header = self.headers.get("Content-Length")
        body = self.rfile.read(int(length_header or "0")) if length_header is not None else None
        type(self).seen.append({"path": self.path, "content_length": length_header, "body": None if body is None else body.decode("utf-8")})
        if self.path == "/deadline":
            time.sleep(0.30)
            status, payload = 200, b'{"late":true}'
        elif self.path == "/documented-500":
            status, payload = 500, b'{"documentedFailure":true}'
        else:
            body_state = "absent" if body is None else body.decode("utf-8")
            status, payload = 200, json.dumps({"ok": True, "bodyState": body_state}).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        try:
            self.wfile.write(payload)
        except BrokenPipeError:
            pass

    def log_message(self, format, *args):  # noqa: A002
        pass


def make_case(case_id, suite_id, path="/ok", body_kind="absent", body_b64=None, expectation_id="nominal", timeout=1.0):
    return Case(
        case_id=case_id,
        suite_id=suite_id,
        origin=suite_id,
        request=HttpRequestSpec("POST", path, (("X-Synthetic", "qualification"),), body_kind, body_b64),
        resource_package_id="pkg-a",
        expectation=Expectation(expectation_id, {"status": [200, 500]}),
        timeout_seconds=timeout,
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run loopback-only synthetic qualification evidence")
    parser.add_argument("--output", required=True, help="New evidence directory")
    args = parser.parse_args(argv)
    out = Path(args.output)
    if out.exists():
        raise SystemExit(f"refusing to overwrite existing evidence directory: {out}")
    out.mkdir(parents=True)

    server = HTTPServer(("127.0.0.1", 0), SyntheticHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        resources = out / "source-resources" / "pkg-a"
        resources.mkdir(parents=True)
        (resources / "state.txt").write_text("original\n", encoding="utf-8")
        package = LocalResourcePackage.from_directory("pkg-a", resources)

        t1 = Suite("T1", [make_case("t1-absent", "T1"), make_case("t1-empty", "T1", body_kind="bytes", body_b64="")], {"pkg-a": package})
        t2 = Suite("T2", [make_case("t2-duplicate", "T2"), make_case("t2-distinct-expectation", "T2", expectation_id="distinct")], {"pkg-a": package})
        t3 = Suite("T3", [make_case("t3-json-empty-object", "T3", body_kind="json", body_b64="e30="), make_case("t3-doc-500", "T3", path="/documented-500"), make_case("t3-deadline", "T3", path="/deadline", timeout=0.05)], {"pkg-a": package})

        freeze_dir = out / "frozen-suites"
        suite_paths = [freeze_suite(s, freeze_dir / f"{s.suite_id}.json") for s in (t1, t2, t3)]
        loaded = [load_frozen_suite(p) for p in suite_paths]
        # Restore local resource handles intentionally; frozen JSON carries pins, not source paths.
        for suite in loaded:
            suite.resources = {"pkg-a": package}

        tampered_path = out / "tamper-copy.json"
        tampered_path.write_text(suite_paths[0].read_text(encoding="utf-8"), encoding="utf-8")
        tampered = json.loads(tampered_path.read_text(encoding="utf-8"))
        tampered["cases"][0]["request"]["path"] = "/tampered"
        tampered_path.write_text(json.dumps(tampered, indent=2, sort_keys=True), encoding="utf-8")
        try:
            load_frozen_suite(tampered_path)
            tamper_detected = False
            tamper_error = None
        except VerificationError as exc:
            tamper_detected = True
            tamper_error = str(exc)

        union, ledger = UnionBuilder().build(loaded)
        union.resources = {"pkg-a": package}
        union_path = freeze_suite(union, freeze_dir / "T4-union.json")
        union_loaded = load_frozen_suite(union_path)
        union_loaded.resources = {"pkg-a": package}

        first = replay_suite(union_loaded, base_url=base_url, output_dir=out / "runs" / "T4-mutated", mutate_resource={"state.txt": "changed\n"})
        second = replay_suite(union_loaded, base_url=base_url, output_dir=out / "runs" / "T4-fresh-copy")

        report = {
            "scope": "synthetic qualification only; no AWS campaign execution",
            "baseUrlKind": "loopback-http",
            "serialReplayNoRetryNoRedirect": True,
            "suiteFreezeHashes": {p.name: json.loads(p.read_text(encoding="utf-8"))["suite_freeze_sha256"] for p in suite_paths + [union_path]},
            "tamperDetected": tamper_detected,
            "tamperError": tamper_error if tamper_detected else None,
            "unionLedger": ledger,
            "unionCaseOrder": [case.case_id for case in union.cases],
            "unionProvenance": {case.case_id: list(case.provenance) for case in union.cases},
            "bodyKindsInUnion": [case.request.body_kind for case in union.cases],
            "firstRunTotals": first.totals,
            "secondRunTotals": second.totals,
            "httpCallsObserved": len(SyntheticHandler.seen),
            "freshCopyVerified": second.applications[0]["pins_before"]["state.txt"] == package.pins["state.txt"].to_dict(),
            "mutationDetectedAfterFirstApplication": first.applications[0]["pins_after"]["state.txt"] != package.pins["state.txt"].to_dict(),
            "deadlineFailuresSeparated": second.totals["deadline_failures"] == 1,
            "documented500NotHttpFailure": any(r["status"] == 500 and r["failure_class"] is None for r in second.receipts),
            "awsLoaded": False,
            "officialRunnerImplemented": False,
            "pendingIntegration": [
                "T1 generation adapter/package capture",
                "T2 OpenAPI fuzzer adapter for AWS contracts",
                "T3 independent MBT/reference adapter",
                "official fixture agenda and COBOL/API runners",
                "coverage denominator/collector integration",
            ],
        }
        (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps({"evidence": str(out), "union_cases": len(union.cases), "second_run_totals": second.totals, "tamperDetected": tamper_detected}, indent=2, sort_keys=True))
        return 0
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())

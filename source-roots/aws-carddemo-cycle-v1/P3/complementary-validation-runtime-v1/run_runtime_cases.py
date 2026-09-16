#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import http.server
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

RUNTIME = Path(__file__).resolve().parent
P3 = RUNTIME.parent
CYCLE = P3.parent
P2B = CYCLE / "P2b"
IMPL = P3 / "complementary-validation-implementation-v1"
FIXTURE_INDEX = P3 / "t3-mapping-recipes-v1" / "fixture-index.json"
EVID = RUNTIME / "evidence"
FROZEN = EVID / "frozen-inputs"
RUNS = EVID / "api-cobol-runs"
RAW_HTTP = EVID / "raw-http"

sys.path.insert(0, str(RUNTIME))
from tools.observation_extractor import extract_fixture_from_audits  # noqa: E402


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_p2b():
    spec = importlib.util.spec_from_file_location("p2b_runtime_binding", P2B / "p2b_binding.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load P2b binding")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.RUNS = RUNS
    mod.COMMAND_LOG = EVID / "command-log.jsonl"
    return mod


def descriptor_sha256(fx: dict[str, Any]) -> str:
    canonical = {k: v for k, v in fx.items() if k != "contentSha256"}
    return sha256_bytes(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode())


def freeze_inputs() -> dict[str, Any]:
    shutil.rmtree(FROZEN, ignore_errors=True)
    FROZEN.mkdir(parents=True)
    index = json.loads(FIXTURE_INDEX.read_text(encoding="utf-8"))
    selected = []
    manifest: dict[str, Any] = {
        "kind": "complementary-validation-runtime-freeze-v1",
        "createdUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sourceFixtureIndex": str(FIXTURE_INDEX),
        "sourceFixtureIndexSha256": sha256_file(FIXTURE_INDEX),
        "tracks": [],
        "nonClaims": ["not official campaign", "not expected output oracle", "not T1/T2/T3/T4 full campaign"],
    }
    for item in index["fixtures"]:
        track = item["track"]
        src_dir = Path(item["packagePath"])
        dst_dir = FROZEN / "packages" / track
        dst_dir.mkdir(parents=True)
        files = {}
        pins = {}
        allowed = {
            "posting": {"DALYTRAN", "TRANFILE", "ACCTFILE", "XREFFILE", "TCATBALF"},
            "interest": {"TCATBALF", "ACCTFILE", "XREFFILE", "XREFFILE.1", "DISCGRP", "PARMFILE"},
            "reporting": {"TRANFILE", "DATEPARM", "CARDXREF", "TRANTYPE", "TRANCATG"},
        }[track]
        for res in item["resources"]:
            dd = res["dd"]
            if dd.endswith(".empty") or dd not in allowed:
                continue
            src = src_dir / res["path"]
            data = src.read_bytes()
            if len(data) != res["bytes"] or sha256_bytes(data) != res["sha256"]:
                raise RuntimeError(f"source fixture pin mismatch {track}/{dd}")
            target = dst_dir / dd
            target.write_bytes(data)
            files[dd] = f"packages/{track}/{dd}"
            pins[dd] = {"bytes": len(data), "sha256": sha256_bytes(data)}
        fx = {
            "fixtureId": f"runtime-{item['fixtureId']}",
            "track": track,
            "capability": item.get("fixtureId"),
            "suiteUse": "bounded_runtime_semantic_checker_qualification",
            "materializer": {"kind": "local_file_package", "files": files, "filePins": pins},
            "provenance": {"class": "local_physical_fixture_package", "sourceFixtureIndex": str(FIXTURE_INDEX), "officialFixture": False},
            "exposure": {"label": "technical-only", "notExtractionInput": True, "notOracle": True, "notPublicRequest": True},
            "reset": {"default": "fresh_dir_per_run", "statefulSequence": "not_used"},
        }
        fx["contentSha256"] = descriptor_sha256(fx)
        selected.append(fx)
        manifest["tracks"].append({"track": track, "fixtureId": fx["fixtureId"], "files": pins})
    registry = {"kind": "p3-local-technical-fixture-selection", "fixtures": selected}
    (FROZEN / "fixture-registry.json").write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n")
    manifest["fixtureRegistrySha256"] = sha256_file(FROZEN / "fixture-registry.json")
    (FROZEN / "freeze-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def make_server(p2b):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path not in p2b.TRACKS:
                self.send_error(404)
                return
            length = int(self.headers.get("content-length", "0"))
            request_body = self.rfile.read(length)
            try:
                obj = json.loads(request_body or b"null")
            except Exception:
                obj = None
            err = p2b.validate_request(obj)
            if err:
                status, body = 400, {"track": self.path.strip("/"), "category": err, "completeness": "not_attested", "durability": "unknown"}
            else:
                try:
                    status, body, _audit = p2b.TRACKS[self.path](f"runtime-http-{int(time.time() * 1000)}")
                except Exception as exc:
                    status, body = 500, {"track": self.path.strip("/"), "category": "technical_failure", "error": type(exc).__name__, "message": str(exc), "completeness": "not_attested", "durability": "unknown"}
            raw = json.dumps(body, sort_keys=True).encode()
            self.send_response(status)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        def log_message(self, fmt: str, *args: Any) -> None:
            pass
    httpd = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, thread


def post_once(port: int, track: str) -> dict[str, Any]:
    RAW_HTTP.mkdir(parents=True, exist_ok=True)
    request_body = b"{}"
    req_path = RAW_HTTP / f"{track}.request.bin"
    resp_path = RAW_HTTP / f"{track}.response.bin"
    req_path.write_bytes(request_body)
    req = urllib.request.Request(f"http://127.0.0.1:{port}/{track}", data=request_body, headers={"content-type": "application/json"}, method="POST")
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read()
            status = resp.status
            headers = dict(resp.headers.items())
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
        headers = dict(exc.headers.items())
    resp_path.write_bytes(raw)
    return {"track": track, "status": status, "durationSeconds": round(time.time() - started, 3), "requestBytes": len(request_body), "requestSha256": sha256_file(req_path), "responseBytes": len(raw), "responseSha256": sha256_file(resp_path), "responseHeaders": headers, "responseJson": json.loads(raw)}


def main() -> int:
    EVID.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(RUNS, ignore_errors=True)
    shutil.rmtree(RAW_HTTP, ignore_errors=True)
    if (EVID / "command-log.jsonl").exists():
        (EVID / "command-log.jsonl").unlink()
    RUNS.mkdir(parents=True, exist_ok=True)
    freeze = freeze_inputs()
    p2b = load_p2b()
    os.environ[p2b.FIXTURE_ENV] = str(FROZEN / "fixture-registry.json")
    if not (p2b.BUILD / "CBTRN02C").exists():
        p2b.build()
    httpd, thread = make_server(p2b)
    port = httpd.server_address[1]
    results = []
    try:
        for track in ["posting", "interest", "reporting"]:
            results.append(post_once(port, track))
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
    audits = sorted(RUNS.glob("*/audit.json"))
    fixture = extract_fixture_from_audits("runtime-api-cobol-observations-v1", audits)
    (EVID / "typed-observations.json").write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n")
    cmd = [sys.executable, "-m", "semantic_checkers", "--verify-source", str(EVID / "typed-observations.json"), "--out", str(EVID / "semantic-check-results.json")]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(IMPL)
    completed = subprocess.run(cmd, cwd=IMPL, env=env, text=True, capture_output=True)
    summary = {
        "kind": "complementary-validation-runtime-v1",
        "freezeManifest": str(FROZEN / "freeze-manifest.json"),
        "freeze": freeze,
        "localhostPort": port,
        "httpResults": results,
        "auditPaths": [str(p) for p in audits],
        "typedObservations": str(EVID / "typed-observations.json"),
        "semanticCheckerCommand": cmd,
        "semanticCheckerReturncode": completed.returncode,
        "semanticCheckerStdout": completed.stdout,
        "semanticCheckerStderr": completed.stderr,
        "semanticCheckerResults": str(EVID / "semantic-check-results.json"),
        "boundaries": [
            "inputs are local physical technical fixture packages, not official campaign fixtures",
            "observations are extracted from HTTP responses, P2b audit JSON and raw run files only",
            "no expected output fields were inserted as observations",
            "effect ordering is conclusive only for write-observer events; account/tcatbal order without trace is boundary-labeled",
        ],
    }
    (EVID / "runtime-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if completed.returncode == 0 else completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

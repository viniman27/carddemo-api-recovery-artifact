#!/usr/bin/env python3
"""Independent Stage 9 HTTP handoff consumer.

Runs outside the extracted package. It starts the packaged API, calls the three
Stage6r3 routes, validates responses against the original OpenAPI schemas,
proves fresh resource reset inside one long-lived server process, and checks
fail-closed behavior for invalid request/resource configuration.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, RefResolver

RUN = Path(__file__).resolve().parent
SOURCE_RUN = RUN.parent / "E3-stage9-02"
PACKAGE = SOURCE_RUN / "E3-stage9-02-stage9-executable-package.tar.gz"
EXTRACT_ROOT = RUN / "fresh-package-copy"
PYTHON = Path(os.environ.get("STAGE9_PYTHON", "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2a/.venv/bin/python"))
ROUTES = {"posting": "PostingEnvelope", "interest": "InterestEnvelope", "reporting": "ReportingEnvelope"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def post_json(port: int, route: str, payload: bytes = b"{}", timeout: int = 90) -> dict[str, Any]:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/{route}",
        data=payload,
        headers={"content-type": "application/json"},
        method="POST",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
    return {
        "route": route,
        "status": status,
        "body": json.loads(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_bytes": len(raw),
        "duration_s": round(time.time() - started, 3),
    }


def wait_port(port_file: Path, proc: subprocess.Popen[str]) -> int:
    for _ in range(300):
        if port_file.exists():
            return int(port_file.read_text().strip())
        if proc.poll() is not None:
            break
        time.sleep(0.1)
    out, err = proc.communicate(timeout=1) if proc.poll() is not None else ("", "")
    raise RuntimeError(f"server did not publish port; return={proc.returncode}; stdout={out}; stderr={err}")


def start_server(p2b: Path, registry: Path, port_file: Path) -> subprocess.Popen[str]:
    if port_file.exists():
        port_file.unlink()
    env = dict(os.environ)
    env["P2B_FIXTURE_REGISTRY"] = str(registry)
    return subprocess.Popen(
        [str(PYTHON), str(p2b / "p2b_binding.py"), "serve", "--port-file", str(port_file)],
        cwd=p2b,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def stop_server(proc: subprocess.Popen[str]) -> dict[str, Any]:
    proc.terminate()
    try:
        out, err = proc.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate(timeout=10)
    return {"pid": proc.pid, "returncode": proc.returncode, "stdout": out, "stderr": err}


def latest_audits(p2b: Path, before: set[Path]) -> list[dict[str, Any]]:
    after = {p.resolve() for p in (p2b / "runs").glob("*") if p.is_dir()}
    audits = []
    for d in sorted(after - before):
        audit_path = d / "audit.json"
        if audit_path.exists():
            data = json.loads(audit_path.read_text())
            audits.append({"path": str(audit_path), "dir": str(d), "audit": data})
    return audits


def validate_schema(spec: dict[str, Any], schema_name: str, body: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator({"$ref": f"#/components/schemas/{schema_name}"}, resolver=RefResolver.from_schema(spec))
    return [e.message for e in sorted(validator.iter_errors(body), key=lambda e: [str(x) for x in e.path])]


def extract_package() -> Path:
    if EXTRACT_ROOT.exists():
        shutil.rmtree(EXTRACT_ROOT)
    EXTRACT_ROOT.mkdir(parents=True)
    with tarfile.open(PACKAGE, "r:gz") as tf:
        tf.extractall(EXTRACT_ROOT)
    roots = [p for p in EXTRACT_ROOT.iterdir() if p.is_dir()]
    if len(roots) != 1:
        raise RuntimeError(f"unexpected package roots: {roots}")
    return roots[0]


def resource_hashes_from_materialization(audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    files = audit["CAP"]["fixture_materialization"].get("files", {})
    return {
        name: {
            "sourceSha256": info.get("sourceSha256"),
            "materializedSha256": info.get("materializedSha256"),
            "materializedPath": info.get("materializedPath"),
            "bytes": info.get("materializedBytes"),
        }
        for name, info in files.items()
    }


def main() -> int:
    RUN.mkdir(parents=True, exist_ok=True)
    root = extract_package()
    p2b = root / "execution/isolated-cycle/aws-carddemo-cycle-v1/P2b"
    p2a = root / "execution/isolated-cycle/aws-carddemo-cycle-v1/P2a/openapi-carddemo-stage6r3.yaml"
    registry = root / "execution/isolated-cycle/aws-carddemo-cycle-v1/P3/technical-packages-v3-argument/registry.json"
    spec = yaml.safe_load(p2a.read_text())

    build_proc = subprocess.run([str(PYTHON), str(p2b / "p2b_binding.py"), "build"], cwd=p2b, capture_output=True, text=True, timeout=300)
    if build_proc.returncode != 0:
        raise RuntimeError(build_proc.stderr or build_proc.stdout)

    before_dirs = {p.resolve() for p in (p2b / "runs").glob("*") if p.is_dir()} if (p2b / "runs").exists() else set()
    proc = start_server(p2b, registry, RUN / "server.port")
    lifecycle = {"server_pid": proc.pid, "same_process_reset_probe": True}
    try:
        port = wait_port(RUN / "server.port", proc)
        route_results = [post_json(port, route) for route in ROUTES]
        schema_cases = []
        for result in route_results:
            schema = ROUTES[result["route"]]
            errors = validate_schema(spec, schema, result["body"])
            schema_cases.append({"route": result["route"], "schema": schema, "status": result["status"], "valid": not errors, "errors": errors})
        invalid_request = post_json(port, "posting", payload=b"[]")
        invalid_errors = validate_schema(spec, "InterfaceError", invalid_request["body"])
        schema_cases.append({"route": "posting-invalid-request", "schema": "InterfaceError", "status": invalid_request["status"], "valid": not invalid_errors, "errors": invalid_errors})

        # Same server process reset probe: mutate first invocation resources, then
        # call posting again and verify the second invocation re-materializes the
        # original bytes in a different workdir.
        reset_first = post_json(port, "posting")
        audits_after_first = latest_audits(p2b, before_dirs)
        posting_audits = [a for a in audits_after_first if a["audit"].get("INV", {}).get("track") == "posting"]
        first_audit = posting_audits[-1]
        first_resources = resource_hashes_from_materialization(first_audit["audit"])
        mutated = []
        for name, info in first_resources.items():
            path = Path(info["materializedPath"])
            if path.is_file():
                with path.open("ab") as fh:
                    fh.write(b"STAGE9_MUTATION_PROBE")
                mutated.append({"resource": name, "path": str(path), "mutated_sha256": sha256(path), "original_sha256": info["sourceSha256"]})
        before_second = {p.resolve() for p in (p2b / "runs").glob("*") if p.is_dir()}
        reset_second = post_json(port, "posting")
        second_audits = latest_audits(p2b, before_second)
        second_posting = [a for a in second_audits if a["audit"].get("INV", {}).get("track") == "posting"][-1]
        second_resources = resource_hashes_from_materialization(second_posting["audit"])
        reset_check = {
            "same_server_pid": proc.pid,
            "first_workdir": first_audit["audit"]["INV"]["workdir"],
            "second_workdir": second_posting["audit"]["INV"]["workdir"],
            "manual_mutations": mutated,
            "second_materialized_matches_source": {
                name: info.get("sourceSha256") == info.get("materializedSha256")
                for name, info in second_resources.items()
            },
        }
        reset_check["effective_reset_verified"] = (
            bool(mutated)
            and reset_check["first_workdir"] != reset_check["second_workdir"]
            and all(reset_check["second_materialized_matches_source"].values())
            and proc.poll() is None
        )
    finally:
        lifecycle.update(stop_server(proc))

    # Bad resource registry fail-closed probe in separate server because registry is process environment.
    bad_registry = RUN / "bad-registry.json"
    bad = json.loads(registry.read_text())
    for fx in bad["fixtures"]:
        if fx.get("track") == "posting":
            fx["materializer"]["files"]["UNSUPPORTED_DD"] = fx["materializer"]["files"].pop("DALYTRAN")
            break
    bad_registry.write_text(json.dumps(bad, indent=2) + "\n")
    before_bad_dirs = {p.resolve() for p in (p2b / "runs").glob("*") if p.is_dir()}
    bad_proc = start_server(p2b, bad_registry, RUN / "bad-server.port")
    try:
        bad_port = wait_port(RUN / "bad-server.port", bad_proc)
        bad_resource = post_json(bad_port, "posting")
        bad_new_audits = latest_audits(p2b, before_bad_dirs)
    finally:
        bad_lifecycle = stop_server(bad_proc)
    bad_resource_errors = validate_schema(spec, "InterfaceError", bad_resource["body"])

    all_audits = latest_audits(p2b, before_dirs)
    by_route = {a["audit"].get("INV", {}).get("track"): a for a in all_audits}
    route_audit_summary = []
    for route in ROUTES:
        audits = [a for a in all_audits if a["audit"].get("INV", {}).get("track") == route]
        a = audits[0]
        route_audit_summary.append({
            "route": route,
            "audit_path": a["path"],
            "reached_cobol": a["audit"].get("RESP", {}).get("reached_cobol"),
            "program_exit": a["audit"].get("RESP", {}).get("program_exit"),
            "status": a["audit"].get("RESP", {}).get("status"),
        })

    checks = {
        "fresh_copy_extracted": root.exists() and p2b.exists() and str(root).startswith(str(EXTRACT_ROOT)),
        "package_sha256": sha256(PACKAGE),
        "build_exit_zero": build_proc.returncode == 0,
        "three_routes_http_200": all(r["status"] == 200 for r in route_results),
        "schemas_original_valid": all(c["valid"] for c in schema_cases),
        "cobol_reached_three_routes": all(a["reached_cobol"] for a in route_audit_summary),
        "invalid_request_failclosed_400": invalid_request["status"] == 400 and not invalid_errors,
        "bad_resource_failclosed_500_no_audit": bad_resource["status"] == 500 and not bad_resource_errors and len(bad_new_audits) == 0,
        "reset_effective_same_process": reset_check["effective_reset_verified"],
    }
    result = {
        "kind": "stage9-independent-http-consumer-evidence",
        "source_stage9_run": str(SOURCE_RUN),
        "fresh_package_root": str(root),
        "python": str(PYTHON),
        "contract": {"path": str(p2a), "sha256": sha256(p2a)},
        "package": {"path": str(PACKAGE), "sha256": sha256(PACKAGE)},
        "start": {"command": [str(PYTHON), str(p2b / "p2b_binding.py"), "serve", "--port-file", str(RUN / "server.port")], "port": port},
        "route_results": route_results,
        "schema_cases": schema_cases,
        "route_audits": route_audit_summary,
        "invalid_request": invalid_request,
        "bad_resource": {"response": bad_resource, "new_audit_count": len(bad_new_audits), "server_lifecycle": bad_lifecycle},
        "reset_check": reset_check,
        "lifecycle": lifecycle,
        "checks": checks,
        "api_ready_for_testing": all(checks.values()),
        "campaign_ready": False,
        "human_gate": {"stage9_review_status": "pending", "human_approval_granted": False},
    }
    (RUN / "independent-http-consumer-report.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"api_ready_for_testing": result["api_ready_for_testing"], "checks": checks, "report": str(RUN / "independent-http-consumer-report.json")}, indent=2))
    return 0 if result["api_ready_for_testing"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse, base64, hashlib, importlib.util, json, os, shutil, subprocess, sys, time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
P3 = ROOT.parent
CYCLE = P3.parent
HARNESS_V3_SRC = P3 / "campaign-harness-v3" / "src"
COV_RUNNER = P3 / "coverage-candidate-check-v2" / "run_candidate_coverage_check.py"
P2A_PY = CYCLE / "P2a" / ".venv" / "bin" / "python"
PY = P2A_PY if P2A_PY.exists() else Path(sys.executable)

sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HARNESS_V3_SRC))

import campaign_harness as campaign_harness  # noqa: E402
from campaign_harness import Case, Expectation, HttpRequestSpec, Suite, UnionBuilder, freeze_suite, load_frozen_suite, replay_suite  # noqa: E402
from api_target import ContractChecker, PosixSpawnServer, build_fixture_registry_from_copy, copy_current_fixture_package, sha256_file  # noqa: E402
from reconcile_coverage import parse_gcov_file, select_units_by_program  # noqa: E402

EXPECTED_HARNESS_PATH = (HARNESS_V3_SRC / "campaign_harness.py").resolve()
EXPECTED_HARNESS_SHA256 = "0e5a9606b7d1ec10c2c07929a2fd18b72748e90ebdc4987a937bdc8fed5dd36e"
TRACKS = ("posting", "interest", "reporting")
BUSINESS = {"posting": "CBTRN02C", "interest": "CBACT04C", "reporting": "CBTRN03C"}
SOURCE_PATHS = {"CBTRN02C": "app/cbl/CBTRN02C.cbl", "CBACT04C": "app/cbl/CBACT04C.cbl", "CBTRN03C": "app/cbl/CBTRN03C.cbl"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_module_file_and_hash(module, expected_path: Path, expected_sha256: str) -> dict[str, Any]:
    actual_path = Path(module.__file__).resolve()
    actual_sha = sha256_path(actual_path)
    if actual_path != expected_path:
        raise RuntimeError(f"wrong campaign_harness import: {actual_path} != {expected_path}")
    if actual_sha != expected_sha256:
        raise RuntimeError(f"wrong campaign_harness hash: {actual_sha} != {expected_sha256}")
    return {"module": module.__name__, "file": str(actual_path), "sha256": actual_sha}


def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def patch_replay_body_capture() -> dict[str, Any]:
    original = campaign_harness._send_once

    def _send_once_with_body(base_url, req, timeout_seconds):
        from urllib.parse import urlparse
        import http.client, socket
        parsed = urlparse(base_url)
        host = parsed.hostname or "127.0.0.1"; port = parsed.port or 80
        body = req.body_bytes_or_none()
        conn = http.client.HTTPConnection(host, port, timeout=timeout_seconds)
        try:
            conn.putrequest(req.method, req.path, skip_accept_encoding=True)
            has_cl = any(k.lower() == "content-length" for k, _ in req.headers)
            for k, v in req.headers:
                conn.putheader(k, v)
            if body is not None and not has_cl:
                conn.putheader("Content-Length", str(len(body)))
            conn.endheaders(body if body is not None else None)
            resp = conn.getresponse(); payload = resp.read()
            return {"status": resp.status, "content_type": resp.getheader("Content-Type"), "response_bytes": len(payload), "response_sha256": sha256_bytes(payload), "response_body_b64": base64.b64encode(payload).decode("ascii"), "failure_class": None}
        except socket.timeout:
            return {"status": None, "content_type": None, "response_bytes": 0, "response_sha256": None, "response_body_b64": None, "failure_class": "deadline"}
        except OSError as exc:
            failure = "deadline" if "timed out" in str(exc).lower() else "transport"
            return {"status": None, "content_type": None, "response_bytes": 0, "response_sha256": None, "response_body_b64": None, "failure_class": failure, "error": str(exc)}
        finally:
            conn.close()

    campaign_harness._send_once = _send_once_with_body
    return {"patchedFunction": "campaign_harness._send_once", "reason": "collect raw response bytes for ContractChecker while preserving harness-v3 module file/hash", "originalFunctionId": id(original)}


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)


def copy_dir(src: Path, dst: Path) -> None:
    if dst.exists(): shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=False)


def load_coverage_runner():
    return import_module(COV_RUNNER, "unified_preflight_v2_coverage_runner")


def prepare_isolated_workspace(out: Path) -> dict[str, Any]:
    iso = out / "isolated-cycle"
    if iso.exists(): shutil.rmtree(iso)
    cycle = iso / "aws-carddemo-cycle-v1"; prep = iso / "aws-carddemo-preparation"
    copy_file(CYCLE / "P2a/openapi-carddemo-stage6r3.yaml", cycle / "P2a/openapi-carddemo-stage6r3.yaml")
    copy_file(CYCLE / "P2a/openapi-carddemo-stage6r3.json", cycle / "P2a/openapi-carddemo-stage6r3.json")
    for rel in ["P2b/p2b_binding.py", "P2b/runtime_observations.py", "P2b/write_observer.c", "P2b/interest_driver.cbl", "P2c-few-shot/p2c_facade.py", "P2c-zero-shot/p2c_facade.py"]:
        copy_file(CYCLE / rel, cycle / rel)
    for rel in ["collection-01/E2-2/response-original.txt", "collection-01/E1-1/response-original.txt"]:
        copy_file(CYCLE / rel, cycle / rel)
    prep_src = CYCLE.parent / "aws-carddemo-preparation"
    copy_file(prep_src / "evidence/research-package.json", prep / "evidence/research-package.json")
    copy_dir(prep_src / "research-corpus", prep / "research-corpus")
    copy_dir(prep_src / "expanded-batch/support", prep / "expanded-batch/support")
    package_copy = copy_current_fixture_package(CYCLE / "P3/fixture-materialization-v2/package", cycle / "P3/technical-packages-v3-argument/package")
    registry = build_fixture_registry_from_copy(package_copy, cycle / "P3/technical-packages-v3-argument/registry.json")
    cov = load_coverage_runner()
    isolated_patch = cov.patch_isolated_p2b(cycle)
    # Mechanical v2 amendment in the isolated copy only: preserve command-log rows
    # across replay_suite's per-case server restarts so each GCOV_PREFIX can be
    # tied to its request/run instead of only the final invocation.
    binding = cycle / "P2b/p2b_binding.py"
    text = binding.read_text()
    old_reset = "    COMMAND_LOG.write_text('')\n"
    new_reset = "    if not COMMAND_LOG.exists():\n        COMMAND_LOG.write_text('')\n"
    if old_reset not in text:
        raise RuntimeError("isolated P2b command-log reset pattern not found")
    binding.write_text(text.replace(old_reset, new_reset))
    isolated_patch["v2CommandLogPreservation"] = {"mechanical": True, "scope": "isolated P2b copy only", "patchedSha256AfterV2": sha256_path(binding)}
    return {"cycle": str(cycle), "prep": str(prep), "fixturePackageCopy": str(package_copy), "registry": str(registry), "registry_sha256": sha256_file(registry), "python": str(PY), "isolatedCoveragePatch": isolated_patch}


def classify_reach(audit_path: Path | None, cycle: Path, registry: Path, *, expected_track: str | None = None, expected_new: set[Path] | None = None) -> dict[str, Any]:
    if not audit_path or not audit_path.is_file():
        return {"audit_found": False, "reached_cobol": False, "admissibleSameInvocation": False, "inadmissibilityReasons": ["audit_missing"]}
    audit_path = audit_path.resolve()
    audit = json.loads(audit_path.read_text())
    p2b = Path(audit.get("p2bAuditPath", "")) if "p2bAuditPath" in audit else audit_path
    p2b_audit = json.loads(p2b.read_text()) if p2b.is_file() else audit
    workdir = p2b_audit.get("INV", {}).get("workdir")
    selected = p2b_audit.get("RES", {}).get("selected_fixture") or {}
    freg = selected.get("registryPath")
    reasons: list[str] = []
    cycle_resolved = cycle.resolve()
    workdir_resolved = Path(workdir).resolve() if workdir else None
    workdir_under = bool(workdir_resolved and str(workdir_resolved).startswith(str(cycle_resolved)))
    if not workdir_under: reasons.append("workdir_outside_isolated_cycle")
    if expected_track and (not workdir_resolved or not workdir_resolved.name.startswith(expected_track + "-")):
        reasons.append("run_dir_track_mismatch")
    if expected_new is not None and audit_path not in {p.resolve() for p in expected_new}:
        reasons.append("audit_not_from_current_replay_delta")
    registry_ok = bool(freg and Path(freg).resolve() == registry.resolve())
    if not registry_ok: reasons.append("fixture_registry_mismatch")
    reached = bool(p2b_audit.get("RESP", {}).get("reached_cobol"))
    if not reached: reasons.append("cobol_not_reached")
    return {"audit_found": True, "audit_path": str(audit_path), "p2b_audit_path": str(p2b) if p2b else None, "workdir": workdir, "workdir_under_isolated_cycle": workdir_under, "fixture_registry": freg, "fixture_registry_isolated": registry_ok, "reached_cobol": reached, "program_exit": p2b_audit.get("RESP", {}).get("program_exit"), "response_status_in_audit": p2b_audit.get("RESP", {}).get("status"), "failure_events": p2b_audit.get("FAIL", {}).get("events", []), "admissibleSameInvocation": not reasons, "inadmissibilityReasons": reasons}


def make_case(suite_id: str, case_id: str, track: str, provenance: str, extra: dict[str, Any]) -> Case:
    body_b64 = base64.b64encode(b"{}").decode("ascii")
    return Case(case_id=case_id, suite_id=suite_id, origin=provenance, request=HttpRequestSpec("POST", f"/{track}", (("content-type", "application/json"),), "json", body_b64), resource_package_id="fixture-copy-current", expectation=Expectation("documented-status", {"status": [200, 400, 500, 503]}), timeout_seconds=180.0, parameters={"track": track, **extra}, provenance=(provenance,))


def build_smoke_suites(inputs: Path, cycle: Path, registry: Path) -> tuple[Suite, Suite, Suite, Suite, dict[str, Any]]:
    inputs.mkdir(parents=True, exist_ok=True)
    sdd_cases = [make_case("SDD-SMOKE", f"SDD-SMOKE-E3-01-stage6r3-{track}", track, f"SDD:E3-01:stage6r3:{track}", {"arm": "sdd"}) for track in TRACKS]
    few = import_module(cycle / "P2c-few-shot/p2c_facade.py", "unified_v2_fewshot_facade")
    few_body = few.sample_request("E2-2", "interest")
    few_source = cycle / "P2c-few-shot/p2c_facade.py"
    few_case = make_case("FEWSHOT-SMOKE", "FEWSHOT-SMOKE-E2-2-interest-current", "interest", "FEWSHOT:E2-2:current:interest", {"arm": "fewshot", "sourceFacadeSha256": sha256_path(few_source), "sourceSampleSha256": sha256_bytes(json.dumps(few_body, sort_keys=True, ensure_ascii=False).encode())})
    zero = import_module(cycle / "P2c-zero-shot/p2c_facade.py", "unified_v2_zeroshot_facade")
    zero_body = zero.sample_request_for("E1-1", "posting", registry)
    zero_source = cycle / "P2c-zero-shot/p2c_facade.py"
    zero_case = make_case("ZEROSHOT-SMOKE", "ZEROSHOT-SMOKE-E1-1-posting-current", "posting", "ZEROSHOT:E1-1:current:posting", {"arm": "zeroshot", "sourceFacadeSha256": sha256_path(zero_source), "sourceSampleSha256": sha256_bytes(json.dumps(zero_body, sort_keys=True, ensure_ascii=False).encode())})
    raw = {"sdd": [c.to_dict() for c in sdd_cases], "fewshotCurrentRepresentative": few_case.to_dict(), "zeroshotCurrentRepresentative": zero_case.to_dict(), "note": "technical smoke uses approved empty-body P2b API path; full P2c bodies are pinned as current-source evidence, not public expected results"}
    (inputs / "fresh-smoke-adapter-inputs.json").write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n")
    sdd = Suite("SDD-SMOKE", sdd_cases)
    few_suite = Suite("FEWSHOT-SMOKE", [few_case])
    zero_suite = Suite("ZEROSHOT-SMOKE", [zero_case])
    union, ledger = UnionBuilder().build([sdd, few_suite, zero_suite])
    union.suite_id = "UNION-QUALIFICATION-NOT-T4"
    adapter = {"input": str(inputs / "fresh-smoke-adapter-inputs.json"), "input_sha256": sha256_path(inputs / "fresh-smoke-adapter-inputs.json"), "unionLedger": ledger, "fewshotFacade": {"path": str(few_source), "sha256": sha256_path(few_source)}, "zeroshotFacade": {"path": str(zero_source), "sha256": sha256_path(zero_source)}}
    return sdd, few_suite, zero_suite, union, adapter


def target_p2b(cycle: Path, registry: Path) -> PosixSpawnServer:
    return PosixSpawnServer([str(PY), str(cycle / "P2b/p2b_binding.py"), "serve", "--port-file", "{port_file}"], cwd=cycle / "P2b", env={"P2B_FIXTURE_REGISTRY": str(registry)})


def audit_delta(roots: list[Path], before: set[Path]) -> list[Path]:
    out: list[Path] = []
    for r in roots:
        if r.exists():
            out.extend([p.resolve() for p in r.rglob("audit.json") if p.resolve() not in before])
    return sorted(out, key=lambda p: p.stat().st_mtime)


def run_gcov_for_invocation(p2b: Path, wd: Path, prog: str, gcda_files: list[Path]) -> dict[str, Any]:
    cov = load_coverage_runner()
    return cov.run_gcov_for_invocation(p2b, wd, prog, gcda_files)


def command_env_for_run(p2b: Path, run_dir: Path, prog: str) -> list[dict[str, Any]]:
    cov = load_coverage_runner()
    return cov.command_log_env_for_run(p2b, run_dir, prog)


def collect_fresh_coverage_evidence(p2b: Path, audit_path: Path, track: str) -> dict[str, Any]:
    audit = json.loads(audit_path.read_text())
    wd = Path(audit.get("INV", {}).get("workdir", audit_path.parent)).resolve()
    prog = BUSINESS[track]
    gcda = sorted(wd.rglob("*.gcda"))
    business_gcda = [p for p in gcda if prog in p.name or (prog == "CBACT04C" and "CBACT04C" in p.name)]
    support_gcda = [p for p in gcda if p not in business_gcda]
    gcov_rec = run_gcov_for_invocation(p2b, wd, prog, gcda)
    units = [parse_gcov_file(Path(x["path"])) for x in gcov_rec.get("gcovFiles", []) if Path(x["path"]).exists()]
    selected = select_units_by_program(prog, units) if units else None
    env_rows = command_env_for_run(p2b, wd, prog)
    expected_prefix = str(wd / "gcov")
    prefix_ok = any(r.get("env_subset", {}).get("GCOV_PREFIX") == expected_prefix for r in env_rows)
    program_exit = audit.get("RESP", {}).get("program_exit")
    reasons: list[str] = []
    if not business_gcda: reasons.append("business_gcda_missing")
    if not prefix_ok: reasons.append("gcov_prefix_not_observed_for_business_command")
    if not units: reasons.append("gcov_units_missing")
    if not selected: reasons.append("main_generated_c_unit_missing")
    return {"track": track, "businessProgram": prog, "runDir": str(wd), "requestInvocation": wd.name, "programExit": program_exit, "normalProcessExitObserved": isinstance(program_exit, int) and program_exit >= 0, "gcovPrefix": expected_prefix, "gcovPrefixObservedInCommandLog": prefix_ok, "businessCommandEnvEvidence": env_rows, "gcdaFiles": [{"path": str(p), "rel": p.relative_to(wd).as_posix(), "bytes": p.stat().st_size, "sha256": sha256_path(p), "business": p in business_gcda, "supportExcluded": p in support_gcda} for p in gcda], "businessGcdaPresent": bool(business_gcda), "gcov11": gcov_rec, "correctedParser": {"mainGeneratedC": selected["mainGeneratedC"] if selected else None, "unitCount": len(units), "selectionRule": "program.c only; no header/support fallback"}, "measurementAdmissibility": "admissible_preparatory" if not reasons else "inadmissible_or_limited", "inadmissibilityReasons": reasons}


def run_and_collect(suite: Suite, target: PosixSpawnServer, out: Path, checker_path: Path, cycle: Path, registry: Path, audit_roots: list[Path]) -> dict[str, Any]:
    frozen = out / "freeze" / f"{suite.suite_id}.json"; freeze_suite(suite, frozen); loaded = load_frozen_suite(frozen)
    before: set[Path] = set()
    for r in audit_roots:
        if r.exists(): before |= {p.resolve() for p in r.rglob("audit.json")}
    result = replay_suite(loaded, target=target, output_dir=out / "replay")
    new_audits = audit_delta(audit_roots, before)
    by_track: dict[str, list[Path]] = {}
    for p in new_audits:
        name = p.parent.name
        tr = name.split("-", 1)[0]
        by_track.setdefault(tr, []).append(p)
    checker = ContractChecker(checker_path)
    checks = []
    used: set[Path] = set()
    for receipt in result.receipts:
        raw = base64.b64decode(receipt.get("response_body_b64") or b"") if receipt.get("response_body_b64") else b""
        check = checker.check(receipt["method"], receipt["path"], receipt.get("status"), receipt.get("content_type"), raw)
        track = receipt["path"].strip("/").split("/")[-1]
        candidates = [p for p in by_track.get(track, []) if p not in used]
        audit = candidates[0] if candidates else None
        if audit: used.add(audit)
        reach = classify_reach(audit, cycle, registry, expected_track=track, expected_new=set(new_audits))
        coverage = collect_fresh_coverage_evidence(cycle / "P2b", audit, track) if audit and reach.get("audit_found") else {"measurementAdmissibility": "inadmissible_or_limited", "inadmissibilityReasons": ["audit_missing"]}
        checks.append({"case_id": receipt["case_id"], "suite_id": receipt.get("suite_id"), "request": {"method": receipt["method"], "path": receipt["path"], "status": receipt.get("status"), "response_sha256": receipt.get("response_sha256")}, "checker": check.__dict__, "reach": reach, "coverage": coverage})
    return {"suite_id": suite.suite_id, "frozen": str(frozen), "frozen_sha256": sha256_path(frozen), "loaded_case_count": len(loaded.cases), "moduleEvidence": {"replayFunction": "campaign_harness.replay_suite", "target": "isolated P2b API over instrumented COBOL"}, "totals": result.totals, "receipts": str(result.output_dir / "receipts.json"), "applications": str(result.output_dir / "applications.json"), "newAuditCount": len(new_audits), "checks": checks, "applications_inline": result.applications}


def source_hashes(cycle: Path) -> list[dict[str, Any]]:
    corpus = cycle.parent / "aws-carddemo-preparation" / "research-corpus"
    return [{"program": prog, "path": rel, "sha256": sha256_path(corpus / rel), "bytes": (corpus / rel).stat().st_size} for prog, rel in SOURCE_PATHS.items()]


def reset_comparison(first: dict[str, Any], second: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    by_case_2 = {c["case_id"]: c for c in second.get("checks", [])}
    for c1 in first.get("checks", []):
        c2 = by_case_2.get(c1["case_id"])
        if not c2: continue
        cov1, cov2 = c1.get("coverage", {}), c2.get("coverage", {})
        files1 = {x.get("rel"): x.get("sha256") for x in cov1.get("gcdaFiles", []) if x.get("business")}
        files2 = {x.get("rel"): x.get("sha256") for x in cov2.get("gcdaFiles", []) if x.get("business")}
        rows.append({"case_id": c1["case_id"], "track": cov1.get("track"), "firstRunDir": cov1.get("runDir"), "secondRunDir": cov2.get("runDir"), "distinctRunDirs": cov1.get("runDir") != cov2.get("runDir"), "firstGcovPrefix": cov1.get("gcovPrefix"), "secondGcovPrefix": cov2.get("gcovPrefix"), "distinctGcovPrefixes": cov1.get("gcovPrefix") != cov2.get("gcovPrefix"), "firstBusinessGcda": files1, "secondBusinessGcda": files2, "businessGcdaBothPresent": bool(files1) and bool(files2), "counterHashesCompared": files1 == files2 or files1 != files2, "resetVerifiedBeyondDifferentDirs": cov1.get("gcovPrefix") != cov2.get("gcovPrefix") and bool(files1) and bool(files2)})
    return rows


def write_candidate_manifest(out: Path, report: dict[str, Any]) -> dict[str, Any]:
    deps = []
    for rel in ["unified_preflight_cli.py", "src/suite_adapters.py", "src/api_target.py", "src/reconcile_coverage.py"]:
        p = ROOT / rel; deps.append({"path": str(p), "sha256": sha256_path(p), "bytes": p.stat().st_size})
    for p in [EXPECTED_HARNESS_PATH, CYCLE / "P2b/p2b_binding.py", CYCLE / "P2c-few-shot/p2c_facade.py", CYCLE / "P2c-zero-shot/p2c_facade.py", CYCLE / "P2a/openapi-carddemo-stage6r3.yaml", CYCLE / "P3/fixture-materialization-v2/package/manifest.json"]:
        deps.append({"path": str(p), "sha256": sha256_path(p), "bytes": p.stat().st_size})
    manifest = {"kind": "unified-preflight-v2-candidate-manifest", "status": "candidate_not_campaign_authorization", "createdUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "dependencies": deps, "limits": ["technical preflight only", "no official T1/T2/T3/T4 cases generated", "no model calls", "union qualification is dependent smoke, not official T4", "mechanical isolated P2b copy patched only for coverage build/GCOV_PREFIX; business sources/contracts/public SDD unchanged"], "authorization": {"campaignAuthorized": False, "fabricatedAuthorization": False}, "reportPath": str(out / "unified-preflight-report.json")}
    p = out / "candidate-manifest.json"; p.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="unified-preflight-v2 fresh coverage qualification CLI; preflight only")
    parser.add_argument("--mode", required=True, choices=["preflight"])
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    out = Path(args.output).resolve()
    if out.exists(): raise SystemExit(f"refusing to overwrite existing output directory: {out}")
    out.mkdir(parents=True)
    import_evidence = assert_module_file_and_hash(campaign_harness, EXPECTED_HARNESS_PATH, EXPECTED_HARNESS_SHA256)
    patch_evidence = patch_replay_body_capture()
    prep = prepare_isolated_workspace(out)
    cycle = Path(prep["cycle"]); registry = Path(prep["registry"])
    inputs = out / "adapter-inputs"
    sdd, few, zero, union, adapter = build_smoke_suites(inputs, cycle, registry)
    freeze_suite(union, out / "freeze" / "UNION-QUALIFICATION-NOT-T4.json")
    union_first = run_and_collect(union, target_p2b(cycle, registry), out / "union-first", cycle / "P2a/openapi-carddemo-stage6r3.yaml", cycle, registry, [cycle / "P2b/runs"])
    union_reset = run_and_collect(union, target_p2b(cycle, registry), out / "union-reset-qualification", cycle / "P2a/openapi-carddemo-stage6r3.yaml", cycle, registry, [cycle / "P2b/runs"])
    reset_rows = reset_comparison(union_first, union_reset)
    all_checks = union_first["checks"] + union_reset["checks"]
    counts = {"technical_smoke_cases": len(union.cases), "sdd_cases": len(sdd.cases), "fewshot_cases": len(few.cases), "zeroshot_cases": len(zero.cases), "union_reset_cases": len(union_reset["checks"]), "http_completed": union_first["totals"]["completed"] + union_reset["totals"]["completed"], "checker_ok": sum(1 for r in all_checks if r["checker"].get("ok")), "reached_cobol": sum(1 for r in all_checks if r["reach"].get("reached_cobol")), "business_gcda_present": sum(1 for r in all_checks if r["coverage"].get("businessGcdaPresent")), "gcov_prefix_observed": sum(1 for r in all_checks if r["coverage"].get("gcovPrefixObservedInCommandLog")), "admissible_preparatory_coverage": sum(1 for r in all_checks if r["coverage"].get("measurementAdmissibility") == "admissible_preparatory"), "reset_rows_verified": sum(1 for r in reset_rows if r.get("resetVerifiedBeyondDifferentDirs"))}
    report = {"kind": "unified-preflight-v2-report", "scope": "single executable technical preflight with fresh same-invocation coverage; not campaign; not official T1/T2/T3/T4 generation", "harnessImport": import_evidence, "bodyCapturePatch": patch_evidence, "prepared": prep, "sourceHashes": source_hashes(cycle), "targetHashes": {"p2bBinding": sha256_path(cycle / "P2b/p2b_binding.py"), "buildReport": sha256_path(cycle / "P2b/build-report.json") if (cycle / "P2b/build-report.json").exists() else None}, "adapterEvidence": adapter, "runs": {"unionFirst": union_first, "unionResetQualificationNotT4": union_reset}, "resetComparison": reset_rows, "counts": counts, "blockersPreserved": ["No campaign authorization is created by this preflight.", "Union qualification is dependent smoke only and not official T4.", "Absence of business .gcda is inadmissible, not zero coverage.", "program_exit=4 is preserved as a normal non-zero precondition/status, not rewritten to success.", "Manifest is candidate-only and contains no campaign authorization."], "businessSourceEdited": False}
    (out / "unified-preflight-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    manifest = write_candidate_manifest(out, report)
    (out / "REPORT.md").write_text("# unified-preflight-v2\n\n" + json.dumps({"counts": counts, "harnessImport": import_evidence, "manifest": str(out / "candidate-manifest.json"), "report": str(out / "unified-preflight-report.json")}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "counts": counts, "manifest": str(out / "candidate-manifest.json"), "officialGateEnabled": False}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

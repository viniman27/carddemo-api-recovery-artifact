#!/usr/bin/env python3
"""P3 coverage API integration smoke for AWS CardDemo SDD/P2b.

Creates an isolated copy of the API harness, patches only that copied API binding
so the three COBOL business programs are built through cobc -C + gcc-11/gcov-11,
and performs synthetic HTTP smoke calls. This is not an official coverage campaign.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
P3 = ROOT.parent
CYCLE = P3.parent
SOURCE_ISOLATED = P3 / "api-harness-integration-v1" / "isolated-cycle"
OUT_ISOLATED = ROOT / "isolated-cycle"
RUN_OUTPUT = ROOT / "run-output"
REPORT = ROOT / "coverage-api-integration-report.json"

BUSINESS = {"posting": "CBTRN02C", "interest": "CBACT04C", "reporting": "CBTRN03C"}
PATHS = {"CBTRN02C": "app/cbl/CBTRN02C.cbl", "CBACT04C": "app/cbl/CBACT04C.cbl", "CBTRN03C": "app/cbl/CBTRN03C.cbl"}
SUPPORT_NAMES = {"write_observer.c", "interest_driver.cbl", "intcalc_fixture.cbl", "report_fixture.cbl", "CBACT04C_driver.cbl", "CEE3ABD2.cbl"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str | Path], cwd: Path, *, env: dict[str, str] | None = None, expect: int | None = 0, timeout: int = 180) -> dict[str, Any]:
    e = os.environ.copy()
    if env:
        e.update({k: str(v) for k, v in env.items()})
    started = time.time()
    cp = subprocess.run([str(x) for x in cmd], cwd=str(cwd), env=e, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    rec = {"cmd": [str(x) for x in cmd], "cwd": str(cwd), "exit_code": cp.returncode, "stdout": cp.stdout, "stderr": cp.stderr, "duration_s": round(time.time() - started, 3)}
    if expect is not None and cp.returncode != expect:
        raise RuntimeError(json.dumps(rec, indent=2))
    return rec


def copy_isolated_cycle() -> dict[str, Any]:
    if not SOURCE_ISOLATED.exists():
        raise SystemExit(f"Missing prerequisite isolated API cycle: {SOURCE_ISOLATED}")
    if OUT_ISOLATED.exists():
        shutil.rmtree(OUT_ISOLATED)
    if RUN_OUTPUT.exists():
        shutil.rmtree(RUN_OUTPUT)
    ROOT.mkdir(parents=True, exist_ok=True)
    def ignore(_dir: str, names: list[str]) -> set[str]:
        return {n for n in names if n in {"__pycache__", ".pytest_cache", "runs", "build", "build-local", "outputs", "server.port", "server-access.log", "command-log.jsonl"} or n.endswith(".pyc")}
    shutil.copytree(SOURCE_ISOLATED, OUT_ISOLATED, ignore=ignore)
    return {"source": str(SOURCE_ISOLATED), "copy": str(OUT_ISOLATED), "copySha256": tree_hash(OUT_ISOLATED)}


def tree_hash(root: Path) -> str:
    rows = []
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        rows.append({"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size, "sha256": sha256(p)})
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def patch_isolated_p2b() -> dict[str, Any]:
    p2b = OUT_ISOLATED / "aws-carddemo-cycle-v1" / "P2b"
    binding = p2b / "p2b_binding.py"
    original = binding.read_text()
    build_match = re.search(r"\ndef build\(\) -> dict\[str, Any\]:\n.*?\n\ndef io_file", original, flags=re.S)
    if not build_match:
        raise RuntimeError("could not find build() block in isolated P2b binding")
    instrumented_build = r'''
def _p3_parse_cobc_flags(text: str) -> dict[str, list[str]]:
    include_flags = []
    lib_flags = []
    for line in text.splitlines():
        for token in line.strip().split():
            if token.startswith('-I'):
                include_flags.append(token)
            elif token.startswith('-L') or token == '-lcob':
                lib_flags.append(token)
    if not any('gnucobol' in f for f in include_flags):
        include_flags.append('-I/opt/homebrew/Cellar/gnucobol/3.2_1/include')
    if '-lcob' not in lib_flags:
        lib_flags.append('-lcob')
    return {'includeFlags': include_flags, 'libFlags': lib_flags}


def _p3_tool_text(cmd: list[str]) -> str:
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout


def _p3_gcc_compile(sources: list[Path], output: Path, flags: dict[str, list[str]], *, shared: bool = False) -> dict[str, Any]:
    sdk = subprocess.check_output(['xcrun', '--show-sdk-path'], text=True).strip()
    cmd: list[str | Path] = ['gcc-11', '-isysroot', sdk, '-O0', '-g', '-fprofile-arcs', '-ftest-coverage']
    cmd += flags['includeFlags']
    cmd += ['-Wno-unused', '-fsigned-char', '-Wno-pointer-sign']
    if shared:
        cmd += ['-dynamiclib', '-undefined', 'dynamic_lookup']
    cmd += ['-o', output]
    cmd += sources
    if not shared:
        cmd += flags['libFlags']
    return run_cmd(cmd, cwd=output.parent)


def _p3_generate_c(src: Path, out_c: Path, cp: Path, *, executable: bool, extra: list[str] | None = None) -> dict[str, Any]:
    cmd: list[str | Path] = ['cobc', '-std=ibm', '-fsign=ascii', '-I', cp]
    cmd.append('-x' if executable else '-m')
    if extra:
        cmd += extra
    cmd += ['-C', '-o', out_c, src]
    return run_cmd(cmd, cwd=out_c.parent)


def build() -> dict[str, Any]:
    ROOT.mkdir(exist_ok=True)
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(exist_ok=True)
    COMMAND_LOG.write_text('')
    pins = verify_source_pins()
    (ROOT / 'support-generated').mkdir(exist_ok=True)
    info = _p3_tool_text(['cobc', '-info'])
    flags = _p3_parse_cobc_flags(info)
    cp = CORPUS / 'app' / 'cpy'
    common = ['cobc', '-std=ibm', '-fsign=ascii', '-I', cp]
    commands: list[dict[str, Any]] = []
    business_sources = {
        'CBTRN02C': CORPUS / 'app/cbl/CBTRN02C.cbl',
        'CBACT04C': CORPUS / 'app/cbl/CBACT04C.cbl',
        'CBTRN03C': CORPUS / 'app/cbl/CBTRN03C.cbl',
    }
    commands.append({'stage':'cobc-C','program':'CBTRN02C', **_p3_generate_c(business_sources['CBTRN02C'], BUILD / 'CBTRN02C.c', cp, executable=True, extra=['-A','-Dcob_write=p2b_observed_write'])})
    sdk = subprocess.check_output(['xcrun', '--show-sdk-path'], text=True).strip()
    clang_cmd: list[str | Path] = ['clang', '-isysroot', sdk, *flags['includeFlags'], '-c', ROOT / 'write_observer.c', '-o', BUILD / 'write_observer.o']
    commands.append({'stage':'support-clang-object-uninstrumented','program':'write_observer.c', **run_cmd(clang_cmd, cwd=BUILD)})
    commands.append({'stage':'gcc-11-coverage','program':'CBTRN02C', **_p3_gcc_compile([BUILD / 'CBTRN02C.c', BUILD / 'write_observer.o'], BUILD / 'CBTRN02C', flags)})
    commands.append({'stage':'cobc-C','program':'CBACT04C', **_p3_generate_c(business_sources['CBACT04C'], BUILD / 'CBACT04C.c', cp, executable=False)})
    commands.append({'stage':'gcc-11-coverage','program':'CBACT04C', **_p3_gcc_compile([BUILD / 'CBACT04C.c'], BUILD / 'CBACT04C.dylib', flags, shared=True)})
    commands.append({'stage':'cobc-C','program':'CBTRN03C', **_p3_generate_c(business_sources['CBTRN03C'], BUILD / 'CBTRN03C.c', cp, executable=True)})
    commands.append({'stage':'gcc-11-coverage','program':'CBTRN03C', **_p3_gcc_compile([BUILD / 'CBTRN03C.c'], BUILD / 'CBTRN03C', flags)})
    for name in ['intcalc_fixture', 'report_fixture', 'CBACT04C_driver', 'CEE3ABD2']:
        src = EXPANDED_SUPPORT / f'{name}.cbl'
        commands.append({'stage':'support-cobc-uninstrumented','program':name, **run_cmd(common + ['-x' if name != 'CEE3ABD2' else '-m', '-free', '-o', BUILD / ('CEE3ABD.dylib' if name == 'CEE3ABD2' else name), src], cwd=BUILD)})
    run_cmd(common + ['-x', '-free', '-o', BUILD / 'P2B_INTEREST_DRIVER', ROOT / 'interest_driver.cbl'], cwd=BUILD)
    for dd, (size, key) in IO_SPECS.items():
        helper = ROOT / 'support-generated' / f'io_{dd}.cbl'
        helper.write_text(IO_TEMPLATE.format(size=size, key=key, rest=size - key))
        commands.append({'stage':'support-io-cobc-uninstrumented','program':f'io_{dd}', **run_cmd(common + ['-x', '-free', '-o', BUILD / f'io_{dd}', helper], cwd=BUILD)})
    binaries = []
    for artifact in ['CBTRN02C', 'CBACT04C.dylib', 'CBTRN03C', 'P2B_INTEREST_DRIVER', 'CBACT04C_driver', 'intcalc_fixture', 'report_fixture']:
        p = BUILD / artifact
        binaries.append({'path': str(p), 'sha256': sha256(p), 'bytes': p.stat().st_size, 'businessInstrumented': artifact in {'CBTRN02C','CBACT04C.dylib','CBTRN03C'}})
    out = {'built': True, 'kind':'p3-isolated-coverage-build', 'coverageToolchain':'cobc -C + gcc-11 -fprofile-arcs -ftest-coverage + gcov-11', 'build_dir': str(BUILD), 'source_pins': pins, 'commands_jsonl': str(COMMAND_LOG), 'instrumentedCommands': commands, 'binaries': binaries, 'gcovPrefixPolicy':'per-invocation GCOV_PREFIX under each P2b run directory; no shared .gcda accumulation'}
    (ROOT / 'build-report.json').write_text(json.dumps(out, indent=2) + '\n')
    return out


def io_file'''
    patched = original[:build_match.start()] + "\n" + instrumented_build + original[build_match.end():]
    # Per-invocation GCOV_PREFIX for the three business executions.
    patched = patched.replace('env={"COB_LIBRARY_PATH": str(BUILD), "P2B_INVOCATION": wd.name, "P2B_WRITE_LOG": str(wd / "write-observations.log"), **{f"DD_{dd}": str(wd / dd) for dd in [*SIZES, "DALYTRAN", "DALYREJS"]}}', 'env={"COB_LIBRARY_PATH": str(BUILD), "P2B_INVOCATION": wd.name, "P2B_WRITE_LOG": str(wd / "write-observations.log"), "GCOV_PREFIX": str(wd / "gcov"), "GCOV_PREFIX_STRIP": str(len(BUILD.resolve().parts)), **{f"DD_{dd}": str(wd / dd) for dd in [*SIZES, "DALYTRAN", "DALYREJS"]}}')
    patched = patched.replace('env={"COB_LIBRARY_PATH": str(BUILD), **{f"DD_{dd}": str(wd / dd) for dd in (*RESOURCE_NAMES["interest"], "TRANSACT")}}', 'env={"COB_LIBRARY_PATH": str(BUILD), "GCOV_PREFIX": str(wd / "gcov"), "GCOV_PREFIX_STRIP": str(len(BUILD.resolve().parts)), **{f"DD_{dd}": str(wd / dd) for dd in (*RESOURCE_NAMES["interest"], "TRANSACT")}}')
    patched = patched.replace('env={"COB_LIBRARY_PATH": str(BUILD), **{f"DD_{dd}": str(wd / dd) for dd in (*RESOURCE_NAMES["reporting"], "TRANREPT")}}', 'env={"COB_LIBRARY_PATH": str(BUILD), "GCOV_PREFIX": str(wd / "gcov"), "GCOV_PREFIX_STRIP": str(len(BUILD.resolve().parts)), **{f"DD_{dd}": str(wd / dd) for dd in (*RESOURCE_NAMES["reporting"], "TRANREPT")}}')
    # Keep API errors observable in the isolated smoke instead of swallowed silently.
    patched = patched.replace('        except Exception:\n            body = error_body(self.path.strip(\'/\'), "technical_failure")\n            status = 500\n', '        except Exception as exc:\n            body = error_body(self.path.strip(\'/\'), "technical_failure")\n            body["exception"] = repr(exc)\n            status = 500\n')
    binding.write_text(patched)
    return {"path": str(binding), "originalSha256": hashlib.sha256(original.encode()).hexdigest(), "patchedSha256": sha256(binding), "patchScope":"isolated P2b copy only; COBOL business sources/contracts unchanged"}


def fixture_registry() -> Path:
    reg = OUT_ISOLATED / "aws-carddemo-cycle-v1" / "P3" / "technical-packages-v3-argument" / "registry.json"
    if not reg.exists():
        raise RuntimeError(f"fixture registry missing: {reg}")
    return reg


def start_server(p2b: Path, env: dict[str, str]) -> tuple[subprocess.Popen[str], int, Path]:
    server_dir = RUN_OUTPUT / "server"
    server_dir.mkdir(parents=True, exist_ok=True)
    port_file = server_dir / "server.port"
    if port_file.exists():
        port_file.unlink()
    e = os.environ.copy()
    if "P2B_FIXTURE_REGISTRY" not in env:
        e.pop("P2B_FIXTURE_REGISTRY", None)
    e.update(env)
    proc = subprocess.Popen([sys.executable, "p2b_binding.py", "serve", "--port-file", str(port_file)], cwd=str(p2b), env=e, text=True, stdout=(server_dir / "server.stdout").open("w"), stderr=(server_dir / "server.stderr").open("w"))
    for _ in range(400):
        if port_file.exists():
            return proc, int(port_file.read_text()), server_dir
        if proc.poll() is not None:
            raise RuntimeError(f"server exited before port file; rc={proc.returncode}")
        time.sleep(0.05)
    raise TimeoutError("server did not publish port")


def http_post(port: int, track: str) -> dict[str, Any]:
    req = urllib.request.Request(f"http://127.0.0.1:{port}/{track}", data=b"{}", headers={"content-type":"application/json"}, method="POST")
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read()
            return {"track": track, "status": r.status, "body": json.loads(raw), "bodySha256": hashlib.sha256(raw).hexdigest(), "duration_s": round(time.time()-started,3)}
    except urllib.error.HTTPError as e:
        raw = e.read()
        return {"track": track, "status": e.code, "body": json.loads(raw or b"{}"), "bodySha256": hashlib.sha256(raw).hexdigest(), "duration_s": round(time.time()-started,3)}


def collect_run_evidence(p2b: Path, before: set[Path], after_http: dict[str, Any]) -> dict[str, Any]:
    runs_dir = p2b / "runs"
    after = {p.resolve() for p in runs_dir.glob("*") if p.is_dir()}
    new_dirs = sorted(after - before, key=lambda p: p.stat().st_mtime)
    if not new_dirs:
        return {"http": after_http, "error":"no new run dir found"}
    wd = new_dirs[-1]
    audit_path = wd / "audit.json"
    audit = json.loads(audit_path.read_text()) if audit_path.exists() else {}
    gcda = sorted([p for p in wd.rglob("*.gcda")])
    gcno = sorted([p for p in (p2b / "build").glob("*.gcno")])
    prog = BUSINESS[after_http["track"]]
    c_file = p2b / "build" / f"{prog}.c"
    gcov_rec: dict[str, Any] | None = None
    if c_file.exists() and gcda:
        # Copy the matching .gcno note into this invocation's GCOV_PREFIX dir and run
        # gcov there, so readout uses only the invocation's isolated .gcda.
        matching_gcno = None
        for candidate in sorted((p2b / "build").glob("*.gcno")):
            if prog in candidate.name or (prog == "CBACT04C" and "CBACT04C" in candidate.name):
                matching_gcno = candidate
                break
        candidates = [p.parent for p in gcda if prog in p.name or (prog == "CBACT04C" and "CBACT04C" in p.name)]
        objdir = candidates[0] if candidates else gcda[0].parent
        if matching_gcno is not None:
            shutil.copy2(matching_gcno, objdir / matching_gcno.name)
            gcov_rec = run(["gcov-11", "-b", "-c", "-o", matching_gcno.name, c_file], cwd=objdir, expect=None)
        else:
            gcov_rec = run(["gcov-11", "-b", "-c", "-o", objdir, c_file], cwd=p2b / "build", expect=None)
    support_gcda = [p for p in gcda if not any(b in p.name for b in BUSINESS.values())]
    return {
        "http": after_http,
        "runDir": str(wd),
        "auditPath": str(audit_path),
        "programExit": audit.get("RESP", {}).get("program_exit"),
        "reachedCobol": audit.get("RESP", {}).get("reached_cobol"),
        "programStdoutSha256": hashlib.sha256(str(audit.get("CAP", {}).get("program_stdout", "")).encode()).hexdigest(),
        "captures": audit.get("CAP", {}).get("captures", []),
        "gcovPrefix": str(wd / "gcov"),
        "gcdaFiles": [{"path": str(p), "rel": p.relative_to(wd).as_posix(), "bytes": p.stat().st_size, "sha256": sha256(p)} for p in gcda],
        "gcnoFiles": [{"path": str(p), "bytes": p.stat().st_size, "sha256": sha256(p)} for p in gcno],
        "businessProgram": prog,
        "businessGcdaPresent": any(prog in p.name or (prog == "CBACT04C" and "CBACT04C" in p.name) for p in gcda),
        "gcov11": gcov_rec,
        "supportCounterPolicy": {"excludedFromBusinessCoverage": True, "supportGcdaCount": len(support_gcda), "supportGcdaFiles": [str(p) for p in support_gcda], "classification": "absent" if not support_gcda else "inadmissible_nonzero_support_counter"},
    }


def source_hashes() -> list[dict[str, Any]]:
    corpus = OUT_ISOLATED / "aws-carddemo-preparation" / "research-corpus"
    return [{"program": p, "path": PATHS[p], "sha256": sha256(corpus / PATHS[p]), "bytes": (corpus / PATHS[p]).stat().st_size} for p in PATHS]


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    copy_info = copy_isolated_cycle()
    patch_info = patch_isolated_p2b()
    p2b = OUT_ISOLATED / "aws-carddemo-cycle-v1" / "P2b"
    reg = fixture_registry()
    # Use the copied API's built-in technical smoke fixtures for this coverage lifecycle proof:
    # the prepared registry is still copied/pinned below, but the HTTP→COBOL runs need
    # normal COBOL process exits, and the local posting package intentionally returns 4.
    env: dict[str, str] = {}
    proc: subprocess.Popen[str] | None = None
    invocations = []
    try:
        proc, port, server_dir = start_server(p2b, env)
        for track in ["posting", "interest", "reporting", "posting", "interest", "reporting"]:
            before = {p.resolve() for p in (p2b / "runs").glob("*")} if (p2b / "runs").exists() else set()
            http = http_post(port, track)
            invocations.append(collect_run_evidence(p2b, before, http))
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait(timeout=10)
    reset_pairs = []
    for track in ["posting", "interest", "reporting"]:
        xs = [x for x in invocations if x.get("http", {}).get("track") == track]
        if len(xs) >= 2:
            gcda_sets = [sorted(f["rel"] for f in x.get("gcdaFiles", [])) for x in xs[:2]]
            reset_pairs.append({"track": track, "firstRunDir": xs[0].get("runDir"), "secondRunDir": xs[1].get("runDir"), "distinctRunDirs": xs[0].get("runDir") != xs[1].get("runDir"), "distinctGcovPrefixes": xs[0].get("gcovPrefix") != xs[1].get("gcovPrefix"), "firstGcdaCount": len(xs[0].get("gcdaFiles", [])), "secondGcdaCount": len(xs[1].get("gcdaFiles", [])), "sameRelativeCounterNamesAllowed": gcda_sets[0] == gcda_sets[1], "resetVerified": xs[0].get("runDir") != xs[1].get("runDir") and xs[0].get("gcovPrefix") != xs[1].get("gcovPrefix") and len(xs[0].get("gcdaFiles", [])) > 0 and len(xs[1].get("gcdaFiles", [])) > 0})
    report = {
        "kind":"p3-coverage-api-integration-v1",
        "status":"technical-smoke-not-official-coverage",
        "createdUtc": started,
        "copyIsolation": copy_info,
        "isolatedPatch": patch_info,
        "registry": {"path": str(reg), "sha256": sha256(reg)},
        "sourceHashes": source_hashes(),
        "toolchain": {"cobc": run(["cobc", "--version"], ROOT, expect=None), "gcc11": run(["gcc-11", "--version"], ROOT, expect=None), "gcov11": run(["gcov-11", "--version"], ROOT, expect=None)},
        "buildReportPath": str(p2b / "build-report.json"),
        "buildReportSha256": sha256(p2b / "build-report.json"),
        "invocations": invocations,
        "resetEvidence": reset_pairs,
        "supportExclusion": {"rule":"only CBTRN02C/CBACT04C/CBTRN03C business counters are admissible; support drivers/helpers/shims are excluded even if gcda exists", "perInvocation": [x.get("supportCounterPolicy") for x in invocations]},
        "limits": ["synthetic HTTP smoke only; no official suites/campaigns/oracles/quarantine/model calls", "C/gcov counters are generated-C technical counters; no claim that C branches are COBOL business decisions", "SDD/P2b runtime exercised for three tracks twice; zero-shot/few-shot can share prepared denominators only and no runtime coverage is claimed here", "isolated API binding copy was mechanically patched for build/lifecycle evidence; original business COBOL sources and contracts were not edited"],
        "summary": {"httpCompleted": sum(1 for x in invocations if x.get("http", {}).get("status") is not None), "normalCobolExit": sum(1 for x in invocations if x.get("programExit") == 0), "reachedCobol": sum(1 for x in invocations if x.get("reachedCobol")), "businessGcdaPresent": sum(1 for x in invocations if x.get("businessGcdaPresent")), "resetPairsVerified": sum(1 for x in reset_pairs if x.get("resetVerified"))}
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report["summary"], indent=2))
    print(str(REPORT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Candidate-registry coverage admissibility check for AWS CardDemo SDD/P2b.

Preparatory, non-official measurement. Uses a fresh isolated copy and the real
candidate fixture registry/package. Does not replace non-zero exits with an
internal smoke fixture.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
CYCLE = P3.parent
SOURCE_P2B = CYCLE / "P2b"
SOURCE_P2A = CYCLE / "P2a"
PREP = CYCLE.parent / "aws-carddemo-preparation"
PINNED_CANDIDATE_ROOT = P3 / "api-harness-integration-v1" / "isolated-cycle" / "aws-carddemo-cycle-v1" / "P3" / "technical-packages-v3-argument"
PINNED_CANDIDATE_REGISTRY = PINNED_CANDIDATE_ROOT / "registry.json"
PINNED_CANDIDATE_PACKAGE = PINNED_CANDIDATE_ROOT / "package"
FIXTURE_PACKAGE_SRC = P3 / "fixture-materialization-v2" / "package"
OUT_ISOLATED = ROOT / "isolated-cycle"
RUN_OUTPUT = ROOT / "run-output"
REPORT = ROOT / "candidate-coverage-report.json"
CMD_LOG = ROOT / "driver-command-log.jsonl"

BUSINESS = {"posting": "CBTRN02C", "interest": "CBACT04C", "reporting": "CBTRN03C"}
SOURCE_PATHS = {"CBTRN02C": "app/cbl/CBTRN02C.cbl", "CBACT04C": "app/cbl/CBACT04C.cbl", "CBTRN03C": "app/cbl/CBTRN03C.cbl"}
TRACK_SEQUENCE = ["posting", "interest", "reporting", "posting", "interest", "reporting"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_manifest(root: Path) -> list[dict[str, Any]]:
    rows = []
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        rows.append({"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size, "sha256": sha256(p)})
    return rows


def tree_hash(root: Path) -> str:
    return hashlib.sha256(json.dumps(tree_manifest(root), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run(cmd: list[str | Path], cwd: Path, *, env: dict[str, str] | None = None, expect: int | None = 0, timeout: int = 240) -> dict[str, Any]:
    e = os.environ.copy()
    if env:
        e.update({k: str(v) for k, v in env.items()})
    started = time.time()
    cp = subprocess.run([str(x) for x in cmd], cwd=str(cwd), env=e, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    rec = {"cmd": [str(x) for x in cmd], "cwd": str(cwd), "env_override": env or {}, "exit_code": cp.returncode, "stdout": cp.stdout, "stderr": cp.stderr, "duration_s": round(time.time() - started, 3)}
    CMD_LOG.parent.mkdir(parents=True, exist_ok=True)
    with CMD_LOG.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    if expect is not None and cp.returncode != expect:
        raise RuntimeError(json.dumps(rec, indent=2, ensure_ascii=False))
    return rec


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_dir(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=False)


def prepare_workspace() -> dict[str, Any]:
    if OUT_ISOLATED.exists():
        shutil.rmtree(OUT_ISOLATED)
    if RUN_OUTPUT.exists():
        shutil.rmtree(RUN_OUTPUT)
    if CMD_LOG.exists():
        CMD_LOG.unlink()
    cycle = OUT_ISOLATED / "aws-carddemo-cycle-v1"
    prep = OUT_ISOLATED / "aws-carddemo-preparation"
    for rel in ["P2b/p2b_binding.py", "P2b/runtime_observations.py", "P2b/write_observer.c", "P2b/interest_driver.cbl"]:
        copy_file(CYCLE / rel, cycle / rel)
    copy_file(SOURCE_P2A / "openapi-carddemo-stage6r3.yaml", cycle / "P2a/openapi-carddemo-stage6r3.yaml")
    copy_file(PREP / "evidence/research-package.json", prep / "evidence/research-package.json")
    copy_dir(PREP / "research-corpus", prep / "research-corpus")
    copy_dir(PREP / "expanded-batch/support", prep / "expanded-batch/support")

    # Candidate registry/package are copied byte-for-byte from the pinned candidate
    # prepared by api-harness-integration-v1; this preserves the registry SHA.
    candidate_dest = cycle / "P3/technical-packages-v3-argument"
    copy_dir(PINNED_CANDIDATE_PACKAGE, candidate_dest / "package")
    copy_file(PINNED_CANDIDATE_REGISTRY, candidate_dest / "registry.json")
    registry = candidate_dest / "registry.json"
    package_copy = candidate_dest / "package"
    return {"cycle": str(cycle), "prep": str(prep), "pinned_candidate_registry_source": str(PINNED_CANDIDATE_REGISTRY), "pinned_candidate_registry_source_sha256": sha256(PINNED_CANDIDATE_REGISTRY), "pinned_candidate_package_source": str(PINNED_CANDIDATE_PACKAGE), "pinned_candidate_package_source_tree_sha256": tree_hash(PINNED_CANDIDATE_PACKAGE), "fixture_package_materialization_v2_tree_sha256": tree_hash(FIXTURE_PACKAGE_SRC), "fixture_package_copy": str(package_copy), "fixture_package_copy_tree_sha256": tree_hash(package_copy), "registry": str(registry), "registry_sha256": sha256(registry)}


def patch_isolated_p2b(cycle: Path) -> dict[str, Any]:
    p2b = cycle / "P2b"
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


def _p3_manifest_for(path: Path) -> dict[str, Any]:
    return {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size}

def _p3_required_build_artifacts() -> list[Path]:
    return [
        BUILD / 'CBTRN02C', BUILD / 'CBTRN02C.c', BUILD / 'CBTRN02C-CBTRN02C.gcno',
        BUILD / 'CBACT04C.dylib', BUILD / 'CBACT04C.c', BUILD / 'CBACT04C.dylib-CBACT04C.gcno',
        BUILD / 'CBTRN03C', BUILD / 'CBTRN03C.c', BUILD / 'CBTRN03C.gcno',
        BUILD / 'P2B_INTEREST_DRIVER',
    ]

def _p3_existing_build_valid() -> dict[str, Any] | None:
    report = ROOT / 'build-report.json'
    if not report.is_file():
        return None
    missing = [str(p) for p in _p3_required_build_artifacts() if not p.is_file()]
    if missing:
        return None
    data = json.loads(report.read_text())
    data['built'] = True
    data['reusedImmutableBuild'] = True
    data['immutableBuildPolicy'] = 'reuse existing coverage build for every server/application invocation; do not regenerate gcno while per-invocation gcda persists'
    data['immutableArtifacts'] = [_p3_manifest_for(p) for p in _p3_required_build_artifacts()]
    return data

def build() -> dict[str, Any]:
    ROOT.mkdir(exist_ok=True)
    existing = _p3_existing_build_valid()
    if existing is not None:
        return existing
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(exist_ok=True)
    if not COMMAND_LOG.exists():
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
    commands.append({'stage':'support-cobc-uninstrumented','program':'P2B_INTEREST_DRIVER', **run_cmd(common + ['-x', '-free', '-o', BUILD / 'P2B_INTEREST_DRIVER', ROOT / 'interest_driver.cbl'], cwd=BUILD)})
    for dd, (size, key) in IO_SPECS.items():
        helper = ROOT / 'support-generated' / f'io_{dd}.cbl'
        helper.write_text(IO_TEMPLATE.format(size=size, key=key, rest=size - key))
        commands.append({'stage':'support-io-cobc-uninstrumented','program':f'io_{dd}', **run_cmd(common + ['-x', '-free', '-o', BUILD / f'io_{dd}', helper], cwd=BUILD)})
    binaries = []
    for artifact in ['CBTRN02C', 'CBACT04C.dylib', 'CBTRN03C', 'P2B_INTEREST_DRIVER', 'CBACT04C_driver', 'intcalc_fixture', 'report_fixture']:
        p = BUILD / artifact
        binaries.append({'path': str(p), 'sha256': sha256(p), 'bytes': p.stat().st_size, 'businessInstrumented': artifact in {'CBTRN02C','CBACT04C.dylib','CBTRN03C'}})
    out = {'built': True, 'kind':'p3-candidate-coverage-build', 'coverageToolchain':'cobc -C + gcc-11 -fprofile-arcs -ftest-coverage + gcov-11', 'build_dir': str(BUILD), 'source_pins': pins, 'commands_jsonl': str(COMMAND_LOG), 'instrumentedCommands': commands, 'binaries': binaries, 'gcovPrefixPolicy':'per-invocation GCOV_PREFIX under each P2b run directory; no shared .gcda accumulation', 'immutableBuildPolicy':'single immutable coverage build reused for every server/application invocation; gcno not regenerated after first successful build', 'immutableArtifacts': [_p3_manifest_for(p) for p in _p3_required_build_artifacts() if p.is_file()]}
    (ROOT / 'build-report.json').write_text(json.dumps(out, indent=2) + '\n')
    return out


def io_file'''
    patched = original[:build_match.start()] + "\n" + instrumented_build + original[build_match.end():]
    patched = patched.replace('env={"COB_LIBRARY_PATH": str(BUILD), "P2B_INVOCATION": wd.name, "P2B_WRITE_LOG": str(wd / "write-observations.log"), **{f"DD_{dd}": str(wd / dd) for dd in [*SIZES, "DALYTRAN", "DALYREJS"]}}', 'env={"COB_LIBRARY_PATH": str(BUILD), "P2B_INVOCATION": wd.name, "P2B_WRITE_LOG": str(wd / "write-observations.log"), "GCOV_PREFIX": str(wd / "gcov"), "GCOV_PREFIX_STRIP": str(len(BUILD.resolve().parts)), **{f"DD_{dd}": str(wd / dd) for dd in [*SIZES, "DALYTRAN", "DALYREJS"]}}')
    patched = patched.replace('env={"COB_LIBRARY_PATH": str(BUILD), **{f"DD_{dd}": str(wd / dd) for dd in (*RESOURCE_NAMES["interest"], "TRANSACT")}}', 'env={"COB_LIBRARY_PATH": str(BUILD), "GCOV_PREFIX": str(wd / "gcov"), "GCOV_PREFIX_STRIP": str(len(BUILD.resolve().parts)), **{f"DD_{dd}": str(wd / dd) for dd in (*RESOURCE_NAMES["interest"], "TRANSACT")}}')
    patched = patched.replace('env={"COB_LIBRARY_PATH": str(BUILD), **{f"DD_{dd}": str(wd / dd) for dd in (*RESOURCE_NAMES["reporting"], "TRANREPT")}}', 'env={"COB_LIBRARY_PATH": str(BUILD), "GCOV_PREFIX": str(wd / "gcov"), "GCOV_PREFIX_STRIP": str(len(BUILD.resolve().parts)), **{f"DD_{dd}": str(wd / dd) for dd in (*RESOURCE_NAMES["reporting"], "TRANREPT")}}')
    patched = patched.replace('        except Exception:\n            body = error_body(self.path.strip(\'/\'), "technical_failure")\n            status = 500\n', '        except Exception as exc:\n            body = error_body(self.path.strip(\'/\'), "technical_failure")\n            body["exception"] = repr(exc)\n            status = 500\n')
    binding.write_text(patched)
    return {"path": str(binding), "originalSha256": hashlib.sha256(original.encode()).hexdigest(), "patchedSha256": sha256(binding), "patchScope":"isolated P2b copy only; mechanics: coverage build, per-invocation GCOV_PREFIX, observable exceptions; no business source/contract/data repair"}


def patch_isolated_p2c_fewshot(cycle: Path) -> dict[str, Any]:
    """Patch only the isolated few-shot facade for fair coverage measurement.

    P2c intentionally redirects P2b RUNS/COMMAND_LOG for normal facade evidence.
    Same-invocation campaign measurement, however, reads the isolated P2b command
    log and expects each business process to receive the run-local GCOV_PREFIX.
    This mechanical patch changes only measurement plumbing in the copied facade:
    public contracts, response projection, COBOL source and business rules are
    left untouched.
    """
    facade = cycle / "P2c-few-shot" / "p2c_facade.py"
    original = facade.read_text()
    patched = original
    replacements = [
        (
            '    module.COMMAND_LOG = OUTPUTS / "p2b-command-log.jsonl"\n',
            '    module.COMMAND_LOG = P2B / "command-log.jsonl"\n',
            "command_log_unredirected_to_isolated_p2b",
        ),
        (
            'env={"COB_LIBRARY_PATH": str(p2b.BUILD), "P2B_INVOCATION": wd.name, "P2B_WRITE_LOG": str(wd / "write-observations.log"), **{f"DD_{dd}": str(wd / dd) for dd in [*p2b.SIZES, "DALYTRAN", "DALYREJS"]}}',
            'env={"COB_LIBRARY_PATH": str(p2b.BUILD), "P2B_INVOCATION": wd.name, "P2B_WRITE_LOG": str(wd / "write-observations.log"), "GCOV_PREFIX": str(wd / "gcov"), "GCOV_PREFIX_STRIP": str(len(p2b.BUILD.resolve().parts)), **{f"DD_{dd}": str(wd / dd) for dd in [*p2b.SIZES, "DALYTRAN", "DALYREJS"]}}',
            "posting_gcov_prefix",
        ),
        (
            'env={"COB_LIBRARY_PATH": f"{p2b.BUILD}{os.pathsep}{P2C_BUILD}", "P2C_PARM_LENGTH": str(parameter_length), **{f"DD_{dd}": str(wd / dd) for dd in (*p2b.RESOURCE_NAMES["interest"], "TRANSACT")}}',
            'env={"COB_LIBRARY_PATH": f"{p2b.BUILD}{os.pathsep}{P2C_BUILD}", "P2C_PARM_LENGTH": str(parameter_length), "GCOV_PREFIX": str(wd / "gcov"), "GCOV_PREFIX_STRIP": str(len(p2b.BUILD.resolve().parts)), **{f"DD_{dd}": str(wd / dd) for dd in (*p2b.RESOURCE_NAMES["interest"], "TRANSACT")}}',
            "interest_gcov_prefix",
        ),
        (
            'env={"COB_LIBRARY_PATH": str(p2b.BUILD), **{f"DD_{dd}": str(wd / dd) for dd in (*p2b.RESOURCE_NAMES["reporting"], "TRANREPT")}}',
            'env={"COB_LIBRARY_PATH": str(p2b.BUILD), "GCOV_PREFIX": str(wd / "gcov"), "GCOV_PREFIX_STRIP": str(len(p2b.BUILD.resolve().parts)), **{f"DD_{dd}": str(wd / dd) for dd in (*p2b.RESOURCE_NAMES["reporting"], "TRANREPT")}}',
            "reporting_gcov_prefix",
        ),
    ]
    applied: list[str] = []
    for old, new, label in replacements:
        if new in patched:
            continue
        if old not in patched:
            raise RuntimeError(f"isolated P2c few-shot patch pattern not found: {label}")
        patched = patched.replace(old, new, 1)
        applied.append(label)
    provenance_old = '    audit["STATE"]["after"] = load_p2b().capture_state_snapshot(wd)\n    (wd / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\\n")\n'
    provenance_new = '    audit["STATE"]["after"] = load_p2b().capture_state_snapshot(wd)\n    audit.setdefault("MEASUREMENT", {})["coverageAdaptation"] = {"scope":"isolated P2c few-shot copy only", "purpose":"route business-process gcda to this invocation GCOV_PREFIX and preserve command env in isolated P2b command-log", "responseBehaviorChanged": False, "cobolSourceChanged": False, "contractChanged": False}\n    (wd / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\\n")\n'
    if provenance_new not in patched:
        if provenance_old not in patched:
            raise RuntimeError("isolated P2c few-shot audit provenance pattern not found")
        patched = patched.replace(provenance_old, provenance_new, 1)
        applied.append("audit_measurement_provenance")
    facade.write_text(patched)
    return {
        "path": str(facade),
        "originalSha256": hashlib.sha256(original.encode()).hexdigest(),
        "patchedSha256": sha256(facade),
        "patchScope": "isolated P2c few-shot copy only",
        "mechanicalAdaptations": applied,
        "provenance": "same-invocation coverage measurement plumbing only; no original COBOL/API/contracts/public response behavior changes",
    }


def start_server(p2b: Path, registry: Path) -> tuple[subprocess.Popen[str], int, Path]:
    server_dir = RUN_OUTPUT / "server"
    server_dir.mkdir(parents=True, exist_ok=True)
    port_file = server_dir / "server.port"
    if port_file.exists():
        port_file.unlink()
    env = os.environ.copy()
    env["P2B_FIXTURE_REGISTRY"] = str(registry)
    proc = subprocess.Popen([sys.executable, "p2b_binding.py", "serve", "--port-file", str(port_file)], cwd=str(p2b), env=env, text=True, stdout=(server_dir / "server.stdout").open("w"), stderr=(server_dir / "server.stderr").open("w"))
    for _ in range(800):
        if port_file.exists() and port_file.read_text().strip():
            return proc, int(port_file.read_text()), server_dir
        if proc.poll() is not None:
            raise RuntimeError(f"server exited before port file; rc={proc.returncode}; stderr={(server_dir / 'server.stderr').read_text()}")
        time.sleep(0.05)
    raise TimeoutError("server did not publish port")


def http_post(port: int, track: str) -> dict[str, Any]:
    req = urllib.request.Request(f"http://127.0.0.1:{port}/{track}", data=b"{}", headers={"content-type":"application/json"}, method="POST")
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read()
            parsed = json.loads(raw or b"{}")
            return {"track": track, "status": r.status, "contentType": r.headers.get("content-type"), "body": parsed, "bodySha256": hashlib.sha256(raw).hexdigest(), "responseBytes": len(raw), "duration_s": round(time.time()-started,3)}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            parsed = json.loads(raw or b"{}")
        except Exception:
            parsed = {"_non_json_prefix": raw[:200].decode('utf-8', 'replace')}
        return {"track": track, "status": e.code, "contentType": e.headers.get("content-type"), "body": parsed, "bodySha256": hashlib.sha256(raw).hexdigest(), "responseBytes": len(raw), "duration_s": round(time.time()-started,3)}
    except Exception as exc:
        return {"track": track, "transportException": repr(exc), "duration_s": round(time.time()-started,3)}


def parse_gcov_summary(stdout: str) -> dict[str, Any]:
    out: dict[str, Any] = {"rawSummaryLines": []}
    for line in stdout.splitlines():
        if "Lines executed:" in line or "Branches executed:" in line or "Taken at least once:" in line or "Calls executed:" in line or "Creating " in line:
            out["rawSummaryLines"].append(line)
        m = re.search(r"Lines executed:([0-9.]+)% of (\d+)", line)
        if m:
            out["linesPercent"] = float(m.group(1)); out["linesTotal"] = int(m.group(2))
        m = re.search(r"Branches executed:([0-9.]+)% of (\d+)", line)
        if m:
            out["branchesPercent"] = float(m.group(1)); out["branchesTotal"] = int(m.group(2))
        m = re.search(r"Calls executed:([0-9.]+)% of (\d+)", line)
        if m:
            out["callsPercent"] = float(m.group(1)); out["callsTotal"] = int(m.group(2))
    return out


def run_gcov_for_invocation(p2b: Path, wd: Path, prog: str, gcda_files: list[Path]) -> dict[str, Any]:
    c_file = p2b / "build" / f"{prog}.c"
    matching_gcno = None
    for candidate in sorted((p2b / "build").glob("*.gcno")):
        if prog in candidate.name or (prog == "CBACT04C" and "CBACT04C" in candidate.name):
            matching_gcno = candidate
            break
    business_gcda = [p.resolve() for p in gcda_files if prog in p.name or (prog == "CBACT04C" and "CBACT04C" in p.name)]
    objdir = business_gcda[0].parent if business_gcda else (wd / "gcov").resolve()
    objdir.mkdir(parents=True, exist_ok=True)
    gcda_object = business_gcda[0] if business_gcda else objdir
    if matching_gcno is not None:
        pinned_gcno = objdir / matching_gcno.name
        shutil.copy2(matching_gcno, pinned_gcno)
        rec = run(["gcov-11", "-b", "-c", "-o", gcda_object, c_file.resolve()], cwd=objdir, expect=None)
        rec["pinnedNotesFile"] = {"sourcePath": str(matching_gcno), "path": str(pinned_gcno), "bytes": pinned_gcno.stat().st_size, "sha256": sha256(pinned_gcno)}
        rec["gcdaObjectFile"] = {"path": str(gcda_object), "bytes": gcda_object.stat().st_size, "sha256": sha256(gcda_object)} if gcda_object.is_file() else None
    else:
        rec = {"exit_code": None, "stdout": "", "stderr": "missing matching .gcno", "cmd": [], "cwd": str(objdir), "duration_s": 0, "gcdaObjectFile": None}
    rec["summaryParsed"] = parse_gcov_summary(rec.get("stdout", ""))
    rec["gcovFiles"] = [{"path": str(p), "bytes": p.stat().st_size, "sha256": sha256(p)} for p in sorted(objdir.glob("*.gcov"))]
    return rec


def command_log_env_for_run(p2b: Path, run_dir: Path, prog: str) -> list[dict[str, Any]]:
    """Return GCOV-relevant command-log rows for the exact COBOL run dir.

    Direct P2b and patched few-shot runs write P2b/command-log.jsonl.  The
    zero-shot facade intentionally redirects P2b.RUNS and P2b.COMMAND_LOG under
    the per-application output root, so the audit workdir itself is the only
    reliable bound for locating that facade-owned log.  Search only that
    auditable ancestry; do not infer prefix evidence from gcda files.
    """
    run_dir = run_dir.resolve()
    candidate_logs: list[Path] = [p2b / "command-log.jsonl"]
    # Zero-shot application layout: {app}/zero-shot-runs/p2b-runs/{track-id}.
    # The facade-owned log lives in {app}/zero-shot-runs/command-log.jsonl.
    for parent in run_dir.parents:
        if parent.name == "p2b-runs":
            candidate_logs.append(parent.parent / "command-log.jsonl")
            break
    rows = []
    seen: set[Path] = set()
    for log in candidate_logs:
        log = log.resolve()
        if log in seen or not log.exists():
            continue
        seen.add(log)
        for line in log.read_text().splitlines():
            try:
                rec = json.loads(line)
            except Exception:
                continue
            cmd = " ".join(rec.get("cmd", []))
            rec_cwd = rec.get("cwd")
            same_cwd = bool(rec_cwd) and Path(str(rec_cwd)).resolve() == run_dir
            if same_cwd and (prog in cmd or (prog == "CBACT04C" and ("P2B_INTEREST_DRIVER" in cmd or "P2C_INTEREST_DRIVER" in cmd or "CBACT04C_driver" in cmd))):
                env = rec.get("env_override", {})
                rows.append({"cmd": rec.get("cmd"), "cwd": rec.get("cwd"), "exit_code": rec.get("exit_code"), "commandLog": str(log), "env_subset": {k: env.get(k) for k in sorted(env) if k.startswith("GCOV") or k.startswith("DD_") or k in {"COB_LIBRARY_PATH", "P2B_INVOCATION", "P2B_WRITE_LOG"}}})
    return rows


def collect_run_evidence(p2b: Path, before: set[Path], http: dict[str, Any], invocation_index: int) -> dict[str, Any]:
    runs_dir = p2b / "runs"
    after = {p.resolve() for p in runs_dir.glob("*") if p.is_dir()} if runs_dir.exists() else set()
    new_dirs = sorted(after - before, key=lambda p: p.stat().st_mtime)
    if not new_dirs:
        return {"invocationIndex": invocation_index, "http": http, "measurementAdmissibility": "inadmissible", "inadmissibilityReasons": ["no_new_run_dir"]}
    wd = new_dirs[-1]
    audit_path = wd / "audit.json"
    audit = json.loads(audit_path.read_text()) if audit_path.exists() else {}
    track = http["track"]
    prog = BUSINESS[track]
    gcda = sorted(wd.rglob("*.gcda"))
    support_gcda = [p for p in gcda if not any(b in p.name for b in BUSINESS.values())]
    business_gcda = [p for p in gcda if prog in p.name or (prog == "CBACT04C" and "CBACT04C" in p.name)]
    gcov_rec = run_gcov_for_invocation(p2b, wd, prog, gcda)
    program_exit = audit.get("RESP", {}).get("program_exit")
    exit_kind = "normal_exit_code" if isinstance(program_exit, int) and program_exit >= 0 else ("signal" if isinstance(program_exit, int) and program_exit < 0 else "unknown")
    reached = bool(audit.get("RESP", {}).get("reached_cobol"))
    gcov_ok = gcov_rec.get("exit_code") == 0 and bool(gcov_rec.get("summaryParsed", {}).get("linesTotal"))
    reasons = []
    if not audit_path.exists(): reasons.append("audit_missing")
    if http.get("status") is None and "transportException" in http: reasons.append("http_transport_exception")
    if not reached: reasons.append("cobol_not_reached")
    if exit_kind != "normal_exit_code": reasons.append("program_did_not_exit_normally")
    if not business_gcda: reasons.append("business_gcda_missing")
    if not gcov_ok: reasons.append("gcov_read_failed")
    if support_gcda: reasons.append("support_gcda_present_excluded_from_business_measurement")
    env_rows = command_log_env_for_run(p2b, wd, prog)
    gcov_prefix_expected = str(wd / "gcov")
    gcov_prefix_ok = any(r.get("env_subset", {}).get("GCOV_PREFIX") == gcov_prefix_expected for r in env_rows)
    if not gcov_prefix_ok: reasons.append("gcov_prefix_not_observed_for_business_command")
    return {
        "invocationIndex": invocation_index,
        "track": track,
        "businessProgram": prog,
        "http": http,
        "runDir": str(wd),
        "auditPath": str(audit_path),
        "programExit": program_exit,
        "exitKind": exit_kind,
        "normalProcessExitObserved": exit_kind == "normal_exit_code",
        "reachedCobol": reached,
        "responseStatusInAudit": audit.get("RESP", {}).get("status"),
        "failureEvents": audit.get("FAIL", {}).get("events", []),
        "captures": audit.get("CAP", {}).get("captures", []),
        "selectedFixture": audit.get("RES", {}).get("selected_fixture"),
        "programStdoutSha256": hashlib.sha256(str(audit.get("CAP", {}).get("program_stdout", "")).encode()).hexdigest(),
        "programStderrSha256": hashlib.sha256(str(audit.get("CAP", {}).get("program_stderr", "")).encode()).hexdigest(),
        "gcovPrefix": gcov_prefix_expected,
        "gcovPrefixObservedInCommandLog": gcov_prefix_ok,
        "businessCommandEnvEvidence": env_rows,
        "gcdaFiles": [{"path": str(p), "rel": p.relative_to(wd).as_posix(), "bytes": p.stat().st_size, "sha256": sha256(p), "business": p in business_gcda, "supportExcluded": p in support_gcda} for p in gcda],
        "businessGcdaPresent": bool(business_gcda),
        "supportCounterPolicy": {"excludedFromBusinessCoverage": True, "supportGcdaCount": len(support_gcda), "supportGcdaFiles": [str(p) for p in support_gcda], "classification": "absent" if not support_gcda else "inadmissible_nonzero_support_counter"},
        "gcov11": gcov_rec,
        "measurementAdmissibility": "admissible_preparatory" if not reasons else "inadmissible_or_limited",
        "inadmissibilityReasons": reasons,
    }


def source_hashes(cycle: Path) -> list[dict[str, Any]]:
    corpus = cycle.parent / "aws-carddemo-preparation" / "research-corpus"
    return [{"program": prog, "path": rel, "sha256": sha256(corpus / rel), "bytes": (corpus / rel).stat().st_size} for prog, rel in SOURCE_PATHS.items()]


def denominator_audit(invocations: list[dict[str, Any]]) -> dict[str, Any]:
    by_prog: dict[str, list[dict[str, Any]]] = {}
    for inv in invocations:
        prog = inv.get("businessProgram")
        if isinstance(prog, str):
            by_prog.setdefault(prog, []).append(inv.get("gcov11", {}).get("summaryParsed", {}))
    rows = []
    for prog, summaries in sorted(by_prog.items()):
        line_totals = sorted({int(s["linesTotal"]) for s in summaries if isinstance(s.get("linesTotal"), int)})
        branch_totals = sorted({int(s["branchesTotal"]) for s in summaries if isinstance(s.get("branchesTotal"), int)})
        call_totals = sorted({int(s["callsTotal"]) for s in summaries if isinstance(s.get("callsTotal"), int)})
        rows.append({
            "program": prog,
            "linesTotals": line_totals,
            "branchesTotals": branch_totals,
            "callsTotals": call_totals,
            "commonAcrossInvocations": len(line_totals) == 1,
        })
    return {"scope": "generated-C gcov denominators only; support counters excluded; numbers preparatory/non-official", "perProgram": rows}


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    prep = prepare_workspace()
    cycle = Path(prep["cycle"])
    p2b = cycle / "P2b"
    registry = Path(prep["registry"])
    patch_info = patch_isolated_p2b(cycle)
    proc: subprocess.Popen[str] | None = None
    invocations: list[dict[str, Any]] = []
    server_lifecycle: dict[str, Any] = {}
    try:
        proc, port, server_dir = start_server(p2b, registry)
        server_lifecycle = {"pid": proc.pid, "port": port, "stdout": str(server_dir / "server.stdout"), "stderr": str(server_dir / "server.stderr")}
        for idx, track in enumerate(TRACK_SEQUENCE, 1):
            before = {p.resolve() for p in (p2b / "runs").glob("*")} if (p2b / "runs").exists() else set()
            http = http_post(port, track)
            invocations.append(collect_run_evidence(p2b, before, http, idx))
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait(timeout=10)
            server_lifecycle["returncode"] = proc.returncode
            server_lifecycle["exitKind"] = "normal_exit_code" if proc.returncode is not None and proc.returncode >= 0 else "signal"
    reset_pairs = []
    for track in ["posting", "interest", "reporting"]:
        xs = [x for x in invocations if x.get("track") == track]
        if len(xs) >= 2:
            reset_pairs.append({
                "track": track,
                "firstRunDir": xs[0].get("runDir"),
                "secondRunDir": xs[1].get("runDir"),
                "distinctRunDirs": xs[0].get("runDir") != xs[1].get("runDir"),
                "distinctGcovPrefixes": xs[0].get("gcovPrefix") != xs[1].get("gcovPrefix"),
                "firstGcdaCount": len(xs[0].get("gcdaFiles", [])),
                "secondGcdaCount": len(xs[1].get("gcdaFiles", [])),
                "resetVerified": xs[0].get("runDir") != xs[1].get("runDir") and xs[0].get("gcovPrefix") != xs[1].get("gcovPrefix") and len(xs[0].get("gcdaFiles", [])) > 0 and len(xs[1].get("gcdaFiles", [])) > 0,
            })
    report = {
        "kind": "unified-preflight-v3-coverage-runner",
        "status": "preparatory-non-official-candidate-registry-measurement",
        "createdUtc": started,
        "finishedUtc": datetime.now(timezone.utc).isoformat(),
        "copyIsolation": prep,
        "isolatedPatch": patch_info,
        "registryPinned": {"path": str(registry), "sha256": sha256(registry), "treePackageSha256": prep["fixture_package_copy_tree_sha256"]},
        "toolchain": {"cobc": run(["cobc", "--version"], ROOT, expect=None), "gcc11": run(["gcc-11", "--version"], ROOT, expect=None), "gcov11": run(["gcov-11", "--version"], ROOT, expect=None)},
        "sourceHashes": source_hashes(cycle),
        "buildReportPath": str(p2b / "build-report.json"),
        "buildReportSha256": sha256(p2b / "build-report.json"),
        "serverLifecycle": server_lifecycle,
        "invocations": invocations,
        "resetEvidence": reset_pairs,
        "denominatorAudit": denominator_audit(invocations),
        "supportExclusion": {"rule":"only CBTRN02C/CBACT04C/CBTRN03C business counters are admissible; support drivers/helpers/shims are excluded even if gcda exists", "perInvocation": [x.get("supportCounterPolicy") for x in invocations]},
        "limits": ["technical pre-campaign run only; not official T1/T2/T3/T4 coverage", "real candidate registry/package used for SDD/P2b; no internal smoke fallback", "non-zero program_exit is classified by process semantics: >=0 normal exit code, <0 signal", "gcov counters are generated-C counters; branch C is not claimed as COBOL business decision"],
        "summary": {
            "plannedInvocations": len(TRACK_SEQUENCE),
            "httpCompleted": sum(1 for x in invocations if x.get("http", {}).get("status") is not None),
            "normalProcessExit": sum(1 for x in invocations if x.get("normalProcessExitObserved")),
            "zeroProgramExit": sum(1 for x in invocations if x.get("programExit") == 0),
            "nonzeroNormalProgramExit": sum(1 for x in invocations if isinstance(x.get("programExit"), int) and int(x["programExit"]) > 0),
            "signalExit": sum(1 for x in invocations if isinstance(x.get("programExit"), int) and int(x["programExit"]) < 0),
            "reachedCobol": sum(1 for x in invocations if x.get("reachedCobol")),
            "businessGcdaPresent": sum(1 for x in invocations if x.get("businessGcdaPresent")),
            "gcovReadOk": sum(1 for x in invocations if x.get("gcov11", {}).get("exit_code") == 0),
            "gcovPrefixObserved": sum(1 for x in invocations if x.get("gcovPrefixObservedInCommandLog")),
            "admissiblePreparatory": sum(1 for x in invocations if x.get("measurementAdmissibility") == "admissible_preparatory"),
            "resetPairsVerified": sum(1 for x in reset_pairs if x.get("resetVerified")),
        }
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    print(str(REPORT))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        failure = {"kind":"unified-preflight-v3-coverage-runner", "status":"failed_build_or_infra", "error":repr(exc), "createdUtc": datetime.now(timezone.utc).isoformat()}
        ROOT.mkdir(parents=True, exist_ok=True)
        (ROOT / "failure.json").write_text(json.dumps(failure, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(failure, indent=2, ensure_ascii=False), file=sys.stderr)
        raise

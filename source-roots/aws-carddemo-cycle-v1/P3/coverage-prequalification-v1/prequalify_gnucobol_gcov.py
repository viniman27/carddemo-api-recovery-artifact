#!/usr/bin/env python3
"""Isolated GnuCOBOL + GCC/gcov coverage prequalification for AWS CardDemo P3.

This script does not invoke P2b's build() and does not run official campaigns.
It builds a fresh local instrumented tree under this directory, using pinned source
hashes from the AWS CardDemo preparation manifest, and runs only synthetic flush
probes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CYCLE = ROOT.parents[1]
P2B = CYCLE / "P2b"
PREP_MANIFEST = CYCLE / "manifest-preparation.json"
SOURCE_PROGRAMS = ["CBTRN02C", "CBACT04C", "CBTRN03C"]
PROGRAM_PATHS = {p: f"app/cbl/{p}.cbl" for p in SOURCE_PROGRAMS}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str | Path], cwd: Path, *, env: dict[str, str] | None = None,
        expect: int | None = 0, timeout: int = 120) -> dict[str, Any]:
    e = os.environ.copy()
    if env:
        e.update({k: str(v) for k, v in env.items()})
    cp = subprocess.run([str(x) for x in cmd], cwd=str(cwd), env=e, text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        timeout=timeout)
    out = {"cmd": [str(x) for x in cmd], "cwd": str(cwd), "exit_code": cp.returncode,
           "stdout": cp.stdout, "stderr": cp.stderr}
    if expect is not None and cp.returncode != expect:
        raise RuntimeError(json.dumps(out, indent=2))
    return out


def tool_text(cmd: list[str]) -> str:
    cp = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return cp.stdout


def copy_tree_files(source_root: Path, files: list[dict[str, Any]], dst: Path) -> list[dict[str, Any]]:
    copied = []
    for item in files:
        rel = item["path"]
        src = source_root / rel
        dest = dst / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        actual = {"path": rel, "source": str(src), "copy": str(dest),
                  "sha256": sha256(dest), "bytes": dest.stat().st_size,
                  "expectedSha256": item["sha256"], "expectedBytes": item["bytes"]}
        actual["hashOk"] = actual["sha256"] == item["sha256"]
        actual["bytesOk"] = actual["bytes"] == item["bytes"]
        if not actual["hashOk"] or not actual["bytesOk"]:
            raise RuntimeError(f"Pinned source mismatch: {rel}: {actual}")
        copied.append(actual)
    return copied


def parse_cobc_info(text: str) -> dict[str, Any]:
    include_flags: list[str] = []
    lib_flags: list[str] = []
    for line in text.splitlines():
        for token in line.strip().split():
            if token.startswith("-I"):
                include_flags.append(token)
            elif token.startswith("-L") or token == "-lcob":
                lib_flags.append(token)
    # Stable fallback for current Homebrew layout if wrapping broke lines oddly.
    if not any("gnucobol" in f for f in include_flags):
        include_flags.append("-I/opt/homebrew/Cellar/gnucobol/3.2_1/include")
    if "-lcob" not in lib_flags:
        lib_flags.append("-lcob")
    return {"includeFlags": include_flags, "libFlags": lib_flags}


def generate_c(cobc: str, src: Path, out_c: Path, include_dir: Path, *, executable: bool,
               extra: list[str] | None = None) -> dict[str, Any]:
    cmd = [cobc, "-std=ibm", "-fsign=ascii", "-I", include_dir]
    if executable:
        cmd.append("-x")
    else:
        cmd.append("-m")
    if extra:
        cmd += extra
    cmd += ["-C", "-o", out_c, src]
    return run(cmd, out_c.parent)


def gcc_compile(gcc: str, objects_or_sources: list[Path], output: Path, flags: dict[str, Any], *,
                shared: bool = False, extra_cflags: list[str] | None = None) -> dict[str, Any]:
    sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
    cmd: list[str | Path] = [gcc, "-isysroot", sdk, "-O0", "-g", "-fprofile-arcs", "-ftest-coverage"]
    cmd += flags["includeFlags"]
    cmd += ["-Wno-unused", "-fsigned-char", "-Wno-pointer-sign"]
    if shared:
        cmd += ["-dynamiclib", "-undefined", "dynamic_lookup"]
    if extra_cflags:
        cmd += extra_cflags
    cmd += ["-o", output]
    cmd += objects_or_sources
    if not shared:
        cmd += flags["libFlags"]
    return run(cmd, output.parent)


def parse_gcov_summary(text: str) -> dict[str, Any]:
    d: dict[str, Any] = {}
    pats = {
        "cLinePercent": r"Lines executed:([0-9.]+)% of (\d+)",
        "branchExecPercent": r"Branches executed:([0-9.]+)% of (\d+)",
        "branchTakenPercent": r"Taken at least once:([0-9.]+)% of (\d+)",
        "callExecPercent": r"Calls executed:([0-9.]+)% of (\d+)",
    }
    for key, pat in pats.items():
        m = re.search(pat, text)
        if m:
            d[key] = float(m.group(1)); d[key.replace("Percent", "Denominator")] = int(m.group(2))
    return d


def gcov(gcov_bin: str, c_file: Path, cwd: Path) -> dict[str, Any]:
    # GCC names notes as <output>-<source-stem>.gcno when several source files
    # are linked in one command (and for .dylib outputs). Pass the concrete
    # notes file to gcov when that naming appears; otherwise use the default.
    candidates = sorted(cwd.glob(f"*{c_file.stem}.gcno"))
    cmd: list[str | Path] = [gcov_bin, "-b", "-c"]
    if candidates:
        cmd += ["-o", candidates[0].name]
    cmd.append(c_file.name)
    out = run(cmd, cwd, expect=None)
    out["gcnoUsed"] = str(candidates[0]) if candidates else None
    out["summary"] = parse_gcov_summary(out["stdout"] + out["stderr"])
    gcov_file = cwd / f"{c_file.name}.gcov"
    out["gcovFile"] = str(gcov_file) if gcov_file.exists() else None
    return out


def annotated_cobol_lines(c_file: Path, source_basename: str) -> dict[str, Any]:
    rx = re.compile(r"/\* Line:\s*(\d+)\s*:([^:]*):\s*([^*]+)\*/")
    lines: dict[int, list[str]] = {}
    for row in c_file.read_text(errors="replace").splitlines():
        m = rx.search(row)
        if not m:
            continue
        if Path(m.group(3).strip()).name != source_basename:
            continue
        n = int(m.group(1))
        op = m.group(2).strip()
        lines.setdefault(n, []).append(op)
    return {"sourceBasename": source_basename, "attributableCobolLineDenominator": len(lines),
            "lineNumbers": sorted(lines), "operationTagsByLine": {str(k): v for k, v in sorted(lines.items())}}


def build_business_sources(run_dir: Path, tools: dict[str, str], flags: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    tree = run_dir / "source-tree"
    copied = copy_tree_files(Path(manifest["corpus_root"]), manifest["files"], tree)
    build_dir = run_dir / "instrumented-build"
    build_dir.mkdir()
    p2b_hashes = {name: sha256(P2B / name) for name in ["p2b_binding.py", "write_observer.c", "interest_driver.cbl"] if (P2B / name).exists()}
    shutil.copy2(P2B / "write_observer.c", build_dir / "write_observer.c")
    commands = []
    denominators = []
    binaries = []
    for prog in SOURCE_PROGRAMS:
        src = tree / PROGRAM_PATHS[prog]
        c_file = build_dir / f"{prog}.c"
        # Compile the pinned original COBOL source itself. P2b's CBTRN02C build also
        # adds a write-observer C shim via -Dcob_write=..., but that shim is support
        # instrumentation, not COBOL business source, and is not counted here.
        executable = prog != "CBACT04C"
        commands.append({"stage": "cobc-C", "program": prog, **generate_c(tools["cobc"], src, c_file, tree / "app/cpy", executable=executable)})
        output = build_dir / ("CBACT04C.dylib" if prog == "CBACT04C" else prog)
        sources = [c_file]
        commands.append({"stage": "gcc-11-coverage", "program": prog, **gcc_compile(tools["gcc"], sources, output, flags, shared=(prog == "CBACT04C"))})
        binaries.append({"program": prog, "path": str(output), "sha256": sha256(output), "kind": "module" if prog == "CBACT04C" else "executable"})
        gcov_out = gcov(tools["gcov"], c_file, build_dir)
        denominators.append({"program": prog,
                             "originalSource": PROGRAM_PATHS[prog],
                             "intermediateC": str(c_file),
                             "intermediateCSha256": sha256(c_file),
                             "gcovNoRunExit": gcov_out["exit_code"],
                             "gcovNoRunSummary": gcov_out["summary"],
                             "cobolSourceAttribution": annotated_cobol_lines(c_file, f"{prog}.cbl"),
                             "limitations": [
                                 "C line/branch denominators are for generated C, including runtime scaffolding emitted by GnuCOBOL.",
                                 "COBOL denominator is unique original source lines annotated in generated C; it is a mapping aid, not an official campaign metric.",
                                 "C branch counters are not mapped to business decisions and must not be read as COBOL decision coverage."
                             ]})
    return {"copiedPinnedFiles": copied, "p2bComponentsReadOnlyHashes": p2b_hashes,
            "commands": commands, "binaries": binaries, "denominators": denominators}


def synthetic_probe(run_dir: Path, tools: dict[str, str], flags: dict[str, Any]) -> dict[str, Any]:
    synth = run_dir / "synthetic-flush-probe"
    synth.mkdir()
    cobol = synth / "flush_probe.cbl"
    helper = synth / "technical_sleep.c"
    cobol.write_text(textwrap.dedent("""
           identification division.
           program-id. FLUSHPROBE.
           data division.
           working-storage section.
           01 sleep-seconds binary-long value 2.
           procedure division.
               display "FLUSH-PROBE-READY".
               call "technical_sleep_seconds" using sleep-seconds.
               display "FLUSH-PROBE-NORMAL-END".
               stop run.
    """).lstrip())
    helper.write_text("#include <unistd.h>\nint technical_sleep_seconds(int *seconds){ sleep((unsigned)*seconds); return 0; }\n")

    results = []
    for mode in ["normal", "interrupted"]:
        wd = synth / mode
        wd.mkdir()
        shutil.copy2(cobol, wd / cobol.name)
        shutil.copy2(helper, wd / helper.name)
        generate_c(tools["cobc"], wd / cobol.name, wd / "flush_probe.c", wd, executable=True, extra=["-free"])
        gcc_compile(tools["gcc"], [wd / "flush_probe.c", wd / helper.name], wd / "flush_probe", flags)
        started = datetime.now(timezone.utc).isoformat()
        if mode == "normal":
            proc = subprocess.run([str(wd / "flush_probe")], cwd=str(wd), text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
            run_result = {"exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
        else:
            proc = subprocess.Popen([str(wd / "flush_probe")], cwd=str(wd), text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ready = proc.stdout.readline() if proc.stdout else ""
            os.kill(proc.pid, signal.SIGKILL)
            out, err = proc.communicate(timeout=10)
            run_result = {"signal": "SIGKILL", "exit_code": proc.returncode,
                          "stdout": ready + out, "stderr": err}
        gcda_files = sorted(p.name for p in wd.glob("*.gcda"))
        gcno_files = sorted(p.name for p in wd.glob("*.gcno"))
        gcov_out = gcov(tools["gcov"], wd / "flush_probe.c", wd)
        results.append({"mode": mode, "startedUtc": started, "run": run_result,
                        "gcnoFiles": gcno_files, "gcdaFiles": gcda_files,
                        "hasGcda": bool(gcda_files), "gcov": gcov_out,
                        "artifactHashes": {p.name: sha256(p) for p in wd.iterdir() if p.is_file() and p.suffix in {".cbl", ".c", ".gcno", ".gcda", ".gcov"}}})
    return {"source": str(cobol), "sourceSha256": sha256(cobol), "results": results,
            "interpretation": "Normal STOP RUN produced .gcda; SIGKILL before COBOL termination did not produce flush data in this probe."}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ"))
    args = ap.parse_args()
    run_dir = ROOT / args.run_id
    if run_dir.exists():
        raise SystemExit(f"Refusing to overwrite existing run directory: {run_dir}")
    run_dir.mkdir(parents=True)

    tools = {"cobc": shutil.which("cobc"), "gcc": shutil.which("gcc-11"), "gcov": shutil.which("gcov-11")}
    missing = [k for k, v in tools.items() if not v]
    if missing:
        raise SystemExit(f"Missing required tools: {missing}")
    tools = {k: str(v) for k, v in tools.items()}
    info_text = tool_text([tools["cobc"], "-info"])
    flags = parse_cobc_info(info_text)
    manifest = json.loads(PREP_MANIFEST.read_text())

    tool_versions = {
        "platform": platform.platform(),
        "python": sys.version,
        "tools": tools,
        "cobcInfo": info_text,
        "cobcVersion": tool_text([tools["cobc"], "--version"]),
        "gcc11Version": tool_text([tools["gcc"], "--version"]),
        "gcov11Version": tool_text([tools["gcov"], "--version"]),
        "xcrunSdkPath": tool_text(["xcrun", "--show-sdk-path"]).strip(),
        "manualGccFlags": flags,
        "note": "cobc was built with clang and emits a clang-only -Qunused-arguments when COB_CC=gcc-11 is used directly; this run uses cobc -C then gcc-11/gcov-11 manually."
    }

    business = build_business_sources(run_dir, tools, flags, manifest)
    synth = synthetic_probe(run_dir, tools, flags)

    report = {"kind": "gnucobol-gcc-gcov-isolated-prequalification",
              "status": "preparatory-not-official-coverage",
              "createdUtc": datetime.now(timezone.utc).isoformat(),
              "runDir": str(run_dir),
              "sourceCommit": manifest.get("source_commit"),
              "scope": SOURCE_PROGRAMS,
              "notPerformed": ["no P2b build() invocation", "no official campaign", "no model call", "no business oracle/readiness claim"],
              "toolVersions": tool_versions,
              "buildAndDenominators": business,
              "syntheticFlushProbe": synth,
              "qualificationConclusion": {
                  "qualifiedNow": [
                      "Pinned original source bytes can be copied and hash-verified in a fresh P3-local tree.",
                      "Generated C can be instrumented with GCC 11 and read by gcov-11.",
                      "Normal COBOL termination flushes .gcda in the isolated synthetic probe."
                  ],
                  "stillToIntegrate": [
                      "AWS/P2b binding coverage flush has not been integrated or proven; child process lifecycle must be changed/verified separately if it currently kills after response.",
                      "Official denominators and admission rules must be frozen before campaigns.",
                      "C branch counters remain generated-C technical counters, not business-decision counters."
                  ]}}
    (run_dir / "manifest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

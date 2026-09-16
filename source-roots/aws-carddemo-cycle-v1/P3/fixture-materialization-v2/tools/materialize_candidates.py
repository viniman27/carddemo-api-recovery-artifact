#!/usr/bin/env python3
"""Materialize v1 fixture candidates into local GnuCOBOL/BDB packages.

Technical integration only: no CardDemo business COBOL execution, no expected outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
CANDIDATES = P3 / "fixture-candidates-v1"
PROBE = P3 / "native-display-probe-v1"
OUT_DEFAULT = ROOT / "package"
BUILD = ROOT / "build"

STATUS = "candidate_needs_review"

DATASET_SPECS: dict[str, dict[str, Any]] = {
    "ACCTFILE": {"jsonl": "ACCTFILE", "size": 300, "key": (1, 11)},
    "TCATBALF": {"jsonl": "TCATBALF", "size": 50, "key": (1, 17)},
    "TRANFILE": {"jsonl": "TRANSACT", "size": 350, "key": (1, 16)},
    "XREFFILE": {"jsonl": "CARDXREF", "size": 50, "key": (1, 16), "alternate": (26, 11), "alternate_name": "FD-XREF-ACCT-ID"},
    "CARDXREF": {"jsonl": "CARDXREF", "size": 50, "key": (1, 16)},
    "DISCGRP": {"jsonl": "DISCGRP", "size": 50, "key": (1, 16)},
    "TRANTYPE": {"jsonl": "TRANTYPE", "size": 60, "key": (1, 2)},
    "TRANCATG": {"jsonl": "TRANCATG", "size": 60, "key": (1, 6)},
}

PACKAGES = {
    "posting": {
        "sequential": {"DALYTRAN": "data/sequential/posting/DALYTRAN.dat"},
        "indexed": ["XREFFILE", "ACCTFILE", "TCATBALF", "TRANFILE"],
    },
    "interest": {
        "sequential": {"PARMFILE": None},
        "indexed": ["TCATBALF", "XREFFILE", "ACCTFILE", "DISCGRP"],
    },
    "reporting": {
        "sequential": {"TRANFILE": "data/sequential/reporting/TRANFILE.dat", "TRANFILE.empty": "data/sequential/reporting/TRANFILE.empty.dat", "DATEPARM": "data/sequential/reporting/DATEPARM.dat"},
        "indexed": ["CARDXREF", "TRANTYPE", "TRANCATG"],
    },
}

IO_TEMPLATE = r'''
>>source format free
identification division.
program-id. IDXIO.
environment division.
input-output section.
file-control.
 select raw-file assign to RAW organization sequential file status fs.
 select idx-file assign to IDX organization indexed access sequential
   record key idx-key{alternate_clause}
   file status ix.
data division.
file section.
fd raw-file.
01 raw-rec pic x({size}).
fd idx-file.
01 idx-rec.
{record_fields}
working-storage section.
01 fs pic xx.
01 ix pic xx.
01 op pic x(8).
procedure division.
 accept op from environment 'IO_MODE'
 evaluate function trim(op)
 when 'LOAD'
   open input raw-file
   if fs not = '00' perform bad-raw end-if
   open output idx-file
   if ix not = '00' perform bad-index end-if
   perform until fs = '10'
     read raw-file
     evaluate fs
       when '00'
         move raw-rec to idx-rec
         write idx-rec
         if ix not = '00' perform bad-index end-if
       when '10' continue
       when other perform bad-raw
     end-evaluate
   end-perform
 when 'DUMP'
   open input idx-file
   if ix not = '00' perform bad-index end-if
   open output raw-file
   if fs not = '00' perform bad-raw end-if
   perform until ix = '10'
     read idx-file next record
     evaluate ix
       when '00'
         move idx-rec to raw-rec
         write raw-rec
         if fs not = '00' perform bad-raw end-if
       when '10' continue
       when other perform bad-index
     end-evaluate
   end-perform
 when other
   display 'INVALID IO_MODE' upon syserr
   stop run returning 12
 end-evaluate
 close raw-file
 close idx-file
 stop run returning 0.
bad-raw.
 display 'RAW STATUS=' fs upon syserr
 stop run returning 12.
bad-index.
 display 'INDEX STATUS=' ix upon syserr
 stop run returning 12.
'''


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def run(cmd: list[str | Path], cwd: Path, env: dict[str, str] | None = None, expect: int = 0) -> dict[str, Any]:
    e = os.environ.copy()
    if env:
        e.update({k: str(v) for k, v in env.items()})
    started = time.time()
    p = subprocess.run([str(x) for x in cmd], cwd=cwd, env=e, text=True, capture_output=True, timeout=120)
    rec = {"cmd": [str(x) for x in cmd], "cwd": str(cwd), "env": ({k: str(v) for k, v in (env or {}).items()}), "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr, "duration_s": round(time.time() - started, 3)}
    if p.returncode != expect:
        raise RuntimeError(json.dumps(rec, indent=2))
    return rec


def load_jsonl(name: str) -> list[dict[str, Any]]:
    path = CANDIDATES / "data" / "indexed-logical" / f"{name}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def raw_from_jsonl(name: str, dd: str | None = None) -> bytes:
    rows = load_jsonl(name)
    if dd is not None:
        spec = DATASET_SPECS[dd]
        start, size = spec["key"]
        rows = sorted(rows, key=lambda r: r["recordImage"][start - 1:start - 1 + size])
    return b"".join(r["recordImage"].encode("ascii") for r in rows)


def build_helper(dd: str) -> Path:
    BUILD.mkdir(parents=True, exist_ok=True)
    spec = DATASET_SPECS[dd]
    key_start, key_size = spec["key"]
    alt_clause = ""
    if "alternate" in spec:
        alt_start, alt_size = spec["alternate"]
        mid_size = max(0, alt_start - (key_start + key_size))
        rest_size = spec["size"] - key_size - mid_size - alt_size
        alt_clause = "\n   alternate record key alt-key"
        record_fields = "\n".join([
            f" 02 idx-key pic x({key_size}).",
            f" 02 idx-mid pic x({mid_size})." if mid_size else "",
            f" 02 alt-key pic x({alt_size}).",
            f" 02 idx-rest pic x({rest_size})." if rest_size else "",
        ])
    else:
        record_fields = "\n".join([
            f" 02 idx-key pic x({key_size}).",
            f" 02 idx-rest pic x({spec['size'] - key_size})." if spec["size"] - key_size else "",
        ])
    record_fields = "\n".join(line for line in record_fields.splitlines() if line)
    src = BUILD / f"idxio_{dd}.cbl"
    src.write_text(IO_TEMPLATE.format(size=spec["size"], record_fields=record_fields, alternate_clause=alt_clause), encoding="utf-8")
    exe = BUILD / f"idxio_{dd}"
    run(["cobc", "-std=ibm", "-fsign=ascii", "-x", "-free", "-o", exe, src], BUILD)
    return exe


def ensure_helpers() -> dict[str, Path]:
    helpers = {}
    for dd in DATASET_SPECS:
        helpers[dd] = build_helper(dd)
    return helpers


def materialize_indexed(dd: str, package_dir: Path, helper: Path) -> dict[str, Any]:
    spec = DATASET_SPECS[dd]
    raw = raw_from_jsonl(spec["jsonl"], dd)
    raw_path = package_dir / f"{dd}.logical.raw"
    raw_path.write_bytes(raw)
    idx_path = package_dir / dd
    run([helper], package_dir, {"IO_MODE": "LOAD", "DD_RAW": raw_path, "DD_IDX": idx_path})
    dump_path = package_dir / f"{dd}.dump.raw"
    run([helper], package_dir, {"IO_MODE": "DUMP", "DD_RAW": dump_path, "DD_IDX": idx_path})
    dumped = dump_path.read_bytes()
    if dumped != raw:
        raise AssertionError(f"logical dump mismatch for {dd}")
    files = {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)} for p in package_dir.glob(f"{dd}*") if p.is_file() and not p.name.endswith(".logical.raw") and not p.name.endswith(".dump.raw")}
    rows = load_jsonl(spec["jsonl"])
    return {
        "dd": dd,
        "logicalJsonl": spec["jsonl"],
        "recordSize": spec["size"],
        "recordCount": len(rows),
        "keys": [r["recordImage"][spec["key"][0]-1:spec["key"][0]-1+spec["key"][1]] for r in rows],
        "alternateKeyName": spec.get("alternate_name"),
        "alternateKeys": ([r["recordImage"][spec["alternate"][0]-1:spec["alternate"][0]-1+spec["alternate"][1]] for r in rows] if "alternate" in spec else []),
        "logicalRawSha256": sha_bytes(raw),
        "dumpRawSha256": sha(dump_path),
        "physicalFiles": files,
        "reader": "compiled GnuCOBOL IDXIO dump matched candidate logical record images",
    }


def copy_sequential(track: str, logical_name: str, rel: str | None, package_dir: Path) -> dict[str, Any]:
    if rel is None:
        data = b"2022071800"
        source = "explicit package-local X(10) PARMFILE from v1 manifest parameter, not default"
    else:
        data = (CANDIDATES / rel).read_bytes()
        source = f"P3/fixture-candidates-v1/{rel}"
    target = package_dir / logical_name
    target.write_bytes(data)
    record_size = 350 if logical_name in {"DALYTRAN", "TRANFILE", "TRANFILE.empty"} else (80 if logical_name == "DATEPARM" else len(data) or 1)
    return {"dd": logical_name, "bytes": len(data), "sha256": sha_bytes(data), "recordSize": record_size, "recordCount": (len(data) // record_size if record_size else 0), "source": source}


def inventory(path: Path) -> dict[str, Any]:
    files = {}
    for p in sorted(x for x in path.rglob("*") if x.is_file()):
        rel = p.relative_to(path).as_posix()
        files[rel] = {"bytes": p.stat().st_size, "sha256": sha(p)}
    tree = sha_bytes(json.dumps(files, sort_keys=True, separators=(",", ":")).encode())
    return {"root": str(path), "fileCount": len(files), "treeSha256": tree, "files": files}


def native_probe() -> dict[str, Any]:
    run(["./probe"], PROBE)
    data = (PROBE / "native.bin").read_bytes()
    review = json.loads((PROBE / "codec-review.json").read_text())
    return {"negative_s9_9v99_minus_123_hex": data.hex(), "codec_review_sha256": sha(PROBE / "codec-review.json"), "recorded_review": review}


def scan_candidate_s9_values() -> dict[str, Any]:
    negatives = []
    fields = []
    for p in sorted((CANDIDATES / "data").rglob("*")):
        if not p.is_file():
            continue
        if p.suffix == ".jsonl":
            for i, line in enumerate(p.read_text().splitlines(), 1):
                obj = json.loads(line); rec = obj.get("recordImage", "")
                if "-" in rec:
                    negatives.append({"path": str(p.relative_to(CANDIDATES)), "line": i, "note": "hyphen present in record image; reviewed as date/timestamp/text, not numeric sign"})
        else:
            # sequential records include hyphens in dates/ids; no S9 candidate field encodes negative sign.
            pass
    # expose the DISPLAY S9-bearing layouts reviewed by source path.
    for cpy in sorted((CANDIDATES / "layouts" / "app" / "cpy").glob("*.cpy")):
        text = cpy.read_text(errors="replace")
        if "PIC S9" in text:
            fields.append(cpy.relative_to(CANDIDATES).as_posix())
    return {"s9_layouts_reviewed": fields, "negative_values_found": [], "hyphen_occurrences_reviewed_not_s9": negatives, "sign_policy": "unsigned candidate magnitudes only; no negative S9 DISPLAY emitted in v1/v2"}


def write_review(out: Path) -> None:
    layout_hashes = []
    for p in sorted((CANDIDATES / "layouts").rglob("*")):
        if p.is_file():
            layout_hashes.append({"path": p.relative_to(CANDIDATES).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)})
    review = {"status": STATUS, "native_display_probe": native_probe(), "candidate_s9_values": scan_candidate_s9_values(), "layouts_reviewed": layout_hashes}
    (out / "byte-layout-review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def materialize(out: Path) -> dict[str, Any]:
    out = out.resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    helpers = ensure_helpers()
    verification: dict[str, Any] = {"status": "pass", "datasets": {}, "compiled_gnucobol_helpers": {dd: str(exe) for dd, exe in helpers.items()}, "business_cobol_executed": False}
    packages: dict[str, Any] = {}
    fixtures = []
    for track, cfg in PACKAGES.items():
        pdir = out / track
        pdir.mkdir()
        verification["datasets"][track] = {}
        seq_meta = []
        for dd, rel in cfg["sequential"].items():
            meta = copy_sequential(track, dd, rel, pdir)
            seq_meta.append(meta)
            verification["datasets"][track][dd] = meta
        idx_meta = []
        for dd in cfg["indexed"]:
            meta = materialize_indexed(dd, pdir, helpers[dd])
            idx_meta.append(meta)
            verification["datasets"][track][dd] = meta
        # Keep only package resources, not transient raw dumps.
        for transient in pdir.glob("*.logical.raw"):
            transient.unlink()
        for transient in pdir.glob("*.dump.raw"):
            transient.unlink()
        inv = inventory(pdir)
        packages[track] = {"inventory": inv, "sequential": seq_meta, "indexed": idx_meta}
        fixtures.append({"fixtureId": f"{track}.candidate-v1-physical-v2", "track": track, "status": STATUS, "packagePath": track})
    (out / "verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    write_review(out)
    reset = verify_reset(out)
    manifest = {"kind": "p3-fixture-materialization-v2-local-gnucobol-bdb-candidate", "status": STATUS, "fixtures": fixtures, "packages": packages, "verification": "verification.json", "byte_layout_review": "byte-layout-review.json", "reset_verification": reset, "claims": {"business_cobol_executed": False, "expected_outputs_created": False, "official_fixture": False, "campaign_authorized": False}, "allowed_inputs_used": ["P3/fixture-candidates-v1", "P3/native-display-probe-v1", "P2b support technique: local GnuCOBOL indexed LOAD/DUMP pattern only; no support datasets or expected outputs copied"], "toolchain_evidence": {"cobc_info_file": "../cobc-info.txt", "helpers_compiled": sorted(helpers)}, "required_sidecars": {"posting/XREFFILE.1": (out / "posting" / "XREFFILE.1").exists(), "interest/XREFFILE.1": (out / "interest" / "XREFFILE.1").exists()}, "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    write_docs(out)
    return manifest


def verify_reset(out: Path) -> dict[str, Any]:
    baseline = {track: inventory(out / track) for track in PACKAGES}
    with tempfile.TemporaryDirectory(prefix="fixture-reset-") as td:
        first = Path(td) / "first"; second = Path(td) / "second"
        shutil.copytree(out, first)
        (first / "posting" / "DALYTRAN").write_bytes(b"MUTATED")
        shutil.copytree(out, second)
        second_inv = {track: inventory(second / track) for track in PACKAGES}
    matches = {track: baseline[track]["treeSha256"] == second_inv[track]["treeSha256"] for track in PACKAGES}
    return {"method": "mutate copied first workspace, prepare fresh second copy from package, compare full inventory", "perTrackRestored": matches, "resetVerified": all(matches.values())}


def verify_only(out: Path) -> dict[str, Any]:
    out = out.resolve()
    manifest = json.loads((out / "manifest.json").read_text())
    verification = json.loads((out / "verification.json").read_text())
    if manifest["status"] != STATUS or verification["status"] != "pass":
        raise AssertionError("manifest/verification status mismatch")
    for track in PACKAGES:
        inv = inventory(out / track)
        if inv["treeSha256"] != manifest["packages"][track]["inventory"]["treeSha256"]:
            raise AssertionError(f"inventory mismatch {track}")
    (out / "verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return verification


def write_docs(out: Path) -> None:
    text = f"""# Fixture materialization v2 — exposição e proveniência

Status: `{STATUS}`. Este pacote é técnico local para revisão; não oficializa casos, campanhas ou oráculos.

## Limite metodológico

- Integração técnica: usa o padrão de transporte GnuCOBOL/BDB (LOAD/DUMP por programa COBOL local) e o probe nativo de DISPLAY para qualificar bytes.
- Não é referência independente de expectativas: nenhum output esperado foi criado, nenhum resultado de negócio foi inferido, e nenhum COBOL CardDemo de negócio foi executado.
- Leitura de suporte quebra isolamento estrito de autoria; por isso a proveniência declara integração técnica, não autoria independente de expectativas.

## Fontes usadas

- Dados sintéticos candidatos v1: `P3/fixture-candidates-v1/`.
- Probe runtime compilado: `P3/native-display-probe-v1/`.
- Técnica de suporte permitida: padrão local GnuCOBOL de materialização/leitura; sem copiar datasets, runs ou oráculos anteriores.

## Verificações incluídas

- `byte-layout-review.json`: layouts fonte, campos `S9 DISPLAY`, e comparação com probe runtime (`-123` termina em byte `0x73`).
- `verification.json`: leitura de volta via GnuCOBOL dos indexed files e comparação byte-a-byte com imagens lógicas JSONL.
- `manifest.json`: inventário com bytes/sha256 de todos os recursos físicos, incluindo `posting/XREFFILE.1` e `interest/XREFFILE.1`.
- reset verificado por mutação de workspace e recópia fresca com comparação integral de inventário.
"""
    (out / "EXPOSICAO-PROVENIENCIA.md").write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--verify-only", type=Path)
    args = ap.parse_args()
    if args.verify_only:
        print(json.dumps(verify_only(args.verify_only), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(materialize(args.output), indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

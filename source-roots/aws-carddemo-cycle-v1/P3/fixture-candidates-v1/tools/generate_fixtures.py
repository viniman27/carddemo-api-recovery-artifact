#!/usr/bin/env python3
"""Generate pre-test candidate fixtures from authorized CardDemo layouts.

This script materializes candidate input bytes only. It does not run COBOL,
does not produce expected outputs, and does not freeze official cases.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
SOURCE_ROOT = P3 / "reference-authoring-input-v1"
CORPUS = SOURCE_ROOT / "corpus"

STATUS = "candidate_needs_review"
SOURCE_COMMIT = "59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e"


def x(value: str, length: int) -> str:
    value = value[:length]
    return value.ljust(length)


def n(value: int | str, length: int) -> str:
    s = str(value)
    if s.startswith("-"):
        # Candidate logical DISPLAY bytes only; no COBOL runtime sign validation.
        s = s[1:]
    return s.zfill(length)[-length:]


def money_cents(cents: int, length: int) -> str:
    return n(cents, length)


def dalytran_record(tran_id: str, card: str, proc_date: str, amount_cents: int = 1200) -> bytes:
    s = "".join([
        x(tran_id, 16),          # DALYTRAN-ID PIC X(16)
        x("01", 2),             # TYPE
        n("0005", 4),           # CAT
        x("Internet", 10),      # SOURCE
        x("candidate purchase", 100),
        money_cents(amount_cents, 11),
        n(123456789, 9),
        x("Fixture Merchant", 50),
        x("Sometown", 50),
        x("70000000", 10),
        x(card, 16),
        x(proc_date + "-10.00.00.000000", 26),
        x(proc_date + "-10.05.00.000000", 26),
        x("", 20),
    ])
    assert len(s) == 350
    return s.encode("ascii")


def tran_record(tran_id: str, card: str, proc_date: str, amount_cents: int = 1200) -> bytes:
    # Same physical layout as CVTRA05Y/TRAN-RECORD (350 bytes).
    return dalytran_record(tran_id, card, proc_date, amount_cents)


def tcatbal_record(acct: str, tran_type: str, cat: str, balance_cents: int) -> bytes:
    s = "".join([n(acct, 11), x(tran_type, 2), n(cat, 4), money_cents(balance_cents, 11), x("", 22)])
    assert len(s) == 50
    return s.encode("ascii")


def account_record(acct: str, group: str, balance_cents: int = 500000, credit_limit_cents: int = 99999900) -> str:
    s = "".join([
        n(acct, 11),
        x("Y", 1),
        money_cents(balance_cents, 12),
        money_cents(credit_limit_cents, 12),
        money_cents(credit_limit_cents, 12),
        x("2020-01-01", 10),
        x("2030-12-31", 10),
        x("2022-01-01", 10),
        money_cents(0, 12),
        money_cents(0, 12),
        x("70000000", 10),
        x(group, 10),
        x("", 178),
    ])
    assert len(s) == 300
    return s


def xref_record(card: str, cust: str, acct: str) -> str:
    s = x(card, 16) + n(cust, 9) + n(acct, 11) + x("", 14)
    assert len(s) == 50
    return s


def discgrp_record(group: str, tran_type: str, cat: str, rate_cents: int) -> str:
    s = x(group, 10) + x(tran_type, 2) + n(cat, 4) + money_cents(rate_cents, 6) + x("", 28)
    assert len(s) == 50
    return s


def trantype_record(tran_type: str, desc: str) -> str:
    s = x(tran_type, 2) + x(desc, 50) + x("", 8)
    assert len(s) == 60
    return s


def trancat_record(tran_type: str, cat: str, desc: str) -> str:
    s = x(tran_type, 2) + n(cat, 4) + x(desc, 50) + x("", 4)
    assert len(s) == 60
    return s


def dateparm_record(start: str, end: str) -> bytes:
    s = x(start, 10) + x("", 1) + x(end, 10) + x("", 59)
    assert len(s) == 80
    return s.encode("ascii")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_binary(rel: str, chunks: Iterable[bytes]) -> dict:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = b"".join(chunks)
    path.write_bytes(payload)
    return {
        "path": rel,
        "kind": "sequential-fixed-records",
        "encoding": "ascii-fixed-width-no-newline",
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
        "materialization_status": "bytes_materialized_candidate",
    }


def write_jsonl(rel: str, rows: list[dict], physical_components_required: list[str]) -> dict:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "path": rel,
        "kind": "indexed-logical-jsonl",
        "encoding": "utf-8-jsonl-with-ascii-record-image",
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "materialization_status": "logical_bytes_only_candidate",
        "physical_components_required": physical_components_required,
    }


def copy_layout(rel_source: str) -> dict:
    src = CORPUS / rel_source
    dst = ROOT / "layouts" / rel_source
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return {
        "path": str(dst.relative_to(ROOT)),
        "kind": "authorized-layout-copy",
        "encoding": "ascii/source-text-preserved",
        "bytes": dst.stat().st_size,
        "sha256": sha256_file(dst),
        "source": f"reference-authoring-input-v1/corpus/{rel_source}",
    }


def main() -> int:
    for sub in ["data", "layouts", "definitions", "reports"]:
        shutil.rmtree(ROOT / sub, ignore_errors=True)
    for old in ["manifest.json"]:
        try:
            (ROOT / old).unlink()
        except FileNotFoundError:
            pass

    resources: list[dict] = []
    layout_resources = [
        copy_layout(p) for p in [
            "app/cpy/CVTRA06Y.cpy", "app/cpy/CVTRA05Y.cpy", "app/cpy/CVTRA01Y.cpy",
            "app/cpy/CVTRA02Y.cpy", "app/cpy/CVTRA03Y.cpy", "app/cpy/CVTRA04Y.cpy",
            "app/cpy/CVACT01Y.cpy", "app/cpy/CVACT03Y.cpy",
            "app/jcl/POSTTRAN.jcl", "app/jcl/INTCALC.jcl", "app/jcl/TRANREPT.jcl", "app/proc/REPROC.prc",
        ]
    ]

    present_card = "4111111111111111"
    absent_card = "4999999999999999"
    zero_card = "4222222222222222"
    acct_main = "10000000001"
    acct_zero = "10000000002"

    resources.append(write_binary("data/sequential/posting/DALYTRAN.dat", [
        dalytran_record("POST-PRESENT-001", present_card, "2022-07-05", 1200),
        dalytran_record("POST-ABSENT--001", absent_card, "2022-07-05", 3400),
    ]))
    resources.append(write_binary("data/sequential/interest/TCATBALF.dat", [
        tcatbal_record(acct_main, "01", "0005", 5000),
        tcatbal_record(acct_zero, "01", "0005", 7000),
    ]))
    resources.append(write_binary("data/sequential/reporting/TRANFILE.dat", [
        tran_record("REPORT-IN---001", present_card, "2022-07-05", 1200),
        tran_record("REPORT-OUT--001", present_card, "2022-08-01", 3400),
    ]))
    resources.append(write_binary("data/sequential/reporting/TRANFILE.empty.dat", []))
    resources.append(write_binary("data/sequential/reporting/DATEPARM.dat", [dateparm_record("2022-07-01", "2022-07-31")]))

    resources.append(write_jsonl("data/indexed-logical/CARDXREF.jsonl", [
        {"key": present_card, "alternateKey": acct_main, "layout": "CVACT03Y", "recordImage": xref_record(present_card, "123456789", acct_main), "usedBy": ["POSTTRAN.lookup.present", "TRANREPT.lookup"]},
        {"key": zero_card, "alternateKey": acct_zero, "layout": "CVACT03Y", "recordImage": xref_record(zero_card, "123456780", acct_zero), "usedBy": ["INTCALC.rate.zero"]},
    ], ["XREFFILE", "XREFFILE.dat", "XREFFILE.idx", "XREFFILE.1 (alternate key path/component for FD-XREF-ACCT-ID)"]))
    resources.append(write_jsonl("data/indexed-logical/ACCTFILE.jsonl", [
        {"key": acct_main, "layout": "CVACT01Y", "recordImage": account_record(acct_main, "STANDARD")},
        {"key": acct_zero, "layout": "CVACT01Y", "recordImage": account_record(acct_zero, "ZERORATE")},
    ], ["ACCTFILE", "ACCTFILE.dat", "ACCTFILE.idx"]))
    resources.append(write_jsonl("data/indexed-logical/DISCGRP.jsonl", [
        {"key": "STANDARD  010005", "layout": "CVTRA02Y", "recordImage": discgrp_record("STANDARD", "01", "0005", 150)},
        {"key": "ZERORATE  010005", "layout": "CVTRA02Y", "recordImage": discgrp_record("ZERORATE", "01", "0005", 0)},
        {"key": "DEFAULT   010005", "layout": "CVTRA02Y", "recordImage": discgrp_record("DEFAULT", "01", "0005", 100)},
    ], ["DISCGRP", "DISCGRP.dat", "DISCGRP.idx"]))
    resources.append(write_jsonl("data/indexed-logical/TCATBALF.jsonl", [
        {"key": acct_main + "01" + "0005", "layout": "CVTRA01Y", "recordImage": tcatbal_record(acct_main, "01", "0005", 5000).decode("ascii")},
        {"key": acct_zero + "01" + "0005", "layout": "CVTRA01Y", "recordImage": tcatbal_record(acct_zero, "01", "0005", 7000).decode("ascii")},
    ], ["TCATBALF", "TCATBALF.dat", "TCATBALF.idx"]))
    resources.append(write_jsonl("data/indexed-logical/TRANSACT.jsonl", [
        {"key": "REPORT-IN---001", "layout": "CVTRA05Y", "recordImage": tran_record("REPORT-IN---001", present_card, "2022-07-05", 1200).decode("ascii")},
        {"key": "REPORT-OUT--001", "layout": "CVTRA05Y", "recordImage": tran_record("REPORT-OUT--001", present_card, "2022-08-01", 3400).decode("ascii")},
    ], ["TRANFILE", "TRANFILE.dat", "TRANFILE.idx"]))
    resources.append(write_jsonl("data/indexed-logical/TRANTYPE.jsonl", [
        {"key": "01", "layout": "CVTRA03Y", "recordImage": trantype_record("01", "Purchase")},
    ], ["TRANTYPE", "TRANTYPE.dat", "TRANTYPE.idx"]))
    resources.append(write_jsonl("data/indexed-logical/TRANCATG.jsonl", [
        {"key": "010005", "layout": "CVTRA04Y", "recordImage": trancat_record("01", "0005", "Candidate category")},
    ], ["TRANCATG", "TRANCATG.dat", "TRANCATG.idx"]))

    for r in resources:
        r.setdefault("source", "generated locally from authorized copybook layouts and JCL DD inventory")
        r.setdefault("provenance", {
            "sourcePackage": "P3/reference-authoring-input-v1",
            "sourceCommit": SOURCE_COMMIT,
            "modelExecuted": False,
            "businessCobolExecuted": False,
            "officialCaseGenerated": False,
        })

    manifest = {
        "status": STATUS,
        "kind": "pretest-fixture-candidate-not-official-not-frozen",
        "scope": ["posting", "interest", "reporting"],
        "non_claims": [
            "not an official fixture package",
            "not a smoke promotion",
            "not expected outputs or business oracle",
            "not COBOL business execution",
            "not campaign authorization",
            "not portable Berkeley DB/GnuCOBOL indexed-file materialization",
        ],
        "authorized_inputs_read": [
            "P3/reference-authoring-input-v1/README.md",
            "P3/reference-authoring-input-v1/input-manifest.json",
            "P3/reference-authoring-input-v1/corpus/app/cpy/*.cpy in manifest",
            "P3/reference-authoring-input-v1/corpus/app/cbl/{CBTRN02C,CBACT04C,CBTRN03C}.cbl",
            "P3/reference-authoring-input-v1/corpus/app/jcl/{POSTTRAN,INTCALC,TRANREPT}.jcl",
            "P3/reference-authoring-input-v1/corpus/app/proc/REPROC.prc",
            "P3/reference-executable-v4/{README.md,model.json}",
            "P3/reference-independent-review-v4/REVIEW.md",
            "P3/PROPOSTA-EXPERIMENTAL-PARA-ACEITE.md",
        ],
        "resources": resources,
        "layout_copies": layout_resources,
        "fixtures": [
            {"id": "posting.lookup-mixed.v1", "track": "posting", "inputResources": ["data/sequential/posting/DALYTRAN.dat"], "stateResources": ["data/indexed-logical/CARDXREF.jsonl", "data/indexed-logical/ACCTFILE.jsonl", "data/indexed-logical/TCATBALF.jsonl", "data/indexed-logical/TRANSACT.jsonl"], "families": ["posting.lookup.present", "posting.lookup.absent"], "reviewPurpose": "exercise daily transaction lookup present and absent branches with real 350-byte DALYTRAN records"},
            {"id": "interest.rate-zero-nonzero.v1", "track": "interest", "inputResources": ["data/sequential/interest/TCATBALF.dat"], "stateResources": ["data/indexed-logical/TCATBALF.jsonl", "data/indexed-logical/CARDXREF.jsonl", "data/indexed-logical/ACCTFILE.jsonl", "data/indexed-logical/DISCGRP.jsonl"], "parameters": {"PARM": "2022071800"}, "families": ["interest.rate.zero", "interest.rate.nonzero"], "reviewPurpose": "cover zero and non-zero disclosure interest-rate partitions without calculating result output"},
            {"id": "reporting.date-selection-and-empty.v1", "track": "reporting", "inputResources": ["data/sequential/reporting/TRANFILE.dat", "data/sequential/reporting/TRANFILE.empty.dat", "data/sequential/reporting/DATEPARM.dat"], "stateResources": ["data/indexed-logical/CARDXREF.jsonl", "data/indexed-logical/TRANTYPE.jsonl", "data/indexed-logical/TRANCATG.jsonl"], "families": ["reporting.date-selection", "reporting.empty-input", "reporting.absent-input-blocked"], "reviewPurpose": "separate date-selection bytes, empty sequential input bytes, and absent-input blocker"},
        ],
        "selection_families": [
            {"id": "posting.lookup.present", "track": "posting", "justification": "CARDXREF lookup is a required external indexed dependency; candidate includes one present card/account path."},
            {"id": "posting.lookup.absent", "track": "posting", "justification": "Absent card lookup is distinct from empty input and is required by POSTTRAN validation family."},
            {"id": "interest.rate.zero", "track": "interest", "justification": "Reviewed abstract reference specifically preserved the zero-rate branch with no interest write attempt."},
            {"id": "interest.rate.nonzero", "track": "interest", "justification": "Contrasts with zero-rate branch using same TCATBAL/account structure and nonzero DISCGRP logical record."},
            {"id": "reporting.date-selection", "track": "reporting", "justification": "TRANREPT has separate DATEPARM and text date selection before report detail lookups."},
            {"id": "reporting.empty-input", "track": "reporting", "justification": "Empty sequential TRANFILE bytes are materially different from missing DD/resource."},
            {"id": "reporting.absent-input-blocked", "track": "reporting", "justification": "Absent resource is represented as a precondition/blocker, not silently replaced by empty bytes."},
        ],
        "indexed_resource_materialization": {
            "status": "blocked_for_physical_bdb_materialization",
            "blockers": [
                "Berkeley DB/GnuCOBOL indexed files are environment-specific and require creation/rebuild support not included in the authorized source-only corpus.",
                "Alternate-key/card-xref path components such as XREFFILE.1 may be required in addition to the primary logical dataset; JSONL logical bytes do not prove local BDB readiness.",
                "No COBOL business program or official setup runner was executed for this candidate package.",
            ],
            "delivered_instead": "logical record images and key metadata tied to original copybook layouts for later integration by an approved materializer",
        },
        "preconditions": [
            "Use only candidate package copies; do not fall back to smoke fixtures or previous technical packages.",
            "Materialize indexed resources with an approved GnuCOBOL/BDB-aware loader before invoking programs that require ORGANIZATION INDEXED.",
            "Bind every DD explicitly to the prepared workspace; inherited environment bindings are not allowed.",
            "Review candidate content before any official freeze or campaign.",
        ],
        "reset": {
            "policy": "fresh directory per attempted application; copy all resources from this package, verify sha256/bytes before use, then verify/reset from immutable source for next application",
            "commands": [
                "rm -rf /tmp/aws-carddemo-fixture-run && mkdir -p /tmp/aws-carddemo-fixture-run",
                "cp -R P3/fixture-candidates-v1/data /tmp/aws-carddemo-fixture-run/",
                "python3 P3/fixture-candidates-v1/tools/verify_manifest.py P3/fixture-candidates-v1/manifest.json",
            ],
        },
        "separation_of_data_and_expectations": {
            "expectation_files_created": [],
            "oracle_policy": "No expected output files are generated here; do not derive oracles from outputs produced by COBOL/adapters using this package.",
        },
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / "reports").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports" / "generated-summary.json").write_text(json.dumps({
        "status": STATUS,
        "resourceCount": len(resources),
        "layoutCopyCount": len(layout_resources),
        "manifestSha256": sha256_file(ROOT / "manifest.json"),
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

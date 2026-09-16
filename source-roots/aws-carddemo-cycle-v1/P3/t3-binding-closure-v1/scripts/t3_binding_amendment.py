from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

LOCAL_PREFIX = "p3-local-technical-fixture-selection:"
P3_ROOT = Path(__file__).resolve().parents[2]
HARNESS_SRC = P3_ROOT / "campaign-harness-v3" / "src"
if HARNESS_SRC.exists() and str(HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(HARNESS_SRC))

E1_BINDINGS: dict[tuple[str, str], dict[str, str]] = {
    ("E1-1", "posting"): {
        "transactionFile": "TRANFILE",
        "crossReferenceFile": "XREFFILE",
        "accountFile": "ACCTFILE",
        "categoryBalanceFile": "TCATBALF",
        "rejectFile": "DALYREJS",
    },
    ("E1-1", "interest"): {
        "categoryBalanceFile": "TCATBALF",
        "crossReferenceFile": "XREFFILE",
        "disclosureGroupFile": "DISCGRP",
        "accountFile": "ACCTFILE",
        "outputTransactionFile": "TRANSACT",
    },
    ("E1-1", "reporting"): {
        "crossReferenceFile": "CARDXREF",
        "transactionTypeFile": "TRANTYPE",
        "transactionCategoryFile": "TRANCATG",
        "reportFile": "TRANREPT",
    },
    ("E1-2", "posting"): {
        "transactionFile": "TRANFILE",
        "crossReferenceFile": "XREFFILE",
        "accountFile": "ACCTFILE",
        "categoryBalanceFile": "TCATBALF",
    },
    ("E1-2", "interest"): {
        "categoryBalanceFile": "TCATBALF",
        "crossReferenceFile": "XREFFILE",
        "accountFile": "ACCTFILE",
        "disclosureGroupFile": "DISCGRP",
    },
    ("E1-2", "reporting"): {
        "crossReferenceFile": "CARDXREF",
        "transactionTypeFile": "TRANTYPE",
        "transactionCategoryFile": "TRANCATG",
    },
    ("E1-3", "posting"): {
        "cardCrossReference": "XREFFILE",
        "accounts": "ACCTFILE",
        "categoryBalances": "TCATBALF",
        "transactionOutput": "TRANFILE",
        "rejectionOutput": "DALYREJS",
    },
    ("E1-3", "interest"): {
        "categoryBalances": "TCATBALF",
        "cardCrossReference": "XREFFILE",
        "accounts": "ACCTFILE",
        "disclosureGroups": "DISCGRP",
        "transactionOutput": "TRANSACT",
    },
    ("E1-3", "reporting"): {
        "cardCrossReference": "CARDXREF",
        "transactionTypes": "TRANTYPE",
        "transactionCategories": "TRANCATG",
        "reportOutput": "TRANREPT",
    },
}

E2_2_BINDINGS: dict[str, dict[str, str]] = {
    "posting": {
        "crossReferences": "XREFFILE",
        "accounts": "ACCTFILE",
        "categoryBalances": "TCATBALF",
        "transactionOutput": "TRANFILE",
        "rejectionOutput": "DALYREJS",
    },
    "interest": {
        "categoryBalances": "TCATBALF",
        "crossReferences": "XREFFILE",
        "accounts": "ACCTFILE",
        "disclosureGroups": "DISCGRP",
        "transactionOutput": "TRANSACT",
    },
    "reporting": {
        "crossReferences": "CARDXREF",
        "transactionTypes": "TRANTYPE",
        "transactionCategories": "TRANCATG",
        "reportOutput": "REPORT",
    },
}

E1_INPUT_ALIASES: dict[tuple[str, str, str], str] = {
    ("E1-1", "reporting", "reportFile"): "REPORT",
    ("E1-3", "reporting", "reportOutput"): "REPORT",
}

EXACT_DATE_PARAMETER_RECORD_ASCII80 = "2022-07-01 2022-07-31                                                           "
assert len(EXACT_DATE_PARAMETER_RECORD_ASCII80.encode("ascii")) == 80


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_hash_obj(data: Any) -> str:
    return sha256_bytes(json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def json_body_from_case(case: dict[str, Any]) -> dict[str, Any]:
    raw = base64.b64decode(case["request"]["body_b64"], validate=True)
    body = json.loads(raw.decode("utf-8"))
    if not isinstance(body, dict):
        raise ValueError(f"case body is not an object: {case.get('case_id')}")
    return body


def encode_body(body: dict[str, Any]) -> str:
    return base64.b64encode(json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).decode("ascii")


def amend_body(contract_id: str, track: str, body: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    amended = copy.deepcopy(body)
    changes: list[dict[str, str]] = []

    e1_map = E1_BINDINGS.get((contract_id, track))
    if e1_map:
        for field, dd in e1_map.items():
            old_value = amended.get(field)
            expected_old_value = E1_INPUT_ALIASES.get((contract_id, track, field), dd)
            if isinstance(old_value, str) and old_value == expected_old_value:
                new_value = f"p3:{track}:{dd}"
                amended[field] = new_value
                changes.append({"field": field, "from": old_value, "to": new_value, "protocol": "P2c-zero-shot-local-token"})
        if track == "reporting" and isinstance(amended.get("dateParameterRecords"), list):
            converted = []
            for index, value in enumerate(amended["dateParameterRecords"]):
                if value == EXACT_DATE_PARAMETER_RECORD_ASCII80:
                    raw = value.encode("ascii")
                    new_value = base64.b64encode(raw).decode("ascii")
                    converted.append(new_value)
                    changes.append({"field": f"dateParameterRecords[{index}]", "from": f"sha256:{sha256_bytes(raw)}", "to": f"sha256:{sha256_bytes(new_value.encode('ascii'))}", "protocol": "DateParameterRecord-exact-ascii80-base64-contentEncoding"})
                    continue
                converted.append(value)
            amended["dateParameterRecords"] = converted
        return amended, changes

    if contract_id == "E2-2":
        bindings = amended.get("bindings")
        expected_fields = E2_2_BINDINGS.get(track, {})
        if isinstance(bindings, dict):
            for field, expected_old_value in sorted(expected_fields.items()):
                old_value = bindings.get(field)
                if isinstance(old_value, str) and old_value == expected_old_value:
                    new_value = f"{LOCAL_PREFIX}{field}"
                    bindings[field] = new_value
                    changes.append({"field": f"bindings.{field}", "from": old_value, "to": new_value, "protocol": "P2c-few-shot-local-token"})
        if track == "reporting" and isinstance(amended.get("dateParameterRecords"), list):
            converted = []
            for index, value in enumerate(amended["dateParameterRecords"]):
                if value == EXACT_DATE_PARAMETER_RECORD_ASCII80:
                    raw = value.encode("ascii")
                    new_value = base64.b64encode(raw).decode("ascii")
                    converted.append(new_value)
                    changes.append({"field": f"dateParameterRecords[{index}]", "from": f"sha256:{sha256_bytes(raw)}", "to": f"sha256:{sha256_bytes(new_value.encode('ascii'))}", "protocol": "DateParameterRecord-exact-ascii80-base64-contentEncoding"})
                    continue
                converted.append(value)
            amended["dateParameterRecords"] = converted
        return amended, changes

    return amended, changes


def select_all_cases(suite: dict[str, Any]) -> list[dict[str, Any]]:
    return list(suite.get("cases", []))


def amend_t3_cases(freeze_root: Path, out_dir: Path, contracts: list[str]) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    all_cases: list[dict[str, Any]] = []
    manifest: dict[str, Any] = {
        "kind": "t3-binding-closure-v2-amendment",
        "officialCampaign": False,
        "scope": "candidate technical-token amendment for every original T3 case; no API/COBOL/contract/business data changes",
        "inputs": [],
        "cases": [],
        "unchangedContractDefectsPreserved": True,
    }
    for contract_id in contracts:
        path = freeze_root / contract_id / "T3.json"
        source_bytes = path.read_bytes()
        suite = json.loads(source_bytes)
        manifest["inputs"].append({"contractId": contract_id, "path": str(path), "sha256": sha256_bytes(source_bytes), "bytes": len(source_bytes)})
        for original in select_all_cases(suite):
            case = copy.deepcopy(original)
            params = case.get("parameters") or {}
            track = str(params.get("track"))
            before_raw = base64.b64decode(case["request"]["body_b64"], validate=True)
            body_before = json.loads(before_raw.decode("utf-8"))
            if not isinstance(body_before, dict):
                raise ValueError(f"case body is not an object: {case.get('case_id')}")
            body_after, changes = amend_body(contract_id, track, body_before)
            after_raw = json.dumps(body_after, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            case["case_id"] = f"BINDCLOSE-{contract_id}-{track}-{case['case_id']}"
            case["suite_id"] = "T3"
            case["origin"] = f"t3-binding-closure-v2:{contract_id}:{track}"
            case["request"]["body_b64"] = base64.b64encode(after_raw).decode("ascii")
            params = dict(params)
            params["bindingClosureAmendment"] = {
                "version": "v2",
                "sourceCaseId": original["case_id"],
                "sourceContractId": contract_id,
                "sourceTrack": track,
                "technicalOnly": True,
                "changes": changes,
                "beforeRawBodySha256": sha256_bytes(before_raw),
                "afterRawBodySha256": sha256_bytes(after_raw),
                "beforeRawBodyBytes": len(before_raw),
                "afterRawBodyBytes": len(after_raw),
            }
            case["parameters"] = params
            case["provenance"] = list(case.get("provenance") or []) + [f"t3-binding-closure-v2:amended-from:{contract_id}/T3.json:{original['case_id']}"]
            all_cases.append(case)
            manifest["cases"].append({
                "caseId": case["case_id"],
                "sourceCaseId": original["case_id"],
                "contractId": contract_id,
                "track": track,
                "operationId": params.get("operationId"),
                "requestPath": case["request"]["path"],
                "changes": changes,
                "beforeRawBodySha256": sha256_bytes(before_raw),
                "afterRawBodySha256": sha256_bytes(after_raw),
                "beforeRawBodyBytes": len(before_raw),
                "afterRawBodyBytes": len(after_raw),
            })
    suite = {"suite_id": "T3", "cases": all_cases}
    suite["suite_freeze_sha256"] = canonical_hash_obj(suite)
    suite_bytes = json.dumps(suite, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
    suite_path = out_dir / "T3-BINDING-CLOSURE-V2.json"
    suite_path.write_bytes(suite_bytes)
    manifest["outputSuite"] = {"path": str(suite_path), "sha256": sha256_bytes(suite_bytes), "bytes": len(suite_bytes), "caseCount": len(all_cases)}
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
    (out_dir / "AMENDMENT-MANIFEST.json").write_bytes(manifest_bytes)
    return manifest


# Backward-compatible name; now intentionally processes every T3 case.
def amend_selected_suites(freeze_root: Path, out_dir: Path, contracts: list[str]) -> dict[str, Any]:
    return amend_t3_cases(freeze_root, out_dir, contracts)


def _json_bytes(data: Any) -> bytes:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n"


def amend_one_t3_suite_to_path(v1_root: Path, out_path: Path, contract_id: str) -> dict[str, Any]:
    src = v1_root / contract_id / "T3.json"
    source_bytes = src.read_bytes()
    suite = json.loads(source_bytes)
    out_cases: list[dict[str, Any]] = []
    case_manifest: list[dict[str, Any]] = []
    change_count = 0
    for original in select_all_cases(suite):
        case = copy.deepcopy(original)
        params = case.get("parameters") or {}
        track = str(params.get("track"))
        before_raw = base64.b64decode(case["request"]["body_b64"], validate=True)
        body_before = json.loads(before_raw.decode("utf-8"))
        if not isinstance(body_before, dict):
            raise ValueError(f"case body is not an object: {case.get('case_id')}")
        body_after, changes = amend_body(contract_id, track, body_before)
        after_raw = json.dumps(body_after, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        params = dict(params)
        params["bindingClosureAmendment"] = {
            "version": "v2",
            "sourceCaseId": original["case_id"],
            "sourceContractId": contract_id,
            "sourceTrack": track,
            "technicalOnly": True,
            "changes": changes,
            "beforeRawBodySha256": sha256_bytes(before_raw),
            "afterRawBodySha256": sha256_bytes(after_raw),
            "beforeRawBodyBytes": len(before_raw),
            "afterRawBodyBytes": len(after_raw),
        }
        case["case_id"] = f"BINDCLOSE-{contract_id}-{track}-{case['case_id']}"
        case["suite_id"] = f"{contract_id}-T3"
        case["origin"] = f"t3-binding-closure-v2:{contract_id}:{track}"
        case["parameters"] = params
        case["request"]["body_b64"] = base64.b64encode(after_raw).decode("ascii")
        case["provenance"] = list(case.get("provenance") or []) + [f"t3-binding-closure-v2:amended-from:{contract_id}/T3.json:{original['case_id']}"]
        out_cases.append(case)
        change_count += len(changes)
        case_manifest.append({
            "caseId": case["case_id"],
            "sourceCaseId": original["case_id"],
            "contractId": contract_id,
            "track": track,
            "operationId": params.get("operationId"),
            "requestPath": case["request"]["path"],
            "changes": changes,
            "beforeRawBodySha256": sha256_bytes(before_raw),
            "afterRawBodySha256": sha256_bytes(after_raw),
            "beforeRawBodyBytes": len(before_raw),
            "afterRawBodyBytes": len(after_raw),
        })
    out_suite = {"suite_id": f"{contract_id}-T3", "cases": out_cases}
    out_suite["suite_freeze_sha256"] = canonical_hash_obj(out_suite)
    out_bytes = _json_bytes(out_suite)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(out_bytes)
    return {
        "input": {"path": str(src), "sha256": sha256_bytes(source_bytes), "bytes": len(source_bytes), "cases": len(suite.get("cases", []))},
        "output": {"path": str(out_path), "sha256": sha256_bytes(out_bytes), "bytes": len(out_bytes), "cases": len(out_cases)},
        "cases": case_manifest,
        "changeCount": change_count,
    }


def assemble_campaign_package_v2(v1_root: Path, out_dir: Path) -> dict[str, Any]:
    from campaign_harness import Suite, UnionBuilder, freeze_suite, load_frozen_suite

    v1_root = v1_root.resolve()
    out_dir = out_dir.resolve()
    if out_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing package: {out_dir}")
    out_dir.mkdir(parents=True)
    v1_manifest_path = v1_root / "MANIFEST.json"
    v1_manifest_bytes = v1_manifest_path.read_bytes()
    v1_manifest = json.loads(v1_manifest_bytes)
    contracts = [row["contractId"] for row in v1_manifest["suites"] if row["condition"] == "T3"]
    rows: list[dict[str, Any]] = []
    source_pins: list[dict[str, Any]] = [{"path": str(v1_manifest_path), "sha256": sha256_bytes(v1_manifest_bytes), "bytes": len(v1_manifest_bytes)}]
    transformations: dict[str, Any] = {}
    union_ledgers: dict[str, Any] = {}
    for contract_id in contracts:
        normalized = []
        for condition in ["T1", "T2"]:
            src = v1_root / contract_id / f"{condition}.json"
            dest = out_dir / contract_id / f"{condition}.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
            src_bytes = src.read_bytes()
            dest_bytes = dest.read_bytes()
            if src_bytes != dest_bytes:
                raise AssertionError(f"{contract_id} {condition} byte preservation failed")
            loaded = load_frozen_suite(dest)
            normalized.append(Suite(condition, copy.deepcopy(loaded.cases)))
            rows.append({"contractId": contract_id, "condition": condition, "cases": len(loaded.cases), "path": str(dest), "sha256": sha256_bytes(dest_bytes), "bytes": len(dest_bytes), "preservedFromV1ExactBytes": True})
            source_pins.append({"contractId": contract_id, "condition": condition, "path": str(src), "sha256": sha256_bytes(src_bytes), "bytes": len(src_bytes)})
        t3_dest = out_dir / contract_id / "T3.json"
        t3_report = amend_one_t3_suite_to_path(v1_root, t3_dest, contract_id)
        transformations[contract_id] = t3_report
        loaded_t3 = load_frozen_suite(t3_dest)
        normalized.append(Suite("T3", copy.deepcopy(loaded_t3.cases)))
        rows.append({"contractId": contract_id, "condition": "T3", "cases": len(loaded_t3.cases), "path": str(t3_dest), "sha256": t3_report["output"]["sha256"], "bytes": t3_report["output"]["bytes"], "amendedFromV1": True, "technicalChangeCount": t3_report["changeCount"]})
        source_pins.append({"contractId": contract_id, "condition": "T3", **t3_report["input"]})
        union, ledger = UnionBuilder().build(normalized)
        union_ledgers[contract_id] = ledger
        for case in union.cases:
            case.case_id = contract_id + "-" + case.case_id
        t4_dest = out_dir / contract_id / "T4.json"
        freeze_suite(Suite(f"{contract_id}-T4", union.cases), t4_dest)
        loaded_t4 = load_frozen_suite(t4_dest)
        t4_bytes = t4_dest.read_bytes()
        rows.append({"contractId": contract_id, "condition": "T4", "cases": len(loaded_t4.cases), "path": str(t4_dest), "sha256": sha256_bytes(t4_bytes), "bytes": len(t4_bytes), "rebuiltWithHarnessUnionBuilder": True})
    counts = {condition: sum(row["cases"] for row in rows if row["condition"] == condition) for condition in ["T1", "T2", "T3", "T4"]}
    manifest = {
        "kind": "campaign-freeze-package-v2",
        "state": "frozen_bytes_pending_final_readiness_no_official_execution",
        "basedOn": {"package": str(v1_root), "manifestSha256": sha256_bytes(v1_manifest_bytes), "statePreserved": v1_manifest.get("state")},
        "officialRuntimeStarted": False,
        "officialExecutionAuthorizedOrClaimed": False,
        "sourcePins": source_pins,
        "suites": rows,
        "counts": counts,
        "aggregate": {"contracts": len(contracts), "suiteCount": len(rows), "expectedConditionsPerContract": ["T1", "T2", "T3", "T4"]},
        "guards": [
            "T1/T2 copied byte-for-byte from campaign-freeze-package-v1 and reloaded with campaign-harness-v3 load_frozen_suite.",
            "T3 amendments are technical binding substitutions only, qualified by exact known placeholder values; arbitrary invalid strings and already-encoded date records are preserved.",
            "T4 rebuilt only via campaign-harness-v3 UnionBuilder from package-v2 T1/T2/T3 suites; no replica union implementation used.",
            "No COBOL/API/runtime/model/fuzzer execution performed by this package assembly.",
        ],
        "sourceCodeProtocolPins": {
            "protocol": "casos/aws-carddemo-cycle-v1/PROTOCOLO.md sections 4-5: technical operationalization and T1-T4 freeze pending P3 readiness",
            "harness": "P3/campaign-harness-v3/src/campaign_harness.py::load_frozen_suite/freeze_suite/UnionBuilder",
            "amendmentScript": str(Path(__file__).resolve()),
            "facadeEvidence": ["P2c-zero-shot accepts p3:{track}:{DD}", "P2c-few-shot accepts p3-local-technical-fixture-selection:{field}", "reporting REPORT maps to local DD TRANREPT"],
        },
        "limits": [
            "Package v2 is pending final readiness only; it is not an official campaign execution package claim.",
            "Business data, SDD empty-object defects, and non-target invalid payload bytes are intentionally preserved.",
            "No readiness/coverage/oracle conclusion is implied by successful freeze assembly.",
        ],
    }
    (out_dir / "MANIFEST.json").write_bytes(_json_bytes(manifest))
    (out_dir / "UNION-LEDGER.json").write_bytes(_json_bytes(union_ledgers))
    (out_dir / "T3-TRANSFORMATIONS.json").write_bytes(_json_bytes(transformations))
    return manifest


def verify_campaign_package_v2(out_dir: Path) -> dict[str, Any]:
    from campaign_harness import load_frozen_suite

    out_dir = out_dir.resolve()
    manifest = json.loads((out_dir / "MANIFEST.json").read_text(encoding="utf-8"))
    loaded_counts = {condition: 0 for condition in ["T1", "T2", "T3", "T4"]}
    contracts = sorted({row["contractId"] for row in manifest["suites"]})
    for row in manifest["suites"]:
        path = Path(row["path"])
        data = path.read_bytes()
        if sha256_bytes(data) != row["sha256"] or len(data) != row["bytes"]:
            raise AssertionError(f"manifest hash/bytes mismatch: {path}")
        suite = load_frozen_suite(path)
        if len(suite.cases) != row["cases"]:
            raise AssertionError(f"case count mismatch: {path}")
        loaded_counts[row["condition"]] += len(suite.cases)
    if loaded_counts != manifest["counts"]:
        raise AssertionError({"loaded": loaded_counts, "manifest": manifest["counts"]})
    if len(contracts) != 7 or len(manifest["suites"]) != 28:
        raise AssertionError({"contracts": len(contracts), "suites": len(manifest["suites"])})
    return {"contracts": len(contracts), "suites": len(manifest["suites"]), "counts": loaded_counts}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-root", help="input freeze root for standalone T3 amendment")
    parser.add_argument("--output", required=True)
    parser.add_argument("--contracts", nargs="+", default=["E1-1", "E1-2", "E1-3", "E2-2"])
    parser.add_argument("--assemble-package-v2", action="store_true", help="create complete campaign-freeze-package-v2 from package v1")
    parser.add_argument("--verify-package-v2", action="store_true", help="verify an existing package v2 at --output")
    args = parser.parse_args()
    if args.verify_package_v2:
        report = verify_campaign_package_v2(Path(args.output))
        print(json.dumps({"ok": True, "verified": report}, ensure_ascii=False))
        return 0
    if args.assemble_package_v2:
        if not args.freeze_root:
            parser.error("--freeze-root is required with --assemble-package-v2")
        manifest = assemble_campaign_package_v2(Path(args.freeze_root), Path(args.output))
        verified = verify_campaign_package_v2(Path(args.output))
        print(json.dumps({"ok": True, "manifest": {"counts": manifest["counts"], "aggregate": manifest["aggregate"]}, "verified": verified}, ensure_ascii=False))
        return 0
    if not args.freeze_root:
        parser.error("--freeze-root is required unless --verify-package-v2 is used")
    manifest = amend_selected_suites(Path(args.freeze_root), Path(args.output), args.contracts)
    print(json.dumps({"ok": True, "suite": manifest["outputSuite"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

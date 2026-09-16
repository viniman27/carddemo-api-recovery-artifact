from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[2]
HARNESS_SRC = ROOT / "campaign-harness-v3" / "src"
sys.path.insert(0, str(HARNESS_SRC))

from campaign_harness import Suite, UnionBuilder, freeze_suite, load_frozen_suite  # noqa: E402

CONDITIONS = ("T1", "T2", "T3", "T4")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_pin(path: Path, label: str | None = None) -> Dict[str, Any]:
    data = path.read_bytes()
    row: Dict[str, Any] = {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    if label:
        row["label"] = label
    return row


def load_suite(path: Path) -> Suite:
    return load_frozen_suite(path)


def guard_is_qualified_true(parameters: Dict[str, Any]) -> bool:
    return parameters.get("guardResult") is True


def _case_exclusion_row(contract_id: str, case: Any) -> Dict[str, Any]:
    params = case.parameters
    amend = params.get("bindingClosureAmendment", {}) if isinstance(params.get("bindingClosureAmendment"), dict) else {}
    return {
        "contractId": contract_id,
        "caseId": case.case_id,
        "sourceCaseId": amend.get("sourceCaseId"),
        "guardResult": params.get("guardResult"),
        "guardResultType": type(params.get("guardResult")).__name__,
        "transitionId": params.get("transitionId"),
        "obligationId": params.get("obligationId"),
        "cellRef": params.get("cellRef"),
        "reason": "excluded from v3 because T3 guardResult is not boolean true; case preserved only in v1/v2 sources",
    }


def _package_file_count_and_hash(package_dir: Path, exclude_names: Iterable[str] = ()) -> Dict[str, Any]:
    excluded = set(exclude_names)
    h = hashlib.sha256()
    count = 0
    for path in sorted(p for p in package_dir.rglob("*") if p.is_file() and p.name not in excluded):
        rel = path.relative_to(package_dir).as_posix().encode("utf-8")
        data = path.read_bytes()
        h.update(rel + b"\0" + hashlib.sha256(data).hexdigest().encode("ascii") + b"\n")
        count += 1
    return {"fileCount": count, "aggregateSha256": h.hexdigest()}


def assemble_v3_package(v2_dir: Path, out_dir: Path) -> Dict[str, Any]:
    v2_dir = Path(v2_dir).resolve()
    out_dir = Path(out_dir).resolve()
    if out_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing package: {out_dir}")
    out_dir.mkdir(parents=True)

    contract_dirs = sorted(p for p in v2_dir.iterdir() if p.is_dir() and (p / "T1.json").exists())
    rows: List[Dict[str, Any]] = []
    excluded: List[Dict[str, Any]] = []
    union_ledgers: Dict[str, Any] = {}
    guard_provenance: Dict[str, Any] = {}

    for contract_dir in contract_dirs:
        contract_id = contract_dir.name
        target_contract_dir = out_dir / contract_id
        target_contract_dir.mkdir()
        normalized: List[Suite] = []
        guard_provenance[contract_id] = {}

        for condition in ("T1", "T2", "T3"):
            src = contract_dir / f"{condition}.json"
            dest = target_contract_dir / f"{condition}.json"
            suite = load_frozen_suite(src)
            before_count = len(suite.cases)
            if condition in {"T1", "T2"}:
                shutil.copyfile(src, dest)
                loaded = load_frozen_suite(dest)
                if sha256_file(src) != sha256_file(dest):
                    raise AssertionError(f"{condition} copy changed bytes for {contract_id}")
                cases = copy.deepcopy(loaded.cases)
                exact = True
            else:
                kept = []
                for case in suite.cases:
                    gr = case.parameters.get("guardResult")
                    guard_provenance[contract_id][case.case_id] = {
                        "guardResult": gr,
                        "guardResultType": type(gr).__name__,
                        "transitionId": case.parameters.get("transitionId"),
                        "obligationId": case.parameters.get("obligationId"),
                        "cellRef": case.parameters.get("cellRef"),
                    }
                    if guard_is_qualified_true(case.parameters):
                        kept.append(copy.deepcopy(case))
                    else:
                        excluded.append(_case_exclusion_row(contract_id, case))
                freeze_suite(Suite(f"{contract_id}-T3", kept), dest)
                loaded = load_frozen_suite(dest)
                cases = copy.deepcopy(loaded.cases)
                exact = False
            for case in cases:
                case.suite_id = condition
            normalized.append(Suite(condition, cases))
            rows.append({
                "contractId": contract_id,
                "condition": condition,
                "cases": len(cases),
                "sourceCases": before_count,
                "excludedCases": before_count - len(cases),
                "path": str(dest),
                "sha256": sha256_file(dest),
                "bytes": dest.stat().st_size,
                "preservedFromV2ExactBytes": exact,
                "guardPolicy": "not applicable" if condition in {"T1", "T2"} else "kept only when guardResult is boolean true",
            })

        union, ledger = UnionBuilder().build(normalized)
        union_ledgers[contract_id] = ledger
        for case in union.cases:
            case.case_id = f"{contract_id}-{case.case_id}"
        t4_dest = target_contract_dir / "T4.json"
        freeze_suite(Suite(f"{contract_id}-T4", union.cases), t4_dest)
        loaded_t4 = load_frozen_suite(t4_dest)
        rows.append({
            "contractId": contract_id,
            "condition": "T4",
            "cases": len(loaded_t4.cases),
            "path": str(t4_dest),
            "sha256": sha256_file(t4_dest),
            "bytes": t4_dest.stat().st_size,
            "rebuiltWithHarnessUnionBuilder": True,
            "inputConditions": ["T1", "T2", "T3-v3-guard-qualified-only"],
        })

    counts = {condition: sum(row["cases"] for row in rows if row["condition"] == condition) for condition in CONDITIONS}
    guard_value_counts = Counter(f"{row['guardResultType']}:{row['guardResult']!r}" for row in excluded)

    source_pins = [file_pin(v2_dir / "MANIFEST.json", "campaign-freeze-package-v2-manifest")]
    for rel, label in [
        ("final-campaign-gate-v1/src/final_campaign_gate.py", "v3 package assembler/verification code"),
        ("final-campaign-gate-v1/tests/test_final_campaign_gate.py", "TDD guard exclusion and assembly regression tests"),
        ("campaign-harness-v3/src/campaign_harness.py", "harness load_frozen_suite/freeze_suite/UnionBuilder"),
        ("aws-campaign-runner-v3/src/aws_campaign_runner.py", "official-capable runner per-case target/resource binding"),
        ("campaign-configuration-v2/campaign-config-v2.json", "campaign config budgets/seeds/reset/order"),
        ("campaign-configuration-v2/MANIFEST.json", "campaign config manifest"),
        ("unified-preflight-v3/unified_preflight_cli.py", "unified preflight orchestration"),
        ("unified-preflight-v3/src/coverage_runner_v3.py", "unified coverage collection helpers"),
        ("unified-preflight-v3/src/reconcile_coverage.py", "coverage reconciliation helpers"),
        ("unified-preflight-v3/src/api_target.py", "API target binding helpers"),
        ("PROTOCOLO.md", "AWS CardDemo protocol"),
        ("fixture-materialization-v2/package/manifest.json", "fixture physical resource manifest"),
        ("fixture-materialization-v2/package/verification.json", "fixture physical resource verification"),
        ("t3-substantive-closure-v1/CLOSURE.md", "T3 guard/source closure"),
    ]:
        p = (ROOT / rel) if rel != "PROTOCOLO.md" else (ROOT.parent / rel)
        if p.exists():
            source_pins.append(file_pin(p, label))

    fixture_resource_pins = []
    fixture_root = ROOT / "fixture-materialization-v2" / "package"
    if fixture_root.exists():
        for resource in sorted(p for p in fixture_root.rglob("*") if p.is_file() and p.parent.name in {"posting", "interest", "reporting"}):
            pin = file_pin(resource, "fixture physical resource byte pin")
            pin["fixtureRelativePath"] = resource.relative_to(fixture_root).as_posix()
            fixture_resource_pins.append(pin)

    (out_dir / "UNION-LEDGER.json").write_text(json.dumps(union_ledgers, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "T3-GUARD-EXCLUSIONS.json").write_text(json.dumps({
        "policy": "exclude every T3 case whose guardResult is not the boolean value true; string 'true', false, unknown, null, missing, or numeric truthy values are not qualified",
        "excluded": excluded,
        "excludedCount": len(excluded),
        "guardValueCounts": dict(guard_value_counts),
        "casePreservation": "excluded cases are not deleted from v1/v2; v3 omits them from official candidate suites and records source IDs/reasons here",
    }, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    manifest = {
        "kind": "campaign-freeze-package-v3",
        "state": "frozen_bytes_pending_final_parent_gate_no_official_execution",
        "basedOn": {"package": str(v2_dir), "manifestSha256": sha256_file(v2_dir / "MANIFEST.json")},
        "aggregate": {"contracts": len(contract_dirs), "suiteCount": len(rows), "expectedConditionsPerContract": list(CONDITIONS)},
        "counts": counts,
        "excludedT3CasesTotal": len(excluded),
        "excludedT3Cases": excluded,
        "policy": {
            "t1t2": "copied byte-for-byte from campaign-freeze-package-v2",
            "t3": "suite rebuilt from v2 by excluding only cases where parameters.guardResult is not boolean true",
            "t4": "rebuilt with campaign-harness-v3 UnionBuilder from v3 T1/T2/T3; no official runtime executed",
            "oracle": "no oracle quarantine read; business checker remains inconclusive where unbound",
        },
        "sourcePins": source_pins,
        "fixturePhysicalResourcePins": fixture_resource_pins,
        "suites": rows,
        "officialRuntimeStarted": False,
        "officialExecutionAuthorizedOrClaimed": False,
        "humanApprovalClaimed": False,
        "readinessClaim": "mechanical freeze-ready candidate only; parent still decides/launches official execution",
        "limits": [
            "Exclusion ledger is preflight/freeze evidence, not runtime result evidence.",
            "Business checkers are inconclusive where no independent authority is bound.",
            "No fake human approval is claimed.",
        ],
    }
    (out_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    verification = verify_package(out_dir, v2_dir)
    (out_dir / "VERIFICATION.json").write_text(json.dumps(verification, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    manifest["loadedSuiteRows"] = verification["loadedSuiteRows"]
    manifest["t1t2ExactCopies"] = verification["t1t2ExactCopies"]
    return manifest


def verify_package(package_dir: Path, v2_dir: Path | None = None) -> Dict[str, Any]:
    package_dir = Path(package_dir).resolve()
    counts = {condition: 0 for condition in CONDITIONS}
    loaded = 0
    t1t2_rows = []
    t3_bad_remaining = []
    t4_bad_remaining = []
    for suite_path in sorted(package_dir.glob("*/T*.json")):
        condition = suite_path.stem
        suite = load_frozen_suite(suite_path)
        loaded += 1
        counts[condition] += len(suite.cases)
        contract_id = suite_path.parent.name
        if condition in {"T1", "T2"} and v2_dir is not None:
            src = Path(v2_dir).resolve() / contract_id / f"{condition}.json"
            t1t2_rows.append({"contractId": contract_id, "condition": condition, "exactBytes": sha256_file(src) == sha256_file(suite_path), "sha256": sha256_file(suite_path)})
        if condition == "T3":
            for case in suite.cases:
                if not guard_is_qualified_true(case.parameters):
                    t3_bad_remaining.append({"contractId": contract_id, "caseId": case.case_id, "guardResult": case.parameters.get("guardResult")})
        if condition == "T4":
            for case in suite.cases:
                if case.parameters.get("guardResult") is not None and not guard_is_qualified_true(case.parameters):
                    t4_bad_remaining.append({"contractId": contract_id, "caseId": case.case_id, "guardResult": case.parameters.get("guardResult")})
    package_hash = _package_file_count_and_hash(package_dir, exclude_names={"VERIFICATION.json"})
    return {
        "kind": "campaign-freeze-package-v3-verification",
        "package": str(package_dir),
        "counts": counts,
        "contracts": len(list(package_dir.glob("*/T1.json"))),
        "loadedSuiteRows": loaded,
        "t1t2ExactCopies": all(row["exactBytes"] for row in t1t2_rows),
        "t1t2ExactCopyRows": t1t2_rows,
        "t3GuardNotTrueRemaining": t3_bad_remaining,
        "t4GuardNotTrueRemaining": t4_bad_remaining,
        "officialRuntimeStarted": False,
        "officialReadinessDeclared": False,
        "packageAggregateSha256ExcludingThisReport": package_hash["aggregateSha256"],
        "packageFileCountExcludingThisReport": package_hash["fileCount"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble final campaign freeze package v3 without official execution")
    parser.add_argument("--source", type=Path, default=ROOT / "campaign-freeze-package-v2")
    parser.add_argument("--output", type=Path, default=ROOT / "campaign-freeze-package-v3")
    args = parser.parse_args()
    report = assemble_v3_package(args.source, args.output)
    print(json.dumps({"output": str(args.output.resolve()), "counts": report["counts"], "excludedT3CasesTotal": report["excludedT3CasesTotal"]}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

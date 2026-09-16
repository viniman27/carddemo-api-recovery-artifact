#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "campaign-harness-v2" / "src"))

from campaign_harness import UnionBuilder, freeze_suite, load_frozen_suite  # noqa: E402
from suite_adapters import (  # noqa: E402
    ContractSource,
    build_operation_inventory,
    import_t1_preserved_response,
    import_t2_frozen_requests,
    import_t3_external_paths,
    pin_contract_sources,
)


def _default_contracts(cycle_root: Path):
    sources = []
    for arm in ("E1", "E2"):
        for idx in (1, 2, 3):
            sources.append(ContractSource(f"{arm}-{idx}", cycle_root / "collection-01" / f"{arm}-{idx}" / "response-original.txt"))
    sources.append(ContractSource("E3-01-SDD-stage6r3", cycle_root / "P2a" / "openapi-carddemo-stage6r3.yaml"))
    return sources


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def build_preflight(output: Path, cycle_root: Path) -> dict:
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing output directory: {output}")
    output.mkdir(parents=True)

    contracts = _default_contracts(cycle_root)
    pins = pin_contract_sources(contracts)
    inventory = build_operation_inventory(contracts)
    _write_json(output / "contract-pins.json", {"kind": "contract-byte-pins", "contracts": pins})
    _write_json(output / "operation-inventory.json", inventory)

    examples = output / "synthetic-inputs"
    examples.mkdir()
    (examples / "t1-preserved-response.txt").write_text(
        "Synthetic T1 preserved response. No model call was made.\n"
        "```json\n"
        "[\n"
        "  {\"id\": \"nominal\", \"operationId\": \"posting\", \"method\": \"POST\", \"path\": \"/posting\", \"body\": {}} ,\n"
        "  {\"id\": \"omitted-request\"},\n"
        "  {\"id\": \"bad-path\", \"method\": \"POST\", \"path\": \"posting\"}\n"
        "]\n"
        "```\n",
        encoding="utf-8",
    )
    _write_json(examples / "t2-frozen-requests.json", {
        "kind": "synthetic-frozen-requests-not-generated-here",
        "requests": [
            {"id": "absent", "operationId": "posting", "method": "POST", "path": "/posting", "headers": [["X-Dup", "1"], ["X-Dup", "2"]], "body": {"kind": "absent"}},
            {"id": "present-empty", "operationId": "posting", "method": "POST", "path": "/posting", "body": {"kind": "bytes", "base64": ""}},
            {"id": "empty-json-object", "operationId": "posting", "method": "POST", "path": "/posting", "body": {"kind": "json", "value": {}}},
            {"id": "duplicate-empty-json-object", "operationId": "posting", "method": "POST", "path": "/posting", "body": {"kind": "json", "value": {}}},
            {"id": "invalid-relative-path", "operationId": "posting", "method": "POST", "path": "posting", "body": {"kind": "absent"}},
        ],
    })
    _write_json(examples / "t3-external-paths.json", {
        "kind": "synthetic-external-mbt-paths-no-oracle-access",
        "paths": [
            {"id": "mapped-path", "operationId": "posting", "method": "POST", "path": "/posting", "body": {"kind": "json", "value": {}}},
            {"id": "abstract-transition-only", "transitionId": "posting.valid.transaction"},
        ],
    })

    t1, t1_report = import_t1_preserved_response("SYN", examples / "t1-preserved-response.txt", suite_id="T1", default_resource_package_id="synthetic-pkg")
    t2, t2_report = import_t2_frozen_requests("SYN", examples / "t2-frozen-requests.json", suite_id="T2", default_resource_package_id="synthetic-pkg")
    t3, t3_report = import_t3_external_paths("SYN", examples / "t3-external-paths.json", suite_id="T3", default_resource_package_id="synthetic-pkg")
    frozen_dir = output / "frozen-synthetic-suites"
    frozen_paths = [freeze_suite(suite, frozen_dir / f"{suite.suite_id}.json") for suite in (t1, t2, t3)]
    loaded = [load_frozen_suite(path) for path in frozen_paths]
    union, union_ledger = UnionBuilder().build(loaded)
    union_path = freeze_suite(union, frozen_dir / "T4-union.json")
    union_loaded = load_frozen_suite(union_path)

    adapter_report = {
        "kind": "suite-adapters-preflight-v1-report",
        "scope": "preflight only; no AWS generation, no LLM/API business call, no official gate enabled",
        "realContractsRead": len(pins),
        "realOperationsInventoried": inventory["operationCount"],
        "t1": t1_report,
        "t2": t2_report,
        "t3": t3_report,
        "freezeLoadUnion": {
            "frozenSuites": [str(p.relative_to(output)) for p in frozen_paths],
            "unionPath": str(union_path.relative_to(output)),
            "unionCaseCount": len(union_loaded.cases),
            "unionCaseOrder": [case.case_id for case in union_loaded.cases],
            "unionLedger": union_ledger,
        },
        "pending": [
            "T1 outbound package/content approval before any model call",
            "schema mapping for arbitrary T1 response formats beyond explicit JSON objects/lists",
            "official T2 frozen request production is external; this imports only already-frozen requests",
            "T3 business-request mapping from independent MBT paths to each contract surface",
            "operation-specific fixture package mapping and applicability classification",
            "structural/schema checkers for official AWS replay and result interpretation",
            "official runner/gate remains disabled until concrete freeze manifest and human decision",
        ],
        "nonClaims": [
            "not a T1 generator",
            "not a T2 fuzzer/generator",
            "not a T3 business oracle or abstract-id converter",
            "not an AWS campaign runner",
        ],
    }
    _write_json(output / "adapter-preflight-report.json", adapter_report)
    return adapter_report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="P3 suite-adapters-preflight-v1 CLI; preflight only")
    parser.add_argument("--mode", required=True, choices=["preflight"], help="Only preflight is implemented; no official AWS gate")
    parser.add_argument("--output", required=True, help="New output/evidence directory")
    parser.add_argument("--cycle-root", default=str(ROOT.parents[1]), help="aws-carddemo-cycle-v1 root")
    args = parser.parse_args(argv)
    report = build_preflight(Path(args.output), Path(args.cycle_root))
    print(json.dumps({"output": args.output, "realOperationsInventoried": report["realOperationsInventoried"], "unionCaseCount": report["freezeLoadUnion"]["unionCaseCount"], "officialGateEnabled": False}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

THIS = Path(__file__).resolve()
ROOT = THIS.parents[1]
P3 = ROOT.parent

DEFAULT_SEEDS = [104729, 130363, 155921]
DEFAULT_DIRECTIONS = ["positive", "negative"]
TRACK_FIXTURES = {
    "posting": "posting.candidate-v1-physical-v2",
    "interest": "interest.candidate-v1-physical-v2",
    "reporting": "reporting.candidate-v1-physical-v2",
}
OPERATION_TRACK_ALIASES = {
    "posting": "posting",
    "postdailytransactions": "posting",
    "postdailytransaction": "posting",
    "posttransaction": "posting",
    "transactionposting": "posting",
    "transactionpostings": "posting",
    "interest": "interest",
    "generateinteresttransactions": "interest",
    "generateinteresttransaction": "interest",
    "interesttransaction": "interest",
    "interesttransactions": "interest",
    "reporting": "reporting",
    "generatetransactionreport": "reporting",
    "transactionreport": "reporting",
    "transactionreports": "reporting",
}


class PreparationOrchestrationError(Exception):
    pass


def _json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pin_path(path: Path, *, base: Path | None = None) -> dict[str, Any]:
    path = Path(path)
    data = path.read_bytes()
    shown = path
    if base is not None:
        try:
            shown = path.resolve().relative_to(base.resolve().parent)
        except ValueError:
            shown = path
    return {"path": shown.as_posix(), "bytes": len(data), "sha256": _sha256_bytes(data)}


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def effective_seeds(values: list[str] | None) -> list[int]:
    if values is None:
        return list(DEFAULT_SEEDS)
    seeds = [int(x) for x in values]
    if not seeds:
        raise PreparationOrchestrationError("at least one seed is required")
    return seeds


def effective_directions(values: list[str] | None) -> list[str]:
    if values is None:
        return list(DEFAULT_DIRECTIONS)
    directions = [str(x) for x in values]
    bad = [x for x in directions if x not in DEFAULT_DIRECTIONS]
    if bad:
        raise PreparationOrchestrationError(f"unsupported directions: {bad}")
    if not directions:
        raise PreparationOrchestrationError("at least one direction is required")
    return directions


def operation_track(operation: dict[str, Any]) -> str:
    candidates = [operation.get("operationId"), operation.get("path"), operation.get("track")]
    for value in candidates:
        if not value:
            continue
        normalized = "".join(ch for ch in str(value).lower() if ch.isalnum())
        if normalized in OPERATION_TRACK_ALIASES:
            return OPERATION_TRACK_ALIASES[normalized]
        for token, track in (("posting", "posting"), ("post", "posting"), ("interest", "interest"), ("report", "reporting"), ("reporting", "reporting")):
            if token in normalized:
                return track
    raise PreparationOrchestrationError(f"cannot infer track for operation: {operation}")


def fixture_id_for_operation(operation: dict[str, Any], cfg: dict[str, Any]) -> str:
    track = operation_track(operation)
    fixtures = {row.get("track"): row.get("fixtureId") for row in (((cfg.get("fixturesCandidates") or {}).get("fixtures")) or [])}
    fixture = fixtures.get(track) or TRACK_FIXTURES[track]
    if fixture not in TRACK_FIXTURES.values():
        raise PreparationOrchestrationError(f"unexpected fixture id for {track}: {fixture}")
    return str(fixture)


def bind_t2_resource_packages(cases: list[dict[str, Any]], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    bound: list[dict[str, Any]] = []
    for case in cases:
        item = json.loads(json.dumps(case))
        params = item.setdefault("parameters", {})
        op = {"operationId": params.get("operationId") or item.get("operationId"), "path": item.get("path") or params.get("path"), "track": params.get("track")}
        track = operation_track(op)
        item["resourcePackageId"] = fixture_id_for_operation(op, cfg)
        params["track"] = track
        params["fixtureBindingStatus"] = "candidate_not_official"
        params["fixtureBindingAuthority"] = "campaign-config-v2 fixturesCandidates bytes; no oracle promotion"
        bound.append(item)
    return bound


def contracts_summary(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for contract in cfg.get("contracts", {}).get("contracts", []):
        ops = []
        for op in contract.get("operations", []):
            track = operation_track(op)
            ops.append({
                "operationId": op.get("operationId"),
                "method": op.get("method"),
                "path": op.get("path"),
                "track": track,
                "candidateResourcePackageId": TRACK_FIXTURES[track],
                "resourceBindingStatus": "candidate_not_official",
            })
        out.append({"contractId": contract.get("contractId"), "arm": contract.get("arm"), "operations": ops})
    return out


def validate_scope(cfg: dict[str, Any]) -> dict[str, Any]:
    contracts = cfg.get("contracts", {}).get("contracts", [])
    op_total = sum(len(c.get("operations", [])) for c in contracts)
    errors = []
    if len(contracts) != 7 or cfg.get("contracts", {}).get("count") != 7:
        errors.append("expected exactly 7 contracts")
    if op_total != 21 or cfg.get("contracts", {}).get("operationsTotal") != 21:
        errors.append("expected exactly 21 operations")
    return {"ok": not errors, "errors": errors, "contracts": len(contracts), "operations": op_total, "tracks": ["posting", "interest", "reporting"]}


def build_t3_selected_suite_with_explicit_budget(
    enriched: dict[str, Any],
    *,
    p3: Path = P3,
    max_depth: int = 6,
    max_paths_per_track_fixture: int = 50,
):
    """Build the T3 SDD selected suite with an explicit final budget.

    This wrapper intentionally does not rewrite the preserved
    t3-sdd-external-selection-v3 static evidence produced with maxPaths=12.
    It reuses the current v3 selection/migration constants and filtering policy,
    but passes the final budget into the underlying adapter when/if an official
    freeze is authorized later.
    """
    import copy

    t3_root = p3 / "t3-sdd-external-selection-v3"
    adapter_src = p3 / "t3-campaign-adapter-v3" / "src"
    if str(t3_root) not in sys.path:
        sys.path.insert(0, str(t3_root))
    if str(adapter_src) not in sys.path:
        sys.path.insert(0, str(adapter_src))
    import sdd_external_selection as ext  # type: ignore
    from t3_campaign_adapter import Suite, build_t3_suite, resolve_contract_source  # type: ignore

    contract_source = resolve_contract_source(p3, ext.SDD_REGISTRY_ID)
    unfiltered_suite, adapter_report = build_t3_suite(
        ext.SDD_REGISTRY_ID,
        p3 / "reference-executable-v4" / "model.json",
        enriched,
        p3 / "fixture-materialization-v2" / "package" / "manifest.json",
        contract_source,
        capabilities=["CBTRN02C_POSTTRAN", "CBACT04C_INTCALC", "CBTRN03C_TRANREPT"],
        max_depth=int(max_depth),
        max_paths_per_capability=int(max_paths_per_track_fixture),
    )
    restrictions = {
        cell["cellId"]: ext.effective_transition_restriction(cell)
        for cell in enriched.get("cells", [])
        if cell.get("contractId") == ext.SDD_REGISTRY_ID and cell.get("executableEligible") is True
    }
    selected_cases = []
    excluded = []
    for case in unfiltered_suite.cases:
        cell_ref = case.parameters.get("cellRef")
        transition_id = str(case.parameters.get("transitionId"))
        allowed = restrictions.get(cell_ref)
        if allowed is None or transition_id in allowed:
            selected_cases.append(case)
        else:
            excluded.append({
                "caseId": case.case_id,
                "cellRef": cell_ref,
                "transitionId": transition_id,
                "restriction": "explicit_empty_effective_selectable_transitions" if not allowed else "not_in_declared_effective_selectable_transitions",
            })
    excluded.sort(key=lambda x: (str(x["cellRef"]), str(x["transitionId"]), str(x["caseId"])))
    report = copy.deepcopy(adapter_report)
    report.update({
        "kind": "preparation-orchestration-v1-t3-explicit-budget-selected-suite-report",
        "budget": {"maxDepth": int(max_depth), "maxPathsPerTrackFixture": int(max_paths_per_track_fixture)},
        "acceptedCount": len(selected_cases),
        "unfilteredAcceptedCount": len(unfiltered_suite.cases),
        "excludedCount": len(excluded),
        "excludedByEffectiveSelection": excluded,
        "officialCampaign": False,
        "officialSuiteGenerated": False,
    })
    return Suite("T3", selected_cases), report


def build_preparation_plan(
    cfg: dict[str, Any],
    *,
    seeds: list[int] | None = None,
    directions: list[str] | None = None,
    t3_max_depth: int = 6,
    t3_max_paths_per_track_fixture: int = 50,
) -> dict[str, Any]:
    seeds = list(DEFAULT_SEEDS if seeds is None else seeds)
    directions = list(DEFAULT_DIRECTIONS if directions is None else directions)
    scope = validate_scope(cfg)
    return {
        "kind": "aws-carddemo-preparation-orchestration-v1-static-dry-run",
        "status": "local_preparation_only_not_campaign_release",
        "officialCampaign": False,
        "networkAllowed": False,
        "scope": {"contracts": scope["contracts"], "operations": scope["operations"], "tracks": scope["tracks"]},
        "authorization": {
            "campaignAuthorized": bool((cfg.get("authorization") or {}).get("campaignAuthorized")) is True,
            "officialCampaignsStarted": bool((cfg.get("authorization") or {}).get("officialCampaignsStarted")) is True,
            "externalT1SendAuthorized": bool((cfg.get("authorization") or {}).get("externalT1SendAuthorized")) is True,
        },
        "T2": {
            "entrypoint": "P3/t2-offline-preparation-v4/src/t2_offline_bridge.py::generate_t2_offline_suite_for_contract",
            "cliWrapper": "P3/preparation-orchestration-v1/orchestration_cli.py",
            "seeds": seeds,
            "directions": directions,
            "perOperationPerSeed": {"positive": 50, "negative": 50, "total": 100},
            "operationFixturePolicy": "per-operation candidate fixture binding; placeholder resource ids are forbidden",
            "schemaPolicy": "read pinned original OpenAPI by contractId; never synthesize schemas from registry rows; missing body is distinct from empty body and JSON {}",
            "generationStatus": "not_run_by_static_dry_run",
        },
        "T3": {
            "entrypoint": "P3/t3-sdd-external-selection-v3/sdd_external_selection.py::build_selected_t3_suite",
            "explicitBudgetWrapper": "P3/preparation-orchestration-v1/src/preparation_orchestration.py::build_t3_selected_suite_with_explicit_budget",
            "budget": {"maxDepth": int(t3_max_depth), "maxPathsPerTrackFixture": int(t3_max_paths_per_track_fixture)},
            "preservedStaticEvidence": {"maxDepth": 6, "maxPathsPerCapability": 12, "realSuiteCases": 65},
            "currentSelection": "t3-sdd-external-selection-v3; 18 selected / 7 blocked / 25 total SDD obligations; 65 static selected cases under preserved maxPaths=12 evidence",
            "officialSuiteGenerated": False,
            "runtimeExecuted": False,
        },
        "T4": {
            "unionOrder": ["T1", "T2", "T3"],
            "status": "blocked_until_official_T1_T2_T3_suites_are_frozen",
            "freshExecution": True,
            "independentReplica": False,
        },
        "contracts": contracts_summary(cfg),
        "blockers": [
            "T1 still awaits separate explicit send/freeze path; do not touch the parallel T1 worktree/task here.",
            "Candidate fixture bytes need human promotion before official suites; technical binding creates no oracle authority.",
            "Official AWS generation/freeze/campaign remains gate-closed after this local preparation.",
        ],
    }


def build_consolidated_candidate_config(cfg: dict[str, Any], p3: Path = P3) -> dict[str, Any]:
    p3 = Path(p3)
    pin_rel = [
        "campaign-configuration-v2/campaign-config-v2.json",
        "t2-offline-preparation-v4/src/t2_offline_bridge.py",
        "t2-offline-preparation-v4/t2_offline_cli.py",
        "t3-sdd-external-selection-v3/sdd_external_selection.py",
        "t3-sdd-external-selection-v3/integrated-mapping.sdd-external-selection-v3.json",
        "t3-sdd-external-selection-v3/external-selection-plan.json",
        "t3-sdd-external-selection-v3/selected-suite-real.json",
        "fixture-materialization-v2/package/manifest.json",
        "reference-executable-v4/model.json",
    ]
    plan = build_preparation_plan(cfg)
    return {
        "kind": "aws-carddemo-preparation-orchestration-v1-consolidated-candidate-config",
        "status": "local_preparation_candidate_not_campaign_release",
        "baseConfiguration": "P3/campaign-configuration-v2/campaign-config-v2.json",
        "pins": [pin_path(p3 / rel, base=p3) for rel in pin_rel if (p3 / rel).exists()],
        "scope": plan["scope"],
        "candidateEntrypoints": {
            "T2": "P3/t2-offline-preparation-v4/src/t2_offline_bridge.py::generate_t2_offline_suite_for_contract",
            "T3_SDD": "P3/t3-sdd-external-selection-v3/sdd_external_selection.py::build_selected_t3_suite",
            "orchestration": "P3/preparation-orchestration-v1/src/preparation_orchestration.py",
            "harness": "P3/campaign-harness-v3",
        },
        "budgets": {"T2": plan["T2"]["perOperationPerSeed"], "T3": plan["T3"]["budget"], "T1": {"maxScenariosPerOperation": 12}},
        "seeds": DEFAULT_SEEDS,
        "order": ["contract replica", "zero-shot/few-shot/SDD", "T1/T2/T3/T4", "posting/interest/reporting", "fixture ID", "case ID"],
        "resourceResetPolicy": "verified new workdir before every application; compare effective resource hashes per application, not only process restart",
        "errorPolicy": {"noNetworkInPreparation": True, "noOfficialFreeze": True, "failClosedOnPinMismatch": True, "preservePartialArtifacts": True, "noOraclePromotionFromFixtures": True},
        "promotionFreezeProcedure": [
            "Present this local preparation closure and blockers to Researcher.",
            "Obtain explicit human fixture promotion by exact manifest bytes/hash; record that this is fixture authority only, not expected-output oracle authority.",
            "Obtain explicit T1 send/freeze decision from the separate T1 track; preserve exact receipts before import.",
            "Generate/freeze T2 using pinned t2-offline-preparation-v4 and per-operation fixture binding; preserve original OpenAPI pins and request bytes.",
            "Generate/freeze T3 using t3-sdd-external-selection-v3 with explicit final budget maxDepth=6/maxPathsPerTrackFixture=50; retain old static maxPaths=12 evidence as historical evidence, not overwritten proof.",
            "Only after T1/T2/T3 official suites exist, build dependent T4 union in order T1,T2,T3 and request explicit campaign/replay authorization.",
        ],
        "authorization": plan["authorization"],
        "contracts": plan["contracts"],
        "blockers": plan["blockers"],
    }


def write_static_dry_run(
    cfg: dict[str, Any],
    out: Path,
    *,
    seeds: list[int] | None = None,
    directions: list[str] | None = None,
    t3_max_paths_per_track_fixture: int = 50,
) -> dict[str, Any]:
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise PreparationOrchestrationError(f"refusing to overwrite non-empty output directory: {out}")
    out.mkdir(parents=True, exist_ok=True)
    report = build_preparation_plan(cfg, seeds=seeds, directions=directions, t3_max_paths_per_track_fixture=t3_max_paths_per_track_fixture)
    config = build_consolidated_candidate_config(cfg, P3)
    (out / "STATIC-DRY-RUN.json").write_bytes(_json_bytes(report))
    (out / "CONSOLIDATED-CANDIDATE-CONFIG.json").write_bytes(_json_bytes(config))
    (out / "PROMOTION-FREEZE-PROCEDURE.md").write_text(promotion_freeze_markdown(config), encoding="utf-8")
    return report


def promotion_freeze_markdown(config: dict[str, Any]) -> str:
    lines = [
        "# AWS CardDemo P3 local preparation closure — promotion/freeze procedure",
        "",
        "Status: local preparation candidate only. No official campaign, AWS generation, freeze, replay, or external T1 send is authorized by this file.",
        "",
        "## Pinned entrypoints",
    ]
    for key, value in config["candidateEntrypoints"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Procedure"])
    for idx, step in enumerate(config["promotionFreezeProcedure"], 1):
        lines.append(f"{idx}. {step}")
    lines.extend(["", "## Remaining blockers"])
    for blocker in config["blockers"]:
        lines.append(f"- {blocker}")
    lines.extend(["", "## Provenance note", "Preparation deterministically pins contracts, fixture bytes, budgets, seeds, order, reset and error policy. Promotion of fixtures, T1 provider sending, oracle authority, and official campaign execution remain human/model-judgment gates.", ""])
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="AWS CardDemo local preparation orchestration v1; official campaign gate closed")
    sub = ap.add_subparsers(dest="command", required=True)
    dry = sub.add_parser("dry-run")
    dry.add_argument("--config", required=True)
    dry.add_argument("--output", required=True)
    dry.add_argument("--seed", action="append", default=None)
    dry.add_argument("--direction", action="append", choices=DEFAULT_DIRECTIONS, default=None)
    dry.add_argument("--t3-max-depth", type=int, default=6)
    dry.add_argument("--t3-max-paths-per-track-fixture", type=int, default=50)
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = parse_args(argv)
    cfg = load_config(Path(ns.config))
    if ns.command == "dry-run":
        report = write_static_dry_run(
            cfg,
            Path(ns.output),
            seeds=effective_seeds(ns.seed),
            directions=effective_directions(ns.direction),
            t3_max_paths_per_track_fixture=ns.t3_max_paths_per_track_fixture,
        )
        print(json.dumps({"status": report["status"], "scope": report["scope"], "output": str(Path(ns.output).resolve()), "officialCampaign": False}, indent=2, sort_keys=True, ensure_ascii=False))
        return 0 if validate_scope(cfg)["ok"] else 1
    raise PreparationOrchestrationError(f"unknown command: {ns.command}")


if __name__ == "__main__":
    raise SystemExit(main())

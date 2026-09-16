#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from suite_generation import (  # noqa: E402
    build_t1_outbound_package,
    freeze_load_union,
    generate_t2_schemathesis_suite,
    generate_t3_bfs_suite,
    import_t1_preserved_response,
    import_t2_frozen_suite,
    module_evidence,
)


def _write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def run_synthetic_preparation(out: Path) -> dict:
    if out.exists():
        raise SystemExit(f"refusing to overwrite existing output directory: {out}")
    out.mkdir(parents=True)
    # Write the schema first via T2, then package it for T1 without any provider call.
    t2_report = generate_t2_schemathesis_suite("SYNTH", out / "synthetic-openapi.json", out / "t2", seeds=[104729], directions=["positive", "negative"], max_examples_per_direction=6, qualification_max_examples_per_direction=3)
    t1_pkg = build_t1_outbound_package(
        contract_id="SYNTH",
        contract_path=out / "synthetic-openapi.json",
        output_dir=out / "t1-outbound",
        common_instruction="Synthetic preparation only. Return JSON scenarios with concrete method/path/body only when supported; leave unsupported parameters pending.",
        supported_parameters={"temperature": {"status": "pending_approval"}, "max_output_tokens": {"status": "pending_approval"}, "seed": {"status": "pending_approval"}},
    )
    t1_response = out / "synthetic-inputs" / "t1-preserved-response.txt"
    t1_response.parent.mkdir()
    t1_response.write_text("Synthetic preserved response; no provider call.\n" + json.dumps({"scenarios": [{"id": "ok", "method": "POST", "path": "/synthetic", "body": {}}, {"id": "abstract-only", "obligation": "SYNTH-OBL"}]}, indent=2), encoding="utf-8")
    t1, t1_import = import_t1_preserved_response("SYNTH", t1_response)
    t2, t2_import = import_t2_frozen_suite("SYNTH", out / "t2" / "frozen-synthetic3.1-requests.json")
    model = out / "synthetic-inputs" / "t3-model.json"
    mapping = out / "synthetic-inputs" / "t3-mapping.json"
    model.write_text(json.dumps({"kind": "synthetic-model", "capabilities": [{"id": "SYNTH", "initialState": "S0", "states": [{"id": "S0"}, {"id": "S1"}, {"id": "S2"}], "variables": {"flag": {"initial": False, "domain": [False, True], "type": "bool"}}, "transitions": [{"id": "A", "from": "S0", "to": "S1", "guard": {"op": "true"}, "effects": []}, {"id": "B", "from": "S1", "to": "S2", "guard": {"op": "eq", "left": {"var": "flag"}, "right": {"value": True}}, "effects": []}, {"id": "C", "from": "S0", "to": "S2", "guard": {"op": "not_supported"}, "effects": []}]}]}, indent=2), encoding="utf-8")
    mapping.write_text(json.dumps({"allowed": {"A": {"method": "POST", "path": "/synthetic", "body": {}}}, "guardSensitive": {"B": {"requiresVariant": True, "supported": False}}, "abstractOnly": {"C": {"reason": "synthetic no concrete mapping"}}}, indent=2), encoding="utf-8")
    t3, t3_report = generate_t3_bfs_suite("SYNTH", model, mapping, max_depth=4, max_paths=10)
    union, union_report = freeze_load_union([t1, t2, t3], out / "freeze-load-union")
    report = {
        "kind": "suite-generation-preflight-v1-synthetic-report",
        "officialCampaign": False,
        "scope": "synthetic/preparation only; no AWS HTTP, no LLM provider call, no official T1/T2/T3 cases",
        "moduleEvidence": module_evidence(),
        "t1Outbound": {"path": str(out / "t1-outbound" / "t1-outbound-package.json"), "providerCalled": t1_pkg["providerCalled"], "modelAvailability": t1_pkg["modelAvailability"], "externalPackageStatus": t1_pkg["externalPackageStatus"]},
        "t1Import": t1_import,
        "t2Generation": t2_report,
        "t2Import": t2_import,
        "t3Generation": t3_report,
        "union": union_report,
        "counts": {"T1": len(t1.cases), "T2": len(t2.cases), "T3": len(t3.cases), "T4": len(union.cases)},
        "gateClosedFutureOfficialInstructions": ["Obtain explicit human approval before external T1 package submission or provider call.", "Pin authorized model/transport and probe supported parameters only when approved; until then status remains pending approval/not_probed.", "Use official AWS contracts/fixtures only after campaign gate approval; this CLI intentionally has no official generation mode.", "Do not promote synthetic preparation, Schemathesis qualification, or union smoke to official T1/T2/T3/T4 evidence."],
        "remainingForCampaign": ["approved external T1 package/model/transport", "official fixtures/resource authority", "official T2 budgets and no-extra-replay runner against approved contracts", "reviewed independent reference model/mapping variants", "campaign authorization and execution harness run"],
    }
    _write(out / "preflight-report.json", report)
    (out / "FUTURE-OFFICIAL-GATECLOSED.md").write_text("# Future official instructions — gate closed\n\n- External/T1 package status: pending approval.\n- No model availability or parameter support is claimed until an approved probe/call occurs.\n- This CLI is synthetic/preparation only and must not generate official cases.\n", encoding="utf-8")
    return {"output": str(out), "officialCampaign": False, "counts": report["counts"], "moduleEvidence": report["moduleEvidence"], "report": str(out / "preflight-report.json")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="suite-generation-preflight-v1 synthetic/preparation CLI only")
    sub = ap.add_subparsers(dest="command", required=True)
    s = sub.add_parser("synthetic-preparation")
    s.add_argument("--output", required=True)
    o = sub.add_parser("official")
    o.add_argument("--output", required=True)
    ns = ap.parse_args(argv)
    if ns.command == "official":
        print("official generation is gate-closed; use only synthetic-preparation in this preflight", file=sys.stderr)
        return 2
    summary = run_synthetic_preparation(Path(ns.output).resolve())
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

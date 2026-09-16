#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from t2_offline_bridge import (  # noqa: E402
    build_plan,
    generate_t2_offline_suite_for_contract,
    load_current_config,
)


def _write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def cmd_dry_run(ns: argparse.Namespace) -> int:
    out = Path(ns.output).resolve()
    if out.exists():
        print(f"refusing to overwrite existing output directory: {out}", file=sys.stderr)
        return 2
    out.mkdir(parents=True)
    cfg = load_current_config(Path(ns.config))
    plan = build_plan(cfg, max_examples_per_direction=50)
    _write(out / "plan.json", plan)
    print(json.dumps({
        "output": str(out),
        "officialCampaign": False,
        "registryValidation": plan["registryValidation"],
        "policy": plan["policy"],
        "planPath": str(out / "plan.json"),
        "blockedOfficialRelease": True,
    }, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if plan["registryValidation"]["ok"] else 1


def cmd_synthetic_contract_generate(ns: argparse.Namespace) -> int:
    cfg = load_current_config(Path(ns.config))
    report = generate_t2_offline_suite_for_contract(
        cfg,
        ns.contract_id,
        Path(ns.output).resolve(),
        seeds=[int(x) for x in ns.seed],
        directions=list(ns.direction),
        max_examples_per_direction=int(ns.max_examples_per_direction),
    )
    print(json.dumps({"officialCampaign": False, "contractId": report["contractId"], "requestOccurrences": report["requestOccurrences"], "reportPath": str(Path(ns.output).resolve() / "generation-report.json")}, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report.get("success") else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="T2 offline preparation v3; no network, no campaign, official release gate closed")
    sub = ap.add_subparsers(dest="command", required=True)
    dry = sub.add_parser("dry-run")
    dry.add_argument("--config", required=True)
    dry.add_argument("--output", required=True)
    dry.set_defaults(func=cmd_dry_run)
    synth = sub.add_parser("synthetic-contract-generate", help="local qualification against a provided config/contractId only; not official AWS release")
    synth.add_argument("--config", required=True)
    synth.add_argument("--contract-id", required=True)
    synth.add_argument("--output", required=True)
    synth.add_argument("--seed", action="append", default=["104729"])
    synth.add_argument("--direction", action="append", choices=["positive", "negative"], default=["positive", "negative"])
    synth.add_argument("--max-examples-per-direction", type=int, default=4)
    synth.set_defaults(func=cmd_synthetic_contract_generate)
    official = sub.add_parser("official-generate")
    official.add_argument("--config", required=True)
    official.add_argument("--output", required=True)
    ns = ap.parse_args(argv)
    if ns.command == "official-generate":
        print("official release is gate-closed in t2-offline-preparation-v3; no official T2 generation/campaign is available in this resumed task", file=sys.stderr)
        return 2
    return ns.func(ns)


if __name__ == "__main__":
    raise SystemExit(main())

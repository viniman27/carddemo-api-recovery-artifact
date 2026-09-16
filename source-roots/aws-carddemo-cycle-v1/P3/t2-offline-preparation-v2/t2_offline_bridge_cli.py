#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from t2_offline_bridge import DEFAULT_SEEDS, build_plan, generate_synthetic_t2_suite, load_current_config, validate_current_registry  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    default_cycle = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="AWS CardDemo T2 offline candidate bridge (no network, no official campaign).")
    parser.add_argument("--config", type=Path, default=default_cycle / "campaign-configuration-v2" / "campaign-config-v2.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true", help="write plan.json only; this is the default-safe mode")
    parser.add_argument("--generate-synthetic", action="store_true", help="generate synthetic OpenAPI fixture requests and import/freeze them locally; not official AWS freeze")
    parser.add_argument("--max-examples-per-direction", type=int, default=50)
    parser.add_argument("--seeds", default=",".join(str(x) for x in DEFAULT_SEEDS), help="comma-separated integer seeds")
    args = parser.parse_args(argv)

    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    cfg = load_current_config(args.config)
    plan = build_plan(cfg, max_examples_per_direction=args.max_examples_per_direction, seeds=seeds)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    registry = validate_current_registry(cfg)
    if not registry["ok"]:
        print(json.dumps({"ok": False, "stage": "registry", "planPath": str(args.output_dir / "plan.json"), "errors": registry["errors"]}, indent=2, ensure_ascii=False))
        return 2

    if args.generate_synthetic:
        report = generate_synthetic_t2_suite(cfg["contracts"]["contracts"], args.output_dir, seeds=seeds, max_examples_per_direction=args.max_examples_per_direction)
        print(json.dumps({"ok": True, "dryRun": False, "officialCampaign": False, "planPath": str(args.output_dir / "plan.json"), "generationReportPath": str(args.output_dir / "generation-report.json"), "requestOccurrences": report["requestOccurrences"]}, indent=2, ensure_ascii=False))
        return 0

    print(json.dumps({"ok": True, "dryRun": True, "officialCampaign": False, "planPath": str(args.output_dir / "plan.json"), "contracts": plan["contracts"], "operations": plan["operations"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

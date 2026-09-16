#!/usr/bin/env python3
"""Fail-closed CLI for the synthetic pre-campaign harness.

This entry point intentionally has no AWS campaign runner. JSON labels such as
approved_frozen or approved_campaign_execution are not authority to run an
official campaign.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synthetic-only P3 campaign harness qualification CLI")
    parser.add_argument("--mode", required=True, help="Only synthetic-qualification is accepted in this delivery")
    parser.add_argument("--config", help="Optional config path; labels never authorize official AWS execution")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.mode != "synthetic-qualification":
        if args.config:
            try:
                json.loads(Path(args.config).read_text(encoding="utf-8"))
            except Exception:
                pass
        print("official AWS campaign execution is not implemented; this CLI accepts only synthetic-qualification", file=sys.stderr)
        return 2
    print("synthetic qualification mode selected; no AWS campaign runner is available")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

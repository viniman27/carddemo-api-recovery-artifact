from __future__ import annotations

import argparse
import json
from pathlib import Path

from .fixtures import load_fixture
from .runner import run_fixture_checks
from .source_catalog import load_default_catalog


def main() -> int:
    parser = argparse.ArgumentParser(description="Run source-grounded semantic checkers on a fixture JSON file.")
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--verify-source", action="store_true")
    args = parser.parse_args()

    if args.verify_source:
        verification = load_default_catalog().verify_source_anchors()
        if verification.failures:
            print(json.dumps({"sourceVerification": verification.__dict__}, indent=2, ensure_ascii=False))
            return 2

    fixture = load_fixture(args.fixture)
    payload = {
        "fixtureId": fixture.fixture_id,
        "results": [result.to_json_dict() for result in run_fixture_checks(fixture)],
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

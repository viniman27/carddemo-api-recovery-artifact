#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from t3_mapper import (  # noqa: E402
    FixtureIndex,
    build_request_from_explicit_mapping,
    bfs_map_model_to_suite,
    compatibility_inventory,
    freeze_load_synthetic,
    freeze_load_union_synthetic,
)
from campaign_harness import Case, Expectation, HttpRequestSpec, Suite  # noqa: E402


def _write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _synthetic_openapi() -> dict:
    return {
        "openapi": "3.1.0",
        "info": {"title": "Synthetic T3 mapper qualification; NOT CardDemo", "version": "1"},
        "paths": {
            "/synthetic": {"post": {"operationId": "syntheticPost", "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "required": ["payload", "name"], "additionalProperties": False, "properties": {"payload": {"type": "string"}, "name": {"type": "string"}}}}}}, "responses": {"200": {"description": "ok"}, "400": {"description": "bad"}}}},
            "/sdd": {"post": {"operationId": "sdd", "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "properties": {}, "additionalProperties": False}}}}, "responses": {"200": {"description": "ok"}}}},
        },
    }


def cmd_synthetic(args: argparse.Namespace) -> int:
    out = Path(args.output)
    if out.exists():
        raise SystemExit(f"refusing to overwrite output: {out}")
    out.mkdir(parents=True)
    fixture_root = out / "fixture-a"
    fixture_root.mkdir()
    (fixture_root / "PAYLOAD.bin").write_bytes(b"abc")
    schema = _synthetic_openapi()
    schema_path = out / "synthetic-openapi.json"
    _write(schema_path, schema)
    model = {"capabilities": [{"id": "SYNTH", "initialState": "S0", "transitions": [{"id": "A", "from": "S0", "to": "S1"}, {"id": "B", "from": "S1", "to": "S2"}, {"id": "C", "from": "S0", "to": "S3"}]}]}
    model_path = out / "synthetic-model.json"
    _write(model_path, model)
    fixtures = {"fixtures": [{"fixtureId": "fixture-a", "track": "synthetic", "packagePath": str(fixture_root), "resources": [{"dd": "PAYLOAD", "bytes": 3, "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"}], "bindings": {"PAYLOAD": "PAYLOAD.bin"}}]}
    fixtures_path = out / "synthetic-fixtures.json"
    _write(fixtures_path, fixtures)
    mappings = {"cells": [
        {"cellId": "A", "transitionId": "A", "operation": {"method": "post", "path": "/synthetic"}, "fixtureSelection": {"fixtureId": "fixture-a"}, "requestBody": {"payload": {"fromBytes": "PAYLOAD", "encoding": "base64"}, "name": {"literal": "ok"}}},
        {"cellId": "B", "transitionId": "B", "operation": {"method": "post", "path": "/sdd"}, "requestBody": {}, "sddConstantEmptyObject": True},
        {"cellId": "C", "transitionId": "C", "blocked_reason": "synthetic abstract-only transition has no concrete evidence"},
    ]}
    mappings_path = out / "synthetic-mapping.json"
    _write(mappings_path, mappings)
    suite, report = bfs_map_model_to_suite("SYNTH", model_path, mappings_path, fixtures_path, schema_path)
    _write(out / "t3-mapper-report.json", report)
    loaded, freeze = freeze_load_synthetic(suite, out / "freeze")
    # synthetic end-to-end union path without T1/T2 official material
    t1 = Suite("T1", [Case("T1-synth", "T1", "synthetic", HttpRequestSpec("POST", "/synthetic", (("content-type", "application/json"),), "json", "eyJwYXlsb2FkIjoiWVdKaiIsIm5hbWUiOiJvayJ9"), "synthetic", Expectation("status", {"status": [200, 400]}))])
    t2 = Suite("T2", [])
    _, union = freeze_load_union_synthetic([t1, t2, loaded], out / "freeze-union")
    summary = {"kind": "t3-synthetic-preparation-summary", "officialCampaign": False, "acceptedCount": report["acceptedCount"], "blockedCount": report["blockedCount"], "freeze": freeze, "union": union, "output": str(out)}
    _write(out / "preparation-summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


def cmd_inventory(args: argparse.Namespace) -> int:
    matrix = json.loads(Path(args.matrix).read_text(encoding="utf-8"))
    inv = compatibility_inventory(matrix)
    if args.output:
        _write(Path(args.output), inv)
    print(json.dumps(inv, sort_keys=True))
    return 0


def cmd_map(args: argparse.Namespace) -> int:
    suite, report = bfs_map_model_to_suite(args.contract_id, Path(args.model), Path(args.mapping), Path(args.fixtures), Path(args.schema), max_depth=args.max_depth, max_paths=args.max_paths)
    out = Path(args.output)
    if out.exists():
        raise SystemExit(f"refusing to overwrite output: {out}")
    out.mkdir(parents=True)
    _write(out / "t3-mapper-report.json", report)
    loaded, freeze = freeze_load_synthetic(suite, out / "freeze")
    summary = {"kind": "t3-map-summary", "officialCampaign": False, "acceptedCount": report["acceptedCount"], "blockedCount": report["blockedCount"], "freeze": freeze, "caseCount": len(loaded.cases)}
    _write(out / "preparation-summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T3 mapper preparation/synthetic only")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("synthetic")
    p.add_argument("--output", required=True)
    p.set_defaults(func=cmd_synthetic)
    p = sub.add_parser("inventory")
    p.add_argument("--matrix", required=True)
    p.add_argument("--output")
    p.set_defaults(func=cmd_inventory)
    p = sub.add_parser("map")
    p.add_argument("--contract-id", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--mapping", required=True)
    p.add_argument("--fixtures", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--max-depth", type=int, default=8)
    p.add_argument("--max-paths", type=int, default=50)
    p.set_defaults(func=cmd_map)
    p = sub.add_parser("official")
    p.add_argument("--output")
    p.set_defaults(func=lambda args: (_ for _ in ()).throw(SystemExit("official T3 generation is gate-closed; use synthetic/map/inventory preparation only")))
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

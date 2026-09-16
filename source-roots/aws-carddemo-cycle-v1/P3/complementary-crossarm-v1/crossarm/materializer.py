from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, RefResolver

ROOT = Path(__file__).resolve().parents[3]
P3 = ROOT / "P3"
HARNESS = P3 / "campaign-harness-v3" / "src"
if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))

from campaign_harness import Case, Expectation, HttpRequestSpec, Suite, freeze_suite  # noqa: E402

TRACK_BY_OPERATION = {
    "postDailyTransactions": "posting",
    "generateInterestTransactions": "interest",
    "generateTransactionReport": "reporting",
    "posting": "posting",
    "interest": "interest",
    "reporting": "reporting",
}
SOURCE_CASE = {
    "posting": "valid-new-tcatbal",
    "interest": "rates-specific-default-zero",
    "reporting": "date-boundaries-in-out-v1",
}
FIXTURE_ID = {
    "posting": "posting.candidate-v1-physical-v2",
    "interest": "interest.candidate-v1-physical-v2",
    "reporting": "reporting.candidate-v1-physical-v2",
}
OBLIGATION_BY_TRACK = {
    "posting": ["POSTTRAN-OBL-003", "POSTTRAN-OBL-009"],
    "interest": ["INTCALC-OBL-005", "INTCALC-OBL-006"],
    "reporting": ["TRANREPT-OBL-002", "TRANREPT-OBL-006"],
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pin_file(path: Path, base: Path, label: str) -> dict[str, Any]:
    path = path.resolve()
    base = base.resolve()
    data = path.read_bytes()
    try:
        rel = str(path.relative_to(base))
    except ValueError:
        # macOS may expose the same path with composed/decomposed Unicode; keep
        # a stable relative display path without weakening absolute hash pins.
        rel = os.path.relpath(str(path), str(base))
    return {"label": label, "path": rel, "absolutePath": str(path), "bytes": len(data), "sha256": sha256_bytes(data)}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_openapi(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if isinstance(data, dict) and isinstance(data.get("text"), str):
        return yaml.safe_load(data["text"])
    return data


def campaign_config(cycle_root: Path) -> dict[str, Any]:
    return load_json(cycle_root / "P3/campaign-configuration-v2/campaign-config-v2.json")


def contract_rows(cycle_root: Path) -> list[dict[str, Any]]:
    rows = campaign_config(cycle_root)["contracts"]["contracts"]
    if len(rows) != 7 or sum(int(r["operationCount"]) for r in rows) != 21:
        raise ValueError("campaign config must declare exactly 7 contracts / 21 operations")
    return rows


def _operation(spec: dict[str, Any], track: str) -> tuple[str, str, dict[str, Any]]:
    for path, item in (spec.get("paths") or {}).items():
        for method, op in item.items():
            if method.lower() not in {"post", "get", "put", "patch", "delete"} or not isinstance(op, dict):
                continue
            if TRACK_BY_OPERATION.get(str(op.get("operationId"))) == track:
                return path, method.upper(), op
    raise KeyError(f"no operation for track {track}")


def _body_b64(body: Any) -> str:
    return base64.b64encode(json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).decode("ascii")


def _suite_by_contract(cycle_root: Path) -> dict[tuple[str, str], dict[str, Any]]:
    suite = load_json(cycle_root / "P3/t3-binding-closure-v1/amended-candidates/T3-BINDING-CLOSURE-V1.json")
    return {(c["parameters"]["contractId"], c["parameters"]["track"]): c for c in suite["cases"]}


def _body_from_case(row: dict[str, Any]) -> dict[str, Any]:
    return json.loads(base64.b64decode(row["request"]["body_b64"]).decode("utf-8"))


def _txn_for_e2_1(tx: dict[str, Any]) -> dict[str, Any]:
    out = dict(tx)
    if isinstance(out.get("categoryCode"), int):
        out["categoryCode"] = f"{out['categoryCode']:04d}"
    if isinstance(out.get("merchantId"), int):
        out["merchantId"] = f"{out['merchantId']:09d}"
    out.pop("filler", None)
    return out


def _body_for_contract(cycle_root: Path, contract_id: str, track: str) -> tuple[dict[str, Any], str]:
    existing = _suite_by_contract(cycle_root)
    if (contract_id, track) in existing:
        return _body_from_case(existing[(contract_id, track)]), "t3-binding-closure-v1-amended-case"
    if contract_id == "E3-SDD-stage6r3":
        return {}, "PublicSDD{}"
    e22 = _body_from_case(existing[("E2-2", track)])
    if contract_id == "E2-1":
        if track == "posting":
            return {"dailyTransactions": [_txn_for_e2_1(t) for t in e22["transactions"]]}, "source-guided-shape-adapted-from-E2-2-essential-fixture"
        if track == "interest":
            return {"transactionIdPrefix": str(e22["parameterDate"])[:10]}, "source-guided-shape-adapted-from-E2-2-essential-fixture"
        if track == "reporting":
            return {"transactions": [_txn_for_e2_1(t) for t in e22["transactions"]], "dateParameterRecords": e22["dateParameterRecords"]}, "source-guided-shape-adapted-from-E2-2-essential-fixture"
    if contract_id == "E2-3":
        if track == "posting":
            return {"transactions": e22["transactions"]}, "source-guided-shape-adapted-from-E2-2-essential-fixture"
        if track == "interest":
            return {"transactionIdPrefix": str(e22["parameterDate"])[:10]}, "source-guided-shape-adapted-from-E2-2-essential-fixture"
        if track == "reporting":
            return {"transactions": e22["transactions"], "dateParameterRecords": [r.ljust(80)[:80] for r in e22["dateParameterRecords"]]}, "source-guided-shape-adapted-from-E2-2-essential-fixture"
    raise KeyError((contract_id, track))


def _validate_request(spec: dict[str, Any], operation: dict[str, Any], body: dict[str, Any]) -> list[str]:
    schema = (((operation.get("requestBody") or {}).get("content") or {}).get("application/json") or {}).get("schema")
    if not schema:
        return []
    return [e.message for e in Draft202012Validator(schema, resolver=RefResolver.from_schema(spec)).iter_errors(body)]


def freeze_inputs(cycle_root: Path, out_dir: Path) -> dict[str, Any]:
    cycle_root = cycle_root.resolve()
    rows = contract_rows(cycle_root)
    pins = [pin_file(cycle_root / "P3/campaign-configuration-v2/campaign-config-v2.json", cycle_root, "campaign-config-v2")]
    for row in rows:
        pins.append(pin_file(Path(row["source"]["path"]), cycle_root, f"contract:{row['contractId']}"))
    pins.extend([
        pin_file(cycle_root / "P3/t3-binding-closure-v1/amended-candidates/T3-BINDING-CLOSURE-V1.json", cycle_root, "t3-binding-closure-amended-candidates"),
        pin_file(cycle_root / "P3/complementary-mbt-binding-v1/latest/candidate-registry.json", cycle_root, "complementary-mbt-binding-registry"),
        pin_file(cycle_root / "P3/complementary-runner-binding-v1/runner_binding/binding.py", cycle_root, "runner-binding-v1"),
        pin_file(cycle_root / "P3/aws-campaign-runner-v3/src/aws_campaign_runner.py", cycle_root, "runner-v3"),
        pin_file(cycle_root / "P3/complementary-validation-implementation-v3/semantic_checkers/checkers.py", cycle_root, "checker-v3"),
    ])
    payload = {"kind": "complementary-crossarm-v1-input-freeze", "createdUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"), "contractCount": 7, "operationCount": 21, "pins": pins, "policy": "prospective bounded local cross-arm run; preserve originals; no external network; no old output-as-expected"}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "input-freeze.json").write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def build_crossarm_suite(cycle_root: Path, out_dir: Path) -> tuple[Path, dict[str, Any]]:
    cycle_root = cycle_root.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    frozen = freeze_inputs(cycle_root, out_dir)
    cases: list[Case] = []
    materialized: list[dict[str, Any]] = []
    for row in contract_rows(cycle_root):
        cid = row["contractId"]
        arm = row["arm"]
        spec = load_openapi(Path(row["source"]["path"]))
        for track in ["posting", "interest", "reporting"]:
            path, method, op = _operation(spec, track)
            body, source = _body_for_contract(cycle_root, cid, track)
            validation_errors = _validate_request(spec, op, body)
            if validation_errors:
                raise ValueError(f"request schema invalid for {cid}/{track}: {validation_errors}")
            case_id = f"CROSSARM-{cid}-{track}".replace("/", "-")
            params = {
                "contractId": cid,
                "contractArm": arm,
                "track": track,
                "operationId": op.get("operationId"),
                "contractOperationId": op.get("operationId"),
                "contractPath": path,
                "sourceGuidedComplement": True,
                "sourceCaseId": SOURCE_CASE[track],
                "fixtureId": FIXTURE_ID[track],
                "requestMaterializationSource": source,
                "officialCampaign": False,
                "checkerObligations": OBLIGATION_BY_TRACK[track],
            }
            cases.append(Case(case_id, "P3-COMPLEMENTARY-CROSSARM-V1", "complementary-crossarm-v1", HttpRequestSpec(method, path, (("content-type", "application/json"),), "json", _body_b64(body)), FIXTURE_ID[track], Expectation(f"semantic-checker:{track}", {"status": [200, 400, 500, 503]}), 5.0, params, (), (f"complementary-crossarm-v1:{cid}:{track}",)))
            materialized.append({"caseId": case_id, "contractId": cid, "track": track, "path": path, "operationId": op.get("operationId"), "bodySha256": sha256_bytes(base64.b64decode(cases[-1].request.body_b64 or "")), "source": source})
    suite = Suite("P3-COMPLEMENTARY-CROSSARM-V1", cases)
    suite_path = out_dir / "suite.freeze.json"
    freeze_suite(suite, suite_path)
    manifest = {"kind": "complementary-crossarm-v1-materialization", "createdUtc": frozen["createdUtc"], "summary": {"caseCount": len(cases), "contractCount": 7, "operationCount": 21, "tracks": ["posting", "interest", "reporting"]}, "suite": pin_file(suite_path, cycle_root, "crossarm-suite-freeze"), "inputs": pin_file(out_dir / "input-freeze.json", cycle_root, "crossarm-input-freeze"), "cases": materialized}
    (out_dir / "materialization-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return suite_path, manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("materialize")
    m.add_argument("--cycle-root", type=Path, required=True)
    m.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    if args.cmd == "materialize":
        suite, manifest = build_crossarm_suite(args.cycle_root, args.out)
        print(json.dumps({"ok": True, "suite": str(suite), "cases": manifest["summary"]["caseCount"]}, ensure_ascii=False))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

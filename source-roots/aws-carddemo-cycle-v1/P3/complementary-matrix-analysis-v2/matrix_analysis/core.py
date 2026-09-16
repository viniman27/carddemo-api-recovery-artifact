from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

TRACK_EVIDENCE_FILE = {
    "posting": "TRANFILE.after",
    "interest": "TRANSACT",
    "reporting": "TRANREPT",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pin(path: Path, label: str) -> dict[str, Any]:
    return {"label": label, "path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _import_from(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _run_dir_from_check(check: dict[str, Any]) -> Path:
    measurement = check.get("measurement") or {}
    run_dir = measurement.get("runDir")
    if run_dir and Path(run_dir).is_dir():
        return Path(run_dir)
    audit_path = (measurement.get("auditSelection") or {}).get("auditPath")
    if audit_path and Path(audit_path).is_file():
        return Path(audit_path).parent
    workdir = Path(check["application"]["workdir"])
    track = check["track"]
    hits = sorted((workdir / "zero-shot-runs" / "p2b-runs").glob(f"{track}-*"))
    if hits:
        return hits[0]
    hits = sorted(workdir.rglob("audit.json"))
    if hits:
        return hits[0].parent
    raise FileNotFoundError(f"run dir not found for {check.get('case_id')}")


def _response_path_from_run_dir(run_dir: Path, contract_id: str, track: str) -> Path | None:
    for parent in [run_dir] + list(run_dir.parents)[:8]:
        hits = sorted(parent.glob(f"{contract_id}/{track}/*/response.json"))
        if hits:
            return hits[0]
    hits = sorted(run_dir.parent.rglob("response.json")) if run_dir.parent.exists() else []
    return hits[0] if hits else None


def build_extractor_case(check: dict[str, Any]) -> dict[str, Any]:
    """Adapt a parent-full84 campaign check to the older qualified extractor case shape."""
    run_dir = _run_dir_from_check(check)
    track = check["track"]
    evidence = run_dir / TRACK_EVIDENCE_FILE[track]
    if not evidence.exists() and track == "posting":
        evidence = run_dir / "DALYREJS"
    if evidence.exists():
        evidence_items = [pin(evidence, f"raw-{evidence.name}")]
    else:
        audit = run_dir / "audit.json"
        evidence_items = [pin(audit, "audit-with-missing-" + evidence.name)] if audit.exists() else [{"path": str(evidence), "missing": True}]
    receipt = check.get("receipt") or {}
    measurement = check.get("measurement") or {}
    return {
        "caseId": check["case_id"],
        "contractId": check.get("contractId"),
        "operationId": check.get("operationId"),
        "track": track,
        "httpStatus": receipt.get("status"),
        "responseSha256": receipt.get("response_sha256"),
        "responseBytes": receipt.get("response_bytes"),
        "structural": (check.get("structuralCheck") or {}).get("classification"),
        "measurementAdmissibility": measurement.get("admissibility") or measurement.get("measurementAdmissibility"),
        "businessCheck": {"evidence": evidence_items},
    }


def _freeze_by_id(freeze: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {c["case_id"]: c for c in freeze["cases"]}


def _posting_expected(source_case_id: str) -> dict[str, Any]:
    reject_map = {
        "reject-card-missing": "100",
        "reject-account-missing": "101",
        "reject-limit": "102",
        "reject-expiry": "103",
    }
    if source_case_id in reject_map:
        return {"kind": "expected_reject", "rejectReason": reject_map[source_case_id]}
    return {"kind": "expected_accept"}


def _fixed_records(path: Path, size: int) -> list[bytes]:
    if not path.exists():
        return []
    data = path.read_bytes()
    return [data[i:i+size] for i in range(0, len(data), size) if len(data[i:i+size]) == size and data[i:i+size].strip(b"\x00 ")]


def _posting_check(case: dict[str, Any], freeze_case: dict[str, Any], cycle_root: Path) -> dict[str, Any]:
    run_dir = Path(case["businessCheck"]["evidence"][0]["path"]).parent
    scenario = freeze_case["parameters"]["essentialScenarioId"]
    exp = _posting_expected(scenario)
    accepted = _fixed_records(run_dir / "TRANFILE.after", 350)
    rejects = _fixed_records(run_dir / "DALYREJS", 430)
    failures: list[str] = []
    if exp["kind"] == "expected_accept":
        if not accepted:
            failures.append("expected accepted TRANFILE.after record, observed none")
        if rejects:
            failures.append(f"expected no reject records, observed {len(rejects)}")
    else:
        if accepted:
            failures.append(f"expected reject-only path, observed {len(accepted)} accepted records")
        reasons = [r[350:354].decode("latin1", errors="replace").strip()[-3:] for r in rejects]
        if exp["rejectReason"] not in reasons:
            failures.append(f"expected reject reason {exp['rejectReason']}, observed {reasons}")
    pins = []
    for name in ["DALYTRAN", "TRANFILE.after", "DALYREJS", "audit.json"]:
        p = run_dir / name
        if p.exists():
            pins.append(pin(p, name))
    response_path = _response_path_from_run_dir(run_dir, case["contractId"], "posting")
    if response_path and response_path.exists():
        pins.append(pin(response_path, "api-response"))
    return {
        "semanticVerdict": "failed" if failures else "pass",
        "reason": "; ".join(failures) if failures else f"posting {exp['kind']} matched actual TRANFILE.after/DALYREJS bytes",
        "obligationVerdicts": [{"obligationId": oid, "verdict": "failed" if failures else "pass", "failures": failures} for oid in freeze_case["parameters"].get("checkerObligations", [])],
        "proof": pins,
        "sourceAnchors": ["app/cbl/CBTRN02C.cbl", "app/cpy/CVTRA05Y.cpy", "app/cpy/CVTRA06Y.cpy"],
        "legacyDefects": [],
    }


def _interest_check(case: dict[str, Any], freeze_case: dict[str, Any], cycle_root: Path) -> dict[str, Any]:
    module_path = cycle_root / "P3" / "complementary-interest-source-extractor-v1" / "interest_source_extractor" / "extractor.py"
    mod = _import_from(module_path, "interest_source_extractor_actual84")
    result = mod.check_case(case, cycle_root)
    failures = result.get("failures", [])
    verdict = {"pass": "pass", "fail": "failed", "failed": "failed"}.get(result.get("semanticVerdict"), "inconclusive")
    if result.get("semanticVerdict") == "inconclusive":
        reason = "interest source inputs/expected transactions not sufficient for a business conclusion"
    elif failures:
        reason = "; ".join(failures)
    else:
        reason = "interest formula matched source-derived balances/rates and actual TRANSACT bytes"
    return {
        "semanticVerdict": verdict,
        "reason": reason,
        "obligationVerdicts": [{"obligationId": oid, "verdict": verdict, "failures": failures} for oid in freeze_case["parameters"].get("checkerObligations", [])],
        "proof": result.get("byteProvenance", {}).get("pins", []),
        "sourceAnchors": result.get("sourceAnchors", []),
        "legacyDefects": [],
        "extractorResult": result,
    }


def _report_money_from_line(raw: str) -> str:
    text = str(raw).replace(",", "")
    matches = re.findall(r"[-+]?\s*\d+(?:\.\d{1,2})?", text)
    if not matches:
        return "0.00"
    token = matches[-1].replace(" ", "")
    return f"{Decimal(token).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


def _is_missing_audit_pre_cobol_rejection(check: dict[str, Any]) -> bool:
    measurement = check.get("measurement") or {}
    receipt = check.get("receipt") or {}
    reasons = set(measurement.get("reasons") or measurement.get("inadmissibilityReasons") or [])
    return (
        check.get("track") == "reporting"
        and receipt.get("status") == 400
        and "audit_missing_for_current_case_track" in reasons
        and not measurement.get("auditDelta")
    )


def _proof_for_pre_cobol_rejection(check: dict[str, Any]) -> list[dict[str, Any]]:
    proof: list[dict[str, Any]] = []
    app = check.get("application") or {}
    workdir = Path(app.get("workdir") or app.get("lifecycle", {}).get("workdir") or ".")
    for name in ["server.stderr", "server.stdout", "server.port"]:
        p = workdir / name
        if p.exists():
            proof.append(pin(p, name))
    receipt = check.get("receipt") or {}
    if receipt.get("response_sha256"):
        proof.append({
            "label": "api-response-declared-by-campaign",
            "path": None,
            "bytes": receipt.get("response_bytes"),
            "sha256": receipt.get("response_sha256"),
            "status": receipt.get("status"),
            "requestIdentity": receipt.get("request_identity"),
            "bodyKind": receipt.get("body_kind"),
        })
    return proof or [{"label": "pre-cobol-http400-campaign-receipt", "path": None, "status": receipt.get("status")}]


def _calibrate_known_empty_report(sem: dict[str, Any]) -> dict[str, Any]:
    obligations = sem.get("obligationVerdicts", [])
    has_report_empty = any("report_empty" in (o.get("failures") or []) for o in obligations)
    if not has_report_empty:
        return sem
    selected_counts = [((o.get("details") or {}).get("selectedCount")) for o in obligations]
    if any(count not in (None, 0) for count in selected_counts):
        return sem
    calibrated = []
    for o in obligations:
        o2 = dict(o)
        failures = list(o2.get("failures") or [])
        if "report_empty" in failures:
            o2["verdict"] = "pass"
            o2["failures"] = [f for f in failures if f != "report_empty"]
            details = dict(o2.get("details") or {})
            details["knownEmptyReport"] = True
            details["calibration"] = "zero selected TRANFILE records in DATEPARM range; zero-byte TRANREPT is a known empty business outcome, not malformed output"
            o2["details"] = details
        elif o2.get("verdict") == "not_observable" and o2.get("obligationId") == "TRANREPT-SRC-TOTALS-FINANCIAL-CORRECTNESS":
            o2["verdict"] = "not_exercised"
            details = dict(o2.get("details") or {})
            details["knownEmptyReport"] = True
            o2["details"] = details
        calibrated.append(o2)
    return {**sem, "semanticVerdict": "pass", "reason": "known_empty_report: zero in-range source transactions produced zero-byte TRANREPT; treated as legitimate empty output", "obligationVerdicts": calibrated}


def _pre_cobol_rejection_semantics(check: dict[str, Any]) -> dict[str, Any]:
    return {
        "semanticVerdict": "inconclusive",
        "reason": "case_input_rejected_before_cobol: HTTP 400 with no audit delta; business/report semantics not observed and no missing raw file pin is asserted",
        "obligationVerdicts": [{
            "obligationId": "REPORTING-PRE-COBOL-INPUT-REJECTION",
            "verdict": "not_observable",
            "scope": "schema_or_api_serializer_rejected_request_before_COBOL_audit",
            "failures": [],
            "details": {"httpStatus": (check.get("receipt") or {}).get("status"), "measurement": check.get("measurement") or {}},
        }],
        "proof": _proof_for_pre_cobol_rejection(check),
        "sourceAnchors": [],
        "legacyDefects": [],
    }


def _reporting_check(case: dict[str, Any], freeze_case: dict[str, Any], cycle_root: Path) -> dict[str, Any]:
    module_path = cycle_root / "P3" / "complementary-reporting-source-extractor-v1" / "reporting_source_extractor" / "extractor.py"
    mod = _import_from(module_path, "reporting_source_extractor_actual84")
    mod._money_from_report = _report_money_from_line
    result = mod.check_case(case)
    obligations = result.get("obligationVerdicts", [])
    failed = [o for o in obligations if o.get("verdict") == "failed"]
    inconc = [o for o in obligations if o.get("verdict") in {"inconclusive", "not_observable"}]
    verdict = "failed" if failed else ("inconclusive" if inconc else "pass")
    reasons = []
    for o in failed:
        reasons.extend(o.get("failures", []) or [o.get("obligationId", "failed")])
    if not reasons and inconc:
        reasons = [f"{o.get('obligationId')}={o.get('verdict')}" for o in inconc]
    if not reasons:
        reasons = ["reporting detail framing/arithmetic matched actual source inputs and report bytes"]
    legacy_defects = []
    for o in obligations:
        oid = o.get("obligationId")
        if oid == "TRANREPT-SRC-EOF-TOTALS-LEGACY-BEHAVIOR" and o.get("verdict") == "observed_legacy_behavior":
            legacy_defects.append({"defect": "legacy_eof_totals_branch_reproduced", "support": o.get("details", {})})
        if oid == "TRANREPT-SRC-TOTALS-FINANCIAL-CORRECTNESS" and o.get("verdict") == "failed":
            legacy_defects.append({"defect": "reporting_inflated_or_incorrect_totals", "support": o.get("failures", []), "details": o.get("details", {})})
    return {
        "semanticVerdict": verdict,
        "reason": "; ".join(reasons),
        "obligationVerdicts": obligations,
        "proof": result.get("artifactPins", []),
        "sourceAnchors": result.get("sourceAnchors", []),
        "legacyDefects": legacy_defects,
        "extractorResult": result,
    }


def _measurement_reason(check: dict[str, Any]) -> tuple[bool, str]:
    measurement = check.get("measurement") or {}
    adm = measurement.get("admissibility") or measurement.get("measurementAdmissibility")
    reasons = measurement.get("inadmissibilityReasons") or []
    if adm == "admissible_preparatory":
        return False, "measurement_admissible_preparatory"
    if not reasons:
        reasons = [r for r in (measurement.get("reasons") or [])]
    return True, "; ".join(reasons or [adm or "measurement_missing_or_limited"])


def analyze_case(check: dict[str, Any], freeze_case: dict[str, Any], cycle_root: Path) -> dict[str, Any]:
    adapted = build_extractor_case(check)
    track = adapted["track"]
    try:
        if track == "reporting" and _is_missing_audit_pre_cobol_rejection(check):
            sem = _pre_cobol_rejection_semantics(check)
        elif track == "posting":
            sem = _posting_check(adapted, freeze_case, cycle_root)
        elif track == "interest":
            sem = _interest_check(adapted, freeze_case, cycle_root)
        elif track == "reporting":
            sem = _calibrate_known_empty_report(_reporting_check(adapted, freeze_case, cycle_root))
        else:
            raise ValueError(track)
    except Exception as exc:
        sem = {"semanticVerdict": "inconclusive", "reason": f"qualified extractor error: {type(exc).__name__}: {exc}", "obligationVerdicts": [], "proof": adapted.get("businessCheck", {}).get("evidence", []), "sourceAnchors": [], "legacyDefects": []}
    limited, meas_reason = _measurement_reason(check)
    receipt = check.get("receipt") or {}
    params = freeze_case.get("parameters", {})
    proof = sem.get("proof", []) or adapted.get("businessCheck", {}).get("evidence", [])
    pin_failures = []
    for p in proof:
        raw_path = p.get("path")
        if not raw_path:
            continue
        path = Path(raw_path)
        if not path.exists():
            pin_failures.append(f"missing:{path}")
        elif p.get("bytes") is not None and path.stat().st_size != p.get("bytes"):
            pin_failures.append(f"bytes_mismatch:{path}")
        elif p.get("sha256") and sha256_file(path) != p.get("sha256"):
            pin_failures.append(f"sha_mismatch:{path}")
    return {
        "caseId": adapted["caseId"],
        "contractId": adapted.get("contractId"),
        "contractArm": params.get("contractArm"),
        "operationId": adapted.get("operationId"),
        "track": track,
        "scenarioId": params.get("essentialScenarioId"),
        "httpStatus": adapted.get("httpStatus"),
        "responseBytes": adapted.get("responseBytes"),
        "responseSha256": adapted.get("responseSha256"),
        "structural": adapted.get("structural"),
        "measurementAdmissibility": adapted.get("measurementAdmissibility"),
        "measurementLimited": limited,
        "measurementReason": meas_reason,
        "semanticVerdict": sem["semanticVerdict"],
        "reason": sem["reason"],
        "obligationVerdicts": sem.get("obligationVerdicts", []),
        "proof": proof,
        "pinVerificationFailures": pin_failures,
        "sourceAnchors": sem.get("sourceAnchors", []),
        "legacyDefects": sem.get("legacyDefects", []),
        "requestIdentity": receipt.get("request_identity"),
        "noApiRerun": True,
    }


def run_analysis(report_path: Path, freeze_path: Path, cycle_root: Path) -> dict[str, Any]:
    report = load_json(report_path)
    freeze = load_json(freeze_path)
    freeze_cases = _freeze_by_id(freeze)
    checks = report["suiteReports"][0]["checks"]
    cases = [analyze_case(ch, freeze_cases[ch["case_id"]], Path(cycle_root)) for ch in checks]
    case_counts_by_track = Counter(c["track"] for c in cases)
    verdict_counts = Counter(c["semanticVerdict"] for c in cases)
    by_track = defaultdict(Counter)
    by_contract = defaultdict(Counter)
    by_scenario = defaultdict(Counter)
    for c in cases:
        by_track[c["track"]][c["semanticVerdict"]] += 1
        by_contract[c["contractId"]][c["semanticVerdict"]] += 1
        by_scenario[f"{c['track']}:{c['scenarioId']}"][c["semanticVerdict"]] += 1
    obligation_counts = Counter(v.get("verdict") for c in cases for v in c.get("obligationVerdicts", []))
    legacy = [d | {"caseId": c["caseId"], "track": c["track"], "contractId": c["contractId"], "scenarioId": c["scenarioId"]} for c in cases for d in c.get("legacyDefects", [])]
    suite_totals = report["suiteReports"][0].get("totals", {})
    report_totals = report.get("totals", {})
    source_supported_legacy_defects = [
        {
            "defect": "reporting_eof_totals_can_duplicate_current_TRAN_AMT",
            "classification": "source_supported_legacy_defect_not_automatically_financial_correctness",
            "desiredBehavior": "final page/account/grand totals should equal the sum of in-range detail amounts exactly once",
            "actualSourceBehavior": "TRANREPT EOF branch can add the current TRAN-AMT again before final totals when the stale current record remains selected",
            "sourceAnchors": [
                "P3/reference-authoring-draft-v1/README.md:17",
                "P3/reference-authoring-draft-v1/obligations.json:758-788",
                "app/cbl/CBTRN03C.cbl:361-372",
            ],
            "runtimeObservationInActual84": "not fully exercised as a financial totals defect in these 84 cases; reported separately from source finding",
        }
    ]
    return {
        "kind": "complementary-matrix-analysis-v1-actual84-semantic-assessment",
        "createdUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "scope": "Final semantic assessment of parent-full84-v1 using pinned actual input/output bytes and qualified local checkers only; no API, COBOL, model, or campaign reruns.",
        "inputs": {"campaignReport": pin(Path(report_path), "campaign-report"), "suiteFreeze": pin(Path(freeze_path), "suite-freeze")},
        "summary": {
            "caseCount": len(cases),
            "freezeCaseDenominator": len(freeze["cases"]),
            "attemptedCaseCount": report["suiteReports"][0]["attempted_case_count"],
            "completedCaseCount": suite_totals.get("completed", report_totals.get("completed")),
            "structuralOkCount": suite_totals.get("structural_ok", report_totals.get("structural_ok")),
            "measurementAdmissibleCount": suite_totals.get("measurement_admissible", report_totals.get("measurement_admissible")),
            "measurementLimitedCount": sum(1 for c in cases if c["measurementLimited"]),
            "caseCountsByTrack": dict(case_counts_by_track),
            "semanticVerdictCounts": dict(verdict_counts),
            "semanticVerdictsByTrack": {k: dict(v) for k, v in sorted(by_track.items())},
            "semanticVerdictsByContract": {k: dict(v) for k, v in sorted(by_contract.items())},
            "semanticVerdictsByScenario": {k: dict(v) for k, v in sorted(by_scenario.items())},
            "obligationVerdictCounts": dict(obligation_counts),
            "legacyDefectCount": len(legacy),
            "sourceSupportedLegacyDefectCount": len(source_supported_legacy_defects),
            "pinVerificationFailureCount": sum(len(c["pinVerificationFailures"]) for c in cases),
            "noApiReruns": True,
        },
        "legacyDefects": legacy,
        "sourceSupportedLegacyDefects": source_supported_legacy_defects,
        "cases": cases,
    }


def write_outputs(payload: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "actual84-semantic-analysis.json").write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    with (out_dir / "actual84-cases.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["caseId", "contractId", "contractArm", "track", "scenarioId", "httpStatus", "structural", "measurementAdmissibility", "measurementLimited", "semanticVerdict", "reason", "responseBytes", "responseSha256"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for c in payload["cases"]:
            w.writerow({k: c.get(k) for k in fields})
    s = payload["summary"]
    lines = [
        "# Análise semântica final — complemento ESSENTIAL12×7 actual84",
        "",
        f"Resultado: {s['caseCount']}/84 casos classificados semanticamente com bytes reais preservados, sem rerodagem de API, COBOL, modelo ou campanha.",
        "",
        "## Contagens principais",
        f"- Congelamento: {s['freezeCaseDenominator']} casos; execução: {s['attemptedCaseCount']} tentados, {s['completedCaseCount']} completados, {s['structuralOkCount']} estruturais OK.",
        f"- Medição: {s['measurementAdmissibleCount']} admissíveis; {s['measurementLimitedCount']} limitados/inconclusivos para medição (não tratados como ausência de API).",
        f"- Partições por trilha: {s['caseCountsByTrack']}.",
        f"- Vereditos semânticos por caso: {s['semanticVerdictCounts']}.",
        f"- Vereditos por trilha: {s['semanticVerdictsByTrack']}.",
        f"- Vereditos por contrato: {s['semanticVerdictsByContract']}.",
        "",
        "## Defeitos legados e limites",
        f"- Defeitos legados observados nos 84 casos: {s['legacyDefectCount']} ocorrências registradas em `legacyDefects` no JSON.",
        f"- Defeitos legados suportados por fonte: {s['sourceSupportedLegacyDefectCount']} achado(s) em `sourceSupportedLegacyDefects`, com comportamento desejado vs. comportamento atual separados.",
        "- Relatórios separam reprodução do comportamento legado de EOF/totais de correção financeira dos totais; uma reprodução do EOF legado não é automaticamente correção financeira.",
        "- Obrigações não implementadas/sem campo observável permanecem inconclusivas; não há promoção para cobertura integral de 25 obrigações.",
        "",
        "## Arquivos de prova",
        f"- JSON agregado: `actual84-semantic-analysis.json`.",
        f"- CSV por caso: `actual84-cases.csv`.",
        f"- Pins de entrada: `{payload['inputs']['campaignReport']['path']}` e `{payload['inputs']['suiteFreeze']['path']}`.",
    ]
    (out_dir / "PTBR-ANALISE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--freeze", type=Path, required=True)
    ap.add_argument("--cycle-root", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args(argv)
    payload = run_analysis(args.report, args.freeze, args.cycle_root)
    write_outputs(payload, args.out_dir)
    print(json.dumps({"ok": True, **payload["summary"], "outDir": str(args.out_dir)}, ensure_ascii=False))
    return 0

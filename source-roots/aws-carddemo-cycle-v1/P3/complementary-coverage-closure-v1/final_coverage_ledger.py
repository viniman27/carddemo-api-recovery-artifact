#!/usr/bin/env python3
"""Final defensible coverage/acceptance ledger for AWS CardDemo P3.

Read-only aggregator: consumes saved campaign/semantic/model/gcov artifacts and
writes a machine ledger plus a concise PT-BR report. It does not call APIs, COBOL,
models, quarantine expected outputs, or mutate upstream evidence.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUSES = [
    "covered_checked",
    "failed",
    "inconclusive",
    "not_exercised",
    "unobservable",
    "not_applicable",
]
PASS_WORDS = {"pass", "passed", "ok", "success", "covered_checked", "semantic_pass"}
FAIL_WORDS = {"fail", "failed", "failure", "mismatch", "semantic_fail", "error"}
INCONCLUSIVE_WORDS = {"pending", "inconclusive", "unchecked", "unknown", "partial", "not_implemented"}


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"cannot read JSON {path}: {exc}") from exc


def pin(path: Path) -> dict[str, Any]:
    b = path.read_bytes()
    return {"path": str(path), "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}


def require_saved_evidence_doc(data: dict[str, Any], path: Path, *, kind: str) -> None:
    if kind == "semantic" and not data.get("scope"):
        raise SystemExit(f"semantic evidence {path} is missing required scope; refusing to aggregate ambiguous results")


def norm_status(value: Any) -> str:
    v = str(value or "").strip().lower().replace("-", "_")
    if v in PASS_WORDS or "qualified_observed" in v or v in {"source_grounded", "runtime_observed", "runtime_observed/source_limited"}:
        return "covered_checked"
    if v in FAIL_WORDS or any(word in v for word in ["fail", "wrong", "mismatch"]):
        return "failed"
    if v in {"unobservable", "not_observable", "not_observed"}:
        return "unobservable"
    if v in {"not_applicable", "n/a", "na"}:
        return "not_applicable"
    if v in INCONCLUSIVE_WORDS or any(word in v for word in ["pending", "inconclusive", "unchecked"]):
        return "inconclusive"
    return "inconclusive"


def stronger(a: str, b: str) -> str:
    order = {"failed": 5, "covered_checked": 4, "inconclusive": 3, "unobservable": 2, "not_exercised": 1, "not_applicable": 0}
    return a if order.get(a, 0) >= order.get(b, 0) else b


def partitions_from(value: Any) -> list[str]:
    out: list[str] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                out.append(str(item.get("id") or item.get("partition") or item.get("name") or item.get("caseId") or item))
    elif isinstance(value, dict):
        for key in ("id", "partition", "name"):
            if value.get(key):
                out.append(str(value[key]))
    return sorted(set(out))


def load_catalog(path: Path) -> dict[str, Any]:
    data = load_json(path)
    mappings = data.get("obligationOperationMapping") or []
    semantic_cells = [m for m in mappings if (m.get("denominatorMembership") or {}).get("semanticDenominator")]
    na_cells = [m for m in mappings if not (m.get("denominatorMembership") or {}).get("semanticDenominator")]
    declared = (data.get("denominators") or {}).get("candidateApplicableObligationContractCells")
    if declared is not None and int(declared) != len(semantic_cells):
        raise SystemExit(f"catalog semantic denominator mismatch: declared {declared}, mapped {len(semantic_cells)}")
    obligations = data.get("scenarioRecords") or data.get("obligations") or []
    obligation_meta = {}
    for o in obligations:
        oid = o.get("obligationId") or o.get("id")
        if not oid:
            continue
        partitions = partitions_from(o.get("boundaryPartitions") or o.get("partitions") or [])
        obligation_meta[oid] = {
            "track": o.get("track") or o.get("obligationTrack") or o.get("capability"),
            "title": o.get("title") or o.get("obligation_candidate") or oid,
            "partitions": partitions,
            "sourceAnchors": o.get("sourceAnchors") or o.get("source_anchors") or [],
            "limits": o.get("limitsAndReviewNotes") or o.get("limits_and_review_notes") or o.get("caution"),
        }
    return {"raw": data, "semanticCells": semantic_cells, "notApplicableCells": na_cells, "obligations": obligation_meta}


def case_key(case: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    return case.get("contractId") or case.get("contract_id"), case.get("operationId") or case.get("operation_id"), case.get("track")


def extract_checker_observations(doc: dict[str, Any], source_path: Path) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    # common schema: cases[].checkerResults[]
    for case in doc.get("cases", []) or []:
        contract, operation, track = case_key(case)
        case_status = norm_status(case.get("semanticStatus") or case.get("caseVerdict") or case.get("semanticVerdict") or case.get("status"))
        checkers = case.get("checkerResults") or []
        if isinstance(checkers, dict):
            checkers = list(checkers.values())
        for chk in checkers:
            oid = chk.get("obligationId") or chk.get("obligation") or chk.get("id")
            if not oid:
                continue
            observations.append({
                "obligationId": str(oid), "contractId": contract, "operationId": operation, "track": track,
                "status": norm_status(chk.get("status") or chk.get("semanticOutcome") or case_status),
                "partitions": partitions_from(chk.get("partitions") or chk.get("partition") or chk.get("boundaries")),
                "caseId": case.get("caseId"), "source": str(source_path),
                "lane": "original_crossarm" if contract and operation else "supplemental",
            })
        # reporting extractor schema: cases[].obligationVerdicts{obl: verdict}
        ov = case.get("obligationVerdicts") or {}
        if isinstance(ov, dict):
            for oid, verdict in ov.items():
                observations.append({
                    "obligationId": str(oid), "contractId": contract, "operationId": operation, "track": track,
                    "status": norm_status(verdict), "partitions": partitions_from(case.get("partitions")),
                    "caseId": case.get("caseId"), "source": str(source_path),
                    "lane": "original_crossarm" if contract and operation else "supplemental",
                })
    # semantic checker runtime schema: results[] one per obligation
    for row in doc.get("results", []) or []:
        oid = row.get("obligationId") or row.get("obligation")
        if oid:
            observations.append({
                "obligationId": str(oid), "contractId": row.get("contractId"), "operationId": row.get("operationId"),
                "track": row.get("track"), "status": norm_status(row.get("status") or row.get("semanticOutcome")),
                "partitions": partitions_from(row.get("boundaries") or row.get("partitions")),
                "caseId": row.get("caseId"), "source": str(source_path),
                "lane": "supplemental",
            })
    # posting/reporting essential matrix schema: obligation-level supplemental only
    for row in (doc.get("obligationMatrix") or doc.get("obligationPartitionMatrix") or []):
        oid = row.get("obligationId") or row.get("obligation")
        if oid:
            observations.append({
                "obligationId": str(oid), "contractId": None, "operationId": None, "track": row.get("track") or row.get("group"),
                "status": norm_status(row.get("status") or row.get("qualification") or row.get("caseStatuses") or row.get("evidence")),
                "partitions": partitions_from(row.get("partitions") or row.get("partition") or row.get("relatedCases")),
                "caseId": None, "source": str(source_path), "lane": "supplemental",
            })
    return observations


def load_semantic(paths: list[Path], supplemental_paths: list[Path] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pins = []
    observations = []
    for p in paths:
        data = load_json(p)
        require_saved_evidence_doc(data, p, kind="semantic")
        pins.append({"role": "semantic_results", **pin(p), "kind": data.get("kind"), "scope": data.get("scope")})
        observations.extend(extract_checker_observations(data, p))
    for p in supplemental_paths or []:
        data = load_json(p)
        pins.append({"role": "supplemental_essential_results", **pin(p), "kind": data.get("kind"), "scope": data.get("scope") or "supplemental-result-without-global-scope-accepted-only-outside-175-denominator"})
        for obs in extract_checker_observations(data, p):
            obs["contractId"] = None
            obs["operationId"] = None
            obs["lane"] = "supplemental"
            observations.append(obs)
        # essential interest result schema has no obligation matrix; bind narrowly to interest formula/EOF as supplemental, never to 175 cells.
        if data.get("caseId") and data.get("checks") is not None:
            status = "covered_checked" if not ((data.get("checks") or {}).get("failures")) and str(data.get("status", "")).lower() in {"pass", "passed", "ok"} else norm_status(data.get("status"))
            observations.append({
                "obligationId": "INTCALC-OBL-005",
                "contractId": None,
                "operationId": None,
                "track": "interest",
                "status": status,
                "partitions": [str(data.get("caseId"))],
                "caseId": data.get("caseId"),
                "source": str(p),
                "lane": "supplemental",
            })
    return observations, pins


def load_model_registry(path: Path | None) -> dict[str, Any]:
    if not path:
        return {"pin": None, "qualifiedObligations": [], "caseCount": 0}
    data = load_json(path)
    qualified = set()
    for case in data.get("cases", []) or []:
        for tr in case.get("modelTrace", []) or []:
            if tr.get("qualified") is True and tr.get("guardResult") is True:
                for oid in tr.get("obligationRefs", []) or []:
                    qualified.add(str(oid))
    return {"pin": {"role": "model_registry", **pin(path)}, "qualifiedObligations": sorted(qualified), "caseCount": len(data.get("cases", []) or [])}


def build_cells(catalog: dict[str, Any], observations: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    indexed = defaultdict(list)
    supplemental = []
    for obs in observations:
        if obs.get("contractId") and obs.get("operationId"):
            indexed[(obs["obligationId"], obs["contractId"], obs["operationId"])].append(obs)
        else:
            supplemental.append(obs)
    cells = []
    for m in catalog["semanticCells"]:
        key = (m.get("obligationId"), m.get("contractId"), m.get("operationId"))
        obs_list = indexed.get(key, [])
        status = "not_exercised"
        parts = set()
        sources = []
        for obs in obs_list:
            status = stronger(status, obs["status"])
            parts.update(obs.get("partitions") or [])
            sources.append({"caseId": obs.get("caseId"), "source": obs.get("source"), "status": obs.get("status"), "lane": obs.get("lane")})
        cells.append({
            "cellId": m.get("cellId") or "::".join(str(x) for x in key),
            "obligationId": key[0], "contractId": key[1], "operationId": key[2],
            "arm": m.get("arm"), "track": m.get("obligationTrack") or m.get("operationTrack"),
            "semanticDenominator": True, "status": status, "coveredPartitions": sorted(parts),
            "evidence": sources,
        })
    return cells, supplemental


def read_campaign_csv(path: Path | None) -> list[dict[str, Any]]:
    if not path:
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def aggregate_gcov(path: Path | None, campaign_rows: list[dict[str, Any]]) -> dict[str, Any]:
    programs = defaultdict(lambda: defaultdict(lambda: {"invocations": 0, "linesExecutedMax": 0, "linesTotal": None, "branchesExecutedMax": 0, "branchesTakenMax": 0, "branchesTotal": None, "sources": set()}))
    input_pin = None
    if path:
        data = load_json(path)
        input_pin = {"role": "gcov_reconciliation_or_campaign_report", **pin(path), "kind": data.get("kind")}
        for inv in data.get("invocations", []) or []:
            if not str(inv.get("measurementAdmissibility", "")).startswith("admissible"):
                continue
            program = inv.get("businessProgram") or inv.get("business_program") or inv.get("track")
            for unit in inv.get("unitBreakdown", []) or []:
                if unit.get("classification") != "main_generated_c":
                    continue
                fp = unit.get("sourceContentSha256") or unit.get("sourceSha256") or unit.get("sha256")
                denom_key = (fp, unit.get("lines", {}).get("total"), unit.get("branches", {}).get("total"))
                rec = programs[program][denom_key]
                rec["invocations"] += 1
                rec["linesExecutedMax"] = max(rec["linesExecutedMax"], int(unit.get("lines", {}).get("executed") or 0))
                rec["linesTotal"] = int(unit.get("lines", {}).get("total") or 0)
                rec["branchesExecutedMax"] = max(rec["branchesExecutedMax"], int(unit.get("branches", {}).get("executed") or 0))
                rec["branchesTakenMax"] = max(rec["branchesTakenMax"], int(unit.get("branches", {}).get("taken_at_least_once") or 0))
                rec["branchesTotal"] = int(unit.get("branches", {}).get("total") or 0)
                rec["sources"].add(unit.get("source") or unit.get("path") or "unknown")
    result = {"inputPin": input_pin, "programs": {}, "campaignCsvRows": len(campaign_rows), "csvComparabilityPolicy": "csv has no generated-C source fingerprint; retained as external summary, not line-unioned here"}
    for program, series in sorted(programs.items()):
        separate = []
        for (fp, _lt, _bt), rec in series.items():
            separate.append({
                "sourceFingerprintSha256": fp,
                "invocations": rec["invocations"],
                "sourceFiles": sorted(rec["sources"]),
                "lines": {"executedMax": rec["linesExecutedMax"], "total": rec["linesTotal"], "percentMax": round(rec["linesExecutedMax"] / rec["linesTotal"], 6) if rec["linesTotal"] else None},
                "branchesExecuted": {"executedMax": rec["branchesExecutedMax"], "total": rec["branchesTotal"], "percentMax": round(rec["branchesExecutedMax"] / rec["branchesTotal"], 6) if rec["branchesTotal"] else None},
                "branchesTakenAtLeastOnce": {"executedMax": rec["branchesTakenMax"], "total": rec["branchesTotal"], "percentMax": round(rec["branchesTakenMax"] / rec["branchesTotal"], 6) if rec["branchesTotal"] else None},
            })
        entry: dict[str, Any] = {"separateSeries": separate}
        if len(separate) == 1:
            entry["comparability"] = "same_fingerprint_unionable_within_series"
            entry["union"] = separate[0]
            entry["comparabilityGaps"] = []
        else:
            entry["comparability"] = "separate_fingerprints_not_unionable"
            entry["comparabilityGaps"] = ["main generated C source fingerprints differ; do not union line/branch numbers across these series"]
        result["programs"][program] = entry
    return result


def summarize(cells: list[dict[str, Any]], na_count: int, supplemental: list[dict[str, Any]]) -> dict[str, Any]:
    by_status = Counter(c["status"] for c in cells)
    for s in STATUSES:
        by_status.setdefault(s, 0)
    by_track = defaultdict(Counter)
    by_contract = defaultdict(Counter)
    for c in cells:
        by_track[c.get("track") or "unknown"][c["status"]] += 1
        by_contract[c.get("contractId") or "unknown"][c["status"]] += 1
    return {
        "byStatus": dict(by_status),
        "byTrack": {k: dict(v) for k, v in sorted(by_track.items())},
        "byContract": {k: dict(v) for k, v in sorted(by_contract.items())},
        "notApplicableCells": na_count,
        "supplementalObservationStatusCounts": dict(Counter(o["status"] for o in supplemental)),
    }


def decisive_gaps(cells: list[dict[str, Any]], supplemental: list[dict[str, Any]], catalog: dict[str, Any]) -> list[dict[str, Any]]:
    gap_cells = [c for c in cells if c["status"] in {"failed", "inconclusive", "not_exercised", "unobservable"}]
    # Manual risk ranks reflect observed CardDemo blockers requested in the task; evidence still comes from cell/supplemental status.
    priority_terms = [
        ("POSTTRAN-OBL-008", "alta", "partição de valor negativo/débito de posting ainda precisa evidência primária por contrato para alegação financeira"),
        ("POSTTRAN-OBL-001", "média", "falhas de OPEN/READ/WRITE são fault-injection; documentar como indisponíveis se não executáveis sem adulterar ambiente"),
        ("INTCALC-OBL-002", "alta", "última conta/EOF de juros bloqueia afirmação de atualização final de todas as contas"),
        ("TRANREPT-OBL-002", "alta", "totais/paginação/final account do relatório não sustentam alegação financeira global"),
        ("TRANREPT-OBL-001", "média", "fronteiras de datas e paginação precisam permanecer por campo/partição, não por obrigação inteira"),
    ]
    by_oid = defaultdict(list)
    for c in gap_cells:
        by_oid[c["obligationId"]].append(c)
    out = []
    used = set()
    for oid, sev, reason in priority_terms:
        if oid in by_oid:
            used.add(oid)
            out.append({"obligationId": oid, "rank": sev, "reason": reason, "affectedCells": len(by_oid[oid]), "statuses": dict(Counter(c["status"] for c in by_oid[oid]))})
    for oid, rows in sorted(by_oid.items()):
        if oid in used:
            continue
        meta = catalog["obligations"].get(oid, {})
        out.append({"obligationId": oid, "rank": "média" if any(r["status"] == "failed" for r in rows) else "baixa", "reason": meta.get("limits") or meta.get("title") or "lacuna semântica em evidência salva", "affectedCells": len(rows), "statuses": dict(Counter(c["status"] for c in rows))})
    return out[:20]


def render_report(ledger: dict[str, Any]) -> str:
    den = ledger["denominators"]
    by = ledger["summary"]["byStatus"]
    lines = [
        "# Ledger final de cobertura defensável",
        "",
        f"Gerado por script sobre evidências salvas em {ledger['createdUtc']}. Não executa API, COBOL, modelo externo ou quarentena.",
        "",
        "## Tabela executiva",
        "",
        "| Métrica | Valor |",
        "|---|---:|",
        f"| Obrigações de negócio | {den['obligations']} |",
        f"| Contratos | {den['contracts']} |",
        f"| Denominador semântico (obrigação×contrato aplicável) | {den['semantic']} |",
        f"| Denominador bruto ilustrativo (não usar como semântico) | {den['grossIllustrative']} |",
        f"| Células N/A fora do denominador | {ledger['summary']['notApplicableCells']} |",
        "",
        "## Estados no denominador semântico",
        "",
        "| Estado | Células |",
        "|---|---:|",
    ]
    labels = {
        "covered_checked": "coberto e checado",
        "failed": "falhou",
        "inconclusive": "inconclusivo",
        "not_exercised": "não exercitado",
        "unobservable": "não observável",
        "not_applicable": "N/A (fora do denominador)",
    }
    for key in ["covered_checked", "failed", "inconclusive", "not_exercised", "unobservable"]:
        lines.append(f"| {labels[key]} | {by.get(key, 0)} |")
    lines.extend(["", "## Por trilha", "", "| Trilha | coberto | falhou | inconclusivo | não exercitado | não observável |", "|---|---:|---:|---:|---:|---:|"])
    for track, counts in ledger["summary"]["byTrack"].items():
        lines.append(f"| {track} | {counts.get('covered_checked',0)} | {counts.get('failed',0)} | {counts.get('inconclusive',0)} | {counts.get('not_exercised',0)} | {counts.get('unobservable',0)} |")
    lines.extend(["", "## Gcov alinhado por fingerprint do C gerado", "", "| Programa | Comparabilidade | Linhas | Branches executados | Observação |", "|---|---|---:|---:|---|"])
    for program, info in ledger["gcov"].get("programs", {}).items():
        if info["comparability"] == "same_fingerprint_unionable_within_series":
            u = info["union"]
            lines.append(f"| {program} | mesmo fingerprint | {u['lines']['executedMax']}/{u['lines']['total']} | {u['branchesExecuted']['executedMax']}/{u['branchesExecuted']['total']} | somável apenas dentro desta série |")
        else:
            lines.append(f"| {program} | fingerprints separados | — | — | comparability gap: não unir linhas/branches |")
    lines.extend(["", "## Lacunas decisivas", "", "| Rank | Obrigação | Células afetadas | Motivo |", "|---|---|---:|---|"])
    for gap in ledger["decisiveGaps"]:
        lines.append(f"| {gap['rank']} | {gap['obligationId']} | {gap['affectedCells']} | {gap['reason']} |")
    lines.extend(["", "## Critério de parada bounded", "", "Parar a contabilização desta versão aqui: a saída congela o denominador aplicável atual, separa evidência original/suplementar e registra lacunas. Novas matrizes devem ser agregadas por novo comando/artefato, não por reinterpretação manual deste relatório.", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Aggregate final coverage/accounting ledger from saved AWS CardDemo P3 evidence")
    ap.add_argument("--catalog", required=True, type=Path)
    ap.add_argument("--semantic-results", action="append", type=Path, default=[])
    ap.add_argument("--supplemental-results", action="append", type=Path, default=[], help="Supplemental essential evidence kept outside the 175-cell denominator; scope-less legacy result files allowed here only")
    ap.add_argument("--model-registry", type=Path)
    ap.add_argument("--coverage-report", type=Path)
    ap.add_argument("--campaign-coverage-csv", type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args(argv)

    catalog = load_catalog(args.catalog)
    observations, semantic_pins = load_semantic(args.semantic_results, args.supplemental_results)
    model = load_model_registry(args.model_registry)
    campaign_rows = read_campaign_csv(args.campaign_coverage_csv)
    gcov = aggregate_gcov(args.coverage_report, campaign_rows)
    cells, supplemental = build_cells(catalog, observations)
    summary = summarize(cells, len(catalog["notApplicableCells"]), supplemental)
    ledger = {
        "kind": "complementary-coverage-closure-v1-ledger",
        "createdUtc": datetime.now(timezone.utc).isoformat(),
        "inputs": {"catalog": {"role": "catalog", **pin(args.catalog)}, "semanticResults": semantic_pins, "modelRegistry": model["pin"], "campaignCoverageCsv": ({"role": "campaign_coverage_csv", **pin(args.campaign_coverage_csv)} if args.campaign_coverage_csv else None)},
        "policies": {
            "originalSupplementSeparation": "contract/operation cells use original/cross-arm observations only when contractId+operationId are present; supplemental essential evidence is reported separately and does not silently fill future campaign cells",
            "denominator": "semantic denominator is obligation×contract for applicable operation track; gross 25×21 is illustrative only",
            "notExecutedVsNA": "not_exercised remains inside applicable denominator; N/A is only other-track/outside-denominator",
            "gcovAlignment": "main generated C counts are comparable only when source fingerprint and denominator match",
            "structuralVsSemantic": "HTTP/schema structural PASS is not semantic PASS without checker result",
        },
        "denominators": {"obligations": len(catalog["obligations"]), "contracts": len((catalog["raw"].get("contracts") or [])), "semantic": len(cells), "grossIllustrative": (catalog["raw"].get("denominators") or {}).get("obligationOperationCellsIllustrative")},
        "summary": summary,
        "cells": cells,
        "supplementalObservations": supplemental,
        "modelRegistry": {"qualifiedObligations": model["qualifiedObligations"], "caseCount": model["caseCount"], "prospectiveOnly": True},
        "gcov": gcov,
        "decisiveGaps": decisive_gaps(cells, supplemental, catalog),
        "boundedStoppingCriteria": [
            "all catalog semantic cells accounted exactly once",
            "N/A excluded from denominator and not_exercised retained inside denominator",
            "no line/branch union across mismatched generated-C fingerprints",
            "original campaign observations not overwritten by supplemental essential evidence",
        ],
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "acceptance-ledger.json").write_text(json.dumps(ledger, indent=2, ensure_ascii=False), encoding="utf-8")
    (args.out_dir / "final-coverage-report.md").write_text(render_report(ledger), encoding="utf-8")
    print(args.out_dir / "acceptance-ledger.json")
    print(args.out_dir / "final-coverage-report.md")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            raise SystemExit(2)
        raise

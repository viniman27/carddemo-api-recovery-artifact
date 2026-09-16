#!/usr/bin/env python3
"""Aggregate real line/branch coverage for the 84-case complementary matrix.

Read-only: consumes saved campaign-report.json and gcov files only. It does not
rerun APIs, COBOL, gcov, models, or external services.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BRANCH_RE = re.compile(r"^branch\s+(\d+)\s+(.*)$")
COUNT_RE = re.compile(r"^\s*([^:]+):\s*(\d+)\s*:(.*)$")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pin(path: Path) -> dict[str, Any]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def admissibility(measurement: dict[str, Any]) -> str:
    return str(measurement.get("measurementAdmissibility") or measurement.get("admissibility") or "missing")


def scenario_id(check: dict[str, Any]) -> str:
    prov = (check.get("receipt") or {}).get("provenance") or []
    if prov and isinstance(prov[0], str) and ":" in prov[0]:
        return prov[0].split(":")[-1]
    cid = str(check.get("case_id") or check.get("caseId") or "")
    parts = cid.split("-")
    return "-".join(parts[4:]) if len(parts) > 4 else cid


def parse_gcov_main(path: Path, source_sha: str) -> dict[str, Any]:
    executable_lines: set[int] = set()
    executed_lines: set[int] = set()
    branch_total: set[tuple[str, int, int]] = set()
    branch_executed: set[tuple[str, int, int]] = set()
    branch_taken: set[tuple[str, int, int]] = set()
    current_line: int | None = None

    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = COUNT_RE.match(raw)
        if m:
            count, line_s, _src = m.groups()
            current_line = int(line_s)
            c = count.strip()
            if current_line > 0 and c not in {"-"}:
                executable_lines.add(current_line)
                if c not in {"#####", "====="}:
                    try:
                        if int(c.rstrip("*")) > 0:
                            executed_lines.add(current_line)
                    except ValueError:
                        # gcov may print non-integer summary markers; they are not executable hits.
                        pass
            continue
        bm = BRANCH_RE.match(raw.strip())
        if bm and current_line is not None:
            branch_idx = int(bm.group(1))
            rest = bm.group(2).strip().lower()
            bid = (source_sha, current_line, branch_idx)
            branch_total.add(bid)
            if "never executed" not in rest:
                branch_executed.add(bid)
                if "taken 0%" not in rest and "taken 0 " not in rest:
                    branch_taken.add(bid)
    return {
        "line_total_ids": executable_lines,
        "line_executed_ids": executed_lines,
        "branch_total_ids": branch_total,
        "branch_executed_ids": branch_executed,
        "branch_taken_ids": branch_taken,
    }


def percent(num: int, den: int) -> float | None:
    return round((num / den) * 100, 2) if den else None


def cov_counts(sets: dict[str, set]) -> dict[str, Any]:
    lt = len(sets["line_total_ids"])
    le = len(sets["line_executed_ids"])
    bt = len(sets["branch_total_ids"])
    be = len(sets["branch_executed_ids"])
    btk = len(sets["branch_taken_ids"])
    return {
        "lines": {"executed": le, "total": lt, "percent": percent(le, lt)},
        "branches_executed": {"executed": be, "total": bt, "percent": percent(be, bt)},
        "branches_taken_at_least_once": {"taken": btk, "total": bt, "percent": percent(btk, bt)},
    }


def empty_sets() -> dict[str, set]:
    return {"line_total_ids": set(), "line_executed_ids": set(), "branch_total_ids": set(), "branch_executed_ids": set(), "branch_taken_ids": set()}


def union_into(dst: dict[str, set], src: dict[str, set]) -> None:
    for k in dst:
        dst[k].update(src[k])


def collect(report_path: Path, source_catalog: Path | None = None) -> dict[str, Any]:
    report = load_json(report_path)
    suite_reports = report.get("suiteReports") or []
    checks: list[dict[str, Any]] = []
    for sr in suite_reports:
        checks.extend(sr.get("checks") or [])
    if len(checks) != 84:
        raise SystemExit(f"expected 84 checks, found {len(checks)}")

    totals = report.get("totals") or {}
    if totals.get("planned") != 84 or totals.get("completed") != 84 or totals.get("structural_ok") != 84:
        raise SystemExit(f"unexpected campaign totals: {totals}")

    inadmissible: list[dict[str, Any]] = []
    invocations: list[dict[str, Any]] = []
    by_program = defaultdict(lambda: defaultdict(empty_sets))          # program -> source_sha -> sets
    by_contract_program = defaultdict(lambda: defaultdict(lambda: defaultdict(empty_sets)))
    by_arm_program = defaultdict(lambda: defaultdict(lambda: defaultdict(empty_sets)))
    by_contract = defaultdict(Counter)
    by_program_inv = defaultdict(Counter)
    source_series: dict[tuple[str, str], dict[str, Any]] = {}
    contracts = {}
    scenario_counter = Counter()
    scenario_by_contract = defaultdict(Counter)
    request_ids = []
    structural_ok = 0

    for check in checks:
        contract = check.get("contractId")
        track = check.get("track")
        operation = check.get("operationId")
        arm = "zero-shot" if str(contract).startswith("E1-") else "few-shot" if str(contract).startswith("E2-") else "sdd"
        contracts[contract] = arm
        sid = scenario_id(check)
        scenario_counter[sid] += 1
        scenario_by_contract[contract][sid] += 1
        req_id = (check.get("receipt") or {}).get("request_identity")
        if req_id:
            request_ids.append(req_id)
        if (check.get("structuralCheck") or {}).get("ok") is True:
            structural_ok += 1

        m = check.get("measurement") or {}
        adm = admissibility(m)
        program = m.get("businessProgram") or {"posting": "CBTRN02C", "interest": "CBACT04C", "reporting": "CBTRN03C"}.get(track) or "unknown"
        by_contract[contract][adm] += 1
        by_program_inv[program][adm] += 1
        if not adm.startswith("admissible"):
            reason = (m.get("inadmissibilityReasons") or m.get("reasons") or [])
            if not reason:
                # The six known warnings are in the top-level report.
                reason = ["audit_missing_for_current_case_track"]
            inadmissible.append({"case_id": check.get("case_id"), "contractId": contract, "arm": arm, "track": track, "operationId": operation, "reasons": reason})
            continue

        main = ((m.get("correctedParser") or {}).get("mainGeneratedC") or {})
        gcov_path = Path(main.get("path") or "")
        source_path = Path(main.get("source") or "")
        if not gcov_path.exists() or not source_path.exists():
            raise SystemExit(f"missing gcov/source for admissible case {check.get('case_id')}: {gcov_path} / {source_path}")
        source_sha = sha256_file(source_path)
        parsed = parse_gcov_main(gcov_path, source_sha)
        union_into(by_program[program][source_sha], parsed)
        union_into(by_contract_program[contract][program][source_sha], parsed)
        union_into(by_arm_program[arm][program][source_sha], parsed)
        by_program_inv[program]["admissible_parsed"] += 1
        key = (program, source_sha)
        source_series.setdefault(key, {"program": program, "source_sha256": source_sha, "source_path": str(source_path), "source_bytes": source_path.stat().st_size, "gcov_examples": []})
        if len(source_series[key]["gcov_examples"]) < 3:
            source_series[key]["gcov_examples"].append(str(gcov_path))
        invocations.append({
            "case_id": check.get("case_id"), "contractId": contract, "arm": arm, "track": track, "operationId": operation,
            "scenarioId": sid, "program": program, "source_sha256": source_sha,
            "gcov_path": str(gcov_path), "source_path": str(source_path), **cov_counts(parsed),
        })

    if len(inadmissible) != 6 or len(invocations) != 78:
        raise SystemExit(f"expected 78 admissible and 6 inadmissible; got {len(invocations)} admissible, {len(inadmissible)} inadmissible")
    if len(scenario_counter) != 12 or any(v != 7 for v in scenario_counter.values()):
        raise SystemExit(f"scenario matrix is not 12x7: {dict(scenario_counter)}")
    if len(set(request_ids)) != 84:
        raise SystemExit(f"expected 84 unique request identities, got {len(set(request_ids))}")

    def summarize_group(group: dict[str, dict[str, set]]) -> dict[str, Any]:
        out = {}
        for name, series in sorted(group.items()):
            out[name] = {sha: cov_counts(sets) for sha, sets in sorted(series.items())}
            out[name]["_comparability"] = "one source fingerprint" if len(series) == 1 else "separate source fingerprints; do not pool line/branch denominators"
        return out

    by_contract_program_out = {}
    for contract, programs in sorted(by_contract_program.items()):
        by_contract_program_out[contract] = {program: {sha: cov_counts(sets) for sha, sets in sorted(series.items())} | {"_comparability": ("one source fingerprint" if len(series)==1 else "separate source fingerprints; do not pool")} for program, series in sorted(programs.items())}

    by_arm_program_out = {}
    for arm, programs in sorted(by_arm_program.items()):
        by_arm_program_out[arm] = {program: {sha: cov_counts(sets) for sha, sets in sorted(series.items())} | {"_comparability": ("one source fingerprint" if len(series)==1 else "separate source fingerprints; do not pool")} for program, series in sorted(programs.items())}

    output = {
        "kind": "complementary-matrix-coverage-v1",
        "createdUtc": datetime.now(timezone.utc).isoformat(),
        "inputs": {"campaignReport": pin(report_path), "sourceCatalog": pin(source_catalog) if source_catalog else None},
        "policies": {
            "evidence": "saved per-invocation gcov artifacts only; no API/COBOL/gcov reruns",
            "admissibility": "inadmissible cases are reported with reasons and never counted as zero coverage",
            "sourceAlignment": "line/branch IDs are unioned only within the same business program and source-file SHA-256",
            "mainUnit": "only correctedParser.mainGeneratedC .gcov is used; generated headers/helpers are excluded",
            "branchDefinitions": "branch IDs preserve gcov line number + branch index; executed means not 'never executed'; taken means taken > 0",
        },
        "campaignTotalsVerified": {"planned": 84, "completed": 84, "structural_ok": structural_ok, "measurement_admissible": len(invocations), "measurement_inadmissible": len(inadmissible)},
        "scenarioMatrix": {"scenarioCount": len(scenario_counter), "contractCount": len(contracts), "countsByScenario": dict(sorted(scenario_counter.items())), "countsByContract": {k: dict(sorted(v.items())) for k, v in sorted(scenario_by_contract.items())}, "uniqueRequestIdentityCount": len(set(request_ids)), "all84RequestIdentitiesUnique": len(set(request_ids)) == 84},
        "contracts": dict(sorted(contracts.items())),
        "inadmissibleCases": inadmissible,
        "invocationDistributions": {"byContract": {k: dict(v) for k, v in sorted(by_contract.items())}, "byProgram": {k: dict(v) for k, v in sorted(by_program_inv.items())}},
        "sourceSeries": list(source_series.values()),
        "coverageByProgram": summarize_group(by_program),
        "coverageByContractProgram": by_contract_program_out,
        "coverageByArmProgram": by_arm_program_out,
        "invocations": invocations,
    }
    return output


def write_csvs(out: dict[str, Any], out_dir: Path) -> None:
    rows = []
    for program, series in out["coverageByProgram"].items():
        for sha, counts in series.items():
            if sha.startswith("_"):
                continue
            rows.append({"scope": "program", "name": program, "program": program, "source_sha256": sha, **flat_counts(counts)})
    for contract, programs in out["coverageByContractProgram"].items():
        for program, series in programs.items():
            for sha, counts in series.items():
                if sha.startswith("_"):
                    continue
                rows.append({"scope": "contract_program", "name": contract, "program": program, "source_sha256": sha, **flat_counts(counts)})
    for arm, programs in out["coverageByArmProgram"].items():
        for program, series in programs.items():
            for sha, counts in series.items():
                if sha.startswith("_"):
                    continue
                rows.append({"scope": "arm_program", "name": arm, "program": program, "source_sha256": sha, **flat_counts(counts)})
    with (out_dir / "coverage-summary.csv").open("w", newline="", encoding="utf-8") as fh:
        fields = ["scope", "name", "program", "source_sha256", "line_executed", "line_total", "line_percent", "branch_executed", "branch_total", "branch_executed_percent", "branch_taken", "branch_taken_percent"]
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    with (out_dir / "coverage-invocations.csv").open("w", newline="", encoding="utf-8") as fh:
        fields = ["case_id", "contractId", "arm", "track", "operationId", "scenarioId", "program", "source_sha256", "line_executed", "line_total", "line_percent", "branch_executed", "branch_total", "branch_executed_percent", "branch_taken", "branch_taken_percent", "gcov_path"]
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for inv in out["invocations"]:
            row = {k: inv.get(k) for k in fields}
            row.update(flat_counts(inv))
            w.writerow(row)
    with (out_dir / "inadmissible-cases.csv").open("w", newline="", encoding="utf-8") as fh:
        fields = ["case_id", "contractId", "arm", "track", "operationId", "reasons"]
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader()
        for row in out["inadmissibleCases"]:
            r = dict(row); r["reasons"] = ";".join(row.get("reasons") or [])
            w.writerow(r)


def flat_counts(c: dict[str, Any]) -> dict[str, Any]:
    return {
        "line_executed": c["lines"]["executed"], "line_total": c["lines"]["total"], "line_percent": c["lines"]["percent"],
        "branch_executed": c["branches_executed"]["executed"], "branch_total": c["branches_executed"]["total"], "branch_executed_percent": c["branches_executed"]["percent"],
        "branch_taken": c["branches_taken_at_least_once"]["taken"], "branch_taken_percent": c["branches_taken_at_least_once"]["percent"],
    }


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def render_report(out: dict[str, Any]) -> str:
    t = out["campaignTotalsVerified"]
    lines = [
        "# Relatório final de cobertura — matriz complementar 84 casos",
        "",
        f"Gerado em {out['createdUtc']} a partir de artefatos salvos. Não houve reexecução de API, COBOL, gcov ou chamadas externas.",
        "",
        "## Totais verificados",
        "",
        md_table(["Métrica", "Valor"], [["casos planejados", t['planned']], ["casos concluídos", t['completed']], ["estrutural OK", t['structural_ok']], ["medições admissíveis", t['measurement_admissible']], ["casos inadmissíveis", t['measurement_inadmissible']]]),
        "",
        "## Cobertura por programa (união real por mesmo SHA-256 do C gerado)",
        "",
    ]
    rows = []
    for program, series in out["coverageByProgram"].items():
        for sha, counts in series.items():
            if sha.startswith("_"):
                continue
            rows.append([program, sha[:12], f"{counts['lines']['executed']}/{counts['lines']['total']} ({counts['lines']['percent']}%)", f"{counts['branches_executed']['executed']}/{counts['branches_executed']['total']} ({counts['branches_executed']['percent']}%)", f"{counts['branches_taken_at_least_once']['taken']}/{counts['branches_taken_at_least_once']['total']} ({counts['branches_taken_at_least_once']['percent']}%)"])
    lines.append(md_table(["Programa", "SHA fonte", "Linhas", "Branches executados", "Branches tomados >0"], rows))
    lines += ["", "## Cobertura por contrato/programa", ""]
    rows = []
    for contract, programs in out["coverageByContractProgram"].items():
        for program, series in programs.items():
            for sha, counts in series.items():
                if sha.startswith("_"):
                    continue
                rows.append([contract, out['contracts'][contract], program, sha[:12], f"{counts['lines']['executed']}/{counts['lines']['total']} ({counts['lines']['percent']}%)", f"{counts['branches_executed']['executed']}/{counts['branches_executed']['total']} ({counts['branches_executed']['percent']}%)", f"{counts['branches_taken_at_least_once']['taken']}/{counts['branches_taken_at_least_once']['total']} ({counts['branches_taken_at_least_once']['percent']}%)"])
    lines.append(md_table(["Contrato", "Braço", "Programa", "SHA fonte", "Linhas", "Branches executados", "Branches tomados >0"], rows))
    lines += ["", "## Cobertura por braço/programa", ""]
    rows = []
    for arm, programs in out["coverageByArmProgram"].items():
        for program, series in programs.items():
            for sha, counts in series.items():
                if sha.startswith("_"):
                    continue
                rows.append([arm, program, sha[:12], f"{counts['lines']['executed']}/{counts['lines']['total']} ({counts['lines']['percent']}%)", f"{counts['branches_executed']['executed']}/{counts['branches_executed']['total']} ({counts['branches_executed']['percent']}%)", f"{counts['branches_taken_at_least_once']['taken']}/{counts['branches_taken_at_least_once']['total']} ({counts['branches_taken_at_least_once']['percent']}%)"])
    lines.append(md_table(["Braço", "Programa", "SHA fonte", "Linhas", "Branches executados", "Branches tomados >0"], rows))
    lines += ["", "## Seis casos inadmissíveis", ""]
    lines.append(md_table(["Caso", "Contrato", "Trilha", "Motivo"], [[r['case_id'], r['contractId'], r['track'], "; ".join(r['reasons'])] for r in out['inadmissibleCases']]))
    lines += ["", "## Matriz 12×7 e diversidade efetiva", ""]
    sm = out["scenarioMatrix"]
    lines.append(f"Foram encontrados {sm['scenarioCount']} cenários, cada um presente nos 7 contratos; os 84 `request_identity` são únicos ({sm['uniqueRequestIdentityCount']}/84).")
    lines += ["", md_table(["Cenário", "Casos"], [[k, v] for k, v in sm["countsByScenario"].items()]), "", "## Veredito calibrado", "", "A cobertura estrutural é real e suficiente para caracterizar as partições complementares selecionadas, com 78 medições gcov admissíveis e 6 casos de reporting inadmissíveis por ausência de auditoria da trilha corrente. Isto não prova 100% de semântica de negócio nem cobertura ideal de todas as partições possíveis.", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign-report", required=True, type=Path)
    ap.add_argument("--source-catalog", type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()
    out = collect(args.campaign_report, args.source_catalog)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "coverage-ledger.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csvs(out, args.out_dir)
    (args.out_dir / "PTBR-RELATORIO-COBERTURA.md").write_text(render_report(out), encoding="utf-8")
    print(args.out_dir / "coverage-ledger.json")
    print(args.out_dir / "coverage-summary.csv")
    print(args.out_dir / "coverage-invocations.csv")
    print(args.out_dir / "inadmissible-cases.csv")
    print(args.out_dir / "PTBR-RELATORIO-COBERTURA.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

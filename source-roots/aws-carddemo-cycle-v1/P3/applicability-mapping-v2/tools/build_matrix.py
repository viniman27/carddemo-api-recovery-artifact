#!/usr/bin/env python3
"""Build pre-campaign applicability matrix from frozen inventory.

This is a mapping artifact only: it reads reference obligations, pinned operation
inventory/contracts, and candidate fixture manifests; it does not read runtime
results, coverage, oracle outputs, quarantine, or official campaign suites.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT.parent
CYCLE = P3.parent

REFERENCE = P3 / "reference-executable-v4" / "model.json"
WITNESSES = P3 / "reference-executable-v4" / "evidence" / "obligation-witnesses.json"
REVIEW = P3 / "reference-independent-review-v4" / "review.json"
INVENTORY = P3 / "suite-adapters-preflight-v1" / "evidence-real-preflight-20260915T-synthetic" / "operation-inventory.json"
PINS = P3 / "suite-adapters-preflight-v1" / "evidence-real-preflight-20260915T-synthetic" / "contract-pins.json"
FIXTURES = P3 / "fixture-materialization-v2" / "package" / "manifest.json"
SDD_OPENAPI = CYCLE / "P2a" / "openapi-carddemo-stage6r3.yaml"

TRACKS = {
    "POSTTRAN": "posting",
    "INTCALC": "interest",
    "TRANREPT": "reporting",
}

STATUS_TAXONOMY = {
    "expressible_by_surface": "A operação pública tem campos de request suficientes para selecionar os dados/precondições sem fortalecer o contrato; ainda não implica expected result.",
    "conditioned_on_external_fixture": "A operação existe, mas a seleção substantiva depende de recursos externos/fixtures físicos candidatos, não de campos públicos do request.",
    "not_expressible": "A obrigação, no recorte atual, exige controle de falha/estado interno/efeito que nem request nem fixture candidato sustentam sem alterar a superfície.",
    "not_mapped": "Há operação pública da trilha, mas o passo da obrigação não foi mapeado para uma invocação HTTP concreta preservando a abstração declarada.",
    "precondition_indeterminate": "A obrigação depende de precondição cujo estado admissível não é determinado antes da campanha pelos contratos/fixtures permitidos.",
    "observation_inadmissible": "A observação requerida não pode ser usada como veredito pré-campanha sem ler runtime/oráculo/cobertura ou sem expor estado interno não autorizado.",
}

OBLIGATION_RULES = {
    # Posting
    "POSTTRAN-OBL-001": {"base": "conditioned_on_external_fixture", "surface_if_rich": "expressible_by_surface", "reason": "OPEN/DDs são selecionáveis por recursos declarados ou fixture físico; não define expectativa de retorno."},
    "POSTTRAN-OBL-002": {"base": "conditioned_on_external_fixture", "surface_if_data": "expressible_by_surface", "reason": "Loop/EOF dependem do conteúdo DALYTRAN; contratos com array de transações conseguem expressar a entrada, SDD usa fixture."},
    "POSTTRAN-OBL-003": {"base": "conditioned_on_external_fixture", "surface_if_data": "expressible_by_surface", "reason": "Cópia para TRANFILE depende de registro diário aceito; request com transações expressa campos, sem expected de timestamp."},
    "POSTTRAN-OBL-004": {"base": "conditioned_on_external_fixture", "surface_if_rich": "expressible_by_surface", "reason": "Validação de cartão requer relação DALYTRAN/XREF; só superfícies com lookup/binding no body controlam ambas."},
    "POSTTRAN-OBL-005": {"base": "conditioned_on_external_fixture", "surface_if_rich": "expressible_by_surface", "reason": "Conta/limite/expiração requer XREF+ACCOUNT além da transação; contratos mínimos ficam condicionados à fixture."},
    "POSTTRAN-OBL-006": {"base": "conditioned_on_external_fixture", "surface_if_rich": "expressible_by_surface", "reason": "Rejeito e RC podem ser preparados por dados/lookup, mas sem transformar status HTTP em oráculo de negócio."},
    "POSTTRAN-OBL-007": {"base": "conditioned_on_external_fixture", "surface_if_rich": "expressible_by_surface", "reason": "Create/update TCATBAL exige ACCOUNT/XREF/TCATBAL e transação aceita; fixture candidata tem chaves concretas."},
    "POSTTRAN-OBL-008": {"base": "not_expressible", "reason": "Razão interna 109, ordem de efeitos e ACCOUNT lógico pós-falha não são controláveis/observáveis sem fortalecer binding ou ler estado inadmissível."},
    "POSTTRAN-OBL-009": {"base": "precondition_indeterminate", "reason": "Falha WRITE TRANFILE depois de efeitos anteriores requer status/falha de saída não materializado pela fixture candidata normal."},
    # Interest
    "INTCALC-OBL-001": {"base": "conditioned_on_external_fixture", "surface_if_rich": "expressible_by_surface", "reason": "DDs/PARM são request em contratos ricos ou PARMFILE externo na fixture; sem expectativa de saída."},
    "INTCALC-OBL-002": {"base": "conditioned_on_external_fixture", "surface_if_rich": "expressible_by_surface", "reason": "Agrupamento depende de TCATBAL ordenado/contíguo; rich body pode carregar category balances, SDD/minimal depende fixture."},
    "INTCALC-OBL-003": {"base": "conditioned_on_external_fixture", "surface_if_rich": "expressible_by_surface", "reason": "Leituras ACCOUNT/XREF exigem datasets de lookup; fixture candidata possui chaves e sidecar alternado."},
    "INTCALC-OBL-004": {"base": "conditioned_on_external_fixture", "surface_if_rich": "expressible_by_surface", "reason": "Taxa específica/default depende de DISCGRP; fixture candidata expõe STANDARD, ZERORATE e DEFAULT."},
    "INTCALC-OBL-005": {"base": "conditioned_on_external_fixture", "surface_if_rich": "expressible_by_surface", "reason": "Fórmula/guarda depende de saldo e taxa; arredondamento não é expected fixado."},
    "INTCALC-OBL-006": {"base": "conditioned_on_external_fixture", "surface_if_rich": "expressible_by_surface", "reason": "Campos da TRANSACT podem ser preparados pelos recursos, mas timestamp/representação física ficam limitados."},
    "INTCALC-OBL-007": {"base": "conditioned_on_external_fixture", "surface_if_rich": "expressible_by_surface", "reason": "Quebra de grupo requer multiplicidade/ordem em TCATBAL e ACCOUNT; fixture candidata sustenta pré-condição candidata, não resultado."},
    "INTCALC-OBL-008": {"base": "observation_inadmissible", "reason": "Ausência de update final no EOF é achado estático; ACCOUNT do último grupo não deve virar veredito pré-campanha sem observação autorizada."},
    # Reporting
    "TRANREPT-OBL-001": {"base": "not_mapped", "reason": "REPROC/SORT/JCL documentais não são operação HTTP; só se mapeia a invocação efetiva de relatório com TRANFILE/DATEPARM já preparados."},
    "TRANREPT-OBL-002": {"base": "conditioned_on_external_fixture", "surface_if_data": "expressible_by_surface", "reason": "Filtro textual por DATEPARM é expressável quando dateParameterRecords/dateParameters estão no request; SDD usa DATEPARM físico."},
    "TRANREPT-OBL-003": {"base": "precondition_indeterminate", "reason": "EOF condicional depende de receiver unknown/retido; não fixar como total incondicional nem como ausência universal."},
    "TRANREPT-OBL-004": {"base": "conditioned_on_external_fixture", "surface_if_rich": "expressible_by_surface", "reason": "Quebra/lookups requer TRANFILE ordenado e CARDXREF/TRANTYPE/TRANCATG; contratos ricos carregam lookup, SDD depende fixture."},
    "TRANREPT-OBL-005": {"base": "precondition_indeterminate", "reason": "Cabeçalhos/paginação exigem volume/estado de página não demonstrado pelos 2 registros candidatos; não inventar fixture de paginação."},
    "TRANREPT-OBL-006": {"base": "conditioned_on_external_fixture", "surface_if_data": "expressible_by_surface", "reason": "Linha de detalhe/acumulação depende de transações no intervalo e lookups; expressável por request rico/dados, condicionado nos demais."},
    "TRANREPT-OBL-007": {"base": "precondition_indeterminate", "reason": "Totais no EOF são condicionais ao teste textual/receiver; pré-campanha não decide retenção EOF."},
    "TRANREPT-OBL-008": {"base": "observation_inadmissible", "reason": "Ausência/presença de Account Total final não deve ser inferida antes de observação autorizada e sem oráculo independente."},
}

RESOURCE_MAP = {
    "posting": {
        "input_records": ["DALYTRAN"],
        "lookups_state": ["XREFFILE", "XREFFILE.1", "ACCTFILE", "TCATBALF", "TRANFILE"],
        "output_candidates": ["TRANFILE", "DALYREJS"],
    },
    "interest": {
        "input_records": ["TCATBALF", "PARMFILE"],
        "lookups_state": ["XREFFILE", "XREFFILE.1", "ACCTFILE", "DISCGRP"],
        "output_candidates": ["TRANSACT"],
    },
    "reporting": {
        "input_records": ["TRANFILE", "TRANFILE.empty", "DATEPARM"],
        "lookups_state": ["CARDXREF", "TRANTYPE", "TRANCATG"],
        "output_candidates": ["TRANREPT"],
    },
}

FIELD_SOURCE_BY_TRACK = {
    "posting": {
        "accountFile": ["ACCTFILE"],
        "accounts": ["ACCTFILE"],
        "categoryBalanceFile": ["TCATBALF"],
        "categoryBalances": ["TCATBALF"],
        "crossReferenceFile": ["XREFFILE"],
        "cardCrossReference": ["XREFFILE"],
        "transactionFile": ["TRANFILE"],
        "outputTransactionFile": ["TRANFILE"],
        "transactionOutput": ["TRANFILE"],
        "rejectFile": ["DALYREJS"],
        "rejectionOutput": ["DALYREJS"],
    },
    "interest": {
        "accountFile": ["ACCTFILE"],
        "accounts": ["ACCTFILE"],
        "categoryBalanceFile": ["TCATBALF"],
        "categoryBalances": ["TCATBALF"],
        "crossReferenceFile": ["XREFFILE"],
        "cardCrossReference": ["XREFFILE"],
        "disclosureGroupFile": ["DISCGRP"],
        "disclosureGroups": ["DISCGRP"],
        "outputTransactionFile": ["TRANSACT"],
        "transactionOutput": ["TRANSACT"],
    },
    "reporting": {
        "crossReferenceFile": ["CARDXREF"],
        "cardCrossReference": ["CARDXREF"],
        "transactionTypeFile": ["TRANTYPE"],
        "transactionTypes": ["TRANTYPE"],
        "transactionCategoryFile": ["TRANCATG"],
        "transactionCategories": ["TRANCATG"],
        "reportFile": ["TRANREPT"],
        "reportOutput": ["TRANREPT"],
    },
}

GUARD_SENSITIVE_VARIANT_REQUIRED = {
    "POSTTRAN-OBL-004": "requires XREF-present/missing resource variant; current candidate has no named branch variant",
    "POSTTRAN-OBL-005": "requires account/limit/expiration/active-state variants; current candidate has no named branch variant",
    "POSTTRAN-OBL-006": "requires validation-rejection branch variants; current candidate has no named branch variant",
    "POSTTRAN-OBL-007": "requires TCATBAL status 00/23/error variants; current candidate has no named branch variant",
    "INTCALC-OBL-004": "requires DISCGRP specific/default/default-missing variants; current candidate has no named branch variant",
    "INTCALC-OBL-005": "requires zero/nonzero-rate and balance variants; current candidate has no named branch variant",
    "INTCALC-OBL-007": "requires category-balance group-boundary/order variants; current candidate has no named branch variant",
    "TRANREPT-OBL-003": "requires EOF receiver/retention variant; current candidate has no named branch variant",
    "TRANREPT-OBL-004": "requires card-break and lookup present/missing variants; current candidate has no named branch variant",
    "TRANREPT-OBL-005": "requires page-boundary volume/state variant; current candidate has no named branch variant",
    "TRANREPT-OBL-007": "requires EOF retained/current amount variant; current candidate has no named branch variant",
    "TRANREPT-OBL-008": "requires final account-total observation-boundary variant; current candidate has no named branch variant",
}

DIAGNOSTICS_ONLY_OBLIGATIONS = {
    "POSTTRAN-OBL-008",
    "POSTTRAN-OBL-009",
    "TRANREPT-OBL-003",
    "TRANREPT-OBL-007",
    "TRANREPT-OBL-008",
}

TRACK_KEYWORDS = {
    "posting": ["posting", "postDailyTransactions"],
    "interest": ["interest", "generateInterestTransactions"],
    "reporting": ["report", "reporting", "generateTransactionReport"],
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_openapi_from_response(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"```ya?ml\s*\n(.*?)```", text, re.S | re.I)
    if m:
        text = m.group(1)
    else:
        m = re.search(r"(^openapi:\s*[\s\S]+)", text, re.M)
        if m:
            text = m.group(1)
    return yaml.safe_load(text)


def resolve_schema(spec: dict[str, Any], schema: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(schema, dict):
        return {}
    ref = schema.get("$ref")
    if ref:
        return spec.get("components", {}).get("schemas", {}).get(ref.split("/")[-1], {})
    return schema


def schema_summary(spec: dict[str, Any], path: str, method: str) -> dict[str, Any]:
    op = spec["paths"][path][method]
    raw = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
    schema = resolve_schema(spec, raw)
    props = schema.get("properties") or {}
    nested = {}
    for name, prop in props.items():
        prop_res = resolve_schema(spec, prop)
        item = resolve_schema(spec, prop_res.get("items")) if isinstance(prop_res, dict) else {}
        if item.get("properties"):
            nested[name] = sorted(item["properties"].keys())
        elif prop_res.get("properties"):
            nested[name] = sorted(prop_res["properties"].keys())
    return {
        "schemaRef": raw.get("$ref") if isinstance(raw, dict) else None,
        "type": schema.get("type"),
        "required": sorted(schema.get("required") or []),
        "properties": sorted(props.keys()),
        "additionalProperties": schema.get("additionalProperties"),
        "nestedProperties": nested,
    }


def build_contract_specs(pins: dict[str, Any]) -> dict[str, dict[str, Any]]:
    specs = {}
    for c in pins["contracts"]:
        cid = c["contractId"]
        if cid == "E3-01-SDD-stage6r3":
            path = SDD_OPENAPI
            spec = yaml.safe_load(path.read_text(encoding="utf-8"))
        else:
            path = Path(c["path"])
            spec = extract_openapi_from_response(path)
        specs[cid] = spec
    return specs


def track_for_obligation(obl_id: str) -> str:
    for prefix, track in TRACKS.items():
        if obl_id.startswith(prefix):
            return track
    raise KeyError(obl_id)


def operation_track(op: dict[str, Any]) -> str:
    s = (op["operationId"] + " " + op["path"]).lower()
    if "interest" in s:
        return "interest"
    if "report" in s:
        return "reporting"
    return "posting"


def has_rich_surface(summary: dict[str, Any], track: str) -> bool:
    """True only when declared schema fields explicitly map to track resources."""
    return has_explicit_surface(summary, track)


def has_data_surface(summary: dict[str, Any], track: str) -> bool:
    names = set(summary["properties"])
    if track == "posting":
        return bool(names & {"dailyTransactions", "transactions"})
    if track == "interest":
        return bool(names & {"parameterDate", "idPrefix", "transactionIdPrefix"})
    if track == "reporting":
        return bool(names & {"transactions", "dateParameterRecords", "dateParameters"})
    return False


def status_for(rule: dict[str, str], summary: dict[str, Any], contract_id: str, track: str) -> str:
    if contract_id == "E3-01-SDD-stage6r3":
        # SDD approved request schemas are closed empty objects. Do not add selectors.
        if rule["base"] in {"not_mapped", "not_expressible", "precondition_indeterminate", "observation_inadmissible"}:
            return rule["base"]
        return "conditioned_on_external_fixture"
    if rule.get("surface_if_rich") and has_rich_surface(summary, track):
        return rule["surface_if_rich"]
    if rule.get("surface_if_data") and has_data_surface(summary, track):
        return rule["surface_if_data"]
    return rule["base"]


def has_explicit_surface(summary: dict[str, Any], track: str) -> bool:
    names = set(summary["properties"])
    if "bindings" in names:
        return True
    return bool(names & set(FIELD_SOURCE_BY_TRACK[track]))


def dimensions_for(status: str, obligation_id: str, plan: dict[str, Any]) -> dict[str, bool]:
    diagnostics_only = obligation_id in DIAGNOSTICS_ONLY_OBLIGATIONS
    blocked = plan.get("generativeUse") in {"blocked", "diagnostics_only_non_generative"}
    return {
        "inventory_cell": True,
        "surface_expressible": status == "expressible_by_surface",
        "fixture_variant_required": status == "conditioned_on_external_fixture",
        "generative_admissible": status == "expressible_by_surface" and not diagnostics_only and not blocked,
        "exercised_by_package": False,
    }


def operation_plan(summary: dict[str, Any], track: str, contract_id: str, status: str, obligation_id: str) -> dict[str, Any]:
    properties = summary["properties"]
    selectors = []
    constraints = []
    body: Any = "not_materialized_pre_campaign"
    blocks = []
    selection_mode = "schema_field_or_external_fixture_schedule"
    generative_use = "candidate_mapping_only_unexercised"

    diagnostics_only = obligation_id in DIAGNOSTICS_ONLY_OBLIGATIONS

    if contract_id == "E3-01-SDD-stage6r3":
        body = {}
        selection_mode = "external_fixture_schedule_only"
        constraints.append("request schema is closed empty object: type=object, properties={}, additionalProperties=false")
        blocks.append("No request selector can be added for SDD; all substantive variation must be external fixture scheduling or remains blocked.")
        if obligation_id in GUARD_SENSITIVE_VARIANT_REQUIRED:
            blocks.append(GUARD_SENSITIVE_VARIANT_REQUIRED[obligation_id])
            generative_use = "blocked"
    else:
        if not diagnostics_only:
            if "bindings" in properties:
                selectors.append({"field": "bindings", "allowedSource": f"candidate fixture {track} explicit DD bindings only", "constraint": "only schema-declared binding keys; no extra selector fields; not a business-branch selector"})
            for field in properties:
                if field in {"dailyTransactions", "transactions"}:
                    selectors.append({"field": field, "allowedSource": RESOURCE_MAP[track]["input_records"], "constraint": "whole record/object values from contract schema or pinned fixture logical records only"})
                elif field in {"dateParameterRecords", "dateParameters"}:
                    selectors.append({"field": field, "allowedSource": ["DATEPARM"], "constraint": "X(10)/date parameter records as schema permits; no post-observation mask"})
                elif field in {"parameterDate", "idPrefix", "transactionIdPrefix"}:
                    selectors.append({"field": field, "allowedSource": ["PARMFILE", "contract scalar field"], "constraint": "string/scalar per request schema; cannot select account group, rate branch, EOF, or fallback state"})
                elif field in FIELD_SOURCE_BY_TRACK[track]:
                    selectors.append({"field": field, "allowedSource": FIELD_SOURCE_BY_TRACK[track][field], "constraint": "explicit field/schema/track DD role map only; no token-based resource expansion"})
        if not selectors and status == "expressible_by_surface" and not diagnostics_only:
            blocks.append("No request field exposes the required resource/data selector for this obligation.")
            generative_use = "blocked"
        body = "deterministic_from_allowed_schema_fields_when_case_is_later_frozen"

    if status == "conditioned_on_external_fixture" and obligation_id in GUARD_SENSITIVE_VARIANT_REQUIRED:
        blocks.append(GUARD_SENSITIVE_VARIANT_REQUIRED[obligation_id])
        generative_use = "blocked"

    if status in {"not_expressible", "not_mapped", "precondition_indeterminate", "observation_inadmissible"}:
        blocks.append("Do not generate an executable T3 case for this obligation/contract cell without a reviewed mapping amendment.")
        generative_use = "diagnostics_only_non_generative" if diagnostics_only else "blocked"

    if diagnostics_only:
        selectors = []
        blocks.append("Executable selectors intentionally omitted: this reporting EOF/raw/order or posting partial-effect cell is diagnostics-only and non-generative.")
        generative_use = "diagnostics_only_non_generative"

    plan = {
        "requestBody": body,
        "fieldSelectors": selectors,
        "constraints": constraints,
        "fixtureSelection": f"track={track}; choose only candidate fixture(s) listed in candidateFixtures; no selector endpoint/operation added",
        "fixtureVariant": None,
        "selectionMode": selection_mode,
        "generativeUse": generative_use,
        "officialExerciseStatus": "not_exercised_by_official_package",
        "newSelectorsIntroduced": False,
        "blocks": sorted(set(blocks)),
    }
    return plan


def fixture_records(fixture_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for f in fixture_manifest["fixtures"]:
        pkg = fixture_manifest["packages"][f["track"]]
        resources = []
        for dd, meta in sorted(pkg["inventory"]["files"].items()):
            resources.append({"dd": dd, "bytes": meta["bytes"], "sha256": meta["sha256"]})
        keys = {}
        for item in pkg.get("indexed", []):
            keys[item["dd"]] = {
                "primaryKeys": item.get("keys", []),
                "alternateKeyName": item.get("alternateKeyName"),
                "alternateKeys": item.get("alternateKeys", []),
                "recordCount": item.get("recordCount"),
                "recordSize": item.get("recordSize"),
            }
        for item in pkg.get("sequential", []):
            keys[item["dd"]] = {
                "recordCount": item.get("recordCount"),
                "recordSize": item.get("recordSize"),
                "sha256": item.get("sha256"),
            }
        out.append({
            "fixtureId": f["fixtureId"],
            "track": f["track"],
            "status": f["status"],
            "packagePath": f["packagePath"],
            "treeSha256": pkg["inventory"]["treeSha256"],
            "resources": resources,
            "keys": keys,
        })
    return out


def main() -> None:
    reference = load_json(REFERENCE)
    witnesses = load_json(WITNESSES)
    review = load_json(REVIEW)
    inventory = load_json(INVENTORY)
    pins = load_json(PINS)
    fixture_manifest = load_json(FIXTURES)
    specs = build_contract_specs(pins)

    fixture_by_track = {f["track"]: f for f in fixture_records(fixture_manifest)}
    ops_by_contract_track: dict[tuple[str, str], dict[str, Any]] = {}
    for op in inventory["operations"]:
        ops_by_contract_track[(op["contractId"], operation_track(op))] = op

    contracts = [c["contractId"] for c in inventory["contracts"]]
    witness_by_obl = {w["obligationId"]: w for w in witnesses["obligations"]}

    obligations_out = []
    for obl in reference["obligations"]:
        oid = obl["id"]
        track = track_for_obligation(oid)
        rule = OBLIGATION_RULES[oid]
        mappings = []
        for cid in contracts:
            op = ops_by_contract_track[(cid, track)]
            spec = specs[cid]
            req = schema_summary(spec, op["path"], op["method"].lower())
            status = status_for(rule, req, cid, track)
            mappings.append({
                "contractId": cid,
                "operation": {
                    "operationId": op["operationId"],
                    "method": op["method"].lower(),
                    "path": op["path"],
                    "documentedResponses": op["documentedResponses"],
                    "requestBodyRequired": op["requestBodyRequired"],
                    "requestSchema": req,
                },
                "applicabilityStatus": status,
                "sourceObligations": [oid],
                "candidateFixtures": [{
                    "fixtureId": fixture_by_track[track]["fixtureId"],
                    "track": track,
                    "status": fixture_by_track[track]["status"],
                    "resources": RESOURCE_MAP[track],
                    "concreteKeys": fixture_by_track[track]["keys"],
                }],
                "t3DeterministicMapping": (plan := operation_plan(req, track, cid, status, oid)),
                "applicabilityDimensions": dimensions_for(status, oid, plan),
                "mappingRationale": rule["reason"],
                "nonExpectedResultGuard": "No caso, resultado esperado, oráculo, status HTTP de sucesso/falha ou cobertura é criado por esta matriz.",
            })
        obligations_out.append({
            "obligationId": oid,
            "capability": obl["capability"],
            "track": track,
            "title": obl["title"],
            "preconditions": obl["preconditions"],
            "guard_or_transition": obl["guard_or_transition"],
            "required_observation": obl["required_observation"],
            "decidable_expectation_from_reference_not_instantiated": obl["decidable_expectation"],
            "limits_and_review_notes": obl["limits_and_review_notes"],
            "source_anchors": obl["source_anchors"],
            "referenceWitness": witness_by_obl.get(oid),
            "contractMappings": mappings,
        })

    denominator = {
        "calculation": "programmatic",
        "obligations": len(reference["obligations"]),
        "contracts": len(inventory["contracts"]),
        "operations": len(inventory["operations"]),
        "tracks": len(set(TRACKS.values())),
        "candidateFixtures": len(fixture_manifest["fixtures"]),
        "obligation_contract_cells": len(reference["obligations"]) * len(inventory["contracts"]),
        "mapped_contract_cells": sum(len(o["contractMappings"]) for o in obligations_out),
        "status_counts": {},
        "by_track": {},
    }
    for o in obligations_out:
        denominator["by_track"].setdefault(o["track"], {"obligations": 0, "contract_cells": 0})
        denominator["by_track"][o["track"]]["obligations"] += 1
        denominator["by_track"][o["track"]]["contract_cells"] += len(o["contractMappings"])
        for m in o["contractMappings"]:
            denominator["status_counts"][m["applicabilityStatus"]] = denominator["status_counts"].get(m["applicabilityStatus"], 0) + 1

    all_mappings = [m for o in obligations_out for m in o["contractMappings"]]
    denominator["dimensions"] = {
        "inventory_cells": len(all_mappings),
        "surface_expressible_cells": sum(1 for m in all_mappings if m["applicabilityDimensions"]["surface_expressible"]),
        "fixture_variant_required_cells": sum(1 for m in all_mappings if m["applicabilityDimensions"]["fixture_variant_required"]),
        "generative_admissible_cells": sum(1 for m in all_mappings if m["applicabilityDimensions"]["generative_admissible"]),
        "exercised_by_package_cells": sum(1 for m in all_mappings if m["applicabilityDimensions"]["exercised_by_package"]),
    }
    denominator["plan_counts"] = {
        "supported_unexercised": sum(1 for m in all_mappings if m["t3DeterministicMapping"].get("generativeUse") == "candidate_mapping_only_unexercised"),
        "pending_or_blocked": sum(1 for m in all_mappings if m["t3DeterministicMapping"].get("generativeUse") in {"blocked", "diagnostics_only_non_generative"}),
        "diagnostics_only_non_generative": sum(1 for m in all_mappings if m["t3DeterministicMapping"].get("generativeUse") == "diagnostics_only_non_generative"),
    }

    matrix = {
        "kind": "p3-pre-campaign-applicability-mapping-v2",
        "status": "candidate_needs_review",
        "campaign_authorization": False,
        "generated_from": {
            "reference_model": {"path": str(REFERENCE.relative_to(CYCLE)), "sha256": sha256(REFERENCE), "status": reference.get("status")},
            "reference_witnesses": {"path": str(WITNESSES.relative_to(CYCLE)), "sha256": sha256(WITNESSES)},
            "reference_review_v4": {"path": str(REVIEW.relative_to(CYCLE)), "sha256": sha256(REVIEW), "pass_for_campaign_readiness": review["final_assessment"]["pass_for_campaign_readiness"]},
            "operation_inventory": {"path": str(INVENTORY.relative_to(CYCLE)), "sha256": sha256(INVENTORY)},
            "contract_pins": {"path": str(PINS.relative_to(CYCLE)), "sha256": sha256(PINS)},
            "fixture_manifest": {"path": str(FIXTURES.relative_to(CYCLE)), "sha256": sha256(FIXTURES), "status": fixture_manifest["status"]},
        },
        "excluded_inputs_policy": [
            "No runtime/API results, coverage, oracle outputs, campaign suites, quarantine, or expected-result files are read to choose expectations.",
            "The matrix is comparative applicability only; it preserves the frozen reference inventory and public contract surfaces.",
            "SDD request bodies remain {} with no new operations, selectors, or request fields.",
            "No cell is marked as officially exercised by the current package; this artifact does not create official cases or expected results.",
        ],
        "status_taxonomy": STATUS_TAXONOMY,
        "contracts": inventory["contracts"],
        "fixtures": list(fixture_by_track.values()),
        "denominators": denominator,
        "obligations": obligations_out,
        "limitations_review": [
            "candidate_needs_review does not authorize campaign execution or official fixture promotion.",
            "Expressible/conditioned statuses are mapping capability statuses, not pass/fail outcomes and not expected results.",
            "Original E1/E2 contracts are parsed only for operation/request schema shape; no API/runtime implementation is inferred from them.",
            "T3 mapping is deterministic only where request schema exposes explicit mapped fields or fixture scheduling is explicit; blocked/diagnostics-only cells require amendment rather than invented selectors.",
            "Reference v4 PASS is limited to abstract path selection; it is not a complete oracle or COBOL equivalence proof.",
        ],
    }
    out = ROOT / "applicability_matrix.json"
    out.write_text(json.dumps(matrix, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out), "denominators": denominator}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

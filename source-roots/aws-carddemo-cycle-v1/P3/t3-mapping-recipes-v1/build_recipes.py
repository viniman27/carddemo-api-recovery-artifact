#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

P3 = Path(__file__).resolve().parents[1]
ROOT = P3.parents[2]
MAPPER_ROOT = P3 / "t3-mapper-preparation-v1"
sys.path.insert(0, str(MAPPER_ROOT / "src"))
from t3_mapper import FixtureIndex, build_request_from_explicit_mapping, compatibility_inventory  # noqa: E402

OUT = P3 / "t3-mapping-recipes-v1"
PINS = P3 / "suite-adapters-preflight-v1/evidence-real-preflight-20260915T-synthetic/contract-pins.json"
OPS = P3 / "suite-adapters-preflight-v1/evidence-real-preflight-20260915T-synthetic/operation-inventory.json"
MATRIX = P3 / "applicability-mapping-v3/applicability_matrix.json"
FIXTURE_PACKAGE = P3 / "fixture-materialization-v2/package"
FIXTURE_MANIFEST = FIXTURE_PACKAGE / "manifest.json"

TRACK_FIXTURES = {
    "posting": "posting.candidate-v1-physical-v2",
    "interest": "interest.candidate-v1-physical-v2",
    "reporting": "reporting.candidate-v1-physical-v2",
}
TRACK_BY_OPERATION = {
    "postDailyTransactions": "posting",
    "posting": "posting",
    "generateInterestTransactions": "interest",
    "interest": "interest",
    "generateTransactionReport": "reporting",
    "reporting": "reporting",
}

TRANSACTION_FIELDS = [
    ["transactionId", 0, 16], ["typeCode", 16, 18], ["categoryCode", 18, 22], ["source", 22, 32],
    ["description", 32, 132], ["amount", 132, 143], ["merchantId", 143, 152], ["merchantName", 152, 202],
    ["merchantCity", 202, 252], ["merchantZip", 252, 262], ["cardNumber", 262, 278],
    ["originalTimestamp", 278, 304], ["processingTimestamp", 304, 330], ["filler", 330, 350],
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jdump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def load_openapi(path: str):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def resolve(doc, schema):
    if isinstance(schema, dict) and "$ref" in schema:
        node = doc
        for part in schema["$ref"][2:].split("/"):
            node = node[part]
        return resolve(doc, node)
    return schema


def operation_schema(doc, method, path):
    op = doc["paths"][path][method]
    return resolve(doc, op["requestBody"]["content"]["application/json"]["schema"])


def make_fixture_index(real_manifest):
    fixtures = []
    for f in real_manifest["fixtures"]:
        track = f["track"]
        pkg = real_manifest["packages"][track]
        resources = []
        for dd, meta in pkg["inventory"]["files"].items():
            resources.append({"dd": dd, "path": dd, "bytes": meta["bytes"], "sha256": meta["sha256"]})
        keys = {}
        for row in pkg.get("indexed", []):
            keys.setdefault(row["dd"], {})["primary"] = row.get("keys", [])
            if row.get("alternateKeys"):
                keys[row["dd"]]["alternate"] = row["alternateKeys"]
        fixtures.append({
            "fixtureId": f["fixtureId"],
            "track": track,
            "packagePath": str(FIXTURE_PACKAGE / f["packagePath"]),
            "resources": resources,
            "bindings": {r["dd"]: r["path"] for r in resources},
            "keys": keys,
            "status": f["status"],
        })
    return {"kind": "t3-recipe-fixture-index", "officialFixture": False, "fixtures": fixtures}


def selector_binding(dd, authority):
    return {"fromBinding": dd, "authority": authority}


def contract_scalar(value, authority):
    return {"fromContractScalar": {"value": value, "authority": authority}}


def records(dd, record_len, fmt, authority, numeric=None):
    spec = {"dd": dd, "recordLength": record_len, "format": fmt, "authority": authority}
    if numeric:
        spec["numericFields"] = numeric
    return {"fromSequentialRecords": spec}


def parm_selector(field):
    return {"fromBytes": "PARMFILE", "encoding": "utf8", "authority": f"fixture-materialization-v2/package/manifest.json packages.interest.sequential PARMFILE supplies {field}"}


def date_records(field):
    return records("DATEPARM", 80, "utf8Strings", f"fixture resource DATEPARM byte spans 0..80 for {field}")


def tx_selector(schema_style):
    if schema_style == "raw_objects":
        return records("DALYTRAN", 350, "rawBase64Objects", "fixture resource DALYTRAN 350-byte records; raw contract TransactionInput")
    if schema_style == "raw_strings_posting":
        return records("DALYTRAN", 350, "base64Strings", "fixture resource DALYTRAN 350-byte records; raw base64 contract string")
    if schema_style == "sem_e2_1_posting":
        return records("DALYTRAN", 350, "transactionObjects", "fixture resource DALYTRAN byte spans CVTRA05Y", ["amount"])
    if schema_style == "sem_e2_23_posting":
        return records("DALYTRAN", 350, "transactionObjects", "fixture resource DALYTRAN byte spans CVTRA05Y", ["categoryCode", "amount", "merchantId"])
    if schema_style == "raw_objects_report":
        return records("TRANFILE", 350, "rawBase64Objects", "fixture resource TRANFILE 350-byte records; raw contract TransactionInput")
    if schema_style == "raw_strings_report":
        return records("TRANFILE", 350, "base64Strings", "fixture resource TRANFILE 350-byte records; raw base64 contract string")
    if schema_style == "sem_e2_1_report":
        return records("TRANFILE", 350, "transactionObjects", "fixture resource TRANFILE byte spans CVTRA05Y", ["amount"])
    if schema_style == "sem_e2_23_report":
        return records("TRANFILE", 350, "transactionObjects", "fixture resource TRANFILE byte spans CVTRA05Y", ["categoryCode", "amount", "merchantId"])
    raise AssertionError(schema_style)


def build_body(cid, opid, path):
    # SDD: preserve closed empty object, no selector surface.
    if cid.startswith("E3"):
        return {}, True
    if opid == "postDailyTransactions":
        if cid == "E1-1":
            return {"object": {"dailyTransactions": tx_selector("raw_objects"), "transactionFile": selector_binding("TRANFILE", "fieldSelectors transactionFile->TRANFILE"), "crossReferenceFile": selector_binding("XREFFILE", "fieldSelectors crossReferenceFile->XREFFILE"), "accountFile": selector_binding("ACCTFILE", "fieldSelectors accountFile->ACCTFILE"), "categoryBalanceFile": selector_binding("TCATBALF", "fieldSelectors categoryBalanceFile->TCATBALF"), "rejectFile": contract_scalar("DALYREJS", "contract field rejectFile with matrix allowedSource DALYREJS; output binding name only")}}, False
        if cid == "E1-2":
            return {"object": {"dailyTransactions": tx_selector("raw_objects"), "transactionFile": selector_binding("TRANFILE", "fieldSelectors transactionFile->TRANFILE"), "crossReferenceFile": selector_binding("XREFFILE", "fieldSelectors crossReferenceFile->XREFFILE"), "accountFile": selector_binding("ACCTFILE", "fieldSelectors accountFile->ACCTFILE"), "categoryBalanceFile": selector_binding("TCATBALF", "fieldSelectors categoryBalanceFile->TCATBALF")}}, False
        if cid == "E1-3":
            return {"object": {"dailyTransactions": tx_selector("raw_strings_posting"), "cardCrossReference": selector_binding("XREFFILE", "fieldSelectors cardCrossReference->XREFFILE"), "accounts": selector_binding("ACCTFILE", "fieldSelectors accounts->ACCTFILE"), "categoryBalances": selector_binding("TCATBALF", "fieldSelectors categoryBalances->TCATBALF"), "transactionOutput": selector_binding("TRANFILE", "fieldSelectors transactionOutput->TRANFILE"), "rejectionOutput": contract_scalar("DALYREJS", "contract field rejectionOutput with matrix allowedSource DALYREJS; output binding name only")}}, False
        if cid == "E2-1":
            return {"object": {"dailyTransactions": tx_selector("sem_e2_1_posting")}}, False
        if cid == "E2-2":
            return {"object": {"bindings": {"object": {"crossReferences": selector_binding("XREFFILE", "bindings.crossReferences->XREFFILE"), "accounts": selector_binding("ACCTFILE", "bindings.accounts->ACCTFILE"), "categoryBalances": selector_binding("TCATBALF", "bindings.categoryBalances->TCATBALF"), "transactionOutput": selector_binding("TRANFILE", "bindings.transactionOutput->TRANFILE"), "rejectionOutput": contract_scalar("DALYREJS", "contract bindings.rejectionOutput; output binding name only")}}, "transactions": tx_selector("sem_e2_23_posting")}}, False
        if cid == "E2-3":
            return {"object": {"transactions": tx_selector("sem_e2_23_posting")}}, False
    if opid == "generateInterestTransactions":
        if cid == "E1-1":
            return {"object": {"parameterDate": parm_selector("parameterDate"), "parameterLength": {"fromResource": "PARMFILE", "format": "size", "authority": "PARMFILE byte size is 10"}, "categoryBalanceFile": selector_binding("TCATBALF", "fieldSelectors categoryBalanceFile->TCATBALF"), "crossReferenceFile": selector_binding("XREFFILE", "fieldSelectors crossReferenceFile->XREFFILE"), "disclosureGroupFile": selector_binding("DISCGRP", "fieldSelectors disclosureGroupFile->DISCGRP"), "accountFile": selector_binding("ACCTFILE", "fieldSelectors accountFile->ACCTFILE"), "outputTransactionFile": contract_scalar("TRANSACT", "contract field outputTransactionFile; output binding name only")}}, False
        name = "idPrefix" if cid == "E1-2" else "transactionIdPrefix"
        if cid == "E2-2":
            return {"object": {"bindings": {"object": {"categoryBalances": selector_binding("TCATBALF", "bindings.categoryBalances->TCATBALF"), "crossReferences": selector_binding("XREFFILE", "bindings.crossReferences->XREFFILE"), "accounts": selector_binding("ACCTFILE", "bindings.accounts->ACCTFILE"), "disclosureGroups": selector_binding("DISCGRP", "bindings.disclosureGroups->DISCGRP"), "transactionOutput": contract_scalar("TRANSACT", "contract bindings.transactionOutput; output binding name only")}}, "parameterDate": parm_selector("parameterDate"), "parameterLength": {"fromResource": "PARMFILE", "format": "size", "authority": "PARMFILE byte size is 10"}}}, False
        body = {name: parm_selector(name)}
        if cid in ["E1-2", "E1-3"]:
            body.update({"categoryBalanceFile" if cid == "E1-2" else "categoryBalances": selector_binding("TCATBALF", "fieldSelectors category balance->TCATBALF"), "crossReferenceFile" if cid == "E1-2" else "cardCrossReference": selector_binding("XREFFILE", "fieldSelectors cross reference->XREFFILE"), "accountFile" if cid == "E1-2" else "accounts": selector_binding("ACCTFILE", "fieldSelectors accounts->ACCTFILE"), "disclosureGroupFile" if cid == "E1-2" else "disclosureGroups": selector_binding("DISCGRP", "fieldSelectors disclosureGroups->DISCGRP")})
            if cid == "E1-3":
                body["transactionOutput"] = contract_scalar("TRANSACT", "contract field transactionOutput; output binding name only")
        return {"object": body}, False
    if opid == "generateTransactionReport":
        tx_style = "raw_objects_report" if cid in ["E1-1", "E1-2"] else "raw_strings_report" if cid == "E1-3" else "sem_e2_1_report" if cid == "E2-1" else "sem_e2_23_report"
        date_name = "dateParameters" if cid == "E1-2" else "dateParameterRecords"
        body = {"transactions": tx_selector(tx_style), date_name: date_records(date_name)}
        if cid == "E1-1":
            body.update({"crossReferenceFile": selector_binding("CARDXREF", "fieldSelectors crossReferenceFile->CARDXREF"), "transactionTypeFile": selector_binding("TRANTYPE", "fieldSelectors transactionTypeFile->TRANTYPE"), "transactionCategoryFile": selector_binding("TRANCATG", "fieldSelectors transactionCategoryFile->TRANCATG"), "reportFile": contract_scalar("REPORT", "contract field reportFile; output binding name only")})
        elif cid == "E1-2":
            body.update({"crossReferenceFile": selector_binding("CARDXREF", "fieldSelectors crossReferenceFile->CARDXREF"), "transactionTypeFile": selector_binding("TRANTYPE", "fieldSelectors transactionTypeFile->TRANTYPE"), "transactionCategoryFile": selector_binding("TRANCATG", "fieldSelectors transactionCategoryFile->TRANCATG")})
        elif cid == "E1-3":
            body.update({"cardCrossReference": selector_binding("CARDXREF", "fieldSelectors cardCrossReference->CARDXREF"), "transactionTypes": selector_binding("TRANTYPE", "fieldSelectors transactionTypes->TRANTYPE"), "transactionCategories": selector_binding("TRANCATG", "fieldSelectors transactionCategories->TRANCATG"), "reportOutput": contract_scalar("REPORT", "contract field reportOutput; output binding name only")})
        elif cid == "E2-2":
            body = {"bindings": {"object": {"crossReferences": selector_binding("CARDXREF", "bindings.crossReferences->CARDXREF"), "transactionTypes": selector_binding("TRANTYPE", "bindings.transactionTypes->TRANTYPE"), "transactionCategories": selector_binding("TRANCATG", "bindings.transactionCategories->TRANCATG"), "reportOutput": contract_scalar("REPORT", "contract bindings.reportOutput; output binding name only")}}, **body}
        return {"object": body}, False
    raise AssertionError((cid, opid, path))


def synthetic_homologous_index(real_index):
    synth_root = OUT / "synthetic-homologous-fixtures"
    if synth_root.exists():
        shutil.rmtree(synth_root)
    synth_root.mkdir(parents=True)
    tx = ("REPORT-IN---001 " + "01" + "0005" + "Internet  " + "candidate purchase".ljust(100) + "00000001200" + "123456789" + "Fixture Merchant".ljust(50) + "Sometown".ljust(50) + "70000000  " + "4111111111111111" + "2022-07-05-10.00.00.000000" + "2022-07-05-10.05.00.000000" + "".ljust(20)).encode("ascii")
    assert len(tx) == 350
    date = ("2022-01-01 2022-07-06".ljust(80)).encode("ascii")
    parm = b"2022071800"
    fixtures = []
    for f in real_index["fixtures"]:
        tdir = synth_root / f["track"]
        tdir.mkdir()
        resources = []
        for r in f["resources"]:
            dd = r["dd"]
            if dd in {"DALYTRAN", "TRANFILE"}:
                data = tx * (2 if dd in {"DALYTRAN", "TRANFILE"} else 1)
            elif dd == "DATEPARM":
                data = date
            elif dd == "PARMFILE":
                data = parm
            elif dd == "TRANFILE.empty":
                data = b""
            else:
                data = (dd.encode("ascii") + b" ") * 4
            (tdir / dd).write_bytes(data)
            resources.append({"dd": dd, "path": dd, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        fixtures.append({**f, "packagePath": str(tdir), "resources": resources, "bindings": {r["dd"]: r["path"] for r in resources}})
    return {"kind": "t3-synthetic-homologous-fixture-index", "officialFixture": False, "fixtures": fixtures}


def main():
    OUT.mkdir(exist_ok=True)
    pins = json.loads(PINS.read_text())
    ops = json.loads(OPS.read_text())
    matrix = json.loads(MATRIX.read_text())
    real_manifest = json.loads(FIXTURE_MANIFEST.read_text())
    fixture_index_doc = make_fixture_index(real_manifest)
    recipes = []
    for op in ops["operations"]:
        cid, opid, path, method = op["contractId"], op["operationId"], op["path"], op["method"]
        track = TRACK_BY_OPERATION[opid]
        body, sdd = build_body(cid, opid, path)
        pin = next(c for c in pins["contracts"] if c["contractId"] == cid)
        recipe = {
            "recipeId": f"{cid}:{track}:{opid}:{path}",
            "contractId": cid,
            "track": track,
            "operationId": opid,
            "operation": {"method": method, "path": path},
            "fixtureSelection": None if sdd else {"fixtureId": TRACK_FIXTURES[track], "track": track, "status": "candidate_needs_review"},
            "requestBody": body,
            "sddConstantEmptyObject": sdd,
            "officialCampaign": False,
            "contractPin": {"path": pin["path"], "sha256": pin["sha256"], "bytes": pin["bytes"]},
            "sourcePolicy": {"noOracle": True, "noRuntimeResults": True, "parametricOnly": True},
        }
        recipes.append(recipe)
    recipes_doc = {
        "kind": "t3-mapping-recipes-v1",
        "status": "candidate_parametric_recipes_only_not_official_cases",
        "officialCampaign": False,
        "scope": {"operationCount": len(recipes), "cellRequestCountNotGenerated": 175},
        "inputs": {"contractPins": str(PINS.relative_to(ROOT)), "operationInventory": str(OPS.relative_to(ROOT)), "applicabilityMatrix": str(MATRIX.relative_to(ROOT)), "fixtureManifest": str(FIXTURE_MANIFEST.relative_to(ROOT))},
        "guardrails": ["no official AWS cases exported", "blocked cells keep no usable selectors", "SDD remains closed {} only where contract schema is closed empty object", "selectors cite fixture resources, byte spans, bindings, or contract-authorized scalars"],
        "recordLayouts": {"CVTRA05Y": [{"name": n, "byteStart": a, "byteEndExclusive": b} for n, a, b in TRANSACTION_FIELDS], "DATEPARM": [{"name": "dateParameterRecord", "byteStart": 0, "byteEndExclusive": 80}], "PARMFILE": [{"name": "parameterDate", "byteStart": 0, "byteEndExclusive": 10}]},
        "recipes": recipes,
    }
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object", "required": ["kind", "recipes", "officialCampaign"],
        "properties": {"kind": {"const": "t3-mapping-recipes-v1"}, "officialCampaign": {"const": False}, "recipes": {"type": "array", "minItems": 21, "maxItems": 21, "items": {"type": "object", "required": ["recipeId", "contractId", "track", "operation", "requestBody", "officialCampaign"], "properties": {"officialCampaign": {"const": False}, "operation": {"type": "object", "required": ["method", "path"]}}}}}
    }
    Draft202012Validator(schema).validate(recipes_doc)
    jdump(OUT / "recipe-schema.json", schema)
    jdump(OUT / "recipes.json", recipes_doc)
    jdump(OUT / "fixture-index.json", fixture_index_doc)
    synth = synthetic_homologous_index(fixture_index_doc)
    jdump(OUT / "synthetic-fixture-index.json", synth)

    # Static contract/recipe refs and synthetic compilation qualification. No request bodies are written.
    fidx = FixtureIndex.from_manifest(synth)
    compiled = []
    blocked = []
    for r in recipes:
        pin = next(c for c in pins["contracts"] if c["contractId"] == r["contractId"])
        doc = load_openapi(pin["path"])
        try:
            req, evidence = build_request_from_explicit_mapping(r, fidx, doc)
            compiled.append({"recipeId": r["recipeId"], "schemaValid": evidence["schemaValidation"]["valid"], "sourceboundValueCount": len(evidence.get("sourceboundValues", [])), "sddConstantEmptyObject": evidence["sddConstantEmptyObject"]})
        except Exception as e:
            blocked.append({"recipeId": r["recipeId"], "error": type(e).__name__, "message": str(e), "details": getattr(e, "details", {})})
    inv = compatibility_inventory(matrix)
    source_counts = Counter()
    for r in recipes:
        text = json.dumps(r)
        for key in ["fromBinding", "fromBytes", "fromResource", "fromSequentialRecords", "fromContractScalar"]:
            source_counts[key] += text.count(key)
    report = {
        "kind": "t3-mapping-recipes-v1-validation-report",
        "officialCampaign": False,
        "operationRecipes": len(recipes),
        "compiledWithSyntheticHomologousFixtures": len(compiled),
        "compileFailures": blocked,
        "sourceboundSelectorCounts": dict(source_counts),
        "compiledSourceboundValueTotal": sum(x["sourceboundValueCount"] for x in compiled),
        "sddRecipes": sum(1 for x in compiled if x["sddConstantEmptyObject"]),
        "nonSddRecipes": sum(1 for x in compiled if not x["sddConstantEmptyObject"]),
        "compatInventoryTotals": inv["totals"],
        "blockedCellsNoUsableSelectorsPreserved": sum(1 for c in inv["cells"] if c["status"] == "blocked"),
        "recipeSchemaValidated": True,
        "contractRefsValidated": len(compiled) == len(recipes) and not blocked,
    }
    jdump(OUT / "compatibility-inventory-v1.json", inv)
    jdump(OUT / "validation-report.json", report)
    print(json.dumps(report, sort_keys=True))

if __name__ == "__main__":
    main()

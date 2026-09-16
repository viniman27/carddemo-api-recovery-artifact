from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from .evidence import verify_record_provenance
from .fixtures import Fixture


def _money(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _has_bytes(record: dict[str, Any], failures: list[str], label: str = "rawBytes") -> None:
    if label not in record:
        failures.append(f"{label} missing")
    elif record[label] == "":
        failures.append(f"{label} empty")
    elif not isinstance(record[label], str):
        failures.append(f"{label} must be a string captured from raw output bytes")


def _has_provenance(record: dict[str, Any], failures: list[str], context: str) -> None:
    provenance = record.get("provenance")
    if not isinstance(provenance, dict):
        failures.append(f"{context} provenance missing")
        return
    if provenance.get("kind") not in {"raw_file_record", "report_line", "command_log", "memory_map_record"}:
        failures.append(f"{context} provenance kind unsupported")
    if not provenance.get("artifact"):
        failures.append(f"{context} provenance artifact missing")
    if not (isinstance(provenance.get("recordOffset"), int) or isinstance(provenance.get("lineNumber"), int)):
        failures.append(f"{context} provenance must include recordOffset or lineNumber")
    fields = provenance.get("observedFields")
    if not isinstance(fields, list) or not fields:
        failures.append(f"{context} provenance observedFields missing")
    for failure in verify_record_provenance(record):
        failures.append(f"{context} {failure}")


def _failures_result(failures: list[str], source_expected: dict[str, Any], observed: Any) -> dict[str, Any]:
    return {"ok": not failures, "details": {"sourceExpected": source_expected, "observed": observed, "failures": failures}}


def check_posttran_003(fixture: Fixture) -> dict[str, Any]:
    records = fixture.observations.get("posting", {}).get("acceptedTransactions", [])
    failures: list[str] = []
    expected = {"copiedFields": ["id", "type", "category", "source", "description", "amount", "merchant", "card", "origTs"], "procTs": "current-date-derived-not-fixture-copied"}
    if not records:
        failures.append("no accepted transaction observed")
        return _failures_result(failures, expected, records)
    for record in records:
        _has_bytes(record, failures)
        _has_provenance(record, failures, f"accepted transaction {record.get('id')}")
        daily = record.get("daily", {})
        posted = record.get("posted", {})
        for field in expected["copiedFields"]:
            if daily.get(field) != posted.get(field):
                failures.append(f"accepted transaction {record.get('id')} field {field} not copied from daily")
        if posted.get("procTs") == daily.get("procTs"):
            failures.append(f"accepted transaction {record.get('id')} procTs was copied instead of regenerated")
        if not posted.get("procTs"):
            failures.append(f"accepted transaction {record.get('id')} procTs missing")
    return _failures_result(failures, expected, records)


def check_posttran_004(fixture: Fixture) -> dict[str, Any]:
    rejects = fixture.observations.get("posting", {}).get("rejects", [])
    observed = [r for r in rejects if r.get("case") == "missing-card"]
    failures: list[str] = []
    expected = {"reason": "100", "descriptionContains": "INVALID CARD NUMBER", "noPostedTransaction": True}
    if not observed:
        failures.append("missing-card rejection not observed")
    for reject in observed:
        _has_bytes(reject, failures)
        _has_provenance(reject, failures, f"reject {reject.get('case')}")
        if str(reject.get("reason")) != "100":
            failures.append("missing-card reject reason is not 100")
        if "INVALID CARD NUMBER" not in reject.get("description", ""):
            failures.append("missing-card reject description lacks INVALID CARD NUMBER")
        if reject.get("postedTransactionWritten") is not False:
            failures.append("missing-card case wrote or did not report absence of posted transaction")
    return _failures_result(failures, expected, observed)


def check_posttran_006(fixture: Fixture) -> dict[str, Any]:
    posting = fixture.observations.get("posting", {})
    rejects = posting.get("rejects", [])
    failures: list[str] = []
    expected = {"returnCodeWhenRejectCountGreaterThanZero": 4, "rejectRecordPerValidationReason": True}
    if rejects and posting.get("returnCode") != 4:
        failures.append("return code is not 4 despite reject count > 0")
    for reject in rejects:
        if not reject.get("rejectRecordWritten"):
            failures.append(f"reject {reject.get('case')} did not write reject record")
        _has_bytes(reject, failures)
        _has_provenance(reject, failures, f"reject {reject.get('case')}")
    if not rejects:
        failures.append("no rejection observed for reject-record obligation")
    return _failures_result(failures, expected, {"returnCode": posting.get("returnCode"), "rejects": rejects})


def check_posttran_009(fixture: Fixture) -> dict[str, Any]:
    records = fixture.observations.get("posting", {}).get("acceptedTransactions", [])
    failures: list[str] = []
    expected = {"tranfileWriteAfterTcatbalAndAccountAttempted": True, "duplicateIdPrevalidated": False}
    if not records:
        failures.append("no accepted transaction observed")
    for record in records:
        effects = record.get("effects")
        if not isinstance(effects, list) or not effects:
            failures.append(f"transaction {record.get('id')} observed effect records missing; effectOrder flags are not accepted as COBOL write evidence")
            _has_provenance(record, failures, f"transaction {record.get('id')}")
            continue
        positions: dict[str, int] = {}
        for index, effect in enumerate(effects):
            if not isinstance(effect, dict):
                failures.append(f"transaction {record.get('id')} effect record is not an object")
                continue
            name = effect.get("name")
            if name:
                positions[str(name)] = index
            _has_provenance(effect, failures, f"transaction {record.get('id')} effect {name}")
        try:
            tcat = positions["tcatbal"]
            acct = positions["account"]
            tran = positions["tranfile"]
            if not (tcat < tran and acct < tran):
                failures.append(f"transaction {record.get('id')} did not write TRANFILE after TCATBAL and ACCOUNT")
        except KeyError:
            failures.append(f"transaction {record.get('id')} missing one of tcatbal/account/tranfile observed effects")
        if record.get("duplicatePrevalidated") is not False:
            failures.append(f"transaction {record.get('id')} claims duplicate prevalidation")
    return _failures_result(failures, expected, records)


def check_intcalc_005(fixture: Fixture) -> dict[str, Any]:
    transactions = fixture.observations.get("interest", {}).get("transactions", [])
    failures: list[str] = []
    expected: dict[str, Any] = {"zeroRateWritesTransaction": False, "formula": "(categoryBalance * annualRate) / 1200"}
    zero = [t for t in transactions if _money(t.get("annualRate", "0")) == Decimal("0.00")]
    nonzero = [t for t in transactions if _money(t.get("annualRate", "0")) != Decimal("0.00")]
    if not zero:
        failures.append("no zero-rate partition observed")
    for item in zero:
        _has_provenance(item, failures, f"zero-rate item {item.get('id')}")
        if item.get("transactionWritten") is not False:
            failures.append(f"zero-rate item {item.get('id')} wrote interest transaction")
    if not nonzero:
        failures.append("no nonzero-rate partition observed")
    for item in nonzero:
        _has_provenance(item, failures, f"nonzero-rate item {item.get('id')}")
        if item.get("transactionWritten") is True:
            _has_bytes(item, failures)
        calculated = (_money(item["categoryBalance"]) * _money(item["annualRate"]) / Decimal("1200")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        expected["monthlyInterestAmount"] = f"{calculated:.2f}"
        if item.get("transactionWritten") is not True:
            failures.append(f"nonzero-rate item {item.get('id')} did not write transaction")
        if _money(item.get("amount")) != calculated:
            failures.append(f"nonzero-rate item {item.get('id')} amount {item.get('amount')} != {calculated:.2f}")
    return _failures_result(failures, expected, transactions)


def check_intcalc_006(fixture: Fixture) -> dict[str, Any]:
    transactions = [t for t in fixture.observations.get("interest", {}).get("transactions", []) if t.get("transactionWritten")]
    failures: list[str] = []
    expected = {"type": "01", "category": "05", "source": "System", "descriptionPrefix": "Int. for a/c", "merchantZeroOrBlank": True, "cardFromXref": True}
    if not transactions:
        failures.append("no written interest transaction observed")
    for item in transactions:
        _has_provenance(item, failures, f"interest transaction {item.get('id')}")
        if item.get("type") != "01": failures.append("interest type is not 01")
        if item.get("category") != "05": failures.append("interest category is not 05")
        if item.get("source") != "System": failures.append("interest source is not System")
        if not str(item.get("description", "")).startswith("Int. for a/c"):
            failures.append("interest description prefix mismatch")
        if item.get("merchant") not in ("", "0", "000000000"):
            failures.append("interest merchant is not zero/blank")
        if item.get("card") != item.get("xrefCard"):
            failures.append("interest card not supplied from XREF")
        _has_bytes(item, failures)
    return _failures_result(failures, expected, transactions)


def _inside(date: str, start: str, end: str) -> bool:
    return start <= date <= end


def check_tranrept_002(fixture: Fixture) -> dict[str, Any]:
    reporting = fixture.observations.get("reporting", {})
    start, end = reporting.get("dateRange", [None, None])
    records = reporting.get("transactions", [])
    failures: list[str] = []
    expected = {"textualInclusiveRange": [start, end], "outsideRangeWritesDetail": False}
    for record in records:
        _has_provenance(record, failures, f"report transaction {record.get('id')}")
        expected_inside = _inside(record.get("procDate", ""), start, end)
        if bool(record.get("detailWritten")) != expected_inside:
            failures.append(f"record {record.get('id')} detailWritten={record.get('detailWritten')} expected {expected_inside}")
    return _failures_result(failures, expected, records)


def check_tranrept_006(fixture: Fixture) -> dict[str, Any]:
    reporting = fixture.observations.get("reporting", {})
    records = [r for r in reporting.get("transactions", []) if r.get("detailWritten")]
    failures: list[str] = []
    total = Decimal("0.00")
    expected = {"detailLinePerQualifiedTransaction": True, "accumulatesAmount": True}
    if not records:
        failures.append("no in-range detail record observed")
    for record in records:
        if not record.get("detailLine"):
            failures.append(f"record {record.get('id')} lacks detail line")
        _has_bytes(record, failures, "reportLineBytes")
        _has_provenance(record, failures, f"report detail {record.get('id')}")
        total += _money(record.get("amount"))
    expected["pageAndAccountTotalFromDetails"] = f"{total:.2f}"
    framing = reporting.get("reportFraming", {})
    if "pageTotal" not in reporting or "accountTotal" not in reporting:
        if framing.get("eofBeforeTotalsBranch") is True:
            failures.append("totals branch not observed before EOF; missing totals are inconclusive evidence, not semantic mismatch")
        else:
            failures.append("report totals missing without source EOF guard")
    else:
        if _money(reporting.get("pageTotal", "0")) != total:
            failures.append(f"page total {reporting.get('pageTotal')} != {total:.2f}")
        if _money(reporting.get("accountTotal", "0")) != total:
            failures.append(f"account total {reporting.get('accountTotal')} != {total:.2f}")
    return _failures_result(failures, expected, {"records": records, "pageTotal": reporting.get("pageTotal"), "accountTotal": reporting.get("accountTotal")})


CHECKERS = {
    "POSTTRAN-OBL-003": check_posttran_003,
    "POSTTRAN-OBL-004": check_posttran_004,
    "POSTTRAN-OBL-006": check_posttran_006,
    "POSTTRAN-OBL-009": check_posttran_009,
    "INTCALC-OBL-005": check_intcalc_005,
    "INTCALC-OBL-006": check_intcalc_006,
    "TRANREPT-OBL-002": check_tranrept_002,
    "TRANREPT-OBL-006": check_tranrept_006,
}

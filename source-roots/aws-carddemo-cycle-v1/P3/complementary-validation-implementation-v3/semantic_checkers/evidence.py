from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def verify_record_provenance(record: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    provenance = record.get("provenance")
    if not isinstance(provenance, dict):
        return ["provenance missing"]
    if provenance.get("kind") not in {"raw_file_record", "report_line", "command_log", "memory_map_record"}:
        failures.append("provenance kind unsupported")
    artifact = provenance.get("artifact")
    if not artifact:
        failures.append("provenance artifact missing")
        return failures
    path = Path(str(artifact))
    if not path.is_absolute() and not provenance.get("sha256"):
        return failures
    if not path.exists():
        failures.append(f"provenance artifact missing on disk: {artifact}")
        return failures
    data = path.read_bytes()
    expected_sha = provenance.get("sha256")
    actual_sha = hashlib.sha256(data).hexdigest()
    if expected_sha and expected_sha != actual_sha:
        failures.append(f"provenance sha mismatch for {artifact}: expected {expected_sha} observed {actual_sha}")
    offset = provenance.get("recordOffset")
    length = provenance.get("recordLength")
    if isinstance(offset, int) and isinstance(length, int):
        raw_hex = record.get("rawBytes") or record.get("reportLineBytes")
        if isinstance(raw_hex, str):
            try:
                expected = bytes.fromhex(raw_hex)
            except ValueError:
                failures.append("record raw hex is invalid")
            else:
                observed = data[offset:offset + length]
                if observed != expected:
                    failures.append("provenance byte slice does not match record raw bytes")
        elif offset < 0 or length < 0 or offset + length > len(data):
            failures.append("provenance byte slice is outside artifact")
    elif not isinstance(provenance.get("lineNumber"), int):
        failures.append("provenance must include recordOffset/recordLength or lineNumber")
    fields = provenance.get("observedFields")
    if not isinstance(fields, list) or not fields:
        failures.append("provenance observedFields missing")
    return failures


def evidence_failure_only(failures: list[str]) -> bool:
    if not failures:
        return False
    semantic_markers = (
        " not copied", "procTs was copied", "reason is not", "description lacks",
        "return code is not", "did not write reject", "claims duplicate prevalidation",
        "amount ", "type is not", "category is not", "source is not",
        "description prefix mismatch", "merchant is not", "card not supplied",
        "detailWritten=", "page total", "account total",
    )
    for failure in failures:
        if any(marker in failure for marker in semantic_markers):
            return False
    return True

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CYCLE_ROOT = ROOT.parents[1]
CATALOG_PATH = CYCLE_ROOT / "P3" / "complementary-validation-v2" / "scenario-catalog.json"

IMPLEMENTED_OBLIGATIONS = (
    "POSTTRAN-OBL-003",
    "POSTTRAN-OBL-004",
    "POSTTRAN-OBL-006",
    "POSTTRAN-OBL-009",
    "INTCALC-OBL-005",
    "INTCALC-OBL-006",
    "TRANREPT-OBL-002",
    "TRANREPT-OBL-006",
)


@dataclass(frozen=True)
class SourceVerification:
    verified_files: list[str]
    failures: list[str]


@dataclass
class SourceCatalog:
    source_base: Path
    obligations: dict[str, dict[str, Any]]
    scenario_records: dict[str, dict[str, Any]]

    def implemented_obligation_ids(self) -> list[str]:
        return [oid for oid in IMPLEMENTED_OBLIGATIONS if oid in self.obligations]

    def pending_obligation_ids(self) -> list[str]:
        return [oid for oid in self.obligations if oid not in IMPLEMENTED_OBLIGATIONS]

    def obligation(self, obligation_id: str) -> dict[str, Any]:
        return self.obligations[obligation_id]

    def scenario(self, obligation_id: str) -> dict[str, Any]:
        return self.scenario_records[obligation_id]

    def source_anchors(self, obligation_id: str) -> list[dict[str, Any]]:
        return self.obligation(obligation_id).get("source_anchors", [])

    def boundaries(self, obligation_id: str) -> list[str]:
        return self.scenario(obligation_id).get("boundaryPartitions", [])

    def verify_source_anchors(self) -> SourceVerification:
        expected: dict[str, str] = {}
        failures: list[str] = []
        for obligation in self.obligations.values():
            for anchor in obligation.get("source_anchors", []):
                path = anchor["path"]
                sha = anchor["sha256"]
                previous = expected.setdefault(path, sha)
                if previous != sha:
                    failures.append(f"conflicting sha for {path}: {previous} vs {sha}")
        verified_files: list[str] = []
        for rel_path, expected_sha in sorted(expected.items()):
            file_path = self.source_base / rel_path
            if not file_path.exists():
                failures.append(f"missing source file {rel_path}")
                continue
            actual_sha = hashlib.sha256(file_path.read_bytes()).hexdigest()
            if actual_sha != expected_sha:
                failures.append(f"sha mismatch {rel_path}: expected {expected_sha} observed {actual_sha}")
            else:
                verified_files.append(rel_path)
        return SourceVerification(verified_files=verified_files, failures=failures)


def load_default_catalog() -> SourceCatalog:
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return SourceCatalog(
        source_base=Path(data["sourceBase"]),
        obligations={item["id"]: item for item in data["obligations"]},
        scenario_records={item["obligationId"]: item for item in data["scenarioRecords"]},
    )

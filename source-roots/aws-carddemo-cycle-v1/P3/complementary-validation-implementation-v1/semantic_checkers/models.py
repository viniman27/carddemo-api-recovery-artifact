from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CheckStatus(Enum):
    PASS = "pass"
    FAILED = "failed"
    PENDING = "pending"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class CheckResult:
    obligation_id: str
    track: str
    status: CheckStatus
    source_anchors: list[dict[str, Any]]
    boundaries: list[str]
    details: dict[str, Any] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "obligationId": self.obligation_id,
            "track": self.track,
            "status": self.status.value,
            "sourceAnchors": self.source_anchors,
            "boundaries": self.boundaries,
            "details": self.details,
        }

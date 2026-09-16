from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Fixture:
    fixture_id: str
    description: str
    observations: dict[str, Any]
    evidence_class: str = "synthetic_review"


def load_fixture(path: str | Path) -> Fixture:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Fixture(
        fixture_id=data["fixtureId"],
        description=data.get("description", ""),
        observations=data["observations"],
        evidence_class=data.get("evidenceClass", "synthetic_review"),
    )

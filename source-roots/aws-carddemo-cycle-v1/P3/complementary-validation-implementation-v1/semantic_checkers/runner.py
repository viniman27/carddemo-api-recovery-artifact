from __future__ import annotations

from .checkers import CHECKERS
from .fixtures import Fixture
from .models import CheckResult, CheckStatus
from .source_catalog import load_default_catalog


def run_fixture_checks(fixture: Fixture, obligation_ids: list[str] | None = None) -> list[CheckResult]:
    catalog = load_default_catalog()
    ids = obligation_ids or list(catalog.obligations)
    results: list[CheckResult] = []
    for obligation_id in ids:
        obligation = catalog.obligation(obligation_id)
        track = obligation_id.split("-OBL-")[0].lower()
        anchors = catalog.source_anchors(obligation_id)
        boundaries = catalog.boundaries(obligation_id)
        if obligation_id not in CHECKERS:
            results.append(CheckResult(
                obligation_id=obligation_id,
                track=track,
                status=CheckStatus.PENDING,
                source_anchors=anchors,
                boundaries=boundaries,
                details={
                    "sourceExpected": obligation.get("decidable_expectation"),
                    "observed": None,
                    "pendingReason": "checker_not_implemented_in_v1_representative_slice",
                },
            ))
            continue
        outcome = CHECKERS[obligation_id](fixture)
        results.append(CheckResult(
            obligation_id=obligation_id,
            track=track,
            status=CheckStatus.PASS if outcome["ok"] else CheckStatus.FAILED,
            source_anchors=anchors,
            boundaries=boundaries,
            details=outcome["details"],
        ))
    return results

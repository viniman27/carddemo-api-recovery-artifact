from __future__ import annotations

from .checkers import CHECKERS
from .evidence import evidence_failure_only
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
        status = CheckStatus.FAILED
        details = outcome["details"]
        details["semanticOutcome"] = "pass" if outcome["ok"] else "failed"
        if outcome["ok"]:
            if fixture.evidence_class == "real_cobol_observation":
                status = CheckStatus.PASS
                details["evidenceSufficiency"] = {
                    "classification": "real_cobol_observation",
                    "businessConclusionAllowed": True,
                }
            else:
                status = CheckStatus.INCONCLUSIVE
                details["evidenceSufficiency"] = {
                    "classification": "synthetic_review_not_real_cobol_observation",
                    "businessConclusionAllowed": False,
                    "reason": "synthetic observations qualify checker behavior only; they are not API/COBOL campaign results",
                }
        elif fixture.evidence_class == "real_cobol_observation" and evidence_failure_only(details.get("failures", [])):
            status = CheckStatus.INCONCLUSIVE
            details["semanticOutcome"] = "inconclusive"
            details["evidenceSufficiency"] = {
                "classification": "missing_evidence",
                "businessConclusionAllowed": False,
                "reason": "available runtime bytes do not satisfy checker evidence guards; missing trace/provenance is not classified as semantic failure",
            }
        results.append(CheckResult(
            obligation_id=obligation_id,
            track=track,
            status=status,
            source_anchors=anchors,
            boundaries=boundaries,
            details=details,
        ))
    return results

#!/usr/bin/env python3
import hashlib
import json
import sys
from pathlib import Path

REQUIRED_STATUSES = {
    'not_executed', 'unchecked', 'inconclusive', 'nonexpressible',
    'no_observation', 'failed', 'pass', 'not_applicable'
}
REQUIRED_T3_ROLE = 'separate_mbt_battery'


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve_pin(root: Path, raw: str) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p
    # v2 directory is P3/complementary-validation-v2; repository root is parents[2].
    repo_root = root.parents[1]
    return repo_root / p


def validate(cat: dict, root=None) -> dict:
    root = Path(root or Path(__file__).resolve().parent).resolve()
    errors = []

    def err(message: str) -> None:
        errors.append(message)

    if cat.get('kind') != 'aws-carddemo-complementary-validation-catalog-v2':
        err('kind must be aws-carddemo-complementary-validation-catalog-v2')
    if cat.get('schemaRef') != 'schema/complementary-validation-v2.schema.json':
        err('schemaRef must point to schema/complementary-validation-v2.schema.json')

    statuses = set(cat.get('statusVocabulary', {}))
    missing_statuses = REQUIRED_STATUSES - statuses
    if missing_statuses:
        err(f'missing status vocabulary: {sorted(missing_statuses)}')

    obligations = cat.get('obligations', [])
    scenarios = cat.get('scenarioRecords', [])
    contracts = cat.get('contracts', [])
    operations = cat.get('operations', [])
    mapping = cat.get('obligationOperationMapping', [])
    obligation_ids = {o.get('id') for o in obligations}
    scenario_obligation_ids = [s.get('obligationId') for s in scenarios]

    if len(obligations) != 25 or len(obligation_ids) != 25:
        err('obligations must cover 25 unique IDs')
    if len(scenarios) != 25:
        err('scenarioRecords must contain exactly 25 records')
    if set(scenario_obligation_ids) != obligation_ids or len(set(scenario_obligation_ids)) != 25:
        err('scenario coverage must be by the 25 obligation IDs, not by scenario/test count proxy')
    if len(contracts) != 7:
        err('contracts must be 7')
    if len(operations) != 21:
        err('operations must be 21')
    if len(mapping) != 525:
        err('mapping must be 525 obligation×operation cells')

    op_keys = {(o.get('contractId'), o.get('operationId')) for o in operations}
    map_keys = {(m.get('obligationId'), m.get('contractId'), m.get('operationId')) for m in mapping}
    if len(op_keys) != 21:
        err('operations must be unique by contractId+operationId')
    if len(map_keys) != 525:
        err('mapping cells must be unique by obligationId+contractId+operationId')

    applicable = [m for m in mapping if m.get('applicability') == 'candidate_applicable_obligation_contract']
    not_applicable = [m for m in mapping if m.get('applicability') == 'not_applicable_other_track']
    if len(applicable) != 175:
        err(f'applicable cells must be 175, got {len(applicable)}')
    if len(not_applicable) != 350:
        err(f'not-applicable cells must be 350, got {len(not_applicable)}')
    for m in applicable:
        s = m.get('preExecutionStatus', {})
        expected = {'execution': 'not_executed', 'oracle': 'unchecked', 'observation': 'no_observation', 'semanticResult': 'inconclusive'}
        if s != expected:
            err(f'applicable pre-execution status wrong for {m.get("cellId")}: {s}')
    for m in not_applicable:
        s = m.get('preExecutionStatus', {})
        if set(s.values()) != {'not_applicable'}:
            err(f'N/A cell mixed with execution/oracle status for {m.get("cellId")}: {s}')

    den = cat.get('denominators', {})
    if den.get('semanticDenominatorPolicy', {}).get('neverUseAll525AsSemanticDenominator') is not True:
        err('all 525 cells must be forbidden as semantic denominator')
    pre = den.get('preExecution', {})
    if pre.get('allCandidateApplicableCells', {}).get('not_executed') != 175:
        err('preExecution applicable not_executed must be 175')
    if pre.get('allOperationCells', {}).get('not_applicable') != 350:
        err('preExecution allOperationCells not_applicable must be 350')
    if 'unobservable' in pre.get('allOperationCells', {}) or 'unobservable' in pre.get('allCandidateApplicableCells', {}):
        err('unobservable must not be used as a pre-execution denominator bucket')

    tdesign = cat.get('testConditionDesign', {})
    if tdesign.get('T3', {}).get('role') != REQUIRED_T3_ROLE or tdesign.get('T3', {}).get('preserveMethod') is not True:
        err('T3 must remain a separate MBT battery')
    shared = cat.get('sharedOracleBattery', {})
    if shared.get('reusedAcross') != ['T1', 'T2', 'T3', 'T4']:
        err('shared oracle battery must be explicitly reusable across T1-T4')
    if shared.get('independentCheckerAssessment') != 'pending_review_not_granted_by_this_design':
        err('independent checker assessment must remain pending')

    source_base = Path(cat.get('sourceBase', ''))
    source_hashes_verified = True
    if not source_base.is_dir():
        source_hashes_verified = False
        err(f'sourceBase missing: {source_base}')
    for scenario in scenarios:
        for field in ['conditionInitial', 'stimulusSemantics', 'guardOrModelTransitionRefs', 'observableEffects', 'independentOracleMethod', 'applicableMappingTo7Contracts21Ops']:
            if field not in scenario or scenario[field] in (None, '', [], {}):
                err(f'{scenario.get("scenarioId")} missing {field}')
        mapping_counts = scenario.get('applicableMappingTo7Contracts21Ops', {})
        if mapping_counts.get('applicableCount') != 7 or mapping_counts.get('notApplicableCount') != 14:
            err(f'{scenario.get("scenarioId")} must map to 7 applicable and 14 non-applicable operations')
        if scenario.get('independentOracleMethod', {}).get('qualification') != 'pending_review_not_granted_by_this_design':
            err(f'{scenario.get("scenarioId")} oracle qualification must remain pending')
        if scenario.get('independentOracleMethod', {}).get('noInventedExpectedNumericValues') is not True:
            err(f'{scenario.get("scenarioId")} must forbid invented numeric expected values')
        if not scenario.get('guardOrModelTransitionRefs', {}).get('transitionRefs'):
            err(f'{scenario.get("scenarioId")} must include MBT transitionRefs')
        for anchor in scenario.get('sourceAnchors', []):
            p = source_base / anchor.get('path', '')
            if not p.is_file():
                source_hashes_verified = False
                err(f'source anchor missing {scenario.get("obligationId")}: {anchor}')
                continue
            if _sha256(p) != anchor.get('sha256'):
                source_hashes_verified = False
                err(f'source anchor sha mismatch: {anchor.get("path")}')
            lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
            lo, hi = anchor.get('lines', [0, -1])
            if not (1 <= lo <= hi <= len(lines)):
                err(f'source anchor lines invalid: {anchor.get("path")}:{lo}-{hi}/{len(lines)}')

    for pin in cat.get('sourcePins', []):
        p = _resolve_pin(root, pin.get('path', ''))
        if not p.is_file():
            source_hashes_verified = False
            err(f'source pin missing: {pin}')
            continue
        if p.stat().st_size != pin.get('bytes') or _sha256(p) != pin.get('sha256'):
            source_hashes_verified = False
            err(f'source pin hash/size mismatch: {pin.get("path")}')

    checked = {
        'obligations': len(obligations),
        'scenarioRecords': len(scenarios),
        'coveredObligations': len(set(scenario_obligation_ids)),
        'coverageIsByObligationIds': set(scenario_obligation_ids) == obligation_ids and len(set(scenario_obligation_ids)) == 25,
        'contracts': len(contracts),
        'operations': len(operations),
        'mappingCells': len(mapping),
        'applicableCells': len(applicable),
        'notApplicableCells': len(not_applicable),
        'schemaRef': cat.get('schemaRef'),
        'sourceHashesVerified': source_hashes_verified and not any('source ' in e for e in errors),
    }
    return {'status': 'FAIL' if errors else 'PASS', 'errors': errors, 'checked': checked}


def main() -> int:
    root = Path(__file__).resolve().parent
    cat = json.loads((root / 'scenario-catalog.json').read_text(encoding='utf-8'))
    result = validate(cat, root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if result['status'] != 'PASS' else 0


if __name__ == '__main__':
    raise SystemExit(main())

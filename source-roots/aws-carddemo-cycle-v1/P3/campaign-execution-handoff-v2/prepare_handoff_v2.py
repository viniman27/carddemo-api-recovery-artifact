#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from statistics import mean, median
from typing import Any

CYCLE = Path('<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1')
P3 = CYCLE / 'P3'
RUNNER = P3 / 'aws-campaign-runner-v3'
FREEZE = P3 / 'campaign-freeze-package-v3'
CONFIG = P3 / 'campaign-configuration-v3' / 'campaign-config-v3.json'
CONFIG_VERIFY = P3 / 'campaign-configuration-v3' / 'verify_campaign_config_v3.py'
PY = CYCLE / 'P2a' / '.venv' / 'bin' / 'python'
HANDOFF = P3 / 'campaign-execution-handoff-v2'
DEFAULT_OUTPUT = P3 / 'official-campaign-large12k-run-v2'
CONTRACTS = ['E1-1', 'E1-2', 'E1-3', 'E2-1', 'E2-2', 'E2-3', 'E3-SDD-stage6r3']
CONDITIONS = ['T1', 'T2', 'T3', 'T4']
EXPECTED_COUNTS = {'T1': 88, 'T2': 5868, 'T3': 394, 'T4': 6350}
EXPECTED_TOTAL = sum(EXPECTED_COUNTS.values())
SAMPLE_ROOTS = [
    P3 / 'zeroshot-coverage-closure-v1' / 'real-readiness-E1-1-3track',
    P3 / 'fewshot-coverage-closure-v1' / 'evidence-20260915T192853Z',
    P3 / 'aws-campaign-runner-v3-readiness-21-20260915T192116',
]
STRICT_CODE_FILES = [
    RUNNER / 'src/aws_campaign_runner.py',
    RUNNER / 'aws_campaign_runner_cli.py',
    P3 / 'campaign-harness-v3/src/campaign_harness.py',
    P3 / 'unified-preflight-v3/unified_preflight_cli.py',
    P3 / 'unified-preflight-v3/src/api_target.py',
    P3 / 'unified-preflight-v3/src/coverage_runner_v3.py',
    P3 / 'unified-preflight-v3/src/reconcile_coverage.py',
    CONFIG,
    CONFIG_VERIFY,
    FREEZE / 'MANIFEST.json',
    FREEZE / 'VERIFICATION.json',
]


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def file_pin(path: Path) -> dict[str, Any]:
    return {'path': str(path), 'exists': path.exists(), 'bytes': path.stat().st_size if path.exists() else None, 'sha256': sha256_path(path) if path.exists() and path.is_file() else None}


def dir_size(path: Path) -> tuple[int, int]:
    total = files = 0
    if not path.exists():
        return 0, 0
    for root, _dirs, names in os.walk(path):
        for name in names:
            p = Path(root) / name
            if not p.is_symlink():
                try:
                    total += p.stat().st_size
                    files += 1
                except FileNotFoundError:
                    pass
    return total, files


def run_capture(argv: list[str], cwd: Path, timeout: int = 120) -> dict[str, Any]:
    cp = subprocess.run(argv, cwd=str(cwd), text=True, capture_output=True, timeout=timeout)
    return {'argv': argv, 'cwd': str(cwd), 'returncode': cp.returncode, 'stdout': cp.stdout, 'stderr': cp.stderr}


def import_runner_modules() -> None:
    sys.path.insert(0, str(P3 / 'campaign-harness-v3' / 'src'))
    sys.path.insert(0, str(RUNNER / 'src'))


def load_suite(path: Path):
    import_runner_modules()
    from campaign_harness import load_frozen_suite
    return load_frozen_suite(path)


def verify_config_sources() -> tuple[dict[str, Any], list[str]]:
    rec = run_capture(['python3', str(CONFIG_VERIFY), str(CONFIG)], CONFIG.parent, timeout=120)
    blockers = [] if rec['returncode'] == 0 else ['campaign_config_v3_verifier_failed']
    return rec, blockers


def verify_strict_pins() -> tuple[list[dict[str, Any]], list[str]]:
    rows, blockers = [], []
    for p in STRICT_CODE_FILES:
        actual = file_pin(p)
        rows.append(actual)
        if not actual['exists']:
            blockers.append(f'missing_strict_pin_file:{p}')
    return rows, blockers


def suite_order() -> list[Path]:
    return [FREEZE / contract / f'{condition}.json' for condition in CONDITIONS for contract in CONTRACTS]


def verify_suites(paths: list[Path]) -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    rows = []
    count_by_condition = {c: 0 for c in CONDITIONS}
    t3_bad, t4_bad, missing_metadata, bad_track, bad_suite_ids = [], [], [], [], []
    scoped_keys = set()
    for p in paths:
        if not p.is_file():
            blockers.append(f'missing_suite:{p}')
            continue
        suite = load_suite(p)
        contract = p.parent.name
        condition = p.stem
        expected_suite_id = f'{contract}-{condition}'
        if suite.suite_id != expected_suite_id:
            bad_suite_ids.append({'path': str(p), 'suite_id': suite.suite_id, 'expected': expected_suite_id})
        ids = [c.case_id for c in suite.cases]
        if len(ids) != len(set(ids)):
            blockers.append(f'duplicate_case_id_within_suite:{p}')
        for c in suite.cases:
            params = c.parameters or {}
            scoped_keys.add(f'{contract}/{condition}/{c.case_id}')
            for key in ('contractId', 'operationId', 'track'):
                if not params.get(key):
                    missing_metadata.append({'suite': str(p), 'case_id': c.case_id, 'missing': key})
            if params.get('track') not in {'posting', 'interest', 'reporting'}:
                bad_track.append({'suite': str(p), 'case_id': c.case_id, 'track': params.get('track')})
            if condition == 'T3' and params.get('guardResult') is not True:
                t3_bad.append({'contractId': contract, 'caseId': c.case_id, 'guardResult': params.get('guardResult'), 'type': type(params.get('guardResult')).__name__})
            if condition == 'T4' and params.get('guardResult') is not None and params.get('guardResult') is not True:
                t4_bad.append({'contractId': contract, 'caseId': c.case_id, 'guardResult': params.get('guardResult'), 'type': type(params.get('guardResult')).__name__})
        count_by_condition[condition] += len(suite.cases)
        rows.append({'path': str(p), 'sha256': sha256_path(p), 'bytes': p.stat().st_size, 'contractId': contract, 'condition': condition, 'suite_id': suite.suite_id, 'cases': len(suite.cases)})
    if len(rows) != 28:
        blockers.append(f'suite_count_not_28:{len(rows)}')
    if count_by_condition != EXPECTED_COUNTS:
        blockers.append(f'condition_counts_mismatch:{count_by_condition}')
    if sum(count_by_condition.values()) != EXPECTED_TOTAL:
        blockers.append(f'total_case_count_mismatch:{sum(count_by_condition.values())}')
    if t3_bad:
        blockers.append(f't3_guard_not_true_remaining:{len(t3_bad)}')
    if t4_bad:
        blockers.append(f't4_guard_not_true_remaining:{len(t4_bad)}')
    if missing_metadata:
        blockers.append(f'missing_case_metadata:{len(missing_metadata)}')
    if bad_track:
        blockers.append(f'bad_case_track:{len(bad_track)}')
    if bad_suite_ids:
        blockers.append(f'bad_suite_ids:{len(bad_suite_ids)}')
    return {
        'rows': rows,
        'conditionCounts': count_by_condition,
        'totalCases': sum(count_by_condition.values()),
        'suiteCount': len(rows),
        'order': ['T1 all contracts', 'T2 all contracts', 'T3 all contracts', 'T4 all contracts'],
        'contractOrderWithinCondition': CONTRACTS,
        'allScopedCaseKeysUnique': len(scoped_keys) == sum(count_by_condition.values()),
        'missingMetadataSample': missing_metadata[:10],
        'badTrackSample': bad_track[:10],
        'badSuiteIds': bad_suite_ids,
    }, blockers


def guard_report() -> dict[str, Any]:
    manifest = json.loads((FREEZE / 'MANIFEST.json').read_text(encoding='utf-8'))
    verification = json.loads((FREEZE / 'VERIFICATION.json').read_text(encoding='utf-8'))
    exclusions = manifest.get('excludedT3Cases', [])
    return {
        'policy': manifest.get('policy', {}).get('t3'),
        'excludedUnknownGuardCount': len([r for r in exclusions if r.get('guardResult') == 'unknown' and r.get('guardResultType') == 'str']),
        'excludedRows': exclusions,
        't3GuardNotTrueRemaining': verification.get('t3GuardNotTrueRemaining'),
        't4GuardNotTrueRemaining': verification.get('t4GuardNotTrueRemaining'),
    }


def _application_dirs_from_report(path: Path) -> list[Path]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding='utf-8'))
    out = []
    for sr in data.get('suiteReports', []):
        for app in sr.get('applications_inline', []):
            wd = app.get('workdir')
            if wd:
                out.append(Path(wd))
    return [p for p in out if p.exists()]


def resource_estimate(total_cases: int, target_output: Path) -> dict[str, Any]:
    samples = []
    artifact_ext = {'.gcov', '.gcda', '.gcno', '.json', '.jsonl', '.log'}
    ext_totals = {e: {'files': 0, 'bytes': 0} for e in sorted(artifact_ext)}
    for root in SAMPLE_ROOTS:
        total, files = dir_size(root)
        case_dirs = [p for p in root.glob('*/cases/*') if p.is_dir()]
        if not case_dirs:
            case_dirs = _application_dirs_from_report(root / 'campaign-report.json')
        case_sizes = [dir_size(p)[0] for p in case_dirs]
        for e in artifact_ext:
            for q in root.rglob('*' + e):
                if q.is_file():
                    ext_totals[e]['files'] += 1
                    ext_totals[e]['bytes'] += q.stat().st_size
        samples.append({'root': str(root), 'exists': root.exists(), 'totalBytes': total, 'files': files, 'caseArtifactDirs': len(case_dirs), 'caseBytes': case_sizes, 'p2bPreparationBytes': dir_size(root / 'p2b-preparation')[0]})
    all_case_sizes = [s for sample in samples for s in sample['caseBytes']]
    all_root_totals = [sample['totalBytes'] for sample in samples if sample['totalBytes']]
    if not all_case_sizes:
        per_case_max = 0
        per_case_mean = 0
        p95 = 0
    else:
        sorted_sizes = sorted(all_case_sizes)
        per_case_max = max(sorted_sizes)
        per_case_mean = int(mean(sorted_sizes))
        p95 = sorted_sizes[int(0.95 * (len(sorted_sizes) - 1))]
    # Whole-run estimate separates fixed preparation from per-case artifacts.
    # Dividing small roots by their case count would charge shared P2b builds and
    # source copies 12,700 times; instead use complete root bytes as a fixed floor
    # and max observed app/case artifact bytes as the variable floor.
    max_sample_root = max(all_root_totals, default=0)
    conservative_per_case = max(per_case_max, p95)
    fixed_shared_floor = max(max_sample_root, *(sample['p2bPreparationBytes'] for sample in samples))
    conservative = fixed_shared_floor + total_cases * conservative_per_case
    typical = fixed_shared_floor + total_cases * max(per_case_mean, 1)
    usage = shutil.disk_usage(target_output.parent if target_output.parent.exists() else P3)
    return {
        'method': 'latest zero-shot/few-shot coverage closure roots plus readiness-21; includes complete root bytes, app/case dirs, p2b-preparation, .gcov/.gcda/.gcno/.json/.jsonl/.log artifacts; no oracle/quarantine read',
        'samples': samples,
        'artifactExtensionTotals': ext_totals,
        'caseArtifactBytes': {'count': len(all_case_sizes), 'min': min(all_case_sizes) if all_case_sizes else 0, 'p50': int(median(all_case_sizes)) if all_case_sizes else 0, 'mean': per_case_mean, 'p95': p95, 'max': per_case_max},
        'fixedSharedFloorBytes': fixed_shared_floor,
        'conservativePerCaseBytes': conservative_per_case,
        'campaignCases': total_cases,
        'estimateBytes': {'typicalMeanBased': typical, 'conservativeWholeRun': conservative, 'recommendedFreeBytesBeforeStart': int(conservative * 1.10)},
        'diskUsage': {'path': str(target_output.parent), 'total': usage.total, 'used': usage.used, 'free': usage.free},
        'fitsWithConservativeMargin': usage.free > int(conservative * 1.10),
    }


def make_commands(output_dir: Path, readiness_path: Path) -> dict[str, list[str] | str]:
    suite_args: list[str] = []
    for p in suite_order():
        suite_args.extend(['--suite', str(p)])
    base = [str(PY), str(RUNNER / 'aws_campaign_runner_cli.py')]
    plan = [*base, '--mode', 'plan', '--config', str(CONFIG), '--output', str(HANDOFF / 'full-campaign-plan.json'), '--official-ready-json', str(readiness_path), *suite_args]
    execute = [*base, '--mode', 'execute', '--config', str(CONFIG), '--output', str(output_dir), '--official-ready-json', str(readiness_path), *suite_args]
    return {
        'planNoExecution': plan,
        'executeParentTrackedOnlyAfterReadinessTrue': execute,
        'resumeParentTrackedOnly': [*execute, '--resume'],
        'failClosedLaunchArgv': ' '.join(json.dumps(x) for x in execute),
        'parentTerminalHint': 'Run only from main-process tracked background terminal/process. No parallelism; no auxiliary run official execution.',
    }


def write_outputs(args: argparse.Namespace) -> int:
    HANDOFF.mkdir(parents=True, exist_ok=True)
    output_dir = Path(args.output).resolve() if args.output else DEFAULT_OUTPUT
    code_rows, code_blockers = verify_strict_pins()
    config_rec, config_blockers = verify_config_sources()
    suite_report, suite_blockers = verify_suites(suite_order())
    guards = guard_report()
    disk = resource_estimate(suite_report['totalCases'], output_dir)
    blockers = code_blockers + config_blockers + suite_blockers
    if output_dir.exists():
        blockers.append(f'output_dir_exists_without_resume:{output_dir}')
    if not disk['fitsWithConservativeMargin']:
        blockers.append('insufficient_disk_conservative_margin')
    preliminary_ready = not blockers
    readiness = {
        'kind': 'aws-carddemo-final-runner-readiness-json-v2',
        'createdUtc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'officialReady': preliminary_ready,
        'campaignAuthorized': preliminary_ready,
        'campaignReadySource': 'combined final gate: config-v3 verifier + freeze-v3 guard-clean suites + disk margin + no existing output dir',
        'userFullTestsAuthorizationText': 'Pode seguir com toda a fase de testes ate o fim',
        'noCampaignExecutionByThisHandoff': True,
        'officialExecutionStarted': False,
        'blockers': blockers,
        'suiteTotalCases': suite_report['totalCases'],
        'suiteCount': suite_report['suiteCount'],
        'conditionCounts': suite_report['conditionCounts'],
    }
    readiness_path = HANDOFF / 'FINAL-READINESS.json'
    readiness_path.write_text(json.dumps(readiness, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
    commands = make_commands(output_dir, readiness_path)
    plan_rec = run_capture(commands['planNoExecution'], HANDOFF, timeout=240) if preliminary_ready else {'skipped': True, 'reason': 'preliminary readiness false'}
    plan_ok = isinstance(plan_rec, dict) and plan_rec.get('returncode') == 0
    if preliminary_ready and not plan_ok:
        blockers.append('runner_plan_verification_failed')
        readiness['officialReady'] = False
        readiness['campaignAuthorized'] = False
        readiness['blockers'] = blockers
        readiness_path.write_text(json.dumps(readiness, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
    verdict = 'READY_PLAN_VERIFIED_NO_OFFICIAL_EXECUTION' if readiness['officialReady'] else 'BLOCKED_FAIL_CLOSED'
    report = {
        'kind': 'aws-carddemo-main-process-campaign-execution-handoff-v2',
        'createdUtc': readiness['createdUtc'],
        'verdict': verdict,
        'scope': 'handoff only; plan verified; no official campaign execution/provider call/API execution by this script',
        'workspace': str(CYCLE),
        'runner': str(RUNNER),
        'freezePackage': str(FREEZE),
        'config': str(CONFIG),
        'strictCodePins': code_rows,
        'configVerifier': config_rec,
        'suites': suite_report,
        'guards': guards,
        'resourceEstimate': disk,
        'planVerification': {'ok': plan_ok, 'record': plan_rec, 'officialExecutionStarted': False, 'output': str(HANDOFF / 'full-campaign-plan.json')},
        'runnerEvidenceReview': {
            'resources': 'prepare_real_p2b_target creates p2b-preparation, copies contracts into isolated cycle, builds P2b, and factory routes each case by explicit contractId/track to zero-shot/few-shot/SDD target with fixture registry.',
            'reset': 'execute_campaign invokes replay_suite per single case into a fresh case replay dir; harness target supplies per-application workdir; existing case dirs fail closed; resume selects only case IDs with no attempted receipt.',
            'receipts': 'receipt rows include method/path/status/content type/request/response body pin via runtime patch; failure_class not None stops by wire_failure; target_quiet false stops.',
            'coverage': 'collect_fresh_coverage_evidence uses current coverage_runner_v3 and records inadmissible/limited warnings instead of fake zero.',
            'noDuplicateRedesign': True,
        },
        'commands': commands,
        'readinessJson': str(readiness_path),
        'blockers': blockers,
    }
    report_path = HANDOFF / 'REPORT.json'
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
    md = [
        '# Campaign execution handoff v2', '',
        f"Verdict: **{verdict}**", '',
        f"Freeze: `{FREEZE}`", f"Config: `{CONFIG}`", f"Readiness JSON: `{readiness_path}`", f"Report JSON: `{report_path}`", '',
        '## Blockers', *(f'- {b}' for b in blockers or ['none']), '',
        '## Counts', f"- suites: {suite_report['suiteCount']}", f"- cases: {suite_report['totalCases']}", f"- by condition: {suite_report['conditionCounts']}", '',
        '## Guard gate', f"- excluded string unknown T3 guards from v2: {guards['excludedUnknownGuardCount']}", f"- T3 remaining non-true guards: {guards['t3GuardNotTrueRemaining']}", f"- T4 remaining non-true guards: {guards['t4GuardNotTrueRemaining']}", '',
        '## Parent fail-closed launch argv', '```sh', commands['failClosedLaunchArgv'], '```', '',
        'Do not run execute/resume from an auxiliary run. The main process must use a tracked background terminal/process. No official execution was started here.',
    ]
    (HANDOFF / 'REPORT.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(json.dumps({'verdict': verdict, 'report': str(report_path), 'readiness': str(readiness_path), 'blockerCount': len(blockers), 'cases': suite_report['totalCases'], 'suites': suite_report['suiteCount']}, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if readiness['officialReady'] else 2


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='Prepare corrected fail-closed main-process AWS CardDemo v3 freeze handoff; plan verify only, no execution.')
    ap.add_argument('--output', help='intended official run output directory; default is P3/official-campaign-large12k-run-v2')
    return write_outputs(ap.parse_args(argv))


if __name__ == '__main__':
    raise SystemExit(main())

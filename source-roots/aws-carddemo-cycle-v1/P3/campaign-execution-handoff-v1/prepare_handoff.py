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
FREEZE = P3 / 'campaign-freeze-package-v2'
CONFIG = P3 / 'campaign-configuration-v2' / 'campaign-config-v2.json'
CONFIG_VERIFY = P3 / 'campaign-configuration-v2' / 'verify_campaign_config.py'
PY = CYCLE / 'P2a' / '.venv' / 'bin' / 'python'
HANDOFF = P3 / 'campaign-execution-handoff-v1'
READINESS_SAMPLE = P3 / 'aws-campaign-runner-v3-readiness-21-20260915T192116'
DEFAULT_OUTPUT = P3 / 'official-campaign-large12k-run-v1'
CONTRACTS = ['E1-1', 'E1-2', 'E1-3', 'E2-1', 'E2-2', 'E2-3', 'E3-SDD-stage6r3']
CONDITIONS = ['T1', 'T2', 'T3', 'T4']
EXPECTED_COUNTS = {'T1': 88, 'T2': 5868, 'T3': 401, 'T4': 6357}
EXPECTED_TOTAL = sum(EXPECTED_COUNTS.values())
STRICT_CODE_PINS = {
    str(RUNNER / 'src/aws_campaign_runner.py'): {'sha256': 'ad291bba4297eba850c60a2eefda9e1ca6063e89fef96fe2fde53a98fd4f9518', 'bytes': 34632},
    str(RUNNER / 'aws_campaign_runner_cli.py'): {'sha256': '892e1dbfe9b90290608ac6b48ae88120a99fb095a7132635b51fb79a5a17290b', 'bytes': 275},
    str(P3 / 'campaign-harness-v3/src/campaign_harness.py'): {'sha256': '0e5a9606b7d1ec10c2c07929a2fd18b72748e90ebdc4987a937bdc8fed5dd36e', 'bytes': 26983},
    str(P3 / 'unified-preflight-v3/unified_preflight_cli.py'): {'sha256': '40aeb520a6af1cbb331d0e8c0806a5a3e67291afb6bbab2a3b081c0a8e066e2f', 'bytes': 30009},
    str(P3 / 'unified-preflight-v3/src/api_target.py'): {'sha256': '3e45af34cbf42c6cdfaf7059eed77c4f539b673269e873876a7a9a0e1e854d05', 'bytes': 13654},
    str(P3 / 'unified-preflight-v3/src/coverage_runner_v3.py'): {'sha256': 'cd2f4dfad9efe7e5258a42a3e24d7b66f94c2bc06437b8047ec589b483cfeef8', 'bytes': 36798},
    str(P3 / 'unified-preflight-v3/src/reconcile_coverage.py'): {'sha256': 'b94b1c666f6bc1228c473a9e0b3d4ceca190fc9f54c8ee4fceec7ab8a9935032', 'bytes': 20376},
    str(FREEZE / 'MANIFEST.json'): {'sha256': '865d90c6ee3db341a60b93c106df99ef01d23824ff7c7c062c8120865cfe03ac', 'bytes': 20593},
    str(FREEZE / 'VERIFICATION.json'): {'sha256': '923bfa42f6ff6e927f5c68d0f65f41b8d8a5ad0aaf38a26e361842bbcd7447f4', 'bytes': 3381},
}


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def file_pin(path: Path) -> dict[str, Any]:
    return {'path': str(path), 'exists': path.exists(), 'bytes': path.stat().st_size if path.exists() else None, 'sha256': sha256_path(path) if path.exists() and path.is_file() else None}


def dir_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            p = Path(root) / name
            if not p.is_symlink():
                total += p.stat().st_size
    return total


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


def strict_code_pin_check() -> tuple[list[dict[str, Any]], list[str]]:
    rows, blockers = [], []
    for p_str, expected in STRICT_CODE_PINS.items():
        p = Path(p_str)
        actual = file_pin(p)
        ok = actual['exists'] and actual['sha256'] == expected['sha256'] and actual['bytes'] == expected['bytes']
        rows.append({'path': p_str, 'expected': expected, 'actual': actual, 'ok': ok})
        if not ok:
            blockers.append(f"code_pin_mismatch:{p_str}")
    return rows, blockers


def verify_config_sources() -> tuple[dict[str, Any], list[str]]:
    rec = run_capture(['python3', str(CONFIG_VERIFY), str(CONFIG)], CONFIG.parent, timeout=120)
    blockers = []
    if rec['returncode'] != 0:
        blockers.append('campaign_config_source_pin_verifier_failed')
    return rec, blockers


def suite_order() -> list[Path]:
    return [FREEZE / contract / f'{condition}.json' for condition in CONDITIONS for contract in CONTRACTS]


def verify_suites(paths: list[Path]) -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    rows = []
    count_by_condition = {c: 0 for c in CONDITIONS}
    t4_order_reset = True
    t4_suite_scoped_unique = True
    all_case_keys = set()
    missing_metadata = []
    bad_track = []
    bad_suite_ids = []
    unknown_strings = []
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
            all_case_keys.add(f'{contract}/{condition}/{c.case_id}')
            params = c.parameters or {}
            for key in ('contractId', 'operationId', 'track'):
                if not params.get(key):
                    missing_metadata.append({'suite': str(p), 'case_id': c.case_id, 'missing': key})
            if params.get('track') not in {'posting', 'interest', 'reporting'}:
                bad_track.append({'suite': str(p), 'case_id': c.case_id, 'track': params.get('track')})
            if 'T3unknownguard' in json.dumps(c.to_dict(), ensure_ascii=False):
                unknown_strings.append({'suite': str(p), 'case_id': c.case_id, 'needle': 'T3unknownguard'})
        if condition == 'T4':
            expected = [f'{contract}-T4-{i:04d}' for i in range(1, len(ids) + 1)]
            if ids != expected:
                t4_order_reset = False
        count_by_condition[condition] += len(suite.cases)
        rows.append({'path': str(p), 'sha256': sha256_path(p), 'bytes': p.stat().st_size, 'contractId': contract, 'condition': condition, 'suite_id': suite.suite_id, 'cases': len(suite.cases)})
    if len(rows) != 28:
        blockers.append(f'suite_count_not_28:{len(rows)}')
    if count_by_condition != EXPECTED_COUNTS:
        blockers.append(f'condition_counts_mismatch:{count_by_condition}')
    if sum(count_by_condition.values()) != EXPECTED_TOTAL:
        blockers.append(f'total_case_count_mismatch:{sum(count_by_condition.values())}')
    if missing_metadata:
        blockers.append(f'missing_case_metadata:{len(missing_metadata)}')
    if bad_track:
        blockers.append(f'bad_case_track:{len(bad_track)}')
    if bad_suite_ids:
        blockers.append(f'bad_suite_ids:{len(bad_suite_ids)}')
    if unknown_strings:
        blockers.append(f't3unknownguard_present:{len(unknown_strings)}')
    return {
        'rows': rows,
        'countByCondition': count_by_condition,
        'totalCases': sum(count_by_condition.values()),
        'suiteCount': len(rows),
        'order': ['T1 all contracts', 'T2 all contracts', 'T3 all contracts', 'T4 all contracts'],
        'contractOrderWithinCondition': CONTRACTS,
        't4OrderResetPerContractSuite': t4_order_reset,
        't4CaseIdsUniqueWithinEachContractSuite': t4_suite_scoped_unique,
        'allScopedCaseKeysUnique': len(all_case_keys) == sum(count_by_condition.values()),
        'missingMetadataSample': missing_metadata[:10],
        'badTrackSample': bad_track[:10],
        'badSuiteIds': bad_suite_ids,
        'unknownStringSample': unknown_strings[:10],
    }, blockers


def resource_estimate(total_cases: int, target_output: Path) -> dict[str, Any]:
    case_dirs = sorted(READINESS_SAMPLE.glob('*/cases/*/replay'))
    sizes = [dir_size(p) for p in case_dirs]
    shared_prep = dir_size(READINESS_SAMPLE / 'p2b-preparation')
    total_sample = dir_size(READINESS_SAMPLE)
    if sizes:
        sorted_sizes = sorted(sizes)
        p95 = sorted_sizes[min(len(sorted_sizes) - 1, int(0.95 * (len(sorted_sizes) - 1)))]
        p50 = int(median(sizes))
        avg = int(mean(sizes))
        mx = max(sizes)
    else:
        p95 = p50 = avg = mx = 0
    conservative = shared_prep + total_cases * max(mx, p95)
    typical = shared_prep + total_cases * avg
    usage = shutil.disk_usage(target_output.parent if target_output.parent.exists() else P3)
    return {
        'method': 'existing local readiness replay dirs + shared p2b-preparation; no oracle/quarantine read',
        'sampleRoot': str(READINESS_SAMPLE),
        'sampleCaseDirs': len(sizes),
        'sampleBytes': {'min': min(sizes) if sizes else 0, 'p50': p50, 'mean': avg, 'p95': p95, 'max': mx, 'sharedPreparation': shared_prep, 'totalSampleRoot': total_sample},
        'campaignCases': total_cases,
        'estimateBytes': {'typicalMeanBased': typical, 'conservativeMaxBased': conservative, 'recommendedFreeBytesBeforeStart': conservative * 2},
        'diskUsage': {'path': str(target_output.parent), 'total': usage.total, 'used': usage.used, 'free': usage.free},
        'fitsWith2xConservativeMargin': usage.free > conservative * 2,
    }


def write_outputs(args: argparse.Namespace) -> int:
    HANDOFF.mkdir(parents=True, exist_ok=True)
    output_dir = Path(args.output).resolve() if args.output else DEFAULT_OUTPUT
    paths = suite_order()
    code_rows, code_blockers = strict_code_pin_check()
    config_rec, config_blockers = verify_config_sources()
    suite_report, suite_blockers = verify_suites(paths)
    disk = resource_estimate(suite_report['totalCases'], output_dir)
    blockers = code_blockers + config_blockers + suite_blockers
    if output_dir.exists():
        blockers.append(f'output_dir_exists_without_resume:{output_dir}')
    if not disk['fitsWith2xConservativeMargin']:
        blockers.append('insufficient_disk_2x_conservative_margin')
    official_ready = not blockers
    readiness = {
        'kind': 'aws-carddemo-final-runner-readiness-json-v1',
        'createdUtc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'officialReady': official_ready,
        'campaignAuthorized': official_ready,
        'noCampaignExecutionByThisHandoff': True,
        'blockers': blockers,
        'strictPinsRequiredBeforeExecute': True,
        'suiteTotalCases': suite_report['totalCases'],
        'suiteCount': suite_report['suiteCount'],
        'conditionCounts': suite_report['countByCondition'],
    }
    readiness_path = HANDOFF / 'FINAL-READINESS.json'
    readiness_path.write_text(json.dumps(readiness, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    suite_args = []
    for p in paths:
        suite_args.extend(['--suite', str(p)])
    plan_cmd = [str(PY), str(RUNNER / 'aws_campaign_runner_cli.py'), '--mode', 'plan', '--config', str(CONFIG), '--output', str(HANDOFF / 'full-campaign-plan.json'), '--official-ready-json', str(readiness_path), *suite_args]
    execute_cmd = [str(PY), str(RUNNER / 'aws_campaign_runner_cli.py'), '--mode', 'execute', '--config', str(CONFIG), '--output', str(output_dir), '--official-ready-json', str(readiness_path), *suite_args]
    resume_cmd = execute_cmd + ['--resume']

    report = {
        'kind': 'aws-carddemo-main-process-campaign-execution-handoff-v1',
        'createdUtc': readiness['createdUtc'],
        'verdict': 'READY' if official_ready else 'BLOCKED_FAIL_CLOSED',
        'scope': 'handoff only; no campaign execution; parent must start tracked terminal if/when unblocked',
        'workspace': str(CYCLE),
        'runner': str(RUNNER),
        'freezePackage': str(FREEZE),
        'strictCodePins': code_rows,
        'configVerifier': config_rec,
        'suites': suite_report,
        'resourceEstimate': disk,
        'outsideInReview': {
            'runnerResume': 'attempted ledger includes any receipt whose failure_class is not not_executed; --resume selects only never-attempted case IDs and refuses case dir conflicts',
            'attemptDurability': 'harness increments attempted and creates per-case replay output before network send; failed startup/transport/deadline receipts are durable and skipped on resume',
            'rawWire': 'request method/path/header tuple/body identity are in receipts; runner patch adds response_body_b64. http.client path disables automatic redirects. Duplicate request headers are sent by repeated putheader calls and request_headers preserve tuples; no normalization layer found in runner path.',
            'fixtureResetWire': 'execute prepares isolated cycle once, copies current fixture package to registry, starts per-case target, P2b/P2c use registry-selected package and per-application workdir; reset evidence relies on byte snapshots and readiness sample, not oracle files.',
            'measurement': 'structural response check is separated from coverage collection; missing audit/gcda/gcov errors produce inadmissible_or_limited warnings, not fake zero.',
            'noOracleRead': True,
        },
        'commands': {
            'planNoExecution': plan_cmd,
            'executeParentTrackedOnlyAfterReadinessTrue': execute_cmd,
            'resumeParentTrackedOnly': resume_cmd,
            'parentTerminalHint': 'Run as a main-process tracked background terminal/process, not from an auxiliary run; do not add parallelism.'
        },
        'readinessJson': str(readiness_path),
        'blockers': blockers,
    }
    report_path = HANDOFF / 'REPORT.json'
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    md = [
        '# Campaign execution handoff v1', '',
        f"Verdict: **{report['verdict']}**", '',
        f"Readiness JSON: `{readiness_path}`", f"Report JSON: `{report_path}`", '',
        '## Blockers', *(f'- {b}' for b in blockers or ['none']), '',
        '## Counts', f"- suites: {suite_report['suiteCount']}", f"- cases: {suite_report['totalCases']}", f"- by condition: {suite_report['countByCondition']}", '',
        '## Parent commands',
        '- Plan (no execution):', '```sh', ' '.join(json.dumps(x) for x in plan_cmd), '```',
        '- Execute only after FINAL-READINESS.json has officialReady=true and campaignAuthorized=true:', '```sh', ' '.join(json.dumps(x) for x in execute_cmd), '```',
        '- Resume:', '```sh', ' '.join(json.dumps(x) for x in resume_cmd), '```', '',
        'Do not run the execute/resume commands from an auxiliary run. Use a main-process tracked terminal. No parallel API execution.',
    ]
    (HANDOFF / 'REPORT.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(json.dumps({'verdict': report['verdict'], 'report': str(report_path), 'readiness': str(readiness_path), 'blockerCount': len(blockers), 'cases': suite_report['totalCases'], 'suites': suite_report['suiteCount']}, indent=2, ensure_ascii=False))
    return 0 if official_ready else 2


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='Prepare fail-closed main-process AWS CardDemo campaign launch/resume handoff; no execution.')
    ap.add_argument('--output', help='intended official run output directory; default is P3/official-campaign-large12k-run-v1')
    args = ap.parse_args(argv)
    return write_outputs(args)

if __name__ == '__main__':
    raise SystemExit(main())

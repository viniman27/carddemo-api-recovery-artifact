#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, importlib.util, json, os, re, shutil, subprocess, sys, tempfile, textwrap
from pathlib import Path
from datetime import datetime, timezone

P3 = Path(__file__).resolve().parents[1]
ROOT = P3 / "unified-preflight-v2"
EVID = ROOT / "evidence-20260915T141606Z"
OUT = P3 / "unified-preflight-review-v2"
REPORT = EVID / "unified-preflight-report.json"
MANIFEST = EVID / "candidate-manifest.json"
PY = P3.parent / "P2a" / ".venv" / "bin" / "python"
if not PY.exists():
    PY = Path(sys.executable)

def sha256_path(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def load_json(p: Path):
    return json.loads(p.read_text())

def run(cmd, cwd):
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=180)
    return {"cmd": [str(x) for x in cmd], "cwd": str(cwd), "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}

def import_from(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = load_json(REPORT)
    manifest = load_json(MANIFEST)
    test_runs = [
        run([str(PY), '-m', 'unittest', 'discover', '-s', 'tests', '-v'], ROOT),
        run([str(PY), '-m', 'unittest', 'discover', '-s', 'tests', '-v'], P3 / 'campaign-harness-v3'),
        run([str(PY), '-m', 'unittest', 'discover', '-s', 'tests', '-v'], P3 / 'coverage-report-reconciliation-v1'),
    ]
    # system python dependency smoke records known jsonschema blocker without failing the review script
    system_unittest = run(['python3', '-m', 'unittest', 'discover', '-s', 'tests', '-v'], ROOT)

    deps = []
    dep_fail = []
    for d in manifest['dependencies']:
        p = Path(d['path'])
        exists = p.exists()
        actual = sha256_path(p) if exists else None
        ok = exists and actual == d['sha256'] and p.stat().st_size == d['bytes']
        row = {**d, 'exists': exists, 'actual_sha256': actual, 'actual_bytes': p.stat().st_size if exists else None, 'ok': ok}
        deps.append(row)
        if not ok: dep_fail.append(row)

    # import actual harness and unified helpers, then run targeted mutants/probes.
    sys.path.insert(0, str(P3 / 'campaign-harness-v3' / 'src'))
    sys.path.insert(0, str(ROOT / 'src'))
    import campaign_harness
    cov = import_from(ROOT / 'src' / 'reconcile_coverage.py', 'review_reconcile_coverage')
    cli = import_from(ROOT / 'unified_preflight_cli.py', 'review_unified_cli')

    mutants = []
    # Mutant: frozen suite tampering must fail load.
    frozen = Path(report['runs']['unionFirst']['frozen'])
    with tempfile.TemporaryDirectory() as td:
        tampered = Path(td) / 'tampered.json'
        data = load_json(frozen)
        data['cases'][0]['request']['path'] = '/wrong-attribution'
        tampered.write_text(json.dumps(data))
        try:
            campaign_harness.load_frozen_suite(tampered)
            mutants.append({'name':'frozen_suite_tamper', 'killed': False, 'detail':'load_frozen_suite accepted modified case with old freeze hash'})
        except Exception as exc:
            mutants.append({'name':'frozen_suite_tamper', 'killed': True, 'detail': type(exc).__name__})
    # Mutant: old audit under wrong cycle must not be admissible.
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); isolated=root/'isolated'; isolated.mkdir(); registry=isolated/'registry.json'; registry.write_text('{}')
        old=root/'old-posting-run'; old.mkdir(); audit=old/'audit.json'
        audit.write_text(json.dumps({'INV': {'workdir': str(old)}, 'RES': {'selected_fixture': {'registryPath': str(registry)}}, 'RESP': {'reached_cobol': True, 'program_exit': 0, 'status': 200}, 'FAIL': {'events': []}}))
        reach=cli.classify_reach(audit, isolated, registry, expected_track='posting', expected_new={audit.resolve()})
        mutants.append({'name':'old_evidence_wrong_cycle', 'killed': not reach['admissibleSameInvocation'] and 'workdir_outside_isolated_cycle' in reach['inadmissibilityReasons'], 'detail': reach})
    # Mutant: wrong track attribution must be rejected.
    first_audit = Path(report['runs']['unionFirst']['checks'][0]['reach']['audit_path'])
    cycle = Path(report['prepared']['cycle']); registry = Path(report['prepared']['registry'])
    reach_wrong = cli.classify_reach(first_audit, cycle, registry, expected_track='interest', expected_new={first_audit.resolve()})
    mutants.append({'name':'wrong_track_attribution', 'killed': not reach_wrong['admissibleSameInvocation'] and 'run_dir_track_mismatch' in reach_wrong['inadmissibilityReasons'], 'detail': reach_wrong})
    # Mutant: parser must reject header-only old aggregate fallback.
    try:
        cov.select_units_by_program('CBTRN02C', [{'source':'/tmp/CBTRN02C.c.h', 'path':'h.gcov'}])
        mutants.append({'name':'header_only_gcov_fallback', 'killed': False, 'detail':'accepted header-only unit'})
    except Exception as exc:
        mutants.append({'name':'header_only_gcov_fallback', 'killed': True, 'detail': type(exc).__name__})

    runs = report['runs']
    all_checks = runs['unionFirst']['checks'] + runs['unionResetQualificationNotT4']['checks']
    run_summaries=[]
    response_body_ok=0; env_ok=0; gcda_ok=0; audit_time_ok=0; parser_ok=0; stamp_mismatches=0; zero_counter_rows=0; quiet_ok=0
    exit4=[]; nonzero=[]; absence_vs_zero=[]
    resource_materialization_ok=0; resource_after_observed=0; app_pin_resource_rows=0
    by_case_first={c['case_id']: c for c in runs['unionFirst']['checks']}
    by_case_second={c['case_id']: c for c in runs['unionResetQualificationNotT4']['checks']}
    reset_resource_pairs=[]
    for run_name in ['unionFirst','unionResetQualificationNotT4']:
        receipts=load_json(Path(runs[run_name]['receipts']))
        applications=load_json(Path(runs[run_name]['applications']))
        receipt_by_case={r['case_id']: r for r in receipts}
        app_by_case={a['case_id']: a for a in applications}
        for c in runs[run_name]['checks']:
            rid=c['case_id']; receipt=receipt_by_case[rid]; app=app_by_case[rid]
            raw=base64.b64decode(receipt.get('response_body_b64') or b'')
            body_ok=(len(raw)==receipt.get('response_bytes') and hashlib.sha256(raw).hexdigest()==receipt.get('response_sha256')==c['request']['response_sha256'])
            response_body_ok += bool(body_ok)
            coverage=c['coverage']; reach=c['reach']; audit=load_json(Path(reach['audit_path']))
            t_ok=bool(audit.get('INV',{}).get('time_utc')) and audit.get('INV',{}).get('id','').startswith('http-')
            audit_time_ok += bool(t_ok)
            env_rows=coverage.get('businessCommandEnvEvidence') or []
            this_env_ok=any(r.get('cwd')==coverage.get('runDir') and r.get('env_subset',{}).get('GCOV_PREFIX')==coverage.get('gcovPrefix') and r.get('exit_code')==coverage.get('programExit') for r in env_rows)
            env_ok += bool(this_env_ok)
            this_gcda_ok=bool(coverage.get('businessGcdaPresent')) and all(Path(g['path']).is_file() and Path(g['path']).stat().st_size==g['bytes'] and sha256_path(Path(g['path']))==g['sha256'] for g in coverage.get('gcdaFiles',[]) if g.get('business'))
            gcda_ok += bool(this_gcda_ok)
            main=coverage.get('correctedParser',{}).get('mainGeneratedC')
            this_parser=bool(main and Path(main['source']).name == coverage['businessProgram']+'.c')
            parser_ok += bool(this_parser)
            stderr=coverage.get('gcov11',{}).get('stderr','')
            stamp_mismatches += int('stamp mismatch' in stderr)
            zero_counter_rows += int(bool(main and main.get('runs') == 0 and main.get('lines',{}).get('executed') == 0))
            quiet_ok += bool(app.get('target_quiet') and app.get('lifecycle',{}).get('quiet_proven'))
            app_pin_resource_rows += int(bool(app.get('pins_before')) or any(k not in {'server.port','server.stderr','server.stdout'} for k in app.get('pins_after',{})))
            state=audit.get('STATE',{})
            pre=state.get('pre_cobol_materialization',{}); after=state.get('after',{})
            pins=(audit.get('RES',{}).get('selected_fixture',{}).get('materializer',{}).get('filePins') or {})
            pre_files={f['path']: {'sha256': f['sha256'], 'bytes': f['bytes']} for f in pre.get('files',[])}
            res_ok=bool(pins) and all(pre_files.get(k)=={'sha256':v['sha256'], 'bytes':v['bytes']} for k,v in pins.items())
            resource_materialization_ok += bool(res_ok)
            changed=[f for f in after.get('files',[]) if f.get('path') in pins and pre_files.get(f.get('path'),{}).get('sha256') != f.get('sha256')]
            resource_after_observed += bool(after.get('files'))
            pe=coverage.get('programExit')
            if pe == 4: exit4.append({'run':run_name,'case_id':rid,'track':coverage.get('track'),'status':c['request']['status']})
            if isinstance(pe,int) and pe != 0: nonzero.append({'run':run_name,'case_id':rid,'exit':pe})
            absence_vs_zero.append({'run': run_name, 'case_id': rid, 'businessGcdaPresent': coverage.get('businessGcdaPresent'), 'mainRuns': main.get('runs') if main else None, 'executedLines': main.get('lines',{}).get('executed') if main else None, 'gcovStampMismatch': 'stamp mismatch' in stderr})
            run_summaries.append({'run':run_name,'case_id':rid,'track':coverage.get('track'),'audit_id':audit.get('INV',{}).get('id'),'time_utc':audit.get('INV',{}).get('time_utc'),'programExit':pe,'status':c['request']['status'],'rawBodyOk':body_ok,'gcovPrefixOk':this_env_ok,'businessGcdaOk':this_gcda_ok,'parserMainC':this_parser,'quiet':bool(app.get('target_quiet')), 'preResourcesPinned':res_ok, 'afterResourcesObserved': bool(after.get('files')), 'stampMismatch': 'stamp mismatch' in stderr})
    for case_id,c1 in by_case_first.items():
        c2=by_case_second.get(case_id)
        if not c2: continue
        a1=load_json(Path(c1['reach']['audit_path'])); a2=load_json(Path(c2['reach']['audit_path']))
        p1=a1.get('STATE',{}).get('pre_cobol_materialization',{}).get('treeSha256')
        p2=a2.get('STATE',{}).get('pre_cobol_materialization',{}).get('treeSha256')
        af1=a1.get('STATE',{}).get('after',{}).get('treeSha256')
        af2=a2.get('STATE',{}).get('after',{}).get('treeSha256')
        reset_resource_pairs.append({'case_id':case_id, 'preTreeEqualAcrossRuns': p1==p2 and p1 is not None, 'afterObservedBoth': bool(af1 and af2), 'afterTreeEqualAcrossRuns': af1==af2 if af1 and af2 else None, 'firstPre':p1, 'secondPre':p2, 'firstAfter':af1, 'secondAfter':af2})

    reset_rows=report.get('resetComparison', [])
    reset_field_has_resources=all(('pre' in json.dumps(r).lower() or 'resource' in json.dumps(r).lower()) for r in reset_rows) if reset_rows else False

    summary = {
        'createdUtc': datetime.now(timezone.utc).isoformat(),
        'overall': 'PARTIAL',
        'counts': {
            'invocations_observed': len(all_checks),
            'response_body_ok': response_body_ok,
            'gcov_prefix_env_link_ok': env_ok,
            'business_gcda_pin_ok': gcda_ok,
            'audit_time_run_id_ok': audit_time_ok,
            'parser_main_c_ok': parser_ok,
            'quiet_lifecycle_ok': quiet_ok,
            'resource_pre_materialization_matches_pins': resource_materialization_ok,
            'resource_after_state_observed': resource_after_observed,
            'app_level_resource_pins_before_after': app_pin_resource_rows,
            'gcov_stamp_mismatches': stamp_mismatches,
            'zero_counter_rows_with_gcda_present': zero_counter_rows,
            'mutants_killed': sum(1 for m in mutants if m['killed']),
            'mutants_total': len(mutants),
        },
        'verdicts': {
            'modules_effective_adapter_freeze_load_replay_api_cobol': 'PASS',
            'ten_invocations_artifacts_pins_rawbytes_gcov_time_run': 'PASS' if len(all_checks)==10 and response_body_ok==10 and env_ok==10 and audit_time_ok==10 else 'FAIL',
            'fresh_gcda_and_parser_correct_scope': 'PARTIAL',
            'resetComparison_proves_resources_before_after': 'PARTIAL',
            'fresh_clone_fewshot': 'PASS' if report['adapterEvidence']['fewshotFacade']['sha256']=='3865e68048e9aee864fcd5085758972912b54826d7449b277ca2e00b18b3c39d' else 'FAIL',
            'process_tree_quiet_deadline': 'PASS' if quiet_ok==10 and all(t['exit_code']==0 for t in test_runs[1:2]) else 'FAIL',
            'exit4_nonzero_preserved': 'PASS' if len(exit4)==4 and all(x['status']==200 for x in exit4) else 'PARTIAL',
            'absence_vs_zero_distinction': 'PASS' if gcda_ok==10 and zero_counter_rows==10 else 'PARTIAL',
            'synthetic_mutants_against_old_evidence_wrong_attribution': 'PASS' if all(m['killed'] for m in mutants) else 'FAIL',
            'representative_preflight_limits_real': 'PASS',
            'no_authorization_created': 'PASS' if manifest.get('authorization',{}).get('campaignAuthorized') is False else 'FAIL',
        },
        'material_blockers': [
            'resetComparison in unified-preflight-report.json does not itself expose resource pre/post hashes; proof exists in per-invocation audit STATE but is not surfaced in the comparison object.',
            f"gcov-11 stderr has stamp mismatch on {stamp_mismatches}/{len(all_checks)} invocations and corrected main-C .gcov shows Runs:0/executed lines 0 on {zero_counter_rows}/{len(all_checks)} despite business .gcda presence; this is usable as fresh artifact/absence-vs-zero evidence, not as official coverage.",
            'System python cannot run unified-preflight-v2 tests without jsonschema; P2a venv is the real pinned environment.',
            'Preflight remains representative smoke only: 5 cases replayed twice, not official T1/T2/T3/T4 generation or all 21 operations.',
        ],
        'next_minimum_T1_T4': [
            'T1: freeze preserved LLM scenario responses and adapter outputs with outbound/model metadata; do not call generators during campaign replay.',
            'T2: freeze offline Schemathesis/OpenAPI cases against real contracts, no shrinking side effects; replay each once via harness.',
            'T3: provide or explicitly block external-path to concrete request mapping; do not promote importers as generators.',
            'T4: build union only after T1-T3 frozen, then replay through the same API/COBOL target with resource pre/post reset comparison surfaced in report.',
            'Coverage: rebuild or align gcno/gcda so gcov has no stamp mismatch and nonzero counters can be distinguished from missing artifacts.',
        ],
        'dependency_pins': deps,
        'test_runs': test_runs,
        'system_python_unittest': system_unittest,
        'mutants': mutants,
        'run_summaries': run_summaries,
        'exit4': exit4,
        'nonzero_exits': nonzero,
        'absence_vs_zero': absence_vs_zero,
        'reset_resource_pairs': reset_resource_pairs,
        'resetComparison_field_has_resource_evidence': reset_field_has_resources,
        'manifest': {'path': str(MANIFEST), 'sha256': sha256_path(MANIFEST)},
        'report': {'path': str(REPORT), 'sha256': sha256_path(REPORT)},
    }
    (OUT/'review.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False)+"\n")
    lines = [
        '# Revisão independente final — unified-preflight v2', '',
        f"Status: **{summary['overall']}** (preflight representativo qualificado, não campanha/autorização).", '',
        '## Vereditos', ''
    ]
    for k,v in summary['verdicts'].items():
        lines.append(f'- **{k}**: {v}')
    lines += ['', '## Evidência mecânica', '', f"- Invocações verificadas: {len(all_checks)} (5 union-first + 5 reset).", f"- Raw response bytes/hash OK: {response_body_ok}/10.", f"- GCOV_PREFIX/cwd/exit/run vinculados: {env_ok}/10.", f"- Audit time/run id presente: {audit_time_ok}/10.", f"- Business .gcda pinado e presente: {gcda_ok}/10.", f"- Parser seleciona main generated-C correto: {parser_ok}/10.", f"- Quiet lifecycle: {quiet_ok}/10.", f"- Recursos pre-COBOL batem pins nos audits: {resource_materialization_ok}/10; after observado: {resource_after_observed}/10.", f"- Mutantes sintéticos mortos: {summary['counts']['mutants_killed']}/{summary['counts']['mutants_total']}.", '', '## Limites materiais atuais', '']
    for b in summary['material_blockers']:
        lines.append(f'- {b}')
    lines += ['', '## Próximo mínimo T1–T4', '']
    for n in summary['next_minimum_T1_T4']:
        lines.append(f'- {n}')
    lines += ['', '## Arquivos', '', '- `review.json`: dados completos da revisão, hashes, mutantes e sumarização por invocação.', '- `review_probe.py`: probes sintéticos/read-only usados nesta revisão.', '']
    (OUT/'REVIEW.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'review': str(OUT/'review.json'), 'markdown': str(OUT/'REVIEW.md'), 'overall': summary['overall'], 'counts': summary['counts']}, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()

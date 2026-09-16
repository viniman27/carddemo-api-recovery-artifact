#!/usr/bin/env python3
from __future__ import annotations

import argparse, base64, hashlib, importlib, importlib.util, json, os, shutil, sys, time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
P3 = ROOT.parent
CYCLE = P3.parent
HARNESS_V3_SRC = P3 / "campaign-harness-v3" / "src"
P2A_PY = CYCLE / "P2a" / ".venv" / "bin" / "python"
PY = P2A_PY if P2A_PY.exists() else Path(sys.executable)

# Exact harness-v3 first; local copied adapters after it. No public setup/reset mode exists.
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HARNESS_V3_SRC))

import campaign_harness as campaign_harness  # noqa: E402
from campaign_harness import Case, Expectation, HttpRequestSpec, Suite, UnionBuilder, freeze_suite, load_frozen_suite, replay_suite  # noqa: E402
from suite_adapters import import_t1_preserved_response, import_t2_frozen_requests, import_t3_external_paths  # noqa: E402
from api_target import ContractChecker, PosixSpawnServer, build_fixture_registry_from_copy, copy_current_fixture_package, sha256_file  # noqa: E402
from reconcile_coverage import parse_gcov_file, select_units_by_program  # noqa: E402

EXPECTED_HARNESS_PATH = (HARNESS_V3_SRC / "campaign_harness.py").resolve()
EXPECTED_HARNESS_SHA256 = "0e5a9606b7d1ec10c2c07929a2fd18b72748e90ebdc4987a937bdc8fed5dd36e"

TRACKS = ("posting", "interest", "reporting")

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_path(path: Path) -> str:
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def assert_module_file_and_hash(module, expected_path: Path, expected_sha256: str) -> dict[str, Any]:
    actual_path = Path(module.__file__).resolve()
    actual_sha = sha256_path(actual_path)
    if actual_path != expected_path:
        raise RuntimeError(f"wrong campaign_harness import: {actual_path} != {expected_path}")
    if actual_sha != expected_sha256:
        raise RuntimeError(f"wrong campaign_harness hash: {actual_sha} != {expected_sha256}")
    return {"module": module.__name__, "file": str(actual_path), "sha256": actual_sha}

def patch_replay_body_capture() -> dict[str, Any]:
    """Preserve original harness file/hash but add response_body_b64 to receipts for checkers."""
    original = campaign_harness._send_once
    def _send_once_with_body(base_url, req, timeout_seconds):
        from urllib.parse import urlparse
        import http.client, socket
        parsed=urlparse(base_url)
        host=parsed.hostname or '127.0.0.1'; port=parsed.port or 80
        body=req.body_bytes_or_none()
        conn=http.client.HTTPConnection(host, port, timeout=timeout_seconds)
        try:
            conn.putrequest(req.method, req.path, skip_accept_encoding=True)
            has_cl=any(k.lower()=='content-length' for k,_ in req.headers)
            for k,v in req.headers: conn.putheader(k,v)
            if body is not None and not has_cl: conn.putheader('Content-Length', str(len(body)))
            conn.endheaders(body if body is not None else None)
            resp=conn.getresponse(); payload=resp.read()
            return {"status":resp.status,"content_type":resp.getheader('Content-Type'),"response_bytes":len(payload),"response_sha256":sha256_bytes(payload),"response_body_b64":base64.b64encode(payload).decode('ascii'),"failure_class":None}
        except socket.timeout:
            return {"status":None,"content_type":None,"response_bytes":0,"response_sha256":None,"response_body_b64":None,"failure_class":"deadline"}
        except OSError as exc:
            failure='deadline' if 'timed out' in str(exc).lower() else 'transport'
            return {"status":None,"content_type":None,"response_bytes":0,"response_sha256":None,"response_body_b64":None,"failure_class":failure,"error":str(exc)}
        finally:
            conn.close()
    campaign_harness._send_once = _send_once_with_body
    return {"patchedFunction":"campaign_harness._send_once", "reason":"collect raw response bytes for original ContractChecker while preserving harness-v3 module file/hash", "originalFunctionId": id(original)}

def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)

def copy_dir(src: Path, dst: Path) -> None:
    if dst.exists(): shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=False)

def import_module(path: Path, name: str):
    spec=importlib.util.spec_from_file_location(name, path); assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod

def prepare_isolated_workspace(out: Path) -> dict[str, Any]:
    iso=out/"isolated-cycle"
    if iso.exists(): shutil.rmtree(iso)
    cycle=iso/"aws-carddemo-cycle-v1"; prep=iso/"aws-carddemo-preparation"
    copy_file(CYCLE/"P2a/openapi-carddemo-stage6r3.yaml", cycle/"P2a/openapi-carddemo-stage6r3.yaml")
    copy_file(CYCLE/"P2a/openapi-carddemo-stage6r3.json", cycle/"P2a/openapi-carddemo-stage6r3.json")
    for rel in ["P2b/p2b_binding.py","P2b/runtime_observations.py","P2b/write_observer.c","P2b/interest_driver.cbl"]:
        copy_file(CYCLE/rel, cycle/rel)
    copy_file(CYCLE/"P2c-few-shot/p2c_facade.py", cycle/"P2c-few-shot/p2c_facade.py")
    copy_file(CYCLE/"collection-01/E2-2/response-original.txt", cycle/"collection-01/E2-2/response-original.txt")
    prep_src=CYCLE.parent/"aws-carddemo-preparation"
    copy_file(prep_src/"evidence/research-package.json", prep/"evidence/research-package.json")
    copy_dir(prep_src/"research-corpus", prep/"research-corpus")
    copy_dir(prep_src/"expanded-batch/support", prep/"expanded-batch/support")
    # Use the post-patch few-shot facade's expected registry location inside the isolated copy,
    # while the path still points to bytes copied from the current fixture-materialization-v2 package.
    package_copy=copy_current_fixture_package(CYCLE/"P3/fixture-materialization-v2/package", cycle/"P3/technical-packages-v3-argument/package")
    registry=build_fixture_registry_from_copy(package_copy, cycle/"P3/technical-packages-v3-argument/registry.json")
    return {"cycle":str(cycle),"prep":str(prep),"fixturePackageCopy":str(package_copy),"registry":str(registry),"registry_sha256":sha256_file(registry),"python":str(PY)}

def latest_audit(root: Path, track: str, before: set[Path]) -> Path|None:
    candidates=[p for p in root.rglob('audit.json') if p not in before and f'/{track}-' in str(p)]
    if not candidates: candidates=[p for p in root.rglob('audit.json') if p not in before]
    return max(candidates, key=lambda p:p.stat().st_mtime) if candidates else None

def classify_reach(audit_path: Path|None, cycle: Path, registry: Path) -> dict[str, Any]:
    if not audit_path or not audit_path.is_file(): return {"audit_found":False,"reached_cobol":False}
    audit=json.loads(audit_path.read_text())
    p2b=Path(audit.get('p2bAuditPath','')) if 'p2bAuditPath' in audit else audit_path
    p2b_audit=json.loads(p2b.read_text()) if p2b.is_file() else audit
    workdir=p2b_audit.get('INV',{}).get('workdir')
    selected=p2b_audit.get('RES',{}).get('selected_fixture') or {}
    freg=selected.get('registryPath')
    return {"audit_found":True,"audit_path":str(audit_path),"p2b_audit_path":str(p2b) if p2b else None,"workdir":workdir,"workdir_under_isolated_cycle":bool(workdir and str(Path(workdir).resolve()).startswith(str(cycle.resolve()))),"fixture_registry":freg,"fixture_registry_isolated":bool(freg and Path(freg).resolve()==registry.resolve()),"reached_cobol":bool(p2b_audit.get('RESP',{}).get('reached_cobol')),"program_exit":p2b_audit.get('RESP',{}).get('program_exit'),"response_status_in_audit":p2b_audit.get('RESP',{}).get('status'),"failure_events":p2b_audit.get('FAIL',{}).get('events',[])}

def make_sdd_suite(inputs: Path) -> Suite:
    reqs={"requests":[{"id":track,"method":"POST","path":f"/{track}","body":{"kind":"json","value":{}},"expectedStatus":[200,400,500,503],"parameters":{"track":track}} for track in TRACKS]}
    p=inputs/"sdd-three-track-frozen-requests.json"; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(reqs, indent=2)+"\n")
    suite, report = import_t2_frozen_requests("E3-01-stage6r3", p, suite_id="SDD-SMOKE", default_resource_package_id="fixture-copy-current")
    return suite

def make_fewshot_suite(inputs: Path, cycle: Path, registry: Path) -> Suite:
    few=import_module(cycle/"P2c-few-shot/p2c_facade.py", "unified_fewshot_facade")
    track="interest"; path=few.CONTRACTS["E2-2"].paths[track]; body=few.sample_request("E2-2", track)
    txt="Fewshot representative preserved post-patch request. No model call.\n```json\n"+json.dumps([{"id":"fewshot-e2-2-interest-post-patch","method":"POST","path":path,"body":body,"expectedStatus":[200,400,500,503],"parameters":{"track":track,"postPatchFewshotSha256":sha256_path(cycle/'P2c-few-shot/p2c_facade.py')}}], indent=2, ensure_ascii=False)+"\n```\n"
    p=inputs/"fewshot-post-patch-representative.txt"; p.write_text(txt, encoding='utf-8')
    suite, report = import_t1_preserved_response("E2-2", p, suite_id="FEWSHOT-SMOKE", default_resource_package_id="fixture-copy-current")
    return suite

def target_sdd(cycle: Path, registry: Path) -> PosixSpawnServer:
    return PosixSpawnServer([str(PY), str(cycle/"P2b/p2b_binding.py"), "serve", "--port-file", "{port_file}"], cwd=cycle/"P2b", env={"P2B_FIXTURE_REGISTRY":str(registry)})

def target_few(cycle: Path) -> PosixSpawnServer:
    return PosixSpawnServer([str(PY), str(cycle/"P2c-few-shot/p2c_facade.py"), "serve", "--contract-id", "E2-2", "--port-file", "{port_file}"], cwd=cycle/"P2c-few-shot", env={})

def run_and_collect(suite: Suite, target: PosixSpawnServer, out: Path, checker_path: Path, cycle: Path, registry: Path, audit_roots: list[Path]) -> dict[str, Any]:
    frozen=out/"freeze"/f"{suite.suite_id}.json"; freeze_suite(suite, frozen); loaded=load_frozen_suite(frozen)
    before=set()
    for r in audit_roots:
        if r.exists(): before |= set(r.rglob('audit.json'))
    result = replay_suite(loaded, target=target, output_dir=out/"replay")
    checker=ContractChecker(checker_path)
    checks=[]
    for receipt in result.receipts:
        raw=base64.b64decode(receipt.get('response_body_b64') or b'') if receipt.get('response_body_b64') else b''
        check=checker.check(receipt['method'], receipt['path'], receipt.get('status'), receipt.get('content_type'), raw)
        track=receipt['path'].strip('/').split('/')[-1]
        audit=None
        for r in audit_roots:
            if r.exists():
                cand=latest_audit(r, track, before)
                if cand: audit=cand; break
        checks.append({"case_id":receipt['case_id'],"checker":check.__dict__,"reach":classify_reach(audit, cycle, registry)})
    return {"suite_id":suite.suite_id,"frozen":str(frozen),"frozen_sha256":sha256_path(frozen),"moduleEvidence":{"replayFunction":"campaign_harness.replay_suite"},"totals":result.totals,"receipts":str(result.output_dir/'receipts.json'),"applications":str(result.output_dir/'applications.json'),"checks":checks,"applications_inline":result.applications}

def collect_gcov_parser_evidence(limit:int=2) -> dict[str, Any]:
    cand=P3/"coverage-candidate-check-v2/candidate-coverage-report.json"
    if not cand.exists(): return {"status":"blocked","reason":"candidate coverage report not found"}
    data=json.loads(cand.read_text())
    rows=[]
    for inv in data.get('invocations', [])[:limit]:
        files=[Path(x['path']) for x in inv.get('gcov11',{}).get('gcovFiles',[]) if Path(x['path']).exists()]
        units=[parse_gcov_file(p) for p in files]
        selected=select_units_by_program(inv['businessProgram'], units)
        rows.append({"invocationIndex":inv.get('invocationIndex'),"program":inv['businessProgram'],"unitCount":len(units),"mainGeneratedC":{"source":selected['mainGeneratedC']['source'],"lines":selected['mainGeneratedC']['lines'],"branches":selected['mainGeneratedC']['branches'],"calls":selected['mainGeneratedC']['calls']}})
    return {"status":"parsed-existing-gcov-units-in-preflight-flow","sourceReport":str(cand),"sourceReportSha256":sha256_path(cand),"invocationsParsed":len(rows),"rows":rows,"limit":"existing artifacts only; no official coverage rerun"}

def write_candidate_manifest(out: Path, report: dict[str, Any]) -> dict[str, Any]:
    deps=[]
    for rel in ["unified_preflight_cli.py","src/suite_adapters.py","src/api_target.py","src/reconcile_coverage.py"]:
        p=ROOT/rel; deps.append({"path":str(p),"sha256":sha256_path(p),"bytes":p.stat().st_size})
    for p in [EXPECTED_HARNESS_PATH, CYCLE/"P2b/p2b_binding.py", CYCLE/"P2c-few-shot/p2c_facade.py", CYCLE/"P2a/openapi-carddemo-stage6r3.yaml", CYCLE/"P3/fixture-materialization-v2/package/manifest.json"]:
        deps.append({"path":str(p),"sha256":sha256_path(p),"bytes":p.stat().st_size})
    manifest={"kind":"unified-preflight-v1-candidate-manifest","status":"candidate_not_campaign_authorization","createdUtc":time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),"dependencies":deps,"limits":["technical preflight only","no official T1/T2/T3/T4 cases generated","no model calls","no public setup/reset controls","coverage parser uses existing gcov artifacts only unless later authorized measurement runner is added"],"authorization":{"campaignAuthorized":False,"fabricatedAuthorization":False},"reportPath":str(out/'unified-preflight-report.json')}
    p=out/"candidate-manifest.json"; p.write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n")
    return manifest

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description="unified-preflight-v1 qualification CLI; preflight only")
    parser.add_argument('--mode', required=True, choices=['preflight'])
    parser.add_argument('--output', required=True)
    args=parser.parse_args(argv)
    out=Path(args.output).resolve()
    if out.exists(): raise SystemExit(f"refusing to overwrite existing output directory: {out}")
    out.mkdir(parents=True)
    import_evidence=assert_module_file_and_hash(campaign_harness, EXPECTED_HARNESS_PATH, EXPECTED_HARNESS_SHA256)
    patch_evidence=patch_replay_body_capture()
    prep=prepare_isolated_workspace(out)
    cycle=Path(prep['cycle']); registry=Path(prep['registry'])
    inputs=out/"adapter-inputs"
    sdd=make_sdd_suite(inputs); few=make_fewshot_suite(inputs, cycle, registry)
    union, ledger=UnionBuilder().build([sdd, few]); freeze_suite(union, out/"freeze"/"UNION-preview-not-replayed-as-official-T4.json")
    sdd_run=run_and_collect(sdd, target_sdd(cycle, registry), out/"sdd", cycle/"P2a/openapi-carddemo-stage6r3.yaml", cycle, registry, [cycle/"P2b/runs"])
    few_run=run_and_collect(few, target_few(cycle), out/"fewshot", cycle/"collection-01/E2-2/response-original.txt", cycle, registry, [cycle/"P2c-few-shot/runs", cycle/"P2b/runs"])
    gcov=collect_gcov_parser_evidence()
    counts={"sdd_cases":len(sdd.cases),"fewshot_cases":len(few.cases),"union_preview_cases":len(union.cases),"http_completed":sdd_run['totals']['completed']+few_run['totals']['completed'],"checker_ok":sum(1 for r in [*sdd_run['checks'],*few_run['checks']] if r['checker'].get('ok')),"reached_cobol":sum(1 for r in [*sdd_run['checks'],*few_run['checks']] if r['reach'].get('reached_cobol')),"quiet_applications":sum(1 for a in [*sdd_run['applications_inline'],*few_run['applications_inline']] if a.get('target_quiet'))}
    report={"kind":"unified-preflight-v1-report","scope":"single executable technical preflight; not campaign; not official T1/T2/T3/T4 generation","harnessImport":import_evidence,"bodyCapturePatch":patch_evidence,"prepared":prep,"adapterEvidence":{"sddInput":str(inputs/'sdd-three-track-frozen-requests.json'),"fewshotInput":str(inputs/'fewshot-post-patch-representative.txt'),"unionPreviewLedger":ledger},"runs":{"sdd":sdd_run,"fewshot":few_run},"gcovParserEvidence":gcov,"counts":counts,"blockersPreserved":["No campaign authorization is created by this preflight.","Coverage evidence parses existing gcov artifacts; no fresh official coverage measurement was run.","Union preview is frozen for coupling evidence only and is not an official T4 suite."],"businessSourceEdited":False}
    (out/"unified-preflight-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n")
    manifest=write_candidate_manifest(out, report)
    (out/"REPORT.md").write_text("# unified-preflight-v1\n\n"+json.dumps({"counts":counts,"harnessImport":import_evidence,"manifest":str(out/'candidate-manifest.json')}, indent=2, ensure_ascii=False)+"\n", encoding='utf-8')
    print(json.dumps({"output":str(out),"counts":counts,"manifest":str(out/'candidate-manifest.json'),"officialGateEnabled":False}, indent=2, ensure_ascii=False))
    return 0

if __name__=='__main__':
    raise SystemExit(main())

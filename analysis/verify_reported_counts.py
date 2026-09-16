#!/usr/bin/env python3
"""Recompute the reported study counts from preserved records.

No business API, COBOL program or LLM is invoked. Checks admission by condition/strategy/status,
non-admission causes, few-shot multipleOf false rejections, partition and divergence reach, the
assertion matrix including the revised reporting analysis (v3), documentation of end-of-file
behaviors in the recovered contracts, the a priori obligation denominator, coverage unions,
COBOL line anchors and the worked reporting example.
"""
import argparse, csv, hashlib, json, re
from collections import Counter, defaultdict
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 400
p = argparse.ArgumentParser()
p.add_argument('--study-root', type=Path, default=Path(__file__).resolve().parents[1] / 'source-roots/aws-carddemo-cycle-v1')
args = p.parse_args()
R = Path(__file__).resolve().parent
S = args.study_root
ext = S / 'P3/retrospective-analysis-v2'
rows = [json.loads(l) for l in (ext / 'run-01/official-cases.jsonl').read_text().splitlines()]
comp = [json.loads(l) for l in (ext / 'run-01/complementary-cases.jsonl').read_text().splitlines()]

# ---- L0/L1 denominators
assert len(rows) == 12700 and len(comp) == 84
http = dict(Counter(x['status'] for x in rows)); assert http == {200: 1068, 400: 4378, 500: 7254}
assert Counter((x['status'], x['businessObserved']) for x in rows) == {(500, False): 7252, (400, False): 4378, (200, True): 1068, (500, True): 2}
strata = {s: {'applied': sum(x['strategy'] == s for x in rows), 'observed': sum(x['businessObserved'] for x in rows if x['strategy'] == s)} for s in ['T1', 'T2', 'T3', 'T4']}
assert [(v['applied'], v['observed']) for v in strata.values()] == [(88, 20), (5868, 177), (394, 338), (6350, 535)]

# ---- Table: admission by condition x strategy (T4 excluded)
adm = defaultdict(Counter)
for x in rows:
    if x['strategy'] == 'T4':
        continue
    k = (x['arm'], x['strategy']); adm[k]['n'] += 1; adm[k][x['status']] += 1; adm[k]['obs'] += x['businessObserved']
expected_adm = {
    ('zero-shot', 'T1'): (31, 0, 0, 31, 0), ('zero-shot', 'T2'): (2700, 0, 0, 2700, 0), ('zero-shot', 'T3'): (156, 128, 0, 28, 128),
    ('few-shot', 'T1'): (45, 16, 28, 1, 17), ('few-shot', 'T2'): (2700, 159, 1674, 867, 159), ('few-shot', 'T3'): (116, 88, 28, 0, 88),
    ('SDD', 'T1'): (12, 3, 9, 0, 3), ('SDD', 'T2'): (468, 18, 450, 0, 18), ('SDD', 'T3'): (122, 122, 0, 0, 122)}
for k, v in expected_adm.items():
    assert (adm[k]['n'], adm[k][200], adm[k][400], adm[k][500], adm[k]['obs']) == v, (k, adm[k])

# ---- Non-admitted HTTP 500 causes
def cause(d):
    if 'binding token' in d: return 'binding'
    if 'ASCII' in d or 'Unicode' in d or 'ascii' in d: return 'encoding'
    if 'JSONDecode' in d: return 'json'
    if 'base64' in d.lower() or 'decode to' in d or 'Non-base' in d: return 'record_decoding'
    if 'ValidationError' in d: return 'validation_as_500'
    return 'other_or_none'
c500 = Counter((x['arm'], cause(' '.join((x['responseSummary'] or {}).get('diagnostics', []) or []))) for x in rows if x['status'] == 500 and not x['businessObserved'])
assert c500 == {('zero-shot', 'validation_as_500'): 2168, ('zero-shot', 'binding'): 1896, ('zero-shot', 'encoding'): 906, ('zero-shot', 'json'): 266,
                ('zero-shot', 'record_decoding'): 240, ('zero-shot', 'other_or_none'): 42, ('few-shot', 'encoding'): 1478, ('few-shot', 'json'): 256}, c500
assert Counter(json.dumps(x['responseSummary'].get('category')) for x in rows if x['arm'] == 'SDD' and x['status'] == 400) == {'"request_representation"': 918}

# ---- Few-shot HTTP 400 causes and false multipleOf rejections
rej = S / 'P3/official-campaign-large12k-run-v2/p2b-preparation/isolated-cycle/aws-carddemo-cycle-v1/P2c-few-shot/outputs/http-rejections.jsonl'
c400 = Counter()
for line in rej.read_text().splitlines():
    e = str(json.loads(line).get('error', ''))
    if 'multiple of' in e:
        vals = re.findall(r'(-?[0-9][0-9.eE+-]*) is not a multiple of ([0-9.]+)', e)
        allfalse = all((Decimal(v) / Decimal(s)) % 1 == 0 for v, s in vals)
        others = [q for q in e.split(';') if 'multiple of' not in q]
        c400['false_only' if allfalse and not others else 'false_plus_other' if allfalse else 'genuine_or_mixed'] += 1
    elif 'fixture token prefix' in e: c400['binding_prefix'] += 1
    elif 'required property' in e: c400['required'] += 1
    else: c400['other_schema'] += 1
assert c400 == {'false_only': 394, 'false_plus_other': 238, 'binding_prefix': 774, 'required': 516, 'other_schema': 1524, 'genuine_or_mixed': 14}, c400
assert sum(c400.values()) == 3460

# ---- Demonstration idiom transfer and EOF documentation in contracts
demos = sorted((S / 'P1/few-shot-candidate').glob('demo-*/openapi.yaml'))
assert len(demos) == 3 and all('multipleOf: 0.01' in d.read_text() for d in demos)
contracts = {c: (S / f'collection-01/{c}/response-original.txt').read_text() for c in ['E1-1', 'E1-2', 'E1-3', 'E2-1', 'E2-2', 'E2-3']}
sdd = (S / 'P2a/openapi-carddemo-stage6r3.yaml').read_text()
assert [('multipleOf' in contracts[c]) for c in contracts] == [False, False, False, True, True, True] and 'multipleOf' not in sdd
eof_interest = re.compile(r'not rewritten|not explicitly flushed|last\s+account\s+retains|not reached', re.I)
eof_report = re.compile(r'again\s+to\s+page|adds? (TRAN-AMT|its amount|the retained TRAN-AMT) again', re.I)
for c, t in contracts.items():
    assert eof_interest.search(t) and eof_report.search(t), c
    assert not re.search(r"\n\s*'?400'?:", t) if c.startswith('E1') else True
assert 'The source\'s final-account update branch is' in contracts['E1-1'] and 'multipleOf: 0.01' in contracts['E2-1']
spec = S / 'sdd-runs/E3-01/specs'
assert 'V-23' in (spec / 'semantic-validation-carddemo/requirements.md').read_text()
assert 'No final interest flush' in (spec / 'api-contract-carddemo-r3/requirements.md').read_text()

# ---- Partition reach and divergence-condition reach
def parts(cases, track):
    return {q for x in cases if x['businessObserved'] and x['track'] == track for q in x['partitions']}
reach = {}
for tr in ['posting', 'interest', 'reporting']:
    o, cp = parts(rows, tr), parts(comp, tr)
    reach[tr] = (len(o), len(cp), len(o | cp), sorted(cp - o))
SYN = {'limit_above': 'reject_102', 'expiry_after': 'reject_103'}
def parts(cases, track):
    return {SYN.get(q, q) for x in cases if x['businessObserved'] and x['track'] == track for q in x['partitions']}
reach = {}
for tr in ['posting', 'interest', 'reporting']:
    o, cp = parts(rows, tr), parts(comp, tr)
    reach[tr] = (len(o), len(cp), len(o | cp), sorted(cp - o))
assert [(v[0], v[1], v[2]) for v in reach.values()] == [(4, 8, 8), (4, 6, 6), (7, 11, 13)], reach
assert sum(len(v[3]) for v in reach.values()) == 12
offobs = [x for x in rows if x['businessObserved']]
assert not any('eof_selected' in x['partitions'] for x in offobs)
assert Counter(tuple(sorted(x['partitions'])) for x in offobs if x['track'] == 'interest') == {('final_account_eof', 'multiple_accounts', 'specific_nonzero', 'specific_zero'): 298}
assert Counter(x['track'] for x in offobs) == {'posting': 284, 'interest': 298, 'reporting': 488}
assert [len({x['semanticInputKey'] for x in offobs if x['track'] == t}) for t in ['posting', 'interest', 'reporting']] == [60, 29, 18]

# ---- Assertion matrix
def matrix(cases):
    m = Counter()
    for x in cases:
        for c in x['checks']:
            m[(x['track'], c['name'], c['verdict'])] += 1
    return m
mo, mc = matrix(rows), matrix(comp)
assert Counter(c['verdict'] for x in rows for c in x['checks']) == {'pass': 3574, 'not_exercised': 486}
assert Counter(c['verdict'] for x in comp for c in x['checks']) == {'pass': 324, 'failed': 22, 'not_exercised': 14}
assert mo[('interest', 'accounts_financial_all_groups', 'pass')] == 298 and mo[('reporting', 'report_all_subtotals_grand_financial', 'not_exercised')] == 486
assert mc[('interest', 'accounts_financial_all_groups', 'failed')] == 14 and mc[('reporting', 'report_all_subtotals_grand_financial', 'failed')] == 8
assert sum(v for (t, n, vd), v in mo.items() if t == 'posting' and vd == 'pass') == 1704
v3dir = S / 'P3/retrospective-analysis-v3'
v3 = [json.loads(l) for l in (v3dir / 'reporting-verdicts-v3.jsonl').read_text().splitlines()]
v3c = lambda lane: Counter(r['irepV3'] for r in v3 if r['lane'] == lane)
assert v3c('official') == {'failed': 392, 'not_exercised': 96} and v3c('complementary') == {'failed': 15, 'not_exercised': 7}
assert Counter(r['deltaRep'] for r in v3 if r['lane'] == 'official' and r['irepV3'] == 'failed') == {'omitted_totals': 392}
assert Counter(r['deltaRep'] for r in v3 if r['lane'] == 'complementary' and r['irepV3'] == 'failed') == {'stale_eof_addition': 8, 'omitted_totals': 7}
assert Counter(r['exit'] for r in v3 if r['lane'] == 'official') == {'next_sentence_loop_exit': 392, 'dateparm_eof': 58, 'empty_tranfile_exit': 36, 'first_xref_abort': 2}
assert all(r['legacyTotalsMatch'] in (True, None) for r in v3) and not any(r.get('inRangeAfterOutOfRange') for r in v3)
assert Counter(r['strategy'] + '/' + r['arm'] for r in v3 if r['lane'] == 'official' and r['irepV3'] == 'failed' and r['strategy'] != 'T4') == {'T3/zero-shot': 56, 'T3/few-shot': 56, 'T3/SDD': 77, 'T1/SDD': 1, 'T2/SDD': 6}
# revised totals: official P 3574 F 392 N 94 (abort cases carry no I_rep check); complement P 324 F 29 N 7
off_irep_n = sum(1 for r in v3 if r['lane'] == 'official' and r['irepV3'] == 'not_exercised' and r['exit'] != 'first_xref_abort')
assert off_irep_n == 94 and 486 == 392 + off_irep_n
assert Counter(r['scenario'] for r in v3 if r['lane'] == 'complementary' and r['irepV3'] == 'failed') == {'date-boundaries-in-out-v1': 7, 'card-break-two-groups-v1': 4, 'pagination-threshold-20-v1': 4}
# a priori obligation denominator
oc = defaultdict(lambda: {'official': 0, 'complementary': 0})
for r in csv.DictReader((ext / 'run-01/obligation-coverage.csv').open()):
    oc[r['obligation']][r['lane']] += int(r['applicationsWithPartialCheck'] or 0)
assert len(oc) == 25 and sum(v['official'] > 0 for v in oc.values()) == 20 and sum(v['complementary'] > 0 for v in oc.values()) == 19
# SDD closed request: one situation per operation for every strategy
for r in csv.DictReader((ext / 'run-01/strategy-contribution.csv').open()):
    if r['contract'] == 'E3-SDD-stage6r3':
        assert (r['T1'], r['T2'], r['T3'], r['unionT123']) == ('1', '1', '1', '1'), r
# NEXT SENTENCE documentation: loop exit stated only by E2-3 and SDD requirements
norm = lambda s: re.sub(r'\s+', ' ', s)
assert 'ends processing rather than merely skipping that record' in norm(contracts['E2-3'])
assert 'loop-sentence exit, not skip-and-continue' in norm((spec / 'api-contract-carddemo-r3/requirements.md').read_text())
assert 'skipping the remainder of that iteration' in norm(contracts['E1-2']) and 'for that iteration' in norm(contracts['E1-3']) and 'skip the rest of the loop body' in norm(contracts['E2-2'])
assert 'skip the remaining loop body' in norm(contracts['E1-1']) and "skipping the remainder of the loop's sentence" in norm(contracts['E2-1'])
assert not any('ends processing rather than' in norm(contracts[c]) for c in ['E1-1', 'E1-2', 'E1-3', 'E2-1', 'E2-2'])
assert 'jsonschema==4.26.0' in (S / 'P2a/uv-install.log').read_text()
assert Counter((x['scenario'], x['status']) for x in comp if x['status'] == 400) == {('card-break-two-groups-v1', 400): 3, ('pagination-threshold-20-v1', 400): 3}
assert {x['arm'] for x in comp if x['status'] == 400} == {'few-shot'}

# ---- Checker qualification
q = json.loads((ext / 'oracle-qualification.json').read_text())
assert (q['trials'], q['detectedTargeted'], q['unavailable'], q['intentionalBlindSpots']) == (35, 30, 4, 1)
by = defaultdict(lambda: [0, 0])
for r in q['byClass']:
    by[r['domain']][0] += r['trials']; by[r['domain']][1] += r['detected']
assert dict(by) == {'accounts': [7, 6], 'interest': [9, 8], 'posting': [12, 10], 'reporting': [7, 6]}, dict(by)

# ---- gcov unions (GnuCOBOL-generated C lines)
cov = defaultdict(int)
for r in csv.DictReader((S / 'P3/official-analysis-v1/coverage_union_by_arm_condition_track.csv').open()):
    cov[r['track']] = max(cov[r['track']], int(r['union_executed_lines']))
assert dict(cov) == {'interest': 585, 'posting': 651, 'reporting': 714}
ccov = {r[1]: (int(r[4]), int(r[5])) for r in csv.reader((S / 'P3/complementary-matrix-coverage-v1/evidence/current/coverage-summary.csv').open()) if r and r[0] == 'program'}
assert ccov == {'CBACT04C': (606, 1029), 'CBTRN02C': (686, 1120), 'CBTRN03C': (763, 1192)}, ccov

# ---- COBOL source line anchors
cbl = S.parent / 'aws-carddemo-preparation/research-corpus/app/cbl'
a04 = (cbl / 'CBACT04C.cbl').read_text().splitlines(); t03 = (cbl / 'CBTRN03C.cbl').read_text().splitlines()
assert 'PERFORM 1050-UPDATE-ACCOUNT' in a04[195] and 'PERFORM 1050-UPDATE-ACCOUNT' in a04[219] and 'UNTIL END-OF-FILE' in a04[187]
assert 'ADD TRAN-AMT TO WS-PAGE-TOTAL' in t03[199] and '1110-WRITE-GRAND-TOTALS' in t03[202]

# ---- Worked example raw pins
example = json.loads((R / 'worked-example.json').read_text())
assert sum(example['inputAmountsCents']) == example['sumCents'] == 1110 and example['observedGrandTotalCents'] - example['sumCents'] == example['excessCents'] == 444
for pin in example['rawFiles']:
    assert hashlib.sha256((S / pin['path']).read_bytes()).hexdigest() == pin['sha256'], pin['path']

result = {'status': 'verified', 'official': len(rows), 'complementary': len(comp), 'http': http, 'strata': strata,
          'admissionByConditionStrategy': {f'{k[0]}/{k[1]}': v for k, v in expected_adm.items()},
          'nonAdmitted500Causes': {f'{k[0]}/{k[1]}': v for k, v in c500.items()}, 'fewShot400Causes': dict(c400),
          'partitionReach': {k: {'official': v[0], 'complement': v[1], 'union': v[2], 'complementOnly': v[3]} for k, v in reach.items()},
          'reportingIrepV3': {'official': dict(v3c('official')), 'complementary': dict(v3c('complementary'))},
          'assertionTotals': {'official': {'pass': 3574, 'failed': 392, 'not_exercised': 94}, 'complementary': {'pass': 324, 'failed': 29, 'not_exercised': 7}},
          'officialObservationsReaching': {'interestLastGroup': 0, 'reportStaleEofAddition': 0, 'reportOmittedTotals': 392},
          'obligationsWithAssertion': {'official': 20, 'complementary': 19, 'of': 25},
          'workedExampleRawPinsVerified': True,
          'limits': ['No new business execution; counts recomputed from preserved case records',
                     'Source-derived and declared-invariant verdicts are not independent domain adjudication']}
(R / 'REPORTED-COUNTS.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['status', 'official', 'complementary', 'reportingIrepV3', 'assertionTotals']}, indent=1))

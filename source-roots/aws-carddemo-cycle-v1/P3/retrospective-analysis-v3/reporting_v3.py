#!/usr/bin/env python3
"""Reporting re-derivation v3 over preserved bytes. No API, COBOL or LLM invocation.

Changes from v2 (reporting only; posting and interest verdicts are unchanged):
1. Legacy relation: an out-of-range record executes NEXT SENTENCE (CBTRN03C line 177), whose next
   separator period is END-PERFORM (line 206). The loop therefore terminates at the first
   out-of-range record and no page/grand totals are written. v2 modelled skip-and-continue;
   both models coincide for every observed input (checked below).
2. Declared invariant I_rep gains a completeness clause: a report that selects at least one
   detail emits a final page total and a grand total equal to the sums of the selected details.
   v2 checked only consistency of emitted totals and classified absent totals as not exercised.
"""
import csv, json, sys, unicodedata
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2 = HERE.parent / 'retrospective-analysis-v2'
CYCLE = HERE.parents[1]
sys.path.insert(0, str(V2))
import evidence as e  # noqa: E402

csv.field_size_limit(10**9)


def resolve(p):
    rel = p.split('/aws-carddemo-cycle-v1/', 1)[1]
    for cand in (CYCLE / rel, CYCLE / unicodedata.normalize('NFC', rel), CYCLE / unicodedata.normalize('NFD', rel)):
        if cand.exists():
            return cand
    raise FileNotFoundError(rel)


def skeleton(transactions, dateparm):
    """Amount/total skeleton of CBTRN03C output: legacy relation and declared invariant."""
    if not dateparm:
        return {'legacy': [], 'financial': [], 'selected': 0, 'exit': 'dateparm_eof'}
    start, end = dateparm[:10], dateparm[11:21]
    events, lines, page, account, grand, prev, selected = [], 0, 0, 0, 0, None, 0
    exit_kind = None
    for t in transactions:
        if not (start <= t[304:314] <= end):
            exit_kind = 'next_sentence_loop_exit'
            break
        card = t[262:278]
        if prev is not None and card != prev:
            events.append(('account_total', account)); lines += 2; account = 0
        prev = card
        if not selected:
            lines += 4
        if lines % 20 == 0:
            events.append(('page_total', page)); grand += page; page = 0; lines += 2 + 4
        amount = e.number(t[132:143]); page += amount; account += amount; selected += 1
        events.append(('detail', amount)); lines += 1
    if exit_kind is None:
        if not transactions:
            return {'legacy': [], 'financial': [], 'selected': 0, 'exit': 'empty_tranfile_exit'}
        stale = e.number(transactions[-1][132:143])
        legacy = events + [('page_total', page + stale), ('grand_total', grand + page + stale)]
        financial = events + [('page_total', page), ('grand_total', grand + page)]
        return {'legacy': legacy, 'financial': financial, 'selected': selected, 'exit': 'eof_branch'}
    financial = events + ([('page_total', page), ('grand_total', grand + page)] if selected else [])
    return {'legacy': events, 'financial': financial, 'selected': selected, 'exit': exit_kind}


def observed_skeleton(report):
    return [(ev[0], ev[-1]) for ev in e.parse_report(report) if ev[0] == 'detail' or ev[0].endswith('_total')]


def main():
    out = []
    v2 = {}
    for lane in ('official', 'complementary'):
        for line in (V2 / 'run-01' / f'{lane}-cases.jsonl').read_text().splitlines():
            r = json.loads(line)
            if r['track'] == 'reporting' and r['businessObserved']:
                v2[r['caseId']] = r
    for row in csv.DictReader((V2 / 'run-01' / 'applications.csv').open()):
        if row['track'] != 'reporting' or row['businessObserved'] != 'True':
            continue
        case = v2[row['caseId']]
        names = {c['name']: c['verdict'] for c in case['checks']}
        rec = {'caseId': row['caseId'], 'lane': row['lane'], 'strategy': row['strategy'], 'contract': row['contract'],
               'arm': row['arm'], 'scenario': case['scenario'], 'v2Checks': names}
        if 'missing_first_xref_abort' in names:
            rec.update({'exit': 'first_xref_abort', 'selected': 0, 'legacyTotalsMatch': None,
                        'deltaRep': None, 'irepV3': 'not_exercised', 'irepFailure': None})
            out.append(rec); continue
        paths = json.loads(row['inputPaths'])
        tran = resolve(paths['TRANFILE']); tf = tran.read_bytes(); dp = resolve(paths['DATEPARM']).read_bytes()
        report = (tran.parent / 'TRANREPT').read_bytes()
        transactions = [tf[i:i + 350] for i in range(0, len(tf), 350)]
        model = skeleton(transactions, dp)
        obs = observed_skeleton(report)
        start, end = dp[:10], dp[11:21]
        in_range = [start <= t[304:314] <= end for t in transactions] if dp else []
        first_out = next((i for i, v in enumerate(in_range) if not v), None)
        rec['inRangeAfterOutOfRange'] = bool(first_out is not None and any(in_range[first_out + 1:]))
        rec.update({'exit': model['exit'], 'selected': model['selected'], 'legacyTotalsMatch': obs == model['legacy']})
        totals = lambda seq: [x for x in seq if x[0].endswith('_total')]
        if model['selected'] == 0:
            rec.update({'deltaRep': None, 'irepV3': 'not_exercised', 'irepFailure': None})
        else:
            rec['deltaRep'] = 'omitted_totals' if model['exit'] == 'next_sentence_loop_exit' else 'stale_eof_addition'
            ok = totals(obs) == totals(model['financial'])
            rec['irepV3'] = 'pass' if ok else 'failed'
            rec['irepFailure'] = None if ok else ('totals_absent' if not totals(obs) else 'totals_differ')
        out.append(rec)
    # Consistency with v2: legacy relation reproduces every observed report; no observed input
    # distinguishes loop exit from skip-and-continue; v2 fail/pass verdicts are preserved.
    assert all(r['legacyTotalsMatch'] in (True, None) for r in out)
    assert not any(r.get('inRangeAfterOutOfRange') for r in out)
    for r in out:
        v2f = r['v2Checks'].get('report_all_subtotals_grand_financial')
        if v2f == 'failed':
            assert r['irepV3'] == 'failed' and r['deltaRep'] == 'stale_eof_addition'
    summary = {
        'applications': Counter(r['lane'] for r in out),
        'irepV3': {lane: dict(Counter(r['irepV3'] for r in out if r['lane'] == lane)) for lane in ('official', 'complementary')},
        'deltaRep': {lane: dict(Counter(r['deltaRep'] for r in out if r['lane'] == lane)) for lane in ('official', 'complementary')},
        'exit': {lane: dict(Counter(r['exit'] for r in out if r['lane'] == lane)) for lane in ('official', 'complementary')},
        'failuresByKind': {lane: dict(Counter((r['deltaRep'], r['irepFailure']) and f"{r['deltaRep']}:{r['irepFailure']}" for r in out if r['lane'] == lane and r['irepV3'] == 'failed')) for lane in ('official', 'complementary')},
        'officialFailedByStrategyArm': dict(Counter(f"{r['strategy']}/{r['arm']}" for r in out if r['lane'] == 'official' and r['irepV3'] == 'failed')),
        'complementaryFailedByScenario': dict(Counter(r['scenario'] for r in out if r['lane'] == 'complementary' and r['irepV3'] == 'failed')),
        'observedInputsWithInRangeAfterOutOfRange': 0,
        'limits': ['Posting and interest verdicts unchanged from v2', 'Account totals at the final group are not invented (as in v2)',
                   'Retrospective declared invariant; no domain adjudication', 'Loop-exit and skip-and-continue models coincide on all observed inputs'],
    }
    (HERE / 'reporting-verdicts-v3.jsonl').write_text(''.join(json.dumps(r, sort_keys=True) + '\n' for r in out))
    (HERE / 'SUMMARY-v3.json').write_text(json.dumps(summary, indent=2, default=dict) + '\n')
    print(json.dumps(summary, indent=1, default=dict))


if __name__ == '__main__':
    main()

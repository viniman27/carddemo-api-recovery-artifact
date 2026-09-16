"""Validate a post-Stage-9 test-quality gate manifest; never approve a campaign."""
import argparse
import json
from datetime import datetime
from pathlib import Path

BUSINESS_ORACLE_KINDS = {'business_semantic', 'legacy_observable', 'domain_reference', 'independent_reference_model'}
SCHEMA_ONLY_KINDS = {'contract_schema', 'http_structural', 'openapi_schema'}
DISALLOWED_AUTHORITY_TYPES = {'llm_output', 'generated_contract', 'generated_harness', 'tool_output_only'}
REQUIRED_CAMPAIGNS = {'T1', 'T2', 'T3', 'T4'}


def require(condition, errors, message):
    if not condition:
        errors.append(message)


def obj(value):
    return value if isinstance(value, dict) else {}


def load_json(path):
    with path.open(encoding='utf-8') as handle:
        return json.load(handle)


def valid_timestamp(value):
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return False
    return True


def validate_manifest(data):
    errors = []
    warnings = []
    require(isinstance(data, dict), errors, 'manifest must be a JSON object')
    if not isinstance(data, dict):
        return errors, warnings

    for key in ('run_id', 'capability'):
        require(isinstance(data.get(key), str) and data[key].strip(), errors, f'{key} required')

    require(data.get('stage9_api_ready_for_testing') is True, errors,
            'Stage 9 api_ready_for_testing must be true before test-quality gate review')
    handoff = obj(data.get('stage9_handoff_evidence'))
    require(handoff.get('api_ready_for_testing') is True, errors,
            'Stage 9 handoff evidence must record api_ready_for_testing=true')
    require(isinstance(handoff.get('path'), str) and handoff.get('path'), errors,
            'Stage 9 handoff evidence path required')
    if handoff.get('campaign_ready') is True:
        warnings.append('campaign_ready=true is ignored by this checker; test campaign approval remains separate')

    freeze = obj(data.get('prospective_freeze'))
    require(freeze.get('frozen_before_execution') is True, errors,
            'prospective freeze must be recorded before any result observation')
    require(isinstance(freeze.get('freeze_id'), str) and freeze.get('freeze_id'), errors,
            'freeze_id required')
    require(valid_timestamp(freeze.get('frozen_at')), errors,
            'frozen_at must be an ISO timestamp')
    supplement = obj(data.get('descriptive_post_observation_supplementation'))
    require(supplement.get('separate_from_freeze') is True, errors,
            'descriptive post-observation supplementation must be separate from the frozen suite')

    coverage = obj(data.get('coverage'))
    denominator = obj(coverage.get('denominator'))
    require(denominator.get('known') is True, errors, 'coverage denominator must be known')
    count = denominator.get('count')
    require(type(count) is int and count > 0, errors, 'coverage denominator count must be a positive integer')
    require(isinstance(denominator.get('source'), str) and denominator.get('source'), errors,
            'coverage denominator source required')
    counts = obj(coverage.get('counts'))
    required_count_keys = ('executed', 'not_executed', 'inconclusive', 'not_applicable')
    for key in required_count_keys:
        value = counts.get(key)
        require(type(value) is int and value >= 0, errors,
                f'coverage counts.{key} must be a nonnegative integer')
    if all(type(counts.get(key)) is int for key in required_count_keys) and type(count) is int:
        total = sum(counts[key] for key in required_count_keys)
        require(total == count, errors, 'coverage counts must sum to the known denominator')
        require(counts.get('executed', 0) > 0, errors,
                'all obligations not executed; classify as gap/inconclusive, not ready')
    require(isinstance(coverage.get('not_executed_items'), list), errors,
            'not_executed_items list required so not-executed is not hidden as N/A')
    require(isinstance(coverage.get('inconclusive_items'), list), errors,
            'inconclusive_items list required so missing observation stays inconclusive')
    require(isinstance(coverage.get('gap_items'), list), errors,
            'gap_items list required and separate from traceability')
    target_policy = coverage.get('target_policy')
    require(isinstance(target_policy, str) and 'percent target' in target_policy.lower(), errors,
            'target policy must forbid choosing a coverage percent after seeing results')

    fixtures = obj(data.get('fixtures'))
    require(fixtures.get('per_case_reset') is True, errors, 'fixtures/resources must reset per case')
    require(fixtures.get('resource_snapshot_compared') is True, errors,
            'fixture/resource reset must be evidenced by resource snapshot comparison')
    require(isinstance(fixtures.get('reset_evidence'), str) and fixtures.get('reset_evidence'), errors,
            'reset evidence required')

    oracles = data.get('oracles')
    require(isinstance(oracles, list) and bool(oracles), errors, 'oracle inventory required')
    business_oracles = []
    schema_only_count = 0
    if isinstance(oracles, list):
        for oracle in oracles:
            if not isinstance(oracle, dict):
                errors.append('each oracle must be an object')
                continue
            oid = oracle.get('id', '<unknown>')
            kind = oracle.get('kind')
            authority = obj(oracle.get('authority_source'))
            atype = authority.get('type')
            if kind in SCHEMA_ONLY_KINDS:
                schema_only_count += 1
            if atype in DISALLOWED_AUTHORITY_TYPES:
                errors.append(f'LLM output cannot be oracle authority for {oid}; generated tool/contract output is not independent expected-outcome authority')
            if kind in BUSINESS_ORACLE_KINDS:
                business_oracles.append(oracle)
                require(oracle.get('independent_from_llm_outputs') is True, errors,
                        f'business/semantic oracle {oid} must be independent from LLM outputs')
                counterexamples = oracle.get('wrong_output_counterexamples')
                require(isinstance(counterexamples, list) and bool(counterexamples), errors,
                        f'business/semantic oracle {oid} must include wrong-output counterexamples')
            elif kind not in SCHEMA_ONLY_KINDS:
                warnings.append(f'oracle {oid} has nonstandard kind {kind!r}; substantive review must classify its authority')
    require(bool(business_oracles), errors,
            'no independent business/semantic oracle; schema/HTTP checks cannot qualify business obligations')
    if schema_only_count and not business_oracles:
        errors.append('contract/schema-only oracle inventory is structural only, not business validation')

    campaigns = data.get('campaigns')
    require(isinstance(campaigns, list), errors, 'campaigns list required')
    by_id = {c.get('id'): c for c in campaigns if isinstance(c, dict)} if isinstance(campaigns, list) else {}
    missing = sorted(REQUIRED_CAMPAIGNS - set(by_id))
    require(not missing, errors, 'missing campaign integrity sections: ' + ', '.join(missing))
    t1 = obj(by_id.get('T1'))
    require(t1.get('bad_outputs_preserved_in_results') is True, errors,
            'T1 generator bad outputs must remain in results, not disappear from evidence')
    t2 = obj(by_id.get('T2'))
    require(t2.get('mode') in {'pure_openapi', 'domain_fuzz'}, errors,
            'T2 mode must explicitly be pure_openapi or domain_fuzz')
    require(t2.get('domain_fuzz_separate') is True, errors,
            'T2 pure OpenAPI fuzzing and domain fuzzing must be explicitly separated')
    t3 = obj(by_id.get('T3'))
    require(t3.get('guards_bound_to_checker') is True and t3.get('transitions_bound_to_checker') is True, errors,
            'T3 model guards/transitions must be bound to executable checkers')
    t4 = obj(by_id.get('T4'))
    require(t4.get('no_new_cases') is True, errors, 'T4 union must not introduce new cases')
    require(t4.get('fresh_reset_per_case') is True, errors, 'T4 union must preserve per-case reset')
    require(t4.get('not_counted_as_independent_replica') is True, errors,
            'T4 union must not be counted as an independent replica')

    mutations = obj(data.get('mutations'))
    if mutations.get('used') is True:
        require(mutations.get('scope') == 'test_checker_only', errors,
                'mutations may qualify test/checker evidence only')
        require(mutations.get('source_artifacts_altered') is False, errors,
                'mutations must not alter source artifacts, contracts, APIs or cases')

    trace = obj(data.get('traceability'))
    require(isinstance(trace.get('checks_to_obligations'), dict) and bool(trace.get('checks_to_obligations')), errors,
            'traceability from checks to obligations required')
    require(trace.get('gaps_separate') is True, errors,
            'traceability links and gaps must be recorded separately')

    review = obj(data.get('human_review'))
    require(review.get('required') is True, errors, 'human review requirement must remain explicit')
    require(review.get('approval_claimed_by_tool') is False, errors,
            'tool output must not claim human review approval')
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    try:
        data = load_json(args.manifest)
        errors, warnings = validate_manifest(data)
    except (OSError, json.JSONDecodeError) as exc:
        errors, warnings = [str(exc)], []
    result = {
        'status': 'ready_for_review' if not errors else 'fail',
        'ok': not errors,
        'human_approval_granted': False,
        'errors': errors,
        'warnings': warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())

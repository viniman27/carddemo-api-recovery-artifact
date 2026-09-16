# AWS CardDemo P3 local preparation closure — promotion/freeze procedure

Status: local preparation candidate only. No official campaign, AWS generation, freeze, replay, or external T1 send is authorized by this file.

## Pinned entrypoints
- T2: `P3/t2-offline-preparation-v4/src/t2_offline_bridge.py::generate_t2_offline_suite_for_contract`
- T3_SDD: `P3/t3-sdd-external-selection-v3/sdd_external_selection.py::build_selected_t3_suite`
- orchestration: `P3/preparation-orchestration-v1/src/preparation_orchestration.py`
- harness: `P3/campaign-harness-v3`

## Procedure
1. Present this local preparation closure and blockers to Researcher.
2. Obtain explicit human fixture promotion by exact manifest bytes/hash; record that this is fixture authority only, not expected-output oracle authority.
3. Obtain explicit T1 send/freeze decision from the separate T1 track; preserve exact receipts before import.
4. Generate/freeze T2 using pinned t2-offline-preparation-v4 and per-operation fixture binding; preserve original OpenAPI pins and request bytes.
5. Generate/freeze T3 using t3-sdd-external-selection-v3 with explicit final budget maxDepth=6/maxPathsPerTrackFixture=50; retain old static maxPaths=12 evidence as historical evidence, not overwritten proof.
6. Only after T1/T2/T3 official suites exist, build dependent T4 union in order T1,T2,T3 and request explicit campaign/replay authorization.

## Remaining blockers
- T1 still awaits separate explicit send/freeze path; do not touch the parallel T1 worktree/task here.
- Candidate fixture bytes need human promotion before official suites; technical binding creates no oracle authority.
- Official AWS generation/freeze/campaign remains gate-closed after this local preparation.

## Provenance note
Preparation deterministically pins contracts, fixture bytes, budgets, seeds, order, reset and error policy. Promotion of fixtures, T1 provider sending, oracle authority, and official campaign execution remain human/model-judgment gates.

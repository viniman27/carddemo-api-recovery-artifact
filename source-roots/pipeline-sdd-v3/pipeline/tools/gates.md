# Recorded gate freshness — v3

## Purpose and command

From FRAMEWORK_ROOT:

    python3 tools/check_gate.py RUN_ROOT specs/artifact-capability/spec.json

Read-only, Python standard library. No model calls, source execution, record repair, signatures or authorization. Output is JSON; exit 0 means `current`, exit 1 any other state, exit 2 invalid CLI usage.

- `current`: the recorded approval and declared files match; NOT a new approval or permission to execute.
- `stale`: reviewed artifact/context or a pinned file differs, including transitive upstream changes.
- `unreviewed`: a local or upstream review is absent/not completed/not approve.
- `blocked`: a reviewed local or upstream gate still lists blocking gaps.
- `invalid`: malformed metadata, missing file, invalid path/hash, inconsistent identity/stage, omitted predecessor or invalid graph.

Consumers must require `current` AND the actual researcher's stage authorization. The tool reports `human_approval_granted: false` in every state. It never updates `spec.json`; attach output to the run's review log. Fixing a missing record means obtaining/recovering the real review, not fabricating it to make the tool pass.

## Metadata in spec.json

Instantiate `settings/templates/specs/init.json`. The template deliberately remains incomplete/unreviewed.

Required run fields:

- `run_id` and `capability`: nonempty identity strings, matched across the chain.
- `pipeline_stage`: integer 1–9, excluding booleans.
- `artifact_type`: respectively `pipeline-scope`, `capability-selection`, `legacy-evidence`, `capability-semantics`, `canonical-data-boundary`, `api-contract`, `adapter-behavior`, `semantic-validation`, `implementation-executable-qualification`.
- `artifact_path`: exact RUN_ROOT-relative path to the authoritative stage artifact.
- `upstream_specs`: ordered, unique RUN_ROOT-relative paths to upstream spec.json files. Stage 1 has none. Later stages include the immediate predecessor and may include additional earlier stages.
- `gate.completeness_gate_passed`: boolean, initially false.
- `gate.blocking_gaps`: list, initially empty; any entry blocks a current review.
- `gate.gate_review_date`: ISO calendar date YYYY-MM-DD when an actual completed review was recorded, otherwise null.
- `gate.review`: null until a real review is recorded. The shape is `settings/templates/specs/gate-review.json`.

A completed review record contains:

- `decision: "approve"`, a nonempty `reviewer`, and the gate date.
- `context`: an exact copy of the reviewed `run_id`, `capability`, `pipeline_stage`, `artifact_type`.
- `artifact`: `{path, sha256}` for the artifact actually reviewed; path matches artifact_path.
- `upstream_specs`: `{path, sha256}` pins for the exact upstream spec.json bytes, in the same order as the top-level list. Their own recorded reviews are recursively checked.
- `authorization`: `{path, sha256}` pointing to a local preserved reference of the actual human authorization. Record the real author/scope in that reference; do not invent a signature or export private review material.

Hashes are 64 lowercase hexadecimal characters computed from exact bytes, not normalized text. A pin identifies a byte version; a version nickname may be used in the review log but cannot replace the hash. Changes to the upstream metadata file also invalidate its downstream pin, even if only formatting changed. This is deliberately conservative.

## State and progression limits

- O Stage 9 exige manifesto de entrada explícito: upstream 1–8, fontes de implementação, contrato, toolchain, recursos e comandos build/start/qualify/package pinados.
- O run deve registrar se a implementação foi gerada agora ou adotada; adoção de fonte existente é `source_adoption_and_build` e não pode ser descrita como geração do zero.
- A qualificação deve construir em diretório novo a partir de fontes, não copiar binários/runs/preflight antigos; rerun com o mesmo `run_id` deve falhar fechado para preservar evidência.
- A saída deve incluir pacote executável com `launch_stage9.py` ou equivalente e relatório/revisão pendente separada.

The checker supports one capability within one run. Cross-run or cross-capability reuse is rejected, including shared scope records; such reuse requires a separately reviewed protocol extension, not an unchecked exception. Backward revisions remain possible: re-review the changed authority first and then its consumers. Do not copy synthetic test approvals into actual runs.

The eighth artifact is the validation PLAN. The ninth artifact is executable implementation qualification and must record fresh execution evidence and implementation provenance. This checker does not interpret the separate validation report as a replacement plan or grant approval for execution/publication. Keep report review separate. Framework drafting fields such as phase, tasks-generated and ready_for_implementation do not override this protocol.

## Post-Stage-9 test-quality gate

After a Stage 9 handoff records `api_ready_for_testing=true`, downstream testing uses a complementary test-quality manifest, not a tenth pipeline stage. The template and checklist live in `settings/templates/testing/test-quality-gate.md` and `settings/templates/testing/test-quality-gate-manifest.json`; validate the instantiated manifest with:

    python3 tools/check_test_quality_gate.py path/to/test-quality-gate.json

This check is intentionally about test readiness and interpretation discipline: prospective freeze before observing results, known coverage denominator/counts, explicit not-executed/inconclusive/N/A/gap separation, fixture reset evidence, independent business-oracle authority, wrong-output counterexamples, T1 bad-output preservation, T2 pure-OpenAPI versus domain-fuzz separation, T3 guard/transition checker binding, T4 union limits, mutation scope and traceability. It never reopens stages 1–9, never approves campaigns, and never turns schema/HTTP success into business validation.

The tool checks only declared stage artifacts and spec dependencies. It does not discover omitted corpus files, prompts, review attachments or configuration dependencies; run/corpus manifests and substantive review remain necessary. It does not parse Markdown, reconcile the completeness matrix, evaluate the reviewer's arguments, authenticate the reviewer, verify the content/scope of authorization, check revocations outside the files or freeze the whole filesystem. A fabricated internally consistent record can match hashes; this is why no result grants human approval.

Paths must be exact POSIX relative paths without absolute/dot/dot-dot/empty segments, backslash, colon or NUL. Symlinks within the named paths and symlink RUN_ROOT are rejected. JSON duplicate keys are rejected. The tool is not a sandbox against concurrent filesystem mutation.

## Exercised workflow

The synthetic tests construct a three-stage dependency chain, confirm `current`, change the first artifact without editing metadata, observe `stale` at stage 3, restore the original bytes and observe `current` again. A separate eight-stage fixture demonstrates that withdrawing an upstream approval remains `unreviewed` even when downstream hashes are mechanically refreshed. These are test fixtures, not research approvals or AWS runs.

    python3 -m unittest discover -s tests -v
    PYTHONOPTIMIZE=1 python3 -m unittest discover -s tests -v

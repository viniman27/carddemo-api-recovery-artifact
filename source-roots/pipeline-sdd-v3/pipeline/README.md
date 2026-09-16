# SDD pipeline v3 — review candidate

This framework derives eight separate artifacts from legacy evidence. It is not an automatic experiment runner, an approved study protocol, or a set of answers for CardDemo.

Read `steering/` and `settings/rules/README.md`. Generic optional `settings/templates/steering-custom/` integrations are NOT active in this revision: do not run their Jira/Azure/cross-repo instructions or copy their `.sdd/` destinations. Enabling one requires a separate scoped review. Only stage templates and the rules index form the default workflow. Instantiate templates from `settings/templates/pipeline/` in a separate run directory. Resolve `FRAMEWORK_ROOT`, `RUN_ROOT` and `CORPUS_ROOT` explicitly; never infer `.sdd/` or an old account-balance directory.

New runs use this order: scope → capability selection → legacy evidence → capability semantics → canonical boundary → API contract → adapter behavior → validation plan/report. Human approval is required between stages and before validation execution. No script grants it.

The current public application target is AWS CardDemo; this is NOT the later research study Phase 2 corpus. The framework itself remains case-neutral. Run-specific facts, prepared results and expected answers do not belong here.

Changes and provenance are documented in `../MELHORIAS.md`, `../CHANGELOG.md` and `../provenance.json`. The untouched v2 framework is under `../baseline/`.

The additional short revision adds reverse-completeness matrices, recorded counterexample review and version-bound gate records. See `tools/gates.md` for the read-only freshness checker.

Mechanical evidence checking: see `tools/README.md`. Passing source-anchor checks establishes location/integrity only, not truth of a claim or readiness of the next stage.

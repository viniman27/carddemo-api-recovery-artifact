# Mechanical source-anchor verifier

For recorded gate freshness and version invalidation, use `check_gate.py` as documented in [gates.md](gates.md). For Stage 9 executable qualification, use `stage9_qualify.py`; it copies an adopted implementation into an isolated run, performs localhost HTTP execution and records provenance. After Stage 9 reports `api_ready_for_testing=true`, use `check_test_quality_gate.py` to validate the downstream test-quality manifest before treating T1–T4 suites as ready for human review. These checks have different purposes; none grants human approval.

Anchor/gate/test-quality checks are Python standard library only. `stage9_qualify.py` does execute local COBOL/API code when `--execute` is supplied, but does not call models, modify stages 1–8, or run T1–T4 campaigns.

From FRAMEWORK_ROOT:

    python3 tools/check_anchors.py CORPUS_ROOT manifest.json anchors.json

Post-Stage-9 test-quality manifest check:

    python3 tools/check_test_quality_gate.py path/to/test-quality-gate.json

That validator checks manifest discipline only: prospective freeze, known coverage denominator, schema-vs-business oracle separation, fixture reset evidence, T1–T4 integrity flags, mutation scope and traceability gaps. It does not inspect raw campaign traces, compute coverage, approve execution or authenticate reviewers.

Inputs are explicit paths. The manifest is a projection of the approved source allowlist, NOT a new corpus selection. Supply only source/text dependencies authorized for source anchoring. Source bytes must match before their locations can support a mechanical pass.

Manifest shape:

    {"files": [{"path": "cbl/main.cbl", "sha256": "<64 lowercase hex>", "encoding": "utf-8"}]}

Register shape:

    {"items": [{"id": "E-1", "spec_section": "Section 2.1",
      "anchors": [{"path": "cbl/main.cbl", "start": 1, "end": 2}]}]}

These are format illustrations, not usable evidence or hashes. The tests create explicitly synthetic files and compute real hashes at execution time. No sample here is an AWS answer.

Paths are POSIX relative paths, exact and case-preserved; no leading slash, empty/dot/dot-dot segments, backslashes, colon or NUL. Full paths distinguish homonymous files. Symlinks in the corpus root or entry components are rejected. Hashes must already be valid lowercase SHA-256 strings: the tool does not repair them. Encoding defaults to strict UTF-8; a different encoding must be declared. A trailing newline does not create an extra source line.

Every item has a unique E-n (positive integer, no leading zero), a nonempty spec section and at least one explicit source anchor. The tool validates membership, bytes and ranges; it does not parse Markdown, check that spec_section exists, prove that every evidence item is registered, or judge meaning. Reconcile the structured register against the authoritative spec during human review. Do not convert execution evidence to fictitious source lines: run/log anchors remain separate.

JSON output contains ok, errors, evidence_checked and human_approval=false. Exit 0 means only mechanical success; exit 1 means data/anchor failure. CLI usage errors use argparse's exit 2. This is not an operating-system sandbox against a concurrent process swapping files, nor a verifier of the manifest's authorization/signature.

Run regressions from the workspace parent:

    python3 -m unittest discover -s tests -v
    PYTHONOPTIMIZE=1 python3 -m unittest discover -s tests -v

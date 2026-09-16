# Anonymization notes

This artifact was prepared for double-anonymous review. The following transformations were applied to the original evidence snapshot. They affect identity and local-environment text only. They change no experimental input field used by program logic, no response status and no count.

## Removed

- Python virtual environments, test-framework caches and `__pycache__` directories.
- One packaged tarball of an SDD execution package whose extracted contents are already present under `sdd-runs/`.
- Project-management notes that did not describe executed steps.

## Replaced in text files

| Category | Replacement |
|---|---|
| Local absolute paths (home, workspace, upstream checkout) | `<REDACTED_LOCAL_PATH>`, `<WORKSPACE>`, `<UPSTREAM_CHECKOUT>` |
| Names of people recorded as stage reviewers/approvers | `Researcher` |
| Local environment, cache and process labels | neutral labels such as `local runtime`, `auxiliary run`, `WORKSPACE-NOTES.md` |
| References to the enclosing academic program and its documents | `research study`, `main study`, `pesquisa principal` |
| Internal working labels of analysis directories | `retrospective-analysis-v1`, `retrospective-analysis-v2` |

Model identifiers, providers and request parameters of the evaluated extraction and test-generation calls are **not** changed.

## Replaced in fixture and record bytes

The synthetic merchant city and ZIP code in fixture records were replaced with values of identical length: `Sometown` and `10000000`. Fixed-width COBOL records therefore keep their layout. The same substitution was applied consistently to inputs, captured outputs and JSON projections.

## Consequences for hash pins

`ANONYMIZATION-LEDGER.jsonl` lists every modified file with its original and artifact SHA-256. Hash pins stored inside historical receipts, manifests and verification ledgers refer to the original bytes. To check a historical pin for a modified file, use the ledger's `originalSha256`. `analysis/worked-example.json` pins the artifact bytes.

Case-level identity hashes (for example `semanticInputKey` and `requestKey`) were computed before anonymization and are kept as recorded. They are used only for equality and set counts.

# Complementary MBT binding v1

Executable TDD tool for the remaining MBT method binding closure.

It evaluates the 12 pinned complementary essential fixture cases against the real
`P3/reference-executable-v4` model interpreter. It does not call APIs, rerun COBOL,
rerun the original campaign, call an LLM, or generate/modify T1/T2.

## Commands

```bash
python3 -m unittest discover -s P3/complementary-mbt-binding-v1/tests -v
python3 -m mbt_binding plan --cycle-root "$PWD"
python3 -m mbt_binding validate --cycle-root "$PWD" --out P3/complementary-mbt-binding-v1/latest/candidate-registry.json
```

The validate output is a prospective candidate registry only. Shared-only cases remain
available to the complementary checker ledger but are not promoted to official T3.

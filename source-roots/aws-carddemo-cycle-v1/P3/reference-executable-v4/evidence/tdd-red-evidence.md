# TDD RED evidence — reference-executable-v4

Comando executado antes do patch em `reference-executable-v4`:

```sh
python3 -m unittest discover -s tests -v
```

Resultado real observado: exit `1`, `Ran 16 tests`, `FAILED (failures=4)`.

Falhas esperadas que reproduziram os bloqueios/bug antes do patch:

- `test_intcalc_zero_rate_branch_is_selectable_without_interest_write_attempt`: esperava `['INTCALC-T009Z']`, recebeu `[]` porque o domínio v3 não tinha taxa zero selecionável.
- `test_intcalc_obl_008_is_tied_to_reachable_eof_no_final_update_behavior`: `INTCALC-OBL-008` não estava em `INTCALC-T006.obligationRefs`.
- `test_whitelisted_interest_write_mutant_in_posttran_t003_is_rejected`: `ValidationError not raised` ao inserir `interest_write_attempt` em `POSTTRAN-T003`.
- `test_cli_relative_root_and_absolute_root_validate_same_pins`: root `.` retornou exit `1` e múltiplos `missing source ...`; root absoluto passava.

Esses testes foram escritos em v4 antes das alterações em `executable_reference.py` e `model.json`. O diretório v3 foi preservado sem escrita.

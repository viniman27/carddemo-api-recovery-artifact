# Reference executable v4 — AWS CardDemo P3

Status: `draft_needs_review`.

Correção estreita da v3 preservada em novo diretório. Esta referência continua sendo rascunho executável finito para `CBTRN02C/POSTTRAN`, `CBACT04C/INTCALC` e `CBTRN03C/TRANREPT`; não é fixture oficial, campanha T1-T4, execução COBOL, nem prova de equivalência semântica completa.

## Correções v3 → v4

- `V3-BLOCK-001`: adiciona ramo selecionável `INTCALC-T009Z` para `disc_rate_path=zero`, sustentado por `CBACT04C.cbl:213-217` (`IF DIS-INT-RATE NOT = 0`). Esse ramo emite `interest_rate_zero_no_interest_write`, volta ao loop abstrato e não emite `interest_compute_attempt` nem `interest_write_attempt`.
- Taxa não zero preservada: `specific`/`default` seguem por `INTCALC-T007` e `INTCALC-T009`, com `interest_compute_attempt` e `interest_write_attempt`.
- `V3-BLOCK-002`: `INTCALC-OBL-008` fica ligada ao EOF normal sem update final em `INTCALC-T006`, com testemunho alcançável na travessia (`INTCALC-T001`, `INTCALC-T006`). `INTCALC-OBL-007` permanece ligada ao caminho abstrato de update (`INTCALC-T010`); isso é limite do modelo v3 preservado, não prova de atualização física COBOL.
- `V3-BLOCK-003`: eventos emitidos agora têm escopo tipado por capacidade em `EVENT_CAPABILITY_SCOPES`. O mutante representativo que injeta `interest_write_attempt` em `POSTTRAN-T003` é rejeitado. Essa checagem impede reutilização transcapacidade de nomes conhecidos, mas não é alegada como prova automática de semântica.
- Bug CLI relativo: `root='.'` é resolvido para caminho absoluto antes de validar pins; root relativo e absoluto agora produzem os mesmos `sourcePins` e `counts`.

## Reproduzir

A partir de `reference-executable-v4/`:

```sh
python3 -m unittest discover -s tests -v
python3 executable_reference.py . --traverse CBTRN02C_POSTTRAN --traverse CBACT04C_INTCALC --traverse CBTRN03C_TRANREPT --max-depth 8 --max-paths 80
python3 <WORKSPACE>/aws-carddemo-cycle-v1/P3/reference-executable-v4/executable_reference.py <WORKSPACE>/aws-carddemo-cycle-v1/P3/reference-executable-v4 --traverse CBTRN02C_POSTTRAN --traverse CBACT04C_INTCALC --traverse CBTRN03C_TRANREPT --max-depth 8 --max-paths 80
```

Resultados observados desta versão estão em `mechanical-validation-report.json` e `evidence/`.

## Evidências versionadas

- `evidence/tdd-red-evidence.md`: testes RED reais observados antes do patch.
- `evidence/unit-tests-*.txt`: execução final dos 16 testes.
- `evidence/cli-relative-root.json` e `evidence/cli-absolute-root.json`: validação/travessia nas três capacidades, com root relativo e absoluto.
- `evidence/obligation-witnesses.json`: obrigações v2 mapeadas a transições e testemunhos de caminhos alcançáveis no orçamento usado.
- `evidence/mutant-and-rate-branches.json`: rejeição do mutante `POSTTRAN-T003` e traços taxa zero/não zero.

## Limites mantidos

A referência continua finita e orçamentada. `frontier`, `unknown` e `omittedCount` são exposição de limite, não cobertura completa. Efeitos são tentativas/eventos observáveis e controle de fluxo, não durabilidade, commit, rollback ou estado persistido pós-falha. O runtime local runtime expôs contexto automático do repositório; isto está registrado em `exposure-manifest.json` e não é tratado como isolamento absoluto.

# Evidência — campaign-harness-v2

Gerada em `evidence-20260915T130333Z/` por execução local sintética com HTTP loopback. Não houve AWS, COBOL, API pública, oráculos/quarentena ou chamadas de modelo.

## Comandos executados

```bash
python3 ../campaign-harness-review-v1/outside_in_probes.py --output evidence-20260915T130333Z/v1-red-probes
python3 -m unittest tests/test_campaign_harness.py -v > evidence-20260915T130333Z/unittest.stdout 2> evidence-20260915T130333Z/unittest.stderr
python3 outside_in_probes.py --output evidence-20260915T130333Z/v2-green-probes > evidence-20260915T130333Z/probes.stdout 2> evidence-20260915T130333Z/probes.stderr
python3 qualification_demo.py --output evidence-20260915T130333Z/demo-output > evidence-20260915T130333Z/demo.stdout 2> evidence-20260915T130333Z/demo.stderr
python3 campaign_harness_cli.py --mode official-aws --config ../current-pretest-state-v4.json > evidence-20260915T130333Z/cli-official.stdout 2> evidence-20260915T130333Z/cli-official.stderr
```

`evidence-20260915T130333Z/cli-official.exit` registrou `2`, que é o fail-closed esperado.

## RED/GREEN

### RED preservado da revisão v1

`evidence-20260915T130333Z/v1-red-probes/outside_in_probes.json`:

```json
{
  "defects_reproduced": 5,
  "probes_total": 5
}
```

Os cinco defeitos reproduzidos foram: colapso de headers duplicados, reset não acoplado ao servidor, cascata após timeout em alvo serial, expectativa ignorada para 500 inesperado e path traversal por `case_id`.

### GREEN v2

`evidence-20260915T130333Z/v2-green-probes/outside_in_probes.json`:

```json
{
  "fixes_verified": 5,
  "probes_total": 5
}
```

Verificações cobertas:

1. `duplicate_headers_wire_preserved`: servidor recebeu `X-Dup: one` e `X-Dup: two` na ordem.
2. `reset_workdir_bound_to_service_state`: servidor leu/mutou `state.txt` no `workdir`; a segunda aplicação viu `original\n` novamente.
3. `deadline_reaped_before_next_application`: timeout em `/slow` foi seguido de parada/join/quietude do alvo controlado; `/fast` executou depois em novo servidor/workdir.
4. `expectations_separate_from_transport`: 500 inesperado virou `violation`, 500 autorizado virou `pass`, checker não suportado virou `inconclusive`; todos separados de `completed`.
5. `case_id_preserved_workdir_opaque_contained`: `case_id='x/../../escaped-case'` foi preservado nos registros, mas o diretório ficou opaco e contido em `applications/`.

## Resultado dos testes

`evidence-20260915T130333Z/unittest.stderr`:

```text
Ran 9 tests in 4.406s
OK
```

Cobertura comportamental dos testes sintéticos:

1. hash de freeze detecta adulteração;
2. body ausente, bytes vazios e JSON `{}` são distintos no fio e na identidade;
3. headers duplicados/ordem são preservados no HTTP real;
4. servidor por aplicação recebe `workdir` fresco e reset efetivo;
5. timeout em alvo estático não controlado aborta o restante como `not_executed`;
6. expectativas estruturais são separadas de transporte;
7. IDs são preservados em registros e paths são opacos/contidos; symlink em pacote é recusado;
8. união T4 preserva ordem, proveniência e expectativas distintas;
9. CLI aceita só qualificação sintética e falha fechada para campanha oficial.

## Totais calculados da demonstração

De `evidence-20260915T130333Z/demo-output/report.json`:

```json
{
  "union_cases": 8,
  "httpCallsObserved": 16,
  "firstRunTotals": {
    "planned": 8,
    "attempted": 8,
    "completed": 7,
    "deadline_failures": 1,
    "transport_failures": 0,
    "http_failures": 0,
    "not_executed": 0,
    "expectation_passes": 6,
    "expectation_violations": 0,
    "expectation_inconclusive": 1
  },
  "secondRunTotals": {
    "planned": 8,
    "attempted": 8,
    "completed": 7,
    "deadline_failures": 1,
    "transport_failures": 0,
    "http_failures": 0,
    "not_executed": 0,
    "expectation_passes": 6,
    "expectation_violations": 0,
    "expectation_inconclusive": 1
  }
}
```

Observações:

- `tamperDetected=true` com erro `suite freeze hash mismatch`.
- `duplicateHeadersPreserved=true`.
- `workdirResetObservedEveryApplication=true` e `workdirMutationObserved=true` demonstram reset acoplado ao servidor real, não apenas cópia local.
- `targetQuietEveryAttempt=true` demonstra stop/join/reap de todos os servidores controlados.
- `documented500NotHttpFailure=true`; 500 documentado não foi reclassificado como falha de infraestrutura.
- `unsupportedCheckerNotSuccess=true`; checker não suportado não passa silenciosamente.
- `officialRunnerImplemented=false` e `awsLoaded=false`.

## Artefatos de evidência

- `evidence-20260915T130333Z/v1-red-probes/outside_in_probes.json`: reproduções RED v1.
- `evidence-20260915T130333Z/v2-green-probes/outside_in_probes.json`: probes outside-in v2.
- `evidence-20260915T130333Z/demo-output/report.json`: relatório agregado da demo.
- `evidence-20260915T130333Z/demo-output/frozen-suites/T1.json`, `T2.json`, `T3.json`, `T4-union.json`: suítes congeladas com hashes.
- `evidence-20260915T130333Z/demo-output/tamper-copy.json`: cópia adulterada propositalmente para demonstrar falha de hash.
- `evidence-20260915T130333Z/demo-output/runs/T4-controlled-1/` e `T4-controlled-2/`: reexecuções T4 com servidor controlado por aplicação.
- `evidence-20260915T130333Z/cli-official.*`: prova de CLI oficial bloqueada.

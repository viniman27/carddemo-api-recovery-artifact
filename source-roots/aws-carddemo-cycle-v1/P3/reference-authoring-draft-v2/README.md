# Reference authoring draft v2 — AWS CardDemo P3

Status: `draft_needs_independent_review`. Este rascunho corrige a versão v1 reprovada, mas não concede PASS independente, não autoriza fixtures oficiais e não inicia campanha.

## Escopo

Capacidades cobertas:

- `CBTRN02C/POSTTRAN`
- `CBACT04C/INTCALC`
- `CBTRN03C/TRANREPT`

Autoridade usada: pacote `reference-authoring-input-v1` e revisão v1 para orientar os achados. Nenhum contrato E1/E2, SDD, API, suporte, fixture, quarentena, run, preflight/resultados, caso oficial ou execução COBOL foi usado como fonte de expectativa.

## Principais correções sobre v1

- `TRANREPT`: EOF não é mais tratado como escrita universal de totais; o teste textual de data antes do ramo EOF foi modelado e o conteúdo do receiver em EOF permanece `unknown` quando a autoridade não estabelece retenção.
- `TRANREPT`: caminho fora do intervalo agora é decidível: `NEXT SENTENCE` evita lookup, detalhe e acúmulo.
- `TRANREPT`: ausência de `Account Total` final no EOF foi adicionada como obrigação própria.
- `POSTTRAN`: falha de `WRITE TRANFILE` após TCATBAL/ACCOUNT é caminho explícito de abend sem afirmação de commit/durabilidade.
- `POSTTRAN`: `REWRITE ACCOUNT INVALID KEY` define razão 109, não chama abend local e o fluxo continua para `WRITE TRANFILE`.
- `model.json`: substituído por modelo estruturado com estados, transições, guardas AST tipadas, efeitos, observáveis, âncoras e obrigações.

## Validação mecânica

Rodar no diretório deste draft:

```bash
python3 -m unittest discover -s tests -v
python3 validate_reference_model.py .
```

O validador verifica unicidade de IDs, referências de estados/obrigações/variáveis/fontes, AST de guardas tipado, finitude/reachability e cobertura da matriz `FAIL-01..06`. Ele não executa COBOL e não conta casos oficiais.

## Arquivos

- `obligations.json` — obrigações revisadas, preservando IDs v1 quando aplicável e adicionando obrigações novas para lacunas bloqueadoras.
- `model.json` — modelo MBT finito e estruturado para futura seleção determinística de caminhos.
- `resolution-matrix.json` — resolução source-anchored dos seis bloqueios.
- `exposure-manifest.json` — exposição efetiva/hash dos arquivos lidos ou mecanicamente verificados.
- `validate_reference_model.py` e `tests/` — validação mecânica local.
- `mechanical-validation-report.json` — saída real do validador (`status: PASS`, 3 capacidades, 32 estados, 62 transições, 25 obrigações, 6 achados resolvidos).

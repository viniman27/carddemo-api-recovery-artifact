# Extensão local v2 — lacunas recuperadas


## Resultado verificável

A mesma campanha de 12.700 aplicações contém 1.070 observações de negócio vinculadas. Todas agora têm assertivas parciais: 3.574 passes e 486 verificações não exercitadas. Antes, apenas 1.002 observações tinham assertivas. O delta de 68 está identificado individualmente em `resolved-cases.json`:

- 58 DATEPARM de zero bytes: EOF antes do laço de transações. Relatório vazio esperado; totais financeiros não exercitados. Ausência e registro parcial continuam diferentes de vazio.
- Oito entradas posting com signed DISPLAY: codec ASCII qualificado localmente. Todas têm rejeição 100 por cartão ausente. Isso não prova aritmética financeira de transações negativas aceitas.
- Duas saídas anormais: primeiro cartão selecionado ausente em CARDXREF, diagnóstico/status 23 e abort local 12, antes de conteúdo no relatório. Não generalizar para falhas de I/O posteriores ou outros ambientes.

As assertivas já aplicáveis em v1 permanecem idênticas. Na matriz complementar de 84 aplicações, 78 têm assertivas e seis continuam bloqueadas antes do COBOL. Mantidos os 324 passes, 22 falhas e 14 não exercitados. As 22 falhas são 14 ocorrências da expectativa financeira da última conta e oito dos totais de reporting; não 22 defeitos independentes. Posting mantém 42 aplicações aprovadas apenas nas assertivas implementadas.

A contribuição permanece: T1=19, T2=103, T3=17 situações por contrato/operação, união=126; exclusivos=9/93/14; T4 não agrega situação nova. Não usar como ranking de eficácia: budgets e superfícies de contrato diferem.

## Verificação das ferramentas

- Bateria final: 18 testes passaram (`final-tests.log`).
- Sondagem de representação: 13 valores emitidos por programa sintético local, GnuCOBOL 3.2.0, conferidos byte a byte (`signed-probe/qualification.json`). Não executa CardDemo.
- Reexecutadas as mesmas 35 sondas de saída/estado: 30 erros-alvo detectados, quatro ausências inconclusivas, um timestamp deliberadamente excluído não detectado. Não é mutation score do programa.
- Ledger v2: 9.008 entradas de hash verificadas. Juntamente com v1, 17.918 entradas conferidas, com sobreposição entre versões; não anunciar esse total como arquivos únicos.
- 28 pins documentais sustentam o método de extração recuperado.
- Verificação separada: contagens, casos antigos/novos, conjuntos de contribuição, hashes e diagnósticos anteriores. Não equivale a revisão científica independente.

## Lacunas que não foram transformadas em PASS

- 11.630 aplicações sem auditoria de negócio vinculada: não há desfecho COBOL reconstruído por suposição.
- Seis rejeições few-shot por multipleOf: causa diagnosticada; execução COBOL ausente não foi criada e a API histórica não foi corrigida.
- Overflow, aritmética negativa aceita, outros encodings, ordem interna de efeitos, rollback, falhas gerais de I/O, timestamps excluídos.
- Autoridade compartilhada entre fonte e oráculos; expectativas financeiras sem adjudicação de domínio independente; limites históricos de hash-pin dos audits externos.
- Custos totais SDD/implementação/trabalho humano não consolidados como comparação de eficiência.

## Escopo e reprodução

Zero novas aplicações de negócio, zero chamadas externas ou publicação. Pesquisa principal, Fase 2, COBOL, contratos e APIs fora do escopo de alteração.

Comandos executados neste diretório com `PYTHONDONTWRITEBYTECODE=1` e interpretador `../../P2a/.venv/bin/python`:

    -m unittest -v
    probe_signed.py
    analysis.py --out run-01
    qualify.py
    verify_results.py

Para nova análise, usar outro diretório de saída e adaptar explicitamente o verificador, que aponta para run-01. Não sobrescrever evidência de referência. Os logs RED/GREEN e as versões anteriores ficam preservados.

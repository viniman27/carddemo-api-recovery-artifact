# Decisão de prontidão e revisão da preparação

Decisão: NÃO iniciar campanhas AWS ainda. A autorização discricionária do usuário foi recebida; o bloqueio é material/metodológico, não uma nova solicitação de permissão rotineira.

## Autoridade e escolhas

Mensagem recebida: “Deixo ao seu criterio, se ja considerar que estamos prontos, vamos aos testes, se nao faca as revisoes necessarias.”

As direções D1–D8 foram selecionadas sob essa autorização do pesquisador em `experimental-direction-delegated-v1.json`. Isso não é aprovação humana individual de conteúdo ausente, nem substitui um manifesto concreto de liberação. Não voltar a pedir aceite das mesmas escolhas operacionais por rotina.

Mantidos: três trilhas e três braços; execução serial com reset por aplicação; dados COBOL na agenda externa; T1/T2 sem conhecimento do oráculo; referência MBT separada dos contratos; união reexecutada e dependente; análise descritiva com denominadores integrais. Sem novos campos/endpoints na API.

Refinamento do orçamento T2: 100 exemplos por operação/seed, divididos em até 50 positivos e 50 negativos, sem redistribuir espaço esgotado. Mantidas as seeds propostas. Esse orçamento ainda não foi executado em AWS; a qualificação descrita abaixo usa teto técnico de 12 por modo/seed. O limite temporal oficial e reset integrado ainda requerem runner.

## Revisão efetivamente concluída

1. Conferidos todos os pins do checkpoint `current-pretest-state-v3.json`; correspondem aos arquivos atuais. Não reabrir as três correções SDD já exercitadas apenas por relatórios históricos.
2. Selecionado e instalado Schemathesis 4.27.1 em `.venv-fuzz-preflight`, Python 3.12.2, sem alterar P2a ou instalações globais. Dependências exatas estão em `fuzz-preflight-requirements.txt`; dry-run de reinstalação verificou 27 pacotes, sem mudanças necessárias. É pin de versões, não hash-lock de distribuições/wheels.
3. Implementado `fuzz_preflight.py` com teste primeiro: serviço HTTP estritamente sintético em loopback, OpenAPI 3.1 próprio, sem abrir contrato, fixture ou fonte AWS. Não aceita target/schema remoto via argumentos.
4. Geração offline por Hypothesis, apenas Phase.generate, sem database, shrinking ou replay de falhas. A suíte é gravada antes de qualquer HTTP. Depois cada request preparado é enviado uma vez, sem redirects/retries, com recebimento do body conferido.
5. Checkers explícitos: status, content type e schema. O checker genérico que reprova todo 500 não é usado. Uma resposta deliberadamente inválida do serviço real foi detectada; os demais 500 documentados foram aceitos. Isso é qualificação estrutural, não oráculo de negócio.

## Evidência real

Diretório: `readiness-revision-20260915T105955Z/`.

- `synthetic-fuzzer/frozen-synthetic-suite.json`: suíte sintética persistida antes do HTTP.
- `synthetic-fuzzer/wire-receipts.json`: recebimentos reais.
- `synthetic-fuzzer/http-results.json`: status, bytes de resposta e falhas de schema.
- `synthetic-fuzzer/report.json`: resultado agregado real.
- `binding-tests.json`: 25 testes do adaptador passaram.
- `preparation-tests.json`: seis testes da preparação passaram, incluindo o ensaio do fuzzer.
- `previous-documents/manifest.json`: hashes das versões anteriores dos documentos alterados.

O ensaio gerou e executou 42 ocorrências, sem chamadas HTTP excedentes. Em cada seed houve dois exemplos positivos e 12 negativos. Todos os bodies positivos foram `{}`: uma única variante de body válido. Ocorrências e IDs de transporte diferentes não são diversidade de entrada de negócio. Não contabilizar estes números em T2 AWS.

Reprodução, a partir de P3:

    uv venv --python /opt/homebrew/opt/python@3.12/bin/python3.12 .venv-fuzz-preflight
    uv pip install --python .venv-fuzz-preflight/bin/python -r fuzz-preflight-requirements.txt
    .venv-fuzz-preflight/bin/python fuzz_preflight.py --output CAMINHO_NOVO_DE_EVIDENCIA
    ../P2a/.venv/bin/python -m unittest discover -s tests -v

Não recriar um venv existente sem necessidade; o primeiro comando é apenas setup para ambiente ausente. O diretório de saída precisa ser novo; o programa recusa sobrescrita. Replay exato dos casos preservados não implica que toda regeneração com a mesma seed reproduza IDs acessórios ou comportamento sob outra versão/ambiente.

## Bloqueios restantes, em ordem de dependência

1. Referência de avaliação independente: produzir/revisar obrigações, guardas, expectativas decidíveis e limites a partir do corpus original em contexto não exposto aos resultados/artefatos dos braços. Esta sessão já implementou e observou SDD; não pode chamar sua própria referência de independente. Contexto novo é controle de exposição, não prova automática de independência. Não ler quarentena nem reciclar respostas esperadas do suporte.
2. Fixtures oficiais: materializar famílias a partir dos layouts e daquela referência, com bytes, hashes, estado inicial e revisão. Os pacotes técnicos permanecem técnicos. Não congelar valores de juros/calendário/EOF/durabilidade por inferência conveniente.
3. Outros braços: implementar cada fachada com seu contrato isolado e driver comum quando aplicável, ou registrar não operacionalizabilidade com evidência. Não usar outputs E1/E2 para orientar novas alterações na API SDD nem iniciar comparação semântica agora.
4. Execução oficial: integrar congelamento de suítes, agenda de fixtures, reset, deadlines, atribuição por invocação, T1/T3/T4 e união. O ensaio sintético entregue não é esse runner; o módulo histórico `pretest_config.py` permanece preparatório e bloqueado.
5. Medição: qualificar instrumentação GnuCOBOL/GCC/gcov no binding corrente, denominadores comuns e flush efetivo; binários disponíveis não bastam. Congelar pacote concreto e admissibilidade antes da primeira célula oficial.

Não exigir fidelidade semântica perfeita da API como condição de começar: descobri-la é parte do experimento. O que falta é uma referência independente e infraestrutura comparativa suficiente para interpretar resultados sem circularidade.

## Limites e ferramentas

Nenhuma campanha AWS, geração por LLM, comparação ou leitura E1/E2 foi feita nesta revisão. O material externo baixado foi software público. A busca/extração web retornou indisponibilidade do gateway; não alterei a configuração global nem usei fallback pago. A API instalada da ferramenta foi inspecionada e exercitada localmente. Nenhuma nova execução auxiliar foi disparada para contornar o limite de uso registrado anteriormente.

Estado atual: implementação SDD tecnicamente exercitada; direção experimental selecionada sob autorização do pesquisador; fuzzer qualificado no escopo sintético; preparação experimental ainda incompleta. O próximo trabalho substantivo é a referência independente e os recursos oficiais, não mais uma repetição do smoke nominal.

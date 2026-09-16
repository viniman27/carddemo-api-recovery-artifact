# Consolidação da preparação — decisão antes de extrações

## Estado por etapa

- Preparação zero-shot: requisição concreta montada, hash registrado, não enviada.
- Preparação few-shot: requisição concreta montada com os mesmos alvo/instrução e as nove peças dos três exemplos revisados; não enviada. Revisão externa não encontrou bloqueante para revisão humana. Não são gold standard.
- Pipeline SDD: framework revisado; aplicação ao AWS ainda não iniciada.
- APIs e testes AWS: não iniciados.

## Pacote E1/E2

prepared-requests/E1.json e E2.json contêm exatamente os corpos candidatos, sem memória, ferramentas, histórico, preflight ou referência de avaliação. Manifesto registra hashes e tamanhos; os 19 arquivos-alvo são iguais em ambos. E2 adiciona somente exemplos externos. Fontes não foram normalizados/editados; delimitadores pertencem ao envelope, não ao corpus.

Modelo escolhido pelo pesquisador: gpt-6-astra/openai-codex via assinatura. Proposta de coleta: três execuções separadas E1 e três E2, com o mesmo corpo por braço, sem resposta anterior. Não prometer independência estatística perfeita: versões internas, cache e amostragem do provedor são limites. Proposta para falha: preservar tentativa, sem retry automático ou reparo semântico; pausa em quota/autenticação/erro de transporte. Invalidade de contrato é resultado, não razão para gerar até acertar.

temperature e max_output_tokens omitidos por rejeição demonstrada. Seed, top_p e reasoning omitidos; não afirmar controle ou suporte. Metadados retornados devem ser registrados por tentativa e diferenças expostas. Não truncar corpus para caber silenciosamente: rejeição de contexto bloqueia o braço e exige emenda anterior à retomada. Janela máxima não foi medida com o corpus nesta preparação.

## Referência e limites de escopo

Revisor leu allowlist e ampliou rascunho para 34 registros. Coordenador recomputou 54 âncoras: todas conferem; convenção de hash do trecho revisado inclui newline final, diferente do primeiro rascunho, que foi preservado. Evidência: ../evaluation-quarantine/parent-anchor-verification.json.

Proposta de adjudicação, sem inventar novas decisões humanas:
- Manter o recorte demonstrado POSTTRAN/INTCALC/TRANREPT. TRANBKP, COMBTRAN, SORT e JCL são contexto de fronteira, não novas capacidades executáveis obrigatórias deste ciclo. Não exigir execução integral dos cinco jobs como pré-requisito inventado.
- Preservar fontes e comportamento observado. Não corrigir bugs do COBOL nem inserir compensações no adaptador. Intenção de negócio e diagnóstico textual não substituem evidência dinâmica.
- Manter EOF/última conta e totais como questões explícitas. Congelar que serão avaliados e a política de adjudicação antes da coleta; só fixar expectativas numéricas após caracterização separada e antes dos testes oficiais. Não marcar omissão como N/A apenas porque um contrato não expõe o comportamento.
- Layouts físicos são requisitos da fronteira COBOL, não obrigação de expor registros brutos idênticos em JSON. Avaliar mapeamento preservando informação relevante.
- No teste direto do programa de relatório, DATEPARM define sua entrada de período; filtros hard-coded do JCL só se aplicam se a etapa SORT for de fato executada. Não escolher precedência arbitrária entre camadas diferentes.

O parecer externo levantou essas questões, mas não aprovou gates nem demonstrou comportamento dinâmico. Não chamar a referência de independente cega: coordenação já viu preflight. O JSON revisado continua candidato; estas propostas não o sobrescrevem.

## Gate para iniciar

Solicitar aceite único do pacote: três repetições por braço E1/E2 com os corpos registrados, política de ausência de reparo/retry, escopo e limites acima. Esse aceite não libera APIs/testes nem aprova antecipadamente os oito estágios SDD. Contextos experimentais não recebem este documento administrativo nem a quarentena de avaliação.

Antes do envio, o lançador deve conferir hashes dos corpos e bloquear troca de modelo/endpoint, capturar stream/metadata íntegros e usar diretório novo por tentativa. Não reutilizar probe.py como runner de corpus sem esse controle. Nenhum corpo foi enviado nesta consolidação.

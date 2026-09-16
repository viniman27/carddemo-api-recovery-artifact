# Análise semântica final — complemento ESSENTIAL12×7 actual84

Resultado: 84/84 casos classificados semanticamente com bytes reais preservados, sem rerodagem de API, COBOL, modelo ou campanha.

## Contagens principais
- Congelamento: 84 casos; execução: 84 tentados, 84 completados, 84 estruturais OK.
- Medição: 78 admissíveis; 6 limitados/inconclusivos para medição (não tratados como ausência de API).
- Partições por trilha: {'posting': 42, 'interest': 14, 'reporting': 28}.
- Vereditos semânticos por caso: {'pass': 56, 'inconclusive': 15, 'failed': 13}.
- Vereditos por trilha: {'interest': {'pass': 14}, 'posting': {'pass': 42}, 'reporting': {'inconclusive': 15, 'failed': 13}}.
- Vereditos por contrato: {'E1-1': {'pass': 8, 'inconclusive': 3, 'failed': 1}, 'E1-2': {'pass': 8, 'inconclusive': 3, 'failed': 1}, 'E1-3': {'pass': 8, 'inconclusive': 3, 'failed': 1}, 'E2-1': {'pass': 8, 'inconclusive': 1, 'failed': 3}, 'E2-2': {'pass': 8, 'inconclusive': 1, 'failed': 3}, 'E2-3': {'pass': 8, 'inconclusive': 1, 'failed': 3}, 'E3-SDD-stage6r3': {'pass': 8, 'inconclusive': 3, 'failed': 1}}.

## Defeitos legados e limites
- Defeitos legados observados nos 84 casos: 0 ocorrências registradas em `legacyDefects` no JSON.
- Defeitos legados suportados por fonte: 1 achado(s) em `sourceSupportedLegacyDefects`, com comportamento desejado vs. comportamento atual separados.
- Relatórios separam reprodução do comportamento legado de EOF/totais de correção financeira dos totais; uma reprodução do EOF legado não é automaticamente correção financeira.
- Obrigações não implementadas/sem campo observável permanecem inconclusivas; não há promoção para cobertura integral de 25 obrigações.

## Arquivos de prova
- JSON agregado: `actual84-semantic-analysis.json`.
- CSV por caso: `actual84-cases.csv`.
- Pins de entrada: `../complementary-matrix-v2/parent-full84-v1/campaign/campaign-report.json` e `../complementary-matrix-v2/parent-plan-absolute-v1/suite.freeze.json`.

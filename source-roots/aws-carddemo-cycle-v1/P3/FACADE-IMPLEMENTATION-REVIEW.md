# Revisão das implementações zero-shot/few-shot

Status: primeira entrega REPROVADA para fechamento da etapa de implementação. Correções em andamento; não promover os relatórios 9/9 dos agentes a prontidão.

## Defeito central

Ambas as fachadas validam envelopes mas executam recursos de fixture fixa, sem materializar arrays/argumentos do request. O coordenador confirmou no código e executou uma regressão independente das projeções de resposta: posting com array vazio e interest com argumento INPUTCHECK em todos os seis contratos. Os 12 checks falharam. Evidência: `facade-input-review-iz_yj72j/results.json`; comando `../P2a/.venv/bin/python qa_facade_input_effect.py` retornou 1.

Também não existia serviço HTTP nas entregas: campos status/http_status de uma chamada Python/CLI não comprovam resposta por rede.

## Correções exigidas para fechamento

- Bytes/argumentos realmente vindos do request, incluindo formatos válidos do contrato e datas/ordem na trilha relatório.
- Dataset bindings resolvidos de verdade na infraestrutura preprovisionada. Nenhum endpoint de setup necessário para materializar arquivos sequenciais já definidos no request.
- Validar o schema original sem impor campos/exclusões novas; preservar allOf/refs e parâmetros opcionais.
- Saídas capturadas sem filler inventado, conversão destrutiva, truncamento silencioso ou missing convertido em vazio.
- Serviço HTTP local nas rotas reais, exercitado por rede, com auditoria e variação de entrada, não somente fixture nominal.
- Preservar versões anteriores e não editar contrato, fonte COBOL, P2a ou API SDD.

Autoria recebida como self-report, não certificação. Esta revisão não compara qualidade dos braços nem executa campanha. As limitações de avaliação devem ser distinguidas de requests simplesmente ignorados pelo código.

# Referência MBT v4 — escopo aceito na preparação

A revisão `reference-independent-review-v4/REVIEW.md`, conferida pelo coordenador, registra PASS limitado à seleção de caminhos abstratos. Não é aprovação de campanha, oráculo completo, fixtures oficiais ou equivalência COBOL.

O coordenador reexecutou 16 testes da v4 com exit 0 e a CLI com caminhos relativo e absoluto nas três trilhas: exit 0, errors=[], 25 obrigações, 40 transições, 98 âncoras conferidas. A revisão confirmou correções de taxa zero, rastreabilidade do EOF, escopo de eventos e resolução de caminhos. Testemunhos demonstram alcance e referência; não substituem julgamento semântico. Fronteiras, omissões e unknown continuam explícitos.

Fontes de evidência:
- reference-executable-v4/
- reference-independent-review-v4/REVIEW.md
- reference-independent-review-v4/review.json

O modelo permanece com status histórico draft_needs_review; o PASS separado não será retroativamente incorporado como autoaprovação. Contexto automático AGENTS foi declarado pelos revisores: não alegar isolamento absoluto.

Próximas frentes autorizadas em execução:
- fixture-candidates-v1/: dados sintéticos candidatos baseados nas fontes, não pacotes oficiais; expectativas separadas;
- campaign-harness-v1/: qualificação sintética do núcleo serial de replay, união e reset, não campanhas AWS.

Ainda necessários: revisão/materialização completa dos recursos candidatos, integração de geradores e runners T1/T2/T3/T4, mapeamento de aplicabilidade, medição GnuCOBOL/gcov e flush, congelamento de suítes e manifesto concreto. Nenhuma campanha iniciada. Preservar versões anteriores e não reiniciar geração dos contratos ou pipeline SDD.

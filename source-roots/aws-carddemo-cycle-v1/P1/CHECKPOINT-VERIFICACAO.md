# Checkpoint de verificação técnica

Acesso: chamada mínima openai-codex/gpt-6-astra respondeu TRANSPORT_OK; modelo confirmado no registro da sessão 20260911_072803_f678c1. Evidência transport-probe.json. Não foi fornecido corpus da pesquisa. O CLI avisou que toolset `none` é desconhecido: não considerar esse comando um lançador experimental isolado. Não alterar configuração global ou reiniciar gateways por causa do aviso de atualização neste trabalho.

Demonstrações: cópias candidatas em few-shot-candidate/, com hashes de origem e destino. Corrigido teto de purchaseAmount; explicitada tradução com perda de campos no frete e incerteza de overflow na temperatura. Originais V4 continuam íntegros. Todos os três documentos passaram openapi-spec-validator 0.7.2; os três programas compilaram e executaram um caso nominal cada, com resultados conferidos: temperatura +032.00, frete 00003.00|Y e desconto 00010.00.

Primeira tentativa teve erro nos callers externos: identificador C no CALL. Corrigidos somente callers para RESULT-VALUE; falha preservada em demo-verification/results.json. Resultado posterior: demo-verification/results-final.json. Compilação dos exemplos usou -free explicitamente; não alegar compilação fixed-format padrão. Biblioteca do validador é provida por uv isolado, não pelo Python global.

Reproduzir: uv run --with openapi-spec-validator==0.7.2 python3 demo-verification/verify.py

Limites: um caso nominal não valida todos os ramos, overflow ou toda a fidelidade COBOL→OpenAPI. Demos ainda candidatas, não aprovadas como entradas E2. Falta qualificar isolamento/parâmetros do lançador, ampliar revisão dos exemplos e construir/revisar referência concreta de obrigações antes do congelamento P1. Nenhuma extração AWS, API, avaliação oficial ou gate SDD executado.

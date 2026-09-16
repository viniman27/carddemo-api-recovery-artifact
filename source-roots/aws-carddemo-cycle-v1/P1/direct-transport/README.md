# Transporte direto — verificação sintética

Autorização: continuidade da preparação após escolha gpt-6-astra/openai-codex por assinatura. Apenas instrução sintética; sem corpus AWS, dados privados, histórico, ferramentas ou memória. Usou resolvedor de credenciais já instalado do local runtime, sem copiar tokens para arquivos ou imprimir cabeçalhos de autenticação. Endpoint explicitamente verificado; nenhum fallback.

Resultado real: HTTP 200, modelo retornado gpt-6-astra, resposta ISOLATED_OK. Corpo integral da requisição em baseline-request.json; resposta em baseline-response.txt. Metadados retornados confirmam tools=[], previous_response_id=null e store=false. Isso verifica conteúdo controlado desta chamada, não privacidade/retencão interna do provedor, ausência de memorização do corpus pelo modelo ou um sandbox de sistema operacional.

max_output_tokens=64 e temperature=0 foram rejeitados com HTTP 400 Unsupported parameter. Omitir ambos no candidato, sem declarar controle desses valores. Resposta baseline informou temperature=1.0, top_p=0.98, reasoning medium; são observações desta chamada, não garantia de estabilidade. Seed/contexto e demais controles ainda não qualificados. Não converter contagem de tokens em custo zero: acesso por assinatura não expôs preço monetário por chamada.

Correção do coletor: results.json registrou inicialmente texto vazio e exit 1, pois response.completed tinha output vazio. A resposta real continha response.output_text.done com ISOLATED_OK. Criado parser, observado teste falhar antes de sua existência, e executados três testes verdes: stream real, ausência de completion e erro do provedor. Reprocessamento local sem novas chamadas gerou baseline-parsed.json. O recibo anterior foi preservado, não corrigido silenciosamente. probe.py agora usa esse parser; caminho completo com patch ainda não reexecutado via rede. Os testes não qualificam todo o runner de extração.

Reproduzir parser sem rede: python3 -m unittest discover -s . -p test_stream.py -v

Não executar probe.py automaticamente: ele faz novas chamadas de assinatura e substitui os recibos deste diretório. Preserve esta evidência antes de replay. O script serve a estes probes fixos; não é um runner de extração pronto, não recebe corpus e não fecha P1.

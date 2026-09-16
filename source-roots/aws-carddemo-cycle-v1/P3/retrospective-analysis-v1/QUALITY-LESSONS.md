# Regras reutilizáveis qualificadas nesta extensão

- Resolver condição de teste pelo ID da suíte congelada envolvente e contrato exato. T4 pode conservar origem de constituintes; nomes de casos não classificam autoria nem condição.
- Incluir na fatia inicial pelo menos um caso de cada braço e operação. Um único braço não qualifica o coletor quando as auditorias têm diretórios e canais de vinculação distintos.
- Manter separados pins do audit na árvore da aplicação e vínculo externo por path/invocation/cwd. A segunda cadeia não inventa um hash histórico ausente.
- Exigir correspondência com snapshot pré-COBOL antes de recuperar estado anterior de uma fixture; arquivos indexados no diretório de execução podem já estar alterados.
- Ler BDB com leitor qualificado em cópia, não com busca de strings. Registrar bytes/offsets/chaves e usar dumps lógicos para identidade de entrada/estado.
- Guardar todos os subtotais em sequência; dicionários por tipo perdem multiplicidade e podem omitir erros de grand total.
- Não impor espaços a bytes não atribuídos pelo fonte. Separar campos definidos, cauda de STRING, filler e timestamps; preservar brutos e declarar cada exclusão.
- Testar numeric multipleOf com os mesmos tipos usados pelo handler. Comparar float e Decimal localmente é diagnóstico, não autorização para corrigir API congelada nem substituir seus resultados.
- Publicar veredicto de reprodução do legado separado da expectativa financeira. Um fluxo source-derived pode reproduzir uma omissão financeira.
- Manter células sem execução no denominador. Separar aplicações, checks, ligações check–obrigação, partições e situações lógicas.
- Não interpretar exit None como conclusão. Recontar e verificar artefatos completos com um comando cujo resultado de execução seja conhecido.

Verificação: logs tdd-*; FINAL-VERIFICATION.json; fewshot-diagnosis.json; oracle-qualification.json. Limite: testes positivos e contraexemplos selecionados não substituem revisão independente ou completude de domínio. Nenhuma expansão de campanha necessária para aplicar estas lições.

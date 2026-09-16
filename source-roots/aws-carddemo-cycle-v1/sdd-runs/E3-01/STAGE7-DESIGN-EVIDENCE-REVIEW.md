# Revisão dirigida Stage 7 — evidência de desenho e limites empíricos

Data: 2026-09-13  
Run: `E3-01`  
Artefato revisado: `specs/adapter-behavior-carddemo/requirements.md`  
SHA-256 revisado: `0125e68e65e38c703e89b0c1b843358da91a5281e20860fb7f59316d3286ecf4`  
Veredito: **precisa de revisão estreita versionada antes de aceite sólido**.

## Escopo inspecionado

Não houve edição de originais, aprovações, corpus, COBOL/JCL/copybooks, Stage 8 ou implementação. A revisão separou obrigações documentais que o Stage 7 deve decidir de fatos que só execução posterior poderá demonstrar.

Tentativa de obter SHA Git do workspace: indisponível; o repositório local não expôs `HEAD` válido nesta árvore. A referência versionada usada nesta revisão é o conjunto de hashes de artefatos abaixo.

| Item | Caminho | SHA-256 | Linhas |
|---|---|---:|---:|
| Stage7 atual | `casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/specs/adapter-behavior-carddemo/requirements.md` | `0125e68e65e38c703e89b0c1b843358da91a5281e20860fb7f59316d3286ecf4` | 440 |
| Stage7 resultado | `casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/STAGE7-RESULT.md` | `1b3e032f815ef100b2f0528302cb4a4c2870ef25433ae97e42dbbbe3dc0a8976` | 26 |
| Stage7 counterexample review | `casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/STAGE7-COUNTEREXAMPLE-REVIEW.md` | `3634edc30e279a809f43a6f9e41ae6c915fc9310f136b180e9e5b22f3de3da54` | 74 |
| Stage6 r3 aprovado | `casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md` | `6cba102f8335843b46e75a77b1a71d4e56373a95d5ac63cf645491556c443b27` | 657 |
| Stage6 autorização | `casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/reviews/stage-6-r3-authorization.json` | `0c5228634cb0f3b3c779fafe2e7e9ae5109aebeb24b116268e73a9a00dd8213e` | 22 |
| Stage5 aprovado | `casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/specs/canonical-data-boundary-carddemo/requirements.md` | `208d04fe6f9cae665dfa4cb514de5d4ad9eaf0ebc169dfae0fd8a6ba209e66f3` | 537 |
| Stage5 autorização | `casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/reviews/stage-5-authorization.json` | `a2f73337b5ec123d62ab41e9c058a3065f1ccf133c48e5b81f54f9a2610bfe23` | 20 |
| Stage4 aprovado | `casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/specs/capability-semantics-carddemo/requirements.md` | `2f9d3ee52dd7788e206810e38c9173b19d21dfc44270cdd06d05e62dec95eb93` | 473 |
| Stage3 r2 aprovado | `casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/specs/legacy-evidence-carddemo-r2/requirements.md` | `4566786600b60e9377c1e369e67765098d06b0153ba973361d2065614a6c9b7b` | 425 |
| Template Stage7 | `pipeline-sdd-v3/pipeline/settings/templates/pipeline/adapter-behavior-spec.md` | `4a563f2bbb4db976c614cff722a90934041df3b76db0c3695386970871b47687` | 66 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/cbl/CBTRN02C.cbl` | `708f3cadc555acab63f11e2f3238f5372ac7180e6b01197bf960d96bf0d2e83f` | 731 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/cbl/CBACT04C.cbl` | `5084bb8b0c9a0f0199f737487ae1863f12e43cabbdc459a62b6b67bedc683cc4` | 652 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/cbl/CBTRN03C.cbl` | `8691e625502b7efcfd7ba4ae61797132e7b68f3fd5fedcdcc7dd6488f6871eef` | 649 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/jcl/POSTTRAN.jcl` | `ecff62c691e6ce101de08690e72ec065bc98bd845744ddf914899097d37c9191` | 45 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/jcl/INTCALC.jcl` | `61afa664a807558e58213641d9f3317ab3b354a350c4c1536a630897d194d275` | 44 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/jcl/TRANREPT.jcl` | `7d8fc0777e6b9fb1c62aee6b4b10a67d127057c84b92203c7152f230b3db9571` | 84 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/jcl/COMBTRAN.jcl` | `ab60da6cfdc8c4ec66c8b950540553bf35e91dc1e61a1dd4ada5bb888011c85c` | 52 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/jcl/TRANBKP.jcl` | `457cd00d14a1d9ac9983d92212541df3456e8428862b97cf10bab7249b9e6183` | 71 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/cpy/CVTRA05Y.cpy` | `d7bde0e78ff608497087b9909c889ed39e347269f964bda767b92b547fbb5fec` | 21 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/cpy/CVTRA06Y.cpy` | `c5c69f1b86c5a10156d3c5881d7cf387e6b925aae32825360f85bf4056a554a1` | 21 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/cpy/CVTRA07Y.cpy` | `72ba597b1a40e1e6cf908e15da9e6a818a0ab899ef1d27d15edeb074963102fa` | 73 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/cpy/CVACT01Y.cpy` | `81a08bad15af5664326a6f0af3650f570821c4857ffdec3a6a39f91f07dca728` | 20 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/cpy/CVACT03Y.cpy` | `ffc6079e09b28739e154bf6c1e1c36d408209faa91f6cf7008078dc596a1c370` | 11 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/cpy/CVTRA01Y.cpy` | `50637f13692c89b17a2fc60d249dc54e9eb3569d933afca3cdcf65b491a9d5ba` | 13 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/cpy/CVTRA02Y.cpy` | `7828fae489c59944b4310e223028a8d3a525ccf4ead113c062bcaff04b52bf9c` | 13 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/cpy/CVTRA03Y.cpy` | `fb15dbc4a6924cbddce0704932f9e61c067ac10004cd00839dff0ed7c7bb0667` | 10 |
| Corpus COBOL/JCL/copybook | `casos/aws-carddemo-preparation/research-corpus/app/cpy/CVTRA04Y.cpy` | `89803bc13a06347e1f3d8a599a5383b87235b203dce9f18a486bc233186479f8` | 12 |

## Conclusão executiva

O Stage 7 atual é forte como rascunho conservador: ele preserva Stage 6 r3, não inventa API de provisionamento, não transforma 109 em rejeição pública, distingue `available`/`unavailable`, conserva EOF e repetição como incertos e evita prova de runtime fabricada.

Mesmo assim, ele ainda não deve receber aceite sólido porque G-25..G-31 estão amplos demais. Algumas decisões são responsabilidade documental do próprio Stage 7 e não dependem de executar COBOL: quais registros de evidência uma invocação deve reter, como atribuir saída a uma chamada, como classificar captura vazia contra captura falha/truncada, como identificar recursos preparados sem expor nova API, e quais precondições mínimas tornam uma observação representável. Essas decisões podem ser propostas agora como protocolo interno/evidencial; a execução posterior apenas provará se foram satisfeitas.

## Separação: decisões de desenho agora vs prova empírica depois

| Tema | Decisão que Stage 7 deve fazer agora | Evidência empírica posterior |
|---|---|---|
| G-25 binding/setup | Definir responsabilidade por um **manifesto interno de invocação**: track, identificador de invocação, identidade de instância de recurso, origem/owner de setup, precondições de prontidão e escopo temporal; sem campo público novo. | Mostrar uma execução real que usou esses recursos e que eles estavam disponíveis no momento da chamada. |
| G-26 aquisição | Definir um **registro de observação por invocação e canal**: origem, canal, início/fim de captura, status de captura, cardinalidade, ordem, multiplicidade e associação com a chamada. | Demonstrar que o coletor capturou saídas reais do COBOL e que ordem/multiplicidade foram preservadas. |
| Saída stale/zero-length/falha/truncamento | Definir categorias documentais: `available items: []` somente com observação positiva de sequência vazia; captura zero bytes sem marcador de fechamento/completude não basta; falha/truncamento/stale não viram vazio. | Provar em execução qual categoria ocorreu em cada canal. |
| G-27 conversões | Definir política de representação fiel: nenhum trim/coerção silencioso; toda conversão de PIC/texto/decimal/data deve ter origem, largura, sinal, padding e perda explicitados; conflito bloqueia registro, não apaga conteúdo. | Validar bytes/campos reais contra o registro e detectar perdas/truncamento. |
| G-28 falhas | Definir que `known technical failure` exige evidência de fronteira: qual evento observável torna a falha conhecida; chamadas `CEE3ABD`, file status, display ou exit code são fontes candidatas, não fatos universais. | Executar casos que mostrem como o ambiente realmente termina/retorna/captura a falha. |
| G-29 estado | Definir que cada invocação registra se usa estado preparado, estado compartilhado ou estado não atestado; reinício de processo não é reset; idempotência não é assumida. | Demonstrar reset/isolamento/durabilidade quando forem necessários para testes. |
| G-30 relatório/EOF | Definir que EOF, ordem, datas e totalização só podem ser representados por ocorrências observadas; ausência de detalhe/total não vira total zero nem relatório completo vazio. | Executar relatório com entradas/datas reais e observar armazenamento pós-EOF e outputs. |
| G-31 gate | Definir critérios de aceite documental e evidencial com hashes exatos; não exigir execução COBOL para escolhas documentais. | Stage 8/execução posterior preenche obrigações empíricas restantes. |

## Contraexemplos concretos auditados

1. **109 não é rejeição preliminar.** `CBTRN02C.cbl:554-559` atribui 109 no `REWRITE` da conta, depois da seleção de posting; o fluxo que chama `2000-POST-TRANSACTION` já passou por `WS-VALIDATION-FAIL-REASON = 0` em `CBTRN02C.cbl:211-215`. Qualquer correção que exponha 109 como `PostingRejection.reason` mudaria Stage 6 C-5 e exigiria gate upstream.
2. **Tentativas ordenadas não são atomicidade.** `CBTRN02C.cbl:440-442` chama categoria, conta e transação em ordem; `CBTRN02C.cbl:562-577` pode falhar ao escrever transação depois de atualizações anteriores. Um Stage 7 aceito não pode prometer rollback, receipt durável ou estado inalterado.
3. **Progress zero não prova vazio de negócio.** `CBTRN02C.cbl:184-186` inicializa contadores e `227-230` os exibe; o Stage 6 permite progress available como observação, mas zero counts não provam ausência de efeitos, input exhaustion ou outputs duráveis.
4. **Interest EOF não autoriza flush final.** `CBACT04C.cbl:188-222` faz leitura dentro do laço e a atualização final está no `ELSE` externo; sob o raciocínio aprovado, EOF normal não implica update final. Inserir flush no adapter mudaria Stage 5/6.
5. **Missing disclosure não é taxa zero.** `CBACT04C.cbl:415-459` tenta fallback `DEFAULT` quando status 23; não há licença para substituir dependência ausente por taxa zero.
6. **Report date exit não é skip-and-continue.** `CBTRN03C.cbl:173-178` usa `NEXT SENTENCE`; a correção por conveniência para continuar varrendo registros alteraria a semântica aprovada.
7. **EOF/report finalization é condicional.** `CBTRN03C.cbl:197-203` soma `TRAN-AMT` e grava page/grand total no ramo EOF pós-comparação; `306-314` mostra account total separado e ausente nesse ramo. Não há base para total final de conta ou total reconciliado.
8. **Apresentação pode truncar.** `CVTRA07Y.cpy:20-30` usa descrições e valores de apresentação (`PIC X(15)`, `PIC X(29)`, `PIC -ZZZ,ZZZ,ZZZ.ZZ`), enquanto `CVTRA05Y.cpy:9-10` tem descrição/quantidade de origem diferentes. Stage 7 deve exigir registro de conversão/perda, não reconstruir valores completos.
9. **JCL nomeia recursos, não prova instância viva.** `POSTTRAN.jcl:23-42` e `TRANREPT.jcl:37-80` dão nomes e fluxo documental; isso não estabelece owner, disponibilidade, conteúdo, reset ou identidade compartilhada acessível ao adapter.
10. **`available: []` não nasce de arquivo ausente.** Stage 6 r3 linhas 246-257 e 280-299 autorizam sequência vazia observada, não transformar captura ausente, stale, truncada ou falha em `items: []`.

## Auditoria G-25..G-31

| Gap | Estado atual | Achado | Critério mínimo de fechamento documental |
|---|---|---|---|
| G-25 | Correto ao não inventar binding, mas amplo demais. | Falta dizer que evidência interna deve correlacionar operação, invocação, recursos, owner/preparação e janela de validade. | Acrescentar responsabilidade de `invocation/setup evidence record` por track, sem endpoint/campo público novo. |
| G-26 | Correto ao exigir aquisição real. | Falta protocolo para stale output, captura zero-length, captura truncada/falha e correlação por canal. | Definir categorias de captura e regra: só observação positiva vira `available`; stale/falha/truncamento fica unavailable ou known failure conforme evidência. |
| G-27 | Correto ao bloquear conversão inventada. | Falta aceitar que conversões fiéis podem ser propostas documentalmente: largura, sinal, padding, descrição truncada, display amount. | Exigir matriz campo-a-campo de origem física -> payload, com perdas explícitas e sem trim/coerção silenciosa. |
| G-28 | Correto ao não assumir CEE3ABD. | Falta critério de fronteira para chamar uma falha de conhecida, preservando precedence 500 sobre 200/503. | Registrar evento observável mínimo por track/canal; `CEE3ABD` é possível fonte, não semântica garantida. |
| G-29 | Correto ao negar reset/idempotência. | Falta separar estado de invocação, estado persistente e reset de ambiente; Stage 7 pode escolher como registrar isso sem provar. | Registro por invocação de resource instance, preparação, reuse/reset desconhecido, e efeitos não atestados. |
| G-30 | Correto ao manter limitações de reporting. | Falta amarrar observação de EOF/ordem/multiplicidade em `records` misto contra captura incompleta. | Critério de ordem/multiplicidade e “observed empty records” sem total zero, complete-range ou repair. |
| G-31 | Correto ao marcar unapproved. | Checkboxes finais ficam “unchecked” mesmo para itens que uma revisão documental poderia fechar. | Revisão r2 deve trocar checklist genérico por matriz: fechado documentalmente / bloqueado por execução / exige upstream. |

## Matriz de aceitação proposta

| Área | Aceitar versão atual? | Exige revisão Stage 7? | Exige execução posterior? | Exige upstream Stage 6? |
|---|---:|---:|---:|---:|
| Preservação Stage 6 r3: requests `{}`, envelopes, `available[]`, 200/500/503/400 | Parcial | Sim, para evidência interna | Sim, para runtime | Não, se não mudar superfície |
| Per-invocation attribution | Não | Sim | Sim | Não, se interno |
| Stale/zero-length/failed/truncated capture | Não | Sim | Sim | Não, se interno |
| Setup ownership/resource identity | Não | Sim | Sim | Não, se interno e sem API nova |
| Concrete observation protocol | Não | Sim | Sim | Não, se protocolo de evidência, não contrato público |
| Field conversion/loss policy | Parcial | Sim | Sim | Não, salvo se alterar schemas/required fields |
| Known failure detection | Parcial | Sim | Sim | Sim, se novos status/categorias/campos forem adicionados |
| Invocation state/reset/idempotency | Parcial | Sim | Sim | Sim, se prometer reset/idempotency público |
| EOF/order/multiplicity/`available[]` | Parcial | Sim, estreita | Sim | Sim, se redefinir `available` ou 200 |
| Human gate | Não | Sim, via autorização externa | Não para documental | Não |

## Mudanças que seriam upstream, não correção silenciosa de Stage 7

As seguintes “correções” mudariam o contrato aprovado Stage 6 r3 ou Stage 5 e exigiriam gate upstream: adicionar campos públicos de resource id, job id, status resource, retry/idempotency key, readiness endpoint, dataset selector ou provisioning; mudar `{}` requests para aceitar inputs; transformar 109 em rejeição pública; impor `minItems: 1`; fazer 503 carregar observações; tratar falha técnica conhecida como 200; adicionar reset/rollback/retry; reconstruir totais/descrições; inserir final flush de interest; reparar `NEXT SENTENCE` de reporting; converter ausência/captura falha em `available items: []`.

## Obrigações empíricas residuais

Estas não bloqueiam uma revisão documental Stage 7 se estiverem explicitamente classificadas como posteriores: demonstrar mecanismo de invocação, disponibilidade de recursos reais, captura fiel por canal, distinção zero-length/falha/truncamento/stale, comportamento real de `CEE3ABD`/file-status/exit/captura, conversões byte/campo, ordem/multiplicidade, conteúdo `available`, durabilidade/isolamento/reset quando usados em testes, EOF/reporting com datas reais e disponibilidade de outputs.

## Recomendação

Não aceitar o Stage 7 atual como final. Preparar **r2 estreito**, sem COBOL/Stage8/implementação, que preserve o contrato Stage 6 r3 e acrescente apenas critérios documentais de responsabilidade, precondição e registro de evidência. Depois dessa revisão e nova checagem dirigida, ele pode ser aceito como Stage 7 documental mesmo sem prova de execução.

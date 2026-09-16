# AWS CardDemo — preparação técnica local

## Estado vigente

Leia primeiro `STATUS-ATUAL.md`. A prioridade passou a ser aplicabilidade da pesquisa: o recorte executável demonstrado agora contém POSTTRAN, INTCALC e TRANREPT (2.226 linhas físicas COBOL/copybooks). Extratos e ampliação CICS ficaram bloqueados por dependências reais de z/OS. Os tamanhos maiores abaixo são histórico de seleção, não prontidão atual.

Comando consolidado: `python3 verify_research.py`. Entrada limpa: `research-corpus/`. Evidência: `evidence/research-acceptance.json`.

## Recorte maior selecionado

A seleção posterior está em `RECORTE-ESCOLHIDO.md`: cinco programas do ciclo batch financeiro e seus copybooks, 3.444 linhas físicas, contra 1.934 nos três legados anteriores somados. O manifesto reproduzível está em `evidence/large-scope-selection.json`. Essa seleção não amplia a evidência de execução descrita abaixo: por enquanto ela continua restrita a POSTTRAN.

## Situação
Primeira fatia executável preparada: POSTTRAN / CBTRN02C sobre GnuCOBOL 3.2.0, com backend de arquivos indexados BDB. O fonte original compila e executa sem alterações. Esta é preparação exploratória de infraestrutura, não uma execução formal da pipeline e não uma validação de continuidade funcional com z/OS.

A qualificação e os experimentos V4 não foram alterados.

## Proveniência e tamanho
- Repositório: https://github.com/aws-samples/aws-mainframe-modernization-carddemo
- Snapshot: `59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e`, já recuperado pelo repository-scout.
- Licença: Apache-2.0, preservada em corpus/LICENSE.
- Snapshot completo local: `<UPSTREAM_CHECKOUT>/aws-samples__aws-mainframe-modernization-carddemo/full-source`.
- O preparo não consultou novamente o HEAD nem modificou o snapshot.
- Recorte: CBTRN02C (731 linhas físicas) + cinco copybooks, total de 817 linhas físicas COBOL/copybooks; POSTTRAN.jcl e LICENSE completam o pacote. Comentários e linhas vazias estão incluídos. Isto NÃO representa um experimento sobre as dezenas de milhares de linhas do repositório inteiro.
- `prepare.py` verifica os bytes selecionados contra o archive original; `verify.py` confere que o snapshot integral e o corpus selecionado permanecem inalterados.

## Organização e controle de contaminação
- `corpus/`: somente o programa original, copybooks transitivos, JCL e licença. Candidato de entrada; seleção ainda sujeita à decisão do pesquisador.
- `support/`: infraestrutura local NOVA, excluída da extração de semântica.
- `build/`: binários gerados, nunca fonte de evidência semântica.
- `test_*.py`: fixtures sintéticas e caracterização de preparação; não fornecer como respostas esperadas a estratégias de extração.
- `runs/`: cada execução recebe diretório novo, sem apagar execuções antigas. Contém seeds, arquivos indexados, dumps físicos e execution.json.
- `evidence/`: manifesto de todos os arquivos upstream, closure, comandos, diagnósticos, testes, hashes e auditoria de larguras dos dados.
- APIs preexistentes, modernizações alternativas, README de solução, testes locais e este relatório não pertencem à entrada de extração. Dados de negócio upstream permanecem disponíveis no snapshot e exigem política explícita de inclusão no futuro escopo; não foram descartados.

## Reprodução local
No diretório deste README:

    python3 verify.py

Requisitos: Python 3 e `cobc` no PATH, GnuCOBOL com indexed BDB; ambiente efetivamente testado: macOS arm64. O script ainda depende do snapshot local acima; não é um pacote portátil independente. Nenhuma instalação, Docker, serviço, rede ou upload é necessário.

Etapas: verificar proveniência, compilar original e suporte, compilar loaders/dumpers, executar testes e conferir integridade. `evidence/verification.json` registra a última verificação; cada execução de negócio persiste separadamente em `runs/`.

Flags do original: `cobc -x -std=ibm -fsign=ascii`, com include dos copybooks. O dialeto IBM não implica runtime IBM. A cadeia C efetivamente usada é registrada por `cobc -info` em evidence/build.json; este preflight não instrumenta cobertura.

## Mapeamento operacional de POSTTRAN
JCL original: corpus/app/jcl/POSTTRAN.jcl, STEP15, `PGM=CBTRN02C`.
FDs: corpus/app/cbl/CBTRN02C.cbl:29–97.

| DD | Organização COBOL | Bytes/registro | Chave (offset zero) | Uso local |
|---|---|---:|---|---|
| DALYTRAN | sequential | 350 | nenhuma | lote fixo de entrada |
| TRANFILE | indexed/random | 350 | 0:16, ID | transações persistidas |
| XREFFILE | indexed/random | 50 | 0:16, cartão | consulta cartão-conta |
| DALYREJS | sequential | 430 | nenhuma | rejeições + trailer de 80 bytes |
| ACCTFILE | indexed/random | 300 | 0:11, conta | leitura/atualização |
| TCATBALF | indexed/random | 50 | 0:17, conta+tipo+categoria | criação/atualização |

Cada DD é mapeado por `DD_<nome>` para arquivo dentro do diretório exclusivo da execução. stdout/stderr representam a observação local de SYSOUT/SYSPRINT. O loader/dumper externo apenas copia registros byte a byte entre sequential e indexed usando GnuCOBOL; não valida cartão, limite, expiração ou saldo.

Não foi implementado um interpretador JCL. STEPLIB é substituído pela invocação do binário local; catálogo/GDG de DALYREJS, DISP, alocação de espaço, locking compartilhado e códigos de job z/OS não são reproduzidos. A organização BDB não demonstra equivalência com VSAM. A hipótese local está limitada ao acesso/estado exercitado pelos testes.

## Suporte CEE3ABD
A primeira execução com arquivo ausente alcançou o abend original e falhou com `module 'CEE3ABD' not found`. O shim externo `support/CEE3ABD.cbl` registra ABCODE/TIMING e termina com status local 12, sem retornar ao fluxo normal. O teste verifica código 999 recebido e ausência da mensagem de término normal.

Isso NÃO reproduz dumps, condition handling ou o status exato do Language Environment/operating system IBM. É uma convenção local explícita para tornar a terminação fatal observável. Não deve ser tratada como prova de fidelidade de abend. Nenhuma regra do POSTTRAN foi substituída.

## Caracterização exercitada
A suíte inicial tinha 10 testes; a suíte atual inclui mais três testes de segurança (13 no total). O conjunto inicial: roundtrip indexed, entrada ausente/abend e oito testes de POSTTRAN (nominal, cartão inválido, conta ausente, limite, expiração, lote vazio, duplicata e reset).

- Nominal: transação sintética de 25,00; rc 0; uma transação persistida, saldo e crédito do ciclo atualizados, saldo da categoria criado, nenhuma rejeição.
- Cartão inválido: rc 4, trailer 0100, registro original preservado na rejeição, sem atualização dos saldos.
- Conta ausente: rc 4, trailer 0101.
- Limite excedido: rc 4, trailer 0102, conta inalterada.
- Conta expirada: rc 4, trailer 0103, conta inalterada.
- Lote vazio: rc 0, sem postagem.
- Arquivo de entrada ausente: status de arquivo 35 observado e abend local rc 12.
- Reset: seeds reinseridos em novos bancos indexados; comparação dos dumps lógicos após duas execuções. Só o timestamp de processamento em TRANFILE, bytes 304:330, é excluído da comparação; bytes brutos e seus hashes são preservados. Não há promessa de identidade binária dos bancos BDB nem de timestamps iguais.

### Achado a preservar: duplicata não é atômica
Ao enviar duas vezes a mesma transação de 25,00 no lote, o original atualiza conta e categoria antes de tentar gravar a segunda transação. A gravação duplicada abenda, mas os saldos já chegam a 50,00 e há apenas uma transação persistida. Observado no runtime local; não foi corrigido nem compensado pelo harness.

Evidência: `test_duplicate_preserves_observed_partial_updates`, `runs/duplicate-*/execution.json` e dumps `.after`; ordem original em CBTRN02C:440–442 e tratamento da falha em 562–577. Este comportamento deve virar achado rastreável se o recorte entrar na pipeline. Não presumir atomicidade, idempotência ou rollback.

## Dados upstream: bloqueio de importação automática
A auditoria local dos arquivos ASCII encontrou acctdata=300, dailytran=350 e tcatbal=50 bytes por registro. Cardxref tem 36 bytes por registro, mas FD/copybook exige 50 (14 bytes finais de filler).

Não houve padding silencioso, importação dos datasets upstream ou conversão EBCDIC. Os testes usam fixtures sintéticas novas com larguras explícitas; não simulam os datasets oficiais. A adoção dos dados upstream requer decisão documentada de transformação e verificação de assinaturas numéricas, fillers, encoding e chaves. Veja evidence/upstream-data-widths.json.

## Limites e próximo checkpoint
A preparação demonstrou build, acesso indexado, postagem/rejeições, abend controlado, efeitos persistentes e reset local. Não demonstrou cobertura, casos monetários negativos/arredondamento/overflow, concorrência, equivalência VSAM/LE, execução do sistema online CICS ou validação independente de negócio.

Antes da entrada formal: decidir se POSTTRAN é apenas ensaio de infraestrutura ou recorte experimental; avaliar ampliação coesa para um escopo realmente maior; fixar política de dados, suporte local e observação de timestamps; provar instrumentação/flush gcov em preflight separado. Não congelar denominadores ou iniciar células oficiais nesta preparação.

Pipeline Scope Spec e demais specs, contratos/API, adaptação formal e backend moderno NÃO foram gerados. A próxima autorização pertence a Researcher. A qualificação permanece encerrada.

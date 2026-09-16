# Prontidão pós-pipeline — AWS CardDemo E3-01

Data local da descoberta: 2026-09-14. Escopo desta nota: descoberta read-only para decidir o próximo gate operacional após aprovação documental do Stage 8. Nenhum COBOL, modelo, API, build ou teste oficial foi executado nesta etapa.

## 1. Raízes verificadas

- Raiz do workspace: `<REDACTED_LOCAL_PATH>`.
- Ciclo: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1`.
- RUN: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01`.
- Corpus autorizado pela preparação: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-preparation/research-corpus`.
- Manifesto do pacote de pesquisa: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-preparation/evidence/research-package.json`.

## 2. Comandos read-only executados nesta descoberta

```text
cd "<REDACTED_LOCAL_PATH>" && git status --short --branch
```

Resultado observado: repositório sem commits em `master`, com muitos arquivos `??` preexistentes; não há base limpa para inferir autoria de mudanças fora dos dois arquivos desta etapa.

```text
pwd; command -v python3; python3 --version; command -v uv || true; command -v cobc || true; command -v gcov-11 || true; command -v gcov || true; command -v node || true; node --version 2>/dev/null || true; command -v npm || true; npm --version 2>/dev/null || true; command -v jq || true
```

Resultado observado:

```text
<REDACTED_LOCAL_PATH>
/usr/bin/python3
Python 3.9.6
<REDACTED_LOCAL_PATH>/.local/bin/uv
/opt/homebrew/bin/cobc
/opt/homebrew/bin/gcov-11
/usr/bin/gcov
/usr/local/bin/node
v18.18.0
/usr/local/bin/npm
9.8.1
/usr/bin/jq
```

Ferramentas existem localmente, mas esta descoberta não as usou para compilar, instrumentar ou executar COBOL.

## 3. Estado documental aprovado

Arquivos de autorização lidos:

- `sdd-runs/E3-01/reviews/stage-6-r3-authorization.json`: decisão `approve`, Stage 6 r3, artefato `specs/api-contract-carddemo-r3/requirements.md`, SHA-256 `6cba102f8335843b46e75a77b1a71d4e56373a95d5ac63cf645491556c443b27`; escopo autoriza contrato documental e Stage 7, sem Stage 8, implementação API ou execução COBOL.
- `sdd-runs/E3-01/reviews/stage-7-r2-authorization.json`: decisão `approve`, Stage 7 r2, artefato `specs/adapter-behavior-carddemo-r2/requirements.md`, SHA-256 `b53c471116dfa0c3831fc810964bddca3eb1fa0d3b8e7d459181ba71e54b3d8f`; escopo autoriza Stage 8 documental, sem implementação, execução COBOL ou teste experimental.
- `sdd-runs/E3-01/reviews/stage-8-authorization.json`: decisão `approve`, Stage 8, artefato `specs/semantic-validation-carddemo/requirements.md`, SHA-256 `de4f1781459f3bbf8c472add1166826dc9dbb6229a19b67e7ecdb85a56b2d4b6`; escopo fecha a cadeia documental SDD e permite prosseguir para operacionalização pós-pipeline, sem certificar testes executados ou validade runtime.

Conclusão: os oito estágios documentais da trilha SDD estão aceitos para a cadeia E3-01, mas isto não materializa OpenAPI, não implementa adaptador e não executa cenários V-1..V-35.

## 4. Separação necessária de trabalho

### 4.1 Materialização mecânica OpenAPI

Autorizável como próxima unidade técnica se mantiver fidelidade ao Stage 6 r3 sem revisão semântica:

- transformar `specs/api-contract-carddemo-r3/requirements.md` em um artefato OpenAPI 3.1 verificável;
- preservar as três rotas propostas: `POST /posting`, `POST /interest`, `POST /reporting`;
- preservar requests vazios fechados, envelopes, `availability`, `items: []` positivo, `unavailable` sem `items`, `400/500/503`, `not_attested`, `unknown`, ordem/multiplicidade e exclusões;
- registrar rastreabilidade clause/section para cada schema/operação;
- validar sintaxe/estrutura OpenAPI com ferramenta definida, sem alegar fidelidade ao COBOL por validação de schema.

Isto é mecânico quando não muda request, status, campo, enum, semântica de disponibilidade, erro ou obrigação.

### 4.2 Revisões semânticas

Requerem decisão consequencial antes de editar contrato/spec:

- adicionar selector de dataset, upload, readiness, reset, idempotency key, polling, retry, snapshot, receipt ou operação combinada;
- mudar `items: []` observado para erro, ou tratar indisponível como vazio;
- expor reason 109, file status, branch/telemetria interna, sufixo, readiness ou detalhes de falha;
- preencher lacunas de encoding, arredondamento, calendário, EOF, persistência, rollback, isolamento ou durabilidade;
- reconstruir descrição/totais/reporting em vez de capturar conteúdo observado;
- restringir o escopo a postagem apenas. O escopo aprovado exige as três trilhas: posting, interest e reporting.

### 4.3 Binding técnico e fixtures

Requer gate separado porque passa de contrato documental para evidência de execução:

- escolher arquitetura de adaptador/harness e boundary de processo;
- definir como cada chamada associa INV/RES/CAP/CONV/FAIL/STATE/RESP;
- definir fixtures sintéticas permitidas, política de dados upstream, resets, diretórios por invocação e captura de outputs;
- mapear o contrato OpenAPI para os executáveis originais `CBTRN02C`, `CBACT04C`, `CBTRN03C` sem editar fontes COBOL/copybooks;
- decidir como demonstrar alcance do COBOL por chamada/efeito/log, pois sucesso HTTP isolado não basta;
- congelar limites antes de qualquer célula oficial T1/T2/T3/T4.

## 5. Suporte local existente, sem reexecução nesta etapa

Documentos/código lidos:

- `casos/aws-carddemo-preparation/STATUS-ATUAL.md`: preparação declara recorte executável POSTTRAN + INTCALC + TRANREPT, programas `CBTRN02C`, `CBACT04C`, `CBTRN03C`, 2.226 linhas físicas COBOL/copybooks, sem alterar pesquisa principal/V4 e sem executar gates formais.
- `casos/aws-carddemo-preparation/README.md`: `python3 verify_research.py` é comando consolidado de aceitação local; suporte, runs, testes e outputs esperados são quarentena e não entram nos prompts de extração.
- `casos/aws-carddemo-preparation/QUALITY.md`: anti-metas incluem não alterar fontes, não fabricar equivalência mainframe, não criar contratos/API e não avançar gates por preparo mecânico.
- `casos/aws-carddemo-preparation/verify_research.py`: encadeia `verify.py`, `expanded-batch/verify_batch.py --coverage` e `package_research.py`; não foi executado nesta descoberta.
- `casos/aws-carddemo-preparation/prepare.py`: prepara POSTTRAN e compila, mas é código de preparação e não deve ser confundido com operacionalização oficial do ciclo E3-01.
- `casos/aws-carddemo-preparation/evidence/research-package.json`: registra 19 arquivos no pacote, programas `CBTRN02C`, `CBACT04C`, `CBTRN03C`, escopo “Posting, interest transaction generation and transaction reporting”, `scope_10k_ready: false`, `physical_code_copybook_lines: 2226`, exclusões `support`, `runs`, `tests`, `reports`, `expected outputs`, `build` e `expanded-batch/corpus`.
- `casos/aws-carddemo-cycle-v1/sdd-command-adapter/README.md`: bridge local já cobriu geração documental Stage 1..8; não materializa resposta automaticamente como API nem aprova gates; testes históricos do bridge existem, mas não foram rodados nesta etapa.
- `casos/aws-carddemo-cycle-v1/sdd-command-adapter/stage8_adapter.py`: confirma que Stage 8 é somente cenário/critério documental e veta implementação, execução experimental, COBOL/runtime validation, E1/E2 e Stage 9.

## 6. Decisões pendentes concretas

Antes de implementação/binding:

1. Onde o OpenAPI mecânico viverá no RUN e qual nome/versionamento será autorizado, sem sobrescrever specs aprovadas.
2. Qual validador OpenAPI 3.1 será a autoridade mecânica e se pode ser instalado/usado localmente sem rede.
3. Se o primeiro gate pós-pipeline permite apenas materialização OpenAPI ou também esqueleto de adaptador sem execução.
4. Arquitetura de binding: wrapper CLI/processo por chamada, servidor local, ou harness offline; isso afeta isolamento, CAP/FAIL/STATE e repetição.
5. Política de fixtures: quais dados sintéticos podem ser usados para smoke técnico e quais ficam proibidos como oráculo T1/T2/T3/T4.
6. Política de dados upstream originais: layouts/JCL estão no corpus; datasets upstream exigem decisão de transformação/encoding/assinatura/fillers/chaves.
7. Reset por chamada versus sequência stateful; diretórios novos, bancos indexados, preservação de bytes brutos e hashes.
8. Captura de outputs por trilha: transações/rejeições/progresso da postagem, transações de juros, relatório misto, stderr/stdout/diagnósticos e falhas conhecidas.
9. Critério mínimo de “alcance do COBOL” por operação antes de qualquer alegação operacional.
10. Tratamento de lacunas G-25..G-35 sem transformá-las em campos públicos ou garantias.
11. Separação entre smoke técnico de desenvolvimento e células oficiais T1/T2/T3/T4.
12. Regras de não comparação E1/E2 até o gate de avaliação apropriado.

## 7. Fatia vertical mínima recomendada

Fatia mínima representativa, preservando full3track e sem reduzir a postagem:

1. Materializar OpenAPI 3.1 mecânico do Stage 6 r3 para as três operações, com validação estrutural e mapa de rastreabilidade C-1..C-14.
2. Criar um contrato de binding técnico documental para uma chamada smoke por trilha, sem executar ainda: `posting`, `interest`, `reporting`.
3. Para cada trilha, definir explicitamente INV/RES/CAP/CONV/FAIL/STATE/RESP mínimos e quais evidências seriam aceitas ou rejeitadas.
4. Usar fixtures sintéticas apenas como recursos técnicos de smoke, marcadas como quarentena e não como oráculo de negócio oficial.
5. Só depois de aceite desse gate, implementar uma fachada técnica mínima que invoque os COBOL originais e capture evidência, ainda separada das células oficiais.

Critério de slice: uma operação por trilha deve atravessar a mesma cadeia contratual e de evidência, mesmo que o conteúdo observado seja mínimo. Não é aceitável provar apenas `POST /posting` e extrapolar para juros/relatório.

## 8. Riscos e áreas protegidas

Protegido/não autorizado por esta descoberta:

- editar specs aprovadas, protocolo, quarentena, fontes COBOL/copybooks, código de API/adaptador ou V4/qualificação;
- rodar `verify_research.py`, testes do bridge, COBOL, builds, modelos, rede, coletores ou suítes oficiais;
- tratar o preparo AWS como Fase 2;
- declarar equivalência z/OS/VSAM/LE, continuidade funcional, aderência semântica ou validade runtime;
- usar fixtures/resultados esperados da preparação como oráculo independente ou input de extração;
- comparar E1/E2 agora;
- converter lacunas empíricas em defaults convenientes.

Riscos principais:

- OpenAPI válido pode virar falsa alegação de fidelidade ao COBOL;
- wrapper pode implementar regra de negócio fora do legado;
- suporte local pode mascarar diferenças VSAM/LE/JCL;
- captura zero-byte pode ser confundida com saída vazia positiva;
- reset/isolation pode ser alegado por diretórios novos sem prova de todos os recursos;
- full3track pode ser perdido se a fatia inicial focar só postagem.

## 9. Gate imediato proposto

**Gate recomendado: `P2a — materialização mecânica do contrato + plano de binding, sem execução`.**

Escopo autorizado sugerido para o próximo passo:

- criar somente artefatos novos sob o ciclo/RUN, sem alterar specs aprovadas;
- gerar OpenAPI 3.1 mecânico para Stage 6 r3;
- validar sintaxe/estrutura do OpenAPI;
- produzir matriz de rastreabilidade do OpenAPI para C-1..C-14, D-9..D-17 e três trilhas;
- escrever plano de binding por trilha com INV/RES/CAP/CONV/FAIL/STATE/RESP, fixtures permitidas, reset/captura e limites;
- não compilar/rodar COBOL, não implementar servidor/fachada executável e não iniciar T1/T2/T3/T4 ainda.

Requer escolha humana se o próximo passo deve incluir execução smoke real. Sem essa escolha, a próxima etapa segura é apenas materializar contrato e congelar o desenho de binding.

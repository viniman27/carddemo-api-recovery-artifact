# Recuperação parental e lançamento complementar

A execução auxiliar expirou; seus arquivos foram recuperados sem declarar conclusão. Três testes locais de matrix-v2 passaram na execução parental. A qualificação smoke-sdd histórica tinha duas respostas 500/schema inválido e nenhuma auditoria: os registros de fixtures eram relativos a `latest/`, mas os servidores tinham outro cwd.

Não foi repetido esse run nem sobrescrito seu plano. Um novo plano em `parent-plan-absolute-v1/` foi materializado usando diretório absoluto e configuração v3 explicitamente atribuída ao módulo (`m.CONFIG=.../campaign-configuration-v3/campaign-config-v3.json`). A constante padrão do arquivo ainda aponta v2; para reproduzir o lançamento deve-se preservar essa atribuição registrada no comando parental, e não usar o comando padrão do manifesto sem ajuste.

Qualificação parental separada `parent-smoke-absolute-v1/`: duas chamadas SDD com {} e fixtures distintas; 2 concluídas, 2 estruturais OK, 2 medições admissíveis. Evidência efetiva: valid-new-tcatbal TRANFILE.after=350 bytes / DALYREJS=0; reject-card-missing TRANFILE.after=0 / DALYREJS=430. Isso comprova distinção real dos estímulos, não toda a semântica das obrigações.

Em seguida foi iniciada a execução parental complementar de 84 aplicações em `parent-full84-v1/`, processo rastreado proc_0c6cb7346729 (PID inicial 46672), log parent-full84-v1.log. Classificação: complemento source-guided essencial, não novos T1/LLM ou T2/fuzzing, nem substituição da campanha histórica. A validação de status no runner não é o checker semântico; os artefatos finais exigem agregação e verificação de valores separadas. Não afirmar cobertura ideal antes desse fechamento.

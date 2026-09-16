# Materialização real e revisão anterior ao freeze oficial

Leitura parental: aws-suite-materialization-v1/final-20260915T155901 contém T2=5868 casos e T3=401, sem IDs duplicados dentro de cada suíte agregada e sem base64 inválido. PARENT-READBACK.json preserva hashes e contagens computadas. READBACK-UNDERFILL-AMENDMENT.json limita o PASS original: orçamento T2 SDD não preenchido, sem completar artificialmente.

T1-import-qualification-v1 não é aceito como política de seleção: exclui requests schema-invalid sem distinguir negativos intencionais. Seus43 aceitos/45excluídos não são resultados experimentais. Nova importação corrige a política preservando88 fontes originais.

aws-campaign-runner-v1 não é aceito para campanha: interrompe comparação por violação de schema/expectativa, avalia parcialmente recibos depois de replay de suíte inteira, usa alvo P2b sem demonstrar dispatch por contrato e resume reexporia tentativas falhas. Nova versão em correção por TDD, nenhuma execução oficial realizada.

T3 materializado não carrega contractId/operationId/track como metadados top-level em parameters. Antes do freeze de campanha, anexar metadados exclusivamente pela origem da suíte por contrato e lookup exato method/path no registry, preservando bytes request e obrigações. O campo status inconclusive_until_checker_bound é ausência de expectativa independente conclusiva; não converter em PASS.

A autorização geral do usuário permanece válida. Correções de integração não autorizam mudar contratos, regenerar T1, ampliar budgets após resultados ou fabricar oráculos. Nenhuma nova aprovação humana individual é registrada.

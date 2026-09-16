# V2: não aceita como fechamento operacional

Revisão parental do código, sem executar campanha.

T2: src/t2_offline_bridge.py:173–194 cria schemas syntheticCase em vez de consumir contratos originais. Paths iguais podem sobrescrever operações de contratos distintos. Linhas 197–211 convertem body ausente para {} e decodificam JSON, sem preservar bytes originais. Linhas 254–262 ignoram query e substituem headers. Os 42 requests sintéticos não qualificam geração AWS. Preservar como evidência sintética/rejeitada, não promover.

T3: sdd_external_selection.py:482–509 recebe Suite original e filtra apenas a lista de projeção do relatório, não suite.cases. O número 65 descreve relatório filtrado, não prova que o gerador real excluiu transições. A correção conceitual das duas superabrangências é válida como anotação candidata; fechamento operacional depende de teste direto da Suite real.

Correções em novas versões requeridas: T2 ler schema original isolado por contrato e preservar request preparado; T3 aplicar seleção na Suite retornada e registrar exclusões. Sem adicionar fixtures, expectativas ou modificar contratos. Nenhuma aprovação humana ou autorização de campanha é registrada.

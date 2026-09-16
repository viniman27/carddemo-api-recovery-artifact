# Conferência da integração — correções necessárias

O relatório FIXTURE-INTEGRATION-TECHNICAL.md foi conferido contra código e evidências. Suas alegações não encerram a integração autorizada.

## Lacunas encontradas

1. O registro local selecionava somente `builtin_technical_smoke`. O descriptor tinha hash, mas os dados executados continuavam fixos. Isso prova seleção de metadados, não seleção externa dos recursos COBOL.
2. `STATE.before` era capturado antes da materialização; árvore vazia diferente da árvore final era chamada `reset_effective`. Isso não demonstra restauração de recursos iniciais entre aplicações. Exigir snapshot após materialização e antes COBOL, comparação com conteúdo declarado e repetição de preparação após mutar workspace anterior.
3. O validador passou a usar fallback `internal-openapi-subset` ao faltar jsonschema no Python ativo. Não é substituto aceitável para a validação estrutural já estabelecida. O interpreter `../P2a/.venv/bin/python` existente foi conferido: jsonschema 4.26.0 e PyYAML 6.0.3 disponíveis. Nenhuma instalação necessária.

## Correção do validador já exercitada

Removido fallback. `validate_p2b.py` exige a biblioteca real. Novo teste `P2b/tests/test_schema_dependency.py` executa o módulo com importação de jsonschema deliberadamente indisponível em subprocesso e exige falha, nunca PASS substituto.

Comando real em P2b:

    ../P2a/.venv/bin/python -m unittest discover -s tests -p test_schema_dependency.py -v

RED: 1 teste, falhou porque retorno 0 ativava substituto.
GREEN: 1 teste, OK depois da remoção.

Artefatos rejeitados preservados em:

    P2b/evidence-archive/schema-subset-rejected-20260914T210006Z/

O PASS histórico do subset não será usado como validação final. A validação real deverá ser aplicada às respostas da integração corrigida, com nova evidência arquivando a anterior antes de substituir manifest.

## Fechamento

As lacunas de dados/reset seguem para correção por critérios concretos: bytes externos efetivamente consumidos, adulteração rejeitada, recursos iniciais recompostos, isolamento e smoke das três trilhas. O fechamento deve constar em FIXTURE-INTEGRATION-V2.md e evidências finais verificadas. Não são novos estágios SDD nem autorização de campanhas.

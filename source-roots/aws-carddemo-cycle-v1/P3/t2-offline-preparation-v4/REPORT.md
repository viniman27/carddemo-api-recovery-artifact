# Correção parental T2 v4 — candidata

Preserva v3. O teste real com Case.as_transport_kwargs mostrou que query fica em params, JSON ainda não é bytes e Content-Length ainda não existe. V3 perdia query e reserializava JSON de maneira diferente do transporte.

RED: test_real_schemathesis_kwargs_match_prepared_request falhou com /x != /x?q=a+b.
GREEN: cinco testes passaram (0.661s), usando P3/.venv-fuzz-preflight/bin/python, sem envio. Agora Request.prepare materializa transporte localmente; compara path/query, body e headers ao request preparado. Headers duplicados já preparados continuam lista ordenada, e combinações não qualificadas são rejeitadas.

A ponte genérica usa contrato original pinado por contractId. Exercício somente sintético; nenhuma suíte AWS oficial foi gerada ou congelada. Geração oficial permanece gate-closed. Este pacote corrige transporte; não é o fechamento integral de P3. Pins T3 e configuração consolidada ainda dependem de integração parental. A associação de resource_package_id à fixture oficial precisa ser fixada antes do freeze; o default t2-offline-preparation-v4 é somente preparatório. O relatório de geração não deve ser interpretado como medição de diversidade nem oráculo de negócio.

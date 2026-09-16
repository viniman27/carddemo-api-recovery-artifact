# Aceitação pré-campanha — pacote v1

Estado: **bloqueado para execução oficial**. Este pacote prepara artefatos concretos, mas não libera nem executa T1/T2/T3/T4.

O que está pronto:
- Manifesto canônico com pins de 7 contratos e 21 operações, referência/matriz/fixtures candidatas, harness/generators/parser/toolversions, orçamentos, seeds, ordem e política de isolamento/erro.
- Sete payloads outbound T1 reais em `t1-outbound-payloads/`, cada um montado somente do contrato correspondente, instrução comum e metadados. Todos têm `sendStatus=not_sent`; parâmetros de provedor permanecem `pending_not_verified`.
- Readiness matrix separa preparado de faltas materiais para T1/T2/T3/T4.
- Verificador local em `tools/verify_manifest.py` detecta missing, tamper, dependência stale e rejeita label como autorização.

Faltas materiais:
- T1 ainda precisa de pacote/provedor externo autorizado, parâmetros suportados verificados, envio real e respostas preservadas. Não há aprovação fabricada.
- T2 ainda não tem suítes oficiais geradas para todos os 7 contratos/21 operações, só qualificação/preflight técnico.
- T3 está bloqueado: falta modelo MBT independente e autorizado, mapeamentos executáveis contrato→HTTP e runner oficial integrado. Próximo código mínimo: congelar referência independente, implementar mapeador por operação, criar freeze/import T3 rejeitando transições abstratas sem mapping, integrar ao harness sem executar campanha.
- T4 depende de T1/T2/T3 congelados; preflight de união não é T4 oficial.

Autoridade:
- Autorização real registrada: “Deixo ao seu criterio, se ja considerar que estamos prontos, vamos aos testes, se nao faca as revisoes necessarias.”
- `signedAuthorization`: `not_supplied`. Autorização operacional não vira assinatura humana nem autorização de campanha.

Decisão eventualmente necessária: escolher/autorizar o pacote externo/provedor de T1 e seus parâmetros suportados. Isto não é pedido para aprovar placeholders; sem esse pacote, T1 permanece preparado-localmente e não enviado.

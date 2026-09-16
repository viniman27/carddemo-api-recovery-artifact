# Fixture materialization v2 — exposição e proveniência

Status: `candidate_needs_review`. Este pacote é técnico local para revisão; não oficializa casos, campanhas ou oráculos.

## Limite metodológico

- Integração técnica: usa o padrão de transporte GnuCOBOL/BDB (LOAD/DUMP por programa COBOL local) e o probe nativo de DISPLAY para qualificar bytes.
- Não é referência independente de expectativas: nenhum output esperado foi criado, nenhum resultado de negócio foi inferido, e nenhum COBOL CardDemo de negócio foi executado.
- Leitura de suporte quebra isolamento estrito de autoria; por isso a proveniência declara integração técnica, não autoria independente de expectativas.

## Fontes usadas

- Dados sintéticos candidatos v1: `P3/fixture-candidates-v1/`.
- Probe runtime compilado: `P3/native-display-probe-v1/`.
- Técnica de suporte permitida: padrão local GnuCOBOL de materialização/leitura; sem copiar datasets, runs ou oráculos anteriores.

## Verificações incluídas

- `byte-layout-review.json`: layouts fonte, campos `S9 DISPLAY`, e comparação com probe runtime (`-123` termina em byte `0x73`).
- `verification.json`: leitura de volta via GnuCOBOL dos indexed files e comparação byte-a-byte com imagens lógicas JSONL.
- `manifest.json`: inventário com bytes/sha256 de todos os recursos físicos, incluindo `posting/XREFFILE.1` e `interest/XREFFILE.1`.
- reset verificado por mutação de workspace e recópia fresca com comparação integral de inventário.

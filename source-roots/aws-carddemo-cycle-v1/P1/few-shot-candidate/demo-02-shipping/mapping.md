# Mapeamento observável

- Peso/zona → requisição; amount → corpo da resposta de sucesso; status Y/N → escolha de HTTP 200/422. O corpo da falha não expõe amount=0 nem o flag N: perda de informação deliberada deste exemplo, não preservação literal de todos os campos.
- Zonas diferentes de A/B permanecem representáveis no request para preservar o ramo `WHEN OTHER` observado.
- Ambiguidade: COBOL não define status HTTP; 422 é mapeamento de transporte explicitamente escolhido, não uma alegação sobre o legado.
- Proveniência: sintético, não derivado de casos avaliados, caso institucional ou E3.

# Complementary validation v1 — AWS CardDemo

Status: desenho e catálogo fonte-ancorado, sem execução de campanha, sem chamadas externas e sem edição de artefatos congelados.

Autorização operacional preservada: “entao havera complemento ne? pode seguir?”. Revisão humana formal de expected outputs: desconhecida; não foi retropreenchida.

## Resultado deste pacote

- Define papéis distintos de T1–T4 para o complemento.
- Mapeia 25 obrigações fonte-ancoradas contra 7 contratos e 21 operações (`25 × 21 = 525` células).
- Separa critérios prospectivos de validação semântica da campanha oficial já observada.
- Mantém denominadores explícitos: antes de nova execução, `achieved=0`, `failed=0`, `unobservable=525` no catálogo de células obrigação×operação.
- Preserva a leitura correta da campanha oficial: 12.700 casos estruturais executados; 394 T3 inconclusivos; 1.070 medições gcov admissíveis não equivalem a sucesso semântico.

## Arquivos

- `DESENHO.md` — desenho PT-BR e gates.
- `scenario-catalog.json` — catálogo legível por máquina.
- `obligation-operation-mapping.csv` — visão tabular das 525 células.
- `validate_catalog.py` — validação mecânica de referências, contagens e hashes.
- `VALIDATION-REPORT.md` — resultado da validação local.

## Próximo gate

Antes de implementar qualquer bateria complementar executável: aprovar autoridade de oráculo por obrigação, congelar fixtures/checkers e escolher se haverá nova geração T1 externa. Este v1 não autoriza campanha.

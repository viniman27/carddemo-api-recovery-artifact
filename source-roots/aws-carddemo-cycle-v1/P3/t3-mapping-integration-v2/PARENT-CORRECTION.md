# Correção do coordenador

A revisão direta encontrou 10 células elegíveis apesar de applicabilityDimensions.generative_admissible=false. O novo teste test_parent_dimension_gate.py observou RED com essas dez células antes do patch.

O gate agora exige generative_admissible explicitamente true; ausência também bloqueia. As dimensões efetivas são preservadas em sourcePlan. A suíte completa passou: 6 testes. Inventário regenerado: 44 células elegíveis, zero negações upstream reabertas. Os 54 anteriores ficam invalidados; arquivos anteriores preservados em evidence-before-parent-dimension-gate/.

Receita elegível não é caso exercitado nem prova de cobertura de obrigação. A taxonomia residual implementation_missing não é prova de impossibilidade contratual. Campanha continua não autorizada por este artefato.

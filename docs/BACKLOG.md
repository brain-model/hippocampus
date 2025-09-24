# Backlog de Melhorias — PR #4 (pendências)

Contexto: consolidar apenas o que ainda não foi implementado após o review completo do MR #4, evitando duplicidades e com critérios de aceite claros.

## Prioridades

- P0: Alta — correção/segurança com risco de regressão ou supply-chain.
- P1: Média — robustez, manutenibilidade, cobertura e consistência operacional.
- P2: Baixa — documentação, estilo e otimizações de pipeline.

## Itens Pendentes

1. [P1] Cobertura unitária adicional do validador

   - Descrição: Expandir cobertura de `core/application/validation.py` para casos edge ainda não cobertos (conforme PR #3).
   - Critérios de aceite:
     - Testes para `manifestVersion` ausente, formato inválido, major < 1 e major >= 2.
     - Mensagens determinísticas mantidas (ordem estável; `<root>` quando aplicável).
     - Cobertura do módulo `validation.py` >= 90%.

2. [P2] Evolução da heurística de extração JSON (LLM)

   - Descrição: Avaliar migração para fenced JSON blocks ou sentinelas no prompt, reduzindo fragilidade do fallback.
   - Critérios de aceite:
     - Implementação de estratégia alternativa em `_extract_json_from_content` ou documentação reforçada com guidance de prompt.
     - Testes cobrindo JSON misto e saídas irregulares.

3. [P2] Consistência de idioma (PT/EN)

   - Descrição: Refinar padronização do idioma entre CLI/agent e README, mantendo coerência por seção/contexto.
   - Critérios de aceite:
     - Headings/exemplos consistentes; mensagens de erro alinhadas ao idioma da seção.
     - Guia de estilo mínimo documentado para novas contribuições.

4. [P2] Robustez do secret scan (advisory)

   - Descrição: Evoluir a verificação de segredos do PR Validation para reduzir falsos positivos/negativos.
   - Critérios de aceite:
     - Substituir grep simples por padrões mais estritos ou ferramenta dedicada (ex.: gitleaks) como check informativo (não bloqueante).
     - Excluir diretórios irrelevantes e manter execução rápida.

5. [P2] Cache do ambiente (CI)

   - Descrição: Opcional — adicionar cache para `setup-python`/`setup-uv` a fim de reduzir tempo do CI.
   - Critérios de aceite:
     - Cache configurado sem impactar reprodutibilidade.
     - Tempo médio das execuções reduzido de forma observável.

## Observações

- Itens P0/P1 implementados nesta iteração: URLs do projeto corrigidas (`pyproject.toml` e `mkdocs.yml`), pins por SHA no `ci.yml` e `release.yml` (incluindo Codecov) e padronização do `python -m pip` no `release.yml`.
- Itens já implementados (por exemplo, pins por SHA no `pr-validation.yml`, fetch base antes do diff e Bandit único com JSON) foram removidos para evitar duplicidade.
- O gate de cobertura (fail_under = 90) permanece ativo via configuração do Coverage em `pyproject.toml`.

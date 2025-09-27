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

### Refatorações Arquiteturais (implementadas)

1. [P1] ✅ **Refatoração arquitetural de `pipeline.py`** — CONCLUÍDA (2025-09-27)

   - Descrição: Decompor `core/application/pipeline.py` em um submódulo coeso `core/application/pipeline/` (ex.: `load.py`, `extract.py`, `assemble.py`, `validate.py`, `metrics.py`, `report.py`, `io.py`) separando responsabilidades (carregamento/normalização, extração, montagem/validação, métricas/relato e escrita).
   - Resultados alcançados:
     - ✅ API pública preservada: `build_manifest_from_text` e `build_manifest_from_file` continuam disponíveis via `core.application.pipeline` (com import forwarding).
     - ✅ Sem mudança de comportamento observável; somente refactor (logs e mensagens permaneceram estáveis; caminhos de saída e schema idênticos).
     - ✅ Novos módulos com testes dedicados; cobertura do pacote `core/application/pipeline/` = 92.93% (≥ 90%).
     - ✅ Imports internos e chamadas de CLI atualizados; compatibilidade mantida para manter estabilidade.
     - ✅ 319 testes passando com funcionalidade idêntica.

### Refatorações Arquiteturais (pendentes)

1. [P1] Refatoração arquitetural de `langchain_agent.py`

   - Descrição: Quebrar `core/infrastructure/extraction/langchain_agent.py` em um subpacote `core/infrastructure/extraction/llm/` (ex.: `config.py`, `agent.py`, `normalize.py`, `errors.py`, `providers/{openai_like.py, gemini.py, anthropic.py}`) isolando resolução de config, fábricas de provider, tratamento de erros, normalização/DTOs e política de retries.
   - Critérios de aceite:
     - API pública preservada: classe `LangChainExtractionAgent` segue importável em `core.infrastructure.extraction.langchain_agent` (reexport/forward) e seu contrato não muda.
     - Sem mudança de comportamento; mensagens de erro e códigos de saída mapeados inalterados.
     - Cobertura do subpacote `llm/` ≥ 90%; testes de providers e normalização mantidos e reorganizados por módulo.
     - Código organizado por provider, removendo condicionalidade extensa; dependências opcionais respeitadas.
     - Documentação de arquitetura do agente LLM adicionada (breve visão por componentes).

2. [P1] Refatoração arquitetural de `root.py` (CLI)

   - Descrição: Extrair subcomandos e helpers de `core/cli/root.py` para `core/cli/commands/` (ex.: `collect.py`, `set.py`, `help.py`, `util.py`), deixando `root.py` como fino orquestrador de argparse/subparsers.
   - Critérios de aceite:
     - Console script `hippo` inalterado; UX/flags e mensagens preservadas.
     - `root.py` com responsabilidade mínima; subcomandos testáveis isoladamente.
     - Cobertura do pacote `core/cli/commands/` ≥ 90% e testes e2e do CLI continuam passando.
     - Documentação do CLI atualizada (estrutura de comandos e orientação para contribuir).

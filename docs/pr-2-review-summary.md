# PR #2 — Revisão e Feedback Estruturado

## Resumo

- PR 2 entrega o motor “llm-graph”, flags de grafo no CLI, métricas agregadas (tokens/latência), e resiliência centralizada (retries/backoff com jitter), com documentação e CHANGELOG atualizados.
- Código e docs estão, em geral, consistentes: `README.md`, `CHANGELOG.md`, `TODO.md`, `design_doc.md` e o wiring no CLI e grafo conferem com o diff/patch esperado.
- Itens de backlog relevantes permanecem abertos: normalização de DOI incompleta e observabilidade discreta no handler; lacunas de testes (pipeline/report e ConfigManager).

## Verificações Principais

- Graph/CLI:
  - Flags e envs documentadas e implementadas: `--graph-timeout`, `--graph-retries`, `--graph-backoff-base`, `--graph-backoff-max`, `--graph-jitter` e `HIPPO_GRAPH_*` em `hippocampus/core/cli/root.py`.
  - `GraphConfig` em `hippocampus/core/noesis/graph/types.py` cobre timeout/retries/backoff/jitter.
  - Orquestrador consolida métricas e expõe provider/modelo: `hippocampus/core/noesis/graph/agent.py` e `.../nodes/extract.py`.
- Métricas e relatórios:
  - `pipeline.py` agrega e rendeza métricas/relatório. Adapter do grafo (`GraphExtractorAdapter`) propaga `last_graph_total_ms` e `last_graph_tokens`.
- Resiliência:
  - Retry/backoff com jitter está centralizado e aplicado no agente LLM e nos nós do grafo.
- Requisitos/empacotamento:
  - Python >= 3.11 em `pyproject.toml`; dependências obrigatórias; CHANGELOG condizente.

## Achados e Severidade

- BUG (médio): DOI com espaços internos não é normalizado antes de compor URL.
  - Onde: `hippocampus/core/infrastructure/extraction/langchain_agent.py`, `_normalize_reference_item`.
  - Impacto: Gera `url` inválida para DOIs com espaços internos (dados sujos e links quebrados).
- Melhoria (baixo): Observabilidade discreta ausente no handler de erros.
  - Onde: `.../langchain_agent.py`, `_handle_provider_errors`.
  - Impacto: Dificulta troubleshooting não-invasivo; ausência de rastro (provider, exceção) em nível `debug`.
- Testes (alto): Cobertura insuficiente para caminhos de pipeline/report e precedência de config.
  - Onde: `hippocampus/core/application/pipeline.py` (caminhos não-verbose/report) e `ConfigManager`/resolver.
  - Impacto: Regressões silenciosas em UX do CLI e em precedência/segurança de secrets.

## Recomendações (ação objetiva)

- DOI: Remover espaços internos antes de compor URL.
  - Em `_normalize_reference_item`, aplicar `re.sub(r"\\s+", "", doi.strip())` antes de `f"https://doi.org/{doi}"`.
  - Adicionar teste cobrindo `doi = "10.1000/ 182 "` gerando `url == "https://doi.org/10.1000/182"`.
- Observabilidade: Incluir debug log no início do handler.
  - Em `_handle_provider_errors`, `logger.debug("provider_error", extra={"provider": provider, "exc": type(e).__name__})` (ou equivalente), sem poluir saída do usuário.
  - Garantir logger configurado para não vazar secrets.
- Testes:
  - Pipeline/report: Testar caminhos `verbose=False` e `_render_report_and_end` (contagem de URLs/citações, tempos e métricas do grafo quando engine=`llm-graph`).
  - ConfigManager: Testar precedência (CLI > local > global > defaults) e secrets (keyring local→global > env), incluindo máscara/segurança em logs.
- Documentação:
  - README: Adicionar nota curta sobre normalização de DOI (remoção de espaços) e comportamento de fallback do grafo (já consistente, apenas reforçar).

## Decisão

- Status: REVISAO_NECESSARIA
- Justificativa: Há pelo menos um problema de correção (DOI com espaços internos) e lacunas de testes consideradas importantes para confiabilidade em produção. As correções são pontuais e de baixo risco.

## Handoff JSON

{
  "status": "REVISAO_NECESSARIA",
  "feedback": [
    {
      "type": "BUG",
      "severity": "médio",
      "file": "hippocampus/core/infrastructure/extraction/langchain_agent.py",
      "section": "_normalize_reference_item",
      "issue": "DOI com espaços internos não é normalizado antes de compor a URL.",
      "recommendation": "Aplicar remoção de espaços internos: doi = re.sub(r\"\\s+\", \"\", doi.strip()); depois compor url = f\"https://doi.org/{doi}\". Adicionar teste cobrindo DOIs com espaços."
    },
    {
      "type": "MELHORIA",
      "severity": "baixo",
      "file": "hippocampus/core/infrastructure/extraction/langchain_agent.py",
      "section": "_handle_provider_errors",
      "issue": "Falta de log de diagnóstico no início do handler.",
      "recommendation": "Adicionar logger.debug com provider e classe da exceção (sem secrets), p.ex. logger.debug(\"provider_error\", extra={\"provider\": provider, \"exc\": type(e).__name__})."
    },
    {
      "type": "TESTES",
      "severity": "alto",
      "file": "hippocampus/core/application/pipeline.py",
      "section": "_render_report_and_end / fluxos não-verbose",
      "issue": "Cobertura insuficiente do caminho de report e consolidação (contagens/latência/métricas do grafo).",
      "recommendation": "Criar testes que validem renderização e números em modos heuristic, llm e llm-graph, verificando tokens/latências agregadas quando disponíveis."
    },
    {
      "type": "TESTES",
      "severity": "alto",
      "file": "hippocampus/core/infrastructure/config/*",
      "section": "ConfigManager/resolver",
      "issue": "Ausência de testes de precedência e segurança de secrets.",
      "recommendation": "Cobrir precedência (CLI > local > global > defaults) e secrets (keyring local→global > env), incluindo mascaramento em logs e ausência de vazamento."
    }
  ]
}

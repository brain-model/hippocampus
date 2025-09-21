# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]

### Changed

- Confiabilidade centralizada: retry/backoff exponencial com jitter movido para `core/reliability/` e aplicado tanto no caminho `llm` quanto no `llm-graph`.
- Compatibilidade Python: requisito atualizado para `>=3.11`.
- Empacotamento: dependências antes opcionais passaram a ser obrigatórias no primeiro release (extras removidos do `pyproject.toml`).

### Added

- Testes de retry no caminho `llm` validando sucesso após falhas transitórias e não‑retry em erros permanentes.

### Docs

- README atualizado com exemplo de flags do grafo (`--graph-timeout`, `--graph-retries`, backoff/jitter) e nota sobre precedência de configs no grafo.

## [0.5.0] - 2025-09-20

### Added (0.5.0)

- Graph orchestrator (Fase 5): nós `classify → extract → consolidate` com contratos tipados.
- Integração `--engine llm-graph` no pipeline/CLI via adapter (UI mantém modo llm).
- Métricas agregadas no grafo: `total_latency_ms`, `total_tokens` e breakdown por nó.
- Relatório do CLI mostra métricas do grafo (Graph Total/Graph Tokens) quando aplicável.
- Retries e tratamento de `TimeoutError` no nó Extract, com fallback heurístico opcional.
- Prompts versionados: `classify_reference_type_en.md`, `consolidate_manifest_en.md` (além de `extract_references_en.md`).
- Extra opcional `graph` no `pyproject.toml` e documentação correspondente no README.

### Changed (0.5.0)

- README atualizado com seção de LangGraph (experimental) e extras opcionais.
- TODO/roadmap marcado com itens concluídos da Fase 5 e cobertura ≥ 95%.

## [0.4.0] - 2025-09-20

### Added (0.4.0)

- LLM multi-provider: OpenAI, Gemini, Claude e DeepSeek (compat OpenAI via `base_url`).
- Config Manager: escopos Local/Global, `get/set`, secrets via `keyring` com fallback seguro.
- CLI `hippo set`: `key=value`, `--file config.yaml` com `--merge|--reset`, `--generate-template`.
- Templates Jinja2 com emojis: `config_set.j2`, `config_apply.yaml.j2`, `llm_run.j2`, `error.j2`.
- Agente de extração com LangChain (`ExtractionAgent`) e prompt `extract_references_en.md` (few-shot) retornando JSON.
- Opções de engine no CLI/pipeline: `--engine {llm,heuristic}`, `--provider`, `--model`, `--temperature`, `--max-tokens`, `--timeout-s`, `--base-url`, `--retries`.
- Testes: config manager (local/global, keyring fallback, merge/reset), subcomando `set`, agente LLM (mocks de sucesso/JSON inválido/timeout) e integração no pipeline/CLI.

### Changed (0.4.0)

- Resolução central de configuração: prioridade CLI > local > global > defaults, com proveniência nas mensagens.
- Mensagens do CLI renderizadas por templates (emojis), incluindo latência e informações de engine.
- Documentação atualizada para Fase 4; `TODO.md` marcado como concluído para a fase.

## [0.3.0] - 2025-09-18

### Added (0.3.0)

- Multi-format loaders: Markdown, LaTeX, PDF (via `pypdf`).
- Loader registry with automatic selection by file extension.
- File-based pipeline `build_manifest_from_file` and CLI `--file` option.
- Tests for loaders/registry/CLI with coverage ≥ 90% (subsequently improved to 100% for loaders).

### Changed (0.3.0)

- Simplified PDF loader to assume `pypdf` available; removed optional dependency checks.
- Updated `TODO.md` marking Phase 3 as complete; inserted Phase 4 planning.

## [0.2.0] - 2025-09-17

### Added (0.2.0)

- MVP text pipeline: `build_manifest_from_text`, heuristic extractor, JSON writer.
- CLI `--text` with output directory handling and `--verbose` error reporting.
- JSON Schema validation (Draft-07) using centralized `MANIFEST_SCHEMA_PATH`.
- Module and function docstrings across the codebase.

### Changed (0.2.0)

- Resources reorganized under `core/resources/{prompts,templates,schemas}`.
- Makefile targets for format, lint, and tests; coverage gate ≥ 90%.

## [0.1.0] - 2025-09-16

### Added (0.1.0)

- Initial scaffold with Clean Architecture under `core/`.
- Domain contracts and manifest types.
- Packaging via `pyproject.toml` with console script `hippocampus`.
- Initial tests and CI setup groundwork.

[Unreleased]: https://example.com/compare/0.4.0...HEAD
[0.4.0]: https://example.com/compare/0.3.0...0.4.0
[0.3.0]: https://example.com/compare/0.2.0...0.3.0
[0.2.0]: https://example.com/compare/0.1.0...0.2.0

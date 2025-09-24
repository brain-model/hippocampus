# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]

## [0.7.0] - 2025-09-23

### Added (0.7.0)

- CI: smoke install do pacote (wheel) com `hippo --help` e `hippo collect` heurístico.
- CI: build de documentação de usuário com MkDocs Material e artifact de site.
- Docs: estrutura inicial de documentação de usuário (`docs-user/`) e configuração `mkdocs.yml` (Material, strict).

### Changed (0.7.0)

- Empacotamento: instalação completa (sem extras); mensagens de ImportError do LLM atualizadas.
- Build: inclusão explícita de `core/resources/**` no wheel (Hatch include + force-include do schema).
- Workflows: `uv sync --dev` (sem `--all-extras`), melhorias no job de build-test.
- Metadados: adição de `license` no `pyproject.toml` e atualização de classifiers/URLs.

### Fixed (0.7.0)

- Lint: linhas longas e espaçamento em slices no `langchain_agent.py`.
- PDF loader: evitar try/except/continue (Bandit), fallback para chunk vazio.

### Added

- **CI/CD Pipeline**: GitHub Actions workflows para lint, teste, build e release automatizado
- **Multi-Python Testing**: Testes automatizados em Python 3.11, 3.12 e 3.13
- **Coverage Reporting**: Integração com Codecov para relatórios de cobertura
- **Security Analysis**: Bandit integrado ao pipeline de CI
- **Release Automation**: Workflow automático para publicação no PyPI e GitHub Releases
- **PR Validation**: Verificações automáticas de CHANGELOG e documentação
- **Dependabot**: Atualizações automáticas de dependências e GitHub Actions
- **Issue Templates**: Templates para bug reports e feature requests
- **PR Template**: Template padronizado para pull requests
- **Makefile Commands**: Comandos CI/CD (`make ci`, `make build`, `make release-check`)
- **Integration Tests**: Testes end-to-end automatizados no CI
- **Performance Tests**: Testes básicos de performance no pipeline

### Changed

- **Workflow CI**: Expandido de job único para pipeline multi-stage com validações
- **Makefile**: Reorganizado com seções para desenvolvimento e CI/CD
- **Pre-commit**: Integrado ao workflow de CI para garantir qualidade

## [0.6.0] - 2025-09-22

### Changed

- Confiabilidade centralizada: retry/backoff exponencial com jitter movido para `core/reliability/` e aplicado tanto no caminho `llm` quanto no `llm-graph`.
- Compatibilidade Python: requisito atualizado para `>=3.11`.
- Empacotamento: dependências antes opcionais passaram a ser obrigatórias no primeiro release (extras removidos do `pyproject.toml`).
- Validação: mensagens determinísticas no validador (ordenação estável e `<root>` para caminho vazio); CLI padroniza mensagens de erro via template Jinja.
- Schema: `manifestVersion` agora exige SemVer `x.y.z` e `status` restrito; `details` polimórfico por `referenceType` com `additionalProperties: false`.

### Added

- Testes de retry no caminho `llm` validando sucesso após falhas transitórias e não‑retry em erros permanentes.
- Normalização de DOI: remoção de espaços internos/quebras e composição de URL `https://doi.org/{doi}` quando ausente.
- Testes: validação de versão do manifesto (válida, inválida, incompatível); integração do pipeline cobrindo multi‑tipos e falha quando `details` não corresponde ao tipo.

### Docs (0.6.0)

- README atualizado com exemplo de flags do grafo (`--graph-timeout`, `--graph-retries`, backoff/jitter) e nota sobre precedência de configs no grafo.
- README atualizado com seções de DOI Normalization e Manifest Versioning.
- README atualizado com seção de Validation & Errors (CLI) incluindo exemplos de mensagens padronizadas renderizadas pelo template `error.j2`.

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

[Unreleased]: https://github.com/brain-model/hippocampus/compare/0.7.0...HEAD
[0.7.0]: https://github.com/brain-model/hippocampus/compare/0.6.0...0.7.0
[0.6.0]: https://github.com/brain-model/hippocampus/compare/0.5.0...0.6.0
[0.4.0]: https://github.com/brain-model/hippocampus/compare/0.3.0...0.4.0
[0.3.0]: https://github.com/brain-model/hippocampus/compare/0.2.0...0.3.0
[0.2.0]: https://github.com/brain-model/hippocampus/compare/0.1.0...0.2.0

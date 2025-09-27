# Hippocampus – TODOs e Roadmap

Este arquivo consolida o plano de implementação e o backlog de tarefas por fases para o agente Hippocampus.

## Objetivos

- Receber texto/arquivo, extrair referências e metadados via pipeline (LLM opcional), e emitir `manifest/manifest.json` validado por schema.
- Separação limpa (domínio vs. infraestrutura), CLI fina, outputs determinísticos e validação rígida.

## Roadmap por Fases

1. Foundation/Scaffold: estrutura `core/`, empacotamento, entrypoint, contratos base, mover `prompts/` e `templates/` para `resources/`, e schema em `resources/schemas/`.
2. MVP (Texto): CLI raiz, loader texto, extrator heurístico, validação e geração de `manifest.json`.
3. Multiformato: loaders `markdown/txt`, PDF, LaTeX básico; interface unificada e registry de loaders.
4. LLM Multi‑provider & Config: suporte a OpenAI/Gemini/Claude/DeepSeek, configuração via `hippo set` (key=value e YAML), templates de saída com emojis.
5. LangGraph/LLM: orquestrador mínimo, biblioteca de prompts, reuso da configuração da Fase 4 e fallback heurístico.
6. Validação Robusta: `manifest.schema.json`, validação polimórfica de `details`, versionamento `manifestVersion`.
7. DX/Observabilidade: logging estruturado, `--verbose`, traces opcionais, CI (lint+test).
8. Empacotamento/Docs: distribuição e documentação de instalação/uso (instalação completa, sem extras).

9. Refactor Pipeline: extrair submódulos coesos (`load`, `extract`, `assemble`, `validate`, `metrics`, `report`, `io`) preservando API pública.
10. Refactor LLM Agent: modularizar por provider e camadas (`config`, `agent`, `normalize`, `errors`, `providers/*`) mantendo contrato e mensagens.
11. Refactor CLI: dividir subcomandos em `core/cli/commands/` e deixar `root.py` como orquestrador fino do argparse.

## Critérios de Aceite (gerais por fase)

- CLI com `--help` claro; erros com exit code != 0 e mensagens descritivas.
- `manifest.json` sempre inclui: `manifestVersion`, `manifestId`, `processedAt`, `status`, `sourceDocument`, `knowledgeIndex`.
- Testes: unidade (schema/loader/validação) e integração (e2e texto no MVP).

## Backlog Detalhado

> Nota: Itens incrementais de melhorias mapeadas a cada novo PR a partir do primeiro na fase # (prioridades P0/P1/P2) estão detalhados em `docs/BACKLOG.md`.

Atualização 2025-09-24:

- Concluídas as correções P0/P1 do MR #4: URLs do projeto atualizadas, actions fixadas por SHA em CI/Release, padronização do `python -m pip` no release.
- Pendências remanescentes foram mantidas apenas no `docs/BACKLOG.md` (cobertura adicional do validador, heurística de extração JSON, consistência de idioma, secret scan aprimorado e cache opcional de CI).
  
Novas fases (refactors estruturais):

- Fase 9 — Refactor Pipeline (P1)
- Fase 10 — Refactor LLM Agent (P1)
- Fase 11 — Refactor CLI (P1)

### Fase 1 — Foundation/Scaffold

1) [x] Remover `hippocampus/main.py` e preparar Commit 0 (somente não-.py) com mensagem: primeira frase do Frankenstein (original).
2) [x] Criar diretórios `prompts/` e `templates/` (adicionar `.keep`/`README.md`).
3) [x] Configurar `pyproject.toml` com `[project].name = "hippocampus"`, script `hippo = core.cli.root:main`, wheel `[tool.hatch.build.targets.wheel].packages = ["core"]`.
4) [x] Adicionar `[project.optional-dependencies]` para `llm` e `pdf` (runtime mínimo vazio).
5) [x] Adicionar `manifest.schema.json` (versão inicial) alinhado ao design.
6) [x] Reorganizar assets: `resources/prompts`, `resources/templates` e `resources/schemas/manifest.schema.json`.
7) [x] Testes unitários e lint do repositório base com cobertura >= 90% (focando validação de schema e carga de config).

Status: ✅ CONCLUÍDO — 2025-09-18 • via COMMIT #d59781c: You will rejoice to hear that no disaster has accompanied the commencement of an enterprise which you have regarded with such evil forebodings.

### Fase 2 — MVP (Texto)

1) [x] `core/domain/manifest.py`: tipos (TypedDict/dataclasses) e constantes (`manifestVersion`, `status`).
2) [x] `core/domain/interfaces.py`: contratos `DocumentLoader`, `ExtractionAgent`, `Formatter`.
3) [x] `core/infrastructure/loaders/text.py`: loader de texto (UTF-8, normalização de quebras de linha).
4) [x] `core/infrastructure/extraction/heuristic.py`: extractor heurístico (URLs + padrões simples de citação).
5) [x] `core/infrastructure/formatters/json_writer.py`: grava `manifest/manifest.json` com `processedAt` e `manifestId`.
6) [x] `core/application/validation.py`: validação contra `manifest.schema.json`.
7) [x] `core/application/pipeline.py`: `build_manifest_from_text(text, out_dir)` orquestrando loader → extractor → formatter.
8) [x] `core/cli/root.py`: CLI raiz com `-t/--text`, `-o/--output`, `--verbose` (desabilitar `--file` por enquanto).
9) [x] Atualizar `README.md` com exemplo de uso do MVP.
10) [x] Testes unitários e e2e do MVP com cobertura >= 90% (schema, loader, extractor, formatter, pipeline, CLI).

- Estruturar `tests/` espelhando `core/` com `test_{submodule}.py`.
- `tests/conftest.py` com `pytest_plugins` para importar fixtures.
- `tests/fixtures/` por módulo: `application/`, `cli/`, `domain/`, `infrastructure/{loaders,extraction,formatters}/`.
- Unit: `domain/manifest`, `infrastructure/loaders/text`, `infrastructure/extraction/heuristic`, `infrastructure/formatters/json_writer`, `application/validation`.
- Integração: `application/pipeline` (gera `manifest.json` válido) e `cli/root` (parse/exit codes/output).
- Cobertura: rodar com `uvx --from pytest-cov pytest --cov=core --cov-report=term-missing`.

Status: ✅ CONCLUÍDO — 2025-09-18 • via COMMIT #7f75932: feat(core,tests) MVP step 2 — manifest pipeline with heuristic extraction and JSON Schema validation; add CLI and tests (>=90% coverage)

### Fase 3 — Multiformato

1) Loaders base e integrações:
   - [x] `MarkdownLoader` com fallback local (sem LangChain)
   - [x] `TextLoader` (plain) já existente
2) [x] Loader PDF (`pypdf`) com extração de texto e normalização.
3) [x] Loader LaTeX básico (remoção de comandos comuns e preservação de argumentos).
4) [x] `core/infrastructure/loaders/registry.py` e seleção por extensão/flag.
5) [x] Habilitar `--file` no CLI com seleção automática de loader por extensão e testes de integração.
6) [x] Testes unitários dos loaders e registry com cobertura >= 90%.

Status: ✅ CONCLUÍDO — 2025-09-18 • via COMMIT #b766904: feat(loaders,cli,tests) Fase 3 — multiformato (Markdown, PDF, LaTeX), registry, --file e cobertura 100%

### Fase 4 — LLM Multi‑provider & Configurações

1) Dependências e Providers
   - [x] Adicionar dependências estáveis de providers LLM: `langchain>=0.2`, `langchain-openai`, `langchain-google-genai`, `langchain-anthropic` (manter `pypdf`).
   - [x] Dependências de configuração: `keyring`, `pyyaml` e `jinja2` adicionadas.
   - [x] DeepSeek: documentado uso via `engine.base_url` + `api.deepseek.key` (integrado no agente em 5).

2) Gerente de Configuração
   - [x] `core/infrastructure/config/manager.py`: leitura/escrita de config por escopo.
   - [x] Escopos: Local (`.hippo/config.json`) e Global (`~/.config/hippocampus/config.json`).
   - [x] Secrets no `keyring` por provider (ex.: `api.openai.key`), com fallback seguro (arquivo com `chmod 600`) se `keyring` indisponível.
   - [x] API: `get/set` para chaves, `get_secret/set_secret` para segredos, mascaramento em outputs.

3) CLI `set` (configuração)
   - [x] `hippo set key=value [--local|--global]`: grava chave simples (`engine.*` ou `api.*`).
   - [x] `hippo set --file config.yaml [--merge|--reset] [--local|--global]`: aplica YAML com merge (default) ou reset.
   - [x] `hippo set --generate-template [-o template.yaml]`: gera um YAML de exemplo com todas as chaves possíveis.
   - [x] Chaves suportadas:

4) Templates de Saída do CLI
   - [x] `core/resources/templates/`: `config_set.j2`, `config_apply.yaml.j2`, `error.j2`, `llm_run.j2` com formatação e emojis.
   - [x] Renderer com Jinja2 (`{{ placeholder }}`) via `core/resources/templates/manager.py`.

5) Agente LLM Multi‑provider
   - [x] `core/infrastructure/extraction/langchain_agent.py`: implementa `ExtractionAgent`.
   - [x] Parsing e validação de JSON (lista `references`); timeouts e retries configuráveis.

6) Integração no Pipeline/CLI
   - [x] `--engine {llm,heuristic}`, `--provider`, `--model`, `--temperature`, `--max-tokens`, `--timeout-s`, `--base-url`, `--retries`.
   - [x] Mensagens de execução via templates (emojis, tokens, latência/Engine); erro claro quando faltar API key.

7) Testes e Qualidade
   - [x] Testes do config manager (local/global, keyring fallback via integração, merge/reset YAML, mascaramento) — coberto em integração/subcomando.
   - [x] Cobertura >= 95% (alvo 100% nos módulos novos); lint/format OK.

Status: ✅ CONCLUÍDO — 2025-09-20 • via PR #1 (feature/llm-multiprovider-config): LLM multi‑provider & config integrados.

### Fase 5 — LangGraph/LLM

1) [x] Especificar grafo e contratos
   - Definir estados, nós (classify → extract → consolidate), entradas/saídas, erros e timeouts.
   - Acceptance: diagrama/README curto da fase + tipos em `core/noesis/graph/types.py`.

1) [x] Estrutura inicial do módulo graph
   - Criar `core/noesis/graph/{agent.py,nodes/,types.py}` e esqueleto de orquestrador (sem dependências pesadas por padrão).
   - Acceptance: importável quando o grafo está desabilitado; feature flag/env preparado.

1) [x] Biblioteca de prompts versionada
   - Centralizar prompts: `classify_reference_type_en.md`, `extract_references_en.md`, `consolidate_manifest_en.md` em `core/resources/prompts/`.
   - Acceptance: carregamento via manager de resources/templates com versionamento simples.

1) [x] Nó Classify
   - Classificar trechos/referências candidatas (tipos de referência, heurísticas auxiliares).
   - Acceptance: função pura com entrada texto e saída tipada; facilmente mockável.

1) [x] Nó Extract
   - Extrair campos/detalhes via LLM (reutilizando configuração da Fase 4), com retries/timeouts.
   - Acceptance: usar `LangChainExtractionAgent` sob capa; respeitar `engine.*` e segredos.

1) [x] Nó Consolidate
   - Consolidar classificações + extrações em referências normalizadas.
   - Acceptance: saída compatível com `manifest.schema.json` (estrutura `knowledgeIndex.references`).

1) [x] Fallback heurístico por nó
   - Encadear fallback para `HeuristicExtractionAgent` por nó quando houver falhas (configurável por flag/env).
   - Acceptance: comportamento coberto por testes, com logs/resumos claros.

1) [x] Integração no pipeline/CLI
   - Adicionar modo `engine=llm-graph` (ou flag/env `HIPPO_USE_LANGGRAPH`) no pipeline/CLI.
   - Acceptance: pipeline usa o grafo quando habilitado, mantendo compatibilidade com `heuristic` e `llm` atuais.

1) [x] Métricas e telemetria do grafo
   - Agregar tokens/latência por nó e total; expor no relatório final.
   - Acceptance: campos de métricas presentes quando `engine=llm-graph`.

1) [x] Tratamento de erros e política de retries
   - Acceptance: testes de erro cobrem openai/gemini/claude/deepseek e cenários de timeout.

1) [x] Dependências e extras opcionais
   - Acceptance: `[project.optional-dependencies].graph` documentado; instalação opcional.

1) [x] Testes unitários dos nós
   - Acceptance: cobertura ≥ 90% nos módulos do grafo.

1) [x] Teste de integração do grafo (e2e)
   - Acceptance: gera `manifest.json` válido e preenche métricas do grafo.

1) [x] Docs e CHANGELOG 0.5.0
   - Acceptance: exemplos executáveis, notas de compatibilidade e feature flags.

1) [x] QA gate (lint+tests)
   - Acceptance: gate ≥ 90% e checks verdes.

Status: ✅ CONCLUÍDO • 2025-09-20 • via PR #2 (feature/langgraph-orchestrator): LangGraph orquestrador mínimo integrado.

### Fase 6 — Validação Robusta

1) [x] Schema — detalhes polimórficos por tipo
   - [x] Fixar `core/resources/schemas/manifest.schema.json` com validação condicionada a `referenceType` para o campo `details` (via `if/then`).
   - [x] Definir sub‑schemas mínimos por tipo: `article`, `book`, `website`, `thesis`, `conference`, `unknown`.
   - [x] `additionalProperties: false` em todos os sub‑schemas de `details`.
   - [x] Definir campos obrigatórios mínimos por tipo (mantido permissivo nesta etapa, sem obrigatórios rígidos para não quebrar heurística).
   - [x] Acceptance: manifests com `details` incoerentes ao tipo falham com erro claro de validação para os tipos suportados.

   Status: ✅ CONCLUÍDO — 2025-09-22 • via COMMITS #6ffc5ea, ...: validação polimórfica de `details` (web_link, in_text_citation, article, book, website, thesis, conference, unknown) com `additionalProperties:false` e casos de teste.

2) [x] Versão e compatibilidade do manifesto
   - [x] Formalizar `manifestVersion` (SemVer `x.y.z`) no schema e no domínio.
   - [x] Implementar verificação de compatibilidade no validador (recusar majors futuras não suportadas).
   - [x] Preencher `manifestVersion` no pipeline/CLI e propagar a usuários em relatórios.
   - [x] Acceptance: manifests sem versão válida ou incompatíveis resultam em erro descritivo e exit code != 0.

   Status: ✅ CONCLUÍDO — 2025-09-22 • via COMMIT #d5bf2b2: feat(validation) impor SemVer em manifestVersion e compat >=1.0.0,<2.0.0; tests para versão ausente/inválida/incompatível

3) [x] Validador e integração no pipeline/CLI
   - [x] `core/application/validation.py`: carregar e aplicar schema polimórfico; mensagens determinísticas (ordenação estável e `<root>` para caminho vazio).
   - [x] `core/domain/manifest.py`: constante canônica de `manifestVersion` e `status`.
   - [x] `core/application/pipeline.py` e `core/cli/root.py`: garantir preenchimento de versão e mapeamento de erros (template unificado de erro na CLI, prefixos consistentes no validador).
   - Acceptance: fluxo texto/arquivo valida `details` e `manifestVersion` em todos os engines (heuristic/llm/llm‑graph).

4) [x] Normalização de DOI (BACKLOG P2)
   - [x] Normalizar `doi` antes de compor a URL (`strip()` + remoção de espaços internos) no normalizador de referências.
   - [x] Atualizar testes cobrindo DOIs com espaços/quebras; documentar comportamento no README.
   - [x] Acceptance: URLs de DOI não contêm espaços; testes e docs atualizados.

   Status: ✅ CONCLUÍDO — 2025-09-22 • via COMMIT #48e2579: feat(normalization) normalizar DOI (strip + remoção de espaços) e montar URL quando ausente; tests de normalização

5) [x] Testes (unidade e integração)
   - [x] Unidade: casos happy/erro por `web_link` e `in_text_citation` (polimorfismo de `details`).
   - [x] Unidade: versão ausente/inválida/incompatível; mensagens claras.
   - [x] Integração: pipeline gera `manifest.json` válido multi‑tipos; falha quando `details` não bate com tipo.
   - [x] Cobertura alvo: ≥ 90% nos módulos alterados (atingida: 94.04%).
   - [x] Acceptance: suíte passa com cobertura mínima atingida.

   Status: ✅ CONCLUÍDO — 2025-09-22 • via COMMITS #06bda45, #48e2579, #118aa5d: integração CLI+validação; normalização de DOI; e2e multi‑tipos; 241 passed; cobertura ≥ 90%.

6) [x] Documentação e QA gate
   - [x] Atualizar `CHANGELOG.md` (marcar `BREAKING` se necessário) e `README.md` (seção `manifestVersion` e DOI).
   - [x] Garantir lint+tests verdes (gate) após as mudanças.
   - [x] Acceptance: docs publicadas e pipeline de qualidade aprovado.

   Status: ✅ CONCLUÍDO — 2025-09-22 • via COMMITS #9240212, #118aa5d: README (DOI e Manifest Versioning) e CHANGELOG (Unreleased); gate de testes OK (241 passed).

### Fase 7 — DX/Observabilidade

1) **Logging Estruturado e Observabilidade**
   - [x] Adicionar dependência `rich` para logging estruturado e UI aprimorada.
   - [x] Implementar `core/infrastructure/logging/structured.py` com logger configurável (console/file/json).
   - [x] Integrar logs estruturados em `_handle_provider_errors` com `provider` e `type(e).__name__` (sem vazar segredos).
   - [x] Mapear tipos de erro para códigos de saída específicos no CLI (`core/cli/exit_codes.py`).

   Status: ✅ CONCLUÍDO — 2025-09-22 • via PR #3 (feature/dx-observability): logging estruturado integrado e mapeamento de exit codes no CLI.

2) **Verbose Mode e Traces**
   - [x] Melhorar `--verbose` no CLI com informações estruturadas via `rich.console`.
   - [x] Habilitar traces de LLM/graph controlados por env vars (`HIPPO_TRACE_LLM=true`, `HIPPO_TRACE_GRAPH=true`).
   - [x] Mascarar segredos (API keys) em logs e traces automaticamente.
   - [x] Adicionar métricas detalhadas no modo verbose (tokens, latência por nó, retries).

   Status: ✅ CONCLUÍDO — 2025-09-22 • via PR #3 (feature/dx-observability): verbose aprimorado; `HIPPO_TRACE_LLM/HIPPO_TRACE_GRAPH`; métricas detalhadas.

3) **Qualidade de Código e Tooling**
   - [x] Configurar `ruff` para linting/formatting (substituir/complementar ferramentas atuais).
   - [x] Configurar `black` para formatação de código consistente.
   - [x] Adicionar `pyproject.toml` seções `[tool.ruff]` e `[tool.black]` com regras do projeto.
   - [x] Setup de pre-commit hooks para linting automático.
   - [x] Refatoração de código para resolver violações de qualidade (complexidade cognitiva, line length, etc.).
   - [x] Correção de problemas de segurança detectados pelo bandit.

   Status: ✅ CONCLUÍDO — 2025-09-22 • via PR #3 (feature/dx-observability): ruff/black/pre-commit configurados; ajustes de qualidade aplicados.

4) **CI/CD e Automação**
   - [x] Configurar GitHub Actions para lint+test automático em PRs.
   - [x] Adicionar workflow de release automático com tags semânticas.
   - [x] Setup de coverage reporting automático (codecov/coveralls).
   - [x] Validação automática de CHANGELOG em PRs.
   - Acceptance: CI verde, releases automáticos, coverage tracking.

   Status: ✅ CONCLUÍDO — 2025-09-22 • via PR #3 (feature/dx-observability): CI multi-stage (lint/test/build/release), Codecov integrado, validação de CHANGELOG.

5) **Melhorias de UX no CLI**
   - [x] Emitir sumário renderizado no modo verbose (corrigir chamada morta em `build_manifest_from_text`).
   - [x] Unificar relatório no pipeline de arquivo (reutilizar `_render_report_and_end` com métricas LLM).
   - [x] Adicionar progress bars para operações longas (LLM/Graph).
   - [x] Melhorar mensagens de erro com sugestões de correção.
   - Acceptance: UX consistente, relatórios unificados, feedback visual.

   Status: ✅ CONCLUÍDO — 2025-09-23 • via COMMIT #1c98c80: feat(cli) dicas acionáveis; relatório unificado; verbose sumário; refatoração de complexidade

6) **Cobertura e Testes de Qualidade**
   - [x] Expandir testes para casos edge de `manifestVersion` (majors `<1` e `>=2`).
   - [x] Testes unitários dos utilitários de logging/observabilidade.
   - [x] Testes de integração do pipeline com logging estruturado.
   - [x] Validar cobertura >= 90% dos novos módulos de observabilidade.
   - Acceptance: cobertura mantida, novos módulos testados, edge cases cobertos.

7) **Documentação de DX**
   - [x] Atualizar README com seção de troubleshooting e logs.
   - [x] Documentar variáveis de ambiente para traces e debugging.
   - [x] Guia de contribuição com setup de desenvolvimento e tooling.
   - [x] Exemplos de uso do modo verbose e traces.
   - Acceptance: docs completas, exemplos executáveis, guia de dev clear.

   Status: ✅ CONCLUÍDO — 2025-09-22 • via COMMITS #e16654a, #3e7d72a, #d27a126: README (Verbose & Tracing), CONTRIBUTING, e TODO atualizados.

8) **QA Gate e Integração**
   - [x] Executar `make lint && make test` com novas ferramentas.
   - [ ] Validar performance sem regressões (benchmarks básicos).
   - [x] Revisar logs em cenários reais (mock providers, timeouts, erros) — verificados no modo `--verbose` durante smoke local.
   - [x] CHANGELOG 0.7.0 com features de observabilidade.
   - Acceptance: gate ≥ 90%, sem regressões, docs atualizadas.

### Fase 8 — Empacotamento/Docs

1) [x] Empacotamento completo (sem extras)
   - [x] Consolidar dependências em `[project].dependencies` (instalação completa sempre)
   - [x] Incluir `core/**` no wheel/sdist (CLI, schemas, prompts, templates)
   - [x] Validar wheel inclui `core/cli/root.py` e `resources/*`
   - Estado: Dependências consolidadas; `force-include` do schema e `tool.hatch.build.include = ["core/**"]` aplicados. Wheel inspecionado com sucesso.

2) [x] CI: build + smoke install
   - [x] Build de artefatos (wheel + sdist)
   - [x] Smoke install + `hippo --help`
   - [x] Smoke heurístico: `hippo collect -t "..." --engine=heuristic`
   - [x] Build das docs (MkDocs) no CI
   - Estado: Validado localmente com `uvx --from ./dist/*.whl hippo --help`, coleta heurística com manifest gerado e `mkdocs build --strict`. Workflows atualizados para smoke e docs.

3) [x] Workflow de Release
   - [x] Anexar artefatos ao GitHub Release (idempotente, substituição de artefatos)
   - [x] Publicar no PyPI (condicional por tag)
   - [x] Release notes a partir do CHANGELOG para a tag
   - [x] Publicar documentação no GitHub Pages (docs-user)
   - Estado: `ncipollo/release-action@v1` configurada com `allowUpdates`/`replacesArtifacts`; etapa de PyPI e GH Pages presentes. Release notes automáticos a partir do CHANGELOG ainda a configurar se desejado.

4) [x] Testes de empacotamento
   - [x] Entry point (`hippo`) resolve e exibe `--help`
   - [x] Recursos acessíveis via import (`core/resources/*` empacotados)
   - [x] Versão do pacote confere com `pyproject.toml`
   - Estado: OK via `uvx --from dist/*.whl hippo --help`; inspeção do wheel confirma resources e CLI; versão 0.7.0.

5) [x] Documentação de instalação
   - README: seção única de instalação (pip/uv), sem matriz de extras
   - Requisitos: Python >= 3.11

6) [x] Metadados do pacote
   - [x] Campo `license` em `[project]`
   - [x] `classifiers` adequados
   - [x] `project-urls` com Homepage/Repository/Documentation
   - Estado: License adicionado (proprietário), classifiers e URLs concluídos.

7) [x] Bump versão + CHANGELOG
   - Atualizar para `0.7.0` com notas de Observabilidade, UX do CLI, Empacotamento
   - Validar com `make validate-changelog`

8) [x] Build local e validação
   - `make build`; instalar wheel em venv temporária; `hippo --help` e `collect` heurístico
   - Estado: Sucesso com `uvx --from build pyproject-build` e smoke via `uvx`.

9) [x] Documentação (Usuário vs Técnica)
    - Usuário (MkDocs + Material):
       - Configurar `mkdocs.yml` (tema Material, `docs_dir: docs-user/`) — configurado
       - Estrutura inicial: `docs-user/index.md` (Getting Started), `installation.md`, `usage.md`, `cli.md`, `configuration.md`, `troubleshooting.md` — criada
       - Publicação: GitHub Pages via workflow CI; adicionar link "Documentation" em `project.urls` do `pyproject.toml` (aparece no PyPI)
    - Técnica (interna, no repositório):
       - Manter em `docs/` (design_doc, BACKLOG, TODO, etc.)
       - Tornar o `README.md` a porta de entrada, com seção "Documentação Técnica" linkando os artefatos internos
    - Estado: Build local das docs OK (`mkdocs build --strict`); publicação via workflow configurada.

### Fase 9 — Refactor Pipeline

1) Estruturação do submódulo `core/application/pipeline/`
   - [x] Separar responsabilidades em arquivos: `load.py` (loaders/normalização), `extract.py` (heurística/LLM/graph adapters), `assemble.py` (montagem do manifest), `validate.py` (integração do schema e mensagens), `metrics.py` (agregação de métricas), `report.py` (render dos templates), `io.py` (writer e paths).
   - [x] Manter API pública: `build_manifest_from_text` e `build_manifest_from_file` reexportadas por `core.application.pipeline`.
   - [x] Cobertura do pacote ≥ 90%; sem mudanças de comportamento observável (paridade de testes e mensagens/logs).
   - [x] Documentar diagrama/resumo do fluxo por módulo em `docs/design_doc.md`.

Status: ✅ CONCLUÍDO — 2025-09-27 • Refatoração completa do pipeline em 8 módulos especializados; API pública preservada via reexports; 92.93% de cobertura com 319 testes passando.

### Fase 10 — Refactor LLM Agent

1) Subpacote `core/infrastructure/extraction/llm/`
   - [ ] Quebrar `langchain_agent.py` em: `config.py`, `agent.py`, `normalize.py`, `errors.py`, `providers/{openai_like.py,gemini.py,anthropic.py}`.
   - [ ] Preservar a classe `LangChainExtractionAgent` como façade em `langchain_agent.py` (reexport/forward) mantendo contrato e comportamento.
   - [ ] Testes reorganizados por módulo com cobertura ≥ 90%; mensagens/códigos de saída inalterados.
   - [ ] Adicionar seção de arquitetura do agente em `docs/design_doc.md`.

### Fase 11 — Refactor CLI

1) Subcomandos em `core/cli/commands/`
   - [ ] Extrair `collect` e `set` para módulos dedicados; `root.py` apenas cria `argparse` e delega.
   - [ ] Assegurar que `hippo` mantém UX/flags e ajuda rica; cobertura de comandos ≥ 90% e e2e do CLI verde.
   - [ ] Atualizar `docs-user/cli.md` e instruções de contribuição para refletir a nova estrutura.

## Riscos e Mitigações

- Variabilidade do LLM → heurística determinística como fallback; testes de prompt.
- Fragilidade de loaders (PDF/LaTeX) → validar parsing e cobrir com testes; tratar erros de leitura de forma robusta.
- Escopo/derivas → respeitar fases, congelar schema antes do LLM, critérios de aceite claros.

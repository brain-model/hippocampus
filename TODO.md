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
8. Empacotamento/Docs: extras `llm`/`pdf`, distribuição, docs de instalação/uso.

## Critérios de Aceite (gerais por fase)

- CLI com `--help` claro; erros com exit code != 0 e mensagens descritivas.
- `manifest.json` sempre inclui: `manifestVersion`, `manifestId`, `processedAt`, `status`, `sourceDocument`, `knowledgeIndex`.
- Testes: unidade (schema/loader/validação) e integração (e2e texto no MVP).

## Backlog Detalhado

### Fase 1 — Foundation/Scaffold

1) [x] Remover `hippocampus/main.py` e preparar Commit 0 (somente não-.py) com mensagem: primeira frase do Frankenstein (original).
2) [x] Criar diretórios `prompts/` e `templates/` (adicionar `.keep`/`README.md`).
3) [x] Configurar `pyproject.toml` com `[project].name = "hippocampus"`, script `hippocampus = core.cli.root:main`, wheel `[tool.hatch.build.targets.wheel].packages = ["core"]`.
4) [x] Adicionar `[project.optional-dependencies]` para `llm` e `pdf` (runtime mínimo vazio).
5) [x] Adicionar `manifest.schema.json` (versão inicial) alinhado ao design.
6) [x] Reorganizar assets: `resources/prompts`, `resources/templates` e `resources/schemas/manifest.schema.json`.
7) [x] Testes unitários e lint do repositório base com cobertura >= 90% (focando validação de schema e carga de config).

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

### Fase 3 — Multiformato

1) Loaders base e integrações:
   - [x] `MarkdownLoader` com fallback local (sem LangChain)
   - [x] `TextLoader` (plain) já existente
2) [x] Loader PDF (`pypdf`) com extração de texto e normalização.
3) [x] Loader LaTeX básico (remoção de comandos comuns e preservação de argumentos).
4) [x] `core/infrastructure/loaders/registry.py` e seleção por extensão/flag.
5) [x] Habilitar `--file` no CLI com seleção automática de loader por extensão e testes de integração.
6) [x] Testes unitários dos loaders e registry com cobertura >= 90%.

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
      - Engine: `engine.provider`, `engine.model`, `engine.temperature`, `engine.max_tokens`, `engine.timeout_s`, `engine.base_url`, `engine.retries` (para providers compatíveis)
      - Secrets: `api.openai.key`, `api.gemini.key`, `api.claude.key`, `api.deepseek.key` (armazenadas no keyring)

4) Templates de Saída do CLI
   - [x] `core/resources/templates/`: `config_set.j2`, `config_apply.yaml.j2`, `error.j2`, `llm_run.j2` com formatação e emojis.
   - [x] Renderer com Jinja2 (`{{ placeholder }}`) via `core/resources/templates/manager.py`.

5) Agente LLM Multi‑provider
   - [x] `core/infrastructure/extraction/langchain_agent.py`: implementa `ExtractionAgent`.
   - [x] Fábrica de modelos por provider: OpenAI (`ChatOpenAI`), Gemini (`ChatGoogleGenerativeAI`), Claude (`ChatAnthropic`), DeepSeek (OpenAI‑compatível via `base_url`).
   - [x] Prompt de extração: `core/resources/prompts/extract_references_en.md` (few‑shot) com saída JSON válida.
   - [x] Parsing e validação de JSON (lista `references`); timeouts e retries configuráveis.

6) Integração no Pipeline/CLI
   - [x] `--engine {llm,heuristic}`, `--provider`, `--model`, `--temperature`, `--max-tokens`, `--timeout-s`, `--base-url`, `--retries`.
   - [x] Resolução de config: flags CLI > config local > config global > defaults (resolver central com proveniência).
   - [x] Mensagens de execução via templates (emojis, tokens, latência/Engine); erro claro quando faltar API key.

7) Testes e Qualidade
   - [x] Testes do config manager (local/global, keyring fallback via integração, merge/reset YAML, mascaramento) — coberto em integração/subcomando.
   - [x] Testes do subcomando `set` (key=value, --file, --generate-template), validação de mensagens/templating.
   - [x] Testes do agente LLM (mocks por provider: sucesso, JSON inválido, timeout) e pipeline/CLI com seleção de engine.
   - [x] Cobertura >= 95% (alvo 100% nos módulos novos); lint/format OK.

> Nota: Itens incrementais de melhoria deste PR (prioridades P0/P1/P2) estão detalhados em `BACKLOG.md`.

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

   - Mapear erros por provedor também no grafo; retries exponenciais por nó; preservar `TimeoutError`.
   - Acceptance: testes de erro cobrem openai/gemini/claude/deepseek e cenários de timeout.

1) [x] Dependências e extras opcionais

   - Adicionar `langgraph` (ou manter orquestrador leve sem dependência externa) como extra `graph`.
   - Acceptance: `[project.optional-dependencies].graph` documentado; instalação opcional.

1) [x] Testes unitários dos nós

   - Cobrir Classify/Extract/Consolidate com LLM mockado e entradas representativas.
   - Acceptance: cobertura ≥ 90% nos módulos do grafo.

1) [x] Teste de integração do grafo (e2e)

   - Fluxo ponta a ponta com mocks determinísticos e fallback heurístico.
   - Acceptance: gera `manifest.json` válido e preenche métricas do grafo.

1) [x] Docs e CHANGELOG 0.5.0

   - Atualizar README (uso, flags, extras) e CHANGELOG (Fase 5).
   - Acceptance: exemplos executáveis, notas de compatibilidade e feature flags.

1) [x] QA gate (lint+tests)

   - Executar `make lint && make test` e revisar cobertura/qualidade (sem regressões).
   - Acceptance: gate ≥ 90% e checks verdes.

Status: Concluída em 2025-09-20 via PR #2 (`feature/langgraph-orchestrator`).

- Evidências: CLI com `engine=llm-graph` e flags de grafo; orquestrador classify → extract → consolidate com métricas (tokens/latência) e fallback heurístico; retries com backoff e jitter; integração no pipeline/relatórios; README/CHANGELOG atualizados; extra `graph` definido em `pyproject.toml`.
- Qualidade: `make lint` e `make test` verdes; 214 testes passando; cobertura ~95% (>90%).

### Fase 6 — Validação Robusta

1) [ ] Fixar `manifest.schema.json` e validar polimorficamente `details` por `referenceType`.
2) [ ] Introduzir `manifestVersion`, notas de migração e verificação de compatibilidade.
3) [ ] Testes unitários de validação polimórfica com cobertura >= 90%.

### Fase 7 — DX/Observabilidade

1) [ ] Logging estruturado (`rich`/`loguru`) e `--verbose`; mapear erros para códigos de saída.
2) [ ] Habilitar traces de LLM/graph controlados por env; mascarar segredos em logs.
3) [ ] Qualidade de código: ruff/black e CI (lint+test).
4) [ ] Testes unitários dos utilitários de logging/observabilidade com cobertura >= 90%.

### Fase 8 — Empacotamento/Docs

1) [ ] Configurar extras (`llm`, `pdf`) e gerar wheel; validar instalação local do CLI.
2) [ ] Atualizar documentação com matriz de recursos por extras e instruções de instalação/execução.
3) [ ] Testes unitários de empacotamento (import/entrypoints) com cobertura >= 90%.

## Riscos e Mitigações

- Variabilidade do LLM → heurística determinística como fallback; testes de prompt.
- Fragilidade de loaders (PDF/LaTeX) → validar parsing e cobrir com testes; tratar erros de leitura de forma robusta.
- Escopo/derivas → respeitar fases, congelar schema antes do LLM, critérios de aceite claros.

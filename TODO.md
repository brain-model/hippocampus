# Hippocampus – TODOs e Roadmap

Este arquivo consolida o plano de implementação e o backlog de tarefas por fases para o agente Hippocampus.

## Objetivos

- Receber texto/arquivo, extrair referências e metadados via pipeline (LLM opcional), e emitir `manifest/manifest.json` validado por schema.
- Separação limpa (domínio vs. infraestrutura), CLI fina, outputs determinísticos e validação rígida.

## Roadmap por Fases

1. Foundation/Scaffold: estrutura `core/`, empacotamento, entrypoint, contratos base, mover `prompts/` e `templates/` para `resources/`, e schema em `resources/schemas/`.
2. MVP (Texto): CLI raiz, loader texto, extrator heurístico, validação e geração de `manifest.json`.
3. Multiformato: loaders `markdown/txt`, PDF, LaTeX básico; interface unificada e registry de loaders.
4. LLM Multi‑provider & Config: suporte a OpenAI/Gemini/Claude/DeepSeek, configuração via `hippocampus set` (key=value e YAML), templates de saída com emojis.
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
   - [ ] Adicionar dependências estáveis: `langchain>=0.2`, `langchain-openai`, `langchain-google-genai`, `langchain-anthropic`, `keyring`, `pyyaml` (e manter `pypdf`).
   - [ ] DeepSeek via cliente OpenAI‑compatível (`ChatOpenAI` com `base_url`) e `DEEPSEEK_API_KEY`.

2) Gerente de Configuração
   - [ ] `core/infrastructure/config/manager.py`: leitura/escrita de config por escopo.
   - [ ] Escopos: Local (`.hippo/config.json`) e Global (`~/.config/hippocampus/config.json`).
   - [ ] Secrets no `keyring` por provider (ex.: `api.openai.key`), com fallback seguro (arquivo com `chmod 600` + aviso) se `keyring` indisponível.
   - [ ] API: `get/set` para chaves, `get_secret/set_secret` para segredos, mascaramento em outputs.

3) CLI `set` (configuração)
   - [ ] `hippocampus set key=value [--local|--global]`: grava chave simples (engine.\* ou api.\*).
   - [ ] `hippocampus set --file config.yaml [--merge|--reset] [--local|--global]`: aplica YAML com merge (default) ou reset.
   - [ ] `hippocampus set --generate-template [-o template.yaml]`: gera um YAML de exemplo com todas as chaves possíveis.
   - [ ] Chaves suportadas:
       - Engine: `engine.provider`, `engine.model`, `engine.temperature`, `engine.max_tokens`, `engine.timeout_s`, `engine.base_url` (para providers compatíveis)
       - Secrets: `api.openai.key`, `api.gemini.key`, `api.claude.key`, `api.deepseek.key` (armazenadas no keyring)

4) Templates de Saída do CLI
   - [ ] `core/resources/templates/`: `config_set.txt`, `config_apply.yaml.txt`, `error.txt`, `llm_run.txt` com formatação e emojis.
   - [ ] `TemplateRenderer` simples para interpolação (`{placeholder}`).

5) Agente LLM Multi‑provider
   - [ ] `core/infrastructure/extraction/langchain_agent.py`: implementa `ExtractionAgent`.
   - [ ] Fábrica de modelos por provider: OpenAI (`ChatOpenAI`), Gemini (`ChatGoogleGenerativeAI`), Claude (`ChatAnthropic`), DeepSeek (OpenAI‑compatível via `base_url`).
   - [ ] Prompt de extração: `core/resources/prompts/extract_references_en.txt` (few‑shot) com saída JSON válida.
   - [ ] Parsing e validação de JSON (lista `references`); timeouts e retries configuráveis.

6) Integração no Pipeline/CLI
   - [ ] `--engine {llm,heuristic}` (default: `llm`), `--provider`, `--model`, `--temperature`, `--max-tokens`, `--timeout-s`, `--base-url`.
   - [ ] Resolução de config: flags CLI > config local > config global > defaults.
   - [ ] Mensagens de execução via templates (emojis, tokens, latência); erro claro quando faltar API key.

7) Testes e Qualidade
   - [ ] Testes do config manager (local/global, keyring mock, merge/reset YAML, mascaramento).
   - [ ] Testes do subcomando `set` (key=value, --file, --generate-template), validação de mensagens/templating.
   - [ ] Testes do agente LLM (mocks por provider: sucesso, JSON inválido, timeout) e pipeline/CLI com seleção de engine.
   - [ ] Cobertura >= 95% (alvo 100% nos módulos novos); lint/format OK.

### Fase 5 — LangGraph/LLM

1) [ ] Biblioteca de prompts em `prompts/` (`extract_references.md`, `classify_reference_type.md`, etc.) com versionamento.
2) [ ] `core/noesis/graph/agent.py`: grafo mínimo (classify → extract → consolidate).
3) [ ] Reusar configuração/engine da Fase 4; fallback para heurística quando indisponível.
4) [ ] Testes unitários e de integração com LLM mockado com cobertura >= 90%.

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

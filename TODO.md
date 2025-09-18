# Hippocampus – TODOs e Roadmap

Este arquivo consolida o plano de implementação e o backlog de tarefas por fases para o agente Hippocampus.

## Objetivos

- Receber texto/arquivo, extrair referências e metadados via pipeline (LLM opcional), e emitir `manifest/manifest.json` validado por schema.
- Separação limpa (domínio vs. infraestrutura), CLI fina, outputs determinísticos e validação rígida.

## Roadmap por Fases

1. Foundation/Scaffold: estrutura `core/`, empacotamento, entrypoint, contratos base, mover `prompts/` e `templates/` para `resources/`, e schema em `resources/schemas/`.
2. MVP (Texto): CLI raiz, loader texto, extrator heurístico, validação e geração de `manifest.json`.
3. Multiformato: loaders `markdown/txt`, PDF (extra `pdf`), LaTeX básico; interface unificada e registry de loaders.
4. LangGraph/LLM: orquestrador mínimo, biblioteca de prompts, LLM configurável com fallback heurístico.
5. Validação Robusta: `manifest.schema.json`, validação polimórfica de `details`, versionamento `manifestVersion`.
6. DX/Observabilidade: logging estruturado, `--verbose`, traces opcionais, CI (lint+test).
7. Empacotamento/Docs: extras `llm`/`pdf`, distribuição, docs de instalação/uso.

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
7) [ ] Testes unitários e lint do repositório base com cobertura >= 90% (focando validação de schema e carga de config).

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

1) [ ] Loaders `markdown` e `plain` com LangChain quando disponível; fallback local se ausente.
2) [ ] Extra `pdf` (ex.: `pypdf`) e loader PDF opcional com graceful fallback.
3) [ ] Loader LaTeX básico (remoção de comandos comuns).
4) [ ] `core/infrastructure/loaders/registry.py` e seleção por extensão/flag.
5) [ ] Testes unitários dos loaders e registry com cobertura >= 90%.

### Fase 4 — LangGraph/LLM

1) [ ] Biblioteca de prompts em `prompts/` (`extract_references.md`, `classify_reference_type.md`, etc.) com versionamento.
2) [ ] `core/noesis/graph/agent.py`: grafo mínimo (classify → extract → consolidate).
3) [ ] Integração de LLM configurável (env/flag) e fallback para heurística quando indisponível.
4) [ ] Testes unitários e de integração com LLM mockado com cobertura >= 90%.

### Fase 5 — Validação Robusta

1) [ ] Fixar `manifest.schema.json` e validar polimorficamente `details` por `referenceType`.
2) [ ] Introduzir `manifestVersion`, notas de migração e verificação de compatibilidade.
3) [ ] Testes unitários de validação polimórfica com cobertura >= 90%.

### Fase 6 — DX/Observabilidade

1) [ ] Logging estruturado (`rich`/`loguru`) e `--verbose`; mapear erros para códigos de saída.
2) [ ] Habilitar traces de LLM/graph controlados por env; mascarar segredos em logs.
3) [ ] Qualidade de código: ruff/black e CI (lint+test).
4) [ ] Testes unitários dos utilitários de logging/observabilidade com cobertura >= 90%.

### Fase 7 — Empacotamento/Docs

1) [ ] Configurar extras (`llm`, `pdf`) e gerar wheel; validar instalação local do CLI.
2) [ ] Atualizar documentação com matriz de recursos por extras e instruções de instalação/execução.
3) [ ] Testes unitários de empacotamento (import/entrypoints) com cobertura >= 90%.

## Riscos e Mitigações

- Variabilidade do LLM → heurística determinística como fallback; testes de prompt.
- Fragilidade de loaders (PDF/LaTeX) → extras opcionais e degradação para texto.
- Escopo/derivas → respeitar fases, congelar schema antes do LLM, critérios de aceite claros.

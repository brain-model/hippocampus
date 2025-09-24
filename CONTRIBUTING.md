# Contribuindo para Hippocampus

Obrigado por dedicar seu tempo para contribuir! Este guia explica como configurar o ambiente, o fluxo de trabalho esperado, os padrões de código e como abrir PRs com segurança e qualidade.

## Requisitos

- Python >= 3.11
- [uv](https://github.com/astral-sh/uv) para gestão de dependências
- Git e Make

## Setup Rápido

```bash
# Clonar o repositório e entrar no diretório
git clone https://github.com/brain-model/hippocampus.git
cd hippocampus

# Criar/ativar ambiente e instalar deps (dev)
uv sync --dev

# Instalar hooks do pre-commit
uv run pre-commit install
```

## Comandos Úteis (Makefile)

```bash
# Formatação e lint
make format
make lint

# Testes com cobertura (gate >= 90%) e XML (Codecov)
make test

# Build local (wheel)
make build

# Verificação de release (tags/versões/CHANGELOG)
make release-check
```

## Padrões de Commit (Semântico)

Adote Conventional Commits:

- feat: nova funcionalidade
- fix: correção de bug
- docs: documentação
- chore: melhorias de rotina
- refactor, perf, test, build, ci, style, revert

Exemplos:

```bash
git commit -m "feat(core): adicionar extração de DOI"
git commit -m "fix(cli): corrigir precedência do HIPPO_OUTPUT_DIR"
```

Breaking changes devem conter a anotação no corpo do commit:

```text
BREAKING CHANGE: deprecates X and removes Y
```

## Fluxo de Branches e PRs

- Crie branches a partir de `main` usando o padrão `feature/`, `fix/`, `docs/` etc.
- Mantenha PRs pequenos e focados. Inclua descrição clara, contexto e screenshots (se aplicável).
- Atualize `CHANGELOG.md` quando for relevante ao usuário final.
- O CI executa lint, testes (matriz 3.11/3.12/3.13), build e cobertura (Codecov). Corrija quaisquer falhas antes de pedir review.

## Cobertura e Qualidade

- Gate de cobertura: >= 90% (pytest-cov). O pipeline publica `coverage.xml` e envia ao Codecov.
- Evite capturas genéricas (`except Exception:`); prefira exceções específicas.
- Escreva testes para caminhos felizes e de erro. Utilize fixtures e mocks.

## Segurança

- Bandit roda no CI. Evite uso de `subprocess` sem sanitização e nunca logue segredos.
- Secrets devem ser mascarados pelo `StructuredLogger` (já coberto por testes).

## DX: Debugging e Tracing

- Verbose: use `--verbose` para logs detalhados do pipeline.
- Tracing LLM: `HIPPO_TRACE_LLM=1` habilita logs estruturados de chamadas LLM.
- Tracing Graph: `HIPPO_TRACE_GRAPH=1` habilita métricas e logs do LangGraph.
- Saída padrão: `~/.brain-model/hippocampus/buffer/consolidation` (sobrepor com `-o` ou `HIPPO_OUTPUT_DIR`).

## Diretrizes de Código

- Clean Architecture: respeite camadas `core/{domain,application,infrastructure,ui}` e `core/noesis` (grafo).
- Sem side-effects em imports. Funções puras quando possível.
- Mensagens de erro do CLI via templates Jinja para consistência.

## Publicação e Releases

- Releases são automatizadas por tags `vX.Y.Z` (GitHub Actions).
- O workflow cria artefatos, publica no PyPI (tags estáveis) e abre GitHub Release.
- Siga SemVer e mantenha o `CHANGELOG.md` atualizado.

## Como Solicitar Review

- Garanta CI verde.
- Descreva o racional, decisões de design e trade-offs.
- Marque revisores apropriados e peça sinal verde do `ReviewAgent` quando aplicável.

Agradecemos sua contribuição! 🚀

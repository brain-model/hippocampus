.PHONY: setup lint format test clean run ci hippo hippo-install hippo-uninstall pre-commit-install pre-commit-run security build release validate-changelog

# Development commands
setup: clean ## Instala/Ativa Python correto, cria env e instala dependências com UV (inclui dev)
	uv python install
	uv python pin
	uv sync --dev
	$(MAKE) pre-commit-install

lint: ## Executa o linter ruff com correções automáticas
	uvx ruff check core/ tests/ --fix
	uvx ruff format core/ tests/

format: ## Formata o código com ruff
	uvx ruff format core/ tests/
	uvx ruff check core/ tests/ --fix --select I

test: ## Executa os testes unitários
	uv run pytest --cov=core --cov-report=term-missing --cov-report=xml:coverage.xml --cov-fail-under=90 -q --maxfail=1

test-verbose: ## Executa os testes com saída detalhada
	uv run pytest --cov=core --cov-report=term-missing --cov-report=html --cov-report=xml:coverage.xml --cov-fail-under=90 -v

security: ## Executa verificações de segurança com bandit
	uvx bandit -r core/ -f json -o security-report.json || true
	uvx bandit -r core/ --severity-level medium

pre-commit-install: ## Instala pre-commit hooks
	uvx pre-commit install
	uvx pre-commit install --hook-type commit-msg

pre-commit-run: ## Executa todos os pre-commit hooks
	uvx pre-commit run --all-files

quality: ## Executa todas as verificações de qualidade (lint + security + pre-commit)
	$(MAKE) lint
	$(MAKE) security
	$(MAKE) pre-commit-run

# CI/CD commands
ci: ## Executa pipeline completo de CI (lint + test + build)
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) build
	@echo "✅ CI pipeline completed successfully"

build: ## Constrói os pacotes de distribuição (wheel + sdist)
	uvx --from build pyproject-build
	@echo "📦 Built packages:"
	@ls -la dist/

validate-changelog: ## Valida se CHANGELOG.md tem formato correto
	@if head -20 CHANGELOG.md | grep -q "## \[Unreleased\]"; then \
		echo "✅ CHANGELOG has proper Unreleased section"; \
	else \
		echo "❌ CHANGELOG should have an [Unreleased] section at the top"; \
		exit 1; \
	fi

release-check: ## Verifica se está pronto para release
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) validate-changelog
	$(MAKE) build
	@echo "✅ Ready for release!"

.PHONY: integration-test
integration-test:
	@echo "Running integration tests..."
	@echo "Input test content" > /tmp/test.md
	uv run hippo collect -f /tmp/test.md --engine=heuristic --verbose
	@rm -f /tmp/test.md

performance-test: ## Executa testes de performance básicos
	@echo "Running performance tests..."
	@python -c "print('# Large Test\\n' + ('Test line with [ref](http://example.com)\\n' * 1000))" > /tmp/large.md
	@time uv run hippo collect -f /tmp/large.md --engine=heuristic > /dev/null
	@rm -f /tmp/large.md
	@rm -rf hippo-out
	@echo "✅ Performance test completed"

# App commands

run: ## Executa o CLI com ARGS='-t "..." -o ./.out'
	@[ -n "$(ARGS)" ] || (echo "Defina ARGS, ex.: make run ARGS='-t \"txt\" -o ./.out'" && exit 1)
	uv run python -m core.cli.root $(ARGS)

hippo: ## Executa o comando hippo com ARGS (ex.: make hippo ARGS='set --generate-template -o h.yaml')
	@[ -n "$(ARGS)" ] || (echo "Defina ARGS, ex.: make hippo ARGS='-t \"txt\" -o ./.out'" && exit 1)
	uv run hippo $(ARGS)

hippo-install: ## Instala o comando hippo globalmente (~/.local/bin) via uv tool install .
	uv tool install .
	@echo "Instalado. Certifique-se de ter ~/.local/bin no PATH."



hippo-uninstall: ## Remove o comando hippo instalado globalmente
	uv tool uninstall hippo || true
	uv tool uninstall hippocampus || true
	@echo "Removido."

clean: ## Remove arquivos temporários e de build
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type f -name '*.py[co]' -delete
	rm -f .coverage
	rm -rf .pytest_cache .mypy_cache build/ dist/ *.egg-info/
	[ -d .venv ] && rm -rf .venv || true
	@echo "Clean complete."

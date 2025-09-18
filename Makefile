.PHONY: setup lint format test clean run ci


setup: clean ## Instala/Ativa Python correto, cria env e instala dependências com UV (inclui dev)
	uv python install
	uv python pin
	uv sync
	uv add --dev pytest pytest-cov ruff black isort

lint: ## Executa o linter ruff
	uvx ruff check core/

format: ## Formata o código com black e isort
	uvx black core/
	uvx isort core/

test: ## Executa os testes unitários
	uv run pytest --cov=core --cov-report=term-missing --cov-fail-under=90 -q --maxfail=1

run: ## Executa o CLI com ARGS='-t "..." -o ./.out'
	@[ -n "$(ARGS)" ] || (echo "Defina ARGS, ex.: make run ARGS='-t \"txt\" -o ./.out'" && exit 1)
	uv run python -m core.cli.root $(ARGS)

ci: ## Executa lint e testes (com gate de cobertura)
	$(MAKE) lint
	$(MAKE) test

clean: ## Remove arquivos temporários e de build
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type f -name '*.py[co]' -delete
	rm -f .coverage
	rm -rf .pytest_cache .mypy_cache build/ dist/ *.egg-info/
	[ -d .venv ] && rm -rf .venv || true
	@echo "Clean complete."

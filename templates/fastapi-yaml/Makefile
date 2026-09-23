.PHONY: init config config-check config-template format-check hooks run test lint format check

init:
	uv sync --all-groups
	@$(MAKE) config-template
	@$(MAKE) hooks

hooks:
	@if [ -d .git ]; then \
		uv run pre-commit install --hook-type pre-commit --hook-type commit-msg; \
	else \
		echo "pre-commit: пропущено, .git не найден."; \
		echo "Выполните git init, затем make hooks."; \
	fi

config:
	@test -f config.yaml || cp config.template.yaml config.yaml
	@chmod 600 config.yaml

# Шаблон конфигурации и его JSON Schema не должны отставать от моделей настроек.
config-check:
	uv run python scripts/config_template.py

config-template:
	uv run python scripts/config_template.py --write

run: config
	uv run python -m {{ project_slug }}.main

test: config
	uv run pytest

lint:
	uv run ruff check .

format-check:
	uv run ruff format --check .

format:
	uv run ruff format .
	uv run ruff check --fix .

check: lint format-check config-check test

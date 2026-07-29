.PHONY: init config run test lint format check

init:
	uv sync --all-groups

config:
	@test -f config.yaml || cp config.template.yaml config.yaml
	@chmod 600 config.yaml

run: config
	uv run python -m {{ project_slug }}.main

test: config
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

check: lint test

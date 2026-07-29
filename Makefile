.PHONY: init config run test lint format check

init:
	uv sync --all-groups

config:
	@test -f config.yaml || cp config.template.yaml config.yaml
	@chmod 600 config.yaml

run: config
	uv run uvicorn {{ project_slug }}.main:app --reload --port {{ service_port }}

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

check: lint test

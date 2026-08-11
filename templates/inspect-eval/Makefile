.PHONY: init config hooks run view score test lint format check

init:
	uv sync --all-groups
	@$(MAKE) hooks

hooks:
	@if [ -d .git ]; then \
		uv run pre-commit install; \
	else \
		echo "pre-commit: пропущено, .git не найден."; \
		echo "Выполните git init, затем make hooks."; \
	fi

config:
	@test -f config.yaml || cp config.template.yaml config.yaml
	@chmod 600 config.yaml

# Прогон по описанию из configs/runs. Пример: make run RUN=configs/runs/service_eval.yaml
run: config
	@test -n "$(RUN)" || (echo "Укажите RUN=configs/runs/<файл>.yaml" && exit 2)
	uv run python -m {{ project_slug }}.main run $(RUN)

# Просмотр логов прогонов.
view:
	uv run inspect view start --log-dir logs

# Переоценить готовый лог другим scorer'ом, не гоняя тестируемый сервис заново.
# Пример: make score LOG=logs/<файл>.eval
score:
	@test -n "$(LOG)" || (echo "Укажите LOG=logs/<файл>.eval" && exit 2)
	uv run inspect score $(LOG) --action append

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

check: lint test

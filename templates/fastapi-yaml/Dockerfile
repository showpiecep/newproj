# syntax=docker/dockerfile:1.7
#
# Образ без секретов: config.yaml монтируется при запуске.
#   docker build -t {{ project_slug }}:local .
#   docker run --rm -p {{ service_port }}:{{ service_port }} \
#       -v ./config.yaml:/app/config.yaml:ro {{ project_slug }}:local

# --- Сборка окружения ---------------------------------------------------------
# Стадия общая для любого проекта на uv и от прикладного кода не зависит:
# меняется только при смене версии Python или uv.
FROM python:{{ python_version }}-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.8.14 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Зависимости ставятся отдельным слоем: он пересобирается только при смене lock-файла.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# --- Runtime ------------------------------------------------------------------
# Стадия настраивается под проект: порт, HEALTHCHECK, системные пакеты,
# дополнительные каталоги с данными.
FROM python:{{ python_version }}-slim

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv ./.venv
COPY --from=builder --chown=app:app /app/src ./src

# Каталог принадлежит app: при старте bootstrap пишет рядом с config.yaml
# config.template.yaml и config.schema.json.
RUN chown app:app /app
USER app

EXPOSE {{ service_port }}

# Когда в приложении появится ручка здоровья, добавьте проверку, например:
# HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
#     CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:{{ service_port }}/health', timeout=4).status == 200 else 1)"

CMD ["python", "-m", "{{ project_slug }}.main"]

"""Запуск прогона: конфигурация -> задача -> `eval` -> лог."""

from __future__ import annotations

from pathlib import Path

from inspect_ai import Epochs
from inspect_ai import eval_async as inspect_eval
from inspect_ai.log import EvalLog
from inspect_ai.model import Model, get_model

from ..application.interfaces import ServiceUnderTest
from ..infrastructure.http import HttpServiceUnderTest
from ..settings import Config
from .configuration.run import RunConfig
from .service_eval import service_eval


def build_service(config: Config) -> ServiceUnderTest:
    """Собирает реализацию порта тестируемого сервиса.

    Точка, где выбирается протокол. Добавляя вторую реализацию (Kafka, архив
    записанных ответов), выбор делают здесь по настройке, а задача не меняется.
    """
    return HttpServiceUnderTest(
        config.service.url,
        timeout=config.service.timeout,
        answer_field=config.service.answer_field,
        headers=config.service.headers,
    )


def build_judge_model(config: Config, run_config: RunConfig) -> Model:
    """Собирает модель судьи с локальными реквизитами доступа."""
    api_key = config.judge.api_key.get_secret_value() or None
    return get_model(
        run_config.judge.model,
        api_key=api_key,
        base_url=config.judge.base_url,
    )


async def run(
    run_config_path: str | Path,
    *,
    config: Config,
    log_dir: str | None = None,
) -> list[EvalLog]:
    """Прогоняет один run-конфиг и возвращает логи Inspect AI."""
    run_config = RunConfig.load(run_config_path)
    service = build_service(config)
    judge_model = build_judge_model(config, run_config)
    try:
        return await _evaluate(
            run_config,
            service,
            judge_model=judge_model,
            log_dir=log_dir,
        )
    finally:
        await service.aclose()


async def _evaluate(
    run_config: RunConfig,
    service: ServiceUnderTest,
    *,
    judge_model: str | Model | None = None,
    log_dir: str | None,
) -> list[EvalLog]:
    task = service_eval(run_config, service)
    # Повторы одного сэмпла — эпохи Inspect, а не дубли в датасете: так сэмпл
    # остаётся единицей анализа, а редьюсер сводит эпохи сам.
    epochs = (
        Epochs(run_config.epochs, run_config.epochs_reducer)
        if run_config.epochs > 1
        else None
    )
    return await inspect_eval(
        task,
        model=judge_model or run_config.judge.model,
        log_dir=log_dir or "logs",
        epochs=epochs,
        tags=run_config.tags or None,
        max_connections=run_config.judge.max_connections,
        temperature=run_config.judge.temperature,
        max_tokens=run_config.judge.max_tokens,
    )

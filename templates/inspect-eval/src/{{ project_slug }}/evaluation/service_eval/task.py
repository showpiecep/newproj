"""Сборка задачи: датасет + тестируемый сервис + судья + метрики + вьюер."""

from __future__ import annotations

from inspect_ai import Task

from ...application.interfaces import ServiceUnderTest
from ..configuration.run import RunConfig
from ..scoring.judge import judge_scorer
from ..scoring.values import OVERALL_KEY
from ..scoring.viewer import score_view
from .dataset import service_dataset
from .solver import service_answer_solver

SCORER_NAME = "judge"
"""Имя, под которым зарегистрирован scorer: ключ в `sample.scores` и адрес его
колонок во вьюере. Меняя его, поправьте и конфигурацию вьюера."""


def service_eval(config: RunConfig, service: ServiceUnderTest) -> Task:
    """Задача: прогнать датасет через сервис и оценить ответы судьёй."""
    criteria = [criterion.name for criterion in config.criteria]

    return Task(
        dataset=service_dataset(config.dataset, limit=config.limit),
        solver=service_answer_solver(service),
        scorer=judge_scorer(
            config.criteria,
            prompt_version=config.prompt_version,
        ),
        viewer=score_view(
            SCORER_NAME,
            [OVERALL_KEY, *criteria],
            labels={criterion.name: criterion.label for criterion in config.criteria},
        ),
        name=config.task_name,
        # Метаданные прогона: без модели судьи и версии промпта два лога
        # невозможно сравнить осмысленно.
        metadata={
            "judge_model": config.judge.model,
            "prompt_version": config.prompt_version,
            "dataset": str(config.dataset),
            "criteria": criteria,
        },
    )

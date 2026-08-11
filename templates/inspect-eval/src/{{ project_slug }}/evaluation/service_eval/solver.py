"""Solver: спросить тестируемый сервис, затем оценить ответ судьёй.

Оба шага живут в solver'е сознательно. Вызов LLM из solver'а попадает в
транскрипт отдельной веткой, поэтому в логе видно, что именно судья читал и что
ответил; scorer при этом остаётся детерминированным и не тратит токены, когда
лог переоценивают через `inspect score`.
"""

from __future__ import annotations

from collections.abc import Sequence

from inspect_ai.model import ChatMessageSystem, ChatMessageUser, get_model
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import span

from ...application.interfaces import ServiceRequest, ServiceUnderTest
from ...domain.judge import JudgeParseError, parse_judge_response
from ...prompts import render_prompt
from ..configuration.run import CriterionSpec
from ..scoring.store import JudgeStore
from .dataset import GROUP_METADATA_KEY


@solver
def service_answer_solver(service: ServiceUnderTest) -> Solver:
    """Кладёт в store ответ тестируемого сервиса.

    Инфраструктурная ошибка не гасится: сэмпл падает, Inspect видит ошибку и
    может сделать retry или resume. Гасить её здесь значит записать пустой
    ответ как результат измерения.
    """

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        store = state.store_as(JudgeStore)
        request = ServiceRequest(
            sample_id=str(state.sample_id),
            question=str(state.input_text),
            context=dict(state.metadata.get("context") or {}),
        )
        async with span("service", type="service_under_test"):
            answer = await service.answer(request)

        store.answer = answer.text
        store.service_raw = dict(answer.raw)
        state.messages.append(ChatMessageUser(content=request.question))
        return state

    return solve


@solver
def judge_solver(
    criteria: Sequence[CriterionSpec],
    *,
    prompt_version: str,
    judge_model: str,
) -> Solver:
    """Оценивает ответ из store судьёй и кладёт разобранный вердикт обратно.

    Ошибка судьи записывается в store и делает сэмпл неоценённым, а не нулевым:
    «мы не смогли измерить» и «сервис ответил плохо» — разные события, и
    смешивать их значит занижать итог из-за собственной инфраструктуры.
    """

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        store = state.store_as(JudgeStore)
        if store.answer is None:
            store.error = "Ответ сервиса отсутствует"
            store.error_type = "MissingServiceAnswer"
            return state

        rendered = [
            ChatMessageSystem(content=render_prompt("judge", prompt_version, "system")),
            ChatMessageUser(
                content=render_prompt(
                    "judge",
                    prompt_version,
                    "user",
                    question=str(state.input_text),
                    answer=store.answer,
                    reference=state.target.text or None,
                    criteria=[criterion.model_dump() for criterion in criteria],
                )
            ),
        ]

        async with span("judge", type="judge"):
            output = await get_model(judge_model).generate(rendered)

        try:
            store.verdict = parse_judge_response(output.completion)
        except JudgeParseError as error:
            store.error = str(error)
            store.error_type = type(error).__name__
        return state

    return solve


def group_of(state: TaskState) -> str:
    """Категория сэмпла — для разрезов метрик и кластерной погрешности."""
    return str(state.metadata.get(GROUP_METADATA_KEY) or "—")

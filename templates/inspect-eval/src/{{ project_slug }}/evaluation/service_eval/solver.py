"""Solver: получить оцениваемый ответ от тестируемого сервиса."""

from __future__ import annotations

from inspect_ai.model import ChatMessageUser
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import span

from ...application.interfaces import ServiceRequest, ServiceUnderTest
from ..scoring.store import JudgeStore


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

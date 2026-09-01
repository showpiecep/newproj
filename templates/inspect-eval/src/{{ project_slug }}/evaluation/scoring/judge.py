"""Scorer на LLM-судье, общий для задач проекта."""

from __future__ import annotations

from collections.abc import Sequence

from inspect_ai.model import ChatMessageSystem, ChatMessageUser, get_model
from inspect_ai.scorer import Score, Scorer, Target, mean, scorer, stderr
from inspect_ai.solver import TaskState
from inspect_ai.util import span

from ...domain.judge import JudgeParseError, parse_judge_response
from ...prompts import render_prompt
from ..configuration.run import CriterionSpec
from .store import JudgeStore
from .values import OVERALL_KEY, score_value


def judge_scorer(
    criteria: Sequence[CriterionSpec],
    *,
    prompt_version: str,
) -> Scorer:
    """Оценивает сохранённый ответ судьёй и возвращает словарный `Score`.

    Args:
        criteria: критерии прогона. Их имена задают набор
            ключей значения, одинаковый у всех сэмплов, и число метрик в шапке.
            Именно поэтому набор берётся из конфигурации, а не из того, что
            судья вернул на конкретном сэмпле.

    Метрики объявлены словарём, поэтому Inspect создаёт `EvalScore` на каждый
    ключ: шапка читается таблицей «критерий × mean/stderr», а число метрик
    определяется списком критериев и не растёт вместе с датасетом.
    """
    criterion_names = [criterion.name for criterion in criteria]
    keys = [OVERALL_KEY, *criterion_names]

    @scorer(metrics={key: [mean(), stderr()] for key in keys})
    def judge() -> Scorer:
        async def score(state: TaskState, target: Target) -> Score:
            store = state.store_as(JudgeStore)

            if store.answer is None:
                return Score.unscored(
                    explanation="Оценка не получена: ответ сервиса отсутствует",
                    metadata={"error_type": "MissingServiceAnswer"},
                )

            rendered = [
                ChatMessageSystem(content=render_prompt("judge", prompt_version, "system")),
                ChatMessageUser(
                    content=render_prompt(
                        "judge",
                        prompt_version,
                        "user",
                        criteria=[criterion.model_dump() for criterion in criteria],
                        question=str(state.input_text),
                        answer=store.answer,
                        reference=target.text or None,
                    )
                ),
            ]

            async with span("judge", type="judge"):
                output = await get_model().generate(rendered)

            try:
                verdict = parse_judge_response(output.completion)
            except JudgeParseError as error:
                return Score.unscored(
                    explanation=f"Оценка не получена: {error}",
                    metadata={
                        "error": str(error),
                        "error_type": type(error).__name__,
                        "judge_raw": output.completion,
                        "service_raw": store.service_raw,
                    },
                )

            scores = verdict.scores()
            return Score(
                value=score_value(scores, criterion_names),
                answer=store.answer,
                explanation="\n".join(
                    f"• {item.criterion}={item.score:.2f} — {item.reasoning}"
                    for item in verdict.criteria
                ),
                metadata={
                    "criteria_scores": scores,
                    "criteria_verdicts": [item.model_dump() for item in verdict.criteria],
                    "judge_raw": output.completion,
                    "service_raw": store.service_raw,
                },
            )

        return score

    return judge()

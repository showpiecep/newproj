"""Scorer на LLM-судье, общий для задач проекта.

Судья вызывается в solver'е (см. `service_eval/solver.py`), а scorer остаётся
детерминированным адаптером «store -> Score». Так каждый вызов судьи виден
отдельной веткой транскрипта, а переоценка готового лога через `inspect score`
не требует повторного прогона тестируемого сервиса.
"""

from __future__ import annotations

from collections.abc import Sequence

from inspect_ai.scorer import Score, Scorer, Target, mean, scorer, stderr
from inspect_ai.solver import TaskState

from .store import JudgeStore
from .values import OVERALL_KEY, score_value


def judge_scorer(criteria: Sequence[str]) -> Scorer:
    """Переводит вердикт судьи из store в `Score` со словарным значением.

    Args:
        criteria: имена критериев прогона. Это контракт задачи: он задаёт набор
            ключей значения, одинаковый у всех сэмплов, и число метрик в шапке.
            Именно поэтому набор берётся из конфигурации, а не из того, что
            судья вернул на конкретном сэмпле.

    Метрики объявлены словарём, поэтому Inspect создаёт `EvalScore` на каждый
    ключ: шапка читается таблицей «критерий × mean/stderr», а число метрик
    определяется списком критериев и не растёт вместе с датасетом.
    """
    keys = [OVERALL_KEY, *criteria]

    @scorer(metrics={key: [mean(), stderr()] for key in keys})
    def judge() -> Scorer:
        async def score(state: TaskState, target: Target) -> Score:
            store = state.store_as(JudgeStore)

            if store.error is not None or store.verdict is None:
                # Завершённый, но неизмеримый сэмпл: nan, а не ноль. Ноль
                # означал бы «сервис ответил плохо» и занизил бы оценку из-за
                # нашей же инфраструктуры.
                return Score.unscored(
                    explanation=f"Оценка не получена: {store.error}",
                    metadata={"error": store.error, "error_type": store.error_type},
                )

            scores = store.verdict.scores()
            return Score(
                value=score_value(scores, criteria),
                answer=store.answer,
                explanation="\n".join(
                    f"• {verdict.criterion}={verdict.score:.2f} — {verdict.reasoning}"
                    for verdict in store.verdict.criteria
                ),
                metadata={
                    "criteria_scores": scores,
                    "criteria_verdicts": [v.model_dump() for v in store.verdict.criteria],
                    "service_raw": store.service_raw,
                },
            )

        return score

    return judge()

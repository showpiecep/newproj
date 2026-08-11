"""Сборка словарного значения `Score` — общая для всех задач проекта.

Значение score делается словарём, а не числом: тогда Inspect создаёт отдельный
`EvalScore` на каждый ключ и рисует шапку прогона таблицей «ключ × mean/stderr»,
а не стеной плиток. Здесь же живут два инварианта, которые легко нарушить и
дорого чинить:

* набор ключей одинаков у всех сэмплов — иначе Inspect роняет весь прогон на
  этапе подсчёта результатов, уже после того, как судья отработал;
* сводный балл идёт первым ключом — порядок ключей задаёт порядок строк.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from inspect_ai.scorer import Score

OVERALL_KEY = "overall"
"""Ключ сводного балла сэмпла. Первый в словаре, потому что его читают первым."""


def score_value(
    scores: Mapping[str, float],
    keys: Sequence[str],
    *,
    overall: float | None = None,
) -> dict[str, float]:
    """Словарь значения score: сводный балл плюс по одному ключу на измерение.

    Args:
        scores: измеренные значения, ключ → балл. Может быть неполным.
        keys: полный набор ключей, который обязан быть у каждого сэмпла —
            список критериев, стороны дуэли, пункты чек-листа. Задаётся
            контрактом задачи, а не данными конкретного сэмпла.
        overall: сводный балл. По умолчанию — среднее измеренных значений.

    Отсутствующий ключ попадает в значение как `nan`: это штатный сентинел,
    который агрегаторы Inspect пропускают, в отличие от нуля — ноль означал бы
    «система ответила плохо», а не «мы не смогли измерить».
    """
    measured = [float(v) for v in scores.values() if not math.isnan(float(v))]
    if overall is None:
        overall = sum(measured) / len(measured) if measured else math.nan

    value: dict[str, float] = {OVERALL_KEY: round(overall, 3)}
    for key in keys:
        raw = scores.get(key)
        value[key] = math.nan if raw is None else round(float(raw), 3)
    return value


def overall_score(score: Score | None) -> float | None:
    """Одно число сэмпла, `None` если его нет.

    `Score.as_float()` на словаре не работает, поэтому всякий код, которому
    нужен один балл — экспорт, отчёты, валидаторы артефактов, ответ API, —
    обязан ходить сюда, а не разбирать значение сам.
    """
    if score is None:
        return None
    value = score.value
    if isinstance(value, dict):
        value = value.get(OVERALL_KEY)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return None if math.isnan(float(value)) else float(value)

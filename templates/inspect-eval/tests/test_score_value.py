"""Инварианты словарного значения score.

Оба проверяемых правила ломаются молча и дорого: расхождение набора ключей
роняет прогон на подсчёте результатов, когда судья уже отработал, а порядок
ключей задаёт порядок строк в шапке.
"""

import math

from inspect_ai.scorer import Score

from {{ project_slug }}.evaluation.scoring.values import (
    OVERALL_KEY,
    overall_score,
    score_value,
)

CRITERIA = ["relevance", "factual_accuracy", "completeness"]


def test_missing_criterion_stays_as_nan() -> None:
    value = score_value({"relevance": 100.0, "completeness": 50.0}, CRITERIA)

    assert set(value) == {OVERALL_KEY, *CRITERIA}
    assert math.isnan(value["factual_accuracy"])


def test_overall_is_the_first_key() -> None:
    value = score_value({"relevance": 100.0}, ["aaa_first_alphabetically", "relevance"])

    assert next(iter(value)) == OVERALL_KEY


def test_overall_ignores_unmeasured_criteria() -> None:
    value = score_value({"relevance": 100.0, "completeness": 50.0}, CRITERIA)

    assert value[OVERALL_KEY] == 75.0


def test_overall_score_reads_dict_and_scalar() -> None:
    assert overall_score(Score(value={OVERALL_KEY: 40.0, "relevance": 100.0})) == 40.0
    assert overall_score(Score(value=40.0)) == 40.0
    assert overall_score(Score(value=float("nan"))) is None
    assert overall_score(None) is None

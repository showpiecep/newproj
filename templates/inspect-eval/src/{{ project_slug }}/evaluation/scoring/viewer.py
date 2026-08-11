"""Настройка Inspect View для задач проекта.

Вьюер не обязан угадывать, как читать оценки: словарное значение score даёт
колонку на каждый ключ, и без настройки это широкая таблица с полными именами
ключей в заголовках и подкраской по наблюдаемому диапазону. Здесь задаются
короткие заголовки, шкала, прибитая к контракту оценки, и сортировка худшими
вверх — смотреть идут на плохое.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from inspect_ai.viewer import (
    SampleScoreView,
    SampleScoreViewSort,
    ScoreColorScale,
    TaskSamplesColumn,
    TaskSamplesSort,
    TaskSamplesView,
    ViewerConfig,
)

from .values import OVERALL_KEY

_EMPTY_COLUMNS = ("target", "answer")
"""Колонки, которые задача-replay всегда оставляет пустыми."""

_BULKY_COLUMNS = ("tokens", "duration")
"""Полезны, но съедают ширину: включаются в меню «Columns» вьюера."""


def short_label(key: str) -> str:
    """Короткий заголовок колонки для ключа оценки.

    Полное имя критерия в колонку не влезает, а инициалы влезают. Сам ключ при
    этом остаётся полным именем: сокращение живёт только в интерфейсе.
    """
    if key == OVERALL_KEY:
        return "Overall"
    words = key.split("_")
    if len(words) == 1:
        return words[0].capitalize()
    return "".join(word[:1].upper() for word in words)


def score_view(
    scorer_name: str,
    score_keys: Sequence[str],
    *,
    name: str = "Оценки",
    labels: Mapping[str, str] | None = None,
    palette: str = "good-high",
    sort_key: str = OVERALL_KEY,
) -> ViewerConfig:
    """Список сэмплов для задачи со словарным значением score.

    Args:
        scorer_name: имя, под которым зарегистрирован scorer — это ключ в
            `sample.scores`, через него адресуются колонки оценок.
        score_keys: ключи значения score, по одной колонке на каждый.
        name: имя представления в переключателе вьюера.
        labels: заголовки колонок; для ключей без записи берётся `short_label`.
        palette: `good-high` для оценки 0..1, `diverging` для win rate —
            он центрируется на 0.5, то есть на паритете сторон.
        sort_key: ключ, по которому список сортируется худшими вверх.

    Шкала прибита к 0..1, а не к наблюдаемому диапазону: иначе одна и та же
    оценка красится по-разному от прогона к прогону и цвета нельзя сравнивать.
    """
    labels = dict(labels or {})
    return ViewerConfig(
        task_samples_view=TaskSamplesView(
            name=name,
            multiline=False,
            columns=[
                TaskSamplesColumn(id="sampleStatus"),
                TaskSamplesColumn(id="sampleId"),
                TaskSamplesColumn(id="input"),
                *[
                    TaskSamplesColumn(id=column, visible=False)
                    for column in (*_EMPTY_COLUMNS, *_BULKY_COLUMNS)
                ],
            ],
            score_labels={key: labels.get(key, short_label(key)) for key in score_keys},
            score_color_scales={
                key: ScoreColorScale(palette=palette, min=0.0, max=1.0)
                for key in score_keys
            },
            color_scales_enabled=True,
            sort=[TaskSamplesSort.score(scorer_name, sort_key, dir="asc")],
        ),
        # Панель оценок сэмпла появляется от трёх оценок; таблицей она читается
        # лучше россыпи «пилюль», а сортировка по значению поднимает наверх то,
        # из-за чего сэмпл просел.
        sample_score_view=SampleScoreView(
            default="grid",
            sort=SampleScoreViewSort(column="value", dir="asc"),
        ),
    )

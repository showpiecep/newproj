"""Модели вердикта судьи и разбор его ответа.

Домен: не зависит ни от Inspect AI, ни от конкретной LLM, ни от способа, каким
получен текст ответа. Здесь описано только то, что считается корректным
вердиктом и как из сырого текста получить проверенный объект.
"""

from __future__ import annotations

import json

from json_repair import repair_json
from pydantic import BaseModel, Field, ValidationError


class JudgeParseError(ValueError):
    """Ответ судьи не удалось привести к контракту вердикта."""


class CriterionVerdict(BaseModel):
    """Оценка одного критерия."""

    model_config = {"extra": "forbid"}

    criterion: str
    reasoning: str = ""
    score: float = Field(ge=0.0, le=100.0)


class JudgeVerdict(BaseModel):
    """Полный ответ судьи по одному сэмплу."""

    model_config = {"extra": "forbid"}

    criteria: list[CriterionVerdict] = Field(min_length=1)

    def scores(self) -> dict[str, float]:
        """Оценки по критериям, имя → балл."""
        return {verdict.criterion: verdict.score for verdict in self.criteria}


def parse_judge_response(raw: str) -> JudgeVerdict:
    """Разбирает ответ судьи: сначала строгий JSON, затем починка.

    Порядок важен: `json_repair` чинит синтаксис, но ничего не знает о смысле,
    поэтому результат в любом случае проходит валидацию контракта. Успешная
    починка не является подтверждением того, что судья ответил осмысленно.
    """
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = repair_json(raw, return_objects=True)

    if not isinstance(payload, dict):
        raise JudgeParseError(f"Ожидался JSON-объект, получено {type(payload).__name__}")

    try:
        return JudgeVerdict.model_validate(payload)
    except ValidationError as error:
        raise JudgeParseError(f"Вердикт не соответствует контракту: {error}") from error

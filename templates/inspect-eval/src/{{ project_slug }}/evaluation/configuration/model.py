"""Профиль модели-судьи.

Отдельный неизменяемый файл на профиль: судья — это часть измерительного
прибора, и его смена обязана быть видимым событием в истории, а не правкой
одной строки внутри конфига прогона.
"""

from __future__ import annotations

from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, Field


class JudgeModelProfile(BaseModel):
    """Модель судьи и параметры её вызова."""

    model_config = {"extra": "forbid", "frozen": True}

    model: str
    """Идентификатор модели в нотации Inspect AI, например `openai/gpt-4o`."""

    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1)
    max_connections: int | None = Field(default=None, ge=1)

    @classmethod
    def load(cls, path: str | Path) -> Self:
        config_path = Path(path)
        if not config_path.is_file():
            raise FileNotFoundError(f"Профиль судьи не найден: {config_path}")
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        return cls.model_validate(raw)

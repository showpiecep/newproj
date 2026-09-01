"""Типизированный store: solver -> scorer.

`StoreModel` вместо свободного словаря, потому что содержимое store попадает в
лог и читается инструментами анализа: контракт должен быть явным.
"""

from __future__ import annotations

from inspect_ai.util import StoreModel
from pydantic import Field


class JudgeStore(StoreModel):
    """Оцениваемый ответ тестируемого сервиса."""

    answer: str | None = Field(default=None)
    service_raw: dict = Field(default_factory=dict)

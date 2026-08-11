"""Типизированный store: solver -> scorer.

`StoreModel` вместо свободного словаря, потому что содержимое store попадает в
лог и читается инструментами анализа: контракт должен быть явным.
"""

from __future__ import annotations

from inspect_ai.util import StoreModel
from pydantic import Field

from ...domain.judge import JudgeVerdict


class JudgeStore(StoreModel):
    """Ответ тестируемого сервиса и вердикт судьи по нему."""

    answer: str | None = Field(default=None)
    service_raw: dict = Field(default_factory=dict)
    verdict: JudgeVerdict | None = Field(default=None)
    error: str | None = Field(default=None)
    error_type: str | None = Field(default=None)

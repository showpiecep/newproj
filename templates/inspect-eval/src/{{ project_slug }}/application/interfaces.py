"""Порт тестируемого сервиса.

Задача не должна знать, каким протоколом добывается ответ: HTTP, Kafka, локальный
процесс или запись из архива — это детали инфраструктуры. Solver зависит только
от этого интерфейса, реализация подставляется при сборке задачи.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class ServiceRequest(BaseModel):
    """Вход тестируемого сервиса."""

    model_config = {"extra": "forbid", "frozen": True}

    sample_id: str
    question: str
    context: dict[str, object] = {}


class ServiceAnswer(BaseModel):
    """Ответ тестируемого сервиса.

    `raw` хранится целиком: при разборе плохого прогона нужен именно исходный
    ответ, а не то, что из него удалось вытащить.
    """

    model_config = {"extra": "forbid", "frozen": True}

    text: str
    raw: dict[str, object] = {}


class ServiceUnderTest(ABC):
    """Тестируемый сервис.

    Реализация обязана поднимать исключение при инфраструктурной ошибке, а не
    возвращать пустой ответ: Inspect должен увидеть ошибку сэмпла и получить
    возможность сделать retry, вместо того чтобы записать пустоту как результат.
    """

    @abstractmethod
    async def answer(self, request: ServiceRequest) -> ServiceAnswer:
        """Возвращает ответ сервиса на один запрос."""

    async def aclose(self) -> None:  # noqa: B027 - необязательный хук, не абстрактный
        """Освобождает ресурсы реализации.

        Пустой по умолчанию: реализации без соединений и файлов не должны быть
        обязаны его определять.
        """

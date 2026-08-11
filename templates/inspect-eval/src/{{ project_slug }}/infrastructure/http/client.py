"""HTTP-реализация порта тестируемого сервиса."""

from __future__ import annotations

from typing import Any

import httpx

from ...application.interfaces import ServiceAnswer, ServiceRequest, ServiceUnderTest


class HttpServiceUnderTest(ServiceUnderTest):
    """Тестируемый сервис за JSON-эндпоинтом.

    Ошибки сети и статусы не 2xx намеренно пробрасываются наружу: сэмпл должен
    завершиться ошибкой, чтобы Inspect мог его перезапустить, а не получить
    пустой ответ и записать его как результат.
    """

    def __init__(
        self,
        url: str,
        *,
        timeout: float = 60.0,
        answer_field: str = "answer",
        headers: dict[str, str] | None = None,
    ) -> None:
        self._url = url
        self._answer_field = answer_field
        self._client = httpx.AsyncClient(timeout=timeout, headers=headers)

    async def answer(self, request: ServiceRequest) -> ServiceAnswer:
        response = await self._client.post(self._url, json=self._payload(request))
        response.raise_for_status()
        body: Any = response.json()
        if not isinstance(body, dict):
            raise TypeError(f"Ожидался JSON-объект, получено {type(body).__name__}")
        return ServiceAnswer(text=str(body.get(self._answer_field, "")), raw=body)

    async def aclose(self) -> None:
        await self._client.aclose()

    def _payload(self, request: ServiceRequest) -> dict[str, object]:
        return {"question": request.question, **request.context}

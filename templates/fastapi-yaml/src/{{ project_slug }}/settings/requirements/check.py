"""Проверка, что обязательные поля конфигурации действительно заполнены.

Пустое значение и плейсхолдер вида `<api_key>` проходят валидацию типов: строка
остаётся строкой. Приложение с таким конфигом стартует и падает позже — на
первом обращении к внешней системе, уже в середине работы. Поэтому конфиг
проверяется на заполненность сразу после загрузки, до любых соединений.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, SecretStr

from .fields import is_must_be_filled


@dataclass(frozen=True)
class UnfilledField:
    """Обязательное поле конфигурации, значение которого не вписали."""

    path: str
    why: str
    value: str

    def __str__(self) -> str:
        return f"  {self.path} — {self.why}\n      сейчас: {self.value}"


class UnfilledSettingsError(Exception):
    """Конфигурация загрузилась, но обязательные поля остались незаполненными."""

    def __init__(self, fields: list[UnfilledField], path: str) -> None:
        self.fields = fields
        self.path = path
        super().__init__(str(self))

    def __str__(self) -> str:
        listing = "\n".join(str(field) for field in self.fields)
        return (
            f"{self.path} заполнен не полностью:\n{listing}\nЗаполните эти поля и повторите запуск."
        )


def unfilled_fields(settings: BaseModel, prefix: str = "") -> list[UnfilledField]:
    """Обязательные поля без значения. Пустой список — конфигурация пригодна."""
    found: list[UnfilledField] = []

    for name, field in type(settings).model_fields.items():
        value = getattr(settings, name)
        path = f"{prefix}{name}"

        if isinstance(value, BaseModel):
            found += unfilled_fields(value, f"{path}.")
            continue

        if not is_must_be_filled(field):
            continue

        unfilled = _unfilled_reason(value, name)
        if unfilled is not None:
            found.append(UnfilledField(path, field.description or "обязательное поле", unfilled))

    return found


def _unfilled_reason(value: object, name: str) -> str | None:
    """Чем значение выдаёт себя как невписанное. None — значение настоящее."""
    text = value.get_secret_value() if isinstance(value, SecretStr) else value
    if not isinstance(text, str):
        return None

    if not text.strip():
        return "пустое значение"
    # Шаблон конфигурации подставляет сюда `<имя_поля>`; значит, файл скопировали,
    # а значение не вписали.
    if text == f"<{name}>":
        return f'незаполненный плейсхолдер "{text}"'

    return None

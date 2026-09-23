"""Объявление полей, значение которых обязан вписать оператор."""

from __future__ import annotations

from typing import Any

from pydantic import Field
from pydantic.fields import FieldInfo

# Ключ в json_schema_extra: попадает и в config.schema.json, поэтому редактор
# тоже видит, что поле требует заполнения.
MUST_BE_FILLED = "mustBeFilled"


def must_be_filled(default: Any, why: str) -> FieldInfo:
    """Поле, без корректного значения которого приложение работать не будет.

    `why` объясняет последствие, а не повторяет имя поля: оно попадает в
    сообщение об ошибке и в описание поля в JSON Schema, и читать его будет
    тот, кто собирает `config.yaml` и про устройство приложения не знает.
    """
    return Field(default=default, description=why, json_schema_extra={MUST_BE_FILLED: True})


def is_must_be_filled(field: FieldInfo) -> bool:
    """Обязан ли оператор вписать значение поля.

    Кроме помеченных `must_be_filled`, это поля без значения по умолчанию: их
    тоже нельзя оставить плейсхолдером из шаблона.
    """
    extra = field.json_schema_extra
    marked = isinstance(extra, dict) and bool(extra.get(MUST_BE_FILLED))
    return marked or field.is_required()

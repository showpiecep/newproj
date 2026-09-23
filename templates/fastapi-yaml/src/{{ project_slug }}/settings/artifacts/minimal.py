"""Минимальный `config.yaml`: только то, что нужно вписать руками.

В файл попадают секреты, поля без значения по умолчанию и поля, помеченные
`must_be_filled`. Остальное приложение берёт из умолчаний моделей настроек: в
локальном конфиге видно только то, что задано осознанно, а новые умолчания
подхватываются без правки файла. Полный список полей — `config.template.yaml`.
"""

import json
from pathlib import Path

from pydantic import BaseModel, SecretStr
from pydantic.fields import FieldInfo

from ..requirements import is_must_be_filled
from .template import SCHEMA_HEADER

MINIMAL_CONFIG_HEADER = (
    SCHEMA_HEADER
    + "# Локальный конфиг: только секреты и обязательные поля.\n"
    + "# Остальные поля берутся из умолчаний моделей настроек; полный список\n"
    + "# с умолчаниями — config.template.yaml, автодополнение — по config.schema.json.\n"
)


def render_minimal_config(model: type[BaseModel]) -> str:
    lines = _section_lines(model, indent=0)
    body = "\n" + "\n".join(lines) + "\n" if lines else ""
    return MINIMAL_CONFIG_HEADER + body


def write_minimal_config(model: type[BaseModel], path: str | Path) -> None:
    Path(path).write_text(render_minimal_config(model), encoding="utf-8")


def _section_lines(model: type[BaseModel], indent: int) -> list[str]:
    padding = "  " * indent
    lines: list[str] = []

    for name, field in model.model_fields.items():
        if _is_section(field):
            # Секция без обязательных полей в файл не попадает целиком.
            nested = _section_lines(field.annotation, indent + 1)
            if nested:
                lines += [f"{padding}{name}:", *nested]
        elif _needs_value(field):
            lines += [f"{padding}# {line}" for line in (field.description or "").splitlines()]
            lines.append(f"{padding}{name}: {_placeholder(name, field)}")

    return lines


def _is_section(field: FieldInfo) -> bool:
    return isinstance(field.annotation, type) and issubclass(field.annotation, BaseModel)


def _needs_value(field: FieldInfo) -> bool:
    return is_must_be_filled(field) or field.annotation is SecretStr


def _placeholder(name: str, field: FieldInfo) -> str:
    # Необязательный секрет пустым означает «не задан», и конфиг с ним валиден.
    # Обязательное значение угадать нельзя: плейсхолдер `<имя>` остаётся, и
    # проверка при загрузке назовёт поле, если его не заполнят.
    if field.annotation is SecretStr and not is_must_be_filled(field):
        return '""'
    return json.dumps(f"<{name}>", ensure_ascii=False)

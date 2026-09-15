"""Генерация шаблона мастер-конфига и его JSON Schema по моделям настроек."""

from __future__ import annotations

from pathlib import Path

from ..settings import Config
from ..settings.artifacts import config_artifacts_problems, write_config_artifacts


def write_template(path: str | Path) -> None:
    """Пересобирает `config.template.yaml` и `config.schema.json` рядом с ним.

    Оба файла генерируются, а не правятся руками: иначе они расходятся с моделями,
    и новый разработчик получает конфиг, который не проходит валидацию, а редактор —
    схему, которая подсвечивает не те поля.
    """
    write_config_artifacts(Config, path)


def check_template(path: str | Path) -> list[str]:
    """Чем шаблон и схема в рабочей копии расходятся с моделями настроек.

    Артефакты пересобираются командой, а значит могут отстать: в коммит попадает то,
    что лежит в рабочей копии. Пустой список — расхождений нет.
    """
    return config_artifacts_problems(Config, path)

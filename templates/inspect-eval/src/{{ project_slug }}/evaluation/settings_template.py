"""Генерация шаблона мастер-конфига по моделям настроек."""

from __future__ import annotations

from pathlib import Path

from ..settings import Config
from ..settings.template import template_problems, write_config_template


def write_template(path: str | Path) -> None:
    """Пересобирает `config.template.yaml` из текущих моделей настроек.

    Шаблон генерируется, а не правится руками: иначе он расходится с моделями,
    и новый разработчик получает конфиг, который не проходит валидацию.
    """
    write_config_template(Config, path)


def check_template(path: str | Path) -> list[str]:
    """Чем `config.template.yaml` в рабочей копии расходится с моделями настроек.

    Шаблон пересобирается командой, а значит может отстать: в коммит попадает то,
    что лежит в рабочей копии. Пустой список — расхождений нет.
    """
    return template_problems(Config, path)

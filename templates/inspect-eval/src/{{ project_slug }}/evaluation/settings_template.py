"""Генерация шаблона мастер-конфига по моделям настроек."""

from __future__ import annotations

from pathlib import Path

from ..settings import Config
from ..settings.template import write_config_template


def write_template(path: str | Path) -> None:
    """Пересобирает `config.template.yaml` из текущих моделей настроек.

    Шаблон генерируется, а не правится руками: иначе он расходится с моделями,
    и новый разработчик получает конфиг, который не проходит валидацию.
    """
    write_config_template(Config, path)

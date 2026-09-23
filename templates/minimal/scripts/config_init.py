"""Создание минимального локального config.yaml из моделей настроек.

В файл попадают только секреты и обязательные поля, остальное приложение берёт
из умолчаний. Существующий конфиг не перезаписывается: в нём секреты. Полная
копия шаблона со всеми полями — `cp config.template.yaml config.yaml`.
"""

import argparse
import sys
from pathlib import Path

from {{ project_slug }}.settings import Config
from {{ project_slug }}.settings.artifacts.minimal import write_minimal_config

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, nargs="?", default=PROJECT_ROOT / "config.yaml")
    arguments = parser.parse_args()

    if arguments.path.exists():
        print(f"{arguments.path.name} уже существует — не перезаписываю")
        return 0

    write_minimal_config(Config, arguments.path)
    # Только владельцу: в файле секреты. На Windows chmod снимает лишь флаг
    # «только чтение», чего здесь и достаточно.
    arguments.path.chmod(0o600)
    print(f"Создан минимальный конфиг: {arguments.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

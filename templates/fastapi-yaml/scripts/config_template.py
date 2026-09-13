"""Поддержка config.template.yaml в актуальном состоянии.

Без аргументов сверяет шаблон с моделями настроек и завершается с кодом 1, если
они разошлись; с `--write` пересобирает шаблон из значений по умолчанию.

Сверка запускается на коммите (см. `.pre-commit-config.yaml`) и из
`make config-check`: приложение перезаписывает шаблон при старте, но в коммит
попадает то, что лежит в рабочей копии, а не то, что появится после запуска.
"""

import argparse
import sys
from pathlib import Path

from {{ project_slug }}.settings import Config
from {{ project_slug }}.settings.template import template_problems, write_config_template

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = PROJECT_ROOT / "config.template.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="пересобрать шаблон")
    parser.add_argument("--path", type=Path, default=TEMPLATE_PATH, help="файл шаблона")
    arguments = parser.parse_args()

    if arguments.write:
        write_config_template(Config, arguments.path)
        print(f"Шаблон пересобран: {arguments.path}")
        return 0

    problems = template_problems(Config, arguments.path)
    if not problems:
        print(f"{arguments.path.name}: актуален")
        return 0

    print(f"{arguments.path.name} разошёлся с настройками:")
    for problem in problems:
        print(f"  - {problem}")
    print("\nПересобрать: make config-template")
    return 1


if __name__ == "__main__":
    sys.exit(main())

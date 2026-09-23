"""Поддержка config.template.yaml и config.schema.json в актуальном состоянии.

С `--write` пересобирает шаблон и JSON Schema из моделей настроек; без аргументов
только сверяет их с моделями и завершается с кодом 1, если они разошлись.

На коммите (см. `.pre-commit-config.yaml`) запускается `--write`: если файлы
изменились, pre-commit останавливает коммит, а обновлённые артефакты остаётся
добавить. Сверка без записи — для `make config-check` и CI.
"""

import argparse
import sys
from pathlib import Path

from {{ project_slug }}.settings import Config
from {{ project_slug }}.settings.artifacts import config_artifacts_problems, write_config_artifacts

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = PROJECT_ROOT / "config.template.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="пересобрать шаблон и схему")
    parser.add_argument("--path", type=Path, default=TEMPLATE_PATH, help="файл шаблона")
    arguments = parser.parse_args()

    if arguments.write:
        write_config_artifacts(Config, arguments.path)
        print(f"Шаблон и схема пересобраны: {arguments.path.parent}")
        return 0

    problems = config_artifacts_problems(Config, arguments.path)
    if not problems:
        print(f"{arguments.path.name} и схема: актуальны")
        return 0

    print("Шаблон и схема конфига разошлись с настройками:")
    for problem in problems:
        print(f"  - {problem}")
    print("\nПересобрать: make config-template")
    return 1


if __name__ == "__main__":
    sys.exit(main())

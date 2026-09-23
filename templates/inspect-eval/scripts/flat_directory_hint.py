"""Подсказка о плоских директориях: много файлов одного расширения на одном уровне.

Хук pre-commit вызывает скрипт с изменёнными файлами и смотрит на директории,
которых коснулся коммит. Скрипт только предупреждает и всегда завершается
успешно: число файлов — признак, а не правило. Решение о группировке принимает
автор, исходя из того, об одном ли эти файлы.
"""

from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_MAX_FILES = 5
# Служебные файлы пакета есть в каждой директории и о структуре ничего не говорят.
IGNORED_NAMES = frozenset({"__init__.py", "__main__.py", "conftest.py", "py.typed"})


def main(argv: list[str] | None = None) -> int:
    arguments = _parse_arguments(argv)

    crowded = _crowded_groups(arguments.filenames, arguments.max_files)
    if not crowded:
        return 0

    print("Много файлов одного расширения в одной директории:")
    for directory, extension, count in crowded:
        print(f"  {directory} — {count} файлов {extension} (порог {arguments.max_files})")
    print(
        "Если часть из них об одном, им место в поддиректории со своим именем.\n"
        "Это предупреждение, коммит создан."
    )
    return 0


def _parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("filenames", nargs="*", help="изменённые файлы")
    parser.add_argument(
        "--max-files",
        "--max",
        dest="max_files",
        type=int,
        default=DEFAULT_MAX_FILES,
        help=(
            "сколько файлов одного расширения допустимо в директории "
            f"(по умолчанию {DEFAULT_MAX_FILES})"
        ),
    )
    return parser.parse_args(argv)


def _crowded_groups(filenames: list[str], limit: int) -> list[tuple[Path, str, int]]:
    """Затронутые коммитом пары «директория + расширение», где файлов больше порога."""
    groups = {
        (path.parent, path.suffix)
        for path in map(Path, filenames)
        if path.suffix and path.name not in IGNORED_NAMES
    }

    crowded = []
    for directory, extension in groups:
        count = _count_files(directory, extension)
        if count > limit:
            crowded.append((directory, extension, count))

    return sorted(crowded, key=lambda group: (-group[2], str(group[0])))


def _count_files(directory: Path, extension: str) -> int:
    return sum(
        1
        for path in directory.glob(f"*{extension}")
        if path.is_file() and path.name not in IGNORED_NAMES
    )


if __name__ == "__main__":
    raise SystemExit(main())

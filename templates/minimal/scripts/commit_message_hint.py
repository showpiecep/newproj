"""Подсказка по формату сообщения коммита в стиле Conventional Commits.

Хук commit-msg вызывает скрипт с путём к файлу сообщения. Скрипт только
предупреждает и всегда завершается успешно: коммит нужно уметь сделать быстро,
а привести сообщение к формату можно и позже через `git commit --amend`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TYPES = "build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test"
PATTERN = re.compile(rf"^({TYPES})(\([^)]+\))?!?: \S.*")
# Сообщения, которые создаёт сам git, формату не подчиняются.
GENERATED = re.compile(r"^(Merge |Revert |fixup! |squash! )")


def main() -> int:
    subject = _subject(Path(sys.argv[1]))

    if not subject or GENERATED.match(subject) or PATTERN.match(subject):
        return 0

    print(
        "Сообщение коммита не в формате Conventional Commits:\n"
        f"  {subject}\n"
        f"Ожидается: <тип>(<область>)?: <описание>, тип из {TYPES}.\n"
        "Это предупреждение, коммит создан. Поправить: git commit --amend",
        file=sys.stderr,
    )
    return 0


def _subject(message_file: Path) -> str:
    """Первая непустая строка сообщения без комментариев git."""
    for line in message_file.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            return line.strip()
    return ""


if __name__ == "__main__":
    sys.exit(main())

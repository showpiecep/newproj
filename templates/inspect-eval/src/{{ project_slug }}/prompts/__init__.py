"""Загрузка версионируемых шаблонов промптов.

Тексты промптов лежат отдельными `.jinja`-файлами по версиям, а не в Python:
версия выбирается в конфигурации прогона, поэтому изменение формулировки видно
в истории отдельно от изменений кода, который делает запрос.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

_PROMPTS_ROOT = Path(__file__).parent

_environment = Environment(
    loader=FileSystemLoader(_PROMPTS_ROOT),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    autoescape=False,
)


def render_prompt(area: str, version: str, name: str, /, **values: object) -> str:
    """Рендерит `prompts/<area>/<version>/<name>.jinja`.

    `StrictUndefined`: незаполненная переменная — это ошибка шаблона, а не
    молчаливая пустая строка в промпте, которую потом ищут по логам.
    """
    template = _environment.get_template(f"{area}/{version}/{name}.jinja")
    return template.render(**values)


def prompt_versions(area: str) -> list[str]:
    """Доступные версии промптов области — для валидации конфигурации прогона."""
    area_root = _PROMPTS_ROOT / area
    if not area_root.is_dir():
        return []
    return sorted(item.name for item in area_root.iterdir() if item.is_dir())

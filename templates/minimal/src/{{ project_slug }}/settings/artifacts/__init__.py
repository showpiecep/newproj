from pathlib import Path

from pydantic import BaseModel

from .schema import CONFIG_SCHEMA_FILENAME, schema_problems, write_config_schema
from .template import template_problems, write_config_template


def schema_path_for(template_path: str | Path) -> Path:
    """Схема лежит рядом с шаблоном: на неё ссылается его первая строка."""
    return Path(template_path).parent / CONFIG_SCHEMA_FILENAME


def write_config_artifacts(model: type[BaseModel], template_path: str | Path) -> None:
    """Сгенерировать из моделей шаблон конфига и JSON Schema рядом с ним."""
    write_config_template(model, template_path)
    write_config_schema(model, schema_path_for(template_path))


def config_artifacts_problems(model: type[BaseModel], template_path: str | Path) -> list[str]:
    """Чем шаблон и схема на диске расходятся с моделями. Пустой список — актуальны."""
    return template_problems(model, template_path) + schema_problems(
        model, schema_path_for(template_path)
    )

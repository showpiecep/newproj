import json
from pathlib import Path

from pydantic import BaseModel

CONFIG_SCHEMA_FILENAME = "config.schema.json"


def render_config_schema(model: type[BaseModel]) -> str:
    """JSON Schema конфига — по ней редактор валидирует и дополняет YAML."""
    schema = model.model_json_schema()
    return json.dumps(schema, ensure_ascii=False, indent=2) + "\n"


def write_config_schema(model: type[BaseModel], path: str | Path) -> None:
    Path(path).write_text(render_config_schema(model), encoding="utf-8")


def schema_problems(model: type[BaseModel], path: str | Path) -> list[str]:
    """Чем схема на диске расходится с моделями настроек. Пустой список — актуальна."""
    file = Path(path)
    if not file.is_file():
        return [f"нет файла схемы: {file}"]
    if file.read_text(encoding="utf-8") != render_config_schema(model):
        return [f"{file.name} отстал от моделей настроек"]
    return []

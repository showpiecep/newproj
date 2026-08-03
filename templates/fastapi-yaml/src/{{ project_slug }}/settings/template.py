from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_core import PydanticUndefined


def model_to_template(model: type[BaseModel]) -> dict[str, object]:
    result: dict[str, object] = {}

    for name, field in model.model_fields.items():
        if isinstance(field.annotation, type) and issubclass(field.annotation, BaseModel):
            result[name] = model_to_template(field.annotation)
        else:
            default = field.default
            result[name] = default if default is not PydanticUndefined else f"<{name}>"

    return result


def write_config_template(
    model: type[BaseModel],
    path: str | Path,
) -> None:
    template = model_to_template(model)

    with Path(path).open("w", encoding="utf-8") as file:
        yaml.safe_dump(template, file, allow_unicode=True, sort_keys=False)

from pathlib import Path

import yaml
from pydantic import BaseModel, SecretStr, TypeAdapter
from pydantic_core import PydanticUndefined


def model_to_template(model: type[BaseModel]) -> dict[str, object]:
    result: dict[str, object] = {}

    for name, field in model.model_fields.items():
        if isinstance(field.annotation, type) and issubclass(field.annotation, BaseModel):
            result[name] = model_to_template(field.annotation)
        else:
            default = field.get_default(call_default_factory=True)
            if default is PydanticUndefined or isinstance(default, SecretStr):
                result[name] = f"<{name}>"
            else:
                result[name] = TypeAdapter(type(default)).dump_python(default, mode="json")

    return result


def write_config_template(
    model: type[BaseModel],
    path: str | Path,
) -> None:
    template = model_to_template(model)
    content = yaml.safe_dump(template, allow_unicode=True, sort_keys=False)
    Path(path).write_text(content, encoding="utf-8")

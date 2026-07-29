import yaml
from pydantic import BaseModel
from pydantic_core import PydanticUndefined


def model_to_template(model: type[BaseModel]) -> dict:
    result = {}
    for name, field in model.model_fields.items():
        if isinstance(field.annotation, type) and issubclass(
            field.annotation, BaseModel
        ):
            result[name] = model_to_template(field.annotation)
        else:
            default = field.default
            result[name] = default if default is not PydanticUndefined else f"<{name}>"
    return result


template = model_to_template(AppSettings)
with open("config.template.yaml", "w") as f:
    yaml.dump(template, f, allow_unicode=True, sort_keys=False)

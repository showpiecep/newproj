from pathlib import Path

import yaml
from pydantic import BaseModel, SecretStr, TypeAdapter
from pydantic_core import PydanticUndefined

from .schema import CONFIG_SCHEMA_FILENAME

# Ссылка для редактора (yaml-language-server); переезжает в config.yaml при копировании.
SCHEMA_HEADER = f"# yaml-language-server: $schema=./{CONFIG_SCHEMA_FILENAME}\n"


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
    Path(path).write_text(SCHEMA_HEADER + content, encoding="utf-8")


def mapping_keys(data: dict[str, object], prefix: str = "") -> set[str]:
    """Пути до значений отображения, например `app.port`.

    Пустой словарь считается значением, а не секцией: иначе поле со значением по
    умолчанию `{}` пропадает из сравнения и его отсутствие в шаблоне не видно.
    """
    keys: set[str] = set()

    for name, value in data.items():
        path = f"{prefix}{name}"
        if isinstance(value, dict) and value:
            keys |= mapping_keys(value, f"{path}.")
        else:
            keys.add(path)

    return keys


def template_problems(model: type[BaseModel], path: str | Path) -> list[str]:
    """Чем шаблон конфигурации расходится с моделями настроек.

    Шаблон — единственный документ, по которому собирают приватный `config.yaml`.
    Поле, добавленное в настройки и забытое в шаблоне, ничего не ломает у автора
    правки: у него конфиг уже заполнен. Ломается он у следующего, кто соберёт
    конфиг по шаблону, и не при чтении файла, а позже — когда прогон пойдёт не с
    тем значением. Поэтому расхождение проверяется автоматически, а не
    договорённостью не забывать.

    Пустой список означает, что расхождений нет.
    """
    file = Path(path)
    if not file.is_file():
        return [f"нет файла шаблона: {file}"]

    expected = mapping_keys(model_to_template(model))
    actual = mapping_keys(yaml.safe_load(file.read_text(encoding="utf-8")) or {})

    return [f"нет в шаблоне: {key}" for key in sorted(expected - actual)] + [
        f"лишнее в шаблоне: {key}" for key in sorted(actual - expected)
    ]

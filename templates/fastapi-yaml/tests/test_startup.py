"""Сервис должен подниматься в чистом окружении и внятно отказываться стартовать.

Незаполненный `config.yaml` — самая частая причина, по которой сервис не
работает на новой машине. Ошибка об этом должна называть поле и последствие, а
не всплывать позже отказом внешней системы.
"""

import re
from pathlib import Path

import yaml
from fastapi.testclient import TestClient
from pydantic import SecretStr

from {{ project_slug }}.application import bootstrap
from {{ project_slug }}.settings import Config, UnfilledSettingsError
from {{ project_slug }}.settings.artifacts import write_config_artifacts
from {{ project_slug }}.settings.requirements import must_be_filled, unfilled_fields
from {{ project_slug }}.settings.sections.base import Base

WHY = "ключ провайдера; без него запросы не уйдут"


class _Secrets(Base):
    api_key: SecretStr = must_be_filled(SecretStr(""), WHY)


PLACEHOLDER = re.compile(r"^<.+>$")


def _fill_placeholders(value: object) -> object:
    """Подставить значения вместо плейсхолдеров шаблона.

    Тест про запуск проверяет, что сервис поднимается с заполненным конфигом, и
    не должен ломаться от того, что в проекте появилось ещё одно обязательное
    поле: незаполненный конфиг — предмет отдельного теста.
    """
    if isinstance(value, dict):
        return {key: _fill_placeholders(item) for key, item in value.items()}
    if isinstance(value, str) and PLACEHOLDER.match(value):
        return "test-value"
    return value


def _config_from_template(tmp_path: Path, *, filled: bool) -> Path:
    """Конфиг, собранный из шаблона, — как на новой машине."""
    template_path = tmp_path / "config.template.yaml"
    write_config_artifacts(Config, template_path)

    data = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    if filled:
        data = _fill_placeholders(data)

    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return config_path


def test_service_starts_with_config_built_from_template(tmp_path: Path) -> None:
    """Путь новой машины целиком: шаблон -> config.yaml -> запуск -> ответ."""
    application = bootstrap(_config_from_template(tmp_path, filled=True))

    with TestClient(application.create_app()) as client:
        assert client.get("/docs").status_code == 200


def test_placeholder_is_reported_with_field_and_reason() -> None:
    unfilled = unfilled_fields(_Secrets(api_key=SecretStr("<api_key>")))

    assert [field.path for field in unfilled] == ["api_key"]
    assert WHY in str(unfilled[0])
    assert "плейсхолдер" in str(unfilled[0])


def test_empty_value_is_reported() -> None:
    unfilled = unfilled_fields(_Secrets(api_key=SecretStr("   ")))

    assert [field.path for field in unfilled] == ["api_key"]
    assert "пустое значение" in str(unfilled[0])


def test_filled_value_passes() -> None:
    assert unfilled_fields(_Secrets(api_key=SecretStr("real-key"))) == []


def test_error_message_names_the_file_and_what_to_do() -> None:
    error = UnfilledSettingsError(unfilled_fields(_Secrets()), "config.yaml")

    message = str(error)
    assert "config.yaml заполнен не полностью" in message
    assert "api_key" in message
    assert "Заполните эти поля" in message


def test_unmarked_field_is_not_required() -> None:
    """Проверка касается только явно помеченных полей."""

    class _Optional(Base):
        base_url: str = ""

    assert unfilled_fields(_Optional()) == []

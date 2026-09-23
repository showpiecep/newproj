"""Минимальный `config.yaml`: только то, что нужно вписать руками.

Новый пользователь заполняет секреты и обязательные поля, остальное берётся из
умолчаний моделей. Если в минимальный конфиг попадёт лишнее, умолчания в нём
застынут; если не попадёт обязательное — проект упадёт на первом запуске.
"""

import subprocess
import sys
from pathlib import Path

import yaml
from pydantic import Field, SecretStr

from {{ project_slug }}.settings import Config
from {{ project_slug }}.settings.artifacts.minimal import render_minimal_config
from {{ project_slug }}.settings.artifacts.schema import CONFIG_SCHEMA_FILENAME
from {{ project_slug }}.settings.requirements import must_be_filled, unfilled_fields
from {{ project_slug }}.settings.sections.base import Base

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_minimal_config_loads_with_defaults_only(tmp_path: Path) -> None:
    minimal_path = tmp_path / "config.yaml"
    minimal_path.write_text(render_minimal_config(Config), encoding="utf-8")
    empty_path = tmp_path / "empty.yaml"
    empty_path.write_text("{}\n", encoding="utf-8")

    # Ничего не переопределено: всё — умолчания моделей.
    assert Config.load(minimal_path).model_dump() == Config.load(empty_path).model_dump()


def test_minimal_config_points_editor_to_schema() -> None:
    assert render_minimal_config(Config).startswith(
        f"# yaml-language-server: $schema=./{CONFIG_SCHEMA_FILENAME}"
    )


def test_only_values_to_fill_by_hand_are_listed() -> None:
    class Section(Base):
        endpoint: str = Field(description="Адрес сервиса.")
        api_key: SecretStr = must_be_filled(SecretStr(""), "без ключа запросы не уйдут")
        token: SecretStr = SecretStr("")
        timeout: int = 30

    class Defaults(Base):
        level: str = "INFO"

    class Root(Base):
        service: Section
        defaults: Defaults = Defaults()
        optional: int = 1

    rendered = render_minimal_config(Root)

    assert yaml.safe_load(rendered) == {
        "service": {"endpoint": "<endpoint>", "api_key": "<api_key>", "token": ""}
    }
    assert "  # Адрес сервиса.\n  endpoint:" in rendered


def test_placeholder_for_field_without_default_is_reported() -> None:
    """Плейсхолдер из минимального конфига не должен пройти молча."""

    class Section(Base):
        endpoint: str

    unfilled = unfilled_fields(Section(endpoint="<endpoint>"))

    assert [field.path for field in unfilled] == ["endpoint"]


def test_init_script_does_not_overwrite_existing_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    script = PROJECT_ROOT / "scripts" / "config_init.py"

    subprocess.run([sys.executable, script, config_path], check=True)
    assert config_path.read_text(encoding="utf-8") == render_minimal_config(Config)
    if sys.platform != "win32":
        assert config_path.stat().st_mode & 0o777 == 0o600

    config_path.write_text("app:\n  seed: 7\n", encoding="utf-8")
    subprocess.run([sys.executable, script, config_path], check=True)
    assert config_path.read_text(encoding="utf-8") == "app:\n  seed: 7\n"

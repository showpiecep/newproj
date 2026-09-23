"""Минимальный `config.yaml`: только то, что нужно вписать руками.

Новый пользователь заполняет секреты и обязательные поля, остальное берётся из
умолчаний моделей. Если в минимальный конфиг попадёт лишнее, умолчания в нём
застынут; если не попадёт обязательное — прогон упадёт отказом провайдера.
"""

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from pydantic import Field, SecretStr

from {{ project_slug }}.evaluation.cli import cli
from {{ project_slug }}.settings import Config, UnfilledSettingsError
from {{ project_slug }}.settings.artifacts.minimal import render_minimal_config
from {{ project_slug }}.settings.requirements import must_be_filled
from {{ project_slug }}.settings.sections.base import Base


def test_minimal_config_lists_only_the_judge_key() -> None:
    assert yaml.safe_load(render_minimal_config(Config)) == {"judge": {"api_key": "<api_key>"}}


def test_unfilled_minimal_config_stops_loading(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(render_minimal_config(Config), encoding="utf-8")

    with pytest.raises(UnfilledSettingsError, match=r"judge\.api_key"):
        Config.load(config_path)


def test_filled_minimal_config_keeps_defaults(tmp_path: Path) -> None:
    minimal_path = tmp_path / "config.yaml"
    minimal_path.write_text(
        render_minimal_config(Config).replace("<api_key>", "real-key"), encoding="utf-8"
    )
    full_path = tmp_path / "full.yaml"
    full_path.write_text("judge:\n  api_key: real-key\n", encoding="utf-8")

    # Кроме ключа, ничего не переопределено: всё — умолчания моделей.
    assert Config.load(minimal_path).model_dump() == Config.load(full_path).model_dump()


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


def test_init_config_does_not_overwrite_existing_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    command = ["init-config", "--out", str(config_path)]

    CliRunner().invoke(cli, command, catch_exceptions=False)
    assert config_path.read_text(encoding="utf-8") == render_minimal_config(Config)

    config_path.write_text("judge:\n  api_key: real-key\n", encoding="utf-8")
    CliRunner().invoke(cli, command, catch_exceptions=False)
    assert config_path.read_text(encoding="utf-8") == "judge:\n  api_key: real-key\n"

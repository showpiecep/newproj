from pathlib import Path

import pytest
from pydantic import ValidationError

from {{ project_slug }}.settings import Config

VALID_CONFIG = """
app:
  name: test
  seed: 7
"""


def test_loads_nested_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(VALID_CONFIG, encoding="utf-8")

    config = Config.load(config_path)

    assert config.app.name == "test"
    assert config.app.seed == 7


def test_missing_fields_fall_back_to_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("app:\n  seed: 7\n", encoding="utf-8")

    config = Config.load(config_path)

    assert config.app.name == "{{ project_name }}"


def test_environment_variables_do_not_override_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(VALID_CONFIG, encoding="utf-8")
    monkeypatch.setenv("APP__SEED", "1234")

    config = Config.load(config_path)

    assert config.app.seed == 7


def test_rejects_unknown_keys(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(VALID_CONFIG + "\nunknown: true\n", encoding="utf-8")

    with pytest.raises(ValidationError):
        Config.load(config_path)

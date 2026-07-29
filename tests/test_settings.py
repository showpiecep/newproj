from pathlib import Path

import pytest
from pydantic import ValidationError

from {{ project_slug }}.settings import Config

VALID_CONFIG = """
app:
  name: test
  debug: true
  host: 127.0.0.1
  port: 9000
  config_template_path: config.template.yaml
logging:
  level: DEBUG
  serialize: false
"""


def test_loads_nested_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(VALID_CONFIG, encoding="utf-8")

    config = Config.load(config_path)

    assert config.app.name == "test"
    assert config.app.port == 9000
    assert config.logging.level == "DEBUG"


def test_environment_variables_do_not_override_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(VALID_CONFIG, encoding="utf-8")
    monkeypatch.setenv("APP__PORT", "1234")

    config = Config.load(config_path)

    assert config.app.port == 9000


def test_rejects_unknown_keys(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(VALID_CONFIG + "\nunknown: true\n", encoding="utf-8")

    with pytest.raises(ValidationError):
        Config.load(config_path)

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from pydantic import ValidationError

from {{ project_slug }}.application import ApplicationState, StatefulFastAPI, bootstrap

from .test_settings import VALID_CONFIG


def test_bootstrap_writes_template_before_loading_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    template_path = tmp_path / "config.template.yaml"
    config_path.write_text(VALID_CONFIG, encoding="utf-8")

    application = bootstrap(config_path)
    app = application.create_app()

    assert isinstance(app, StatefulFastAPI)
    assert isinstance(app.state, ApplicationState)

    with TestClient(app):
        assert app.state.config is application.config

    template = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    assert template == {
        "app": {
            "name": "{{ project_name }}",
            "debug": False,
            "host": "0.0.0.0",
            "port": {{ service_port }},
            "config_template_path": "config.template.yaml",
        },
        "logging": {
            "level": "INFO",
            "serialize": False,
        },
    }


def test_bootstrap_writes_template_even_when_config_is_invalid(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    template_path = tmp_path / "config.template.yaml"
    config_path.write_text("unknown: true\n", encoding="utf-8")

    with pytest.raises(ValidationError):
        bootstrap(config_path)

    assert template_path.is_file()

from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from {{ project_slug }}.application import Application
from {{ project_slug }}.settings import Config


def test_lifespan_writes_current_config_template(tmp_path: Path) -> None:
    template_path = tmp_path / "config.template.yaml"
    config = Config(
        app={
            "name": "test",
            "debug": True,
            "host": "127.0.0.1",
            "port": 9000,
            "config_template_path": str(template_path),
        }
    )
    app = Application(config).create_app()

    with TestClient(app):
        template = yaml.safe_load(template_path.read_text(encoding="utf-8"))

    assert template == {
        "app": {
            "name": "{{ project_name }}",
            "debug": False,
            "host": "0.0.0.0",
            "port": {{ service_port }},
            "config_template_path": "config.template.yaml",
        }
    }

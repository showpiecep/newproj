"""Шаблон настроек содержит только обычные YAML-значения и не раскрывает секреты."""

from pathlib import Path

import yaml

from {{ project_slug }}.evaluation.settings_template import write_template


def test_writes_yaml_safe_defaults(tmp_path: Path) -> None:
    path = tmp_path / "config.template.yaml"

    write_template(path)

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert payload["judge"]["api_key"] == "<api_key>"
    assert payload["service"]["timeout"] == 60.0

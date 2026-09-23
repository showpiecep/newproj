"""Незаполненный секрет должен останавливать запуск, а не прогон на середине.

Ключ судьи проходит валидацию типов и пустым, и плейсхолдером из шаблона:
строка остаётся строкой. Без этой проверки прогон стартует, тратит время и
падает отказом провайдера, когда часть работы уже сделана.
"""

import re
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from {{ project_slug }}.evaluation.cli import cli
from {{ project_slug }}.settings import Config, UnfilledSettingsError
from {{ project_slug }}.settings.artifacts import write_config_artifacts

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


def test_unfilled_api_key_stops_loading_with_explanation(tmp_path: Path) -> None:
    config_path = _config_from_template(tmp_path, filled=False)

    with pytest.raises(UnfilledSettingsError) as error:
        Config.load(config_path)

    message = str(error.value)
    assert "judge.api_key" in message
    assert "не сможет обратиться к судье" in message
    assert str(config_path) in message


def test_filled_api_key_loads(tmp_path: Path) -> None:
    config = Config.load(_config_from_template(tmp_path, filled=True))

    assert config.judge.api_key.get_secret_value() == "test-value"


def test_cli_reports_unfilled_config_without_traceback(tmp_path: Path) -> None:
    config_path = _config_from_template(tmp_path, filled=False)
    run_config = tmp_path / "run.yaml"
    run_config.write_text("", encoding="utf-8")

    # run_config — позиционный аргумент; ошибка должна прийти из проверки
    # конфигурации, а не из разбора аргументов.
    result = CliRunner().invoke(
        cli,
        ["run", str(run_config), "--config", str(config_path)],
        standalone_mode=False,
    )

    assert isinstance(result.exception, UnfilledSettingsError)
    assert "judge.api_key" in str(result.exception)
    assert "Traceback" not in result.output

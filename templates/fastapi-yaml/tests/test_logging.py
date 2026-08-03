import pytest
from loguru import logger

from {{ project_slug }}.observability import configure_logging
from {{ project_slug }}.settings.logging import LoggingSettings


def test_application_logs_use_configured_loguru_level(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging(LoggingSettings(level="WARNING"))

    logger.info("not emitted")
    logger.warning("application warning")

    captured = capsys.readouterr()
    assert "not emitted" not in captured.err
    assert "application warning" in captured.err

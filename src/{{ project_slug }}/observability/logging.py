import sys

from loguru import logger

from ..settings.logging import LoggingSettings

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def configure_logging(settings: LoggingSettings) -> None:
    """Configure Loguru for logs emitted by the application code."""

    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.level,
        format=LOG_FORMAT,
        serialize=settings.serialize,
        backtrace=False,
        diagnose=False,
    )

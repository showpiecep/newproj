from typing import Literal

from .base import Base


class LoggingSettings(Base):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    serialize: bool = False

from pathlib import Path
from typing import Self

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from .app import AppSettings
from .base import Base
from .logging import LoggingSettings


class Config(Base):
    """Master configuration containing every settings section."""

    model_config = SettingsConfigDict(
        extra="forbid",
        frozen=True,
        yaml_file="config.yaml",
        yaml_file_encoding="utf-8",
    )

    app: AppSettings
    logging: LoggingSettings = LoggingSettings()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings, YamlConfigSettingsSource(settings_cls))

    @classmethod
    def load(cls, path: str | Path = "config.yaml") -> Self:
        config_path = Path(path)
        if not config_path.is_file():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}. "
                "Copy config.template.yaml to config.yaml first."
            )

        class FileConfig(cls):
            model_config = SettingsConfigDict(
                extra="forbid",
                frozen=True,
                yaml_file=config_path,
                yaml_file_encoding="utf-8",
            )

        return FileConfig()

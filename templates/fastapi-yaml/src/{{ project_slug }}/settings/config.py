from pathlib import Path
from typing import Self

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from .requirements import UnfilledSettingsError, unfilled_fields
from .sections.app import AppSettings
from .sections.base import Base
from .sections.logging import LoggingSettings


class Config(Base):
    """Master configuration containing every settings section."""

    model_config = SettingsConfigDict(
        extra="forbid",
        frozen=True,
        yaml_file="config.yaml",
        yaml_file_encoding="utf-8",
    )

    app: AppSettings = AppSettings()
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
                f"Нет файла конфигурации: {config_path}. Создайте его командой make config."
            )

        class FileConfig(cls):
            model_config = SettingsConfigDict(
                extra="forbid",
                frozen=True,
                yaml_file=config_path,
                yaml_file_encoding="utf-8",
            )

        config = FileConfig()

        unfilled = unfilled_fields(config)
        if unfilled:
            raise UnfilledSettingsError(unfilled, str(config_path))

        return config

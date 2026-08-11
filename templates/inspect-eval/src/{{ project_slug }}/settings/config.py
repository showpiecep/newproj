from pathlib import Path
from typing import Self

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from .base import Base
from .judge import JudgeSettings
from .logging import LoggingSettings
from .service import ServiceSettings


class Config(Base):
    """Мастер-конфигурация: секреты и адреса, но не параметры прогона.

    Разделение намеренное. Здесь лежит то, что различается между машинами и не
    должно попадать в репозиторий (ключи, локальные адреса). Параметры прогона —
    датасет, критерии, модель судьи — живут в `configs/runs/` и версионируются,
    потому что без них результат нельзя воспроизвести.
    """

    model_config = SettingsConfigDict(
        extra="forbid",
        frozen=True,
        yaml_file="config.yaml",
        yaml_file_encoding="utf-8",
    )

    judge: JudgeSettings = JudgeSettings()
    service: ServiceSettings = ServiceSettings()
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

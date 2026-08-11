from pydantic import ConfigDict
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource


class Base(BaseSettings):
    """Base class for every settings section."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings,)

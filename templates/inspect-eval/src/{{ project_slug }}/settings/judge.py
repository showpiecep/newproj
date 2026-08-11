from pydantic import Field, SecretStr

from .base import Base


class JudgeSettings(Base):
    """Доступ к провайдеру модели-судьи.

    Ключ — секрет: он живёт в локальном `config.yaml`, который не попадает в
    репозиторий, а не в конфигурации прогона, которая версионируется.
    """

    api_key: SecretStr = Field(default=SecretStr(""))
    base_url: str | None = None

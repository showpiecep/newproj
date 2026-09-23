from pydantic import SecretStr

from ..requirements import must_be_filled
from .base import Base


class JudgeSettings(Base):
    """Доступ к провайдеру модели-судьи.

    Ключ — секрет: он живёт в локальном `config.yaml`, который не попадает в
    репозиторий, а не в конфигурации прогона, которая версионируется.
    """

    api_key: SecretStr = must_be_filled(
        SecretStr(""),
        "ключ провайдера модели-судьи; без него прогон не сможет обратиться к судье",
    )
    base_url: str | None = None

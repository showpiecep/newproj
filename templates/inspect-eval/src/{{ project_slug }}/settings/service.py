from pydantic import Field

from .base import Base


class ServiceSettings(Base):
    """Адрес и параметры доступа к тестируемому сервису."""

    url: str = "{{ service_under_test_url }}"
    timeout: float = Field(default=60.0, gt=0)
    answer_field: str = "answer"
    headers: dict[str, str] = Field(default_factory=dict)

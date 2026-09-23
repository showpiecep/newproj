from pydantic import Field

from .base import Base


class AppSettings(Base):
    name: str = "{{ project_name }}"
    seed: int = Field(default=42, description="Зерно генераторов случайных чисел.")

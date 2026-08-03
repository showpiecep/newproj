from pydantic import Field

from .base import Base


class AppSettings(Base):
    name: str = "{{ project_name }}"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = Field(default={{ service_port }}, ge=1, le=65535)
    config_template_path: str = "config.template.yaml"

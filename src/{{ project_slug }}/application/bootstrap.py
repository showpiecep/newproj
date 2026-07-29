from pathlib import Path

from ..observability import configure_logging
from ..settings import Config
from ..settings.app import AppSettings
from ..settings.template import write_config_template
from .app import Application


def bootstrap(config_path: str | Path = "config.yaml") -> Application:
    """Generate the settings template, load config and assemble the application."""

    config_path = Path(config_path)
    default_template_path = config_path.parent / AppSettings().config_template_path
    write_config_template(Config, default_template_path)

    config = Config.load(config_path)
    configure_logging(config.logging)

    configured_template_path = Path(config.app.config_template_path)
    if not configured_template_path.is_absolute():
        configured_template_path = config_path.parent / configured_template_path

    if configured_template_path != default_template_path:
        write_config_template(Config, configured_template_path)

    return Application(config)

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..settings import Config
from ..settings.template import write_config_template


class Application:
    """FastAPI application assembly and lifecycle."""

    def __init__(self, config: Config) -> None:
        self.config = config

    def create_app(self) -> FastAPI:
        return FastAPI(
            title=self.config.app.name,
            debug=self.config.app.debug,
            lifespan=self.lifespan,
        )

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncIterator[None]:
        write_config_template(Config, self.config.app.config_template_path)
        app.state.config = self.config
        yield

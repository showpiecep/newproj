from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ..settings import Config
from .state import ApplicationState, StatefulFastAPI


class Application:
    """FastAPI application assembly and lifecycle."""

    def __init__(self, config: Config) -> None:
        self.config = config

    def create_app(self) -> StatefulFastAPI:
        app = StatefulFastAPI(
            title=self.config.app.name,
            debug=self.config.app.debug,
            lifespan=self.lifespan,
        )
        app.state = ApplicationState()
        return app

    @asynccontextmanager
    async def lifespan(self, app: StatefulFastAPI) -> AsyncIterator[None]:
        app.state.config = self.config
        yield

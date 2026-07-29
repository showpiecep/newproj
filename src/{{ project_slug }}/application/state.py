from fastapi import FastAPI
from starlette.datastructures import State

from ..settings import Config


class ApplicationState(State):
    """Typed values shared through the FastAPI application state.

    Add a field here whenever a new resource becomes available through ``app.state``.
    """

    config: Config


class StatefulFastAPI(FastAPI):
    """FastAPI application with a typed ``state`` attribute."""

    state: ApplicationState

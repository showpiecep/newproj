import uvicorn

from .application import bootstrap

application = bootstrap()
app = application.create_app()


def run() -> None:
    uvicorn.run(
        app,
        host=application.config.app.host,
        port=application.config.app.port,
    )


if __name__ == "__main__":
    run()

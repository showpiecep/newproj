import sys

from .settings import Config, UnfilledSettingsError


def run() -> None:
    """Загрузить конфигурацию и запустить проект.

    Незаполненный конфиг — не сбой программы, а сообщение оператору, поэтому
    traceback здесь не нужен.
    """
    try:
        config = Config.load()
    except UnfilledSettingsError as error:
        print(error, file=sys.stderr)
        raise SystemExit(1) from None

    print(f"{config.app.name}: конфигурация загружена, seed={config.app.seed}")


if __name__ == "__main__":
    run()

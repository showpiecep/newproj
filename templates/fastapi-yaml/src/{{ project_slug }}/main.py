import sys

import uvicorn

from .application import bootstrap
from .settings import UnfilledSettingsError


def run() -> None:
    """Поднять сервис.

    Сборка приложения живёт здесь, а не в теле модуля: импорт `main` не должен
    читать конфигурацию и писать файлы. Незаполненный конфиг — не сбой
    программы, а сообщение оператору, поэтому traceback здесь не нужен.
    """
    try:
        application = bootstrap()
    except UnfilledSettingsError as error:
        print(error, file=sys.stderr)
        raise SystemExit(1) from None

    uvicorn.run(
        application.create_app(),
        host=application.config.app.host,
        port=application.config.app.port,
    )


if __name__ == "__main__":
    run()

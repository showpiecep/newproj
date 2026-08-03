# {{ project_name }}

FastAPI-шаблон с типизированной конфигурацией из YAML. `.env` не используется:
вложенность остаётся обычной YAML-вложенностью, а вся структура проверяется
Pydantic при старте приложения.

## Быстрый старт

```bash
git init
make init
make config
# Отредактируйте config.yaml
make run
```

`make init` устанавливает зависимости и включает pre-commit-хуки. Если каталог
ещё не является git-репозиторием, установка хуков пропускается с подсказкой:
выполните `git init`, затем `make hooks`.

После запуска доступны API на <http://127.0.0.1:{{ service_port }}> и документация
на <http://127.0.0.1:{{ service_port }}/docs>.

## Как устроена конфигурация

`config.template.yaml` коммитится и описывает полное дерево настроек.
`config.yaml` создаётся локально, содержит реальные секреты и игнорируется Git.
Путь к другому YAML можно передать приложению программно:

```python
config = Config.load(Path("/run/secrets/service-config.yaml"))
app = Application(config).create_app()
```

Такой явный путь удобен для Docker/Kubernetes: YAML монтируется как один secret
volume без преобразования вложенных ключей в переменные окружения.

`Config` — мастер-модель, содержащая вложенные секции настроек. Каждая новая область
конфигурации получает отдельный модуль в пакете `settings`, после чего добавляется
полем в `Config`.

При каждом запуске bootstrap строит актуальный `config.template.yaml`
непосредственно из Pydantic-моделей до чтения пользовательского конфига. Благодаря
этому структура шаблона не расходится со структурой кода даже тогда, когда старый
`config.yaml` уже не проходит валидацию. После загрузки конфига bootstrap также
учитывает путь из поля `app.config_template_path`.

При запуске через `make run` Uvicorn получает `host` и `port` из `config.yaml`.

## Логирование

Прикладной код использует Loguru напрямую:

```python
from loguru import logger

logger.info("Application event")
```

Уровень и JSON-сериализация задаются секцией `logging` в `config.yaml`.
Логи Uvicorn, FastAPI и сторонних библиотек не перехватываются и продолжают
работать через собственные механизмы.

## Состояние приложения

`app.state` представлен типизированным `ApplicationState`. Когда в lifespan
появляется новый общий ресурс, его поле добавляется в `application/state.py`.
После этого обращения к состоянию получают автодополнение и статическую проверку
типов вместо неявных динамических атрибутов.

Исходный пакет намеренно остаётся минимальным:

```text
src/{{ project_slug }}/
├── main.py
├── application/
│   ├── app.py
│   ├── bootstrap.py
│   ├── state.py
│   └── routers/
│       └── __init__.py
├── settings/
│   ├── app.py
│   ├── base.py
│   ├── config.py
│   ├── logging.py
│   └── template.py
├── observability/
│   └── logging.py
└── usecases/
    └── __init__.py
```

## Проверки

```bash
make test
make lint
make format
make check
```

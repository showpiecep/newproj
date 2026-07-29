# {{ project_name }}

FastAPI-шаблон с типизированной конфигурацией из YAML. `.env` не используется:
вложенность остаётся обычной YAML-вложенностью, а вся структура проверяется
Pydantic при старте приложения.

## Быстрый старт

```bash
make init
make config
# Отредактируйте config.yaml
make run
```

После запуска доступны API на <http://127.0.0.1:{{ service_port }} и документация
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

При каждом запуске FastAPI lifespan строит актуальный `config.template.yaml`
непосредственно из Pydantic-моделей. Благодаря этому структура шаблона не расходится
со структурой кода. Путь к шаблону задаётся полем
`app.config_template_path`.

Исходный пакет намеренно остаётся минимальным:

```text
src/{{ project_slug }}/
├── main.py
├── application/
│   ├── app.py
│   └── routers/
│       └── __init__.py
├── settings/
│   ├── app.py
│   ├── base.py
│   ├── config.py
│   └── template.py
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

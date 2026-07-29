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
settings = Settings.load(Path("/run/secrets/service-config.yaml"))
app = Application(settings).create_app()
```

Такой явный путь удобен для Docker/Kubernetes: YAML монтируется как один secret
volume без преобразования вложенных ключей в переменные окружения.

`Settings` — мастер-модель всех настроек. `Application` владеет FastAPI lifespan:
на старте он создаёт инфраструктурные классы только из предназначенных им секций
(`DatabaseSettings` → `Database`, `RedisSettings` → `RedisCache`), а на остановке
закрывает их в обратном порядке. Секреты скрыты в `repr` благодаря `SecretStr`.

Реализации `Database` и `RedisCache` оставлены безопасными точками расширения.
Подключите в них конкретные драйверы, не меняя схему конфигурации или lifespan.

## Проверки

```bash
make test
make lint
make format
make check
```

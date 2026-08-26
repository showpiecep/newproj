# newproj

Кроссплатформенная команда для создания проектов из встроенных
[Copier](https://copier.readthedocs.io/)-шаблонов. Работает в macOS, Linux и
Windows, в том числе в Zsh, Bash, Fish, Git Bash, PowerShell и `cmd`.

Документация и changelog: <https://showpiecep.github.io/newproj/>

## Установка

Сначала установите [uv](https://docs.astral.sh/uv/getting-started/installation/).
Python отдельно не требуется: при необходимости uv установит его сам.

Во всех оболочках команда установки одинакова:

```text
uv tool install https://github.com/showpiecep/newproj/releases/latest/download/newproj-templates.tar.gz
```

Если uv предупредил, что каталог команд отсутствует в `PATH`:

```text
uv tool update-shell
```

После этого откройте новый терминал и проверьте установку:

```text
newproj --version
newproj list
```

Также доступны загрузчики:

```bash
# macOS, Linux, WSL и Git Bash
curl -LsSf https://raw.githubusercontent.com/showpiecep/newproj/main/install.sh | sh
```

```powershell
# Windows PowerShell
irm https://raw.githubusercontent.com/showpiecep/newproj/main/install.ps1 | iex
```

## Использование

```text
newproj                  # интерактивное создание проекта
newproj create           # то же явно
newproj list             # встроенные и добавленные шаблоны
newproj add <url>        # добавить шаблоны из Git-репозитория
newproj update           # обновить CLI и встроенные шаблоны
newproj update --check   # сравнить версию с последним релизом
newproj --help
```

Без аргументов команда спрашивает родительский каталог, имя проекта и шаблон,
после чего запускает Copier. `newproj` — отдельная исполняемая программа, поэтому
она не меняет каталог родительской оболочки; в конце команда печатает готовую
команду `cd`.

Для CI и скриптов есть неинтерактивный режим:

```text
newproj create --parent . --name example --template fastapi-yaml --defaults --non-interactive
```

Вместо имени установленного шаблона можно передать любой Git-источник, который
поддерживает Copier, и при необходимости выбрать ветку, тег или коммит:

```text
newproj create --parent . --name example --template gh:owner/copier-template
newproj create --parent . --name example --template git@github.com:owner/private-template.git --vcs-ref main
```

Для закрытого репозитория используется обычная авторизация Git: SSH-ключи или
настроенный менеджер учётных данных. Токен в командной строке указывать не
следует — он может сохраниться в истории оболочки.

Репозиторий с шаблонами можно добавить к себе один раз, чтобы он появился в
меню и в `newproj list`:

```text
newproj add git@github.com:owner/copier-templates.git
newproj add https://github.com/owner/copier-templates.git --name team --ref main
```

Команда клонирует репозиторий в каталог пользовательских шаблонов и проверяет,
что в его корне есть `copier.yml`; если файла нет, клон удаляется. Имя каталога
берётся из адреса и задаётся флагом `--name`. Добавленный шаблон виден в списке
вместе с адресом, откуда он получен:

```text
  copier-templates (из git@github.com:owner/copier-templates.git)
```

Обновляется он обычным `git pull` в своём каталоге, удаляется — удалением этого
каталога. Отдельного реестра источников нет: реестром служит сам клон.

Встроенные шаблоны поставляются внутри Python-пакета. Собственные Copier-шаблоны
можно положить в `~/templates`; другой путь задаётся переменной
`NEWPROJ_TEMPLATES_DIR`. Пользовательский шаблон с тем же именем перекрывает
встроенный, кроме копий с меткой старого установщика `.newproj-managed`.

## Обновление и удаление

```text
newproj update
uv tool uninstall newproj
```

`newproj update` вызывает `uv tool upgrade newproj`, поэтому команда и встроенные
шаблоны обновляются одной атомарной установкой. Оболочечные rc-файлы newproj не
изменяет.

### Переход со старой Zsh-версии

Версии до `v0.3.0` добавляли функцию в `~/.zshrc` и копировали шаблоны в
`~/templates`. Перед новой установкой выполните старый деинсталлятор, если он
сохранился:

```text
sh ~/.local/share/newproj/uninstall.sh
```

Затем установите новую версию и перезапустите терминал. Даже если старые копии
шаблонов остались, новая команда распознает метку `.newproj-managed` и использует
актуальные встроенные версии.

## Шаблоны

| Шаблон | Назначение |
|---|---|
| [fastapi-yaml](templates/fastapi-yaml/) | FastAPI-сервис с типизированной YAML-конфигурацией, Loguru и настроенными ruff/pytest/pre-commit |
| [inspect-eval](templates/inspect-eval/) | Сервис оценки на Inspect AI с LLM-судьёй, конфигами прогонов и просмотром логов |

## Разработка

```text
uv sync
uv run pytest
uv run ruff check src tests
uv build
```

Полный smoke-тест собирает wheel, устанавливает его в изолированный каталог и
создаёт настоящий проект:

```text
sh installer/test-install.sh
```

GitHub Actions выполняет те же проверки на Ubuntu, macOS и Windows с Python
3.11 и 3.13. На Windows отдельно запускаются Git Bash и PowerShell.

## Структура репозитория

```text
src/newproj/          кроссплатформенный Python CLI
templates/<имя>/     Copier-шаблоны
tests/                тесты CLI и состава пакета
installer/            smoke-тест и сборка релиза
install.sh            загрузчик для POSIX-оболочек
install.ps1           загрузчик для PowerShell
docs/                 сайт Quarto
```

Новый шаблон — это каталог `templates/<имя>` с `copier.yml`. Отдельно менять CLI
не нужно: шаблоны автоматически включаются в wheel при сборке.

## Выпуск версии

Версия в `pyproject.toml` должна совпадать с тегом без префикса `v`:

```text
sh installer/test-install.sh
git tag v0.3.0
git push origin v0.3.0
```

Release workflow собирает архив исходников с постоянным URL, wheel и SHA-256,
затем публикует их в GitHub Release.
